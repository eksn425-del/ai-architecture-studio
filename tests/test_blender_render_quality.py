"""Render-only quality bounds, receipt/identity isolation, and native smoke tests."""
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from app.blender_backend import BlenderBackend
from app.blender_render_options import render_cache_key, validate_render_options


CAMERA = {'position': [5, -8, 4], 'target': [0, 0, 0], 'lens': 35}


def test_default_settings_and_legacy_filenames_are_preserved():
    options = validate_render_options({}, [])
    assert options == {'view': 'front', 'camera': None, 'hide_ids': [], 'resolution': 800}
    assert render_cache_key(options) == 'front'
    assert render_cache_key(validate_render_options({'resolution': 800}, [])) == 'front'
    original = {'view': 'front', 'camera': CAMERA, 'hide_ids': []}
    legacy = 'front-' + hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()[:12]
    assert render_cache_key(validate_render_options(original, [])) == legacy


@pytest.mark.parametrize('value', [799, 1601, 10**100, -1, 0, True, False, 1200.0, '1200', None, float('inf'), float('nan')])
def test_resolution_rejects_unbounded_or_noninteger_values(value):
    with pytest.raises(ValueError, match='Resolution'):
        validate_render_options({'resolution': value}, [])


@pytest.mark.parametrize('value', [None, 0, 1, 'true', [], {}])
def test_denoise_requires_an_actual_boolean(value):
    with pytest.raises(ValueError, match='Denoise'):
        validate_render_options({'denoise': value}, [])


def test_quality_and_view_variants_have_distinct_identity():
    variants = [{}, {'resolution': 1200}, {'resolution': 1600}, {'denoise': False},
                {'denoise': True}, {'resolution': 1600, 'denoise': True},
                {'camera': CAMERA}, {'camera': CAMERA, 'resolution': 1600},
                {'hide_ids': ['roof']}, {'hide_ids': ['roof'], 'resolution': 1600}]
    keys = [render_cache_key(validate_render_options(args, ['roof'])) for args in variants]
    assert len(keys) == len(set(keys))


def _backend_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr('app.blender_backend.shutil.which', lambda _: '/test/blender')
    backend = BlenderBackend(tmp_path)
    model = backend.root / 'fixture.blend'
    model.write_bytes(b'unchanged native model')
    original = {'model_path': str(model.relative_to(tmp_path)), 'revision': 9,
                'objects': {'roof': {'id': 'roof'}}, 'geometry': {'roof': {'stable': True}},
                'sha256': hashlib.sha256(model.read_bytes()).hexdigest()}
    backend.state.write_text(json.dumps(original))
    return backend, model, original


def test_schema_contains_only_bounded_quality_controls(tmp_path, monkeypatch):
    backend, _, _ = _backend_fixture(tmp_path, monkeypatch)
    schema = next(t['inputSchema'] for t in backend.tools() if t['name'] == 'blender_render_scene')
    assert schema['additionalProperties'] is False
    assert schema['properties']['resolution'] == {'type': 'integer', 'minimum': 800, 'maximum': 1600, 'default': 800}
    assert schema['properties']['denoise'] == {'type': 'boolean'}


def test_dispatch_reports_applied_settings_and_preserves_other_render(tmp_path, monkeypatch):
    backend, model, original = _backend_fixture(tmp_path, monkeypatch)
    calls = []

    def fake_render(run_dir, phase, command):
        assert phase == 'render'
        assert '--disable-autoexec' in command and '--python-exit-code' in command
        argv = command[command.index('--') + 1:]
        options = json.loads(argv[3])
        calls.append(options)
        Path(argv[1]).write_bytes(json.dumps(options).encode())
        Path(argv[4]).write_text(json.dumps({'resolution': options['resolution'],
                                            'denoise': options.get('denoise', False),
                                            'samples': 256 if options.get('camera') else 128}))

    monkeypatch.setattr(backend, '_run', fake_render)
    default = backend.dispatch('blender_render_scene', {})
    original_image = (tmp_path / default['image_path']).read_bytes()
    high = backend.dispatch('blender_render_scene', {'resolution': 1600, 'denoise': True})
    assert default['resolution'] == 800 and default['denoise'] is False and default['samples'] == 128
    assert default['denoise_requested'] is None
    assert high['resolution'] == 1600 and high['denoise'] is True and high['denoise_requested'] is True
    assert high['image_path'] != default['image_path']
    assert (tmp_path / default['image_path']).read_bytes() == original_image
    assert hashlib.sha256(model.read_bytes()).hexdigest() == original['sha256']
    current = json.loads(backend.state.read_text())
    assert len(current['renders']) == 2
    assert {k: current[k] for k in original} == original
    assert calls[1]['resolution'] == 1600


def test_invalid_settings_never_launch_blender_or_change_state(tmp_path, monkeypatch):
    backend, _, _ = _backend_fixture(tmp_path, monkeypatch)
    state = backend.state.read_bytes()
    monkeypatch.setattr(backend, '_run', lambda *args: pytest.fail('Invalid settings launched Blender'))
    for args in [{'resolution': True}, {'resolution': 1601}, {'denoise': 1}]:
        with pytest.raises(ValueError):
            backend.dispatch('blender_render_scene', args)
    assert backend.state.read_bytes() == state


def test_failed_render_does_not_commit_or_reuse_a_stale_receipt(tmp_path, monkeypatch):
    backend, _, _ = _backend_fixture(tmp_path, monkeypatch)
    state = backend.state.read_bytes()
    (backend.root / 'view-front.render.json').write_text('{"resolution":800,"denoise":false,"samples":128}')
    monkeypatch.setattr(backend, '_run', lambda *args: None)
    with pytest.raises(FileNotFoundError):
        backend.dispatch('blender_render_scene', {})
    assert backend.state.read_bytes() == state


@pytest.mark.skipif(not shutil.which('blender'), reason='real Blender required')
def test_native_render_resolution_and_geometry_preservation(tmp_path):
    backend = BlenderBackend(tmp_path)
    original = backend.dispatch('blender_apply_objects', {'objects': [
        {'id': 'quality_probe', 'location': [0, 0, 0], 'dimensions': [1, 1, 1]}]})
    model = tmp_path / original['model_path']
    model_hash = hashlib.sha256(model.read_bytes()).hexdigest()
    results = []
    for args in [{}, {'resolution': 1600, 'denoise': False}]:
        result = backend.dispatch('blender_render_scene', args)
        image = tmp_path / result['image_path']
        raw = image.read_bytes()
        assert raw[:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II', raw[16:24]) == (result['resolution'], result['resolution'])
        assert result['denoise'] is False and result['samples'] == 128
        results.append(result)
    assert results[0]['image_path'] != results[1]['image_path']
    assert all((tmp_path / r['image_path']).is_file() for r in results)
    assert hashlib.sha256(model.read_bytes()).hexdigest() == model_hash
    current = backend.dispatch('blender_inspect_scene', {})
    assert current['revision'] == original['revision']
    assert current['objects'] == original['objects']
    assert current['geometry'] == original['geometry']


@pytest.mark.skipif(not shutil.which('blender'), reason='real Blender required')
@pytest.mark.parametrize('options', [{'resolution': True}, {'resolution': 1601}, {'denoise': 1}])
def test_native_worker_rejects_direct_invalid_options(tmp_path, options):
    worker = Path(__file__).resolve().parents[1] / 'app/blender_worker.py'
    image = tmp_path / 'rejected.png'
    receipt = tmp_path / 'rejected.json'
    command = [shutil.which('blender'), '--background', '--factory-startup', '--disable-autoexec',
               '--python-exit-code', '1', '--python', str(worker), '--', 'render',
               str(image), 'front', json.dumps(options), str(receipt)]
    completed = subprocess.run(command, text=True, capture_output=True, timeout=60)
    assert completed.returncode != 0
    assert not image.exists() and not receipt.exists()
