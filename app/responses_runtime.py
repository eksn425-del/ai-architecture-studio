"""Responses transport for the existing project/Skill/guarded-tool/QA harness.

No Codex dependency and no provider fallback. Owner-trusted local pilot only;
not authentication, cloud tenant isolation or billing. Live inference is off
unless the operator supplies a key, explicit consent and a priced finite cap.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from .litellm_runtime import LiteLLMRuntime
from .native_agent import NativeAgentUnavailable


PROFILES = {
    "bai": "https://api.b.ai/v1/responses",
    "official": "https://api.openai.com/v1/responses",
}


@dataclass(frozen=True)
class ResponsesProfile:
    provider: str = "bai"
    model: str = "gpt-6.1-sol"
    images: bool = True
    encrypted_reasoning: bool = True

    @property
    def endpoint(self) -> str:
        if self.provider not in PROFILES:
            raise ValueError("Unapproved Responses endpoint profile")
        return PROFILES[self.provider]


@dataclass(frozen=True)
class PilotBudget:
    max_usd: Decimal
    input_rate_upper: Decimal
    output_rate_upper: Decimal
    max_input_tokens: int = 200000
    max_output_tokens: int = 12000
    max_requests: int = 12

    def __post_init__(self):
        if any(not isinstance(v, Decimal) or not v.is_finite() or v <= 0
               for v in (self.max_usd, self.input_rate_upper, self.output_rate_upper)):
            raise ValueError("Finite positive operator cap and worst-tier prices required")
        if any(type(v) is not int or v <= 0 for v in
               (self.max_input_tokens, self.max_output_tokens, self.max_requests)):
            raise ValueError("Positive token/request limits required")

    @property
    def reservation(self) -> Decimal:
        return (self.input_rate_upper * self.max_input_tokens +
                self.output_rate_upper * self.max_output_tokens) / 1000000


def responses_input(messages: list[dict[str, Any]], *, images: bool) -> list[dict[str, Any]]:
    """Replay full stateless item history, including opaque reasoning items."""
    items = []
    pending: set[str] = set()
    for message in messages:
        role = message.get("role")
        if role == "tool":
            call_id = message["tool_call_id"]
            if call_id not in pending:
                raise ValueError("Orphan or duplicate function_call_output")
            pending.remove(call_id)
            items.append({"type": "function_call_output", "call_id": call_id,
                          "output": message["content"]})
            continue
        if pending:
            raise ValueError("All function calls must receive outputs before further messages")
        raw = message.get("responses_output")
        if raw is not None:
            items.extend(raw)
            for item in raw:
                if item.get("type") == "function_call":
                    if item["call_id"] in pending:
                        raise ValueError("Duplicate function call ID")
                    pending.add(item["call_id"])
            continue
        content = message.get("content")
        if content:
            if isinstance(content, str):
                blocks = [{"type": "input_text", "text": content}]
            else:
                blocks = []
                for block in content:
                    if block.get("type") == "text":
                        blocks.append({"type": "input_text", "text": block["text"]})
                    elif block.get("type") == "image_url":
                        if not images:
                            raise ValueError("Selected profile has not enabled image input")
                        url = block["image_url"]["url"]
                        if not url.startswith("data:image/"):
                            raise ValueError("Only project-owned image bytes may be sent")
                        blocks.append({"type": "input_image", "image_url": url})
                    else:
                        raise ValueError("Unsupported Responses input block")
            items.append({"role": "developer" if role == "system" else role, "content": blocks})
        for call in message.get("tool_calls") or []:
            call_id = call["id"]
            pending.add(call_id)
            items.append({"type": "function_call", "call_id": call_id,
                          **call["function"]})
    if pending:
        raise ValueError("Unanswered function calls in persisted history")
    return items


class ResponsesRuntime(LiteLLMRuntime):
    provider_name = "managed-responses"
    supports_responses_tools = True

    def __init__(self, runtime_root: Path, *, profile: ResponsesProfile | None = None,
                 budget: PilotBudget | None = None, transport: Callable | None = None,
                 sketchup_mcp=None, max_tool_calls: int = 48):
        self.profile = profile or ResponsesProfile()
        self.profile.endpoint  # validate without contacting upstream
        super().__init__(runtime_root, model=self.profile.model,
                         sketchup_mcp=sketchup_mcp, max_tool_calls=max_tool_calls)
        self.key_env = "K_STUDIO_OPERATOR_API_KEY"
        self.region = self.profile.provider + " Responses / trusted-local-pilot"
        self.budget = budget
        self.transport = transport
        self.cancelled = threading.Event()
        self.receipts: list[dict[str, Any]] = []
        self.spent = Decimal(0)
        self.unknown_usage = False
        self._run_lock = threading.Lock()

    @property
    def api_base(self):
        return self.profile.endpoint.removesuffix("/responses")

    @property
    def dependency_installed(self):
        return True

    @property
    def available(self):
        return self.credential_configured and self.budget is not None and (
            self.transport is not None or (os.environ.get("K_STUDIO_OPERATOR_LIVE_CONSENT") == "1"
                                          and os.environ.get("K_STUDIO_OPERATOR_TERMS_APPROVED") == "1"))

    def completion_callable(self):
        return self._responses_completion

    def before_tool_execution(self):
        if self.cancelled.is_set():
            raise NativeAgentUnavailable("Managed Agent cancelled; no further tools executed")

    def respond(self, **kwargs):
        if not self._run_lock.acquire(blocking=False):
            raise NativeAgentUnavailable("Managed local pilot already running")
        try:
            self.receipts = []
            self.spent = Decimal(0)
            self.unknown_usage = False
            self.cancelled.clear()
            # This is our same harness, not a Codex or external tool writer.
            return super().respond(**kwargs)
        finally:
            try:
                self._persist_receipts(kwargs.get("project_dir"))
            finally:
                self._run_lock.release()

    def _persist_receipts(self, project):
        if project:
            folder = Path(project) / "runtime" / "responses_receipts"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{time.time_ns()}.json"
            encoded = json.dumps({"provider_label": self.profile.provider,
                "api_base_profile": self.profile.endpoint, "requested_model": self.profile.model,
                "receipts": self.receipts, "estimated_usd": str(self.spent),
                "cost_is_operator_estimate_not_invoice": True,
                "unknown_usage": self.unknown_usage, "live": self.transport is None}, indent=2)
            for secret in (self.session_api_key, os.environ.get(self.key_env, "")):
                if secret:
                    encoded = encoded.replace(secret, "[credential hidden]")
            path.write_text(encoded, encoding="utf-8")

    def _responses_completion(self, **kwargs):
        self.before_tool_execution()
        if kwargs["model"] != self.profile.model:
            raise ValueError("Provider/model change requires a new explicit profile")
        key = kwargs["api_key"]
        if not key or not self.budget:
            raise NativeAgentUnavailable("Operator key and finite priced budget required")
        if self.transport is None and (os.environ.get("K_STUDIO_OPERATOR_LIVE_CONSENT") != "1"
                                      or os.environ.get("K_STUDIO_OPERATOR_TERMS_APPROVED") != "1"):
            raise NativeAgentUnavailable("Live Responses not authorized; no request sent")
        if self.unknown_usage or len(self.receipts) >= self.budget.max_requests:
            raise NativeAgentUnavailable("Request/unknown-usage circuit breaker")
        if self.spent + self.budget.reservation > self.budget.max_usd:
            raise NativeAgentUnavailable("Hard pilot reservation limit: no further request sent")
        items = responses_input(kwargs["messages"], images=self.profile.images)
        # Conservative UTF-8 byte ceiling (including image data); no guessed
        # tokenizer/model limits or discounted/cache pricing assumed.
        if len(json.dumps(items, ensure_ascii=False).encode()) > self.budget.max_input_tokens:
            raise NativeAgentUnavailable("Input byte safety ceiling exceeded; no request sent")
        body: dict[str, Any] = {"model": self.profile.model, "input": items,
            "store": False, "max_output_tokens": self.budget.max_output_tokens}
        if self.profile.encrypted_reasoning:
            body["include"] = ["reasoning.encrypted_content"]
        if kwargs.get("reasoning_effort"):
            body["reasoning"] = {"effort": kwargs["reasoning_effort"]}
        if kwargs.get("tools"):
            body["tools"] = [{"type": "function", **t["function"], "strict": False} for t in kwargs["tools"]]
            body["parallel_tool_calls"] = False
        # Tool descriptions/schema are also billed input, not just messages.
        if len(json.dumps(body, ensure_ascii=False).encode()) > self.budget.max_input_tokens:
            raise NativeAgentUnavailable("Full request byte safety ceiling exceeded; no request sent")
        digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        receipt = {"requested_model": self.profile.model, "provider_label": self.profile.provider,
                   "request_sha256": digest, "idempotency_key": digest,
                   "image_count": sum(b.get("type") == "input_image" for i in items for b in i.get("content", []) if isinstance(b, dict)),
                   "tool_schema_count": len(body.get("tools", [])), "status": "pending"}
        self.receipts.append(receipt)
        start = time.monotonic()
        try:
            if self.transport:
                data = self.transport(body, {"Idempotency-Key": digest})
                request_id = data.get("request_id")
            else:
                import httpx
                with httpx.Client(timeout=90, trust_env=False, follow_redirects=False) as client:
                    response = client.post(self.profile.endpoint, json=body,
                        headers={"Authorization": "Bearer " + key, "Idempotency-Key": digest})
                    request_id = response.headers.get("x-request-id")
                    receipt["http_status"] = response.status_code
                    if response.status_code != 200:
                        raise NativeAgentUnavailable(f"Responses HTTP {response.status_code}; no automatic retry")
                    data = response.json()
            receipt.update(request_id=request_id, response_id=data.get("id"), actual_model=data.get("model"),
                           usage=data.get("usage"), status=data.get("status"))
            usage = data.get("usage") or {}
            inp, out = usage.get("input_tokens"), usage.get("output_tokens")
            if type(inp) is not int or type(out) is not int or min(inp, out) < 0:
                raise NativeAgentUnavailable("Provider omitted valid usage; stop before tools or further spend")
            self.spent += (self.budget.input_rate_upper * inp + self.budget.output_rate_upper * out) / 1000000
            receipt["estimated_usd"] = str(self.spent)
            if inp > self.budget.max_input_tokens or out > self.budget.max_output_tokens or self.spent > self.budget.max_usd:
                raise NativeAgentUnavailable("Provider exceeded reserved token/cost envelope; tools blocked")
            if data.get("model") != self.profile.model:
                raise NativeAgentUnavailable("Returned model differs; no silent substitution allowed")
            if data.get("status") != "completed" or not isinstance(data.get("output"), list):
                raise NativeAgentUnavailable("Responses incomplete/failed/malformed; no tools executed")
            self.before_tool_execution()
            texts, calls = [], []
            for item in data["output"]:
                kind = item.get("type")
                if kind == "function_call":
                    if any(i.get("type") == "function_call" and i.get("call_id") == item.get("call_id") for i in items):
                        raise ValueError("Provider repeated a persisted call ID; execution blocked")
                    args = json.loads(item["arguments"])
                    if not isinstance(args, dict) or not item.get("call_id") or not item.get("name"):
                        raise ValueError("Malformed function call")
                    calls.append({"id": item["call_id"], "type": "function", "function":
                                  {"name": item["name"], "arguments": item["arguments"]}})
                elif kind == "message":
                    for block in item.get("content", []):
                        if block.get("type") == "refusal":
                            raise NativeAgentUnavailable("Provider refused this request")
                        if block.get("type") == "output_text":
                            texts.append(block["text"])
                elif kind == "reasoning":
                    if self.profile.encrypted_reasoning and not item.get("encrypted_content"):
                        raise NativeAgentUnavailable("Missing encrypted reasoning for stateless continuation")
                else:
                    raise ValueError("Unsupported Responses output type")
            if len({c['id'] for c in calls}) != len(calls):
                raise ValueError("Duplicate function call ID")
            return SimpleNamespace(model=data['model'], usage=usage, choices=[SimpleNamespace(message={
                "content": "\n".join(texts), "tool_calls": calls, "responses_output": data['output']})])
        except Exception as error:
            self.unknown_usage = receipt.get("usage") is None
            receipt["error_type"] = type(error).__name__
            # Never persist raw upstream body, prompt, headers or credentials.
            raise NativeAgentUnavailable(f"Responses stopped ({type(error).__name__}): {str(error).replace(key, '[hidden]')[:300]}") from None
        finally:
            receipt["latency_ms"] = round((time.monotonic()-start)*1000)
