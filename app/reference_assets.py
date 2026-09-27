from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_REFERENCE_IMAGES = 8
MAX_REFERENCE_IMAGE_BYTES = 8 * 1024 * 1024


def discover_project_reference_images(
    project_dir: Path,
    *,
    max_images: int = MAX_REFERENCE_IMAGES,
    max_bytes: int = MAX_REFERENCE_IMAGE_BYTES,
) -> list[Path]:
    """Return safe project-local images in a stable, reference-first order.

    Only files already stored under this project's inputs directory are eligible.
    Runtime/output screenshots are intentionally excluded so a benchmark cannot
    accidentally feed its own generated result back as precedent evidence.
    """
    root = project_dir.resolve()
    inputs_root = (root / "inputs").resolve()
    if max_images <= 0 or not inputs_root.is_dir():
        return []

    ordered_roots = [inputs_root / "reference", inputs_root / "site", inputs_root / "brief"]
    images: list[Path] = []
    seen: set[Path] = set()
    for category_root in ordered_roots:
        if not category_root.is_dir() or category_root.is_symlink():
            continue
        for candidate in sorted(category_root.rglob("*"), key=lambda item: item.as_posix().casefold()):
            if len(images) >= max_images:
                return images
            if not candidate.is_file() or candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            if resolved in seen or not resolved.is_relative_to(inputs_root):
                continue
            if resolved.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                continue
            try:
                size = resolved.stat().st_size
            except OSError:
                continue
            if size <= 0 or size > max_bytes:
                continue
            seen.add(resolved)
            images.append(resolved)
    return images


def image_data_url(path: Path) -> str:
    resolved = path.resolve()
    if resolved.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"Unsupported reference image type: {resolved.suffix}")
    data = resolved.read_bytes()
    if not data or len(data) > MAX_REFERENCE_IMAGE_BYTES:
        raise ValueError("Reference image is empty or exceeds the per-image size limit.")
    media_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    return f"data:{media_type};base64,{base64.b64encode(data).decode('ascii')}"


def reference_image_label(paths: list[Path]) -> str:
    if not paths:
        return ""
    names = ", ".join(path.name for path in paths)
    return (
        "Attached project/reference images are first-class design evidence. "
        "Inspect them before deciding form, plan, section, envelope, openings, and site relationships. "
        f"Image files in attachment order: {names}. "
        "Transfer principles and spatial logic; do not blindly copy a precedent or override the project brief/site."
    )
