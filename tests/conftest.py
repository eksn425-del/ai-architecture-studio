from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.models import BuildPlan, BuildOperation, DesignIR, DesignObject, EditPlan, PlanValidation, ProjectContext


def sample_context(project_id: str = "demo-cultural-center") -> ProjectContext:
    return ProjectContext(
        project_id=project_id,
        project_name="Tidal Commons",
        brief={"summary": "A public cultural house with three calm volumes."},
        site={"summary": "60 by 48 meter synthetic plot.", "boundary": [[0, 0], [60, 0], [60, 48], [0, 48]]},
        user_intent="Keep a clear public passage and shaded outdoor room.",
    )


def sample_design(project_id: str = "demo-cultural-center") -> DesignIR:
    return DesignIR(
        project_id=project_id,
        concept={"summary": "Three low pavilions frame a shared waterfront passage."},
        site={"boundary": [[0, 0], [60, 0], [60, 48], [0, 48]]},
        objects=[
            DesignObject(id="SITE_BASE_01", type="site_base", name="Site Base", footprint=[[0, 0], [60, 0], [60, 48], [0, 48]], floors=1, floor_height=0.2, height=0.2),
            DesignObject(id="MASS_01", type="building_mass", name="Reading Pavilion", footprint=[[7, 8], [19, 8], [19, 20], [7, 20]], floors=2, floor_height=3.6, height=7.2),
            DesignObject(id="MASS_02", type="building_mass", name="Learning House", footprint=[[24, 8], [36, 8], [36, 18], [24, 18]], floors=1, floor_height=4.2, height=4.2),
            DesignObject(id="MASS_03", type="building_mass", name="Workshop Hall", footprint=[[40, 34], [52, 34], [52, 44], [40, 44]], floors=1, floor_height=4.8, height=4.8),
            DesignObject(id="PUBLIC_STREET_01", type="circulation", name="Public Passage", polyline=[[0, 24], [60, 24]], width=5.0),
        ],
        assumptions=["The massing remains low and rectangular for the first editable model pass."],
    )


def sample_plan(project_id: str = "demo-cultural-center") -> BuildPlan:
    design = sample_design(project_id)
    operations = [
        BuildOperation(op_id=f"OP_{index:03d}", action="create_circulation" if obj.type == "circulation" else "create_mass", target_id=obj.id)
        for index, obj in enumerate(design.objects, 1)
    ]
    operations.extend([
        BuildOperation(op_id="OP_006", action="capture_view"),
        BuildOperation(op_id="OP_007", action="save_model"),
    ])
    return BuildPlan(project_id=project_id, operations=operations, validation=PlanValidation(
        required_ids=[obj.id for obj in design.objects], expected_object_count_min=len(design.objects),
    ))


class FakeBrain:
    available = True

    def __init__(self):
        self.edit_calls = 0
        self.prepare_calls: list[tuple[list[str], dict[str, Any] | None]] = []

    def prepare(self, context: ProjectContext, images: list[Path] | None = None, previous_design: DesignIR | None = None):
        messages = [message.content for message in context.conversation]
        self.prepare_calls.append((messages, previous_design.model_dump(mode="json") if previous_design else None))
        design = previous_design.model_copy(deep=True) if previous_design else sample_design(context.project_id)
        if any("街道" in message and ("宽" in message or "加宽" in message) for message in messages):
            route = next(item for item in design.objects if item.type == "circulation")
            route.width = 7.0 if route.width < 7.0 else 8.0
        return design, sample_plan(context.project_id), "已根据讨论调整公共空间与体块关系。"

    def plan_edit(self, context: ProjectContext, design: DesignIR, model_state: dict[str, Any], instruction: str) -> EditPlan:
        self.edit_calls += 1
        if ("街道" in instruction or "流线" in instruction) and ("宽" in instruction or "加宽" in instruction):
            route = next(item for item in model_state["objects"] if item["object_type"] == "circulation")
            return EditPlan(target_id=route["stable_id"], patch={"route_width": 8.0}, rationale="已将公共流线调整至 8 米宽。")
        if "宽度" in instruction or "宽" in instruction:
            return EditPlan(target_id="MASS_01", patch={"width": 15.0}, rationale="扩大阅览体块的宽度。")
        if "进深" in instruction:
            return EditPlan(target_id="MASS_01", patch={"depth": 14.0}, rationale="调整阅览体块的进深。")
        if self.edit_calls == 1:
            return EditPlan(target_id="MASS_01", patch={"floors": 3, "height": 10.8}, rationale="Add one floor while preserving the footprint.")
        return EditPlan(target_id="MASS_02", patch={"origin": [27, 8, 0]}, rationale="Shift east by three meters.")


class FakeSketchUp:
    def __init__(self, root: Path | None = None):
        self.root = root
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.entity_id = 500

    def ping(self):
        self.calls.append(("ping", {}))
        return {"ok": True}

    def get_model_info(self):
        self.calls.append(("get_model_info", {}))
        return {"entity_count": len([call for call in self.calls if call[0] in {"create_mass", "create_circulation"}]), "units": "meters", "selection_count": 0}

    def create_mass(self, **kwargs):
        self.entity_id += 1
        self.calls.append(("create_mass", kwargs))
        return {"entity_id": self.entity_id, "bounds": {"height": kwargs["height_m"]}}

    def create_circulation(self, **kwargs):
        self.entity_id += 1
        self.calls.append(("create_circulation", kwargs))
        return {"entity_id": self.entity_id, "bounds": {"width": kwargs["width_m"]}}

    def modify_object(self, **kwargs):
        self.calls.append(("modify_object", kwargs))
        return {"entity_id": int(kwargs["connector_ref"]), "modified": True}

    def capture_view(self, output_path: Path, **kwargs):
        self.calls.append(("capture_view", {"path": str(output_path)}))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake png evidence")
        return {"path": str(output_path)}

    def save_model(self, target_path: Path, operation_name: str = "checkpoint"):
        self.calls.append(("save_model", {"path": str(target_path), "operation_name": operation_name}))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(b"fake skp evidence")
        return {"saved": True, "path": str(target_path)}


@pytest.fixture
def fake_components():
    return FakeBrain(), FakeSketchUp()
