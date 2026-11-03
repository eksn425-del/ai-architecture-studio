from app.stage_quality import ReviewProgress


def observe(p, row, geometry='a'):
    p.observe(row, host_observation={'model_revisions': row['model_revisions'],
                                    'geometry_sha256': geometry * 64})


def receipt(revision, wording='seam still open', *, desired='closed', goal=None, features=('wall.seam',)):
    requirements = [{'feature_id': fid, 'desired_state': desired,
                     'requirement_id': f'{fid}-{revision}',
                     'prior_requirement_id': f'{fid}-{revision-1}',
                     'relation': 'equivalent' if revision > 1 else 'new',
                     'model_revisions': {'root': revision}}
                    for fid in features]
    reviewer = {'review_requirements': requirements, 'requirement_resolutions': []}
    if goal is not None:
        reviewer['review_context_fingerprint'] = goal
    return {'needs_fix': True, 'model_revisions': {'root': revision},
            'issues': [{'view': 'rear', 'problem': wording}], 'reviewer': reviewer}


def test_paraphrase_is_same_structured_defect():
    p = ReviewProgress()
    for rev, words in enumerate(['open seam', 'gap remains', 'wall still disconnected'], 1):
        observe(p, receipt(rev, words, desired=words))
    assert p.blocked


def test_durable_restart_and_same_revision_reread(tmp_path):
    path = tmp_path / 'progress.json'
    p = ReviewProgress(path, context_fingerprint='goal1')
    observe(p, receipt(1)); observe(p, receipt(2))
    p = ReviewProgress(path, context_fingerprint='goal1')
    observe(p, receipt(2)); observe(p, receipt(1))
    assert not p.blocked
    observe(p, receipt(3))
    assert p.blocked
    assert ReviewProgress(path, context_fingerprint='goal1').blocked
    assert not ReviewProgress(path, context_fingerprint='goal2').blocked


def test_legacy_a_b_a_cycle():
    p = ReviewProgress()
    for rev, words in enumerate(['gap in wall', 'roof slope wrong', 'gap in wall'], 1):
        p.observe({'needs_fix': True, 'model_revisions': {'root': rev},
                   'issues': [{'view': 'front', 'problem': words}]})
    assert not p.blocked and p.advisory_stagnation


def test_arbitrary_changed_measurement_not_progress():
    p = ReviewProgress()
    for rev in range(1, 4):
        row = receipt(rev)
        row['reviewer']['review_requirements'][0]['distance_to_target'] = 10 - rev
        p.observe(row)
    assert not p.blocked and p.advisory_stagnation  # Optional numbers prove neither progress nor stagnation.


def test_explicit_resolution_is_progress_and_changed_goal_not_stopped():
    p = ReviewProgress()
    observe(p, receipt(1, features=('wall.seam', 'door.width')))
    observe(p, receipt(2, features=('wall.seam', 'door.width')))
    row = receipt(3)
    row['reviewer']['requirement_resolutions'] = [{
        'feature_id': 'door.width', 'prior_requirement_id': 'door.width-2',
        'status': 'resolved', 'model_revisions': {'root': 3}}]
    observe(p, row)
    assert not p.blocked
    observe(p, receipt(4)); observe(p, receipt(5))
    assert p.blocked
    fresh_goal = ReviewProgress(context_fingerprint='new goal')
    fresh_goal.observe(receipt(6, goal='new goal'))
    assert not fresh_goal.blocked


def test_omission_does_not_resolve_and_malformed_ignored():
    p = ReviewProgress()
    p.observe({'needs_fix': True, 'issues': [{'problem': 'missing revision'}]})
    assert not p.blocked
    observe(p, receipt(1, features=('wall.seam', 'door.width')))
    observe(p, receipt(2)); observe(p, receipt(3))
    assert p.blocked


def test_legacy_fallback_does_not_guess_semantic_equivalence():
    p = ReviewProgress()
    for rev, problem in enumerate(['gap in wall', 'roof slope wrong', 'door too tall'], 1):
        p.observe({'needs_fix': True, 'model_revisions': {'root': rev},
                   'issues': [{'view': 'front', 'problem': problem}]})
    assert not p.blocked


def test_progress_scope_ignores_turn_id_but_not_goal_or_source(tmp_path, monkeypatch):
    from app.review_progress import current_progress_context_fingerprint
    instruction = {'user_message_id': 'turn1', 'user_message': 'repair wall',
                   'starting_model_revisions': {'root': 1}}
    monkeypatch.setattr('app.review_context.review_intent_context', lambda _: {
        'approved_design_scope': {}, 'current_user_instruction': instruction})
    first = current_progress_context_fingerprint(tmp_path)
    instruction.update(user_message_id='turn2', starting_model_revisions={'root': 3})
    assert current_progress_context_fingerprint(tmp_path) == first
    instruction['user_message'] = 'remove wall'
    assert current_progress_context_fingerprint(tmp_path) != first


def test_corrupt_state_does_not_silently_reset(tmp_path):
    path = tmp_path / 'progress.json'
    path.write_text('{broken')
    progress = ReviewProgress(path)
    assert progress.blocked and progress.reason == 'progress_state_unreadable'


def test_accepted_text_cannot_resolve_omitted_requirements():
    p = ReviewProgress()
    for rev in range(1, 4):
        observe(p, receipt(rev))
    accepted = receipt(4, features=())
    accepted['needs_fix'] = False
    p.observe(accepted)
    assert p.blocked


def test_prepare_restart_keeps_stagnation_with_limits_disabled(tmp_path, monkeypatch):
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError
    import pytest
    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs['ruby_state']
    monkeypatch.setattr('app.agent_tools.ProjectRubyExecutor', Executor)
    monkeypatch.setenv('KSTUDIO_EXECUTION_LIMITS', 'off')
    monkeypatch.setattr('app.agent_tools.load_current_independent_visual_review', lambda *a: None)
    monkeypatch.setattr('app.agent_tools.submit_visual_review',
                        lambda project, state, args: {k:v for k,v in receipt(state['root']['revision']).items() if k != 'reviewer'})
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, 'dynamic_tools', lambda **kw: [])
    monkeypatch.setattr(surface, 'dispatch', lambda *a, **kw: {'success': True})
    for revision in range(1, 4):
        context = surface.prepare(project_dir=tmp_path, mcp_enabled=True,
            model_path=tmp_path/'fixture.skp', model_guid='fixture', ruby_enabled=True,
            ruby_state={'root': {'revision': revision}}, tool_profile='reconstruction_coding')
        context.dispatch('sketchup_submit_visual_review', {})
    assert context.quality_state['write_limit'] == 0
    context = surface.prepare(project_dir=tmp_path, mcp_enabled=True,
        model_path=tmp_path/'fixture.skp', model_guid='fixture', ruby_enabled=True,
        ruby_state={'root': {'revision': 3}}, tool_profile='reconstruction_coding')
    assert context.quality_state['advisory_stagnation']
    assert not context.quality_state['no_progress']
    assert context.dispatch('sketchup_get_model_info', {})['success']


def test_partial_improvement_with_same_requirement_does_not_block():
    p = ReviewProgress()
    for revision, geometry in enumerate('abcdef', 1):
        observe(p, receipt(revision), geometry)
        assert not p.blocked
    assert p.advisory_stagnation  # Need measurements, not a hidden correction cap.


def test_host_geometry_a_b_a_and_stale_observation():
    p = ReviewProgress()
    for revision, geometry in enumerate('aba', 1):
        observe(p, receipt(revision), geometry)
    assert p.blocked and p.reason == 'verified_outcome_repeat'
    p = ReviewProgress()
    for revision in range(1, 4):
        p.observe(receipt(revision), host_observation={
            'model_revisions': {'root': 0}, 'geometry_sha256': 'a' * 64})
    assert not p.blocked


def test_fresh_review_intent_race_rejected_before_writer(tmp_path, monkeypatch):
    from app.agent_tools import AgentToolSurface
    from app.sketchup_mcp import MCPCallError
    import pytest
    class Executor:
        def __init__(self, *args, **kwargs):
            self.ruby_state = kwargs['ruby_state']
    monkeypatch.setattr('app.agent_tools.ProjectRubyExecutor', Executor)
    monkeypatch.setattr('app.agent_tools.load_current_independent_visual_review', lambda *a: None)
    row = receipt(1)
    row['reviewer']['review_context_fingerprint'] = 'old-intent'
    monkeypatch.setattr('app.agent_tools.submit_visual_review', lambda *a: row)
    monkeypatch.setattr('app.review_context.current_review_context_fingerprint', lambda *a: 'new-intent')
    surface = AgentToolSurface(tmp_path, object(), oss_backends={})
    monkeypatch.setattr(surface, 'dynamic_tools', lambda **kw: [])
    def no_write(*a, **kw):
        raise AssertionError('Writer must not run')
    monkeypatch.setattr(surface, 'dispatch', no_write)
    context = surface.prepare(project_dir=tmp_path, mcp_enabled=True,
        model_path=tmp_path/'fixture.skp', model_guid='fixture', ruby_enabled=True,
        ruby_state={'root': {'revision': 1, 'root_pid': 10}}, tool_profile='reconstruction_coding')
    context.dispatch('sketchup_submit_visual_review', {})
    with pytest.raises(MCPCallError, match='intent or source scope changed'):
        context.dispatch('sketchup_run_workspace_ruby', {})
    with pytest.raises(MCPCallError):
        context.dispatch('sketchup_run_workspace_ruby', {})
