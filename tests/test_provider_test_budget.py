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
    with pytest.raises(ValueError, match="模型或用量"):
        call({}, lambda: SimpleNamespace(model="other", usage={"prompt_tokens": 10, "completion_tokens": 2}))
    with pytest.raises(ValueError, match="安全边界"):
        call({}, lambda: pytest.fail("uncertain spend cannot be reset"))
    assert [r["status"] for r in json.loads(path.read_text())["requests"]] == ["unresolved", "unresolved"]


def test_no_opt_in_does_not_change_existing_transport(monkeypatch):
    monkeypatch.delenv("K_STUDIO_LOCAL_API_TEST_BUDGET", raising=False)
    kwargs = {}
    assert call(kwargs, lambda: "unchanged") == "unchanged"
    assert kwargs == {}
