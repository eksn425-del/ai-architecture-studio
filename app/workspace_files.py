"""Minimal file glue for providers without Codex's built-in coding tools."""
from pathlib import Path, PurePosixPath
import re

MAX_TEXT_BYTES = 120000


def workspace_file_tools() -> list[dict]:
    schema = {"type": "string", "description": "Project workspace path: notes/*.md, qa/*.md or scripts/*.rb"}
    return [
        {"type": "function", "name": "workspace_read", "description": "List persistent workspace files, or read one UTF-8 note/Ruby file.",
         "inputSchema": {"type": "object", "properties": {"relative_path": schema}, "additionalProperties": False}},
        {"type": "function", "name": "workspace_write", "description": "Write or append persistent reconstruction notes/Ruby inside the generated workspace only.",
         "inputSchema": {"type": "object", "required": ["relative_path", "content"], "properties": {
             "relative_path": schema, "content": {"type": "string", "maxLength": MAX_TEXT_BYTES}, "append": {"type": "boolean"}}, "additionalProperties": False}},
    ]


def workspace_file_call(workspace: Path, name: str, arguments: dict) -> dict:
    root = workspace.resolve()
    if name not in {"workspace_read", "workspace_write"}:
        raise ValueError("Unknown workspace tool.")
    if workspace.is_symlink():
        raise ValueError("Workspace may not be a link.")
    path = arguments.get("relative_path", "")
    if name == "workspace_read" and not path:
        files = []
        for directory, suffix in (("notes", ".md"), ("qa", ".md"), ("scripts", ".rb")):
            parent = root / directory
            if parent.is_symlink() or not parent.resolve().is_relative_to(root):
                continue
            files.extend(p.relative_to(root).as_posix() for p in parent.glob("*" + suffix)
                         if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root))
        return {"success": True, "files": sorted(files)}
    if not isinstance(path, str) or not re.fullmatch(r"(?:notes|qa)/[A-Za-z0-9_.-]+\.md|scripts/[A-Za-z0-9_.-]+\.rb", path):
        raise ValueError("Only workspace notes/qa Markdown and scripts Ruby are allowed.")
    target = root.joinpath(*PurePosixPath(path).parts)
    if workspace.is_symlink() or any(p.is_symlink() for p in (target, target.parent)) or not target.resolve().is_relative_to(root):
        raise ValueError("Workspace files may not escape through links.")
    if name == "workspace_write":
        content = arguments.get("content")
        if not isinstance(content, str):
            raise ValueError("content must be UTF-8 text.")
        if arguments.get("append") and target.exists():
            content = target.read_text(encoding="utf-8") + content
        if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("Workspace text exceeds the size limit.")
        target.write_text(content, encoding="utf-8")
        return {"success": True, "relative_path": path, "bytes": target.stat().st_size}
    if target.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError("Workspace text exceeds the size limit.")
    return {"success": True, "relative_path": path, "content": target.read_text(encoding="utf-8")}
