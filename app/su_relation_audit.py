"""Read-only adapter for the EXISTING ProjectRubyExecutor.inspect_owned schema.

The adapter calls the guarded native collector itself. No model-authored receipt
or invented native evidence field is accepted. The collector returns AABBs in
parent-local millimetres, not solids or ancestor transforms. Therefore this
bounded adapter can diagnose same-parent contact proxies, but cannot certify
physical clearance, walkability, a saved/reopened file, or a repair completion.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

from .spatial_clearance import (SpatialEvidence, SpatialObject, _vector,
                                audit_spatial_connections, audit_spatial_clearance)


def owned_path_id(path: list[str]) -> str:
    """Unambiguous ID: a slash in a native name is not a path separator."""
    if (not isinstance(path, list) or not 1 <= len(path) <= 8
            or any(not isinstance(p, str) or not p or len(p) > 200 for p in path)):
        raise ValueError("Expected a nonempty exact owned path of at most eight names")
    return json.dumps(path, ensure_ascii=False, separators=(",", ":"))


def _identity(executor, script_id):
    if not isinstance(script_id, str) or not script_id:
        raise ValueError("An existing script_id is required")
    state = executor.ruby_state.get(script_id, {})
    if (type(state.get("root_pid")) is not int or state["root_pid"] <= 0
            or type(state.get("revision")) is not int or state["revision"] < 1):
        raise ValueError("An existing committed native root and revision are required")
    identity = {"project_id": executor.project_id, "script_id": script_id,
                "model_path": str(executor.expected_model_path),
                "model_guid": executor.expected_model_guid, "root_pid": state["root_pid"]}
    if any(not isinstance(identity[k], str) or not identity[k] for k in
           ("project_id", "script_id", "model_path", "model_guid")):
        raise ValueError("Missing host-bound model identity")
    return identity, state["revision"]


def inspect_su_relation_evidence(executor, script_id: str,
                                 paths: list[list[str]]) -> SpatialEvidence:
    """Collect at most 48 exact paths in one existing guarded read-only query.

    Pass the host's ProjectRubyExecutor, not untrusted JSON. Native guard errors
    propagate. Recheck identity/revision after the call to reject a concurrent
    document switch or commit. Native output schema is defined in project_ruby.py
    and KStudioProfessionalHelpers.inspect_named_owned_group, unmodified here.
    """
    if not isinstance(paths, list) or not 1 <= len(paths) <= 48:
        raise ValueError("Expected 1 to 48 exact owned paths")
    ids = [owned_path_id(path) for path in paths]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate owned paths")
    # Resolve an already-stale autosave token through the executor's existing
    # native ownership proof BEFORE capturing the race baseline. Never forgive
    # an identity/revision change during the inspection below.
    verify_identity = getattr(executor, "verify_active_model", None)
    if callable(verify_identity):
        verify_identity()
    identity, revision = _identity(executor, script_id)
    response = executor.inspect_owned({"script_id": script_id, "paths": deepcopy(paths)})
    if _identity(executor, script_id) != (identity, revision):
        raise ValueError("Model identity or revision changed during native inspection; inspect again")
    if not isinstance(response, dict) or response.get("success") is not True:
        raise ValueError("Native owned inspection failed")
    items = response.get("contentItems")
    if (not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict)
            or items[0].get("type") != "inputText" or not isinstance(items[0].get("text"), str)
            or len(items[0]["text"]) > 2_000_000):
        raise ValueError("Invalid owned-inspection envelope")
    payload = json.loads(items[0]["text"])
    if (not isinstance(payload, dict) or payload.get("read_only") is not True
            or payload.get("script_id") != script_id or type(payload.get("revision")) is not int
            or payload["revision"] != revision):
        raise ValueError("Inspection provenance/revision does not match the host-bound model")
    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != len(paths):
        raise ValueError("Incomplete native owned-path batch")
    objects, collected, native_paths = [], set(), []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            raise ValueError("Invalid native snapshot")
        path = snapshot.get("path")
        object_id = owned_path_id(path)
        if object_id not in ids or object_id in collected:
            raise ValueError("Native path batch was substituted or duplicated")
        collected.add(object_id)
        pid = snapshot.get("persistent_id")
        collector = snapshot.get("deep_fingerprint_collector")
        deep_sha = snapshot.get("deep_geometry_material_sha256")
        if (type(pid) is not int or pid <= 0 or snapshot.get("bounds_units") != "mm"
                or snapshot.get("bounds_frame") != "parent-local"
                or snapshot.get("object_bounds_frame") != "selected-group-local"
                or collector not in {"KStudioNativeDeepFingerprint/1", "KStudioNativeDefinitionGraph/1"}
                or not isinstance(deep_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", deep_sha)):
            raise ValueError("Unsupported native bounds frame, units, identity or fingerprint provenance")
        bounds = snapshot.get("bounds_mm")
        if not isinstance(bounds, dict):
            raise ValueError("Missing measured native bounds")
        low, high = _vector(bounds.get("min"), "native bounds"), _vector(bounds.get("max"), "native bounds")
        if any(a > b for a, b in zip(low, high)):
            raise ValueError("Inverted native bounds")
        # All selected groups are geometry-unclassified. Deep hashes prove
        # change detection, not solid-box geometry or an identity world matrix.
        frame_id = "sketchup:parent:" + json.dumps(path[:-1], ensure_ascii=False, separators=(",", ":"))
        objects.append(SpatialObject(object_id, frame_id, tuple(v / 1000 for v in low),
                                     tuple(v / 1000 for v in high), False, False,
                                     ("aabb_not_solid_geometry", "ancestor_transforms_not_returned")))
        native_paths.append({"path": deepcopy(path), "persistent_id": pid,
                             "deep_fingerprint_collector": collector,
                             "deep_geometry_material_sha256": deep_sha})
    return SpatialEvidence("sketchup", identity, revision, tuple(objects), False,
                           "selected_owned_paths_only_not_whole_document",
                           {"source": "ProjectRubyExecutor.inspect_owned(paths)", "read_only": True,
                            "bounds_units": "mm", "bounds_frame": "parent-local",
                            "inspection_sha256": hashlib.sha256(items[0]["text"].encode()).hexdigest(),
                            "native_paths": native_paths})


def audit_su_relations(executor, script_id: str, connections: list[dict]) -> dict:
    """Convenience wrapper: connections use exact path arrays for a and b.

    Other fields match the existing contact audit: axis=0|1|2, tolerance in
    parent-frame metres (0..0.1). No returned SU relation is an exact-solid PASS.
    """
    if not isinstance(connections, list) or not 1 <= len(connections) <= 64:
        raise ValueError("Expected 1 to 64 connections")
    paths, ids, normalized = [], set(), []
    for connection in connections:
        if not isinstance(connection, dict) or set(connection) != {"a", "b", "axis", "tolerance"}:
            raise ValueError("Invalid SU connection fields")
        endpoints = {}
        for key in ("a", "b"):
            path = connection[key]
            object_id = owned_path_id(path)
            endpoints[key] = object_id
            if object_id not in ids:
                ids.add(object_id)
                paths.append(path)
        normalized.append({**connection, **endpoints})
    # Validate declarations before issuing any native read.
    from .blender_connections import audit_connections
    audit_connections({key: {"location": [0, 0, 0], "dimensions": [1, 1, 1]} for key in ids}, normalized)
    evidence = inspect_su_relation_evidence(executor, script_id, paths)
    result = audit_spatial_connections(evidence, normalized)
    for row, original in zip(result["connections"], connections):
        row["a_path"], row["b_path"] = deepcopy(original["a"]), deepcopy(original["b"])
    result["note"] = ("Parent-local native AABB contact proxy only; no exact solid, ancestor transform, "
                      "world metric, saved-file, source-fidelity or walking-route pass is established.")
    return result


def prepare_su_relation_tools(executor):
    """Return (schemas, dispatcher), closing the model-authored receipt path.

    The dispatcher owns the current guarded inspection. Raw model identities,
    revisions, snapshots, geometry classifications or transform assertions are
    not tool parameters. No writer or repair-plan completion is introduced.
    """
    path_schema = {"type": "array", "minItems": 1, "maxItems": 8,
                   "items": {"type": "string", "minLength": 1, "maxLength": 200}}
    relation_spec = {"name": "sketchup_audit_relations", "description": (
        "Read-only current owned-native AABB relation proxies, never solid or walking-route PASS. "
        "connections=[{a:[exact,names],b:[exact,names],axis:0|1|2,tolerance:0..0.1}]. "
        "A max to B min on axis. Lengths are parent-local metres, ancestor scaling/orientation "
        "is unverified. Different parent frames remain unverified. At most48 unique paths. "
        "Host binds model GUID/root/revision and obtains native evidence itself."),
        "inputSchema": {"type": "object", "properties": {
            "script_id": {"type": "string"}, "connections": {"type": "array", "minItems": 1,
                "maxItems": 64, "items": {"type": "object", "properties": {
                    "a": path_schema, "b": path_schema,
                    "axis": {"type": "integer", "enum": [0, 1, 2]},
                    "tolerance": {"type": "number", "minimum": 0, "maximum": .1}},
                    "required": ["a", "b", "axis", "tolerance"], "additionalProperties": False}}},
            "required": ["script_id", "connections"], "additionalProperties": False}}
    vector_schema = {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}
    zone_schema = {"type": "object", "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 80},
        "location": vector_schema,
        "dimensions": {**vector_schema, "items": {"type": "number", "exclusiveMinimum": 0}},
        "ignore_paths": {"type": "array", "maxItems": 256, "items": path_schema},
        "parent_path": {**path_schema, "minItems": 0}},
        "required": ["name", "location", "dimensions", "ignore_paths", "parent_path"], "additionalProperties": False}
    endpoint_schema = {"type": "object", "properties": {
        "a": path_schema, "b": path_schema, "axis": {"type": "integer", "enum": [0, 1]},
        "min_width_m": {"type": "number", "minimum": .001, "maximum": 100},
        "max_step_m": {"type": "number", "minimum": 0, "maximum": 1},
        "tolerance_m": {"type": "number", "minimum": 0, "maximum": .1}},
        "required": ["a", "b", "axis", "min_width_m", "max_step_m", "tolerance_m"], "additionalProperties": False}
    clearance_spec = {"name": "sketchup_audit_clearance", "description": (
        "Read-only bounded clearance/endpoint candidates from selected exact native owned paths. "
        "paths=[[exact,names],...], max48. zones=[{name,location:[x,y,z],dimensions:[w,d,h],"
        "ignore_paths:[[exact,names],...],parent_path:[exact,parent]}]. parent_path may be [] "
        "for direct children of the owned root. It must equal path[:-1] of at least one selected path; "
        "do not supply frame_id. ignore_paths and endpoint paths must be in paths. "
        "All distances in parent-local metres; native "
        "ancestor transforms and full obstacle inventory are unavailable, so results stay unverified. "
        "endpoints=[{a:[exact,names],b:[exact,names],axis:0|1,min_width_m,max_step_m,tolerance_m}]. "
        "No physical walkability, stair safety, source-fidelity or building-code PASS."),
        "inputSchema": {"type": "object", "properties": {
            "script_id": {"type": "string"},
            "paths": {"type": "array", "minItems": 1, "maxItems": 48, "items": path_schema},
            "zones": {"type": "array", "maxItems": 32, "items": zone_schema},
            "endpoints": {"type": "array", "maxItems": 32, "items": endpoint_schema}},
            "required": ["script_id", "paths", "zones", "endpoints"], "additionalProperties": False}}

    def dispatch(name, arguments):
        if not isinstance(arguments, dict):
            raise ValueError("Invalid SU audit arguments")
        if name == relation_spec["name"]:
            if set(arguments) != {"script_id", "connections"}:
                raise ValueError("Only script_id and declared connections are accepted")
            return audit_su_relations(executor, arguments["script_id"], arguments["connections"])
        if name != clearance_spec["name"] or set(arguments) != {"script_id", "paths", "zones", "endpoints"}:
            raise ValueError("Only script_id, exact paths, zones and endpoints are accepted")
        if (not isinstance(arguments["zones"], list) or len(arguments["zones"]) > 32
                or not isinstance(arguments["endpoints"], list) or len(arguments["endpoints"]) > 32
                or not (arguments["zones"] or arguments["endpoints"])):
            raise ValueError("Invalid bounded clearance checks")
        zones, endpoints = [], []
        for zone in arguments["zones"]:
            if not isinstance(zone, dict) or set(zone) != {"name", "location", "dimensions", "ignore_paths", "parent_path"}:
                raise ValueError("Native zone requires exactly name, location, dimensions, ignore_paths and parent_path; use parent_path, not frame_id. No native read was attempted.")
            parent = zone["parent_path"]
            if parent != []:
                owned_path_id(parent)
            if not isinstance(arguments["paths"], list) or not any(
                    isinstance(path, list) and path[:-1] == parent for path in arguments["paths"]):
                raise ValueError("zone.parent_path must match the parent of a selected exact path (path[:-1]); coordinates are parent-local metres. No native read was attempted.")
            if not isinstance(zone["ignore_paths"], list) or len(zone["ignore_paths"]) > 256:
                raise ValueError("Invalid ignored exact paths")
            zones.append({"name": zone["name"], "location": zone["location"],
                          "dimensions": zone["dimensions"],
                          "ignore_ids": [owned_path_id(p) for p in zone["ignore_paths"]],
                          "frame_id": "sketchup:parent:" + json.dumps(parent, ensure_ascii=False, separators=(",", ":"))})
        for endpoint in arguments["endpoints"]:
            if not isinstance(endpoint, dict) or set(endpoint) != {"a", "b", "axis", "min_width_m", "max_step_m", "tolerance_m"}:
                raise ValueError("Invalid declared native endpoint")
            endpoints.append({**endpoint, "a": owned_path_id(endpoint["a"]),
                              "b": owned_path_id(endpoint["b"])})
        evidence = inspect_su_relation_evidence(executor, arguments["script_id"], arguments["paths"])
        return audit_spatial_clearance(evidence, zones, endpoints)

    return [relation_spec, clearance_spec], dispatch
