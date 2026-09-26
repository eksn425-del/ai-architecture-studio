from __future__ import annotations

import html
import io
import json
import mimetypes
import re
import shutil
import uuid
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from .brain import BrainUnavailable, CodexBrainAdapter
from .generators import generate_drawing, generate_presentation
from .models import (
    Artifact, BuildPlan, CreateProjectRequest, DesignIR, EditPlan, EditRequest,
    ModelObject, ModelState, OutputManifest, PrepareRequest, ProjectContext,
)
from .sketchup_mcp import ConnectorUnavailable, MCPCallError, SketchUpAdapter, _resolve_server
from .store import ProjectStore, safe_project_id, utc_now


ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
SAFE_FILENAME_RE = re.compile(r"[^\w.() -]+", re.UNICODE)


class JobCompletion(BaseModel):
    design_ir: dict[str, Any]
    build_plan: dict[str, Any]
    decision_summary: str = "Completed by the active Codex session."


def _relative(project_dir: Path, file_path: Path) -> str:
    return file_path.resolve().relative_to(project_dir.resolve()).as_posix()


def _artifact(project_id: str, project_dir: Path, path: Path, artifact_type: str) -> Artifact:
    relative = _relative(project_dir, path)
    return Artifact(
        id=f"{artifact_type}-{uuid.uuid4().hex[:10]}",
        type=artifact_type,
        path=relative,
        url=f"/api/projects/{project_id}/files/{quote(relative, safe='/')}?v={path.stat().st_mtime_ns if path.exists() else uuid.uuid4().hex[:6]}",
        created_at=utc_now(),
    )


def _safe_readback(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"value": value}
    result: dict[str, Any] = {}
    for key, item in value.items():
        normalized = key.lower()
        if "token" in normalized or "secret" in normalized or "auth" in normalized:
            continue
        if "path" in normalized and isinstance(item, str):
            result[key] = PureWindowsPath(item).name or Path(item).name
        elif key in {"entity_count", "units", "selection_count", "bounds", "model_name", "active_entities", "status", "ok", "success"}:
            result[key] = item
    return result


def _validate_plan(design: DesignIR, plan: BuildPlan) -> None:
    if design.project_id != plan.project_id:
        raise ValueError("DesignIR and BuildPlan project_id values must match.")
    geometry = [obj for obj in design.objects if obj.type in {"site_base", "building_mass", "circulation"}]
    if len([obj for obj in geometry if obj.type == "building_mass"]) < 3:
        raise ValueError("DesignIR must contain at least three building masses.")
    if not any(obj.type == "circulation" for obj in geometry):
        raise ValueError("DesignIR must contain at least one circulation object.")
    ids = {obj.id for obj in geometry}
    actions: dict[str, str] = {}
    for operation in plan.operations:
        if operation.action in {"create_mass", "create_circulation"}:
            if operation.target_id not in ids:
                raise ValueError(f"BuildPlan targets unknown object {operation.target_id!r}.")
            if operation.target_id in actions:
                raise ValueError(f"BuildPlan creates {operation.target_id} more than once.")
            actions[operation.target_id] = operation.action
    if ids != set(actions):
        missing = sorted(ids - set(actions))
        raise ValueError(f"BuildPlan is missing create operations for: {', '.join(missing)}.")
    if not ids.issubset(set(plan.validation.required_ids)):
        raise ValueError("BuildPlan validation.required_ids must contain every geometry object ID.")
    if plan.validation.expected_object_count_min != len(geometry):
        raise ValueError("BuildPlan expected_object_count_min must equal the geometry count.")
    boundary = design.site.boundary or next((obj.footprint for obj in geometry if obj.type == "site_base"), [])
    if boundary:
        min_x, max_x = min(p[0] for p in boundary), max(p[0] for p in boundary)
        min_y, max_y = min(p[1] for p in boundary), max(p[1] for p in boundary)
        for obj in geometry:
            for x, y in obj.footprint + obj.polyline:
                if x < min_x - 0.01 or x > max_x + 0.01 or y < min_y - 0.01 or y > max_y + 0.01:
                    raise ValueError(f"{obj.id} extends outside the site boundary.")
    for obj in geometry:
        expected = "create_circulation" if obj.type == "circulation" else "create_mass"
        if actions[obj.id] != expected:
            raise ValueError(f"{obj.id} requires a {expected} operation.")
        if obj.type not in {"site_base", "building_mass"}:
            continue
        xs = {round(point[0], 5) for point in obj.footprint}
        ys = {round(point[1], 5) for point in obj.footprint}
        if len(xs) != 2 or len(ys) != 2:
            raise ValueError(f"{obj.id} must use a rectangular footprint for the v0.1 SketchUp connector.")


def _mcp_image_paths(store: ProjectStore, project_id: str) -> list[Path]:
    return [path for path in store.find_input_files(project_id) if path.suffix.lower() in IMAGE_SUFFIXES][:6]


def _extract_brief_text(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md", ".rst", ".csv"}:
            return path.read_text(encoding="utf-8", errors="replace")[:30000]
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages[:30])[:30000]
        if suffix == ".docx":
            from docx import Document
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())[:30000]
    except Exception:
        return ""
    return ""


def _context_with_brief_files(store: ProjectStore, project_id: str, context: ProjectContext) -> ProjectContext:
    enriched = context.model_copy(deep=True)
    excerpts: list[str] = []
    project_dir = store.project_dir(project_id)
    for relative in context.brief.source_files:
        file_path = (project_dir / Path(relative)).resolve()
        if file_path.is_relative_to(project_dir.resolve()) and file_path.is_file():
            text = _extract_brief_text(file_path).strip()
            if text:
                excerpts.append(f"[{file_path.name}]\n{text}")
    if excerpts:
        enriched.brief.summary = (enriched.brief.summary + "\n\nUploaded brief extracts:\n" + "\n\n".join(excerpts))[:50000]
    return enriched


def _read_site_boundary(path: Path) -> tuple[list[tuple[float, float]], str] | None:
    if path.suffix.lower() != ".dxf":
        return None
    try:
        import ezdxf
        document = ezdxf.readfile(path)
        unit_scale = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 7: 1000.0}.get(document.units, 1.0)
        candidates: list[tuple[float, list[tuple[float, float]]]] = []
        for entity in document.modelspace().query("LWPOLYLINE"):
            if entity.closed:
                points = [(float(point[0]) * unit_scale, float(point[1]) * unit_scale) for point in entity.get_points()]
                if len(points) >= 3:
                    area = abs(sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points))) / 2)
                    candidates.append((area, points))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[0])[1], f"DXF units converted to meters (INSUNITS={document.units})."
    except Exception:
        return None


def _job_prompt(context: ProjectContext) -> str:
    return (
        "Prepare a DesignIR and BuildPlan for this AI Architecture Studio project. "
        "Use the output schema in docs/SCHEMAS_V0_1.md. Include a site_base, three building masses, "
        "a circulation object, stable IDs, and create/capture/save operations. Keep all dimensions in meters.\n\n"
        + json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
    )


def create_app(runtime_root: Path | None = None, brain: CodexBrainAdapter | None = None,
               sketchup: SketchUpAdapter | None = None) -> FastAPI:
    runtime = runtime_root or Path(__import__("os").environ.get("ARCH_STUDIO_RUNTIME_DIR", ROOT / "runtime"))
    store = ProjectStore(runtime)
    app = FastAPI(title="AI Architecture Studio Demo", version="0.1.0")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    app.state.store = store
    app.state.brain = brain or CodexBrainAdapter()
    app.state.sketchup = sketchup or SketchUpAdapter()

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html", media_type="text/html; charset=utf-8")

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        try:
            _resolve_server()
            connector_configured = True
            connector_detail = "Existing kongxing_sketchup MCP configured"
        except ConnectorUnavailable as error:
            connector_configured = False
            connector_detail = str(error)
        return {
            "app": "ready",
            "brain": "Codex CLI" if app.state.brain.available else "Codex Job Mode",
            "codex_available": app.state.brain.available,
            "sketchup_configured": connector_configured,
            "sketchup_detail": connector_detail,
            "runtime": "local",
        }

    @app.get("/api/projects")
    def list_projects() -> list[dict[str, Any]]:
        has_saved_project = store.projects_root.exists() and any(
            directory.is_dir() and (directory / "state" / "project_context.json").exists()
            for directory in store.projects_root.iterdir()
        )
        if not has_saved_project:
            store.ensure_seed_project()
        items: list[dict[str, Any]] = []
        for directory in sorted(store.projects_root.iterdir(), key=lambda item: item.name):
            context_file = directory / "state" / "project_context.json"
            if context_file.exists():
                context = store.load(ProjectContext, context_file)
                model_state = store.load_state(directory.name, "model_state.json", ModelState)
                items.append({"project_id": context.project_id, "project_name": context.project_name, "status": model_state.status})
        return items

    @app.post("/api/projects")
    def create_project(request: CreateProjectRequest) -> dict[str, Any]:
        context = ProjectContext(
            project_name=request.project_name,
            brief={"summary": request.brief},
            site={"summary": request.site_note},
            user_intent=request.user_intent,
        )
        created = store.create_project(context)
        return {"project_id": created.project_id, "project": store.load_project(created.project_id)}

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        try:
            return store.load_project(project_id)
        except (ValueError, FileNotFoundError, ValidationError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/inputs/{category}")
    async def upload_input(project_id: str, category: str, request: Request, filename: str = "upload") -> dict[str, Any]:
        if category not in {"brief", "site", "reference"}:
            raise HTTPException(status_code=400, detail="category must be brief, site, or reference")
        try:
            project_dir = store.ensure_layout(project_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        content = await request.body()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Maximum upload size is 25 MB.")
        raw_name = PureWindowsPath(filename).name
        raw_name = Path(raw_name).name
        safe_name = SAFE_FILENAME_RE.sub("_", raw_name).strip(" .") or "upload"
        destination = project_dir / "inputs" / category / f"{uuid.uuid4().hex[:10]}-{safe_name}"
        destination.write_bytes(content)
        relative = _relative(project_dir, destination)
        context = store.load_context(project_id)
        source_list = getattr(context.brief if category == "brief" else context.site if category == "site" else context, "source_files") if category != "reference" else None
        if category == "reference":
            context.references.append({"type": "image" if destination.suffix.lower() in IMAGE_SUFFIXES else "note", "source": relative})
        else:
            if relative not in source_list:
                source_list.append(relative)
            if category == "site":
                boundary = _read_site_boundary(destination)
                if boundary:
                    context.site.boundary, units_note = boundary
                    context.site.summary = (context.site.summary + " " + units_note).strip()
        store.save(context, project_dir / "state" / "project_context.json")
        return {"path": relative, "filename": safe_name, "category": category, "bytes": len(content)}

    @app.post("/api/projects/{project_id}/prepare")
    def prepare_project(project_id: str, request: PrepareRequest) -> dict[str, Any]:
        try:
            context = store.load_context(project_id)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        if request.project_name.strip():
            context.project_name = request.project_name.strip()[:120]
        if request.brief.strip():
            context.brief.summary = request.brief.strip()[:30000]
        if request.site_note.strip():
            context.site.summary = request.site_note.strip()[:8000]
        if request.reference_url.strip():
            context.references = [ref for ref in context.references if not (ref.type == "url" and ref.source)]
            context.references.append({"type": "url", "source": request.reference_url.strip()[:1200]})
        context.user_intent = request.user_intent.strip()[:8000]
        store.save(context, store.project_dir(project_id) / "state" / "project_context.json")
        brain_context = _context_with_brief_files(store, project_id, context)
        job_id, job_dir = store.create_job(project_id, {"project_context": brain_context.model_dump(mode="json")})
        (job_dir / "request.md").write_text(_job_prompt(brain_context), encoding="utf-8")
        try:
            design, plan, summary = app.state.brain.prepare(brain_context, _mcp_image_paths(store, project_id))
            _validate_plan(design, plan)
        except BrainUnavailable as error:
            job = store.set_job(job_id, status="awaiting_codex", mode="Codex Job Mode", detail=str(error))
            return {"job": job, "status": "awaiting_codex", "detail": str(error), "request_url": f"/api/jobs/{job_id}"}
        except (ValidationError, ValueError) as error:
            store.set_job(job_id, status="failed", detail=str(error))
            raise HTTPException(status_code=422, detail=f"Codex output failed deterministic validation: {error}") from error
        store.save_state(project_id, design, "design_ir.json")
        store.save_state(project_id, plan, "build_plan.json")
        context.decisions = [
            {"id": f"DECISION_{index + 1:02d}", "statement": statement, "source": "Codex"}
            for index, statement in enumerate([summary, *design.assumptions]) if statement
        ]
        store.save(context, store.project_dir(project_id) / "state" / "project_context.json")
        project_dir = store.project_dir(project_id)
        drawing_dxf, drawing_svg = generate_drawing(project_dir, design)
        generate_presentation(project_dir, context, design, drawing_svg, None)
        manifest = store.load_state(project_id, "output_manifest.json", OutputManifest)
        manifest.drawing = [_artifact(project_id, project_dir, drawing_dxf, "dxf"), _artifact(project_id, project_dir, drawing_svg, "drawing-preview")]
        board = project_dir / "outputs" / "presentation" / "presentation.html"
        manifest.presentation = [_artifact(project_id, project_dir, board, "presentation")]
        store.save_state(project_id, manifest, "output_manifest.json")
        job = store.set_job(job_id, status="complete", mode="Codex CLI", completed_at=utc_now(), decision_summary=summary)
        return {"job": job, "status": "complete", "decision_summary": summary, "project": store.load_project(project_id)}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        try:
            path = store.jobs_root / job_id / "job.json"
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise HTTPException(status_code=404, detail="Job not found") from error

    @app.post("/api/jobs/{job_id}/complete")
    def complete_job(job_id: str, completion: JobCompletion) -> dict[str, Any]:
        try:
            job = store.set_job(job_id, status="validating")
            project_id = safe_project_id(str(job["project_id"]))
            design = DesignIR.model_validate(completion.design_ir)
            plan = BuildPlan.model_validate(completion.build_plan)
            _validate_plan(design, plan)
        except (OSError, ValueError, ValidationError, KeyError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if design.project_id != project_id:
            raise HTTPException(status_code=422, detail="Job result project_id does not match the job.")
        store.save_state(project_id, design, "design_ir.json")
        store.save_state(project_id, plan, "build_plan.json")
        project_dir = store.project_dir(project_id)
        context = store.load_context(project_id)
        drawing_dxf, drawing_svg = generate_drawing(project_dir, design)
        generate_presentation(project_dir, context, design, drawing_svg, None)
        manifest = store.load_state(project_id, "output_manifest.json", OutputManifest)
        manifest.drawing = [_artifact(project_id, project_dir, drawing_dxf, "dxf"), _artifact(project_id, project_dir, drawing_svg, "drawing-preview")]
        board = project_dir / "outputs" / "presentation" / "presentation.html"
        manifest.presentation = [_artifact(project_id, project_dir, board, "presentation")]
        store.save_state(project_id, manifest, "output_manifest.json")
        job = store.set_job(job_id, status="complete", mode="Codex Job Mode", completed_at=utc_now(), decision_summary=completion.decision_summary)
        return {"job": job, "project": store.load_project(project_id)}

    @app.get("/api/projects/{project_id}/connector")
    def connector_status(project_id: str) -> dict[str, Any]:
        try:
            project_dir = store.ensure_layout(project_id)
            health = app.state.sketchup.ping()
            model_info = app.state.sketchup.get_model_info()
            return {"configured": True, "reachable": True, "health": _safe_readback(health), "model": _safe_readback(model_info)}
        except (ConnectorUnavailable, MCPCallError) as error:
            return {"configured": True, "reachable": False, "detail": str(error)}

    @app.post("/api/projects/{project_id}/build")
    def build_in_sketchup(project_id: str, request: dict[str, Any]) -> dict[str, Any]:
        if not request.get("confirm_disposable_model"):
            raise HTTPException(status_code=400, detail="Confirm that the active SketchUp document is blank or disposable before building.")
        try:
            data = store.load_project(project_id)
            design: DesignIR | None = data["design_ir"]  # type: ignore[assignment]
            plan: BuildPlan | None = data["build_plan"]  # type: ignore[assignment]
            if design is None or plan is None:
                raise HTTPException(status_code=409, detail="Prepare Design before building in SketchUp.")
            _validate_plan(design, plan)
            model_state: ModelState = data["model_state"]  # type: ignore[assignment]
            if model_state.objects and model_state.status == "built":
                raise HTTPException(status_code=409, detail="This project already has a live SketchUp model. Use a new project to build another model.")
            adapter: SketchUpAdapter = app.state.sketchup
            adapter.ping()
            model_info = adapter.get_model_info()
            active_model_name = str(model_info.get("model_name", "")).strip().lower() if isinstance(model_info, dict) else ""
            if active_model_name and not (active_model_name.startswith("blank-disposable") or active_model_name in {"untitled", "untitled0"}):
                raise HTTPException(status_code=409, detail=f"Active SketchUp model '{active_model_name}' is not the disposable demo model. Open blank-disposable.skp first.")
            prior_model_name = str((model_state.connector_readback or {}).get("model_name", "")).strip().lower()
            if model_state.objects and prior_model_name and active_model_name != prior_model_name:
                raise HTTPException(status_code=409, detail=f"The partial build belongs to SketchUp model '{prior_model_name}'. Reopen that same disposable model to resume safely.")
            model_state.status = "building"
            store.save_state(project_id, model_state, "model_state.json")
            objects_by_id = {obj.id: obj for obj in design.objects}
            site_top_z = max((obj.height for obj in design.objects if obj.type == "site_base"), default=0.0)
            completed_ids: list[str] = []
            existing_ids = {obj.stable_id for obj in model_state.objects}
            for operation in plan.operations:
                if operation.action not in {"create_mass", "create_circulation"}:
                    continue
                if operation.target_id in existing_ids:
                    completed_ids.append(operation.target_id)
                    continue
                obj = objects_by_id[operation.target_id]
                if obj.type in {"site_base", "building_mass"}:
                    min_x, max_x = min(p[0] for p in obj.footprint), max(p[0] for p in obj.footprint)
                    min_y, max_y = min(p[1] for p in obj.footprint), max(p[1] for p in obj.footprint)
                    result = adapter.create_mass(
                        stable_id=obj.id,
                        name=obj.name,
                        origin_m=[min_x, min_y, 0],
                        width_m=max_x - min_x,
                        depth_m=max_y - min_y,
                        height_m=obj.height,
                        color=str(obj.metadata.get("color", "#D9D9D9")),
                    )
                    connector_ref = result.get("entity_id", result.get("id", ""))
                    model_state.objects.append(ModelObject(
                        stable_id=obj.id, connector_ref=str(connector_ref), name=obj.name,
                        bounds=result.get("bounds") if isinstance(result.get("bounds"), dict) else None,
                        height=obj.height, floors=obj.floors, origin=[min_x, min_y, 0],
                        width=max_x - min_x, depth=max_y - min_y, object_type=obj.type,
                    ))
                else:
                    first, last = obj.polyline[0], obj.polyline[-1]
                    result = adapter.create_circulation(
                        stable_id=obj.id, name=obj.name,
                        start_m=[first[0], first[1], site_top_z], end_m=[last[0], last[1], site_top_z], width_m=obj.width,
                    )
                    connector_ref = result.get("entity_id", result.get("id", ""))
                    model_state.objects.append(ModelObject(
                        stable_id=obj.id, connector_ref=str(connector_ref), name=obj.name,
                        bounds=result.get("bounds") if isinstance(result.get("bounds"), dict) else None,
                        origin=[first[0], first[1], site_top_z], width=obj.width, object_type="circulation",
                    ))
                completed_ids.append(obj.id)
                existing_ids.add(obj.id)
                model_state.last_operation = {"op_id": operation.op_id, "action": operation.action, "target_id": obj.id, "result": _safe_readback(result)}
                store.save_state(project_id, model_state, "model_state.json")
            readback = adapter.get_model_info()
            model_state.connector_readback = _safe_readback(readback)
            model_state.last_operation = {"action": "build", "completed_ids": completed_ids, "readback": model_state.connector_readback}
            model_state.status = "built"
            project_dir = store.project_dir(project_id)
            model_path = project_dir / "outputs" / "model" / f"{project_id}.skp"
            save_result = adapter.save_model(model_path, "AI Architecture Studio initial build")
            model_state.model_path = _relative(project_dir, model_path)
            capture_path = project_dir / "outputs" / "renders" / "model-initial.png"
            connector_capture = ROOT / "artifacts" / project_id / "model-initial.png"
            connector_capture.parent.mkdir(parents=True, exist_ok=True)
            capture_result = adapter.capture_view(connector_capture)
            if connector_capture.exists():
                shutil.copy2(connector_capture, capture_path)
            capture_exists = capture_path.exists()
            if capture_exists:
                model_state.last_capture = _relative(project_dir, capture_path)
            store.save_state(project_id, model_state, "model_state.json")
            manifest = store.load_state(project_id, "output_manifest.json", OutputManifest)
            if capture_exists:
                image_artifact = _artifact(project_id, project_dir, capture_path, "viewport")
                manifest.render = [image_artifact]
                manifest.model_captures.append(image_artifact)
            if model_path.exists():
                manifest.model_captures.append(_artifact(project_id, project_dir, model_path, "skp"))
            drawing_svg = project_dir / "outputs" / "drawings" / "site-plan.svg"
            board_path = generate_presentation(project_dir, data["context"], design, drawing_svg, capture_path if capture_exists else None)  # type: ignore[arg-type]
            manifest.presentation = [_artifact(project_id, project_dir, board_path, "presentation")]
            store.save_state(project_id, manifest, "output_manifest.json")
            return {
                "status": model_state.status,
                "completed_ids": completed_ids,
                "model_state": model_state,
                "save_result": _safe_readback(save_result),
                "capture_result": _safe_readback(capture_result),
                "project": store.load_project(project_id),
            }
        except HTTPException:
            raise
        except (ConnectorUnavailable, MCPCallError, ValueError) as error:
            try:
                model_state.status = "partial" if model_state.objects else "unavailable"
                store.save_state(project_id, model_state, "model_state.json")
            except Exception:
                pass
            raise HTTPException(status_code=502, detail=str(error)) from error

    @app.post("/api/projects/{project_id}/edit")
    def edit_model(project_id: str, request: EditRequest) -> dict[str, Any]:
        data = store.load_project(project_id)
        design: DesignIR | None = data["design_ir"]  # type: ignore[assignment]
        model_state: ModelState = data["model_state"]  # type: ignore[assignment]
        context: ProjectContext = data["context"]  # type: ignore[assignment]
        if design is None or not model_state.objects:
            raise HTTPException(status_code=409, detail="Build a SketchUp model before editing it.")
        try:
            edit_plan: EditPlan = app.state.brain.plan_edit(context, design, model_state.model_dump(mode="json"), request.instruction)
            target = next((obj for obj in model_state.objects if obj.stable_id == edit_plan.target_id), None)
            if target is None:
                raise ValueError("Codex edit plan targets an object not present in ModelState.")
            keys = set(edit_plan.patch)
            if keys not in ({"height"}, {"floors", "height"}, {"origin"}):
                raise ValueError("EditPlan must change height, floors+height, or origin only.")
            translate: list[float] | None = None
            scale: list[float] | None = None
            previous = target.model_copy(deep=True)
            if "height" in edit_plan.patch:
                next_height = float(edit_plan.patch["height"])
                if next_height <= 0 or not target.height:
                    raise ValueError("EditPlan height must be positive and the current object height must be known.")
                scale = [1, 1, next_height / target.height]
                target.height = next_height
            if "floors" in edit_plan.patch:
                next_floors = int(edit_plan.patch["floors"])
                if next_floors < 1 or target.stable_id not in {item.id for item in design.objects if item.type == "building_mass"}:
                    raise ValueError("EditPlan floors must target a building mass and be positive.")
                target.floors = next_floors
                design_obj = next(item for item in design.objects if item.id == target.stable_id)
                if abs((target.height or 0) - next_floors * design_obj.floor_height) > 0.05:
                    raise ValueError("EditPlan height must equal floors × floor_height.")
            if "origin" in edit_plan.patch:
                next_origin = [float(value) for value in edit_plan.patch["origin"]]
                if len(next_origin) != 3 or target.origin is None:
                    raise ValueError("EditPlan origin must be a three-number point and the current origin must be known.")
                translate = [next_origin[index] - target.origin[index] for index in range(3)]
                design_obj = next((item for item in design.objects if item.id == target.stable_id), None)
                if design_obj is None:
                    raise ValueError("The edited stable ID is missing from DesignIR.")
                design_obj.footprint = [[point[0] + translate[0], point[1] + translate[1]] for point in design_obj.footprint]
                design_obj.polyline = [[point[0] + translate[0], point[1] + translate[1]] for point in design_obj.polyline]
                boundary = design.site.boundary
                if boundary:
                    min_x, max_x = min(point[0] for point in boundary), max(point[0] for point in boundary)
                    min_y, max_y = min(point[1] for point in boundary), max(point[1] for point in boundary)
                    for x, y in design_obj.footprint + design_obj.polyline:
                        if x < min_x - 0.01 or x > max_x + 0.01 or y < min_y - 0.01 or y > max_y + 0.01:
                            raise ValueError("The edited object would extend outside the project site boundary.")
                target.origin = next_origin
            adapter: SketchUpAdapter = app.state.sketchup
            result = adapter.modify_object(connector_ref=target.connector_ref, translate_m=translate, scale=scale)
            readback = adapter.get_model_info()
            model_state.connector_readback = _safe_readback(readback)
            target.last_change = {"instruction": request.instruction, "patch": edit_plan.patch, "rationale": edit_plan.rationale, "result": _safe_readback(result)}
            model_state.last_operation = {"action": "modify_object", "stable_id": target.stable_id, "instruction": request.instruction, "readback": model_state.connector_readback}
            model_state.status = "edited"
            project_dir = store.project_dir(project_id)
            capture_path = project_dir / "outputs" / "renders" / f"edit-{uuid.uuid4().hex[:8]}.png"
            connector_capture = ROOT / "artifacts" / project_id / capture_path.name
            connector_capture.parent.mkdir(parents=True, exist_ok=True)
            adapter.capture_view(connector_capture)
            if connector_capture.exists():
                shutil.copy2(connector_capture, capture_path)
            model_state.last_capture = _relative(project_dir, capture_path) if capture_path.exists() else model_state.last_capture
            model_path = project_dir / "outputs" / "model" / f"{project_id}.skp"
            save_result = adapter.save_model(model_path, "AI Architecture Studio edit checkpoint")
            model_state.model_path = _relative(project_dir, model_path)
            store.save_state(project_id, model_state, "model_state.json")
            store.save_state(project_id, design, "design_ir.json")
            manifest = store.load_state(project_id, "output_manifest.json", OutputManifest)
            if capture_path.exists():
                artifact = _artifact(project_id, project_dir, capture_path, "viewport")
                manifest.render.append(artifact)
                manifest.model_captures.append(artifact)
            if model_path.exists():
                manifest.model_captures.append(_artifact(project_id, project_dir, model_path, "skp"))
            drawing_svg = project_dir / "outputs" / "drawings" / "site-plan.svg"
            generate_drawing(project_dir, design)
            board = generate_presentation(project_dir, context, design, drawing_svg, capture_path if capture_path.exists() else None)
            manifest.drawing = [
                _artifact(project_id, project_dir, project_dir / "outputs/drawings/site-plan.dxf", "dxf"),
                _artifact(project_id, project_dir, drawing_svg, "drawing-preview"),
            ]
            manifest.presentation = [_artifact(project_id, project_dir, board, "presentation")]
            store.save_state(project_id, manifest, "output_manifest.json")
            log_path = project_dir / "logs" / "model-edits.jsonl"
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"at": utc_now(), "target_id": target.stable_id, "instruction": request.instruction, "patch": edit_plan.patch, "previous": previous.model_dump(mode="json")}, ensure_ascii=False) + "\n")
            return {"edit_plan": edit_plan, "model_state": model_state, "save_result": _safe_readback(save_result), "project": store.load_project(project_id)}
        except (BrainUnavailable, ConnectorUnavailable, MCPCallError, ValueError, ValidationError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    @app.get("/api/projects/{project_id}/files/{asset_path:path}")
    def project_file(project_id: str, asset_path: str) -> FileResponse:
        try:
            project_dir = store.project_dir(project_id)
            target = (project_dir / Path(asset_path)).resolve()
        except ValueError as error:
            raise HTTPException(status_code=404, detail="Project file not found") from error
        if not target.is_relative_to(project_dir.resolve()) or not target.is_file():
            raise HTTPException(status_code=404, detail="Project file not found")
        media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        return FileResponse(target, media_type=media_type, filename=target.name if media_type == "application/octet-stream" else None)

    return app


app = create_app()
