import pytest
from app import native_agent as subject

def test_independent_native_critic_has_fresh_read_only_context(tmp_path, monkeypatch):
    project=tmp_path/'project'; workspace=project/'runtime/agent_workspace'; workspace.mkdir(parents=True)
    source=project/'inputs/reference/source.png'; source.parent.mkdir(parents=True); source.write_bytes(b'source')
    image=project/'outputs/renders/agent-view-front.png'; image.parent.mkdir(parents=True); image.write_bytes(b'current')
    monkeypatch.setattr(subject, 'validate_visual_review_views', lambda *args: ({'cafe':3},{},{'front':image}))
    monkeypatch.setattr(subject, 'validate_source_matched_pairs', lambda *args: [])
    runtime=subject.CodexAppServerRuntime(tmp_path, codex_executable='fixture')
    calls=[]
    def run(**kw):
        calls.append(kw)
        return subject.AgentTurnResult('critic', 'NEEDS_FIX: YES\n<assessment>Missing annex</assessment>\n<issue priority="1" view="right">problem: lower roof missing\naction: add attached roof</issue>\n<keep>entry</keep>',model_name='gpt-6-luna',reasoning_effort='max')
    monkeypatch.setattr(runtime,'_run_turn',run)
    result=runtime._native_visual_review(project_dir=project,agent_workspace=workspace,ruby_state={},arguments={'views':{},'critique':'BUILDER_FAKE_PASS'},model='gpt-6-luna',reasoning_effort='max')
    call=calls[0]
    assert call['read_only'] is True and call['thread_id'] is None
    assert not call['mcp_enabled'] and call['dynamic_tools']==[]
    assert 'BUILDER_FAKE_PASS' not in call['prompt']
    assert 'Do not protect an entire roof or volume' in call['prompt']
    assert call['reference_images']==[source,image]
    assert result['_reviewer']['mode']=='dedicated_read_only'
    assert 'Missing annex' in result['critique']
    monkeypatch.setattr(subject, 'validate_source_matched_pairs', lambda *args: [
        {'current_view':'outputs/renders/agent-view-front.png','label':'ramp end'},
        {'current_view':'outputs/renders/agent-view-front.png','label':'roof section'},
    ])
    runtime._native_visual_review(project_dir=project,agent_workspace=workspace,ruby_state={},arguments={'views':{}},model='gpt-6-luna',reasoning_effort='max')
    assert calls[-1]['reference_images']==[source,image]
    assert 'source-matched ramp end' in calls[-1]['prompt']
    assert 'source-matched roof section' in calls[-1]['prompt']
    monkeypatch.setattr(runtime,'_run_turn',lambda **kw: subject.AgentTurnResult('critic','PASS'))
    with pytest.raises(ValueError,match='invalid envelope'):
        runtime._native_visual_review(project_dir=project,agent_workspace=workspace,ruby_state={},arguments={'views':{},'critique':'BUILDER_FAKE_PASS'},model='gpt-6-luna',reasoning_effort='max')

def test_native_read_only_policy_and_resumed_usage_delta(tmp_path, monkeypatch):
    import io,json
    class Process:
        stdout=io.BytesIO(); stdin=io.BytesIO()
        def poll(self): return 0
    monkeypatch.setattr(subject.subprocess,'Popen',lambda *a,**kw:Process())
    runtime=subject.CodexAppServerRuntime(tmp_path,codex_executable='fixture')
    requests=[]; sent=[]
    def request(*args):
        requests.append(args[4])
        return {'thread':{'id':'fresh-critic'}}
    monkeypatch.setattr(runtime,'_request',request)
    monkeypatch.setattr(runtime,'_send',lambda p,msg:sent.append(msg))
    def usage(i,o,li,lo):
        return {'method':'thread/tokenUsage/updated','params':{'tokenUsage':{'total':{'inputTokens':i,'outputTokens':o},'last':{'inputTokens':li,'outputTokens':lo}}}}
    events=iter([usage(1050,208,50,8),usage(1130,219,80,11),{'method':'turn/completed','params':{'turn':{'status':'completed'}}}])
    monkeypatch.setattr(runtime,'_next_event',lambda *a:next(events))
    project=tmp_path/'project'; workspace=project/'runtime/agent_workspace';workspace.mkdir(parents=True)
    result=runtime._run_turn(project_dir=project,agent_workspace=workspace,thread_id=None,prompt='review',mcp_enabled=False,developer_instructions='review',dynamic_tools=[],tool_handler=lambda *a:{},model='gpt-6-luna',reasoning_effort='max',reference_images=[],read_only=True)
    assert result.input_tokens==130 and result.output_tokens==19
    assert requests[1]['sandbox']=='read-only'
    assert requests[1]['dynamicTools']==[]
    turn=next(m for m in sent if m.get('method')=='turn/start')
    assert turn['params']['sandboxPolicy']=={'type':'readOnly','networkAccess':False}
    log=next((project/'runtime/agent_events').glob('*.jsonl'))
    recorded=[json.loads(line) for line in log.read_text().splitlines()]
    assert next(e for e in recorded if e['event']=='turn_input')['role']=='visual_critic'
    assert next(e for e in recorded if e['event']=='project_budget_finished')['input_tokens']==130


def test_returned_native_model_mismatch_blocks_inference(tmp_path,monkeypatch):
    import io
    class Process:
        stdout=io.BytesIO(); stdin=io.BytesIO()
        def poll(self):return 0
    monkeypatch.setattr(subject.subprocess,'Popen',lambda *_args,**_kw:Process())
    runtime=subject.CodexAppServerRuntime(tmp_path,codex_executable='fixture')
    monkeypatch.setattr(runtime,'_request',lambda *args:{'model':'wrong-model','thread':{'id':'fixture'}})
    sent=[]
    monkeypatch.setattr(runtime,'_send',lambda p,msg:sent.append(msg))
    project=tmp_path/'project';workspace=project/'runtime/agent_workspace';workspace.mkdir(parents=True)
    with pytest.raises(subject.NativeAgentUnavailable,match='different model'):
        runtime._run_turn(project_dir=project,agent_workspace=workspace,thread_id=None,prompt='fixture',
            mcp_enabled=False,developer_instructions='fixture',dynamic_tools=[],tool_handler=lambda *_:{},
            model='gpt-6.1-sol',reasoning_effort='low',reference_images=[])
    assert not any(m.get('method')=='turn/start' for m in sent)

def test_compact_model_bootstrap_starts_actual_new_thread(tmp_path, monkeypatch):
    import io,json
    class Process:
        stdout=io.BytesIO();stdin=io.BytesIO()
        def poll(self): return 0
    monkeypatch.setattr(subject.subprocess,'Popen',lambda *_a,**_k:Process())
    runtime=subject.CodexAppServerRuntime(tmp_path,codex_executable='fixture')
    methods=[]
    def request(*args):
        methods.append(args[3]);return {'model':'gpt-6.1-sol','thread':{'id':'fresh'}}
    monkeypatch.setattr(runtime,'_request',request)
    monkeypatch.setattr(runtime,'_send',lambda *_:None)
    monkeypatch.setattr(runtime,'_next_event',lambda *_:{'method':'turn/completed','params':{'turn':{'status':'completed'}}})
    project=tmp_path/'project';workspace=project/'runtime/agent_workspace';workspace.mkdir(parents=True)
    (project/'runtime/native_thread_tools.json').write_text(json.dumps({'old':subject._thread_tool_fingerprint([])}))
    runtime._run_turn(project_dir=project,agent_workspace=workspace,thread_id='old',prompt='user',mcp_enabled=True,
        developer_instructions='policy',dynamic_tools=[],tool_handler=lambda *_:{},model='gpt-6.1-sol',reasoning_effort='low',
        reference_images=[],tool_profile='reconstruction_coding',compact_project_context=True)
    assert 'thread/start' in methods and 'thread/resume' not in methods

def test_harness_parity_fresh_builder_receives_small_verified_spatial_memory():
    from app.native_agent import _verified_review_checkpoint_prompt
    review = {"review_reused": True, "review": {
        "issues": [
            {"priority": 1, "view": "front", "problem": "wrong screen enclosure", "action": "fix SCREENS"},
            {"priority": 2, "view": "right", "problem": "missing recessed wall", "action": "fix ENVELOPE"},
        ],
        "keep": ["SITE"],
    }}
    p = _verified_review_checkpoint_prompt(review)
    assert "wrong screen enclosure" in p
    assert "missing recessed wall" in p
    assert "another six-view capture" in p
    assert "The latest human request controls intent" in p
    assert _verified_review_checkpoint_prompt({"review_reused": False, "review": review["review"]}) == ""
    assert _verified_review_checkpoint_prompt({"review_reused": True, "review": {"issues": []}})


def test_actual_codex_native_context_mode_needs_identical_source_bytes_and_tool_specs(tmp_path):
    from app.native_agent import (_reference_images_fingerprint, _native_thread_can_resume,
                                  _thread_tool_fingerprint)
    root = tmp_path / "project"
    source = root / "inputs/reference/photo.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source version A")
    alternate = root / "inputs/reference/angle.png"
    alternate.write_bytes(b"second image")
    tools = [{"type": "function", "name": "sketchup", "description": "verified"}]
    fp = _reference_images_fingerprint(root, [source, alternate])
    assert fp != _reference_images_fingerprint(root, [alternate, source])
    registration = {"codex-thread": _thread_tool_fingerprint(tools)}
    image_registry = {"codex-thread": fp}
    kwargs = dict(compact_restart=True, native_mode=True)
    assert _native_thread_can_resume("codex-thread", registration, image_registry, tools, fp, **kwargs)
    assert not _native_thread_can_resume("codex-thread", registration, image_registry, tools, fp,
                                         compact_restart=True, native_mode=False)
    assert not _native_thread_can_resume("codex-thread", registration, {}, tools, fp, **kwargs)
    assert not _native_thread_can_resume("codex-thread", registration, image_registry,
                                         tools + [{"type": "function", "name": "new"}], fp, **kwargs)
    source.write_bytes(b"source version B")
    assert not _native_thread_can_resume("codex-thread", registration, image_registry, tools,
                                         _reference_images_fingerprint(root, [source, alternate]), **kwargs)
    assert _native_thread_can_resume("codex-thread", registration, {}, tools, fp,
                                     compact_restart=False, native_mode=False)


def test_harness_first_skill_keeps_human_goal_and_visual_safety(monkeypatch):
    from app.workflow_context import load_workflow_skill_context
    monkeypatch.setenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE", "harness")
    prompt = load_workflow_skill_context("image_reconstruction", mcp_enabled=True)
    assert "actual user goal" in prompt
    assert "primary form" in prompt
    assert "host-owned" in prompt
    assert "AGENTS.md" in prompt
    assert len(prompt) < 3800
    monkeypatch.delenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE")
    legacy = load_workflow_skill_context("image_reconstruction", mcp_enabled=True)
    assert len(legacy) > len(prompt)


def test_site_real_app_server_native_thread_resume_and_source_change_fails_closed(tmp_path, monkeypatch):
    import io, json
    from app import native_agent as subject
    class Process:
        stdout=io.BytesIO(); stdin=io.BytesIO()
        def poll(self): return 0
    monkeypatch.setenv("ARCH_STUDIO_CODEX_RECONSTRUCTION_THREAD_MODE", "native")
    monkeypatch.setattr(subject.subprocess, "Popen", lambda *_args, **_kwargs: Process())
    runtime = subject.CodexAppServerRuntime(tmp_path, codex_executable="fixture")
    requested = []
    def request(*args):
        requested.append(args[3])
        return {"model": "gpt-6.1-sol", "reasoningEffort": "medium", "thread": {"id": "source-bound"}}
    monkeypatch.setattr(runtime, "_request", request)
    monkeypatch.setattr(runtime, "_send", lambda *_: None)
    monkeypatch.setattr(runtime, "_next_event", lambda *_: {"method": "turn/completed", "params": {"turn": {"status": "completed"}}})
    project = tmp_path/"project"
    workspace = project/"runtime/agent_workspace"
    workspace.mkdir(parents=True)
    source = project/"inputs/reference/source.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"first user source")
    kwargs = dict(project_dir=project,agent_workspace=workspace,prompt="real Chinese prompt",
                  mcp_enabled=True,developer_instructions="guarded instruction",
                  dynamic_tools=[],tool_handler=lambda *_:{},
                  model="gpt-6.1-sol",reasoning_effort="medium",reference_images=[source],
                  tool_profile="reconstruction_coding",compact_project_context=True)
    runtime._run_turn(thread_id=None, **kwargs)
    assert requested[-1] == "thread/start"
    assert json.loads((project/"runtime/native_thread_images.json").read_text())["source-bound"]
    runtime._run_turn(thread_id="source-bound", **kwargs)
    assert requested[-1] == "thread/resume"
    source.write_bytes(b"changed uploaded user source")
    runtime._run_turn(thread_id="source-bound", **kwargs)
    assert requested[-1] == "thread/start"


def test_harness_first_developer_stage_is_bounded_and_does_not_open_write_gate(monkeypatch):
    from app.workflow_context import workflow_developer_instructions
    monkeypatch.setenv("ARCH_STUDIO_RECONSTRUCTION_PROMPT_PROFILE", "harness")
    discussion = workflow_developer_instructions("image_reconstruction", mcp_enabled=False, action="clarify")
    assert "no scripts or geometry writes" in discussion
    assert "writer tools are withheld" in discussion
    plan = workflow_developer_instructions("image_reconstruction", mcp_enabled=False, action="plan")
    assert "notes/reconstruction_card.md" in plan
    assert "no geometry writes" in plan
    execute = workflow_developer_instructions("image_reconstruction", mcp_enabled=True, action="execute")
    assert "same verified model" in execute.lower()
    assert "independent" in execute and "scope" in execute
    assert "Never use project Ruby to access files" in execute
    assert len(execute) < 2900
