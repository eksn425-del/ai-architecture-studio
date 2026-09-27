from __future__ import annotations

import json
import os
import time
import uuid
import importlib.util
from pathlib import Path
from typing import Any

from .agent_tools import AgentToolSurface
from .native_agent import AgentTurnResult, NativeAgentUnavailable
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError


class LiteLLMRuntime:
    """Optional LiteLLM chat-completion adapter for multimodal/function-call providers."""

    provider_name = "litellm"

    def __init__(self, runtime_root: Path, *, sketchup_mcp: ConfiguredSketchUpMCP | None = None,
                 model: str | None = None, region: str | None = None,
                 max_tool_calls: int = 48):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp or ConfiguredSketchUpMCP(timeout_seconds=180)
        self.tool_surface = AgentToolSurface(self.runtime_root, self.sketchup_mcp)
        self.model = model or os.environ.get("ARCH_STUDIO_CHINA_MODEL", "dashscope/qwen3-vl-flash")
        self.region = (region or os.environ.get("ARCH_STUDIO_CHINA_REGION", "international")).lower()
        if self.region not in {"international", "beijing"}:
            raise ValueError("ARCH_STUDIO_CHINA_REGION must be 'international' or 'beijing'.")
        self.max_tool_calls = max_tool_calls

    @property
    def credential_configured(self) -> bool:
        return bool(os.environ.get("DASHSCOPE_API_KEY", "").strip())

    @property
    def dependency_installed(self) -> bool:
        try:
            return importlib.util.find_spec("litellm") is not None
        except (ImportError, ValueError):
            return False

    @property
    def available(self) -> bool:
        return self.credential_configured and self.dependency_installed

    @property
    def api_base(self) -> str:
        if self.region == "beijing":
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    def respond(self, *, project_dir: Path, thread_id: str | None, prompt: str,
                mcp_enabled: bool, developer_instructions: str,
                model_path: Path | None = None, model_guid: str = "",
                ruby_enabled: bool = True, ruby_state: dict[str, dict[str, Any]] | None = None,
                architecture_skill_context: str = "", model: str | None = None,
                reasoning_effort: str | None = None) -> AgentTurnResult:
        api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise NativeAgentUnavailable(
                "Qwen is configured through LiteLLM, but DASHSCOPE_API_KEY is not set; no provider request was sent."
            )
        try:
            from litellm import completion
        except ImportError as error:
            raise NativeAgentUnavailable(
                "LiteLLM is not installed. Install the optional provider requirements to enable the Qwen route."
            ) from error
        try:
            tool_context = self.tool_surface.prepare(
                project_dir=project_dir, mcp_enabled=mcp_enabled, model_path=model_path,
                model_guid=model_guid, ruby_enabled=ruby_enabled, ruby_state=ruby_state,
            )
        except RuntimeError as error:
            raise NativeAgentUnavailable(str(error)) from error

        selected_model = model or self.model
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": developer_instructions},
            {"role": "user", "content": prompt.rstrip() + (("\n\n" + architecture_skill_context.strip()) if architecture_skill_context else "")},
        ]
        tools = [_to_litellm_tool(tool) for tool in tool_context.dynamic_tools] if mcp_enabled else []
        started = time.monotonic()
        input_tokens: int | None = None
        output_tokens: int | None = None
        tool_calls: list[dict[str, str]] = []
        tool_call_count = 0
        failed_tool_calls = 0
        last_reply = ""
        while True:
            kwargs: dict[str, Any] = {
                "model": selected_model,
                "messages": messages,
                "api_key": api_key,
                "api_base": self.api_base,
                "timeout": 240,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                kwargs["parallel_tool_calls"] = False
            try:
                response = completion(**kwargs)
            except Exception as error:
                raise NativeAgentUnavailable(f"LiteLLM request failed for {selected_model}: {error}") from error
            usage = _usage_from_response(response)
            input_tokens = usage[0] if usage[0] is not None else input_tokens
            output_tokens = usage[1] if usage[1] is not None else output_tokens
            message = _response_message(response)
            raw_tool_calls = message.get("tool_calls") or []
            last_reply = _message_content(message)
            if not raw_tool_calls:
                break
            if tool_call_count + len(raw_tool_calls) > self.max_tool_calls:
                raise NativeAgentUnavailable(
                    f"LiteLLM tool loop reached the configured {self.max_tool_calls}-call limit."
                )
            assistant_message = {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": raw_tool_calls,
            }
            messages.append(assistant_message)
            for call in raw_tool_calls:
                call_id, name, arguments = _tool_call_parts(call)
                tool_call_count += 1
                tool_calls.append({"server": "kongxing_sketchup", "tool": name})
                allowed = {str(tool.get("name", "")) for tool in tool_context.dynamic_tools}
                try:
                    if name not in allowed:
                        raise MCPCallError("The agent requested a tool outside this turn's Kongxing MCP allowlist.")
                    output = tool_context.dispatch(name, arguments)
                    if output.get("success") is False or output.get("isError") is True:
                        failed_tool_calls += 1
                except (ConnectorUnavailable, MCPCallError, OSError, ValueError, RuntimeError) as error:
                    failed_tool_calls += 1
                    output = {"success": False, "contentItems": [{"type": "inputText", "text": str(error)}]}
                text_result, images = _tool_result_parts(output)
                messages.append({"role": "tool", "tool_call_id": call_id, "content": text_result})
                if images:
                    content: list[dict[str, Any]] = [{"type": "text", "text": f"Visual readback from SketchUp tool {name}."}]
                    content.extend({"type": "image_url", "image_url": {"url": image}} for image in images)
                    messages.append({"role": "user", "content": content})

        return AgentTurnResult(
            thread_id=thread_id or f"litellm-{uuid.uuid4().hex}",
            reply=last_reply or "已完成这轮推演；模型操作记录已保存。",
            status="completed",
            tool_calls=tool_calls[-40:],
            model_name=selected_model,
            reasoning_effort=reasoning_effort or "provider-default",
            provider_name=self.provider_name,
            region=self.region,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round((time.monotonic() - started) * 1000),
            tool_call_count=tool_call_count,
            failed_tool_calls=failed_tool_calls,
        )


def _to_litellm_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool.get("inputSchema") or {"type": "object", "properties": {}},
        },
    }


def _response_message(response: Any) -> dict[str, Any]:
    try:
        message = response.choices[0].message
    except (AttributeError, IndexError, TypeError) as error:
        raise NativeAgentUnavailable("LiteLLM returned no chat-completion message.") from error
    if isinstance(message, dict):
        return message
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    return {
        "content": getattr(message, "content", None),
        "tool_calls": getattr(message, "tool_calls", None),
    }


def _message_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict) and item.get("type") == "text"
        ).strip()
    return ""


def _tool_call_parts(call: Any) -> tuple[str, str, dict[str, Any]]:
    if isinstance(call, dict):
        call_id = str(call.get("id") or uuid.uuid4().hex)
        function = call.get("function") or {}
    else:
        call_id = str(getattr(call, "id", "") or uuid.uuid4().hex)
        function = getattr(call, "function", None)
        if function is None:
            function = {}
        elif not isinstance(function, dict) and hasattr(function, "model_dump"):
            function = function.model_dump()
    name = str(function.get("name", ""))
    raw_arguments = function.get("arguments", "{}")
    if isinstance(raw_arguments, dict):
        arguments = raw_arguments
    else:
        try:
            arguments = json.loads(str(raw_arguments))
        except json.JSONDecodeError as error:
            raise NativeAgentUnavailable(f"LiteLLM returned invalid arguments for tool {name or '[unnamed]'}.") from error
    if not isinstance(arguments, dict):
        raise NativeAgentUnavailable(f"LiteLLM returned non-object arguments for tool {name or '[unnamed]'}.")
    return call_id, name, arguments


def _tool_result_parts(output: dict[str, Any]) -> tuple[str, list[str]]:
    clean = dict(output)
    images: list[str] = []
    content_items = clean.pop("contentItems", [])
    if isinstance(content_items, list):
        for item in content_items:
            if not isinstance(item, dict):
                continue
            image_url = item.get("imageUrl") or item.get("url")
            if item.get("type") in {"inputImage", "image"} and isinstance(image_url, str):
                images.append(image_url)
            elif item.get("type") in {"inputText", "text"}:
                clean.setdefault("text", "")
                clean["text"] += ("\n" if clean["text"] else "") + str(item.get("text", ""))
    return json.dumps(clean, ensure_ascii=False, default=str)[:60000], images


def _usage_from_response(response: Any) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return None, None
    if not isinstance(usage, dict) and hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    if not isinstance(usage, dict):
        return None, None
    input_count = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_count = usage.get("completion_tokens", usage.get("output_tokens"))
    return (
        input_count if isinstance(input_count, int) and input_count >= 0 else None,
        output_count if isinstance(output_count, int) and output_count >= 0 else None,
    )
