"""Active-wire native-mesh projection; raw journal and exact specs stay untouched."""
from __future__ import annotations
import copy
import hashlib
import json
import re

SCENE_TOOLS = frozenset({'blender_apply_objects', 'blender_inspect_scene'})
_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')


def project_blender_tool_text(name: str, text: str) -> str:
    if name not in SCENE_TOOLS:
        return text
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return text
    from .blender_api_readback import committed_blender_result
    if (not committed_blender_result(value) or value.get('include_geometry_detail') is True
            or value.get('error') or value.get('errors')
            or 'wire_geometry_projection' in value
            or not isinstance(value.get('geometry'), dict)):
        return text
    projected = copy.deepcopy(value)
    changed = False
    for native in projected['geometry'].values():
        if not isinstance(native, dict) or 'wire_geometry_omission' in native:
            continue
        arrays = {k: native[k] for k in ('vertices', 'faces') if isinstance(native.get(k), list)}
        if not arrays:
            continue
        try:
            digest = hashlib.sha256(json.dumps(arrays, sort_keys=True, ensure_ascii=False,
                                              separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        except (ValueError, TypeError):
            # Malformed/non-finite native values are evidence, not compressible success.
            return text
        for key in arrays:
            del native[key]
        native['wire_geometry_omission'] = {
            'omitted_fields': list(arrays), 'counts': {k: len(v) for k, v in arrays.items()},
            'sha256': digest,
        }
        changed = True
    if changed:
        projected['wire_geometry_projection'] = {
            'digest_encoding': 'UTF-8 canonical compact sorted-key JSON of omitted fields',
            'label': 'Native mesh arrays omitted ONLY from active wire context; full raw receipt retained in provider history. Exact authored object specs and native transforms/materials retained. Not a source-fidelity verdict.',
            'retrieve': 'blender_inspect_scene(object_ids=[selected IDs, max 8], include_geometry_detail=true)',
        }
    return json.dumps(projected, ensure_ascii=False, separators=(',', ':')) if changed else text


def inspect_scene_selection(scene: dict, arguments: dict) -> dict:
    """Select only already-owned IDs, never accept a file path or executable input."""
    if not isinstance(arguments, dict) or set(arguments) - {'object_ids', 'include_geometry_detail'}:
        raise ValueError('Invalid inspect arguments')
    detail = arguments.get('include_geometry_detail', False)
    if type(detail) is not bool:
        raise ValueError('include_geometry_detail must be boolean')
    ids = arguments.get('object_ids')
    if ids is None:
        if detail or 'object_ids' in arguments:
            raise ValueError('Detailed geometry requires 1..8 explicit object_ids')
        return scene
    if (not isinstance(ids, list) or not 1 <= len(ids) <= 8
            or any(not isinstance(i, str) or not _ID.fullmatch(i) for i in ids)
            or len(set(ids)) != len(ids)
            or any(i not in scene.get('objects', {}) or i not in scene.get('geometry', {}) for i in ids)):
        raise ValueError('Expected 1..8 unique existing object_ids with native geometry')
    result = copy.deepcopy(scene)
    result['objects'] = {i: result['objects'][i] for i in ids}
    result['geometry'] = {i: result['geometry'][i] for i in ids}
    result['include_geometry_detail'] = detail
    result['inspection_scope'] = {'object_ids': ids[:], 'scene_object_count': len(scene['objects']),
                                  'label': 'Selected owned objects only; other scene metadata retained unchanged.'}
    return result
