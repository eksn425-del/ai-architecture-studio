import json
from types import SimpleNamespace
import pytest
from app.litellm_runtime import LiteLLMRuntime
from app.stage_quality import geometry_stage_limit
from tests.test_api_execution_contracts import response, call, run
from tests.test_novice_flow import workspace
from app.design_scope_approval import capture_pending_design_plan, consume_pending_design_plan
from app.models import AgentSession

@pytest.mark.parametrize("tool", ["sketchup_run_workspace_ruby", "workspace_write"])
def test_owner_mode_continues_past_48_calls_and_three_failures(tmp_path, monkeypatch, tool):
    monkeypatch.setenv("KSTUDIO_EXECUTION_LIMITS", "off")
    r=LiteLLMRuntime(tmp_path,model="deepseek/deepseek-flash")
    r.session_api_key="fixture-not-real"
    seen=[]
    def completion(**kw):
        seen.append(kw)
        return response([call(str(len(seen)),tool,json.dumps({"relative_path":"notes/test.md"}))]) if len(seen)<=52 else response()
    monkeypatch.setattr(r,"completion_callable",lambda:completion)
    attempted=[]
    def dispatch(*args):
        attempted.append(args)
        return {"success":len(attempted)>4,"text":"fixture validation failure"}
    monkeypatch.setattr(r.tool_surface,"prepare",lambda **kw:SimpleNamespace(dynamic_tools=[{"name":tool,"inputSchema":{"type":"object"}}],quality_state={},dispatch=dispatch))
    result=run(r,tmp_path)
    assert result.status=="completed" and len(attempted)==52 and len(seen)==53
    assert result.failed_tool_calls==4
    events=next((tmp_path/"runtime/agent_events").glob("*.jsonl")).read_text()
    assert "retry_budget_exhausted" not in events
    assert geometry_stage_limit(False)==("initial_build",0)
    assert geometry_stage_limit(True)==("targeted_repair",0)


def pending_fixture(tmp_path):
    app,client,project,agent,su=workspace(tmp_path)
    root=tmp_path/"runtime/projects"/project
    card=root/"runtime/agent_workspace/notes/reconstruction_card.md"
    card.parent.mkdir(parents=True,exist_ok=True);card.write_text("same owner plan",encoding="utf-8")
    snapshot=capture_pending_design_plan(root,"same owner plan",is_followup=False)
    consume_pending_design_plan(root,snapshot["pending_plan_id"])
    model=root/"outputs/model/blank-disposable-fixture.skp"
    model.parent.mkdir(parents=True,exist_ok=True);model.write_bytes(b"native-fixture")
    session=AgentSession(project_id=project,status="ready",reconstruction_state="planned",model_path=str(model.relative_to(root)))
    app.state.store.save_state(project,session,"agent_session.json")
    su.active_model_path=str(model)
    return app,client,project,root,snapshot,su


def test_retry_plan_proves_empty_model_and_requires_fresh_approval(tmp_path):
    app,client,project,root,snapshot,su=pending_fixture(tmp_path)
    result=client.post(f"/api/projects/{project}/agent/retry-plan",json={"pending_plan_id":snapshot["pending_plan_id"]})
    assert result.status_code==200,result.text
    new=result.json()
    assert not new["execution_started"] and not new["model_changed"]
    assert new["pending_plan_id"]!=snapshot["pending_plan_id"]
    assert (root/"runtime/plan_retry_history.jsonl").is_file()
    assert all(name in {"get_model_info","get_active_model_identity"} for name,_ in su.calls)
    assert client.post(f"/api/projects/{project}/agent/retry-plan",json={"pending_plan_id":snapshot["pending_plan_id"]}).status_code==409


@pytest.mark.parametrize("change",["nonempty","wrong-document","changed-plan","busy","committed","timeout"])
def test_retry_refuses_uncertain_or_changed_evidence(tmp_path,monkeypatch,change):
    app,client,project,root,snapshot,su=pending_fixture(tmp_path)
    original=(root/"runtime/pending_design_scope.json").read_bytes()
    if change=="nonempty":monkeypatch.setattr(su,"get_model_info",lambda:{"entity_count":1})
    if change=="wrong-document":su.active_model_path=str(root/"other.skp")
    if change=="changed-plan":(root/"runtime/agent_workspace/notes/reconstruction_card.md").write_text("new",encoding="utf-8")
    if change=="committed":
        state=app.state.store.load_state(project,"agent_session.json",AgentSession)
        state.ruby_state={"owned":{"revision":1}};app.state.store.save_state(project,state,"agent_session.json")
    if change=="timeout":
        from app.sketchup_mcp import MCPCallError
        def failed():raise MCPCallError("fixture bridge timed out")
        monkeypatch.setattr(su,"get_model_info",failed)
    if change=="busy":app.state.agent_lock.acquire()
    try:result=client.post(f"/api/projects/{project}/agent/retry-plan",json={"pending_plan_id":snapshot["pending_plan_id"]})
    finally:
        if change=="busy":app.state.agent_lock.release()
    assert result.status_code in {409,502}
    assert (root/"runtime/pending_design_scope.json").read_bytes()==original
