from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, conlist, model_validator


Point2 = conlist(float, min_length=2, max_length=2)
Point3 = conlist(float, min_length=3, max_length=3)


class Model(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class Brief(Model):
    source_files: list[str] = Field(default_factory=list)
    summary: str = ""
    requirements: list[str] = Field(default_factory=list)


class Site(Model):
    source_files: list[str] = Field(default_factory=list)
    summary: str = ""
    boundary: list[Point2] = Field(default_factory=list)
    north: float | None = None
    access_points: list[Point2] = Field(default_factory=list)


class Reference(Model):
    type: Literal["url", "image", "note"] = "note"
    source: str = ""
    submitted_at: str = ""
    status: Literal["pending", "readable", "unreadable"] = "pending"
    title: str = ""
    excerpt: str = ""
    fetched_at: str = ""
    error: str = ""
    observed_principles: list[str] = Field(default_factory=list)


class Decision(Model):
    id: str
    statement: str
    source: str = "Codex"


class ConversationMessage(Model):
    role: Literal["user", "assistant"]
    phase: Literal["pre_build", "after_build", "agent"]
    content: str = Field(min_length=1, max_length=12000)
    created_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectContext(Model):
    project_id: str = ""
    project_name: str = "Untitled Architecture Project"
    brief: Brief = Field(default_factory=Brief)
    site: Site = Field(default_factory=Site)
    references: list[Reference] = Field(default_factory=list)
    user_intent: str = ""
    decisions: list[Decision] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    conversation: list[ConversationMessage] = Field(default_factory=list)


class Concept(Model):
    summary: str = ""
    reference_principles_used: list[str] = Field(default_factory=list)
    reference_principles_rejected: list[str] = Field(default_factory=list)


class Program(Model):
    id: str
    name: str
    target_area: float = Field(default=0, ge=0)


class DesignObject(Model):
    id: str = Field(min_length=1, max_length=80)
    type: str
    name: str
    footprint: list[Point2] = Field(default_factory=list)
    polyline: list[Point2] = Field(default_factory=list)
    floors: int = Field(default=1, ge=1, le=100)
    floor_height: float = Field(default=3.6, gt=0, le=30)
    height: float = Field(default=3.6, gt=0, le=500)
    width: float = Field(default=0, ge=0, le=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def geometry_matches_type(self) -> "DesignObject":
        if self.type in {"building_mass", "site_base"} and len(self.footprint) < 3:
            raise ValueError(f"{self.id} needs a footprint with at least three points")
        if self.type == "circulation":
            if len(self.polyline) < 2 or self.width <= 0:
                raise ValueError(f"{self.id} needs a polyline and positive width")
        return self


class DesignSite(Model):
    boundary: list[Point2] = Field(default_factory=list)


class DesignIR(Model):
    version: str = "0.1"
    project_id: str
    concept: Concept = Field(default_factory=Concept)
    site: DesignSite = Field(default_factory=DesignSite)
    program: list[Program] = Field(default_factory=list)
    objects: list[DesignObject] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_object_ids(self) -> "DesignIR":
        ids = [obj.id for obj in self.objects]
        if len(ids) != len(set(ids)):
            raise ValueError("DesignIR object IDs must be unique")
        return self


Action = Literal["create_mass", "create_circulation", "modify_object", "capture_view", "save_model"]


class BuildOperation(Model):
    op_id: str
    action: Action
    target_id: str = ""
    args: dict[str, Any] = Field(default_factory=dict)


class PlanValidation(Model):
    required_ids: list[str] = Field(default_factory=list)
    expected_object_count_min: int = Field(default=0, ge=0)


class BuildPlan(Model):
    version: str = "0.1"
    project_id: str
    operations: list[BuildOperation] = Field(default_factory=list)
    validation: PlanValidation = Field(default_factory=PlanValidation)

    @model_validator(mode="after")
    def unique_operation_ids(self) -> "BuildPlan":
        ids = [operation.op_id for operation in self.operations]
        if len(ids) != len(set(ids)):
            raise ValueError("BuildPlan operation IDs must be unique")
        return self


class ModelObject(Model):
    stable_id: str
    connector_ref: str = ""
    name: str
    bounds: dict[str, Any] | None = None
    height: float | None = None
    floors: int | None = None
    origin: Point3 | None = None
    width: float | None = None
    depth: float | None = None
    object_type: str = "building_mass"
    last_change: dict[str, Any] | None = None


class ModelState(Model):
    project_id: str
    model_path: str | None = None
    objects: list[ModelObject] = Field(default_factory=list)
    last_capture: str | None = None
    last_operation: dict[str, Any] | None = None
    connector_readback: dict[str, Any] | None = None
    status: str = "ready"


class AgentSession(Model):
    project_id: str
    status: Literal["idle", "conversation", "ready", "failed"] = "idle"
    thread_id: str = ""
    model: str = "gpt-6.1-sol"
    reasoning_effort: Literal["low", "medium", "high", "xhigh", "max", "provider-default"] = "low"
    routing_tier: Literal["economy", "premium"] = "economy"
    provider: str = "codex-app-server"
    region: str = "codex-managed (not exposed)"
    workflow_mode: Literal["architecture_design", "image_reconstruction"] = "architecture_design"
    reconstruction_state: Literal["idle", "clarifying", "planned", "building"] = "idle"
    clarification_rounds: int = Field(default=0, ge=0, le=8)
    plan_started_ns: int = 0
    plan_request_message: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int = 0
    tool_call_count: int = 0
    failed_tool_calls: int = 0
    economy_tool_failure_streak: int = 0
    premium_rescue_pending: bool = False
    model_path: str = ""
    model_guid: str = ""
    started_at: str = ""
    updated_at: str = ""
    last_reply: str = ""
    last_tool_calls: list[dict[str, str]] = Field(default_factory=list)
    last_model_info: dict[str, Any] = Field(default_factory=dict)
    ruby_state: dict[str, dict[str, Any]] = Field(default_factory=dict)
    error: str = ""


class QualityBenchmarkRun(Model):
    benchmark_id: str
    variant: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,30}$")
    project_id: str
    model: str
    reasoning_effort: Literal["low", "medium", "high", "xhigh", "max", "provider-default"]
    input_sha256: str
    model_guid: str = ""
    sketchup_version: str = ""
    architecture_skill: bool = False
    ruby_enabled: bool = False
    skill_revision: str = ""
    script_ids: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, str]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    provider: str = ""
    region: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    tool_call_count: int = 0
    failed_tool_calls: int = 0
    inspected: bool = False
    correction_count: int = 0
    same_model_followup: bool = False
    status: Literal["planned", "running", "complete", "partial", "failed"] = "planned"
    notes: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class Artifact(Model):
    id: str
    type: str
    path: str
    url: str = ""
    created_at: str


class OutputManifest(Model):
    project_id: str
    drawing: list[Artifact] = Field(default_factory=list)
    render: list[Artifact] = Field(default_factory=list)
    presentation: list[Artifact] = Field(default_factory=list)
    model_captures: list[Artifact] = Field(default_factory=list)


class PrepareRequest(Model):
    project_name: str = ""
    brief: str = ""
    site_note: str = ""
    reference_url: str = ""
    user_intent: str = ""


class CreateProjectRequest(Model):
    project_name: str
    brief: str = ""
    site_note: str = ""
    user_intent: str = ""


class EditRequest(Model):
    instruction: str = Field(min_length=3, max_length=1200)


class EditPlan(Model):
    target_id: str
    patch: dict[str, Any]
    rationale: str = ""


class ConversationRequest(Model):
    message: str = Field(min_length=1, max_length=1200)
    tier: Literal["economy", "premium"] = "economy"
    workflow_mode: Literal["architecture_design", "image_reconstruction"] = "architecture_design"
    agent_action: Literal["auto", "clarify", "plan", "execute"] = "auto"
    project_name: str = ""
    brief: str = ""
    site_note: str = ""
    reference_url: str = ""
    user_intent: str = ""
