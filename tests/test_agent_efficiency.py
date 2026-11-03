import json
from types import SimpleNamespace
import pytest
from app.context_compaction import compact_active_reconstruction_context
from app.agent_tools import AgentToolSurface, _CANONICAL_REVIEW_VIEWS
from app.sketchup_mcp import MCPCallError
from app.native_agent import NativeAgentUnavailable
from tests.test_api_execution_contracts import runtime, response, call, run


def test_long_single_turn_prunes_complete_exchanges_keeps_sources_and_human_keep():
    messages=[{"role":"system","content":"rules"},{"role":"user","content":[{"type":"text","text":"只改副本，屋顶保留"},{"type":"image_url","image_url":{"url":"data:image/png;base64,source"}}]}]
    for i in range(12):
        messages.extend([{"role":"assistant","content":None,"tool_calls":[call(str(i),"workspace_write")]},{"role":"tool","tool_call_id":str(i),"content":"x"*18000}])
        if i == 1:
            messages.append({'role': 'user', 'content': [
                {'type': 'text', 'text': 'Visual readback from SketchUp tool capture.'},
                {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,current-front'}}]})
    original=json.dumps(messages)
    slim,meta=compact_active_reconstruction_context(messages,"ACTIVE RECONSTRUCTION CHECKPOINT roof KEEP, latest revision12",compact_current_turn=True)
    assert meta["after_chars"] < meta["before_chars"] / 3
    assert slim[1]==messages[1] and slim[-4:]==messages[-4:]
    assert json.dumps(messages)==original
    assert [m["tool_call_id"] for m in slim if m["role"]=="tool"]==["10","11"]
    assert 'data:image/png;base64,current-front' in json.dumps(slim)
    messages.append({"role":"assistant","tool_calls":[call("unresolved")]})
    kept,meta=compact_active_reconstruction_context(messages,"checkpoint",compact_current_turn=True)
    assert kept==messages and not meta["compacted"]


def test_batch_capture_keeps_six_certified_views_and_rejects_revision_mix(tmp_path,monkeypatch):
    surface=AgentToolSurface(tmp_path,None,oss_backends={})
    actual=surface.dispatch; seen=[]; writer=SimpleNamespace(ruby_state={"owned":{"revision":6}})
    def capture(name,args,**kw):
        if name!="sketchup_capture_canonical_view":return actual(name,args,**kw)
        seen.append(args["view_name"])
        return {"success":True,"visual_evidence":{"canonical_view":args["view_name"],"model_revisions":{"owned":6},"path":args["view_name"]+".png"},"contentItems":[]}
    monkeypatch.setattr(surface,"dispatch",capture)
    result=actual("sketchup_capture_review_views",{"script_id":"owned"},project_dir=tmp_path,project_ruby=writer)
    assert seen==list(_CANONICAL_REVIEW_VIEWS) and set(result["views"])==set(_CANONICAL_REVIEW_VIEWS)
    writer.ruby_state["owned"]["revision"]=7
    with pytest.raises(MCPCallError,match="revision changed"):
        actual("sketchup_capture_review_views",{"script_id":"owned"},project_dir=tmp_path,project_ruby=writer)


def test_current_valid_review_does_not_force_paid_refinement(tmp_path,monkeypatch):
    r,effects,requests=runtime(tmp_path,monkeypatch,[response()])
    quality={"writes":6,"write_limit":0,"review":{"needs_fix":True,"issues":[{"problem":"glass appearance needs work"}]}}
    monkeypatch.setattr(r.tool_surface,"prepare",lambda **kw:SimpleNamespace(dynamic_tools=[],quality_state=quality,dispatch=lambda *a:effects.append(a)))
    result=r.respond(project_dir=tmp_path,thread_id=None,prompt="建模",mcp_enabled=True,ruby_enabled=False,developer_instructions="fixture",workflow_mode="image_reconstruction",tool_profile="reconstruction_coding")
    assert len(requests)==1 and not effects and "尚不能判定" in result.reply


def test_cancelled_api_response_retains_usage_and_closes_unexecuted_tool_ids(tmp_path,monkeypatch):
    r,effects,requests=runtime(tmp_path,monkeypatch,[response([call("a"),call("b")])])
    stopped=[False]
    complete=r.completion_callable()
    def paid_fixture(**kw):
        value=complete(**kw);stopped[0]=True;return value
    monkeypatch.setattr(r,"completion_callable",lambda:paid_fixture)
    with pytest.raises(NativeAgentUnavailable) as error:
        r.respond(project_dir=tmp_path,thread_id=None,prompt="建模",mcp_enabled=True,ruby_enabled=False,developer_instructions="fixture",cancel_requested=lambda:stopped[0])
    assert len(requests)==1 and effects==[] and error.value.partial_result.input_tokens==10
    saved=json.loads(next((tmp_path/"runtime/provider_sessions").glob("*.json")).read_text(encoding="utf-8"))["messages"]
    assert [m["tool_call_id"] for m in saved if m["role"]=="tool"]==["a","b"]


def test_stop_endpoint_accepts_api_without_native_interrupt_or_model_write(tmp_path):
    from tests.test_novice_flow import workspace
    app,client,project,_,su=workspace(tmp_path)
    app.state.active_turns[project]={"provider":"litellm","request_id":"current"}
    assert client.post(f"/api/projects/{project}/agent/cancel",json={"expected_request_id":"old"}).status_code==409
    result=client.post(f"/api/projects/{project}/agent/cancel",json={"expected_request_id":"current"})
    assert result.status_code==200 and result.json()["cancel_requested"] and not result.json()["terminal_confirmed"]
    assert not su.calls
