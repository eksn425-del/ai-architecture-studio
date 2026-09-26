from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .models import BuildPlan, DesignIR, ModelState, OutputManifest, ProjectContext


T = TypeVar("T", bound=BaseModel)
PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,55}$")
STATE_FILES: dict[str, type[BaseModel]] = {
    "project_context.json": ProjectContext,
    "design_ir.json": DesignIR,
    "build_plan.json": BuildPlan,
    "model_state.json": ModelState,
    "output_manifest.json": OutputManifest,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_project_id(value: str) -> str:
    if not PROJECT_ID_RE.fullmatch(value):
        raise ValueError("project_id must contain lowercase letters, numbers, and hyphens")
    return value


class ProjectStore:
    def __init__(self, root: Path, examples_root: Path | None = None):
        self.root = root.resolve()
        self.projects_root = self.root / "projects"
        self.jobs_root = self.root / "jobs"
        self.examples_root = examples_root or Path(__file__).resolve().parents[1] / "examples" / "demo_project"

    def project_dir(self, project_id: str) -> Path:
        project_id = safe_project_id(project_id)
        return self.projects_root / project_id

    def ensure_layout(self, project_id: str) -> Path:
        directory = self.project_dir(project_id)
        for relative in (
            "inputs/brief",
            "inputs/site",
            "inputs/reference",
            "state",
            "outputs/model",
            "outputs/drawings",
            "outputs/renders",
            "outputs/presentation",
            "logs",
        ):
            (directory / relative).mkdir(parents=True, exist_ok=True)
        return directory

    def ensure_seed_project(self) -> ProjectContext:
        project_id = "demo-cultural-center"
        directory = self.ensure_layout(project_id)
        context_path = directory / "state" / "project_context.json"
        if context_path.exists():
            return self.load(ProjectContext, context_path)
        seed_path = self.examples_root / "project_context.json"
        context = ProjectContext.model_validate_json(seed_path.read_text(encoding="utf-8"))
        context.project_id = project_id
        self.save(context, context_path)
        self.save(ModelState(project_id=project_id), directory / "state" / "model_state.json")
        self.save(OutputManifest(project_id=project_id), directory / "state" / "output_manifest.json")
        return context

    def create_project(self, context: ProjectContext) -> ProjectContext:
        requested_id = context.project_id or ""
        base_id = safe_project_id(requested_id) if requested_id else self.slug(context.project_name)
        project_id = base_id
        while self.project_dir(project_id).exists():
            project_id = f"{base_id}-{uuid.uuid4().hex[:5]}"
        context.project_id = project_id
        directory = self.ensure_layout(project_id)
        self.save(context, directory / "state" / "project_context.json")
        self.save(ModelState(project_id=project_id), directory / "state" / "model_state.json")
        self.save(OutputManifest(project_id=project_id), directory / "state" / "output_manifest.json")
        return context

    @staticmethod
    def slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return (slug[:48] or "architecture-project")

    @staticmethod
    def save(model: BaseModel, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)

    @staticmethod
    def load(model_type: type[T], path: Path) -> T:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def load_state(self, project_id: str, filename: str, model_type: type[T]) -> T:
        if filename not in STATE_FILES:
            raise ValueError("Unknown state file")
        path = self.ensure_layout(project_id) / "state" / filename
        if path.exists():
            return self.load(model_type, path)
        if model_type is ModelState:
            value = ModelState(project_id=project_id)
        elif model_type is OutputManifest:
            value = OutputManifest(project_id=project_id)
        else:
            raise FileNotFoundError(path)
        self.save(value, path)
        return value

    def save_state(self, project_id: str, model: BaseModel, filename: str) -> None:
        if filename not in STATE_FILES:
            raise ValueError("Unknown state file")
        self.save(model, self.ensure_layout(project_id) / "state" / filename)

    def load_context(self, project_id: str) -> ProjectContext:
        context = self.load_state(project_id, "project_context.json", ProjectContext)
        if not context.project_id:
            context.project_id = project_id
        return context

    def load_project(self, project_id: str) -> dict[str, object]:
        self.ensure_layout(project_id)
        return {
            "context": self.load_context(project_id),
            "design_ir": self.load_state(project_id, "design_ir.json", DesignIR) if (self.project_dir(project_id) / "state/design_ir.json").exists() else None,
            "build_plan": self.load_state(project_id, "build_plan.json", BuildPlan) if (self.project_dir(project_id) / "state/build_plan.json").exists() else None,
            "model_state": self.load_state(project_id, "model_state.json", ModelState),
            "output_manifest": self.load_state(project_id, "output_manifest.json", OutputManifest),
        }

    def create_job(self, project_id: str, request: dict[str, object]) -> tuple[str, Path]:
        safe_project_id(project_id)
        job_id = uuid.uuid4().hex
        directory = self.jobs_root / job_id
        directory.mkdir(parents=True, exist_ok=False)
        payload = {
            "job_id": job_id,
            "project_id": project_id,
            "status": "running",
            "created_at": utc_now(),
            "request": request,
        }
        (directory / "job.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return job_id, directory

    def set_job(self, job_id: str, **updates: object) -> dict[str, object]:
        if not re.fullmatch(r"[a-f0-9]{32}", job_id):
            raise ValueError("Invalid job_id")
        path = self.jobs_root / job_id / "job.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.update(updates)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def find_input_files(self, project_id: str) -> list[Path]:
        return [p for p in self.project_dir(project_id).joinpath("inputs").rglob("*") if p.is_file()]
