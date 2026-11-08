"""Owner-authorized network recovery, durable unknowns; no paid/native calls."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.dsh_configuration import resolve_configuration
from app.dsh_runtime import DSHHostSession
from app.dsh_test_budget import TestBatchBudget
from app.native_agent import NativeAgentUnavailable
from tests.test_dsh_test_budget import setup_batch, request, finish
from tests.test_official_dsh_local import enable_budget


def authorize(path, acknowledged=()):
    config=json.loads(path.read_text(encoding='utf-8-sig'))
    policy={'schema_version':1,'batch_id':config['batch_id'],
        'configuration_sha256':hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'authorization':{'status':'granted','reference':'Offline fixture owner decision'},
        'mode':'bounded-network-retry','max_consecutive_retries':2,
        'acknowledged_unknown_attempts':list(acknowledged)}
    target=path.with_name(path.stem+'.recovery.json')
    target.write_text(json.dumps(policy),encoding='utf8')
    return target


def fail(budget, data, code='TRANSPORT'):
    budget.settle({'attempt_id':data['attempt_id'],'finish_reason':'error',
                  'error_code':code,'usage':None})


def test_acknowledgement_preserves_unknown_and_original_ceilings(tmp_path):
    path,cfg=setup_batch(tmp_path,4);budget=TestBatchBudget(path,cfg)
    first=request();budget.reserve(first);fail(budget,first,code=None);budget.close()
    original=path.read_bytes();authorize(path,[first['attempt_id']])
    budget=TestBatchBudget(path,cfg)
    try:
        for _ in range(3):
            data=request();budget.reserve(data);finish(budget,data)
        with pytest.raises(ValueError,match='ceiling'):budget.reserve(request())
        with budget.connect() as db:
            rows=db.execute('SELECT status FROM attempts ORDER BY created').fetchall()
        assert rows==[('unknown',),('settled',),('settled',),('settled',)]
        assert path.read_bytes()==original
    finally:budget.close()


def test_two_retry_limit_survives_restart_and_unknowns_are_not_erased(tmp_path):
    path,cfg=setup_batch(tmp_path,10);authorize(path)
    for _ in range(3):
        budget=TestBatchBudget(path,cfg)
        data=request();budget.reserve(data);fail(budget,data);budget.close()
    budget=TestBatchBudget(path,cfg)
    try:
        with pytest.raises(ValueError,match='network retry limit'):budget.reserve(request())
        with budget.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM attempts WHERE status="unknown"').fetchone()==(3,)
    finally:budget.close()


@pytest.mark.parametrize('code',[None,'AUTHENTICATION','QUOTA','SERVER','RATE_LIMIT'])
def test_network_policy_never_releases_other_unknowns(tmp_path,code):
    path,cfg=setup_batch(tmp_path,10);authorize(path);budget=TestBatchBudget(path,cfg)
    try:
        data=request();budget.reserve(data);fail(budget,data,code)
        with pytest.raises(ValueError,match='unknown provider'):budget.reserve(request())
    finally:budget.close()


def test_pending_and_parallel_calls_cannot_multiply_retries(tmp_path):
    path,cfg=setup_batch(tmp_path,10);authorize(path)
    owners=[TestBatchBudget(path,cfg) for _ in range(4)]
    try:
        data=request();owners[0].reserve(data);fail(owners[0],data)
        owners[1].reserve(request());owners[2].reserve(request())
        with pytest.raises(ValueError,match='network retry limit'):owners[3].reserve(request())
    finally:
        for owner in owners:owner.close()


@pytest.mark.parametrize('change',['batch_id','configuration_sha256','authorization','max_consecutive_retries'])
def test_foreign_unapproved_or_expanded_recovery_rejected(tmp_path,change):
    path,cfg=setup_batch(tmp_path,10);target=authorize(path)
    policy=json.loads(target.read_text());policy[change]=3 if change=='max_consecutive_retries' else {} if change=='authorization' else 'other'
    target.write_text(json.dumps(policy))
    with pytest.raises(ValueError,match='authorization'):TestBatchBudget(path,cfg)


def test_recovery_decision_cannot_be_silently_rewritten(tmp_path):
    path,cfg=setup_batch(tmp_path,10);target=authorize(path)
    budget=TestBatchBudget(path,cfg);budget.close()
    policy=json.loads(target.read_text());policy['authorization']['reference']='changed decision'
    target.write_text(json.dumps(policy))
    with pytest.raises(ValueError,match='authorization changed'):TestBatchBudget(path,cfg)


@pytest.mark.parametrize('protocol',['openai-completions','openai-responses'])
@pytest.mark.parametrize('failures',[1,3])
def test_actual_official_sdk_recovers_or_stops_after_two_retries(tmp_path,monkeypatch,protocol,failures):
    sdk=os.environ.get('KSTUDIO_TEST_DSH_SDK_SITE');binary=os.environ.get('KSTUDIO_TEST_DSH_BIN')
    if not sdk or not binary:pytest.skip('Explicit pinned SDK paths required; no real provider')
    requests=[]
    class Provider(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            n=len(requests)
            if n<=failures:
                self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            def send(row):self.wfile.write(('data: '+json.dumps(row)+'\n\n').encode());self.wfile.flush()
            if protocol=='openai-completions':
                send({'id':'recovered','object':'chat.completion.chunk','model':'fixture-model',
                    'choices':[{'index':0,'delta':{'role':'assistant','content':'Recovered.'},'finish_reason':None}]})
                send({'id':'recovered','object':'chat.completion.chunk','model':'fixture-model',
                    'choices':[{'index':0,'delta':{},'finish_reason':'stop'}],
                    'usage':{'prompt_tokens':20,'completion_tokens':5,'total_tokens':25}})
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                item={'id':'m1','type':'message','role':'assistant','status':'in_progress','content':[]}
                send({'type':'response.created','response':{'id':'recovered','model':'fixture-model','status':'in_progress','output':[]}})
                send({'type':'response.output_item.added','output_index':0,'item':item})
                send({'type':'response.content_part.added','item_id':'m1','output_index':0,'content_index':0,'part':{'type':'output_text','text':'','annotations':[]}})
                send({'type':'response.output_text.delta','item_id':'m1','output_index':0,'content_index':0,'delta':'Recovered.'})
                item={**item,'status':'completed','content':[{'type':'output_text','text':'Recovered.','annotations':[]}]}
                send({'type':'response.output_item.done','output_index':0,'item':item})
                send({'type':'response.completed','response':{'id':'recovered','model':'fixture-model','status':'completed','output':[item],
                    'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25}}})
    server=ThreadingHTTPServer(('127.0.0.1',0),Provider)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    cfg=resolve_configuration({'api_base':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture-model',
        'mode':'codex-responses' if protocol=='openai-responses' else 'compatible',
        'capabilities_json':json.dumps({'tools':True,'streaming':True,'context_window':65536,'max_output_tokens':4096})})
    enable_budget(monkeypatch,tmp_path,cfg,6)
    path=Path(os.environ['KSTUDIO_TEST_BATCH_CONFIG']);authorize(path)
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','production-file-proxy')
    monkeypatch.delenv('KSTUDIO_DSH_MCP_CONFIG',raising=False)
    host=DSHHostSession(home=tmp_path/'home',workspace=tmp_path,api_base=cfg.endpoint,api_key='offline-fixture',
        model=cfg.model,specs=[],dispatch=lambda *_:pytest.fail('No native writes'),trace_path=tmp_path/'events.jsonl',
        sdk_site=Path(sdk),dsh_bin=Path(binary),effective_configuration=cfg,
        reasoning_effort=cfg.requested_effort,protocol=cfg.protocol,full_capabilities=True)
    try:
        if failures==1:
            assert host.run(prompt='Reply once.',images=[]).status=='completed'
            assert len(requests)==2
        else:
            with pytest.raises(NativeAgentUnavailable):host.run(prompt='Reply once.',images=[])
            assert len(requests)==3
            with pytest.raises(ValueError,match='network retry limit'):
                host.test_budget.reserve({'attempt_id':'11111111-1111-1111-1111-111111111111',
                    'provider':'kstudio-bai','model':cfg.model,'max_output_tokens':4096})
        with sqlite3.connect(path.parent/'dsh-test-batches.sqlite3') as db:
            rows=db.execute('SELECT status,usage_json FROM attempts ORDER BY created').fetchall()
        expected=['unknown','settled'] if failures==1 else ['unknown']*3
        assert [r[0] for r in rows]==expected
        assert all(json.loads(r[1])['error_code']=='TRANSPORT' for r in rows[:failures])
        (tmp_path/'network-recovery-receipt.json').write_text(json.dumps({'protocol':protocol,'http_requests':len(requests),
            'unknowns_retained':failures,'known_success':failures==1,'paid_calls':0,'native_writes':0}),encoding='utf8')
    finally:host.close();server.shutdown();server.server_close()
