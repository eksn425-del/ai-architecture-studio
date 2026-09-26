from __future__ import annotations

import json
from pathlib import Path

import ezdxf
from fastapi.testclient import TestClient

from app.brain import BrainUnavailable, CodexBrainAdapter
from app.generators import generate_drawing, generate_presentation
from app.main import _validate_plan, create_app
from app.models import BuildPlan, DesignIR, ModelState, OutputManifest
from app.sketchup_mcp import SketchUpAdapter
from app.store import ProjectStore
from tests.conftest import FakeBrain, FakeSketchUp, sample_context, sample_design, sample_plan


def test_schema_validation_and_plan_preflight():
    design = sample_design()
    plan = sample_plan()
    _validate_plan(design, plan)
    duplicate = design.model_dump(mode="json")
    duplicate["objects"].append(duplicate["objects"][1])
    try:
        DesignIR.model_validate(duplicate)
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate stable IDs should be rejected")


def test_codex_build_plan_is_compiled_from_design_ids():
    design = sample_design()
    plan = sample_plan().model_dump(mode="json")
    plan["operations"][0]["target_id"] = "HALLUCINATED_ID"
    plan["validation"]["required_ids"] = ["HALLUCINATED_ID"]
    plan["validation"]["expected_object_count_min"] = 99
    brain = CodexBrainAdapter(codex_executable="codex")
    brain._run = lambda *_args, **_kwargs: {  # type: ignore[method-assign]
        "design_ir": design.model_dump(mode="json"),
        "build_plan": plan,
        "decision_summary": "Three pavilions and a public passage.",
    }

    _, compiled, _ = brain.prepare(sample_context())

    geometry = [obj for obj in design.objects if obj.type in {"site_base", "building_mass", "circulation"}]
    geometry_operations = [op for op in compiled.operations if op.action in {"create_mass", "create_circulation"}]
    assert [op.target_id for op in geometry_operations] == [obj.id for obj in geometry]
    assert [op.action for op in geometry_operations] == [
        "create_circulation" if obj.type == "circulation" else "create_mass" for obj in geometry
    ]
    assert compiled.validation.required_ids == [obj.id for obj in geometry]
    assert compiled.validation.expected_object_count_min == len(geometry)
    assert [op.action for op in compiled.operations[-2:]] == ["capture_view", "save_model"]


def test_project_create_load_and_seed(tmp_path: Path):
    store = ProjectStore(tmp_path / "runtime")
    context = store.ensure_seed_project()
    assert context.project_id == "demo-cultural-center"
    loaded = store.load_project(context.project_id)
    assert loaded["context"].project_name == context.project_name
    assert loaded["model_state"].status == "ready"
    created = store.create_project(sample_context(""))
    assert created.project_id == "tidal-commons"
    assert store.load_project(created.project_id)["context"].project_id == created.project_id


def test_uploaded_brief_is_stored_in_project_context(tmp_path: Path):
    app = create_app(tmp_path / "runtime", brain=FakeBrain(), sketchup=FakeSketchUp())
    client = TestClient(app)
    client.get("/api/projects")
    upload = client.post(
        "/api/projects/demo-cultural-center/inputs/brief",
        params={"filename": "brief.txt"},
        content=b"Keep a clear route through the site.",
    )
    assert upload.status_code == 200
    path = upload.json()["path"]
    project = client.get("/api/projects/demo-cultural-center").json()
    assert path in project["context"]["brief"]["source_files"]
    assert (tmp_path / "runtime/projects/demo-cultural-center" / path).read_text(encoding="utf-8") == "Keep a clear route through the site."


def test_dxf_and_presentation_generation(tmp_path: Path):
    context = sample_context()
    design = sample_design()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    dxf_path, svg_path = generate_drawing(project_dir, design)
    document = ezdxf.readfile(dxf_path)
    modelspace = document.modelspace()
    assert len(modelspace.query("LWPOLYLINE")) >= 5
    assert {layer.dxf.name for layer in document.layers} >= {"SITE", "MASS", "CIRCULATION", "LABELS"}
    assert "PUBLIC PASSAGE" in svg_path.read_text(encoding="utf-8").upper()
    board = generate_presentation(project_dir, context, design, svg_path, None)
    text = board.read_text(encoding="utf-8")
    assert "A3 landscape" in text
    assert "Reading Pavilion" in text
    assert "data:image/png;base64" not in text


def test_sketchup_adapter_wraps_existing_tools():
    class RecordingClient:
        def __init__(self):
            self.calls = []

        def call(self, name, args=None):
            self.calls.append((name, args or {}))
            return {"entity_id": 712}

    client = RecordingClient()
    adapter = SketchUpAdapter(client)
    result = adapter.create_mass(stable_id="MASS_01", name="Reading Pavilion", origin_m=[1, 2, 0], width_m=12, depth_m=8, height_m=7.2)
    assert result["entity_id"] == 712
    assert client.calls[0][0] == "sketchup_create_mass"
    assert client.calls[0][1]["name"] == "[MASS_01] Reading Pavilion"
    adapter.modify_object(connector_ref="712", translate_m=[3, 0, 0])
    assert client.calls[1][0] == "sketchup_transform_group"
    assert client.calls[1][1]["entity_id"] == 712


def test_sketchup_adapter_saves_a_copy_without_changing_active_model_path(tmp_path: Path, monkeypatch):
    generated_scripts = tmp_path / "generated_scripts"
    monkeypatch.setenv("ARCHFLOW_GENERATED_SCRIPT_DIR", str(generated_scripts))

    class SaveRecordingClient:
        script = ""

        def call(self, name, args=None):
            assert name == "sketchup_eval_project_file"
            self.script = Path(args["script_path"]).read_text(encoding="utf-8")
            return {"saved": True}

    client = SaveRecordingClient()
    target = tmp_path / "outputs" / "demo.skp"
    SketchUpAdapter(client).save_model(target)
    assert "model.save_copy(" in client.script
    assert "model.save_as(" not in client.script


def test_brain_job_lifecycle_and_project_prepare(tmp_path: Path):
    class OfflineBrain(FakeBrain):
        def prepare(self, context, images=None):
            raise BrainUnavailable("Codex CLI is not available.")

    app = create_app(tmp_path / "runtime", brain=OfflineBrain(), sketchup=FakeSketchUp())
    client = TestClient(app)
    client.get("/api/projects")
    response = client.post("/api/projects/demo-cultural-center/prepare", json={"user_intent": "Keep the route open."})
    assert response.status_code == 200
    job_id = response.json()["job"]["job_id"]
    assert response.json()["status"] == "awaiting_codex"
    completion = client.post(f"/api/jobs/{job_id}/complete", json={
        "design_ir": sample_design().model_dump(mode="json"),
        "build_plan": sample_plan().model_dump(mode="json"),
        "decision_summary": "Three pavilions with a public route.",
    })
    assert completion.status_code == 200
    saved = client.get("/api/projects/demo-cultural-center")
    assert saved.json()["design_ir"]["objects"][0]["id"] == "SITE_BASE_01"
    assert Path(tmp_path / "runtime/jobs" / job_id / "job.json").exists()


def test_build_and_two_edits_use_the_same_model(tmp_path: Path):
    brain, sketchup = FakeBrain(), FakeSketchUp()
    app = create_app(tmp_path / "runtime", brain=brain, sketchup=sketchup)
    client = TestClient(app)
    client.get("/api/projects")
    prepared = client.post("/api/projects/demo-cultural-center/prepare", json={})
    assert prepared.status_code == 200
    built = client.post("/api/projects/demo-cultural-center/build", json={"confirm_disposable_model": True})
    assert built.status_code == 200
    assert len(built.json()["model_state"]["objects"]) == 5
    first = client.post("/api/projects/demo-cultural-center/edit", json={"instruction": "Raise the reading pavilion by one floor."})
    second = client.post("/api/projects/demo-cultural-center/edit", json={"instruction": "Move the learning house three meters east."})
    assert first.status_code == second.status_code == 200
    calls = [call for call in sketchup.calls if call[0] == "modify_object"]
    assert len(calls) == 2
    assert calls[0][1]["connector_ref"] != calls[1][1]["connector_ref"]
    final_project = client.get("/api/projects/demo-cultural-center").json()
    model = final_project["model_state"]
    assert model["status"] == "edited"
    assert len([item for item in model["objects"] if item.get("last_change")]) == 2
    route = next(item for item in model["objects"] if item["stable_id"] == "PUBLIC_STREET_01")
    assert route["origin"][2] == 0.2
    road_call = next(call for call in sketchup.calls if call[0] == "create_circulation")
    assert road_call[1]["start_m"][2] == road_call[1]["end_m"][2] == 0.2
    shifted_workshop = next(item for item in final_project["design_ir"]["objects"] if item["id"] == "MASS_02")
    assert shifted_workshop["footprint"] == [[27, 8], [39, 8], [39, 18], [27, 18]]
    assert len(final_project["output_manifest"]["render"]) == 3
    assert final_project["output_manifest"]["drawing"]
    assert final_project["output_manifest"]["presentation"]
    assert any(call[0] == "get_model_info" for call in sketchup.calls)


def test_partial_build_can_resume_without_duplicate_geometry(tmp_path: Path):
    class SaveFailsOnceSketchUp(FakeSketchUp):
        save_attempts = 0

        def save_model(self, target_path: Path, operation_name: str = "checkpoint"):
            self.save_attempts += 1
            if self.save_attempts == 1:
                raise ValueError("Simulated first-save failure.")
            return super().save_model(target_path, operation_name)

    sketchup = SaveFailsOnceSketchUp()
    app = create_app(tmp_path / "runtime", brain=FakeBrain(), sketchup=sketchup)
    client = TestClient(app)
    client.get("/api/projects")
    assert client.post("/api/projects/demo-cultural-center/prepare", json={}).status_code == 200
    first = client.post("/api/projects/demo-cultural-center/build", json={"confirm_disposable_model": True})
    assert first.status_code == 502
    partial = client.get("/api/projects/demo-cultural-center").json()["model_state"]
    assert partial["status"] == "partial"
    assert len(partial["objects"]) == 5

    resumed = client.post("/api/projects/demo-cultural-center/build", json={"confirm_disposable_model": True})
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "built"
    create_calls = [call for call in sketchup.calls if call[0] in {"create_mass", "create_circulation"}]
    assert len(create_calls) == 5
    assert sketchup.save_attempts == 2
