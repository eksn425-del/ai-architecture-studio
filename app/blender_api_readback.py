"""Confined native Blender render-to-provider adapter (not a general file reader)."""
from __future__ import annotations
import base64
import io
import json
from pathlib import Path
from PIL import Image

MAX_RENDER_BYTES = 16 * 1024 * 1024


def committed_blender_result(value):
    return (isinstance(value, dict) and value.get('success') is not False
            and value.get('isError') is not True
            and value.get('candidate_status') == 'saved_candidate'
            and value.get('native_reopen') == 'PASS'
            and type(value.get('revision')) is int and value['revision'] > 0)


def _owned_file(project, relative):
    if not isinstance(relative, str) or '\\' in relative:
        raise ValueError('Invalid Blender readback path')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or path.parts[:2] != ('runtime', 'blender'):
        raise ValueError('Blender readback must be project-owned')
    target = project / path
    if any(part.is_symlink() for part in [target, *target.parents] if part != project and part.is_relative_to(project)):
        raise ValueError('Blender readback symlinks are forbidden')
    if not target.resolve().is_relative_to(project / 'runtime/blender') or not target.is_file():
        raise ValueError('Missing project-owned Blender readback')
    return target


def blender_render_data_url(project_dir: Path, output: dict) -> str:
    # Serialize with native commits/renders so receipt and pixels describe the
    # same revision. Do not infer trust from an arbitrary image_path field.
    from .blender_backend import _LOCK
    with _LOCK:
        project = project_dir.resolve()
        state = _owned_file(project, 'runtime/blender/scene.json')
        if state.stat().st_size > 32 * 1024 * 1024:
            raise ValueError('Blender scene receipt exceeds readback limit')
        current = json.loads(state.read_text(encoding='utf-8'))
        if (not committed_blender_result(current)
                or output.get('success') is False or output.get('isError') is True
                or type(output.get('revision')) is not int
                or output['revision'] != current['revision']
                or output not in current.get('renders', {}).values()):
            raise ValueError('Blender render receipt is not current')
        image = _owned_file(project, output.get('image_path'))
        model = _owned_file(project, current.get('model_path'))
        if image.parent != model.parent or image.suffix.lower() != '.png':
            raise ValueError('Blender render is not owned by the current model')
        if not 0 < image.stat().st_size <= MAX_RENDER_BYTES:
            raise ValueError('Blender render exceeds readback size limit')
        with image.open('rb') as stream:
            data = stream.read(MAX_RENDER_BYTES + 1)
        if len(data) > MAX_RENDER_BYTES:
            raise ValueError('Blender render exceeds readback size limit')
        with Image.open(io.BytesIO(data)) as decoded:
            if (decoded.format != 'PNG' or decoded.width != output.get('resolution')
                    or decoded.height != output.get('resolution')
                    or not 800 <= decoded.width <= 1600):
                raise ValueError('Blender render format or dimensions mismatch')
            decoded.verify()
        return 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
