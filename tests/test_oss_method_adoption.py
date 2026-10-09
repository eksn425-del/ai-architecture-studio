"""No-network OSS adoption contract tests; real SketchUp still requires Windows proof."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.oss_method_catalog import BY_ID, STAGES, candidate_methods, capability_selection_note
from app.construction_strategy import (
    CONSTRUCTION_STAGE_ORDER,
    validate_construction_strategy_payload,
)
from app.project_ruby import ProjectRubyExecutor, validate_project_ruby_source


def _strategy(**overrides):
    system = {
        "id": "roof", "stage": "primary_form", "role": "roof",
        "method": "loft_or_mesh", "status": "pending",
        "method_id": "adai.loft_sections",
        "selection_reason": "The source roof has changing sections, not a flat slab.",
    }
    system.update(overrides)
    return {
        "schema_version": 1, "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "current_stage": "pending", "systems": [system],
    }


def test_catalog_distinguishes_availability_from_actual_use():
    assert "adai.profile_with_holes" in BY_ID
    assert "saie.wall_with_openings" in BY_ID
    assert "product_used" in STAGES
    assert "effect_verified" in STAGES
    assert "adai.loft_sections" not in {m.method_id for m in candidate_methods("roof")}
    assert "adai.loft_sections" in {
        m.method_id for m in candidate_methods("roof", adai_enabled=True)
    }
    assert "ZERO method calls" in capability_selection_note(adai_enabled=True)
    assert "not exposed" in capability_selection_note(adai_enabled=False)


def test_strategy_preserves_concrete_provider_and_requires_reason():
    data = validate_construction_strategy_payload(_strategy())
    assert data["systems"][0]["method_id"] == "adai.loft_sections"
    assert "changing sections" in data["systems"][0]["selection_reason"]
    with pytest.raises(ValueError, match="selection_reason"):
        validate_construction_strategy_payload(_strategy(selection_reason=""))
    with pytest.raises(ValueError, match="method_id"):
        validate_construction_strategy_payload(_strategy(method_id="imaginary.unknown"))
    # Persisted legacy plans still load; missing selection is not false usage.
    old = _strategy()
    old["systems"][0].pop("method_id")
    old["systems"][0].pop("selection_reason")
    parsed = validate_construction_strategy_payload(old)
    assert "method_id" not in parsed["systems"][0]


def test_guarded_transport_records_real_wrapped_calls_and_zero_call_ledger(monkeypatch, tmp_path):
    from app import project_ruby
    executor = object.__new__(ProjectRubyExecutor)
    executor.project_id = "oss-test"
    executor.expected_model_path = tmp_path / "blank-disposable-test.skp"
    executor.expected_model_guid = "test-guid"
    write_sha = "a" * 64

    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: None)
    script = executor._build_transport_script(
        tmp_path / "run.rb", tmp_path / "report.json",
        expected_revision=3, root_pid=22, update_mode="edit",
        source_sha256=write_sha,
    )
    assert "KStudioOSSMethodRuntime.record(oss_method_events, 'saie.wall')" in script
    assert "KStudioOSSMethodRuntime.record(oss_method_events, 'saie.wall_with_openings')" in script
    assert "oss_method_ledger" in script
    assert write_sha in script
    assert "snapshot" not in script
    assert "ADAIProxy.new" not in script
    assert "eval(source, binding" in script

    monkeypatch.setattr(project_ruby, "geometry_helper", lambda *_: tmp_path / "pinned.rb")
    with_adai = executor._build_transport_script(
        tmp_path / "run.rb", tmp_path / "report.json", 0, None, source_sha256=write_sha,
    )
    assert "KStudioOSSMethodRuntime::ADAIProxy.new" in with_adai
    assert "KStudioOSSMethodRuntime" in with_adai
    assert with_adai.count("root.set_attribute(CodexSketchupArchitect::DICT, 'oss_method_ledger'") == 1


def test_agent_cannot_spoof_host_recorder_class():
    with pytest.raises(ValueError, match="blocked host"):
        validate_project_ruby_source(
            "roof", "KStudioOSSMethodRuntime.record([], 'adai.loft_sections') { nil }"
        )
