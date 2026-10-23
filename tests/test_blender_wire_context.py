import copy
import hashlib
import json
import pytest
from app.blender_wire_context import project_blender_tool_text, inspect_scene_selection
from app.litellm_runtime import _current_visual_context
from app.blender_backend import BlenderBackend


def receipt():
    native = {'location': [0.12345678901234567, 0, 0], 'dimensions': [1, 2, 3],
              'material': [{'roughness': 0.12345678901234567}],
              'vertices': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'faces': [[0, 1, 2]],
              'unknown_native': {'do_not_drop': [1, 2]}}
    return {'revision': 7, 'native_reopen': 'PASS', 'candidate_status': 'saved_candidate',
            'quality_status': 'unverified', 'intent': {'keep': ['B']}, 'objects': {
                'A': {'id': 'A', 'vertices': native['vertices'], 'faces': native['faces']},
                'B': {'id': 'B', 'dimensions': [1, 2, 3]}},
            'geometry': {'A': copy.deepcopy(native), 'B': copy.deepcopy(native)},
            'unknown': {'must_stay': 'x' * 10000}}


def test_projection_valid_exact_auditable_and_nonmutating():
    raw = receipt()
    saved = copy.deepcopy(raw)
    text = json.dumps(raw)
    output = json.loads(project_blender_tool_text('blender_apply_objects', text))
    assert raw == saved and json.loads(text) == saved
    assert output['objects'] == raw['objects']
    for k in raw.keys() - {'geometry'}:
        assert output[k] == raw[k]
    for oid, native in raw['geometry'].items():
        out = output['geometry'][oid]
        for k in native.keys() - {'vertices', 'faces'}:
            assert out[k] == native[k]
        meta = out.pop('wire_geometry_omission')
        arrays = {k: native[k] for k in ('vertices', 'faces')}
        assert meta['sha256'] == hashlib.sha256(json.dumps(arrays, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        assert meta['counts'] == {'vertices': 3, 'faces': 1}
        assert 'vertices' not in out and 'faces' not in out


@pytest.mark.parametrize('patch', [{'success': False}, {'isError': True}, {'native_reopen': 'FAIL'}, {'errors': ['failure']}, {'error': 'failure'}, {'include_geometry_detail': True}])
def test_failure_or_detail_never_projected(patch):
    text = json.dumps({**receipt(), **patch})
    assert project_blender_tool_text('blender_inspect_scene', text) == text


def test_default_and_targeted_inspection():
    raw = receipt()
    saved = copy.deepcopy(raw)
    assert inspect_scene_selection(raw, {}) == raw
    selected = inspect_scene_selection(raw, {'object_ids': ['A'], 'include_geometry_detail': True})
    assert selected['geometry'] == {'A': raw['geometry']['A']}
    assert selected['objects'] == {'A': raw['objects']['A']}
    assert selected['inspection_scope']['scene_object_count'] == 2
    assert selected['unknown'] == raw['unknown']
    assert raw == saved
    text = json.dumps(selected)
    assert project_blender_tool_text('blender_inspect_scene', text) == text


@pytest.mark.parametrize('args', [{'path': '/etc/passwd'}, {'include_geometry_detail': True}, {'object_ids': ['../A']}, {'object_ids': ['missing']}, {'object_ids': []}, {'object_ids': ['A', 'A']}, {'object_ids': ['A'] * 9}, {'object_ids': None}, {'include_geometry_detail': 1}, {'object_ids': 'A'}])
def test_invalid_scope_rejected(args):
    with pytest.raises(ValueError):
        inspect_scene_selection(receipt(), args)


def test_active_wire_keeps_raw_history_and_old_failures():
    messages = []
    raw = json.dumps(receipt())
    for i in range(9):
        text = raw if i else json.dumps({**receipt(), 'success': False})
        messages.extend([{'role': 'assistant', 'tool_calls': [{'id': str(i), 'function': {'name': 'blender_inspect_scene'}}]},
                         {'role': 'tool', 'tool_call_id': str(i), 'content': text}])
    saved = copy.deepcopy(messages)
    wire = _current_visual_context(messages)
    assert messages == saved
    assert wire[1] == messages[1]
    for msg in wire:
        if msg['role'] == 'tool':
            json.loads(msg['content'])
    assert 'wire_geometry_omission' in wire[-1]['content']


def test_backend_default_detailed_and_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr('app.blender_backend.shutil.which', lambda _: '/fixture/blender')
    backend = BlenderBackend(tmp_path)
    raw = receipt()
    backend.state.write_text(json.dumps(raw))
    assert backend.dispatch('blender_inspect_scene', {}) == raw
    selected = backend.dispatch('blender_inspect_scene', {'object_ids': ['B'], 'include_geometry_detail': True})
    assert selected['geometry'] == {'B': raw['geometry']['B']}
    assert json.loads(backend.state.read_text()) == raw
    backend.state.unlink()
    outside = tmp_path / 'outside.json'
    outside.write_text(json.dumps(raw))
    backend.state.symlink_to(outside)
    with pytest.raises(ValueError, match='symlink'):
        backend.dispatch('blender_inspect_scene', {'object_ids': ['B'], 'include_geometry_detail': True})


def test_unknown_tool_or_invalid_json_unchanged():
    raw = json.dumps(receipt())
    assert project_blender_tool_text('other_tool', raw) == raw
    assert project_blender_tool_text('blender_inspect_scene', 'bad json') == 'bad json'


def test_projection_metadata_collision_and_nonfinite_fail_open():
    for raw in [{**receipt(), 'wire_geometry_projection': {'unknown': 'preserve'}}, receipt()]:
        if 'wire_geometry_projection' not in raw:
            raw['geometry']['A']['vertices'][0][0] = float('nan')
        text = json.dumps(raw)
        assert project_blender_tool_text('blender_inspect_scene', text) == text


def test_shared_explanation_once():
    text = project_blender_tool_text('blender_inspect_scene', json.dumps(receipt()))
    assert text.count('Not a source-fidelity verdict.') == 1
    assert json.loads(text)['wire_geometry_projection']['retrieve']
