import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.dsh_configuration import resolve_configuration
from app.dsh_test_budget import TestBatchBudget


def setup_batch(tmp_path,max_requests=2):
    connection={'api_base':'http://127.0.0.1:1/v1','model':'fixture','capabilities_json':json.dumps({'tools':True,'streaming':True})}
    cfg=resolve_configuration(connection)
    spec={'schema_version':1,'authorization':{'status':'local_fixture'},'batch_id':'fixture-batch','api_base':cfg.endpoint,'model':cfg.model,'protocol':cfg.protocol,
          'max_requests':max_requests,'max_output_tokens':cfg.max_output_tokens,'reserved_tokens_per_request':cfg.context_window+cfg.max_output_tokens,
          'max_reserved_tokens':max_requests*(cfg.context_window+cfg.max_output_tokens),'billing_guarantee':False}
    path=tmp_path/'batch.json';path.write_text(json.dumps(spec));return path,cfg


def request():return {'attempt_id':str(uuid.uuid4()),'provider':'kstudio-bai','model':'fixture','session_id':str(uuid.uuid4()),'max_output_tokens':4096}


def finish(budget,data):budget.settle({'attempt_id':data['attempt_id'],'finish_reason':'stop','usage':{'inputTokens':10,'outputTokens':5}})


def test_ceiling_persists_across_sessions_and_cannot_reconfigure(tmp_path):
    path,cfg=setup_batch(tmp_path)
    for _ in range(2):
        budget=TestBatchBudget(path,cfg);data=request();budget.reserve(data);finish(budget,data);budget.close()
    budget=TestBatchBudget(path,cfg)
    try:
        with pytest.raises(ValueError,match='ceiling'):budget.reserve(request())
    finally:budget.close()
    data=json.loads(path.read_text());data['max_requests']=99;path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='configuration changed'):TestBatchBudget(path,cfg)


def test_parallel_owners_cannot_overspend(tmp_path):
    path,cfg=setup_batch(tmp_path,3);owners=[TestBatchBudget(path,cfg) for _ in range(8)]
    def run(budget):
        try:data=request();budget.reserve(data);finish(budget,data);return True
        except ValueError:return False
    try:
        with ThreadPoolExecutor(8) as pool:assert sum(pool.map(run,owners))==3
    finally:
        for budget in owners:budget.close()


@pytest.mark.parametrize('kind',['cancel','missing_usage','provider_error'])
def test_unknown_preserved_blocks_new_session(tmp_path,kind):
    path,cfg=setup_batch(tmp_path);budget=TestBatchBudget(path,cfg);data=request();budget.reserve(data)
    if kind!='cancel':budget.settle({'attempt_id':data['attempt_id'],'finish_reason':'stop' if kind=='missing_usage' else 'error','usage':None})
    budget.close();other=TestBatchBudget(path,cfg)
    try:
        with pytest.raises(ValueError,match='unknown'):other.reserve(request())
    finally:other.close()


def test_crashed_process_reservation_is_not_reset(tmp_path):
    path,cfg=setup_batch(tmp_path)
    code="from pathlib import Path; import os; from app.dsh_test_budget import TestBatchBudget; from tests.test_dsh_test_budget import request; from app.dsh_configuration import resolve_configuration; import json; c=json.loads(Path(os.environ['FIXTURE_CONFIG']).read_text()); b=TestBatchBudget(Path(os.environ['FIXTURE_CONFIG']),resolve_configuration({'api_base':c['api_base'],'model':c['model']})); b.reserve(request()); os._exit(0)"
    subprocess.run([sys.executable,'-c',code],env={**os.environ,'FIXTURE_CONFIG':str(path)},check=True)
    budget=TestBatchBudget(path,cfg)
    try:
        with pytest.raises(ValueError,match='unknown'):budget.reserve(request())
    finally:budget.close()


def test_disabled_default_has_no_ledger(tmp_path,monkeypatch):
    monkeypatch.delenv('KSTUDIO_TEST_BATCH_CONFIG',raising=False)
    assert TestBatchBudget.configured(resolve_configuration({'api_base':'https://example.invalid','model':'fixture'})) is None


def test_actual_processes_share_request_ceiling(tmp_path):
    path,cfg=setup_batch(tmp_path,3)
    code="from pathlib import Path; import os,json; from app.dsh_test_budget import TestBatchBudget; from tests.test_dsh_test_budget import request,finish; from app.dsh_configuration import resolve_configuration; c=json.loads(Path(os.environ['FIXTURE_CONFIG']).read_text()); b=TestBatchBudget(Path(os.environ['FIXTURE_CONFIG']),resolve_configuration({'api_base':c['api_base'],'model':c['model']}));\ntry:\n d=request(); b.reserve(d); finish(b,d); print('reserved')\nexcept ValueError: print('denied')\nfinally: b.close()"
    children=[subprocess.Popen([sys.executable,'-c',code],env={**os.environ,'FIXTURE_CONFIG':str(path)},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(7)]
    results=[p.communicate(timeout=20) for p in children]
    assert all(p.returncode==0 for p in children),results
    assert sum(out.strip()=='reserved' for out,_ in results)==3


def test_token_reservation_ceiling_and_provider_output_guard(tmp_path):
    path,cfg=setup_batch(tmp_path,3);spec=json.loads(path.read_text());spec['max_reserved_tokens']=spec['reserved_tokens_per_request'];path.write_text(json.dumps(spec))
    budget=TestBatchBudget(path,cfg)
    try:
        wrong=request();wrong['max_output_tokens']=5000
        with pytest.raises(ValueError,match='output'):budget.reserve(wrong)
        data=request();budget.reserve(data);finish(budget,data)
        with pytest.raises(ValueError,match='ceiling'):budget.reserve(request())
    finally:budget.close()


def test_desktop_bootstrap_preserves_explicit_test_batch_path(tmp_path,monkeypatch):
    from app.desktop_bootstrap import configure
    from tests.test_desktop_bootstrap import bundle
    monkeypatch.setattr(os,'environ',dict(os.environ))
    path,cfg=setup_batch(tmp_path);monkeypatch.setenv('KSTUDIO_TEST_BATCH_CONFIG',str(path))
    configure(bundle(tmp_path/'bundle'),tmp_path/'data')
    assert os.environ['KSTUDIO_TEST_BATCH_CONFIG']==str(path)
    budget=TestBatchBudget.configured(cfg)
    try:assert budget.batch=='fixture-batch'
    finally:budget.close()


def test_fair_per_run_ceilings_and_unregistered_project_cannot_reset(tmp_path):
    path,cfg=setup_batch(tmp_path,4);c=json.loads(path.read_text());c.update(allowed_run_ids=['run-a','run-b'],per_run_max_requests=2);path.write_text(json.dumps(c))
    for name in ('run-a','run-b'):
        budget=TestBatchBudget(path,cfg,run_id=name)
        try:
            for _ in range(2):data=request();budget.reserve(data);finish(budget,data)
            with pytest.raises(ValueError,match='ceiling'):budget.reserve(request())
        finally:budget.close()
    with pytest.raises(ValueError,match='preregistered'):TestBatchBudget(path,cfg,run_id='new-project-reset')


def test_unapproved_proposal_and_changed_effort_fail_closed(tmp_path):
    path,cfg=setup_batch(tmp_path);c=json.loads(path.read_text());c['authorization']={'status':'awaiting_owner_confirmation'};path.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='authorization'):TestBatchBudget(path,cfg)
    c['authorization']={'status':'local_fixture'};c['effective_configuration_sha256']=cfg.binding();path.write_text(json.dumps(c))
    changed=resolve_configuration({'api_base':cfg.endpoint,'model':cfg.model,'reasoning_effort':'high'})
    with pytest.raises(ValueError,match='Effective model'):TestBatchBudget(path,changed)
