"""Compact project-local construction strategy for image reconstruction.

The design is an independent K Studio implementation inspired by the staged
construction/method-card architecture observed in ADAI SketchUp Skill + Managed
MCP. No CPAL source code is copied here.

The strategy is deliberately smaller than geometry truth. It records which
construction method owns each visible system, which shared parameters it
depends on, and which views must verify it. Actual SketchUp geometry remains
owned by the guarded ProjectRuby writer and real readback.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONSTRUCTION_STAGE_ORDER = (
    "primary_form",
    "representative_module",
    "replication",
    "variants",
    "finish",
)

CONSTRUCTION_METHODS = {
    "continuous_wall_with_openings",
    "profile_extrusion",
    "loft_or_mesh",
    "prototype_instance",
    "typed_semantic_helper",
    "custom_owned_ruby",
}

CONSTRUCTION_ROLES = {
    "shell",
    "opening_system",
    "roof",
    "balcony",
    "repetition",
    "facade_detail",
    "interior_detail",
    "site",
}

CONSTRUCTION_STATUS = {"pending", "built", "verified", "needs_fix"}
CONSTRUCTION_PROVENANCE = {"pending", "observed", "user_confirmed", "estimated", "inferred"}
PARAMETER_UNITS = {"mm", "degrees", "count", "ratio", "text"}
CANONICAL_REVIEW_VIEWS = {"front", "rear", "left", "right", "roof", "oblique"}


def default_construction_strategy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "current_stage": "pending",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": {},
        "systems": [],
        "notes": [],
    }


def construction_strategy_schema_note() -> str:
    """Expose the validator contract to a model that cannot read repository code."""
    example = default_construction_strategy()
    example["shared_parameters"] = {
        "storey_height": {"value": 3100, "units": "mm", "provenance": "estimated", "source": "image proportion"}
    }
    example["systems"] = [{
        "id": "walls", "stage": "primary_form", "role": "shell",
        "method": "continuous_wall_with_openings", "status": "pending",
        "depends_on": ["storey_height"], "target_paths": [["WALL_FRONT"]],
        "verification_views": ["front", "oblique"], "notes": ["Verify actual openings before replication."]
    }]
    return (
        "# Construction strategy JSON contract\n\n"
        "Read before writing notes/construction_strategy.json. JSON syntax alone is insufficient. "
        "Use current_stage=pending before execution; plan_only is invalid.\n\n"
        f"Stages: pending (current_stage only), {', '.join(CONSTRUCTION_STAGE_ORDER)}.\n"
        f"Methods: {', '.join(sorted(CONSTRUCTION_METHODS))}.\n"
        f"Roles: {', '.join(sorted(CONSTRUCTION_ROLES))}.\n"
        f"Status: {', '.join(sorted(CONSTRUCTION_STATUS))}.\n"
        f"Parameter provenance: {', '.join(sorted(CONSTRUCTION_PROVENANCE))}.\n"
        f"Parameter units: {', '.join(sorted(PARAMETER_UNITS))}.\n\n"
        "Numeric units require one numeric value, not an array. Split level/bay arrays into named scalar parameters; "
        "put explanations in source/notes, not provenance. Text units require a string. "
        "depends_on must reference shared parameter keys. target_paths is a list of exact owned-name segment lists. "
        "verification_views only front/rear/left/right/roof/oblique. notes must be concise string lists.\n\n"
        "```json\n" + json.dumps(example, ensure_ascii=False, indent=2) + "\n```\n"
    )


def _string_list(value: Any, label: str, *, maximum: int = 64) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > maximum or any(
        not isinstance(item, str) or not item.strip() or len(item) > 300 for item in value
    ):
        raise ValueError(f"{label} must be a list of concise nonempty strings.")
    return [item.strip() for item in value]


def _owned_paths(value: Any, label: str) -> list[list[str]]:
    if value in (None, []):
        return []
    if not isinstance(value, list) or len(value) > 32:
        raise ValueError(f"{label} must contain at most 32 owned paths.")
    paths: list[list[str]] = []
    for path in value:
        if (
            not isinstance(path, list)
            or not path
            or len(path) > 8
            or any(not isinstance(part, str) or not part.strip() or len(part) > 200 for part in path)
        ):
            raise ValueError(f"{label} paths must contain 1..8 exact owned-group names.")
        paths.append([part.strip() for part in path])
    return paths


def validate_construction_strategy_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("construction strategy root must be an object.")
    if value.get("schema_version") != 1:
        raise ValueError("construction strategy schema_version must be 1.")

    stage_order = value.get("stage_order", list(CONSTRUCTION_STAGE_ORDER))
    if stage_order != list(CONSTRUCTION_STAGE_ORDER):
        raise ValueError("construction strategy stage_order must use the supported five-stage sequence.")
    current_stage = value.get("current_stage", "pending")
    if current_stage not in {"pending", *CONSTRUCTION_STAGE_ORDER}:
        raise ValueError("construction strategy current_stage is invalid.")

    raw_parameters = value.get("shared_parameters", {})
    if not isinstance(raw_parameters, dict) or len(raw_parameters) > 96:
        raise ValueError("construction strategy shared_parameters must be an object with at most 96 entries.")
    parameters: dict[str, dict[str, Any]] = {}
    for key, item in raw_parameters.items():
        if not isinstance(key, str) or not key.strip() or len(key) > 100:
            raise ValueError("construction strategy parameter names must be concise nonempty strings.")
        if not isinstance(item, dict):
            raise ValueError(f"construction strategy parameter {key!r} must be an object.")
        units = item.get("units", "text")
        provenance = item.get("provenance", "pending")
        if units not in PARAMETER_UNITS:
            raise ValueError(f"construction strategy parameter {key!r} has invalid units.")
        if provenance not in CONSTRUCTION_PROVENANCE:
            raise ValueError(f"construction strategy parameter {key!r} has invalid provenance.")
        raw_value = item.get("value")
        if units in {"mm", "degrees", "count", "ratio"} and raw_value is not None:
            if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
                raise ValueError(f"construction strategy parameter {key!r} must use a numeric value.")
            if units == "count" and (int(raw_value) != raw_value or raw_value < 0):
                raise ValueError(f"construction strategy count parameter {key!r} must be a nonnegative integer.")
        if units == "text" and raw_value is not None and not isinstance(raw_value, str):
            raise ValueError(f"construction strategy text parameter {key!r} must use a string value.")
        source = item.get("source", "")
        if not isinstance(source, str) or len(source) > 1000:
            raise ValueError(f"construction strategy parameter {key!r} source is invalid.")
        parameters[key.strip()] = {
            "value": raw_value,
            "units": units,
            "provenance": provenance,
            "source": source.strip(),
        }

    raw_systems = value.get("systems", [])
    if not isinstance(raw_systems, list) or len(raw_systems) > 48:
        raise ValueError("construction strategy systems must be a list with at most 48 entries.")
    systems: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_systems):
        if not isinstance(item, dict):
            raise ValueError(f"construction strategy systems[{index}] must be an object.")
        system_id = item.get("id")
        if not isinstance(system_id, str) or not system_id.strip() or len(system_id) > 100:
            raise ValueError(f"construction strategy systems[{index}].id is invalid.")
        system_id = system_id.strip()
        if system_id in seen_ids:
            raise ValueError(f"construction strategy system id {system_id!r} is duplicated.")
        seen_ids.add(system_id)
        stage = item.get("stage")
        role = item.get("role")
        method = item.get("method")
        status = item.get("status", "pending")
        if stage not in CONSTRUCTION_STAGE_ORDER:
            raise ValueError(f"construction strategy system {system_id!r} has invalid stage.")
        if role not in CONSTRUCTION_ROLES:
            raise ValueError(f"construction strategy system {system_id!r} has invalid role.")
        if method not in CONSTRUCTION_METHODS:
            raise ValueError(f"construction strategy system {system_id!r} has invalid method.")
        if status not in CONSTRUCTION_STATUS:
            raise ValueError(f"construction strategy system {system_id!r} has invalid status.")
        depends_on = _string_list(item.get("depends_on", []), f"systems[{index}].depends_on")
        unknown = [name for name in depends_on if name not in parameters]
        if unknown:
            raise ValueError(
                f"construction strategy system {system_id!r} depends on unknown parameters: {', '.join(unknown)}."
            )
        verification_views = _string_list(
            item.get("verification_views", []),
            f"systems[{index}].verification_views",
            maximum=6,
        )
        bad_views = [name for name in verification_views if name not in CANONICAL_REVIEW_VIEWS]
        if bad_views:
            raise ValueError(
                f"construction strategy system {system_id!r} has invalid verification views: {', '.join(bad_views)}."
            )
        systems.append({
            "id": system_id,
            "stage": stage,
            "role": role,
            "method": method,
            "status": status,
            "depends_on": depends_on,
            "target_paths": _owned_paths(item.get("target_paths", []), f"systems[{index}].target_paths"),
            "verification_views": verification_views,
            "notes": _string_list(item.get("notes", []), f"systems[{index}].notes"),
        })

    notes = _string_list(value.get("notes", []), "construction strategy notes")
    return {
        "schema_version": 1,
        "current_stage": current_stage,
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": parameters,
        "systems": systems,
        "notes": notes,
    }


def strategy_has_signal(value: dict[str, Any] | None) -> bool:
    if not value:
        return False
    if value.get("current_stage") not in {None, "", "pending"}:
        return True
    if value.get("systems"):
        return True
    for item in (value.get("shared_parameters") or {}).values():
        if isinstance(item, dict) and item.get("value") is not None:
            return True
    return False


def load_construction_strategy(project_dir: Path) -> dict[str, Any] | None:
    path = (
        project_dir.resolve()
        / "runtime"
        / "agent_workspace"
        / "notes"
        / "construction_strategy.json"
    )
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 96 * 1024:
        return None
    try:
        return validate_construction_strategy_payload(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
