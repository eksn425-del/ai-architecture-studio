"""Validate complete, content-addressed native definition-graph evidence."""
from __future__ import annotations
import hashlib
import json
import math
import re
from typing import Any

GRAPH_COLLECTOR = "KStudioNativeDefinitionGraph/1"


def validate_definition_graph(value: dict[str, Any]) -> None:
    def fail(message: str) -> None:
        raise ValueError("Incomplete native definition graph: " + message)

    def finite(items: Any) -> None:
        if isinstance(items, float) and not math.isfinite(items):
            fail("nonfinite number")
        elif isinstance(items, dict):
            for part in items.values():
                finite(part)
        elif isinstance(items, list):
            for part in items:
                finite(part)

    def digest_json(raw: Any, expected: str) -> dict:
        if not isinstance(raw, str) or hashlib.sha256(raw.encode("utf-8")).hexdigest() != expected:
            fail("canonical native payload SHA mismatch")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            fail("canonical payload is not an object")
        finite(parsed)
        return parsed

    def vector(items: Any, size: int) -> None:
        if not isinstance(items, list) or len(items) != size or any(type(x) not in (int, float) or not math.isfinite(x) for x in items):
            fail("invalid native coordinate/transform")

    if value.get("collector") != GRAPH_COLLECTOR or value.get("complete_reference_graph") is not True:
        fail("collector/completeness contract missing")
    visited = value.get("unique_entities_visited")
    if type(visited) is not int or not 0 < visited <= 250_000:
        fail("physical entity budget invalid")
    definitions = value.get("definitions")
    if not isinstance(definitions, dict) or not definitions or value.get("definition_count") != len(definitions):
        fail("definition table missing or truncated")
    parsed: dict[str, dict] = {}
    memo: dict[str, tuple[dict, int]] = {}
    active: set[str] = set()

    def instance(item: Any) -> str:
        keys = {"type", "name", "definition_name", "definition_ref", "local_transform", "material", "hidden", "locked", "tag"}
        if not isinstance(item, dict) or set(item) != keys or item["type"] not in ("Group", "ComponentInstance"):
            fail("incomplete instance descriptor")
        if not isinstance(item["name"], str) or not isinstance(item["definition_name"], str):
            fail("instance names missing")
        if type(item["hidden"]) is not bool or type(item["locked"]) is not bool:
            fail("instance display/lock state missing")
        vector(item["local_transform"], 16)
        return item["definition_ref"]

    def resolve(ref: str) -> tuple[dict, int]:
        if not isinstance(ref, str) or not re.fullmatch(r"[a-f0-9]{64}", ref) or ref not in definitions:
            fail("missing referenced definition")
        if ref in active:
            fail("recursive definition reference")
        if ref in memo:
            return memo[ref]
        if len(active) >= 24:
            fail("definition depth exceeded")
        active.add(ref)
        record = definitions[ref]
        if not isinstance(record, dict):
            fail("definition record missing")
        payload = digest_json(record.get("canonical_payload_json"), ref)
        if set(payload) != {"definition_name", "faces_local_mm", "edges_local_mm", "sections", "instances"}:
            fail("prototype geometry/topology fields missing")
        if not isinstance(payload["definition_name"], str) or any(not isinstance(payload[k], list) for k in ("faces_local_mm", "edges_local_mm", "sections", "instances")):
            fail("prototype collections missing")
        for face in payload["faces_local_mm"]:
            if not isinstance(face, dict) or set(face) != {"loops", "normal", "front", "back", "hidden", "tag"}:
                fail("face topology/material missing")
            vector(face["normal"], 3)
            if type(face["hidden"]) is not bool:
                fail("face visibility missing")
            loops = face["loops"]
            if not isinstance(loops, list) or sum(l.get("outer") is True for l in loops if isinstance(l, dict)) != 1:
                fail("face outer/hole loops incomplete")
            for loop in loops:
                if not isinstance(loop, dict) or type(loop.get("outer")) is not bool or not isinstance(loop.get("points"), list) or len(loop["points"]) < 3:
                    fail("face loop incomplete")
                for point in loop["points"]:
                    vector(point, 3)
        for edge in payload["edges_local_mm"]:
            if not isinstance(edge, dict) or set(edge) != {"endpoints", "hidden", "soft", "smooth", "tag"} or not isinstance(edge["endpoints"], list) or len(edge["endpoints"]) != 2:
                fail("edge geometry/flags incomplete")
            for point in edge["endpoints"]:
                vector(point, 3)
            if any(type(edge[key]) is not bool for key in ("hidden", "soft", "smooth")):
                fail("edge flags missing")
        boundaries = {tuple(sorted(tuple(p) for p in edge["endpoints"])) for edge in payload["edges_local_mm"]}
        for face in payload["faces_local_mm"]:
            for loop in face["loops"]:
                points = loop["points"]
                if any(tuple(sorted((tuple(points[i]), tuple(points[(i + 1) % len(points)])))) not in boundaries for i in range(len(points))):
                    fail("face boundary edges omitted")
        for section in payload["sections"]:
            if not isinstance(section, dict) or set(section) != {"name", "plane", "active", "hidden", "tag"}:
                fail("section geometry missing")
            vector(section["plane"], 4)
        counts = {"faces": len(payload["faces_local_mm"]), "edges": len(payload["edges_local_mm"]), "instances": len(payload["instances"])}
        depth = 0
        for child in payload["instances"]:
            child_counts, child_depth = resolve(instance(child))
            for key in counts:
                counts[key] += child_counts[key]
            depth = max(depth, 1 + child_depth)
        if record.get("counts") != counts or any(type(x) is not int for x in record.get("counts", {}).values()) or type(record.get("depth")) is not int or record.get("depth") != depth:
            fail("expanded counts/depth disagree with complete instance graph")
        active.remove(ref)
        parsed[ref] = payload
        memo[ref] = (counts, depth)
        return memo[ref]

    document = digest_json(value.get("document_canonical_json"), value.get("document_geometry_material_sha256", ""))
    if set(document) != {"faces", "edges", "sections", "nodes"} or any(not isinstance(document[k], list) for k in document):
        fail("document geometry missing")
    native_instances = value.get("document_instances")
    if not isinstance(native_instances, list) or document["nodes"] != [x.get("geometry") for x in native_instances]:
        fail("document instances truncated")
    for item in document["nodes"]:
        resolve(instance(item))
    if set(memo) != set(definitions):
        fail("unreferenced or unverified definition table entries")
    if value.get("document_loose") != {k: document[k] for k in ("faces", "edges", "sections")}:
        fail("document loose geometry mismatch")

    def node(item: Any) -> dict:
        if not isinstance(item, dict):
            fail("native instance node missing")
        payload = digest_json(item.get("canonical_geometry_json"), item.get("geometry_material_sha256", ""))
        if set(payload) != {"instance", "world_transform"}:
            fail("instance world frame missing")
        vector(payload["world_transform"], 16)
        ref = instance(payload["instance"])
        counts, _ = resolve(ref)
        if item.get("definition_ref") != ref or item.get("counts") != counts or item.get("name") != payload["instance"]["name"]:
            fail("instance readback disagrees with definition graph")
        return payload["instance"]

    root = value.get("root_instance")
    root_geometry = node(root)
    if root.get("pid") != value.get("root_pid") or root.get("counts") != value.get("counts") or root.get("geometry_material_sha256") != value.get("root_geometry_material_sha256"):
        fail("owned root identity/count/hash mismatch")
    if not any(x.get("pid") == value["root_pid"] and x.get("geometry") == root_geometry for x in native_instances):
        fail("owned root absent from document graph")
    groups = value.get("groups")
    if not isinstance(groups, list):
        fail("owned group readback missing")
    actual = [node(x) for x in groups]
    expected = parsed[root_geometry["definition_ref"]]["instances"]
    if sorted(actual, key=lambda x: x["name"]) != sorted(expected, key=lambda x: x["name"]):
        fail("owned direct groups omitted or changed")
