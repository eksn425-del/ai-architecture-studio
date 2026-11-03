"""Bounded read-only geometry proxies shared by native backend adapters.

Only host adapters construct SpatialEvidence. It is not a model/tool argument
schema or independent evidence authentication. Inputs must come from a current
native inspection. A clear box volume or joined endpoint never proves a walking
route, stair safety, accessibility, structural safety, or building-code approval.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import re

from .blender_connections import audit_connections
from .repair_relations import _native_objects


@dataclass(frozen=True)
class SpatialObject:
    object_id: str
    frame_id: str
    low: tuple[float, float, float]
    high: tuple[float, float, float]
    exact_box: bool
    metric_frame_verified: bool
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpatialEvidence:
    backend: str
    identity: dict
    revision: int
    objects: tuple[SpatialObject, ...]
    inventory_complete: bool
    inventory_scope: str
    provenance: dict


def _number(value, name, low=0, high=10000):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Invalid {name}")
    return float(value)


def _vector(value, name, *, positive=False):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"Invalid {name}")
    result = tuple(_number(v, name, -1000000, 1000000) for v in value)
    if positive and any(v <= 0 for v in result):
        raise ValueError(f"Invalid {name}")
    return result


def _objects(evidence):
    if (not isinstance(evidence, SpatialEvidence) or type(evidence.revision) is not int
            or evidence.revision < 1 or not evidence.identity or not evidence.provenance
            or not 1 <= len(evidence.objects) <= 2048):
        raise ValueError("Expected host-adapted native spatial evidence")
    objects = {}
    for obj in evidence.objects:
        if (not isinstance(obj, SpatialObject) or not isinstance(obj.object_id, str)
                or not obj.object_id or obj.object_id in objects or not obj.frame_id
                or type(obj.exact_box) is not bool or type(obj.metric_frame_verified) is not bool):
            raise ValueError("Invalid spatial object identity or evidence class")
        low, high = _vector(obj.low, "bounds"), _vector(obj.high, "bounds")
        if any(a > b for a, b in zip(low, high)):
            raise ValueError("Inverted spatial bounds")
        objects[obj.object_id] = obj
    return objects


def _receipt(evidence):
    return {"backend": evidence.backend, "model_identity": deepcopy(evidence.identity),
            "revision": evidence.revision, "provenance": deepcopy(evidence.provenance),
            "inventory_complete": evidence.inventory_complete,
            "inventory_scope": evidence.inventory_scope,
            "automatic_geometry_changes": False, "navigation_verified": False,
            "actual_walkability": "unverified", "building_code_compliance": False}


def blender_spatial_evidence(scene: dict) -> SpatialEvidence:
    """Adapt BlenderBackend's saved/reopened receipt, never proposed geometry.

The fixed Blender writer has translation-only transforms and applied box scale.
Its schema does not supply rotation/parent/modifier transforms. Unknown transform
fields fail closed rather than applying guessed transforms to native vertices.
"""
    measured = _native_objects(scene)
    if (not isinstance(scene.get("model_path"), str) or not scene["model_path"]
            or not isinstance(scene.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", scene["sha256"])):
        raise ValueError("Native model path and SHA256 identity are required")
    objects = []
    for name, obj in measured.items():
        native, spec = scene["geometry"][name], scene["objects"][name]
        unsupported = {"rotation", "rotation_euler", "rotation_quaternion", "scale",
                       "matrix_world", "matrix_local", "parent", "modifiers"}
        if unsupported.intersection(native) or unsupported.intersection(spec):
            raise ValueError("Unsupported native transform; spatial geometry is unverified")
        exact = "dimensions" in obj
        if exact:
            low = tuple(x - d / 2 for x, d in zip(obj["location"], obj["dimensions"]))
            high = tuple(x + d / 2 for x, d in zip(obj["location"], obj["dimensions"]))
        else:
            low = tuple(min(v[i] for v in obj["vertices"]) + obj["location"][i] for i in range(3))
            high = tuple(max(v[i] for v in obj["vertices"]) + obj["location"][i] for i in range(3))
        objects.append(SpatialObject(name, "blender:model", low, high, exact, True,
                                     () if exact else ("mesh_surface_not_inspected",)))
    evidence = SpatialEvidence("blender", {"model_path": scene["model_path"],
                               "sha256": scene["sha256"]}, scene["revision"],
                               tuple(objects), True, "project_owned_scene",
                               {"source": "BlenderBackend.blender_inspect_scene",
                                "native_reopen": scene["native_reopen"],
                                "geometry_sha256": hashlib.sha256(json.dumps(
                                    scene["geometry"], sort_keys=True, allow_nan=False).encode()).hexdigest()})
    _objects(evidence)
    return evidence


def audit_spatial_connections(evidence: SpatialEvidence, connections: list[dict]) -> dict:
    """Check oriented A-max/B-min contact, retaining bounds-only uncertainty."""
    objects = _objects(evidence)
    if not isinstance(connections, list) or not 1 <= len(connections) <= 64:
        raise ValueError("Expected 1 to 64 connections")
    # Reuse the existing complete connection-input validation without granting
    # exact-box status to an AABB that merely happens to have six bounds.
    proxies = {key: {"location": [0, 0, 0], "vertices": [list(o.low), list(o.high)]}
               for key, o in objects.items()}
    checked = audit_connections(proxies, connections)["connections"]
    rows = []
    for connection, measured in zip(connections, checked):
        a, b = objects[connection["a"]], objects[connection["b"]]
        common = {"a": a.object_id, "b": b.object_id, "axis": connection["axis"],
                  "tolerance_m": connection["tolerance"], "actual_walkability": "unverified"}
        if a.frame_id != b.frame_id:
            rows.append({**common, "status": "unverified", "bounds_status": "unverified",
                         "reason": "different_parent_frames_without_native_transforms",
                         "exact_for_boxes": False, "signed_gap_m": None})
            continue
        exact = a.exact_box and b.exact_box and a.metric_frame_verified and b.metric_frame_verified
        rows.append({**common, **measured, "frame_id": a.frame_id,
                     "metric_frame_verified": a.metric_frame_verified and b.metric_frame_verified,
                     "exact_for_boxes": exact, "mesh_surface_verification_required": not exact,
                     "status": ("satisfied_contact_proxy" if measured["bounds_status"] == "contact"
                                else "needs_fix") if exact else "unverified",
                     "reason": "exact_axis_aligned_box_contact_only" if exact else
                               "bounds_only_or_unverified_frame_transform"})
    return {**_receipt(evidence), "connections": rows,
            "note": "Local-frame metre values are not verified world distances when metric_frame_verified is false."}


def audit_spatial_clearance(evidence: SpatialEvidence, zones: list[dict],
                            endpoints: list[dict] | None = None) -> dict:
    """Audit up to 32 declared zones and 32 adjacent stair/landing endpoints.

    Zones: {name, location, dimensions, ignore_ids, frame_id?}. If omitted,
    frame_id is allowed only when every object shares one frame. Dimensions and
    requested thresholds use metres in that frame. Endpoints: {a,b,axis,
    min_width_m,max_step_m,tolerance_m}; axis is horizontal X or Y. The endpoint
    check compares adjacent A-max/B-min faces, lateral overlap and top elevation.
    It intentionally does not infer route order or claim stair walkability.
    """
    objects = _objects(evidence)
    if not isinstance(zones, list) or len(zones) > 32:
        raise ValueError("Expected at most 32 clearance zones")
    if endpoints is None:
        endpoints = []
    if not isinstance(endpoints, list) or len(endpoints) > 32 or not (zones or endpoints):
        raise ValueError("Expected at most 32 endpoints and at least one check")
    frames = {obj.frame_id for obj in objects.values()}
    zone_rows, names = [], set()
    for zone in zones:
        if (not isinstance(zone, dict) or not {"name", "location", "dimensions", "ignore_ids"}.issubset(zone)
                or set(zone) - {"name", "location", "dimensions", "ignore_ids", "frame_id"}
                or not isinstance(zone["name"], str) or not 1 <= len(zone["name"].strip()) <= 80
                or zone["name"] in names):
            raise ValueError("Invalid or duplicate clearance zone")
        names.add(zone["name"])
        location = _vector(zone["location"], "zone location")
        dimensions = _vector(zone["dimensions"], "zone dimensions", positive=True)
        frame = zone.get("frame_id")
        if frame is None and len(frames) == 1:
            frame = next(iter(frames))
        if not isinstance(frame, str) or frame not in frames:
            raise ValueError("A known explicit frame_id is required for mixed-frame geometry")
        ignored = zone["ignore_ids"]
        if (not isinstance(ignored, list) or len(ignored) > 256
                or any(not isinstance(i, str) or i not in objects for i in ignored)
                or len(set(ignored)) != len(ignored)):
            raise ValueError("Invalid clearance ignore_ids")
        low = tuple(x - d / 2 for x, d in zip(location, dimensions))
        high = tuple(x + d / 2 for x, d in zip(location, dimensions))
        blockers, candidates, unknown = [], [], []
        for name, obj in objects.items():
            if name in ignored:
                continue
            if obj.frame_id != frame or not obj.metric_frame_verified:
                unknown.append(name)
            if obj.frame_id != frame:
                continue
            overlap = all(min(high[i], obj.high[i]) - max(low[i], obj.low[i]) > 1e-6 for i in range(3))
            if overlap:
                (blockers if obj.exact_box and obj.metric_frame_verified else candidates).append(name)
        status = ("blocked" if blockers else "unverified" if candidates or unknown
                  or not evidence.inventory_complete else "clear_for_declared_zone")
        zone_rows.append({"name": zone["name"], "frame_id": frame, "status": status,
                          "box_blockers": blockers, "bounds_candidates": candidates,
                          "unverified_frame_ids": unknown, "ignored_ids": list(ignored),
                          "actual_walkability": "unverified"})
    endpoint_rows = []
    for endpoint in endpoints:
        if (not isinstance(endpoint, dict) or set(endpoint) != {
                "a", "b", "axis", "min_width_m", "max_step_m", "tolerance_m"}
                or not isinstance(endpoint["a"], str) or not isinstance(endpoint["b"], str)
                or endpoint["a"] not in objects or endpoint["b"] not in objects
                or endpoint["a"] == endpoint["b"] or type(endpoint["axis"]) is not int
                or endpoint["axis"] not in (0, 1)):
            raise ValueError("Invalid declared endpoint")
        width = _number(endpoint["min_width_m"], "minimum endpoint width", 0.001, 100)
        step = _number(endpoint["max_step_m"], "maximum endpoint step", 0, 1)
        tolerance = _number(endpoint["tolerance_m"], "endpoint tolerance", 0, 0.1)
        a, b = objects[endpoint["a"]], objects[endpoint["b"]]
        row = {**deepcopy(endpoint), "actual_walkability": "unverified"}
        if a.frame_id != b.frame_id:
            row.update(status="unverified", reason="different_parent_frames_without_native_transforms")
        else:
            axis, lateral = endpoint["axis"], 1 - endpoint["axis"]
            gap = b.low[axis] - a.high[axis]
            overlap = min(a.high[lateral], b.high[lateral]) - max(a.low[lateral], b.low[lateral])
            rise = b.high[2] - a.high[2]
            checks = {"oriented_contact": abs(gap) <= tolerance,
                      "minimum_width": overlap + tolerance >= width,
                      "maximum_step": abs(rise) <= step + tolerance}
            exact = a.exact_box and b.exact_box and a.metric_frame_verified and b.metric_frame_verified
            row.update(frame_id=a.frame_id, signed_gap_m=gap, overlap_width_m=overlap,
                       signed_top_step_m=rise, checks=checks,
                       metric_frame_verified=a.metric_frame_verified and b.metric_frame_verified,
                       exact_for_boxes=exact,
                       status=("satisfied_endpoint_proxy" if all(checks.values()) else "needs_fix")
                       if exact else "unverified",
                       reason="adjacent_box_top_endpoint_only" if exact else
                              "bounds_only_or_unverified_frame_transform")
        endpoint_rows.append(row)
    return {**_receipt(evidence), "zones": zone_rows, "endpoints": endpoint_rows,
            "method": "Declared axis-aligned empty-volume and adjacent-top endpoint proxies only"}


def prepare_blender_clearance_tools(backend):
    """Return (tool schemas, dispatcher); evidence is always read by the host."""
    name = "blender_audit_spatial_clearance"
    spec = {"name": name, "description": (
        "Read-only native measured clearance and adjacent stair/landing/corridor endpoint proxies. "
        "zones=[{name,location:[x,y,z],dimensions:[w,d,h],ignore_ids:[]}]; "
        "endpoints=[{a:existingID,b:existingID,axis:0|1,min_width_m,max_step_m,tolerance_m}]. "
        "Lengths in metres. Exact only for current axis-aligned boxes; meshes remain bounds candidates. "
        "A-max joins B-min; compare lateral width and top elevation. No full walking route, source "
        "fidelity or building-code approval. The host obtains native geometry, never accept receipts."),
        "inputSchema": {"type": "object", "properties": {
            "zones": {"type": "array", "maxItems": 32, "items": {"type": "object"}},
            "endpoints": {"type": "array", "maxItems": 32, "items": {"type": "object"}}},
            "required": ["zones", "endpoints"], "additionalProperties": False}}

    def dispatch(tool_name, arguments):
        if tool_name != name or not isinstance(arguments, dict) or set(arguments) != {"zones", "endpoints"}:
            raise ValueError("Expected declared zones and endpoints only")
        scene = backend.dispatch("blender_inspect_scene", {})
        return audit_spatial_clearance(blender_spatial_evidence(scene),
                                       arguments["zones"], arguments["endpoints"])

    return [spec], dispatch
