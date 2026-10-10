"""Progress must reflect actual model readback; planning and executed are distinct."""
from pathlib import Path

from app.construction_strategy import CONSTRUCTION_STAGE_ORDER, validate_construction_strategy_payload
from app.strategy_progress import assess_strategy_progress, persist_verified_strategy_progress


def _plan():
    return validate_construction_strategy_payload({
        "schema_version": 1, "current_stage": "pending",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "systems": [
            {"id": "base", "stage": "primary_form", "role": "shell",
             "method": "custom_owned_ruby", "status": "pending",
             "target_paths": [["GROUND_SHELL"]]},
            {"id": "gable", "stage": "representative_module", "role": "roof",
             "method": "loft_or_mesh", "status": "pending",
             "target_paths": [["UPPER_GLASS_PAVILION", "GABLE_GLAZING"]]},
            {"id": "fascia", "stage": "finish", "role": "facade_detail",
             "method": "custom_owned_ruby", "status": "pending",
             "target_paths": [["SIGNAGE_FRONT"]]},
        ],
    })


def test_real_root_readback_advances_only_directly_verified_paths():
    updated, evidence = assess_strategy_progress(
        _plan(), script_id="coffee", revision=3, root_pid=35529,
        named_paths=[["GROUND_SHELL"], ["UPPER_GLASS_PAVILION"]],
        full_readback=True,
    )
    assert updated["systems"][0]["status"] == "built"
    assert updated["systems"][1]["status"] == "pending"
    assert updated["systems"][2]["status"] == "pending"
    assert updated["current_stage"] == "representative_module"
    assert evidence["systems"][1]["missing_paths"] == [
        ["UPPER_GLASS_PAVILION", "GABLE_GLAZING"]]
    assert evidence["visual_verification"] == "NOT_RUN"


def test_empty_or_partial_readback_never_upgrades_a_planner_claim():
    updated, evidence = assess_strategy_progress(
        _plan(), script_id="coffee", revision=1, root_pid=8,
        named_paths=[["GROUND_SHELL"]], full_readback=False,
    )
    assert all(x["status"] == "pending" for x in updated["systems"])
    assert evidence["systems"][0]["result"] == "incomplete_readback"


def test_existing_visual_needs_fix_cannot_be_overridden_by_geometry():
    plan = _plan()
    plan["systems"][0]["status"] = "needs_fix"
    updated, _ = assess_strategy_progress(
        plan, script_id="coffee", revision=3, root_pid=8,
        named_paths=[["GROUND_SHELL"]], full_readback=True,
    )
    assert updated["systems"][0]["status"] == "needs_fix"
    assert updated["current_stage"] == "primary_form"


def test_missing_plan_or_missing_system_not_false_built(tmp_path: Path):
    assert persist_verified_strategy_progress(
        tmp_path, script_id="coffee", revision=1, root_pid=8,
        named_paths=[["GROUND_SHELL"]], full_readback=True,
    ) is None
