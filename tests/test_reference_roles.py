import io
import json
import pytest
from PIL import Image
from app.models import Reference
from app.reference_roles import reference_manifest, role_labels, manifest_fingerprint, validate_review_requirements
from app.reference_assets import reference_image_label
from tests.test_novice_flow import workspace


def fixture_manifest(tmp_path):
    refs = []
    images = []
    for name, role in [('original', 'target_building'), ('old_bad_model', 'defect_location'), ('legacy', 'unknown')]:
        path = tmp_path / f'inputs/reference/{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        images.append(path)
        refs.append({'source': path.relative_to(tmp_path).as_posix(), 'evidence_role': role,
                     'evidence_turn_id': 'round3' if role == 'defect_location' else 'round1',
                     'evidence_model_revisions': {'villa': 5} if role == 'defect_location' else {}})
    (tmp_path / 'state').mkdir()
    (tmp_path / 'state/project_context.json').write_text(json.dumps({'references': refs}))
    return images, reference_manifest(tmp_path, images)


def requirement(source='inputs/reference/original.png', desired='absent', revision=6):
    return {'feature_id': 'rear.window.mullion', 'desired_state': desired, 'source_ref': source,
            'model_revisions': {'villa': revision}}


def envelope(items):
    return '<review_requirements>' + json.dumps(items) + '</review_requirements>'


def test_roles_do_not_promote_old_model_images_to_source(tmp_path):
    images, manifest = fixture_manifest(tmp_path)
    labels = role_labels(manifest)
    assert labels[0].startswith('SOURCE TARGET')
    assert labels[1].startswith('ISSUE LOCATION') and 'NOT target truth' in labels[1]
    assert labels[2].startswith('UNKNOWN ROLE')
    prompt = reference_image_label(images, reconstruction=True)
    assert 'must never be copied as target geometry' in prompt
    assert 'model revisions={"villa": 5}' in prompt
    assert Reference.model_validate({'source': 'old.png'}).evidence_role == 'unknown'


@pytest.mark.parametrize('source', ['inputs/reference/old_bad_model.png', 'inputs/reference/legacy.png'])
def test_defect_and_unknown_cannot_back_correction(tmp_path, source):
    _, manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValueError, match='target_building'):
        validate_review_requirements(envelope([requirement(source)]), manifest=manifest,
                                     revisions={'villa': 6}, issue_count=1, history=[])


def test_stale_review_and_contradiction_block_blind_oscillation(tmp_path):
    _, manifest = fixture_manifest(tmp_path)
    kwargs = dict(manifest=manifest, revisions={'villa': 6}, issue_count=1, history=[])
    with pytest.raises(ValueError, match='Stale'):
        validate_review_requirements(envelope([requirement(revision=5)]), **kwargs)
    old = requirement(desired='absent', revision=5)
    kwargs['history'] = [{'requirements': [old]}]
    with pytest.raises(ValueError, match='reverses'):
        validate_review_requirements(envelope([requirement(desired='present')]), **kwargs)
    assert validate_review_requirements(envelope([requirement()]), **kwargs)
    kwargs.update(history=[], issue_count=2)
    with pytest.raises(ValueError, match='Conflicting'):
        validate_review_requirements(envelope([requirement(), requirement(desired='present')]), **kwargs)


def test_role_change_invalidates_fingerprint(tmp_path):
    images, manifest = fixture_manifest(tmp_path)
    before = manifest_fingerprint(manifest)
    context = tmp_path / 'state/project_context.json'
    data = json.loads(context.read_text()); data['references'][1]['evidence_role'] = 'supporting'
    context.write_text(json.dumps(data))
    assert before != manifest_fingerprint(reference_manifest(tmp_path, images))


def test_upload_persists_role_and_turn_and_safe_legacy_classification(tmp_path):
    app, client, project, _, _ = workspace(tmp_path)
    image = io.BytesIO(); Image.new('RGB', (12, 12), 'white').save(image, 'PNG')
    response = client.post(f'/api/projects/{project}/inputs/reference?filename=defect.png&evidence_role=defect_location', content=image.getvalue())
    assert response.status_code == 200
    source = response.json()['path']
    response = client.post(f'/api/projects/{project}/conversation', json={'message': '只修截图的问题', 'workflow_mode': 'image_reconstruction'})
    context = response.json()['project']['context']
    ref = context['references'][0]
    assert ref['evidence_role'] == 'defect_location'
    assert ref['evidence_turn_id'] == context['conversation'][0]['metadata']['evidence_turn_id']
    assert client.patch(f'/api/projects/{project}/reference-role', json={'source': source, 'evidence_role': 'supporting'}).status_code == 200
    assert client.patch(f'/api/projects/{project}/reference-role', json={'source': source, 'evidence_role': 'SOURCE'}).status_code == 400
    app.state.agent_lock.acquire()
    try:
        assert client.patch(f'/api/projects/{project}/reference-role', json={'source': source, 'evidence_role': 'target_building'}).status_code == 409
    finally:
        app.state.agent_lock.release()


def test_native_critic_labels_defects_and_rejects_stale_inflight_images(tmp_path, monkeypatch):
    from app import native_agent as subject
    project = tmp_path / 'project'; project.mkdir()
    images, manifest = fixture_manifest(project)
    current = project / 'outputs/renders/agent-view-front.png'
    current.parent.mkdir(parents=True); current.write_bytes(b'current')
    monkeypatch.setattr(subject, 'validate_visual_review_views', lambda *_: ({'villa': 6}, {}, {'front': current}))
    monkeypatch.setattr(subject, 'validate_source_matched_pairs', lambda *_: [])
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable='fixture')
    calls = []
    reply = 'NEEDS_FIX: NO\n<assessment>Current target comparison complete.</assessment>\n' + envelope([])
    def run(**kwargs):
        calls.append(kwargs)
        return subject.AgentTurnResult('review', reply, model_name='offline-fixture')
    monkeypatch.setattr(runtime, '_run_turn', run)
    workspace_path = project / 'runtime/agent_workspace'; workspace_path.mkdir(parents=True)
    kwargs = dict(project_dir=project, agent_workspace=workspace_path, ruby_state={}, arguments={'views': {}}, model='fixture', reasoning_effort='medium')
    result = runtime._native_visual_review(**kwargs)
    assert result['_reviewer']['reference_manifest'][1]['role'] == 'defect_location'
    assert 'ISSUE LOCATION (historical model; NOT target truth)' in calls[0]['prompt']
    assert all('SOURCE TARGET inputs/reference/old_bad_model' not in call['prompt'] for call in calls)
    def stale_run(**kwargs):
        current.write_bytes(b'changed during inference')
        return subject.AgentTurnResult('review', reply, model_name='offline-fixture')
    monkeypatch.setattr(runtime, '_run_turn', stale_run)
    with pytest.raises(ValueError, match='image changed'):
        runtime._native_visual_review(**kwargs)
    # No second successful history record was appended after rejection.
    assert len((project / 'runtime/reference_role_review_history.jsonl').read_text().splitlines()) == 1


def test_unbound_corrections_and_duplicate_metadata_fail_closed(tmp_path):
    images, manifest = fixture_manifest(tmp_path)
    with pytest.raises(ValueError, match='revision-bound'):
        validate_review_requirements('NEEDS_FIX: YES', manifest=manifest, revisions={'villa': 6}, issue_count=1, history=[])
    context = tmp_path / 'state/project_context.json'
    data = json.loads(context.read_text())
    data['references'].append({**data['references'][1], 'evidence_role': 'target_building'})
    context.write_text(json.dumps(data))
    assert reference_manifest(tmp_path, images)[1]['role'] == 'unknown'
