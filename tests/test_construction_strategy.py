import json

import pytest

from app.construction_strategy import (
    CONSTRUCTION_STAGE_ORDER,
    default_construction_strategy,
    strategy_has_signal,
    validate_construction_strategy_payload,
)


def test_default_construction_strategy_is_empty_and_valid():
    value = validate_construction_strategy_payload(default_construction_strategy())
    assert value["stage_order"] == list(CONSTRUCTION_STAGE_ORDER)
    assert value["current_stage"] == "pending"
    assert value["systems"] == []
    assert strategy_has_signal(value) is False


def test_strategy_supports_shared_parameter_driven_staged_systems():
    value = validate_construction_strategy_payload({
        "schema_version": 1,
        "current_stage": "representative_module",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": {
            "floor_height": {
                "value": 3200,
                "units": "mm",
                "provenance": "user_confirmed",
                "source": "user",
            },
            "front_bays": {
                "value": 3,
                "units": "count",
                "provenance": "observed",
                "source": "front panel",
            },
        },
        "systems": [
            {
                "id": "front-wall-system",
                "stage": "primary_form",
                "role": "opening_system",
                "method": "continuous_wall_with_openings",
                "status": "built",
                "depends_on": ["floor_height", "front_bays"],
                "target_paths": [["SHELL", "FRONT_WALL"]],
                "verification_views": ["front", "oblique"],
                "notes": ["one continuous host, real openings"],
            },
            {
                "id": "window-module",
                "stage": "representative_module",
                "role": "repetition",
                "method": "prototype_instance",
                "status": "pending",
                "depends_on": ["floor_height"],
                "target_paths": [["FACADE", "WINDOW_MODULE"]],
                "verification_views": ["front", "left"],
                "notes": [],
            },
        ],
        "notes": ["verify representative module before replication"],
    })
    assert strategy_has_signal(value) is True
    assert value["systems"][0]["method"] == "continuous_wall_with_openings"
    assert value["systems"][1]["stage"] == "representative_module"


def test_strategy_rejects_unknown_dependency_and_bad_method():
    base = {
        "schema_version": 1,
        "current_stage": "primary_form",
        "stage_order": list(CONSTRUCTION_STAGE_ORDER),
        "shared_parameters": {},
        "systems": [{
            "id": "roof",
            "stage": "primary_form",
            "role": "roof",
            "method": "loft_or_mesh",
            "status": "pending",
            "depends_on": ["missing"],
            "target_paths": [],
            "verification_views": ["roof"],
            "notes": [],
        }],
        "notes": [],
    }
    with pytest.raises(ValueError, match="unknown parameters"):
        validate_construction_strategy_payload(base)

    base["systems"][0]["depends_on"] = []
    base["systems"][0]["method"] = "magic"
    with pytest.raises(ValueError, match="invalid method"):
        validate_construction_strategy_payload(base)


def test_strategy_rejects_arbitrary_stage_order_or_view():
    value = default_construction_strategy()
    value["stage_order"] = ["finish"]
    with pytest.raises(ValueError, match="five-stage"):
        validate_construction_strategy_payload(value)

    value = default_construction_strategy()
    value["systems"] = [{
        "id": "facade",
        "stage": "primary_form",
        "role": "shell",
        "method": "custom_owned_ruby",
        "status": "pending",
        "depends_on": [],
        "target_paths": [],
        "verification_views": ["pretty"],
        "notes": [],
    }]
    with pytest.raises(ValueError, match="invalid verification views"):
        validate_construction_strategy_payload(value)
