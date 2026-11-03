"""Synthetic SSE adapter regression; never accesses a provider or user session."""
import json
import httpx
from app.workspace_files import workspace_file_call
from app.litellm_runtime import LiteLLMRuntime, _tool_result_parts
from app.read_repetition import ReadRepetitionTracker
from app import bai_transport


def test_workspace_pagination_and_api_read_advisory(tmp_path, monkeypatch):
    root = tmp_path
    workspace = root / 'workspace'
    (workspace / 'notes').mkdir(parents=True)
    file = workspace / 'notes/a.md'
    source = 'A\\B"\n' * 18000
    file.write_bytes(source.encode('utf-8'))
    batch = workspace_file_call(workspace, 'workspace_read_many', {'relative_paths':['notes/a.md','notes/missing.md','../escape']})
    assert batch['success'] and batch['results'][0]['complete'] is False
    assert not batch['results'][1]['success'] and not batch['results'][2]['success']
    row = batch['results'][0]
    pieces = [row['content']]
    while row['next_offset'] is not None:
        row = workspace_file_call(workspace, 'workspace_read', {'relative_path':'notes/a.md', 'offset':row['next_offset'], 'expected_sha256':row['file_sha256']})
        pieces.append(row['content'])
    assert ''.join(pieces) == source
    first = workspace_file_call(workspace, 'workspace_read', {'relative_path':'notes/a.md', 'offset':0, 'limit':10})
    file.write_bytes((source + 'changed').encode('utf-8'))
    try:
        workspace_file_call(workspace, 'workspace_read', {'relative_path':'notes/a.md','offset':first['next_offset'],'expected_sha256':first['file_sha256']})
        raise AssertionError('changed file accepted')
    except ValueError as e:
        assert 'changed' in str(e)
    for args in ({'relative_paths': ['../escape'] * 2}, {'relative_paths':['a'] * 5}, {'relative_paths':['notes/']}):
        try:
            result = workspace_file_call(workspace, 'workspace_read_many', args)
            assert all(not r['success'] for r in result['results'])
        except ValueError:
            pass
    full = workspace_file_call(workspace,'workspace_read', {'relative_path':'notes/a.md'})
    wire, _ = _tool_result_parts(full)
    encoded = json.loads(wire)
    assert len(wire) <= 60000 and encoded['transport_truncated'] and not encoded['complete']
    rest = workspace_file_call(workspace,'workspace_read', {'relative_path':'notes/a.md','offset':encoded['next_offset'],'expected_sha256':encoded['file_sha256']})
    assert encoded['content'] + rest['content'] == (source+'changed')[:len(encoded['content'])+len(rest['content'])]
    other, _ = _tool_result_parts({'success': True, 'data': 'x'*90000})
    assert json.loads(other)['transport_truncated'] is True
    print('PASS bounded valid JSON, batch paths, pagination and SHA change')

    tracker = ReadRepetitionTracker()
    args = {'relative_path':'notes/a.md'}
    assert not tracker.observe('workspace_read', args, full)
    assert not tracker.observe('workspace_read', args, full)
    assert tracker.observe('workspace_read', args, full)
    assert not tracker.observe('workspace_read', args, full)
    changed = dict(full, file_sha256='f'*64)
    assert not tracker.observe('workspace_read', args, changed)
    assert not tracker.observe('workspace_read', {'relative_path':'notes/other.md'}, full)
    assert not tracker.observe('sketchup_capture_review_views', args, full)
    tracker.before_tool('workspace_write')
    assert not tracker.observe('workspace_read', args, full)
    print('PASS repetition identity, SHA/path change, view exclusion and write boundary')

    requests = []
    original = bai_transport.complete_bai
    def server(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body['model'] == 'fixture-model'
        assert any(t['function']['name'] == 'workspace_read_many' for t in body['tools'])
        n = len(requests)
        if n == 1:
            name, args = 'workspace_read_many', {'relative_paths':['notes/reconstruction_card.md', 'notes/facade_schedule.json']}
        elif n in (2, 3, 4):
            previous = json.loads(body['messages'][-1]['content'])
            if n == 2:
                assert len(previous['results']) == 2
            if n == 4:
                assert 'host_notice' not in previous
            name, args = 'workspace_read', {'relative_path':'notes/reconstruction_card.md'}
        else:
            assert n == 5 and 'host_notice' in json.loads(body['messages'][-1]['content'])
            name, args = None, {}
        delta = {'tool_calls':[{'index':0,'id':'fixture-'+str(n),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]} if name else {'content':'已完成离线方案。'}
        chunks = [dict(model='fixture-model', choices=[dict(index=0,delta={'reasoning_content':'fixture-thinking'})]),
                  dict(model='fixture-model', choices=[dict(index=0,delta=delta)]),
                  dict(model='fixture-model', choices=[dict(index=0,delta={},finish_reason='tool_calls' if name else 'stop')]),
                  dict(model='fixture-model', choices=[],usage=dict(prompt_tokens=100,completion_tokens=5))]
        text = ''.join('data: '+json.dumps(c)+'\n\n' for c in chunks)+'data: [DONE]\n\n'
        return httpx.Response(200, headers={'content-type':'text/event-stream'}, text=text)
    monkeypatch.setattr(bai_transport, "complete_bai", lambda kwargs, record: original(kwargs, record=record, transport=httpx.MockTransport(server)))
    runtime = LiteLLMRuntime(root, model='openai/fixture-model')
    runtime.custom_api_base = 'https://api.b.ai/v1'
    runtime.session_api_key = 'fixture-key'
    runtime.completion_callable = lambda: lambda **_: (_ for _ in ()).throw(AssertionError('wrong transport'))
    project = root / 'project'
    result = runtime.respond(project_dir=project, thread_id=None, prompt='请整理方案。', mcp_enabled=False,
        ruby_enabled=False, developer_instructions='offline fixture', workflow_mode='image_reconstruction',
        tool_profile='reconstruction_coding')
    assert result.status == 'completed' and result.tool_call_count == 4 and result.failed_tool_calls == 0
    assert result.input_tokens == 500 and len(requests) == 5
    history = json.loads(next(project.rglob('litellm-*.json')).read_text(encoding='utf-8'))['messages']
    assert len([m for m in history if m['role']=='tool']) == 4
    assert all('fixture-thinking' in str(body['messages']) for body in requests[1:])
    assert not list(project.rglob('*.skp'))
    print('PASS real B.AI adapter + tool loop, saved tool IDs, thinking and advisory notice with mock SSE')
