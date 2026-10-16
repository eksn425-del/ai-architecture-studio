"""Progress must reflect actual model readback; planning and executed are distinct."""
from pathlib import Path
import pytest

from app.construction_strategy import CONSTRUCTION_STAGE_ORDER, validate_construction_strategy_payload
from app.strategy_progress import assess_strategy_progress, persist_verified_strategy_progress, collect_verified_strategy_paths


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


def test_existing_nested_geometry_requires_real_readback_before_progress_change():
    plan = _plan()
    plan['systems'][1]['status'] = 'built'
    calls = []

    def native(paths):
        calls.append(paths)
        return [{'path': paths[0], 'persistent_id': 123, 'objects_total': 17}]

    names = collect_verified_strategy_paths(
        plan, [['GROUND_SHELL'], ['UPPER_GLASS_PAVILION']], native,
    )
    updated, report = assess_strategy_progress(
        plan, script_id='same-case', revision=11, root_pid=20606,
        named_paths=names, full_readback=True,
    )
    assert calls == [[['UPPER_GLASS_PAVILION', 'GABLE_GLAZING']]]
    assert updated['systems'][1]['status'] == 'built'
    assert report['systems'][1]['missing_paths'] == []
    assert report['visual_verification'] == 'NOT_RUN'


@pytest.mark.parametrize('snapshots', [[], [{'path': ['WRONG'], 'persistent_id': 123, 'objects_total': 17}], [{'path': ['UPPER_GLASS_PAVILION', 'GABLE_GLAZING'], 'persistent_id': 0, 'objects_total': 17}]])
def test_partial_or_mismatched_nested_snapshot_cannot_certify_progress(snapshots):
    with pytest.raises(ValueError, match='native'):
        collect_verified_strategy_paths(_plan(), [['UPPER_GLASS_PAVILION']], lambda _: snapshots)


def test_absent_root_never_triggers_nested_probe_or_fakes_presence():
    names = collect_verified_strategy_paths(
        _plan(), [['GROUND_SHELL']], lambda _: pytest.fail('nested ancestor absent'),
    )
    assert names == [['GROUND_SHELL']]
