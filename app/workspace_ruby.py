from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from .project_ruby import ProjectRubyExecutor


MAX_WORKSPACE_RUBY_BYTES = 120_000


def resolve_workspace_ruby_path(agent_workspace: Path, relative_path: str) -> Path:
    """Resolve a project-authored Ruby file inside ``agent_workspace/scripts`` only."""
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("relative_path must name a Ruby file under scripts/.")
    normalized = relative_path.replace("\\", "/").strip()
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("Workspace Ruby paths must be relative and may not traverse parent directories.")
    if not pure.parts or pure.parts[0] != "scripts" or pure.suffix.lower() != ".rb":
        raise ValueError("Workspace Ruby files must live under scripts/ and end in .rb.")

    workspace = agent_workspace.expanduser().resolve()
    scripts_root = (workspace / "scripts").resolve()
    target = (workspace / Path(*pure.parts)).resolve()
    if not scripts_root.is_relative_to(workspace) or not target.is_relative_to(scripts_root):
        raise ValueError("Workspace Ruby path resolved outside the scripts directory.")
    if target.is_symlink():
        raise ValueError("Workspace Ruby source may not be a symbolic link.")
    return target


def run_workspace_ruby(
    executor: ProjectRubyExecutor,
    *,
    agent_workspace: Path,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Read a persistent agent-authored Ruby file and execute it through existing safeguards."""
    script_id = str(arguments.get("script_id") or "")
    relative_path = str(arguments.get("relative_path") or "")
    path = resolve_workspace_ruby_path(agent_workspace, relative_path)
    if not path.is_file():
        raise ValueError(f"Workspace Ruby file does not exist: {relative_path}")
    if path.stat().st_size > MAX_WORKSPACE_RUBY_BYTES:
        raise ValueError("Workspace Ruby file exceeds the 120 KB project-script limit.")
    source = path.read_text(encoding="utf-8")
    payload = {"script_id": script_id, "ruby_source": source,
               "update_mode": arguments.get("update_mode", "replace")}
    if "allowed_mutation_paths" in arguments:
        payload["allowed_mutation_paths"] = arguments["allowed_mutation_paths"]
    if "allow_full_rebuild" in arguments:
        payload["allow_full_rebuild"] = arguments["allow_full_rebuild"]
    # Host-only field: AgentToolSurface fingerprints reviewer KEEP paths before
    # the write and injects them here. It is intentionally absent from the
    # model-visible JSON schema, so the model cannot forge the expected state.
    if "_keep_expectations" in arguments:
        payload["_keep_expectations"] = arguments["_keep_expectations"]
    return executor.run(payload)
