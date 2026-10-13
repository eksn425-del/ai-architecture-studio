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
from pathlib import Path
from typing import Any


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
