import base64
import json
import pytest
from PIL import Image
from app.blender_api_readback import blender_render_data_url
from app.litellm_runtime import _current_visual_context, _image_count, _tool_result_parts


@pytest.fixture
def render(tmp_path):
    project = tmp_path / 'project'
    run = project / 'runtime/blender/run'
    run.mkdir(parents=True)
    (run / 'model.blend').write_bytes(b'native')
    Image.new('RGB', (800, 800)).save(run / 'view.png')
    output = {'image_path': 'runtime/blender/run/view.png', 'revision': 1, 'resolution': 800}
    scene = {'revision': 1, 'candidate_status': 'saved_candidate', 'native_reopen': 'PASS',
             'model_path': 'runtime/blender/run/model.blend', 'renders': {'test': output.copy()}}
    state = project / 'runtime/blender/scene.json'
    state.write_text(json.dumps(scene))
    return project, run, output, scene, state


def test_native_png_bytes_and_output_preserved(render):
    project, run, output, _, _ = render
    url = blender_render_data_url(project, output)
    assert base64.b64decode(url.split(',', 1)[1]) == (run / 'view.png').read_bytes()
    assert output == {'image_path': 'runtime/blender/run/view.png', 'revision': 1, 'resolution': 800}
    huge = {**output, 'native_details': 'x' * 70000}
    assert json.loads(_tool_result_parts(huge, truncate=False)[0]) == huge


@pytest.mark.parametrize('mutation', ['stale', 'failed', 'uncommitted', 'missing_receipt', 'wrong_resolution', 'bad_png', 'oversize'])
def test_rejects_untrusted_render(render, monkeypatch, mutation):
    project, run, output, scene, state = render
    if mutation == 'stale': scene['revision'] = 2
    if mutation == 'failed': output['success'] = False
    if mutation == 'uncommitted': scene['native_reopen'] = 'FAIL'
    if mutation == 'missing_receipt': scene['renders'] = {}
    if mutation == 'wrong_resolution': Image.new('RGB', (100, 100)).save(run / 'view.png')
    if mutation == 'bad_png': (run / 'view.png').write_bytes(b'not png')
    if mutation == 'oversize': monkeypatch.setattr('app.blender_api_readback.MAX_RENDER_BYTES', 10)
    state.write_text(json.dumps(scene))
    with pytest.raises((ValueError, OSError)):
        blender_render_data_url(project, output)


@pytest.mark.parametrize('path', ['../other/view.png', '/tmp/view.png', 'https://example.org/a.png', 'runtime/blender/../../other/a.png'])
def test_rejects_paths_even_with_forged_receipt(render, path):
    project, _, output, scene, state = render
    output['image_path'] = path
    scene['renders']['test'] = output
    state.write_text(json.dumps(scene))
    with pytest.raises(ValueError): blender_render_data_url(project, output)


@pytest.mark.parametrize('target', ['image', 'scene', 'directory'])
def test_rejects_symlinks(render, tmp_path, target):
    project, run, output, _, state = render
    path = {'image': run / 'view.png', 'scene': state, 'directory': run}[target]
    outside = tmp_path / ('outside' + path.suffix)
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=target == 'directory')
    with pytest.raises(ValueError): blender_render_data_url(project, output)


def test_cross_project_receipt_not_accepted(render, tmp_path):
    project, _, output, _, _ = render
    other = tmp_path / 'other'
    other.mkdir()
    with pytest.raises(ValueError): blender_render_data_url(other, output)


def capture(revision, legacy=False):
    label = 'Visual readback from SketchUp tool capture.' if legacy else f'Visual readback from tool blender_render_scene. Blender scene revision {revision}.'
    return {'role': 'user', 'content': [{'type': 'text', 'text': label}, {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,abc'}}]}


def commit(**changes):
    result = {'revision': 2, 'candidate_status': 'saved_candidate', 'native_reopen': 'PASS', **changes}
    return [{'role': 'assistant', 'tool_calls': [{'id': 'edit', 'function': {'name': 'blender_apply_objects'}}]},
            {'role': 'tool', 'tool_call_id': 'edit', 'content': json.dumps(result)}]


def test_commit_invalidates_old_and_same_batch_images_without_mutating_audit():
    messages = [capture(1, True), capture(1), *commit(), capture(1), capture(2)]
    active = _current_visual_context(messages)
    assert _image_count(active) == 1
    assert _image_count(messages) == 4
    assert active[2:4] == messages[2:4]


@pytest.mark.parametrize('changes', [{'success': False}, {'isError': True}, {'native_reopen': 'FAIL'}, {'candidate_status': 'pending'}, {'revision': 0}, {'revision': True}])
def test_failed_or_uncommitted_writer_does_not_invalidate(render, changes):
    assert _image_count(_current_visual_context([capture(1), *commit(**changes)])) == 1


def test_adapter_failure_keeps_tool_id_and_native_receipt(render, monkeypatch):
    from types import SimpleNamespace
    from tests.test_api_execution_contracts import runtime, response, call, run
    project, _, native, _, _ = render
    r, _, requests = runtime(project, monkeypatch,
        [response([call('render-id', 'blender_render_scene')]), response()])
    context = SimpleNamespace(dynamic_tools=[{'name': 'blender_render_scene', 'inputSchema': {'type': 'object'}}],
                              quality_state={}, dispatch=lambda *_: native)
    monkeypatch.setattr(r.tool_surface, 'prepare', lambda **_: context)
    def fail(*_): raise RuntimeError('readback decoder failed')
    monkeypatch.setattr('app.litellm_runtime.blender_render_data_url', fail)
    result = run(r, project)
    receipts = [m for m in requests[1]['messages'] if m.get('role') == 'tool']
    assert receipts[-1]['tool_call_id'] == 'render-id'
    receipt = json.loads(receipts[-1]['content'])
    assert receipt['success'] is False and receipt['native_result'] == native
    assert result.failed_tool_calls == 1
    assert _image_count(requests[1]['messages']) == 0
