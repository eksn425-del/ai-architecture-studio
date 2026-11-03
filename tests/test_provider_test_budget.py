import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.provider_test_budget import invoke_with_test_budget


def configured(tmp_path, monkeypatch, limit="1"):
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"model": "openai/deepseek-v4.1-flash", "api_base": "https://api.b.ai/v1",
        "limit_usd": limit, "input_usd_per_million": "0.30", "output_usd_per_million": "1.20",
        "max_input_tokens": 1048576, "max_output_tokens": 32768}), encoding="utf-8")
    monkeypatch.setenv("K_STUDIO_LOCAL_API_TEST_BUDGET", str(path))
    return path


def call(kwargs, invoke):
    return invoke_with_test_budget("openai/deepseek-v4.1-flash", "https://api.b.ai/v1", kwargs, invoke)


def test_budget_persists_before_dispatch_caps_output_and_settles(tmp_path, monkeypatch):
    path = configured(tmp_path, monkeypatch)
    kwargs = {"max_tokens": 100000}
    def provider():
        assert json.loads(path.read_text())["requests"][-1]["status"] == "reserved"
        assert kwargs["max_tokens"] == 32768
        return SimpleNamespace(model="deepseek-v4.1-flash", usage={"prompt_tokens": 10, "completion_tokens": 2})
    call(kwargs, provider)
    call({}, provider)
    rows = json.loads(path.read_text())["requests"]
    assert len(rows) == 2 and all(r["status"] == "settled_upper_bound" for r in rows)
    assert sum(Decimal(r["liability_usd"]) for r in rows) == Decimal("0.0000108")


def test_ceiling_or_wrong_route_has_zero_network_effects(tmp_path, monkeypatch):
    configured(tmp_path, monkeypatch, "0.1")
    with pytest.raises(ValueError, match="安全边界"):
        call({}, lambda: pytest.fail("must not dispatch"))
    with pytest.raises(ValueError, match="供应商和模型"):
        invoke_with_test_budget("openai/other", "https://api.b.ai/v1", {}, lambda: pytest.fail("must not dispatch"))


def test_unknown_failure_and_bad_metering_retain_liability(tmp_path, monkeypatch):
    path = configured(tmp_path, monkeypatch, "0.71")
    def lost():
        raise TimeoutError("response lost")
    with pytest.raises(TimeoutError):
        call({}, lost)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="费用尚未核实"):
        call({}, lambda: pytest.fail("uncertain spend cannot dispatch another request"))
    assert path.read_bytes() == before
    assert [r["status"] for r in json.loads(path.read_text())["requests"]] == ["unresolved"]


def test_bad_metering_quarantines_a_separate_budget_before_next_dispatch(tmp_path, monkeypatch):
    path = configured(tmp_path, monkeypatch, "0.71")
    with pytest.raises(ValueError, match="模型或用量"):
        call({}, lambda: SimpleNamespace(model="other", usage={"prompt_tokens": 10, "completion_tokens": 2}))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="费用尚未核实"):
        call({}, lambda: pytest.fail("unmetered spend cannot dispatch another request"))
    assert path.read_bytes() == before
    assert [r["status"] for r in json.loads(path.read_text())["requests"]] == ["unresolved"]


def test_no_opt_in_does_not_change_existing_transport(monkeypatch):
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    kwargs = {}
    assert call(kwargs, lambda: "unchanged") == "unchanged"
    assert kwargs == {}


def test_two_processes_cannot_dispatch_from_the_same_stale_budget(tmp_path):
    import json,os,subprocess,sys
    from pathlib import Path
    ledger=tmp_path / "budget.json"
    ledger.write_text(json.dumps({"model":"fixture","api_base":"https://fixture.invalid/v1",
        "limit_usd":"1","input_usd_per_million":"450000","output_usd_per_million":"450000",
        "max_input_tokens":1,"max_output_tokens":1,"requests":[]}),encoding="utf-8")
    worker=tmp_path / "worker.py"
    worker.write_text("""import os,sys,time
from pathlib import Path
from app.provider_test_budget import invoke_with_test_budget
sys.stdin.readline()
def invoke():
    with Path(sys.argv[1]).with_suffix('.dispatches').open('a') as f:f.write(str(os.getpid())+'\\n')
    time.sleep(.4)
    return {'model':'fixture','usage':{'prompt_tokens':1,'completion_tokens':1}}
try:
    invoke_with_test_budget('fixture','https://fixture.invalid/v1',{},invoke)
    print('settled')
except (ValueError,RuntimeError):print('blocked')
""",encoding="utf-8")
    env=dict(os.environ,K_STUDIO_LOCAL_API_TEST_BUDGET=str(ledger),
             PYTHONPATH=str(Path(__file__).resolve().parents[1]),WEB_CONCURRENCY="1",K_STUDIO_DEPLOYMENT_MODE="local")
    envs=[env,{**env,"K_STUDIO_LOCAL_API_TEST_BUDGET":str(ledger.with_name(ledger.name.upper())) if os.name=="nt" else str(ledger)}]
    children=[subprocess.Popen([sys.executable,str(worker),str(ledger)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=child_env) for child_env in envs]
    for child in children:child.stdin.write('go\n');child.stdin.flush()
    outputs=[child.communicate(timeout=10) for child in children]
    assert all(child.returncode==0 for child in children),outputs
    assert sorted(o.strip() for o,e in outputs)==['blocked','settled'],outputs
    saved=json.loads(ledger.read_text(encoding="utf-8"))
    assert len(saved['requests'])==1
    assert saved['requests'][0]['liability_usd']=='0.9'
    assert len(ledger.with_suffix('.dispatches').read_text().splitlines())==1


@pytest.mark.parametrize('liability', ['-0.7', 'NaN', 'Infinity', None])
def test_invalid_historical_cost_cannot_create_budget_room(tmp_path, monkeypatch, liability):
    path = configured(tmp_path, monkeypatch)
    data = json.loads(path.read_text())
    data['requests'] = [{'id': 'old', 'status': 'settled_upper_bound', 'liability_usd': liability}]
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='历史费用无效'):
        call({}, lambda: pytest.fail('Invalid ledger must not dispatch'))
    assert path.read_bytes() == before


@pytest.mark.parametrize('max_tokens', [0, -1, True, None, '100'])
def test_invalid_output_limit_has_no_dispatch_or_ledger_effect(tmp_path, monkeypatch, max_tokens):
    path = configured(tmp_path, monkeypatch)
    before = path.read_bytes()
    with pytest.raises(ValueError, match='输出上限无效'):
        call({'max_tokens': max_tokens}, lambda: pytest.fail('Invalid output limit must not dispatch'))
    assert path.read_bytes() == before


@pytest.mark.parametrize('rows', [None, {'status': 'settled_upper_bound'}])
def test_malformed_request_collection_never_dispatches(tmp_path, monkeypatch, rows):
    path = configured(tmp_path, monkeypatch)
    data = json.loads(path.read_text())
    data['requests'] = rows
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='账本格式无效'):
        call({}, lambda: pytest.fail('Malformed ledger must not dispatch'))
    assert path.read_bytes() == before
