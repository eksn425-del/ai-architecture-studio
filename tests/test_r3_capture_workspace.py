"""Host capture destination regressions, with a strict paired-workspace fixture.

These are offline protocol/route tests, not real native SketchUp image evidence.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main
from app.sketchup_mcp import MCPCallError, SketchUpAdapter
from tests.conftest import FakeBrain, FakeSketchUp


class PairedCaptureClient:
    requires_document_binding = True

    def __init__(self, workspace):
        self.workspace = workspace.resolve()
        self.calls = []
        self.identity = {'model_path': str(self.workspace / 'owned.skp'),
                         'model_guid': 'fixture-owned-guid', 'main_thread': True}

    def call(self, name, args):
        self.calls.append((name, args))
        if name == 'sketchup_get_model_context':
            return self.identity
        assert name == 'sketchup_export_view_image'
        if self.requires_document_binding:
            assert args['expected_model_path'] == self.identity['model_path']
            assert args['expected_model_guid'] == self.identity['model_guid']
        else:
            assert 'expected_model_path' not in args and 'expected_model_guid' not in args
        output = Path(args['output_path'])
        # Match the public Ruby connector's real-parent workspace rule. Merely
        # returning success without writing a file cannot satisfy the host test.
        parent = output.parent.resolve(strict=True)
        if not parent.is_relative_to(self.workspace) or output.suffix.lower() != '.png':
            raise MCPCallError('Image destination is outside paired workspaces')
        if output.is_symlink():
            raise MCPCallError('Image destination must not be a symlink')
        output.write_bytes(b'fixture native capture bytes')
        return {'saved': True, 'path': str(output)}


@pytest.mark.parametrize('public', [True, False])
def test_agent_post_capture_uses_paired_project_and_preserves_protocol(tmp_path, monkeypatch, public):
    runtime = tmp_path / 'profile' / 'runtime'
    runtime.mkdir(parents=True)
    program = tmp_path / 'installed-program'
    monkeypatch.setattr(main, 'ROOT', program)
    client = PairedCaptureClient(runtime)
    client.requires_document_binding = public
    adapter = SketchUpAdapter(client)
    project = runtime / 'projects' / 'case'
    store = SimpleNamespace(project_dir=lambda project_id: project)
    # Reproduce the historical host destination rejection without enlarging roots.
    outside = tmp_path / 'old-program-artifacts' / 'bad.png'
    outside.parent.mkdir()
    with pytest.raises(MCPCallError, match='outside paired'):
        adapter.capture_view(outside)
    result = main._capture_agent_view(adapter, store, 'case')
    assert result.parent == project / 'outputs' / 'renders'
    assert result.read_bytes() == b'fixture native capture bytes'
    assert not program.exists()


def test_initial_build_and_edit_http_capture_remain_inside_runtime(tmp_path, monkeypatch):
    runtime = tmp_path / 'runtime'
    capture_client = PairedCaptureClient(runtime)
    capture_adapter = SketchUpAdapter(capture_client)

    class ScopedSketchUp(FakeSketchUp):
        def capture_view(self, output_path, **kwargs):
            return capture_adapter.capture_view(output_path, **kwargs)

    monkeypatch.setattr(main, 'ROOT', tmp_path / 'immutable-program')
    app = main.create_app(runtime, brain=FakeBrain(), sketchup=ScopedSketchUp())
    client = TestClient(app)
    assert client.get('/api/projects').status_code == 200
    base = '/api/projects/demo-cultural-center'
    assert client.post(base + '/prepare', json={}).status_code == 200
    built = client.post(base + '/build', json={'confirm_disposable_model': True})
    assert built.status_code == 200, built.text
    edited = client.post(base + '/edit', json={'instruction': 'Raise the reading pavilion by one floor.'})
    assert edited.status_code == 200, edited.text
    exports = [args for name, args in capture_client.calls if name == 'sketchup_export_view_image']
    assert len(exports) == 2
    renders = (runtime / 'projects/demo-cultural-center/outputs/renders').resolve()
    assert all(Path(args['output_path']).parent == renders for args in exports)
    assert all(Path(args['output_path']).is_file() for args in exports)
    assert not (main.ROOT / 'artifacts').exists()


@pytest.mark.parametrize('filename', ['../escape.png', '..\\escape.png', 'not-an-image.txt'])
def test_capture_filename_cannot_escape_project(tmp_path, filename):
    adapter = SketchUpAdapter(PairedCaptureClient(tmp_path))
    with pytest.raises(MCPCallError, match='local PNG'):
        main._capture_project_view(adapter, tmp_path, filename)
    assert adapter.client.calls == []


def test_capture_parent_cannot_redirect_outside_project(tmp_path, require_symlink):
    project = tmp_path / 'project'
    (project / 'outputs').mkdir(parents=True)
    outside = tmp_path / 'other-project'
    outside.mkdir()
    (project / 'outputs/renders').symlink_to(outside, target_is_directory=True)
    adapter = SketchUpAdapter(PairedCaptureClient(tmp_path))
    with pytest.raises(MCPCallError, match='escape'):
        main._capture_project_view(adapter, project, 'view.png')
    assert adapter.client.calls == []


def test_missing_native_image_is_not_an_artifact(tmp_path):
    adapter = SimpleNamespace(capture_view=lambda path: {'saved': False})
    store = SimpleNamespace(project_dir=lambda project_id: tmp_path / project_id)
    assert main._capture_agent_view(adapter, store, 'case') is None
