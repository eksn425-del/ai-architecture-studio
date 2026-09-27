from __future__ import annotations

import hashlib
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.architecture_skill import UPSTREAM_REVISION  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import AgentSession, ProjectContext, QualityBenchmarkRun  # noqa: E402
from app.store import ProjectStore, utc_now  # noqa: E402


BENCHMARK_PATH = REPO_ROOT / "examples" / "model_router_v1" / "input.json"
FOLLOWUP = (
    "请只把南侧主入口前的公共步道有效宽度增加 0.5 m，保持现有建筑体量和其它几何的位置、尺寸不变。"
    "先读取当前模型确认已有入口路径，再在同一命名项目根内增量修改；修改后查看截图和模型状态并简述结果。"
)


def _require_ok(response: Any, action: str) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception as error:
        raise RuntimeError(f"{action} returned HTTP {response.status_code} without JSON.") from error
    if not response.is_success:
        detail = data.get("detail", "request failed") if isinstance(data, dict) else "request failed"
        raise RuntimeError(f"{action} failed (HTTP {response.status_code}): {detail}")
    if not isinstance(data, dict):
        raise RuntimeError(f"{action} returned an unexpected response.")
    return data


def _tool_summary(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": agent.get("model"),
        "provider": agent.get("provider"),
        "tier": agent.get("tier"),
        "region": agent.get("region"),
        "reasoning_effort": agent.get("reasoning_effort"),
        "input_tokens": agent.get("input_tokens"),
        "output_tokens": agent.get("output_tokens"),
        "latency_ms": agent.get("latency_ms"),
        "tool_call_count": agent.get("tool_call_count"),
        "failed_tool_calls": agent.get("failed_tool_calls"),
        "routing_reason": agent.get("routing_reason"),
    }


def _find_sketchup_version(value: Any) -> str:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold().replace("_", "") in {"sketchupversion", "version"} and isinstance(item, (str, int, float)):
                return str(item)
        for item in value.values():
            found = _find_sketchup_version(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_sketchup_version(item)
            if found:
                return found
    return ""


def _launch_and_wait(app: Any, runtime_root: Path, project_id: str) -> Path:
    project_dir = runtime_root / "projects" / project_id
    model_dir = (project_dir / "outputs" / "model").resolve()
    try:
        app.state.sketchup.ping()
        identity = app.state.sketchup.get_active_model_identity()
        active_path = Path(str(identity.get("model_path") or "")).resolve()
        if (
            active_path.is_relative_to(model_dir)
            and active_path.name.lower().startswith("blank-disposable-")
            and identity.get("model_guid")
            and not identity.get("active_context")
        ):
            return active_path
    except Exception:
        pass
    powershell = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
    helper = REPO_ROOT / "scripts" / "open_blank_sketchup.ps1"
    completed = subprocess.run(
        [
            powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(helper),
            "-ProjectId", project_id, "-RuntimeRoot", str(runtime_root.resolve()),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise RuntimeError(detail or "Could not open a new blank disposable SketchUp copy.")
    deadline = time.monotonic() + 90
    last_error = "Kongxing bridge did not respond."
    while time.monotonic() < deadline:
        try:
            app.state.sketchup.ping()
            identity = app.state.sketchup.get_active_model_identity()
            active_path = Path(str(identity.get("model_path") or "")).resolve()
            if (
                active_path.is_relative_to(model_dir)
                and active_path.name.lower().startswith("blank-disposable-")
                and identity.get("model_guid")
                and not identity.get("active_context")
            ):
                return active_path
            last_error = "SketchUp's active model is not this benchmark project's blank disposable copy."
        except Exception as error:
            last_error = str(error)
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for the project's local SketchUp copy: {last_error}")


def _close_active_disposable_sketchup(app: Any, runtime_root: Path, project_id: str) -> None:
    identity = app.state.sketchup.get_active_model_identity()
    active_path = Path(str(identity.get("model_path") or "")).resolve()
    project_dir = (runtime_root / "projects" / project_id).resolve()
    model_dir = (project_dir / "outputs" / "model").resolve()
    checkpoint = model_dir / "fast-assembly-agent.skp"
    if (
        not active_path.is_relative_to(model_dir)
        or not active_path.name.lower().startswith("blank-disposable-")
        or not checkpoint.is_file()
    ):
        raise RuntimeError("Refusing to close SketchUp: the active document is not this completed disposable benchmark model.")
    stem = active_path.stem
    if not stem.startswith("blank-disposable-") or not stem.replace("-", "").isalnum():
        raise RuntimeError("Refusing to close SketchUp: the active benchmark window name did not pass validation.")
    powershell = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
    command = (
        "$ErrorActionPreference='Stop'; "
        f"$modelTitle='{stem}'; "
        "$targets=Get-Process SketchUp -ErrorAction SilentlyContinue | "
        "Where-Object { $_.MainWindowTitle -like ($modelTitle + '* - SketchUp*') }; "
        "if ($targets.Count -ne 1) { throw 'Expected exactly one verified benchmark SketchUp window.' }; "
        "Stop-Process -Id $targets.Id -Force"
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-800:]
        raise RuntimeError(detail or "Could not close the completed disposable SketchUp window.")


def _run_variant(*, run_id: str, source: dict[str, Any], variant: str, tier: str,
                 close_after: bool = False) -> dict[str, Any]:
    benchmark_input = source["input"]
    context = ProjectContext.model_validate(benchmark_input["context"])
    project_id = context.project_id
    runtime_root = REPO_ROOT / "runtime" / f"model-router-benchmark-{run_id}" / variant
    store = ProjectStore(runtime_root)
    if (store.project_dir(project_id) / "state" / "project_context.json").is_file():
        previous = store.load_context(project_id)
        if previous.project_name != context.project_name or previous.brief.summary != context.brief.summary:
            raise RuntimeError("An existing benchmark project does not match the committed synthetic input.")
    else:
        store.create_project(context)
    app = create_app(runtime_root=runtime_root)
    prompt_mode = "economy"
    if tier == "premium":
        prompt_mode = "premium"

    with TestClient(app) as client:
        active_model_path = _launch_and_wait(app, runtime_root, project_id)
        start = _require_ok(
            client.post(
                f"/api/projects/{project_id}/agent/session",
                json={"confirm_disposable_model": True},
            ),
            "Start local model session",
        )
        if start["session"]["model_path"].split("/")[-1] != active_model_path.name:
            raise RuntimeError("The API session did not bind to the newly opened disposable model.")

        request_context = {
            "brief": benchmark_input["brief"],
            "site_note": benchmark_input["site_note"],
            "user_intent": benchmark_input["user_intent"],
        }
        first = _require_ok(
            client.post(
                f"/api/projects/{project_id}/conversation",
                json={"message": benchmark_input["user_message"], "tier": prompt_mode, **request_context},
            ),
            "Run identical architecture benchmark",
        )
        first_agent = first["agent"]

        # This is a controlled same-model comparison: retain the selected tier for
        # the follow-up even if the product has marked a rescue as pending.
        session = store.load_state(project_id, "agent_session.json", AgentSession)
        rescue_was_pending = session.premium_rescue_pending
        if rescue_was_pending and tier == "economy":
            session.premium_rescue_pending = False
            store.save_state(project_id, session, "agent_session.json")

        followup_data: dict[str, Any] | None = None
        followup_error = ""
        try:
            followup_data = _require_ok(
                client.post(
                    f"/api/projects/{project_id}/conversation",
                    json={"message": FOLLOWUP, "tier": prompt_mode, **request_context},
                ),
                "Run same-model follow-up",
            )
        except Exception as error:
            followup_error = str(error)

        project_dir = store.project_dir(project_id)
        render_dir = project_dir / "outputs" / "renders"
        render_dir.mkdir(parents=True, exist_ok=True)
        plan_path = render_dir / f"router-{variant}-plan.png"
        exterior_path = render_dir / f"router-{variant}-exterior.png"
        capture_findings: list[str] = []
        try:
            app.state.sketchup.set_camera([30, 24, 150], [30, 24, 0], up_m=[0, 1, 0])
            app.state.sketchup.capture_view(plan_path, zoom_extents=False)
            if not plan_path.is_file():
                capture_findings.append("Matched plan screenshot was not written.")
        except Exception as error:
            capture_findings.append(f"Matched plan view capture failed: {error}")
        try:
            app.state.sketchup.set_camera([94, -85, 77], [30, 24, 8])
            app.state.sketchup.capture_view(exterior_path, zoom_extents=False)
            if not exterior_path.is_file():
                capture_findings.append("Matched exterior screenshot was not written.")
        except Exception as error:
            capture_findings.append(f"Matched exterior view capture failed: {error}")

        final_session = store.load_state(project_id, "agent_session.json", AgentSession)
        turns = [first_agent]
        if followup_data:
            turns.append(followup_data["agent"])
        images = [
            _relative(project_dir, path)
            for path in (plan_path, exterior_path)
            if path.is_file()
        ]
        all_tool_calls = (first_agent.get("tool_calls") or []) + ((followup_data or {}).get("agent", {}).get("tool_calls") or [])
        total_input = sum(item["input_tokens"] for item in turns) if all(isinstance(item.get("input_tokens"), int) for item in turns) else None
        total_output = sum(item["output_tokens"] for item in turns) if all(isinstance(item.get("output_tokens"), int) for item in turns) else None
        run = QualityBenchmarkRun(
            benchmark_id="cost-quality-router-v1",
            variant=variant,
            project_id=project_id,
            model=first_agent["model"],
            reasoning_effort=first_agent["reasoning_effort"] if first_agent["reasoning_effort"] in {"low", "medium", "high", "xhigh", "max"} else "low",
            input_sha256=source["input_sha256"],
            model_guid=final_session.model_guid,
            sketchup_version=_find_sketchup_version(final_session.last_model_info),
            architecture_skill=True,
            ruby_enabled=True,
            skill_revision=UPSTREAM_REVISION,
            script_ids=list(final_session.ruby_state),
            screenshots=images,
            tool_calls=all_tool_calls,
            metrics={
                "turns": [_tool_summary(item) for item in turns],
                "same_model_followup": followup_data is not None,
                "same_model_followup_error": followup_error,
                "premium_rescue_was_pending_after_initial_economy_turn": rescue_was_pending,
                "matched_views": {"plan": plan_path.is_file(), "exterior": exterior_path.is_file()},
                "capture_findings": capture_findings,
                "self_check_and_correction_requested": True,
                "self_correction_count_is_pending_visual_review": True,
                "input_json_sha256": hashlib.sha256(BENCHMARK_PATH.read_bytes()).hexdigest(),
                "input": "examples/model_router_v1/input.json",
            },
            provider=first_agent.get("provider", ""),
            region=first_agent.get("region", ""),
            input_tokens=total_input,
            output_tokens=total_output,
            latency_ms=sum(int(item.get("latency_ms") or 0) for item in turns),
            tool_call_count=sum(int(item.get("tool_call_count") or 0) for item in turns),
            failed_tool_calls=sum(int(item.get("failed_tool_calls") or 0) for item in turns),
            inspected=any(item.get("tool") in {"sketchup_export_view_image", "sketchup_run_project_ruby"} for item in all_tool_calls),
            correction_count=0,
            same_model_followup=followup_data is not None,
            status="complete" if followup_data and len(images) == 2 else "partial",
            notes=[
                "Synthetic public benchmark; disposable SketchUp copy only.",
                "Same architecture Skill revision, Kongxing tool schemas, guarded project Ruby, input brief, user request, and follow-up prompt.",
                "Token usage is recorded only when returned by the provider runtime; no cost is inferred.",
            ] + capture_findings + ([followup_error] if followup_error else []),
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        store.save_benchmark_run(run)
        if close_after:
            _close_active_disposable_sketchup(app, runtime_root, project_id)
        return {
            "variant": variant,
            "runtime_root": str(runtime_root),
            "active_model": active_model_path.name,
            "run": run.model_dump(mode="json"),
            "reply": first["reply"],
            "followup_reply": (followup_data or {}).get("reply", ""),
        }


def _relative(project_dir: Path, target: Path) -> str:
    return target.resolve().relative_to(project_dir.resolve()).as_posix()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not BENCHMARK_PATH.is_file():
        raise SystemExit(f"Sanitized benchmark input is missing: {BENCHMARK_PATH}")
    source = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description="Run the same synthetic SketchUp benchmark through the selected model-router tier.")
    parser.add_argument("--run-id", help="Reuse a ten-character benchmark runtime ID when resuming a partial local run.")
    parser.add_argument("--variant", choices=("all", "luna", "astra"), default="all")
    arguments = parser.parse_args()
    run_id = arguments.run_id or uuid.uuid4().hex[:10]
    if len(run_id) != 10 or any(char not in "0123456789abcdef" for char in run_id):
        raise SystemExit("--run-id must be ten lowercase hexadecimal characters.")

    os.environ["ARCH_STUDIO_ECONOMY_PROVIDER"] = "codex"
    os.environ["ARCH_STUDIO_ECONOMY_MODEL"] = "gpt-6-luna"
    os.environ["ARCH_STUDIO_PREMIUM_MODEL"] = "gpt-6-astra"
    os.environ["ARCH_STUDIO_CODEX_REASONING_EFFORT"] = "low"
    variants = (
        [("luna", "economy"), ("astra", "premium")]
        if arguments.variant == "all"
        else [("luna", "economy")] if arguments.variant == "luna"
        else [("astra", "premium")]
    )
    results = [
        _run_variant(
            run_id=run_id, source=source, variant=variant, tier=tier,
            close_after=arguments.variant == "all" and variant == "luna",
        )
        for variant, tier in variants
    ]
    print(json.dumps({
        "benchmark_input_sha256": source["input_sha256"],
        "benchmark_json_sha256": hashlib.sha256(BENCHMARK_PATH.read_bytes()).hexdigest(),
        "qwen_live_key_present": bool(os.environ.get("DASHSCOPE_API_KEY", "").strip()),
        "results": results,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
