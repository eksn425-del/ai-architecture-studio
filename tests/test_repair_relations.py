"""Unit contracts use explicit receipts; the private fixture uses real Blender."""
from copy import deepcopy

import pytest

from app.repair_relations import plan_relation_repairs, evaluate_relation_repairs


def scene(x=1.1, revision=1):
    objects = {
        "stair": {"id": "stair", "location": [0, 0, 0], "dimensions": [1, 1, 1]},
        "landing": {"id": "landing", "location": [x, 0, 0], "dimensions": [1, 1, 1]},
        "wall": {"id": "wall", "location": [5, 5, 1], "dimensions": [1, 1, 2]},
    }
    return {"revision": revision, "native_reopen": "PASS", "objects": objects,
            "geometry": {k: {"location": deepcopy(v["location"]),
                              "dimensions": deepcopy(v["dimensions"]), "material": []}
                         for k, v in objects.items()}}


def review():
    return {"needs_fix": True, "provenance": "independent_critic",
            "issues": [{"priority": 1, "problem": "Stair and landing have a gap", "action": "join"},
                       {"priority": 2, "problem": "Appearance needs independent source review"}]}


def repairs():
    return [{"priority": 1, "component_ids": ["landing"], "planned_edit": "Move landing to the stair end",
             "connections": [{"a": "stair", "b": "landing", "axis": 0, "tolerance": 0.00001}]}]


def test_failing_review_is_allowed_before_repair_and_provenance_not_trusted():
    plan = plan_relation_repairs(review(), scene(), repairs())
    assert plan["status"] == "ready_to_repair"
    assert plan["review_provenance"] == "agent_proposed_not_independent_critic"
    assert plan["unresolved_priorities"] == [1, 2]
    assert plan["unmapped_priorities"] == [2]
    assert plan["keep_ids"] == ["stair", "wall"]
    assert plan["repairs"][0]["before"]["checks"][0]["signed_gap_m"] == pytest.approx(.1)


def test_actual_native_gap_overrides_proposed_specification():
    native = scene()
    native["objects"]["landing"]["location"][0] = 1  # Proposed contact is not measured contact.
    plan = plan_relation_repairs(review(), native, repairs())
    assert plan["repairs"][0]["before"]["checks"][0]["bounds_status"] == "gap"


def test_measured_repair_closes_only_declared_relations_and_preserves_keep():
    before = scene()
    plan = plan_relation_repairs(review(), before, repairs())
    after = evaluate_relation_repairs(plan, scene(x=1, revision=2))
    assert after["status"] == "relations_satisfied"
    assert after["resolved_relation_priorities"] == [1]
    assert after["unresolved_priorities"] == [2]
    assert after["source_fidelity_status"] == after["visual_quality_status"] == "unverified"
    assert after["independent_critic_pass"] is False
    assert after["keep_verified"] is True
    assert after["attempts"] == 1
    assert after["history"][0]["repairs"][0]["checks"][0]["signed_gap_m"] == pytest.approx(0)
    assert plan["attempts"] == 0  # Evaluation never mutates caller inputs.
    assert before == scene()


def test_rereading_revision_does_not_consume_attempt_and_budget_bounds_failing_repairs():
    plan = plan_relation_repairs(review(), scene(), repairs(), max_attempts=2)
    assert evaluate_relation_repairs(plan, scene()) == plan
    first = evaluate_relation_repairs(plan, scene(x=1.08, revision=2))
    assert first["status"] == "still_needs_fix"
    assert evaluate_relation_repairs(first, scene(x=1.08, revision=2)) == first
    second = evaluate_relation_repairs(first, scene(x=1.04, revision=3))
    assert second["status"] == "blocked"
    assert second["block_reason"] == "repair_attempt_budget_exhausted"
    assert second["remaining_attempts"] == 0
    assert evaluate_relation_repairs(second, scene(x=1, revision=4)) == second


@pytest.mark.parametrize("field", ["objects", "geometry"])
def test_keep_change_blocks_even_if_relation_passes(field):
    plan = plan_relation_repairs(review(), scene(), repairs())
    after = scene(x=1, revision=2)
    after[field]["wall"]["location"][0] += .1
    result = evaluate_relation_repairs(plan, after)
    assert result["status"] == "blocked"
    assert result["block_reason"] == "protected_KEEP_changed"
    assert result["keep_verified"] is False
    assert result["resolved_relation_priorities"] == []


@pytest.mark.parametrize("mutation", ["new_object", "delete_target", "delete_keep"])
def test_inventory_cannot_expand_or_shrink(mutation):
    plan = plan_relation_repairs(review(), scene(), repairs())
    after = scene(x=1, revision=2)
    for field in ("objects", "geometry"):
        if mutation == "new_object":
            after[field]["new"] = deepcopy(after[field]["wall"])
        else:
            after[field].pop("landing" if mutation == "delete_target" else "wall")
    result = evaluate_relation_repairs(plan, after)
    assert result["block_reason"] == "object_inventory_changed_outside_existing_target_contract"


@pytest.mark.parametrize("revision", [0, 1, 3])
def test_only_next_checked_revision_allowed(revision):
    plan = plan_relation_repairs(review(), scene(), repairs())
    if revision == 0:
        with pytest.raises(ValueError, match="trusted"):
            evaluate_relation_repairs(plan, scene(x=1, revision=revision))
    else:
        result = evaluate_relation_repairs(plan, scene(x=1, revision=revision))
        assert result["block_reason"] == "revision_not_next_checked_commit"


def test_native_no_progress_cannot_be_hidden_by_changed_spec():
    before = scene()
    plan = plan_relation_repairs(review(), before, repairs())
    after = deepcopy(before)
    after["revision"] = 2
    after["objects"]["landing"]["location"][0] = 1
    result = evaluate_relation_repairs(plan, after)
    assert result["block_reason"] == "no_native_geometry_progress"


def test_mesh_aabb_contact_never_claims_exact_surface_pass():
    before = scene(x=1)
    vertices = [[-.5, -.5, -.5], [.5, -.5, -.5], [.5, .5, .5]]
    before["objects"]["landing"].pop("dimensions")
    before["objects"]["landing"]["vertices"] = vertices
    before["geometry"]["landing"]["vertices"] = vertices
    plan = plan_relation_repairs(review(), before, repairs())
    assert plan["resolved_relation_priorities"] == []
    assert plan["repairs"][0]["current"]["checks"][0]["check_status"] == "unverified_mesh_surface"
    assert plan["repairs"][0]["current"]["checks"][0]["exact_for_boxes"] is False


@pytest.mark.parametrize("change", ["missing_native", "missing_reopen", "nan_geometry", "bad_dimensions"])
def test_untrusted_or_incomplete_scene_rejected(change):
    value = scene()
    if change == "missing_native":
        value.pop("geometry")
    elif change == "missing_reopen":
        value["native_reopen"] = "NOT_RUN"
    elif change == "nan_geometry":
        value["geometry"]["stair"]["location"][0] = float("nan")
    else:
        value["geometry"]["stair"]["dimensions"][0] = 0
    with pytest.raises(ValueError):
        plan_relation_repairs(review(), value, repairs())


@pytest.mark.parametrize("change", ["unknown_priority", "duplicate_priority", "unknown_target", "duplicate_target",
                                    "unrelated_relation", "empty_edit", "invalid_axis", "nan_tolerance"])
def test_invalid_mapping_fails_closed(change):
    mapped = repairs()
    if change == "unknown_priority": mapped[0]["priority"] = 99
    elif change == "duplicate_priority": mapped.append(deepcopy(mapped[0]))
    elif change == "unknown_target": mapped[0]["component_ids"] = ["absent"]
    elif change == "duplicate_target": mapped[0]["component_ids"] *= 2
    elif change == "unrelated_relation": mapped[0]["component_ids"] = ["wall"]
    elif change == "empty_edit": mapped[0]["planned_edit"] = " "
    elif change == "invalid_axis": mapped[0]["connections"][0]["axis"] = True
    elif change == "nan_tolerance": mapped[0]["connections"][0]["tolerance"] = float("nan")
    with pytest.raises(ValueError):
        plan_relation_repairs(review(), scene(), mapped)


@pytest.mark.parametrize("budget", [0, 13, True, "2"])
def test_invalid_attempt_limits_rejected(budget):
    with pytest.raises(ValueError):
        plan_relation_repairs(review(), scene(), repairs(), max_attempts=budget)


def test_plan_json_roundtrip_retains_check_contract():
    import json
    plan = json.loads(json.dumps(plan_relation_repairs(review(), scene(), repairs())))
    assert evaluate_relation_repairs(plan, scene(x=1, revision=2))["status"] == "relations_satisfied"
