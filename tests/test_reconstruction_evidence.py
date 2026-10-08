import json

import pytest

from app.reconstruction_evidence import (
    default_reconstruction_evidence,
    fidelity_contract_summary,
    validate_reconstruction_evidence_payload,
)


def _single():
    value = default_reconstruction_evidence()
    value["fidelity_mode"] = "single_view_inference"
    value["primary_source"] = "inputs/reference/front-oblique.png"
    value["sources"] = [{
        "path": "inputs/reference/front-oblique.png",
        "kind": "exterior_image",
        "provenance": "observed",
        "role": "primary",
    }]
    value["exterior_views"]["oblique"] = {
        "provenance": "observed",
        "source_refs": ["inputs/reference/front-oblique.png"],
        "notes": ["primary visible target"],
    }
    return value


def test_single_view_contract_allows_inference_but_requires_observed_source():
    value = validate_reconstruction_evidence_payload(_single())
    assert value["fidelity_mode"] == "single_view_inference"
    assert "hard visual target" in fidelity_contract_summary(value)

    broken = default_reconstruction_evidence()
    broken["fidelity_mode"] = "single_view_inference"
    with pytest.raises(ValueError, match="at least one observed"):
        validate_reconstruction_evidence_payload(broken)


def test_multi_view_requires_two_observed_views():
    value = _single()
    value["fidelity_mode"] = "multi_view_reconstruction"
    value["exterior_views"]["rear"] = {
        "provenance": "observed",
        "source_refs": ["inputs/reference/rear.png"],
        "notes": [],
    }
    validate_reconstruction_evidence_payload(value)

    value["exterior_views"]["rear"]["provenance"] = "inferred"
    value["exterior_views"]["rear"]["source_refs"] = []
    with pytest.raises(ValueError, match="at least two observed"):
        validate_reconstruction_evidence_payload(value)


def test_full_evidence_requires_all_exterior_cad_floorplan_and_interior():
    value = default_reconstruction_evidence()
    value["fidelity_mode"] = "full_evidence_reconstruction"
    for view in ("front", "rear", "left", "right", "roof"):
        ref = f"inputs/reference/{view}.png"
        value["exterior_views"][view] = {
            "provenance": "observed",
            "source_refs": [ref],
            "notes": [],
        }
        value["sources"].append({
            "path": ref,
            "kind": "exterior_image",
            "provenance": "observed",
            "role": view,
        })
    value["floorplan"] = {
        "provided": True,
        "provenance": "observed",
        "source_refs": ["inputs/reference/floor-1.png"],
        "levels": ["L1"],
        "notes": [],
    }
    value["cad"] = {
        "provided": True,
        "provenance": "observed",
        "source_refs": ["inputs/reference/model.dxf"],
        "notes": [],
    }
    value["interior"] = {
        "provided": True,
        "provenance": "observed",
        "source_refs": ["inputs/reference/living-room.png"],
        "spaces": ["living room"],
        "notes": [],
    }
    validated = validate_reconstruction_evidence_payload(value)
    assert validated["fidelity_mode"] == "full_evidence_reconstruction"
    assert "hard constraints" in fidelity_contract_summary(validated)

    broken = json.loads(json.dumps(value))
    broken["cad"]["provided"] = False
    with pytest.raises(ValueError, match="cad.provided=true"):
        validate_reconstruction_evidence_payload(broken)


def test_observed_view_requires_source_reference():
    value = _single()
    value["exterior_views"]["oblique"]["source_refs"] = []
    with pytest.raises(ValueError, match="requires source_refs"):
        validate_reconstruction_evidence_payload(value)
