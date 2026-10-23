"""Actual loopback HTTP + product dispatch; deterministic replies, no inference."""
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from benchmark_simulated_api_usage import ScriptedServer, run_case, summarize, tool_message, file_reply

@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv('HOME',str(tmp_path/'home'))
    monkeypatch.setenv('LITELLM_LOCAL_MODEL_COST_MAP','True')
    monkeypatch.setenv('NO_PROXY','127.0.0.1,localhost')
    monkeypatch.setenv('KSTUDIO_EXECUTION_LIMITS', 'on')


def test_actual_http_tool_pipeline_and_compaction(tmp_path):
    with_checkpoint=run_case(tmp_path,'long_chain_checkpoint',8)
    without=run_case(tmp_path,'long_chain_no_checkpoint',8)
    assert with_checkpoint['http_requests']==without['http_requests']==9
    assert with_checkpoint['results'][0]['tool_calls']==8
    assert with_checkpoint['results'][0]['failed_tool_calls']==0
    assert with_checkpoint['compacted_requests']>0
    assert without['compacted_requests']==0
    assert with_checkpoint['wire_body_bytes']<without['wire_body_bytes']
    assert with_checkpoint['image_attachment_count']==9


def test_actual_http_error_does_not_retry(tmp_path):
    result=run_case(tmp_path,'http_503_no_retry')
    assert result['http_requests']==1
    assert result['results'][0]['status']=='interrupted'
    assert result['results'][0]['tool_calls']==0


def test_failed_tool_then_explicit_scripted_repair(tmp_path):
    result=run_case(tmp_path,'tool_error_recovery')
    assert result['http_requests']==3
    assert result['results'][0]['tool_calls']==2
    assert result['results'][0]['failed_tool_calls']==1
    assert not (tmp_path/'forbidden').exists()


def test_changed_instruction_and_source_dedup_on_wire(tmp_path):
    result=run_case(tmp_path,'changed_instruction')
    full=json.loads((tmp_path/'changed_instruction/result.json').read_text())
    second=full['requests'][1]['body']['messages']
    assert 'NEW USER: only inspect roof now; do not add roads.' in json.dumps(second)
    assert 'Only inspect the main building. KEEP wall unchanged.' in json.dumps(second)
    assert result['image_attachment_count']==2  # one per request, not 1+2
    assert result['http_requests']==2


def test_real_sse_transport_parses_tool_and_usage():
    from app.bai_transport import complete_bai
    with ScriptedServer([tool_message('workspace_read', {'relative_path':'notes/a.md'},'a')]) as server:
        response=complete_bai({'model':'openai/local-scripted-model','api_key':'not-a-real-key',
                             'api_base':server.base_url,'messages':[{'role':'user','content':'test'}]})
        assert response.choices[0].message['tool_calls'][0]['function']['name']=='workspace_read'
        assert len(server.requests)==1
        assert server.requests[0]['body']['stream'] is True
        assert response.usage['prompt_tokens']==server.requests[0]['estimated_text_tokens']


def test_manual_relay_is_explicit_and_bounded(tmp_path):
    response={'role':'assistant','content':'human or assistant supplied, not model inference'}
    (tmp_path/'response-000.json').write_text(json.dumps(response))
    relay=file_reply(tmp_path,timeout_seconds=0.2)
    assert relay({'messages':[]})==response
    assert (tmp_path/'request-000.json').is_file()
    assert relay({'messages':[]})=={'http_error':504}
