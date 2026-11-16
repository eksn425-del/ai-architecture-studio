"""B.AI SSE transport; tools wait for complete output and actual metered usage."""
from __future__ import annotations

import json
import re
import time
from types import SimpleNamespace

import httpx


def _bounded_lines(response, started):
    """Bound bytes before line buffering, including comments/unfinished frames.

    Keep HTTPX's incremental UTF-8/newline handling. Its socket read timeout
    still bounds a silent read; elapsed time is checked on every received chunk.
    """
    class BoundedStream(httpx.SyncByteStream):
        def __iter__(self):
            received = 0
            for chunk in response.iter_bytes():
                if time.monotonic() - started > 900:
                    raise TimeoutError("B.AI streaming response exceeded its time limit; Request timed out.")
                received += len(chunk)
                if received > 8 * 1024 * 1024:
                    raise ValueError("B.AI streaming response exceeded its size limit; no tools executed.")
                yield chunk

    # The outer response context owns the real connection. This wrapper only
    # supplies the bounded bytes to the public HTTPX line decoder.
    framed = httpx.Response(200, headers={"content-type": "text/event-stream; charset=utf-8"},
                            stream=BoundedStream())
    try:
        yield from framed.iter_lines()
    finally:
        framed.close()


def complete_bai(kwargs: dict, *, record=lambda event: None, transport=None):
    # Do not run partial tool arguments or infer missing usage from token counts.
    body = {k: v for k, v in kwargs.items() if k not in {
        "api_key", "api_base", "timeout", "max_retries", "num_retries",
    }}
    expected = body["model"].removeprefix("openai/")
    body.update(model=expected, stream=True, stream_options={"include_usage": True})
    content, reasoning, calls = [], [], {}
    usage, finish, done = None, None, False
    started = last_report = time.monotonic()
    chunk_count = 0
    phase, request_id = "awaiting_headers", ""

    def telemetry(event, **fields):
        record({"event": event, "phase": phase, "request_id": request_id,
                "elapsed_ms": round((time.monotonic() - started) * 1000), **fields})

    def accept(data):
        nonlocal usage, finish, done, chunk_count, last_report
        if data == "[DONE]":
            done = True
            return
        chunk = json.loads(data)
        if chunk.get("error"):
            raise ValueError("B.AI 流返回错误；未执行本次工具输出。")
        if chunk.get("model") != expected:
            raise ValueError("B.AI 流返回的模型不匹配；未执行本次工具输出。")
        chunk_count += 1
        if chunk_count == 1:
            telemetry("provider_stream_first_chunk")
        if time.monotonic() - last_report >= 15:
            record({"event": "provider_stream_progress", "chunks_received": chunk_count,
                    "elapsed_ms": round((time.monotonic() - started) * 1000)})
            last_report = time.monotonic()
        if chunk.get("usage") is not None:
            usage = chunk["usage"]
        choices = chunk.get("choices", [])
        if len(choices) > 1:
            raise ValueError("B.AI returned multiple choices; no tools executed.")
        for choice in choices:
            if choice.get("index") != 0:
                raise ValueError("B.AI returned an invalid choice index.")
            delta = choice.get("delta") or {}
            if finish and any(delta.get(k) for k in ("content", "reasoning_content", "tool_calls")):
                raise ValueError("B.AI returned output after the terminal choice.")
            for key, parts in (("content", content), ("reasoning_content", reasoning)):
                value = delta.get(key)
                if value is not None:
                    if not isinstance(value, str):
                        raise ValueError("B.AI returned a non-text output fragment.")
                    parts.append(value)
            for fragment in delta.get("tool_calls") or []:
                index = fragment.get("index")
                if type(index) is not int or not 0 <= index < 64:
                    raise ValueError("B.AI returned an invalid tool index.")
                call = calls.setdefault(index, {"id": "", "type": "function",
                                               "function": {"name": "", "arguments": ""}})
                if fragment.get("type", "function") != "function":
                    raise ValueError("B.AI returned an unsupported tool type.")
                call["id"] += fragment.get("id") or ""
                function = fragment.get("function") or {}
                for key in ("name", "arguments"):
                    value = function.get(key) or ""
                    if not isinstance(value, str):
                        raise ValueError("B.AI returned an invalid tool fragment.")
                    call["function"][key] += value
            if choice.get("finish_reason") is not None:
                if finish is not None:
                    raise ValueError("B.AI repeated a terminal choice.")
                finish = choice["finish_reason"]

    try:
        with httpx.Client(timeout=kwargs.get("timeout", 240), trust_env=True,
                          follow_redirects=False, transport=transport) as client:
            with client.stream("POST", kwargs["api_base"].rstrip("/") + "/chat/completions",
                               headers={"Authorization": "Bearer " + kwargs["api_key"]}, json=body) as response:
                phase = "headers_received"
                candidate = response.headers.get("x-request-id", response.headers.get("request-id", ""))
                request_id = candidate if (re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", candidate)
                    and kwargs["api_key"] not in candidate) else ""
                telemetry("provider_stream_headers", status_code=response.status_code)
                response.raise_for_status()
                if "text/event-stream" not in response.headers.get("content-type", ""):
                    raise ValueError("B.AI did not return the requested SSE stream.")
                phase = "streaming"
                data_lines = []
                for line in _bounded_lines(response, started):
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                    elif not line and data_lines:
                        accept("\n".join(data_lines))
                        data_lines.clear()
                        if done:
                            break
                if data_lines and not done:
                    accept("\n".join(data_lines))
        if not done or finish not in {"stop", "tool_calls"}:
            raise ValueError("B.AI 流输出中断或被截断；未执行本次工具输出。")
        if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                                            for k in ("prompt_tokens", "completion_tokens")):
            raise ValueError("B.AI 流缺少真实用量；保留预算预留，未执行本次工具输出。")
    except Exception as error:
        if isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout)):
            phase = "connecting"
        telemetry("provider_transport_failed", error_type=type(error).__name__, chunks_received=chunk_count)
        raise
    message = {"role": "assistant", "content": "".join(content),
               "tool_calls": [calls[i] for i in sorted(calls)]}
    if reasoning:
        message["reasoning_content"] = "".join(reasoning)
    return SimpleNamespace(model=expected, usage=usage,
                           choices=[SimpleNamespace(message=message, finish_reason=finish)])
