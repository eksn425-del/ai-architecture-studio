"""Generic bounded geometry checks, with one genuine native Blender fixture."""
from copy import deepcopy
from dataclasses import replace
import shutil

import pytest

from app.spatial_clearance import (audit_spatial_clearance, audit_spatial_connections,
                                    blender_spatial_evidence, prepare_blender_clearance_tools)


def native_scene():
    objects = {"stair_end": {"id": "stair_end", "location": [.5, 0, .5], "dimensions": [1, 1.2, 1]},
               "landing": {"id": "landing", "location": [1.5, 0, .5], "dimensions": [1, 1.2, 1]},
               "wall": {"id": "wall", "location": [3, 3, 1], "dimensions": [1, .2, 2]}}
    return {"objects": objects, "geometry": {key: {k: deepcopy(v) for k, v in obj.items() if k != "id"}
            for key, obj in objects.items()}, "revision": 1, "native_reopen": "PASS",
            "model_path": "runtime/blender/mock/model.blend", "sha256": "a" * 64}


def zone(location=None):
    return {"name": "corridor", "location": location or [1.5, 0, 2],
            "dimensions": [1, 1, 2], "ignore_ids": []}


def endpoint(**kwargs):
    return {"a": "stair_end", "b": "landing", "axis": 0, "min_width_m": 1,
            "max_step_m": .02, "tolerance_m": .0001, **kwargs}


def test_clearance_and_endpoint_proxy_do_not_certify_route_or_source():
    evidence = blender_spatial_evidence(native_scene())
    result = audit_spatial_clearance(evidence, [zone()], [endpoint()])
    assert result["zones"][0]["status"] == "clear_for_declared_zone"
    assert result["endpoints"][0]["status"] == "satisfied_endpoint_proxy"
    assert result["actual_walkability"] == "unverified"
    assert result["navigation_verified"] is result["building_code_compliance"] is False
    assert result["model_identity"]["sha256"] == "a" * 64


@pytest.mark.parametrize("mutation,failed", [
    (lambda s: s["geometry"]["landing"]["location"].__setitem__(0, 1.55), "oriented_contact"),
    (lambda s: s["geometry"]["landing"]["location"].__setitem__(0, 1.45), "oriented_contact"),
    (lambda s: s["geometry"]["landing"]["location"].__setitem__(1, 1), "minimum_width"),
    (lambda s: s["geometry"]["landing"]["location"].__setitem__(2, .8), "maximum_step"),
])
def test_native_endpoint_measurements_detect_gap_penetration_narrow_and_step(mutation, failed):
    scene = native_scene()
    mutation(scene)
    # Proposed object specification still looks perfect; measured receipt wins.
    row = audit_spatial_clearance(blender_spatial_evidence(scene), [], [endpoint()])["endpoints"][0]
    assert row["status"] == "needs_fix" and row["checks"][failed] is False


def test_reverse_endpoints_do_not_pass_contact():
    row = audit_spatial_clearance(blender_spatial_evidence(native_scene()), [],
        [endpoint(a="landing", b="stair_end")])["endpoints"][0]
    assert row["status"] == "needs_fix"


def test_exact_box_blocker_and_boundary_contact():
    evidence = blender_spatial_evidence(native_scene())
    assert audit_spatial_clearance(evidence, [zone([3, 3, 1])])["zones"][0]["box_blockers"] == ["wall"]
    assert audit_spatial_clearance(evidence, [zone()])["zones"][0]["box_blockers"] == []


def test_mesh_bounds_overlap_does_not_become_exact_blocker_or_endpoint_pass():
    scene = native_scene()
    scene["objects"]["landing"].pop("dimensions")
    vertices = [[-.5, -.6, -.5], [.5, -.6, -.5], [.5, .6, .5]]
    scene["objects"]["landing"]["vertices"] = deepcopy(vertices)
    scene["geometry"]["landing"]["vertices"] = vertices
    evidence = blender_spatial_evidence(scene)
    result = audit_spatial_clearance(evidence, [zone([1.5, 0, 1])], [endpoint()])
    assert result["zones"][0]["status"] == "unverified"
    assert result["zones"][0]["bounds_candidates"] == ["landing"]
    assert result["endpoints"][0]["status"] == "unverified"
    assert audit_spatial_connections(evidence, [{"a": "stair_end", "b": "landing", "axis": 0,
        "tolerance": .001}])["connections"][0]["status"] == "unverified"


def test_incomplete_inventory_cannot_clear_even_empty_zone():
    evidence = replace(blender_spatial_evidence(native_scene()), inventory_complete=False)
    assert audit_spatial_clearance(evidence, [zone()])["zones"][0]["status"] == "unverified"


@pytest.mark.parametrize("change", [
    lambda s: s.pop("model_path"), lambda s: s.update(sha256="unverified"),
    lambda s: s.update(native_reopen="NOT_RUN"),
    lambda s: s["geometry"]["landing"].update(rotation_euler=[0, 0, 1]),
    lambda s: s["objects"]["landing"].update(scale=[2, 2, 2]),
])
def test_missing_identity_or_unsupported_geometry_fails_closed(change):
    scene = native_scene()
    change(scene)
    with pytest.raises(ValueError):
        blender_spatial_evidence(scene)


@pytest.mark.parametrize("change", [
    lambda z: z.update(dimensions=[0, 1, 2]), lambda z: z.update(location=[float("nan"), 0, 0]),
    lambda z: z.update(ignore_ids=["absent"]), lambda z: z.update(ignore_ids=["wall", "wall"]),
    lambda z: z.update(frame_id="fabricated"), lambda z: z.update(receipt={}),
])
def test_invalid_zone_inputs_fail_closed(change):
    value = zone()
    change(value)
    with pytest.raises(ValueError):
        audit_spatial_clearance(blender_spatial_evidence(native_scene()), [value])


@pytest.mark.parametrize("parameters", [{"axis": 2}, {"axis": True}, {"min_width_m": 0},
    {"max_step_m": float("nan")}, {"tolerance_m": -.1}, {"a": "absent"}, {"b": "stair_end"}])
def test_invalid_endpoint_inputs_fail_closed(parameters):
    with pytest.raises(ValueError):
        audit_spatial_clearance(blender_spatial_evidence(native_scene()), [], [endpoint(**parameters)])


def test_mixed_frames_require_explicit_zone_and_never_clear_unknown_obstacles():
    evidence = blender_spatial_evidence(native_scene())
    evidence = replace(evidence, objects=(*evidence.objects[:2], replace(evidence.objects[2], frame_id="other")))
    with pytest.raises(ValueError, match="frame"):
        audit_spatial_clearance(evidence, [zone()])
    result = audit_spatial_clearance(evidence, [{**zone(), "frame_id": "blender:model"}])
    assert result["zones"][0]["status"] == "unverified"
    assert result["zones"][0]["unverified_frame_ids"] == ["wall"]


def test_product_tool_reads_native_scene_and_rejects_geometry_injection():
    class Backend:
        calls = []
        def dispatch(self, name, args):
            self.calls.append((name, args))
            return native_scene()
    backend = Backend()
    specs, dispatch = prepare_blender_clearance_tools(backend)
    name = specs[0]["name"]
    result = dispatch(name, {"zones": [zone()], "endpoints": [endpoint()]})
    assert backend.calls == [("blender_inspect_scene", {})]
    assert result["endpoints"][0]["status"] == "satisfied_endpoint_proxy"
    with pytest.raises(ValueError):
        dispatch(name, {"zones": [], "endpoints": [], "scene": native_scene()})
    assert len(backend.calls) == 1


@pytest.mark.skipif(not shutil.which("blender"), reason="Real Blender unavailable; no substitute native PASS")
def test_real_blender_saved_reopened_stair_landing_clearance(tmp_path):
    from app.blender_backend import BlenderBackend
    backend = BlenderBackend(tmp_path)
    receipt = backend.dispatch("blender_apply_objects", {"objects": list(native_scene()["objects"].values())})
    assert receipt["native_reopen"] == "PASS"
    specs, dispatch = prepare_blender_clearance_tools(backend)
    before = (backend.state.read_bytes(), (tmp_path / receipt["model_path"]).read_bytes())
    result = dispatch(specs[0]["name"], {"zones": [zone()], "endpoints": [endpoint()]})
    assert result["endpoints"][0]["status"] == "satisfied_endpoint_proxy"
    assert result["zones"][0]["status"] == "clear_for_declared_zone"
    assert result["navigation_verified"] is False
    assert before == (backend.state.read_bytes(), (tmp_path / receipt["model_path"]).read_bytes())
