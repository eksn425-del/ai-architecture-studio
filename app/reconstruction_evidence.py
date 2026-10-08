"""Structured evidence contract for image-to-SketchUp reconstruction.

The shape follows two proven ideas used by comparable open-source agent systems:
- SketchUp Agent Harness separates source-backed constraints from project-local inference.
- Realsee/Astra-style reconstruction keeps an explicit source inventory and stable
  observed/inferred boundaries before geometry generation.

K Studio uses this file only as project memory and quality-policy input. It does
not replace SketchUp geometry as execution truth.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


FIDELITY_MODES = {
    "pending",
    "single_view_inference",
    "multi_view_reconstruction",
    "full_evidence_reconstruction",
}
EVIDENCE_PROVENANCE = {"pending", "observed", "user_confirmed", "inferred"}
EXTERIOR_VIEWS = ("front", "rear", "left", "right", "roof", "oblique")
SOURCE_KINDS = {
    "exterior_image",
    "interior_image",
    "floorplan_image",
    "cad",
    "document",
    "dimension_note",
}


def default_reconstruction_evidence() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "fidelity_mode": "pending",
        "primary_source": "",
        "sources": [],
        "exterior_views": {
            name: {
                "provenance": "pending",
                "source_refs": [],
                "notes": [],
            }
            for name in EXTERIOR_VIEWS
        },
        "floorplan": {
            "provided": False,
            "provenance": "pending",
            "source_refs": [],
            "levels": [],
            "notes": [],
        },
        "cad": {
            "provided": False,
            "provenance": "pending",
            "source_refs": [],
            "notes": [],
        },
        "interior": {
            "provided": False,
            "provenance": "pending",
            "source_refs": [],
            "spaces": [],
            "notes": [],
        },
        "scale_anchors": [],
        "hard_constraints": [],
        "assumptions": [],
        "inference_policy": {
            "unseen_exterior": "infer_coherent",
            "unseen_interior": "infer_plausible",
            "preserve_circulation": True,
        },
    }


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a string list.")
    for item in value:
        if ".." in item.replace("\\", "/").split("/"):
            raise ValueError(f"{field} may not contain traversal paths.")
    return value


def _validate_source_ref(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty project source path.")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/"):
        raise ValueError(f"{field} must stay inside the project.")
    return normalized


def _validate_provenance(value: Any, field: str) -> str:
    if value not in EVIDENCE_PROVENANCE:
        raise ValueError(f"{field} provenance is invalid.")
    return str(value)


def validate_reconstruction_evidence_payload(value: Any) -> dict[str, Any]:
    """Validate evidence coverage and the fidelity mode selected by the planner."""
    if not isinstance(value, dict):
        raise ValueError("reconstruction evidence root must be an object.")
    if value.get("schema_version") != 1:
        raise ValueError("reconstruction evidence schema_version must be 1.")

    mode = value.get("fidelity_mode", "pending")
    if mode not in FIDELITY_MODES:
        raise ValueError("reconstruction evidence fidelity_mode is invalid.")

    primary = value.get("primary_source", "")
    if primary:
        _validate_source_ref(primary, "primary_source")

    sources = value.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("reconstruction evidence sources must be a list.")
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ValueError(f"sources[{index}] must be an object.")
        _validate_source_ref(item.get("path"), f"sources[{index}].path")
        if item.get("kind") not in SOURCE_KINDS:
            raise ValueError(f"sources[{index}].kind is invalid.")
        _validate_provenance(item.get("provenance", "pending"), f"sources[{index}]")
        if "role" in item and not isinstance(item["role"], str):
            raise ValueError(f"sources[{index}].role must be a string.")

    exterior = value.get("exterior_views", {})
    if not isinstance(exterior, dict):
        raise ValueError("reconstruction evidence exterior_views must be an object.")
    observed_count = 0
    for view_name in EXTERIOR_VIEWS:
        item = exterior.get(view_name, {})
        if not isinstance(item, dict):
            raise ValueError(f"exterior_views.{view_name} must be an object.")
        provenance = _validate_provenance(
            item.get("provenance", "pending"), f"exterior_views.{view_name}"
        )
        refs = _string_list(item.get("source_refs", []), f"exterior_views.{view_name}.source_refs")
        _string_list(item.get("notes", []), f"exterior_views.{view_name}.notes")
        if provenance in {"observed", "user_confirmed"}:
            observed_count += 1
            if not refs:
                raise ValueError(
                    f"exterior_views.{view_name} marked {provenance} requires source_refs."
                )

    for field in ("floorplan", "cad", "interior"):
        item = value.get(field, {})
        if not isinstance(item, dict):
            raise ValueError(f"reconstruction evidence {field} must be an object.")
        provided = item.get("provided", False)
        if not isinstance(provided, bool):
            raise ValueError(f"reconstruction evidence {field}.provided must be boolean.")
        provenance = _validate_provenance(item.get("provenance", "pending"), field)
        refs = _string_list(item.get("source_refs", []), f"{field}.source_refs")
        _string_list(item.get("notes", []), f"{field}.notes")
        if provided and provenance not in {"observed", "user_confirmed"}:
            raise ValueError(f"{field}.provided requires observed or user_confirmed provenance.")
        if provided and not refs:
            raise ValueError(f"{field}.provided requires source_refs.")
        if field == "floorplan":
            _string_list(item.get("levels", []), "floorplan.levels")
        if field == "interior":
            spaces = item.get("spaces", [])
            if not isinstance(spaces, list) or any(not isinstance(space, str) for space in spaces):
                raise ValueError("interior.spaces must be a string list.")

    anchors = value.get("scale_anchors", [])
    if not isinstance(anchors, list):
        raise ValueError("scale_anchors must be a list.")
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            raise ValueError(f"scale_anchors[{index}] must be an object.")
        if not isinstance(anchor.get("name"), str) or not anchor["name"].strip():
            raise ValueError(f"scale_anchors[{index}].name is required.")
        number = anchor.get("value_mm")
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)) or number <= 0:
            raise ValueError(f"scale_anchors[{index}].value_mm must be a positive finite number.")
        _validate_provenance(anchor.get("provenance", "pending"), f"scale_anchors[{index}]")
        if anchor.get("source_ref"):
            _validate_source_ref(anchor["source_ref"], f"scale_anchors[{index}].source_ref")

    _string_list(value.get("hard_constraints", []), "hard_constraints")
    _string_list(value.get("assumptions", []), "assumptions")

    policy = value.get("inference_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("inference_policy must be an object.")
    if policy.get("unseen_exterior", "infer_coherent") not in {"infer_coherent", "do_not_infer"}:
        raise ValueError("inference_policy.unseen_exterior is invalid.")
    if policy.get("unseen_interior", "infer_plausible") not in {"infer_plausible", "do_not_infer"}:
        raise ValueError("inference_policy.unseen_interior is invalid.")
    if not isinstance(policy.get("preserve_circulation", True), bool):
        raise ValueError("inference_policy.preserve_circulation must be boolean.")

    if mode == "single_view_inference" and observed_count < 1:
        raise ValueError("single_view_inference requires at least one observed exterior view.")
    if mode == "multi_view_reconstruction" and observed_count < 2:
        raise ValueError("multi_view_reconstruction requires at least two observed exterior views.")
    if mode == "full_evidence_reconstruction":
        missing_views = [
            name for name in ("front", "rear", "left", "right", "roof")
            if exterior.get(name, {}).get("provenance") not in {"observed", "user_confirmed"}
        ]
        if missing_views:
            raise ValueError(
                "full_evidence_reconstruction requires observed/confirmed front, rear, left, right and roof views; "
                f"missing: {', '.join(missing_views)}."
            )
        for field in ("floorplan", "cad", "interior"):
            if not value.get(field, {}).get("provided"):
                raise ValueError(
                    f"full_evidence_reconstruction requires {field}.provided=true."
                )
        if policy.get("unseen_exterior") != "infer_coherent":
            raise ValueError("full evidence may still infer only genuinely unseen exterior gaps.")
        if policy.get("unseen_interior") != "infer_plausible":
            raise ValueError("full evidence may still infer only genuinely unseen interior gaps.")

    return value



def validate_reconstruction_evidence_sources(
    project_dir: Path,
    value: dict[str, Any],
) -> dict[str, Any]:
    """Require every claimed evidence reference to resolve to a real project input file."""
    value = validate_reconstruction_evidence_payload(value)
    project_root = project_dir.resolve()
    inputs_root = (project_root / "inputs").resolve()
    refs: set[str] = set()

    if value.get("primary_source"):
        refs.add(str(value["primary_source"]))
    for item in value.get("sources", []):
        refs.add(str(item["path"]))
    for item in value.get("exterior_views", {}).values():
        refs.update(str(ref) for ref in item.get("source_refs", []))
    for field in ("floorplan", "cad", "interior"):
        refs.update(str(ref) for ref in value.get(field, {}).get("source_refs", []))
    for anchor in value.get("scale_anchors", []):
        if anchor.get("source_ref"):
            refs.add(str(anchor["source_ref"]))

    for ref in refs:
        pure = ref.replace("\\", "/")
        candidate = (project_root / pure).resolve()
        if not candidate.is_relative_to(inputs_root) or not candidate.is_file() or candidate.is_symlink():
            raise ValueError(f"reconstruction evidence source does not exist in project inputs: {ref}")
    return value

def load_reconstruction_evidence(project_dir: Path) -> dict[str, Any] | None:
    path = (
        project_dir.resolve()
        / "runtime"
        / "agent_workspace"
        / "notes"
        / "reconstruction_evidence.json"
    )
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return validate_reconstruction_evidence_sources(project_dir, value)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def fidelity_contract_summary(value: dict[str, Any] | None) -> str:
    mode = (value or {}).get("fidelity_mode", "pending")
    if mode == "single_view_inference":
        return (
            "SINGLE_VIEW_INFERENCE: the supplied visible facade/view is a hard visual target for silhouette, "
            "proportions, openings, colors/material zones, glass, railings and visible interior/detail. "
            "Unseen sides/roof/interior may be plausibly inferred, but inferred geometry must remain coherent and labeled as inference."
        )
    if mode == "multi_view_reconstruction":
        return (
            "MULTI_VIEW_RECONSTRUCTION: every supplied exterior view is a hard visual constraint on one coherent building. "
            "Do not trade fidelity on one observed facade to improve another; infer only regions absent from all sources."
        )
    if mode == "full_evidence_reconstruction":
        return (
            "FULL_EVIDENCE_RECONSTRUCTION: supplied exterior views, CAD/floor plans, dimensions and interior images are hard constraints. "
            "CAD/floor-plan dimensions govern geometry where perspective images are ambiguous; images govern visible appearance/material/detail. "
            "Do not redesign any evidenced region. A visual PASS requires consistency across all evidenced exterior and interior regions; "
            "only genuinely unobserved gaps may be inferred."
        )
    return (
        "PENDING_FIDELITY: classify the source package before claiming reconstruction acceptance."
    )
