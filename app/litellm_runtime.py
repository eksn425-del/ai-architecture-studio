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
from .modeling_quality import (
    CANONICAL_REVIEW_VIEWS,
    build_visual_critic_prompt,
    load_facade_schedule,
    parse_visual_critique_response,
    submit_visual_review,
)
from .reference_assets import discover_project_reference_images, image_data_url, reference_image_label
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError
from .workflow_context import WorkflowMode, ToolProfile, workflow_reference_categories


def requires_responses_tools(model: str) -> bool:
    # Official GPT-6 docs: Chat Completions supports conversation, not tools.
    return model.removeprefix("openai/") in {"gpt-6.1-sol", "gpt-6-astra"}


def _completion_with_transport(completion: Any, kwargs: dict[str, Any], selected_model: str) -> Any:
    """Use the same explicit DeepSeek proxy policy for builder and independent critic calls."""
    api_base = str(kwargs.get("api_base") or "")
    if selected_model.startswith("deepseek/") and api_base.rstrip("/") == "https://api.deepseek.com":
        import httpx
        from litellm.llms.custom_httpx.http_handler import HTTPHandler

        proxy_setting = os.environ.get("ARCH_STUDIO_API_TRUST_ENV", "").strip().lower()
        if proxy_setting not in {"", "0", "1", "false", "true"}:
            raise ValueError("ARCH_STUDIO_API_TRUST_ENV must be 0/1 or false/true.")
        trust_env = proxy_setting in {"1", "true"} if proxy_setting else os.name != "nt"
        with httpx.Client(trust_env=trust_env, timeout=240) as direct_client:
            return completion(**kwargs, client=HTTPHandler(client=direct_client))
    return completion(**kwargs)


class LiteLLMRuntime:
    """Optional LiteLLM chat-completion adapter for multimodal/function-call providers."""

    provider_name = "litellm"

    def __init__(self, runtime_root: Path, *, sketchup_mcp: ConfiguredSketchUpMCP | None = None,
                 model: str | None = None, region: str | None = None,
                 max_tool_calls: int = 48):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp or ConfiguredSketchUpMCP(timeout_seconds=180)
        self.tool_surface = AgentToolSurface(self.runtime_root, self.sketchup_mcp)
        self.model = model or os.environ.get("ARCH_STUDIO_API_MODEL") or os.environ.get("ARCH_STUDIO_CHINA_MODEL", "dashscope/qwen3-vl-flash")
        self.session_api_key = ""
        self.key_env = os.environ.get("ARCH_STUDIO_API_KEY_ENV", "DASHSCOPE_API_KEY")
        self.custom_api_base = os.environ.get("ARCH_STUDIO_API_BASE", "").strip()
        self.region = (region or os.environ.get("ARCH_STUDIO_CHINA_REGION", "international")).lower()
        if self.region not in {"international", "beijing"}:
            raise ValueError("ARCH_STUDIO_CHINA_REGION must be 'international' or 'beijing'.")
        self.max_tool_calls = max_tool_calls

    @property
    def credential_configured(self) -> bool:
        return bool(self.session_api_key or os.environ.get(self.key_env, "").strip())

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
        if self.custom_api_base:
            return self.custom_api_base
        if not self.model.startswith("dashscope/"):
            return ""
        if self.region == "beijing":
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    def respond(self, *, project_dir: Path, thread_id: str | None, prompt: str,
                mcp_enabled: bool, developer_instructions: str,
                model_path: Path | None = None, model_guid: str = "",
                ruby_enabled: bool = True, ruby_state: dict[str, dict[str, Any]] | None = None,
                architecture_skill_context: str = "", model: str | None = None,
                reasoning_effort: str | None = None, workflow_mode: WorkflowMode = "architecture_design",
                tool_profile: ToolProfile = "full") -> AgentTurnResult:
        if requires_responses_tools(model or self.model):
            raise NativeAgentUnavailable("当前 API 建模适配器使用 Chat Completions；GPT-6.1 Sol / Astra 的工具调用需要 Responses API。尚未开放此 API 建模路线，没有发送请求或自动切换模型。")
        api_key = self.session_api_key or os.environ.get(self.key_env, "").strip()
        if not api_key:
            raise NativeAgentUnavailable(
                f"LiteLLM credential {self.key_env} is not set; no provider request was sent."
            )
        try:
            from litellm import completion
        except Exception as error:
            raise NativeAgentUnavailable(
                f"模型 API 运行依赖加载失败（{type(error).__name__}）：{str(error).replace(api_key, '[credential hidden]')[:600]}。尚未发送供应商请求。"
            ) from error
        try:
            tool_context = self.tool_surface.prepare(
                project_dir=project_dir, mcp_enabled=mcp_enabled, model_path=model_path,
                model_guid=model_guid, ruby_enabled=ruby_enabled, ruby_state=ruby_state,
                tool_profile=tool_profile, workspace_tools_enabled=workflow_mode == "image_reconstruction",
            )
        except RuntimeError as error:
            raise NativeAgentUnavailable(str(error)) from error

        selected_model = model or self.model
        # The current Skill belongs once in the system context, not once per saved
        # user turn. Persistent notes/scripts and actual tool exchanges stay intact.
        skill = architecture_skill_context.strip()
        prompt_text = prompt.rstrip()
        system_text = developer_instructions + (("\n\n" + skill) if skill else "")
        reference_images = discover_project_reference_images(project_dir, categories=workflow_reference_categories(workflow_mode))
        if reference_images:
            prompt_text += "\n\n" + reference_image_label(reference_images, reconstruction=workflow_mode == "image_reconstruction")
            user_content: str | list[dict[str, Any]] = [{"type": "text", "text": prompt_text}]
            for index, image_path in enumerate(reference_images, 1):
                user_content.append({"type": "text", "text": f"Source image {index}: {image_path.parent.name}/{image_path.name}. Verify this view using visible landmarks."})
                user_content.append({"type": "image_url", "image_url": {"url": image_data_url(image_path)}})
        else:
            user_content = prompt_text
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_content},
        ]
        # Preserve actual tool messages across turns, not just a cosmetic thread id.
        resolved_thread = thread_id if thread_id and thread_id.startswith("litellm-") else f"litellm-{uuid.uuid4().hex}"
        if not resolved_thread.removeprefix("litellm-").isalnum():
            raise NativeAgentUnavailable("Invalid provider thread id.")
        history_dir = project_dir / "runtime" / "provider_sessions"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_path = history_dir / f"{resolved_thread}.json"
        def save_history() -> None:
            history_tmp = history_path.with_suffix(".tmp")
            history_tmp.write_text(json.dumps({"model": selected_model, "region": self.region,
                                               "messages": messages[1:]}, ensure_ascii=False), encoding="utf-8")
            history_tmp.replace(history_path)
        if history_path.exists():
            saved = json.loads(history_path.read_text(encoding="utf-8"))
            if saved.get("model") != selected_model or saved.get("region") != self.region:
                raise NativeAgentUnavailable("Provider/model changed; start a new provider session explicitly.")
            # Images already in real history remain visible to the model. Do not
            # append the identical six-image package again on every user reply.
            seen_images: set[str] = set()
            for old_message in saved["messages"]:
                content = old_message.get("content")
                if isinstance(content, list):
                    kept = []
                    for block in content:
                        url = block.get("image_url", {}).get("url") if block.get("type") == "image_url" else None
                        if url and url in seen_images:
                            if kept and kept[-1].get("type") == "text" and kept[-1].get("text", "").startswith("Source image "):
                                kept.pop()
                            continue
                        if url:
                            seen_images.add(url)
                        kept.append(block)
                    old_message["content"] = kept
            if isinstance(user_content, list):
                kept = []
                for block in user_content:
                    if block.get("type") == "image_url" and block["image_url"]["url"] in seen_images:
                        if kept and kept[-1].get("type") == "text" and kept[-1].get("text", "").startswith("Source image "):
                            kept.pop()
                        continue
                    kept.append(block)
                messages[1]["content"] = kept
            if skill:
                # Migrate exact duplicated Skill text from pre-existing sessions.
                for old_message in saved["messages"]:
                    if old_message.get("role") != "user":
                        continue
                    content = old_message.get("content")
                    if isinstance(content, str):
                        old_message["content"] = content.replace(skill, "")
                    elif isinstance(content, list):
                        for block in content:
                            if block.get("type") == "text":
                                block["text"] = block.get("text", "").replace(skill, "")
            messages = [messages[0], *saved["messages"], messages[1]]
        tools = [_to_litellm_tool(tool) for tool in tool_context.dynamic_tools]
        evidence_dir = project_dir / "runtime" / "agent_events"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / f"{uuid.uuid4().hex}.jsonl"
        def record(event: dict[str, Any]) -> None:
            with evidence_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        record({"event": "turn_input", "model": selected_model, "tool_profile": tool_profile,
                "workflow_mode": workflow_mode, "reference_categories": list(workflow_reference_categories(workflow_mode)),
                "reference_files": [p.relative_to(project_dir).as_posix() for p in reference_images],
                "input_types": ["text"] + ["image_url"] * len(reference_images),
                "tool_names": [t["name"] for t in tool_context.dynamic_tools]})
        started = time.monotonic()
        input_tokens: int | None = None
        output_tokens: int | None = None
        tool_calls: list[dict[str, str]] = []
        tool_call_count = 0
        failed_tool_calls = 0
        modeling_failure_streak = 0
        last_reply = ""
        quality_gate_nudges = 0
        max_quality_gate_nudges = 6


        def run_independent_visual_critic(builder_receipt: dict[str, Any]) -> dict[str, Any]:
            """Fresh no-tools visual judge modeled on 3DCodeBench's separated critic pass."""
            nonlocal input_tokens, output_tokens
            critic_reference_images = discover_project_reference_images(project_dir, categories=("reference",))
            source_labels = [path.relative_to(project_dir).as_posix() for path in critic_reference_images]
            schedule = load_facade_schedule(project_dir)
            system = build_visual_critic_prompt(source_labels, CANONICAL_REVIEW_VIEWS)
            system += (
                "\nYou are an INDEPENDENT host critic, not the Builder. Do not trust the Builder's self-review, "
                "tool success, filenames, or prose. Use only the attached source evidence, the CURRENT six SketchUp captures, "
                "and the compact facade schedule when supplied. Do not call tools and do not emit code. "
                "If evidence is insufficient or contradictory, use NEEDS_FIX: YES rather than guessing a PASS."
            )
            content: list[dict[str, Any]] = [{
                "type": "text",
                "text": (
                    "Independent visual acceptance pass. The facade schedule is advisory structured evidence; "
                    "user_confirmed entries outrank inferred entries.\n"
                    + ("Facade schedule:\n" + json.dumps(schedule, ensure_ascii=False)[:12000] if schedule else "Facade schedule: unavailable.")
                ),
            }]
            for index, image_path in enumerate(critic_reference_images, 1):
                content.append({"type": "text", "text": f"SOURCE {index}: {image_path.name}"})
                content.append({"type": "image_url", "image_url": {"url": image_data_url(image_path)}})
            for view_name in CANONICAL_REVIEW_VIEWS:
                view_info = builder_receipt.get("views", {}).get(view_name, {})
                relative = view_info.get("path") if isinstance(view_info, dict) else None
                if not isinstance(relative, str):
                    raise ValueError(f"Independent critic is missing current {view_name} evidence.")
                image_path = (project_dir / relative).resolve()
                if not image_path.is_file() or not image_path.is_relative_to(project_dir.resolve()):
                    raise ValueError(f"Independent critic cannot read current {view_name} evidence.")
                content.append({"type": "text", "text": f"CURRENT SKETCHUP {view_name.upper()}: {relative}"})
                content.append({"type": "image_url", "image_url": {"url": image_data_url(image_path)}})

            critic_kwargs: dict[str, Any] = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": content},
                ],
                "api_key": api_key,
                "timeout": 240,
                "max_retries": 0,
                "num_retries": 0,
            }
            if self.api_base:
                critic_kwargs["api_base"] = self.api_base
            if selected_model.startswith("zai/"):
                critic_kwargs["allowed_openai_params"] = ["max_retries"]
            if reasoning_effort in {"low", "high", "max"}:
                if selected_model.startswith("zai/"):
                    critic_kwargs["extra_body"] = {"thinking": {"type": "enabled"}, "reasoning_effort": reasoning_effort}
                else:
                    critic_kwargs["reasoning_effort"] = reasoning_effort
                if selected_model.startswith("deepseek/"):
                    critic_kwargs["extra_body"] = {"reasoning_effort": reasoning_effort}

            critic_started = time.monotonic()
            record({
                "event": "independent_visual_critic_started",
                "model": selected_model,
                "source_images": len(critic_reference_images),
                "review_views": len(CANONICAL_REVIEW_VIEWS),
                "schedule_present": bool(schedule),
            })
            reviewer_status = "ok"
            try:
                critic_response = _completion_with_transport(completion, critic_kwargs, selected_model)
                critic_usage = _usage_from_response(critic_response)
                input_tokens = (input_tokens or 0) + critic_usage[0] if critic_usage[0] is not None else input_tokens
                output_tokens = (output_tokens or 0) + critic_usage[1] if critic_usage[1] is not None else output_tokens
                critic_text = _message_content(_response_message(critic_response))
                parsed = parse_visual_critique_response(critic_text)
                if parsed.malformed or parsed.needs_fix is None:
                    raise ValueError("Independent critic returned an unparseable quality envelope.")
                record({
                    "event": "independent_visual_critic_response",
                    "model": selected_model,
                    "latency_ms": round((time.monotonic() - critic_started) * 1000),
                    "input_tokens": critic_usage[0],
                    "output_tokens": critic_usage[1],
                    "needs_fix": parsed.needs_fix,
                    "issue_count": len(parsed.issues),
                })
            except Exception as error:
                reviewer_status = "failed"
                safe_error = str(error).replace(api_key, "[credential hidden]")[:1000]
                record({
                    "event": "independent_visual_critic_failed",
                    "model": selected_model,
                    "latency_ms": round((time.monotonic() - critic_started) * 1000),
                    "detail": safe_error,
                })
                critic_text = (
                    "NEEDS_FIX: YES\n"
                    "<assessment>Independent host critic could not produce a valid review; visual acceptance remains pending.</assessment>\n"
                    "<issue priority=\"1\" view=\"unspecified\">problem: independent visual review unavailable\n"
                    "action: stop geometry writes and report PARTIAL until the critic can review current evidence</issue>\n"
                    "<keep>current verified geometry</keep>"
                )

            review_args = {
                "views": {
                    name: builder_receipt["views"][name]["path"]
                    for name in CANONICAL_REVIEW_VIEWS
                },
                "critique": critic_text,
                "reviewer": {
                    "kind": "independent_host_critic",
                    "status": reviewer_status,
                    "provider": self.provider_name,
                    "model": selected_model,
                },
            }
            independent = submit_visual_review(project_dir, ruby_state or {}, review_args)
            independent["builder_self_review"] = {
                "needs_fix": builder_receipt.get("needs_fix"),
                "assessment": builder_receipt.get("assessment"),
            }
            quality_file = project_dir / "runtime" / "agent_workspace" / "qa" / "visual_review.json"
            quality_file.write_text(json.dumps(independent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return independent

        def interrupted(detail: str) -> NativeAgentUnavailable:
            # Preserve real usage/checkpoint state even when a bounded turn stops.
            save_history()
            error = NativeAgentUnavailable(detail)
            error.partial_result = AgentTurnResult(
                thread_id=resolved_thread, reply="本轮中断；已有工作与记录已保留。",
                status="interrupted", tool_calls=tool_calls[-40:], model_name=selected_model,
                reasoning_effort=reasoning_effort or "provider-default",
                provider_name=self.provider_name, region=self.region,
                input_tokens=input_tokens, output_tokens=output_tokens,
                latency_ms=round((time.monotonic() - started) * 1000),
                tool_call_count=tool_call_count, failed_tool_calls=failed_tool_calls,
            )
            return error

        while True:
            request_messages = _current_visual_context(messages)
            kwargs: dict[str, Any] = {
                "model": selected_model,
                "messages": request_messages,
                "api_key": api_key,
                "timeout": 240,
                # A user-visible turn must not silently wait through several
                # full SDK timeout/retry cycles before reporting a failure.
                "max_retries": 0,
                "num_retries": 0,
            }
            if self.api_base:
                kwargs["api_base"] = self.api_base
            if selected_model.startswith("zai/"):
                # The installed ZAI map omits this SDK option. Use LiteLLM's
                # documented override so zero reaches the OpenAI SDK client.
                kwargs["allowed_openai_params"] = ["max_retries"]
            if reasoning_effort in {"low", "high", "max"}:
                if selected_model.startswith("zai/"):
                    # ZAI's current LiteLLM mapping does not advertise reasoning_effort.
                    kwargs["extra_body"] = {"thinking": {"type": "enabled"}, "reasoning_effort": reasoning_effort}
                else:
                    kwargs["reasoning_effort"] = reasoning_effort
                if selected_model.startswith("deepseek/"):
                    # Installed LiteLLM enables thinking but consumes effort in its mapping.
                    # Forward the vendor field too so measured Low is actually Low on the wire.
                    kwargs["extra_body"] = {"reasoning_effort": reasoning_effort}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                if not selected_model.startswith("zai/"):
                    kwargs["parallel_tool_calls"] = False
            try:
                request_started = time.monotonic()
                record({"event": "provider_started", "requested_model": selected_model, "reasoning_effort": reasoning_effort or "provider-default",
                    "context_messages": len(request_messages), "redundant_images_removed": _image_count(messages) - _image_count(request_messages)})
                response = _completion_with_transport(completion, kwargs, selected_model)
            except Exception as error:
                safe_error = str(error).replace(api_key, "[credential hidden]")
                record({"event": "provider_failed", "model": selected_model, "detail": safe_error[:1000]})
                raise interrupted(f"LiteLLM request failed for {selected_model}: {safe_error}") from None
            usage = _usage_from_response(response)
            record({"event": "provider_response", "requested_model": selected_model,
                    "response_model": getattr(response, "model", None), "reasoning_effort": reasoning_effort or "provider-default",
                    "latency_ms": round((time.monotonic() - request_started) * 1000),
                    "input_tokens": usage[0], "output_tokens": usage[1]})
            input_tokens = (input_tokens or 0) + usage[0] if usage[0] is not None else input_tokens
            output_tokens = (output_tokens or 0) + usage[1] if usage[1] is not None else output_tokens
            message = _response_message(response)
            raw_tool_calls = message.get("tool_calls") or []
            last_reply = _message_content(message)
            if not raw_tool_calls:
                quality = tool_context.quality_state
                gated_reconstruction = (
                    workflow_mode == "image_reconstruction"
                    and mcp_enabled
                    and tool_profile == "reconstruction_coding"
                    and int(quality.get("writes", 0) or 0) > 0
                )
                if gated_reconstruction:
                    review = quality.get("review")
                    writes = int(quality.get("writes", 0) or 0)
                    write_limit = int(quality.get("write_limit", 0) or 0)
                    gate_prompt = ""
                    if not isinstance(review, dict) and quality_gate_nudges < max_quality_gate_nudges:
                        gate_prompt = (
                            "HOST QUALITY GATE: You have committed geometry but have not submitted a CURRENT six-view review. "
                            "Do not finish yet and do not write geometry again. Capture six distinct current-revision views "
                            "(front, rear, left, right, roof, oblique), compare them against the attached source evidence, "
                            "then call sketchup_submit_visual_review with the actual returned output paths. "
                            "Use NEEDS_FIX plus at most three high-impact issues and a KEEP list."
                        )
                    elif (
                        isinstance(review, dict)
                        and review.get("needs_fix") is True
                        and review.get("reviewer", {}).get("status") != "failed"
                        and writes < write_limit
                        and quality_gate_nudges < max_quality_gate_nudges
                    ):
                        gate_prompt = (
                            "HOST QUALITY GATE: The current independent visual review says NEEDS_FIX: YES and writer budget remains. "
                            "Apply ONE targeted correction pass to the named affected groups only, preserve the KEEP geometry, "
                            "then recapture all six current views and submit a new visual review. Do not use a full-root replace "
                            "unless the review explicitly shows the whole baseline is invalid."
                        )
                    if gate_prompt:
                        messages.append({
                            "role": "assistant",
                            "content": last_reply or "已完成当前步骤，准备质量检查。",
                        })
                        messages.append({"role": "user", "content": gate_prompt})
                        quality_gate_nudges += 1
                        record({
                            "event": "quality_gate_nudge",
                            "nudge": quality_gate_nudges,
                            "writes": writes,
                            "write_limit": write_limit,
                            "has_review": isinstance(review, dict),
                            "needs_fix": review.get("needs_fix") if isinstance(review, dict) else None,
                        })
                        save_history()
                        continue

                    if not isinstance(review, dict):
                        last_reply = (
                            (last_reply + "\n\n") if last_reply else ""
                        ) + "当前模型已提交，但本轮没有完成可验证的当前六视图质量审查，因此还不能判定还原质量通过。"
                    elif review.get("needs_fix") is True:
                        reviewer_failed = review.get("reviewer", {}).get("status") == "failed"
                        last_reply = (
                            (last_reply + "\n\n") if last_reply else ""
                        ) + (
                            "独立视觉审查本轮未成功完成；已保留当前验证模型并停止盲目写入，质量按 PARTIAL 保留。"
                            if reviewer_failed else
                            "当前独立六视图审查仍为 NEEDS_FIX；本轮修正预算已用完或质量门已停止继续写入，剩余问题按 PARTIAL 保留。"
                        )
                break
            if tool_call_count + len(raw_tool_calls) > self.max_tool_calls:
                raise interrupted(
                    f"LiteLLM tool loop reached the configured {self.max_tool_calls}-call limit."
                )
            assistant_message = {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": raw_tool_calls,
            }
            # DeepSeek thinking tool turns require this field on subsequent calls.
            if message.get("reasoning_content") is not None:
                assistant_message["reasoning_content"] = message["reasoning_content"]
            messages.append(assistant_message)
            for call in raw_tool_calls:
                call_id, name, arguments = _tool_call_parts(call)
                tool_call_count += 1
                tool_calls.append({"server": "kongxing_sketchup", "tool": name})
                record({"event": "tool_started", "tool": name})
                allowed = {str(tool.get("name", "")) for tool in tool_context.dynamic_tools}
                try:
                    if name not in allowed:
                        raise MCPCallError("The agent requested a tool outside this turn's Kongxing MCP allowlist.")
                    output = tool_context.dispatch(name, arguments)
                    if (
                        name == "sketchup_submit_visual_review"
                        and output.get("success") is not False
                        and isinstance(output.get("visual_review"), dict)
                    ):
                        independent_review = run_independent_visual_critic(output["visual_review"])
                        tool_context.quality_state["review"] = independent_review
                        output["visual_review"] = independent_review
                        output["contentItems"] = [{
                            "type": "inputText",
                            "text": json.dumps({"visual_review": independent_review}, ensure_ascii=False),
                        }]
                    if output.get("success") is False or output.get("isError") is True:
                        failed_tool_calls += 1
                except (ConnectorUnavailable, MCPCallError, OSError, ValueError, RuntimeError) as error:
                    failed_tool_calls += 1
                    output = {"success": False, "contentItems": [{"type": "inputText", "text": str(error)}]}
                text_result, images = _tool_result_parts(output)
                succeeded = output.get("success", not output.get("isError", False))
                event = {"event": "tool_result", "tool": name, "success": succeeded, "image_count": len(images)}
                if not succeeded:
                    event["error"] = text_result.replace(api_key, "[credential hidden]")[:1500]
                record(event)
                if name == "sketchup_run_workspace_ruby":
                    modeling_failure_streak = 0 if succeeded else modeling_failure_streak + 1
                messages.append({"role": "tool", "tool_call_id": call_id, "content": text_result})
                if images:
                    content: list[dict[str, Any]] = [{"type": "text", "text": f"Visual readback from SketchUp tool {name}."}]
                    content.extend({"type": "image_url", "image_url": {"url": image}} for image in images)
                    messages.append({"role": "user", "content": content})
            # Checkpoint complete function-call exchanges, including failed attempts.
            # Repeated full-script generation must not silently spend the whole call budget.
            save_history()
            if modeling_failure_streak >= 3:
                record({"event": "retry_budget_exhausted", "failed_modeling_calls": modeling_failure_streak})
                raise interrupted(
                    "建模脚本连续 3 次执行失败，本轮已停止重试以避免重复消耗。"
                    "已有模型和完整工具记录已保留；请检查错误、修订同一脚本后继续。"
                )

        final_message = {"role": "assistant", "content": last_reply}
        if message.get("reasoning_content") is not None:
            final_message["reasoning_content"] = message["reasoning_content"]
        messages.append(final_message)
        save_history()
        return AgentTurnResult(
            thread_id=resolved_thread,
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


def _image_count(messages: list[dict[str, Any]]) -> int:
    return sum(block.get("type") == "image_url" for message in messages
               if isinstance(message.get("content"), list) for block in message["content"])


def _current_visual_context(messages: list[dict[str, Any]], *, readback_images: int = 6) -> list[dict[str, Any]]:
    """Deduplicate source images and drop obsolete readbacks on the wire.

    Keep tool exchanges/IDs, reasoning fields, user inputs and source images. Shorten only old oversized tool-result text; keep the six latest tool results intact.
    The full local history remains available for audit/recovery. This is a small
    product-specific filter, not a replacement for provider compaction.
    """
    # Pictures from before the most recent successful geometry execution show
    # an older model. Keep their audit text, but never present them as current QA.
    geometry_calls: set[str] = set()
    geometry_boundary = -1
    for index, message in enumerate(messages):
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or []:
                if call.get("function", {}).get("name") in {"sketchup_run_workspace_ruby", "sketchup_run_project_ruby"}:
                    geometry_calls.add(call.get("id", ""))
        elif message.get("role") == "tool" and message.get("tool_call_id") in geometry_calls:
            try:
                outcome = json.loads(message.get("content") or "{}")
            except (ValueError, TypeError):
                continue
            if isinstance(outcome, dict) and outcome.get("success") is True:
                geometry_boundary = index
    remaining = readback_images
    recent_tools = 6
    source_urls: set[str] = set()
    result = []
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        content = message.get("content")
        if message.get("role") == "tool":
            recent_tools -= 1
            if recent_tools < 0 and isinstance(content, str) and len(content) > 8000:
                # Keep exchange IDs and complete on-disk audit history. Old
                # source/readback dumps can be reread through workspace tools;
                # they must not grow every subsequent request without bound.
                result.append({**message, "content": content[:2000] +
                    "\n[Historical tool output shortened for active context. Full result remains in provider session history; "
                    "reread the current workspace file/model before relying on omitted details.]\n" + content[-2000:]})
                continue
        is_readback = (message.get("role") == "user" and isinstance(content, list)
                       and bool(content) and content[0].get("type") == "text"
                       and content[0].get("text", "").startswith("Visual readback from SketchUp tool "))
        if not is_readback:
            if message.get("role") == "user" and isinstance(content, list):
                kept_source = []
                duplicates = 0
                message_urls: set[str] = set()
                for block in content:
                    url = block.get("image_url", {}).get("url") if block.get("type") == "image_url" else None
                    if isinstance(url, str):
                        if url in source_urls:
                            duplicates += 1
                            continue
                        message_urls.add(url)
                    kept_source.append(block)
                source_urls.update(message_urls)
                if duplicates:
                    kept_source.append({"type": "text", "text": "Repeated source image omitted from active context; identical pixels are included in a newer reference message. Original message and full source remain in project history."})
                    result.append({**message, "content": kept_source})
                    continue
            result.append(message)
            continue
        kept = []
        omitted = 0
        for block in reversed(content):
            if block.get("type") == "image_url":
                if remaining <= 0 or index < geometry_boundary:
                    omitted += 1
                    continue
                remaining -= 1
            kept.append(block)
        kept.reverse()
        if omitted:
            kept.append({"type": "text", "text": "Earlier generated screenshot omitted from active context; it is historical evidence, not the current model. Use current screenshots or capture the required view again."})
        result.append({**message, "content": kept})
    return list(reversed(result))


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
