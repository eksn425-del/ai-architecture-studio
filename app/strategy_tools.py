"""Typed, version-bound plan updates for APIs without a native coding harness.

This writes planning memory only. It never grants approval or touches geometry.
The persisted strategy validator remains the source of the plan contract.
"""
import hashlib
import json

from .construction_strategy import (
    CONSTRUCTION_METHODS, CONSTRUCTION_PROVENANCE, CONSTRUCTION_ROLES,
    CONSTRUCTION_STAGE_ORDER, CONSTRUCTION_STATUS, CANONICAL_REVIEW_VIEWS,
    validate_construction_strategy_payload,
)
from .oss_method_catalog import BY_ID

PATH = "notes/construction_strategy.json"
NAME = "workspace_update_strategy"


def strategy_update_tool():
    string = {"type": "string", "minLength": 1, "maxLength": 100}
    strings = {"type": "array", "items": {"type": "string"}, "maxItems": 64}
    parameter = {"type": "object", "additionalProperties": False, "required": [
        "name", "units", "value", "provenance", "source"], "properties": {
        "name": string, "units": {"type": "string", "enum": ["mm", "degrees", "count", "ratio", "text"]},
        "value": {"anyOf": [{"type": "number"}, {"type": "string"}, {"type": "null"}]},
        "provenance": {"type": "string", "enum": sorted(CONSTRUCTION_PROVENANCE)},
        "source": {"type": "string", "maxLength": 1000}}}
    system = {"type": "object", "additionalProperties": False, "required": [
        "id", "stage", "role", "method", "method_id", "selection_reason", "depends_on",
        "target_paths", "verification_views", "notes"], "properties": {
        "id": string, "stage": {"type": "string", "enum": list(CONSTRUCTION_STAGE_ORDER)},
        "role": {"type": "string", "enum": sorted(CONSTRUCTION_ROLES)},
        "method": {"type": "string", "enum": sorted(CONSTRUCTION_METHODS)},
        "status": {"type": "string", "enum": sorted(CONSTRUCTION_STATUS)},
        "method_id": {"type": "string", "enum": sorted(BY_ID)},
        "selection_reason": {"type": "string", "minLength": 1, "maxLength": 500},
        "depends_on": strings,
        "target_paths": {"type": "array", "maxItems": 32, "items": {
            "type": "array", "minItems": 1, "maxItems": 8,
            "items": {"type": "string", "minLength": 1, "maxLength": 200}}},
        "verification_views": {"type": "array", "maxItems": 6, "items": {
            "type": "string", "enum": sorted(CANONICAL_REVIEW_VIEWS)}}, "notes": strings}}
    return {"type": "function", "name": NAME,
        "description": "Update only changed construction-strategy parameters/systems by stable name/id. Read notes/construction_strategy.json first and copy its file_sha256 into expected_sha256. Unspecified entries remain unchanged; no deletion, geometry execution or approval. Prefer this typed tool over rewriting JSON text. Numeric units require scalar numbers, text units strings; counts are nonnegative integers. Array coordinates must be separate scalar parameters. Status is advisory, never host QA. All changes validate together before writing.",
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["expected_sha256"],
            "properties": {"expected_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "parameters": {"type": "array", "maxItems": 96, "items": parameter},
                "systems": {"type": "array", "maxItems": 48, "items": system}}}}


def update_strategy(arguments, *, read, write):
    """No coercion of units, provenance, roles, coordinates or evidence."""
    schema = strategy_update_tool()["inputSchema"]
    if not isinstance(arguments, dict) or set(arguments) - set(schema["properties"]):
        raise ValueError("Unknown strategy update fields; use the typed tool contract.")
    previous = read()
    digest = hashlib.sha256(previous["content"].encode("utf-8")).hexdigest()
    if arguments.get("expected_sha256") != digest:
        raise ValueError("Strategy changed or version missing. Read the file again; no file was changed.")
    value = validate_construction_strategy_payload(json.loads(previous["content"]))
    parameters = arguments.get("parameters", [])
    systems = arguments.get("systems", [])
    if not isinstance(parameters, list) or len(parameters) > 96 or not isinstance(systems, list) or len(systems) > 48:
        raise ValueError("Strategy update exceeds parameter/system limits.")
    if not parameters and not systems:
        raise ValueError("Supply changed parameters or systems, not an empty update.")
    for items, kind, key in ((parameters, "parameters", "name"), (systems, "systems", "id")):
        item_schema = schema["properties"][kind]["items"]
        seen = set()
        for item in items:
            if (not isinstance(item, dict) or set(item) - set(item_schema["properties"])
                    or set(item_schema["required"]) - set(item)):
                raise ValueError(f"Invalid {kind} fields; use exact required fields from the typed tool contract.")
            identity = item[key]
            if not isinstance(identity, str) or not identity.strip() or identity.strip() in seen:
                raise ValueError(f"Missing or duplicate {kind} identity.")
            seen.add(identity.strip())
    for item in parameters:
        value["shared_parameters"][item["name"].strip()] = {k: v for k, v in item.items() if k != "name"}
    by_id = {item["id"]: item for item in value["systems"]}
    for item in systems:
        by_id[item["id"].strip()] = item
    value["systems"] = list(by_id.values())
    validated = validate_construction_strategy_payload(value)
    result = write(json.dumps(validated, ensure_ascii=False, indent=2) + "\n")
    return {**result, "updated_parameters": [p["name"] for p in parameters],
            "updated_systems": [s["id"] for s in systems],
            "notice": "Planning memory only; no geometry, approval or verified-quality claim."}
