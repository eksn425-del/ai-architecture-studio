from types import SimpleNamespace
import pytest
from app.dsh_runtime import DSHHostSession
from app.native_agent import NativeAgentUnavailable


@pytest.mark.parametrize('requested,finish,expected', [
    (True, 'aborted', 'interrupted'),
    (False, 'aborted', 'failed'),
    (True, 'error', 'interrupted_failure'),
])
def test_only_acknowledged_user_abort_is_normal_interruption(requested, finish, expected):
    host = DSHHostSession.__new__(DSHHostSession)
    host.effective_configuration = SimpleNamespace(vision=True, tools=True, streaming=True, evidence=lambda: {})
    host.specs=[];host.full_capabilities=False;host.calls=[{'name':'writer','success':True}]
    host.events=[];host.cancelled=requested;host.api_key='fixture';host.token='fixture-token'
    host.native_recovery_required=False
    host.model='fixture-model';host.reasoning_effort='low';host.start=lambda: None
    recorded=[];host.record=recorded.append;host.emit_progress=lambda event: None
    result=SimpleNamespace(session_id='same-session',events=[],final_response='',finish_reason=finish)
    session=SimpleNamespace(id='same-session',run=lambda *a,**kw: result)
    host.harness=SimpleNamespace(start_session=lambda: session)
    if expected == 'interrupted':
        turn=host.run(prompt='continue', images=[])
        assert turn.status=='interrupted' and turn.cancellation_requested
        assert turn.thread_id=='same-session' and turn.tool_call_count==1
        assert turn.tool_calls==[{'tool':'writer','status':'completed'}]
        assert any(e.get('event')=='turn_interrupted' for e in recorded)
    else:
        with pytest.raises(NativeAgentUnavailable) as exc:
            host.run(prompt='continue', images=[])
        assert exc.value.partial_result.tool_call_count==1
        assert any(e.get('event')=='turn_failed' for e in recorded)
