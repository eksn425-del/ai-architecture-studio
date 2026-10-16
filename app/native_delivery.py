"""Honest native delivery receipts for the single-user SketchUp prototype.

Two successful file saves and a matching revision are NOT proof that a
downloaded SKP reopens to the same geometry. This intentionally fails open
*only* for downloading a candidate: delivery quality remains unverified until
a human/native host collects and compares deep pre/post-reopen fingerprints.
No automatic native open or modification occurs here.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def bind_current_checkpoint_download(reply: str, model_path: str) -> str:
    """Bind current-download claims to the host checkpoint saved AFTER inference.

    Historical/comparison links remain immutable. The model cannot know the
    new checkpoint's random filename before the host finishes saving it.
    """
    path = Path(model_path)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".skp" or path.parts[:2] != ("outputs", "model"):
        raise ValueError("Current download must name a project model checkpoint.")
    target = "../../" + path.as_posix()

    def replace(match: re.Match[str]) -> str:
        label, old_target = match.group(1), match.group(2)
        current = any(word in label for word in ("下载", "当前", "本轮", "最新"))
        historical = any(word in label for word in ("历史", "原始", "修改前", "旧版", "上一版"))
        owned_checkpoint = "://" not in old_target and re.search(
            r"(?:^|/)outputs/model/(?:agent-checkpoint-[a-f0-9]{12}|fast-assembly-agent)\.skp(?:\?[^\s]*)?$",
            old_target, re.I,
        )
        if current and not historical and owned_checkpoint:
            return f"[{label}]({target})"
        return match.group(0)

    return re.sub(r"(?<!!)\[([^\]\n]+)\]\(([^\s)]+)\)", replace, reply)


def _artifact_identity(project_dir: Path, path: Path) -> dict[str, Any]:
    root = project_dir.resolve()
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("A delivery checkpoint requires a real project-owned SKP file.")
    if path.suffix.lower() != ".skp" or path.stat().st_size == 0:
        raise ValueError("A delivery checkpoint requires a nonempty SKP file.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "path": path.resolve().relative_to(root).as_posix(),
        "sha256": digest.hexdigest(),
        "bytes": path.stat().st_size,
    }


def record_delivery_checkpoint(
    project_dir: Path, bound_model: Path, downloaded_candidate: Path,
    *, roots: list[int], revisions: dict[str, int],
) -> dict[str, Any]:
    """Record exactly what was saved; NEVER mark native delivery PASS here."""
    if not roots or any(not isinstance(pid, int) or pid <= 0 for pid in roots):
        raise ValueError("Cannot publish delivery receipt without verified owned root IDs.")
    if not revisions or any(not isinstance(rev, int) or rev <= 0 for rev in revisions.values()):
        raise ValueError("Cannot publish delivery receipt without committed revisions.")
    receipt = {
        "schema_version": 1,
        "status": "UNVERIFIED_NATIVE_REOPEN",
        "reason": "File bytes and successful save are not an editable native geometry/reopen/replay comparison.",
        "bound_document": _artifact_identity(project_dir, bound_model),
        "download_candidate": _artifact_identity(project_dir, downloaded_candidate),
        "roots": roots,
        "script_revisions": revisions,
        "required_next": ["before_save_native_fingerprint", "bound_reopened_native_fingerprint",
                          "clean_download_reopened_native_fingerprint"],
    }
    target = project_dir / "runtime" / "native_delivery_checkpoint.json"
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError("Delivery receipt path must not be a symbolic link.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    if temporary.is_symlink():
        raise ValueError("Delivery receipt temporary path must not be a symbolic link.")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return receipt
