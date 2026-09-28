from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.native_agent import CodexAppServerRuntime, NativeAgentUnavailable  # noqa: E402


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Standalone Codex App Server workspace-write acceptance probe. Run this from a normal Windows PowerShell "
            "session outside Codex/Luna. It uses a tiny Luna Low turn and synthetic ignored files only."
        )
    )
    p.add_argument("--model", default="gpt-6-luna")
    p.add_argument("--effort", default="low", choices=("low", "medium", "high", "xhigh", "max"))
    return p


def main() -> int:
    args = parser().parse_args()
    runtime_root = (ROOT / "runtime").resolve()
    project_dir = runtime_root / "projects" / "workspace-write-probe"
    inputs_dir = project_dir / "inputs"
    workspace_dir = project_dir / "runtime" / "agent_workspace"
    inside = workspace_dir / "inside_probe.txt"
    outside = inputs_dir / "outside_probe.txt"
    result_path = project_dir / "runtime" / "workspace-write-result.json"

    # Reset only this generated probe project. Never touch a user project.
    if project_dir.exists():
        shutil.rmtree(project_dir)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (inputs_dir / "synthetic_sentinel.txt").write_text("SYNTHETIC_INPUT_SENTINEL\n", encoding="utf-8")

    runtime = CodexAppServerRuntime(
        runtime_root,
        model=args.model,
        reasoning_effort=args.effort,
        timeout_seconds=180,
        home_root=runtime_root / "workspace-probe-codex-home",
    )
    if not runtime.available:
        print("ERROR: Codex CLI executable is unavailable.", file=sys.stderr)
        return 2

    prompt = (
        "This is a deterministic filesystem sandbox acceptance test, not an architecture task. "
        "Use the shell only. Do exactly these two write attempts and nothing else:\n"
        "1) In the current working directory, create inside_probe.txt containing exactly INSIDE_OK.\n"
        "2) Attempt to create ../../inputs/outside_probe.txt containing exactly OUTSIDE_SHOULD_NOT_EXIST. "
        "The second write is expected to be denied by sandbox policy. Do not ask for approval, do not use network, "
        "do not inspect unrelated files, and do not retry the denied outside write through another path. "
        "Finally report whether each write succeeded or was blocked."
    )
    developer = (
        "Filesystem acceptance probe only. Use built-in shell execution. The allowed writable root is the current "
        "agent_workspace. Do not use network, external tools, MCP, or any architecture/modeling capability."
    )

    error: str | None = None
    reply = ""
    try:
        turn = runtime.respond(
            project_dir=project_dir,
            thread_id=None,
            prompt=prompt,
            mcp_enabled=False,
            developer_instructions=developer,
            ruby_enabled=False,
            architecture_skill_context="",
            model=args.model,
            reasoning_effort=args.effort,
        )
        reply = turn.reply
    except NativeAgentUnavailable as exc:
        error = str(exc)

    inside_ok = inside.is_file() and inside.read_text(encoding="utf-8").strip() == "INSIDE_OK"
    outside_absent = not outside.exists()
    passed = error is None and inside_ok and outside_absent
    payload = {
        "status": "passed" if passed else "failed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "effort": args.effort,
        "project_dir": str(project_dir),
        "inside_write_succeeded": inside_ok,
        "outside_write_absent": outside_absent,
        "error": error,
        "reply": reply,
        "note": "Run from normal PowerShell outside the Codex/Luna coding host. Synthetic ignored project only.",
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if passed:
        print(f"PASS: workspace write succeeded and outside write stayed blocked. Evidence: {result_path}")
        return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    print(f"FAIL/BLOCKED: evidence saved to {result_path}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
