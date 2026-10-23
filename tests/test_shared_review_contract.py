"""Provider-neutral host review intent/evidence regression tests; no inference."""
import json
import pytest


def test_changed_execution_instruction_invalidates_unchanged_geometry(tmp_path, monkeypatch):
    from tests.test_modeling_quality import _feedback_review_fixture
    from app.modeling_quality import load_current_independent_visual_review
    project, state, _, receipt = _feedback_review_fixture(tmp_path)
    assert load_current_independent_visual_review(project, state) == receipt
    monkeypatch.setattr('app.design_scope_approval.current_execution_instruction', lambda _: {
        'user_message_id': 'new-owner-turn', 'user_message': '保留露台，只修改入口'})
    assert load_current_independent_visual_review(project, state) is None


def test_changed_approved_scope_invalidates_unchanged_geometry(tmp_path):
    from tests.test_modeling_quality import _feedback_review_fixture
    from app.modeling_quality import load_current_independent_visual_review
    project, state, _, _ = _feedback_review_fixture(tmp_path)
    (project/'runtime/approved_design_scope.json').write_text(json.dumps({'version': 2, 'valid': False, 'features': []}))
    assert load_current_independent_visual_review(project, state) is None


def _context(tmp_path, *, role='target_building'):
    from app.review_context import prepare_review_context
    source = tmp_path/'inputs/reference/source.png'
    source.parent.mkdir(parents=True); source.write_bytes(b'source')
    state = tmp_path/'state'; state.mkdir()
    (state/'project_context.json').write_text(json.dumps({'references': [{
        'type': 'image', 'source': 'inputs/reference/source.png', 'evidence_role': role}]}))
    capture = tmp_path/'outputs/current.png'; capture.parent.mkdir(); capture.write_bytes(b'actual capture')
    return prepare_review_context(tmp_path, {'villa': 1}, {'front': capture}, [])


@pytest.mark.parametrize('role', ['unknown', 'supporting', 'defect_location'])
def test_no_silent_target_role_fallback(tmp_path, role):
    with pytest.raises(ValueError, match='roles are unresolved'):
        _context(tmp_path, role=role)


@pytest.mark.parametrize('mutation', ['instruction', 'scope', 'pixels', 'sidecar', 'revision', 'source', 'history'])
def test_shared_review_rejects_races(tmp_path, monkeypatch, mutation):
    from app.review_context import validate_review_context_current
    context = _context(tmp_path)
    runtime = tmp_path/'runtime'; runtime.mkdir(exist_ok=True)
    if mutation == 'instruction':
        monkeypatch.setattr('app.design_scope_approval.current_execution_instruction', lambda _: {'user_message': '新的要求'})
    elif mutation == 'scope':
        (runtime/'approved_design_scope.json').write_text(json.dumps({'version': 2, 'valid': False, 'features': []}))
    elif mutation == 'pixels':
        context.images[-1].write_bytes(b'changed')
    elif mutation == 'sidecar':
        context.images[-1].with_suffix('.evidence.json').write_text('{}')
    elif mutation == 'revision':
        (runtime/'project_ruby_state.json').write_text(json.dumps({'scripts': {'villa': {'revision': 2}}}))
    elif mutation == 'source':
        extra = tmp_path/'inputs/reference/new.png'; extra.write_bytes(b'new source')
    elif mutation == 'history':
        (runtime/'reference_role_review_history.jsonl').write_text(json.dumps({
            'manifest_fingerprint': context.metadata['target_manifest_fingerprint'], 'requirements': []})+'\n')
    with pytest.raises(ValueError, match='changed'):
        validate_review_context_current(context)


@pytest.mark.parametrize('valid,fingerprint', [(False, 'current'), (True, 'stale'), (None, 'current')])
def test_invalid_scope_never_supersedes_requirements(tmp_path, valid, fingerprint):
    from app.review_context import prepare_review_context, finalize_review_context
    from app.design_scope_approval import current_reference_fingerprint
    context = _context(tmp_path)
    runtime = tmp_path/'runtime'; runtime.mkdir(exist_ok=True)
    (runtime/'approved_design_scope.json').write_text(json.dumps({
        'valid': valid, 'version': 10, 'reference_manifest_fingerprint':
            current_reference_fingerprint(tmp_path) if fingerprint == 'current' else fingerprint,
        'features': [{'feature_id': 'roof', 'requested_state': 'remove'}]}))
    context = prepare_review_context(tmp_path, context.revisions, {'front': context.images[-1]}, [])
    assert context.metadata['approved_design_scope']['features'] == []
    assert context.metadata['approved_design_scope']['valid'] is False


def test_shared_requirement_lifecycle_and_revision_independent_goal_key(tmp_path):
    from app.review_context import prepare_review_context, finalize_review_context, current_review_context_fingerprint
    context = _context(tmp_path)
    requirement = {'feature_id': 'roof', 'desired_state': 'retain roof',
                   'source_ref': 'inputs/reference/source.png', 'model_revisions': {'villa': 1}}
    reply = ('NEEDS_FIX: YES\n<assessment>Roof missing.</assessment>\n'
             '<issue priority="1" view="front">problem: missing roof\naction: add roof</issue>'
             '<review_requirements>'+json.dumps([requirement])+'</review_requirements>')
    metadata = finalize_review_context(context, reply)
    next_context = prepare_review_context(tmp_path, {'villa': 2}, {'front': context.images[-1]}, [])
    assert metadata['review_context_fingerprint'] == next_context.metadata['review_context_fingerprint']
    assert current_review_context_fingerprint(tmp_path) == metadata['review_context_fingerprint']
    assert 'retain roof' in next_context.prompt
    resolution = {'feature_id': 'roof', 'prior_requirement_id': metadata['review_requirements'][0]['requirement_id'],
                  'source_ref': requirement['source_ref'], 'model_revisions': {'villa': 2},
                  'status': 'resolved', 'evidence': 'Current front capture shows the roof.'}
    final = finalize_review_context(next_context, 'NEEDS_FIX: NO\n<assessment>Roof restored.</assessment>'
        '<review_requirements>[]</review_requirements><requirement_resolutions>'+json.dumps([resolution])+'</requirement_resolutions>')
    assert final['requirement_resolutions'][0]['status'] == 'resolved'


def test_native_and_api_use_identical_shared_context(tmp_path, monkeypatch):
    """Execute real runtime host paths with fake inference, not a replacement critic."""
    from tests.test_modeling_quality import test_litellm_host_requires_visual_review_before_final_reply
    from app import review_context, native_agent
    contexts = []
    original = review_context.prepare_review_context
    def capture(*args, **kwargs):
        value = original(*args, **kwargs); contexts.append(value); return value
    monkeypatch.setattr(review_context, 'prepare_review_context', capture)
    test_litellm_host_requires_visual_review_before_final_reply(tmp_path, monkeypatch)
    api_context = contexts[-1]
    runtime = native_agent.CodexAppServerRuntime(tmp_path, codex_executable='fixture')
    requirement = {'feature_id': 'wall.seam', 'desired_state': 'continuous shell',
        'source_ref': 'inputs/reference/source.png', 'model_revisions': {'villa': 1}}
    reply = ('NEEDS_FIX: YES\n<assessment>Wall seams remain.</assessment>\n'
        '<issue priority="1" view="front">problem: visible seam\naction: patch shell</issue>'
        '<review_requirements>'+json.dumps([requirement])+'</review_requirements>')
    native_calls = []
    def fake_inference(**kwargs):
        native_calls.append(kwargs)
        return native_agent.AgentTurnResult('critic', reply)
    monkeypatch.setattr(runtime, '_run_turn', fake_inference)
    views = {}
    for path in (tmp_path/'outputs/renders').glob('*.evidence.json'):
        data = json.loads(path.read_text()); views[data['canonical_view']] = data['path']
    result = runtime._native_visual_review(project_dir=tmp_path, agent_workspace=tmp_path/'runtime/agent_workspace',
        ruby_state={'villa': {'revision': 1, 'last_verification': {'verified': True}}},
        arguments={'views': views}, model='test-model', reasoning_effort='low')
    native_context = contexts[-1]
    assert api_context.metadata == native_context.metadata
    assert api_context.images == native_context.images
    assert api_context.evidence_prompt == native_context.evidence_prompt
    assert 'FACADE_SCHEDULE' in native_calls[0]['prompt']
    assert 'rear opening_count=3' in native_calls[0]['prompt']
    assert 'review_requirements' in api_context.prompt and 'Exact current host-granted' in api_context.prompt
    assert result['_reviewer']['review_requirements'][0]['feature_id'] == 'wall.seam'


def test_invalid_scope_never_leaks_stale_plan_text_into_review_prompt(tmp_path, monkeypatch):
    from app.review_context import prepare_review_context, validate_review_context_current
    context = _context(tmp_path)
    runtime = tmp_path/'runtime'; runtime.mkdir(exist_ok=True)
    stale_instruction = '把所有立面改为深色横带'
    current_instruction = '保持浅色立面，仅修复入口'
    scope = {'version': 6, 'valid': False, 'plan_text': stale_instruction,
             'features': [{'feature_id': 'facade.band', 'requested_state': stale_instruction}],
             'invalidation_reason': '旧方案要求：'+stale_instruction,
             'other_builder_payload': stale_instruction}
    scope_path = runtime/'approved_design_scope.json'
    scope_path.write_text(json.dumps(scope, ensure_ascii=False))
    monkeypatch.setattr('app.design_scope_approval.current_execution_instruction', lambda _: {
        'user_message_id': 'current-turn', 'user_message': current_instruction})
    prepared = prepare_review_context(tmp_path, context.revisions, {'front': context.images[-1]}, [])
    assert stale_instruction not in prepared.prompt
    assert current_instruction in prepared.prompt
    sanitized = prepared.metadata['approved_design_scope']
    assert sanitized['version'] == 6 and sanitized['valid'] is False
    assert sanitized['features'] == [] and 'plan_text' not in sanitized
    original_key = prepared.metadata['review_context_fingerprint']
    scope['plan_text'] = '不同但仍然失效的旧方案'
    scope_path.write_text(json.dumps(scope, ensure_ascii=False))
    changed = prepare_review_context(tmp_path, context.revisions, {'front': context.images[-1]}, [])
    assert changed.metadata['review_context_fingerprint'] != original_key
    with pytest.raises(ValueError, match='scope changed'):
        validate_review_context_current(prepared)
