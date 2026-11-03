import json

import pytest

from app.construction_strategy import (
    CONSTRUCTION_STAGE_ORDER,
    construction_strategy_schema_note,
    default_construction_strategy,
    strategy_has_signal,
    validate_construction_strategy_payload,
    load_construction_strategy,
)


def test_agent_schema_note_example_is_valid_and_seeded(tmp_path):
    from app.codex_parity import prepare_codex_parity_workspace
    note = construction_strategy_schema_note()
    example = json.loads(note.split("```json\n", 1)[1].split("```", 1)[0])
    assert strategy_has_signal(validate_construction_strategy_payload(example))
    workspace = prepare_codex_parity_workspace(tmp_path / "workspace")
    assert (workspace / "notes/construction_strategy_schema.md").read_text(encoding="utf-8") == note
    assert "plan_only is invalid" in note


def test_default_construction_strategy_is_empty_and_valid():
    value = validate_construction_strategy_payload(default_construction_strategy())
    assert value["stage_order"] == list(CONSTRUCTION_STAGE_ORDER)
    assert value["current_stage"] == "pending"
    assert value["systems"] == []
    assert strategy_has_signal(value) is False


def test_failed_strategy_write_includes_full_contract_without_changing_file(tmp_path):
    from app.workspace_files import workspace_file_call
    notes = tmp_path / "notes"
    notes.mkdir()
    target = notes / "construction_strategy.json"
    original = json.dumps(default_construction_strategy())
    target.write_text(original, encoding="utf-8")
    bad = default_construction_strategy()
    bad["shared_parameters"] = {"width": {"value": 10800, "unit": "mm", "provenance": "generated"}}
    with pytest.raises(ValueError) as caught:
        workspace_file_call(tmp_path, "workspace_write", {"relative_path": "notes/construction_strategy.json", "content": json.dumps(bad)})
    assert target.read_text(encoding="utf-8") == original
    assert "exact key 'units'" in str(caught.value)
    assert "Parameter provenance:" in str(caught.value) and "Roles:" in str(caught.value)


def test_strategy_supports_shared_parameter_driven_staged_systems():
    value = validate_construction_strategy_payload({
        "schema_version": 1,
        "current_stage": "representative_module",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": {
            "floor_height": {
                "value": 3200,
                "units": "mm",
                "provenance": "user_confirmed",
                "source": "user",
            },
            "front_bays": {
                "value": 3,
                "units": "count",
                "provenance": "observed",
                "source": "front panel",
            },
        },
        "systems": [
            {
                "id": "front-wall-system",
                "stage": "primary_form",
                "role": "opening_system",
                "method": "continuous_wall_with_openings",
                "status": "built",
                "depends_on": ["floor_height", "front_bays"],
                "target_paths": [["SHELL", "FRONT_WALL"]],
                "verification_views": ["front", "oblique"],
                "notes": ["one continuous host, real openings"],
            },
            {
                "id": "window-module",
                "stage": "representative_module",
                "role": "repetition",
                "method": "prototype_instance",
                "status": "pending",
                "depends_on": ["floor_height"],
                "target_paths": [["FACADE", "WINDOW_MODULE"]],
                "verification_views": ["front", "left"],
                "notes": [],
            },
        ],
        "notes": ["verify representative module before replication"],
    })
    assert strategy_has_signal(value) is True
    assert value["systems"][0]["method"] == "continuous_wall_with_openings"
    assert value["systems"][1]["stage"] == "representative_module"


def test_strategy_rejects_unknown_dependency_and_bad_method():
    base = {
        "schema_version": 1,
        "current_stage": "primary_form",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": {},
        "systems": [{
            "id": "roof",
            "stage": "primary_form",
            "role": "roof",
            "method": "loft_or_mesh",
            "status": "pending",
            "depends_on": ["missing"],
            "target_paths": [],
            "verification_views": ["roof"],
            "notes": [],
        }],
        "notes": [],
    }
    with pytest.raises(ValueError, match="unknown parameters"):
        validate_construction_strategy_payload(base)

    base["systems"][0]["depends_on"] = []
    base["systems"][0]["method"] = "magic"
    with pytest.raises(ValueError, match="invalid method"):
        validate_construction_strategy_payload(base)


def test_strategy_rejects_arbitrary_stage_order_or_view():
    value = default_construction_strategy()
    value["stage_order"] = ["finish"]
    with pytest.raises(ValueError, match="five-stage"):
        validate_construction_strategy_payload(value)

    value = default_construction_strategy()
    value["systems"] = [{
        "id": "facade",
        "stage": "primary_form",
        "role": "shell",
        "method": "custom_owned_ruby",
        "status": "pending",
        "depends_on": [],
        "target_paths": [],
        "verification_views": ["pretty"],
        "notes": [],
    }]
    with pytest.raises(ValueError, match="invalid verification views"):
        validate_construction_strategy_payload(value)


def test_persisted_invalid_strategy_is_not_missing_at_writer_preflight(tmp_path):
    from app.project_ruby import ProjectRubyExecutor

    note = tmp_path / "runtime/agent_workspace/notes/construction_strategy.json"
    note.parent.mkdir(parents=True)
    assert load_construction_strategy(tmp_path, strict=True) is None
    strategy = default_construction_strategy()
    strategy["systems"] = [{
        "id": "frame", "stage": "primary_form", "role": "shell",
        "method": "prototype_instance", "status": "pending",
        "method_id": "sketchup.component_definition_and_instances",
        "selection_reason": "Historical invalid registry identifier from real r10 case.",
    }]
    note.write_text(json.dumps(strategy), encoding="utf-8")
    assert load_construction_strategy(tmp_path) is None  # compatible optional reader
    with pytest.raises(ValueError, match="frame.*invalid OSS method_id"):
        load_construction_strategy(tmp_path, strict=True)

    executor = object.__new__(ProjectRubyExecutor)
    executor.project_dir = tmp_path
    executor.ruby_state = {}
    executor._assert_active_model = lambda: pytest.fail("must reject before contacting SketchUp")
    with pytest.raises(ValueError, match="No model operation was attempted"):
        executor.run({"script_id": "frame", "ruby_source": "root.entities.add_group"})
    assert not (tmp_path / "runtime/scripts").exists()
    assert note.read_text(encoding="utf-8") == json.dumps(strategy)

    note.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid notes/construction_strategy.json"):
        load_construction_strategy(tmp_path, strict=True)
    note.write_text(json.dumps(default_construction_strategy()), encoding="utf-8")
    assert load_construction_strategy(tmp_path, strict=True) == default_construction_strategy()
