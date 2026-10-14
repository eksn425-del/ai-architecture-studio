"""Small, zero-SketchUp spatial handedness probe for the owner's eight source images.

This is an EXPLICIT diagnostic artefact, not inferred truth or an automatic
approval to overwrite the existing r1. A human architect confirms the X/Y
reference frame, high/low roof ends and ramp travel BEFORE geometry generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AXES = {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}
PLAN_AXES = {"+X", "-X", "+Y", "-Y"}
KINDS = {"exterior", "physical_model", "floor_plan", "section", "interior", "detail", "unknown"}
PROVENANCE = {"observed", "user_confirmed", "estimated", "unresolved"}


def _landmark(data: Any, label: str, *, vertical: bool = False) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ValueError(label + " needs source, axis, feature and provenance.")
    axis = data.get("axis")
    provenance = data.get("provenance")
    source = data.get("source")
    feature = data.get("feature")
    if axis not in (AXES if vertical else PLAN_AXES):
        raise ValueError(label + " must use an explicit signed model axis.")
    if provenance not in PROVENANCE:
        raise ValueError(label + " must declare evidence provenance.")
    if not isinstance(source, str) or not source.strip() or len(source) > 180:
        raise ValueError(label + " must cite a specific real source filename/panel.")
    if not isinstance(feature, str) or not feature.strip() or len(feature) > 180:
        raise ValueError(label + " must describe a spatial observation, not an abstract axis.")
    return {"axis": axis, "provenance": provenance, "source": source.strip(), "feature": feature.strip()}


def validate_spatial_spec(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Spatial specification requires schema_version 1.")
    status = data.get("status")
    if status not in {"DRAFT_NEEDS_OWNER_REVIEW", "OWNER_CONFIRMED", "AGENT_REVIEWED_OWNER_DELEGATED"}:
        raise ValueError("Spatial status must be an honest human review state.")
    anchor = data.get("model_axes")
    if not isinstance(anchor, dict):
        raise ValueError("Define model_axes before any perspective mapping.")
    directions: dict[str, str] = {}
    for field in ("positive_x", "positive_y", "positive_z"):
        value = anchor.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 180:
            raise ValueError("model_axes." + field + " requires a source-grounded explanation.")
        directions[field] = value.strip()
    views = data.get("source_views")
    if not isinstance(views, list) or not 1 <= len(views) <= 16:
        raise ValueError("Give 1..16 actual original source files, one entry per real input.")
    normalized = []
    seen = set()
    for i, view in enumerate(views):
        if not isinstance(view, dict) or not isinstance(view.get("filename"), str):
            raise ValueError("source_views entry requires real filename.")
        filename = view["filename"].strip()
        if not filename or filename in seen or "/" in filename or "\\" in filename:
            raise ValueError("Duplicate/unsafe source filename or non-leaf path.")
        seen.add(filename)
        if view.get("kind") not in KINDS:
            raise ValueError("Source kind must distinguish exterior/plan/section/interior/details.")
        if view.get("looking_towards") not in AXES | {"undetermined", "not_applicable"}:
            raise ValueError("Each image must map to a known model direction or say undetermined.")
        normalized.append({"filename": filename, "kind": view["kind"],
                           "looking_towards": view["looking_towards"]})
    roof = data.get("roof")
    ramp = data.get("ramp")
    if not isinstance(roof, dict) or not isinstance(ramp, dict):
        raise ValueError("Roof and ramp need explicit handedness observations.")
    high = _landmark(roof.get("high_end"), "roof.high_end")
    low = _landmark(roof.get("low_end"), "roof.low_end")
    entry = _landmark(ramp.get("entry"), "ramp.entry")
    exit = _landmark(ramp.get("exit"), "ramp.exit")
    if high["axis"] == low["axis"]:
        raise ValueError("Roof high and low ends cannot occupy the identical model direction.")
    if entry["axis"] == exit["axis"]:
        raise ValueError("Ramp entry and exit cannot occupy the identical model direction.")
    if status == "OWNER_CONFIRMED" and any(
        item["provenance"] in {"estimated", "unresolved"} for item in (high, low, entry, exit)
    ):
        raise ValueError("Cannot falsely certify inferred or unresolved handedness as owner-confirmed.")
    owner_note = data.get("owner_review_note")
    if status == "OWNER_CONFIRMED" and (not isinstance(owner_note, str) or not owner_note.strip()):
        raise ValueError("Owner confirmation requires actual recorded review note.")
    delegation_note = data.get("owner_delegation_note")
    agent_note = data.get("agent_review_note")
    if status == "AGENT_REVIEWED_OWNER_DELEGATED":
        if not all(isinstance(note, str) and note.strip() for note in (delegation_note, agent_note)):
            raise ValueError("Delegated review requires the owner's actual delegation and source-backed agent review.")
        if any(item["provenance"] in {"estimated", "unresolved"} for item in (high, low, entry, exit)):
            raise ValueError("Delegated review cannot certify unresolved spatial landmarks.")
    return {"schema_version": 1, "status": status, "model_axes": directions,
            "source_views": normalized, "roof": {"high_end": high, "low_end": low},
            "ramp": {"entry": entry, "exit": exit},
            "owner_review_note": owner_note.strip() if isinstance(owner_note, str) else "",
            "owner_delegation_note": delegation_note.strip() if isinstance(delegation_note, str) else "",
            "agent_review_note": agent_note.strip() if isinstance(agent_note, str) else ""}


def load_spatial_spec(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000:
        raise ValueError("Spatial probe must be a small real JSON file.")
    return validate_spatial_spec(json.loads(path.read_text(encoding="utf-8")))
