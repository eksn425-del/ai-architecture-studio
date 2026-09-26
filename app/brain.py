from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from .models import BuildOperation, BuildPlan, DesignIR, EditPlan, ProjectContext


class BrainUnavailable(RuntimeError):
    pass


def _schema_for(*models: type[BaseModel], root: dict[str, Any]) -> dict[str, Any]:
    definitions: dict[str, Any] = {}
    for model in models:
        schema = model.model_json_schema(ref_template="#/$defs/{model}")
        definitions.update(schema.pop("$defs", {}))
        definitions[model.__name__] = schema
    return _strict_response_schema({"$schema": "https://json-schema.org/draft/2020-12/schema", **root, "$defs": definitions})


def _strict_response_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Close objects and require every declared property for Codex structured output."""
    def visit(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if not isinstance(value, dict):
            return
        value.pop("default", None)
        value.pop("title", None)
        properties = value.get("properties")
        if value.get("type") == "object":
            if isinstance(properties, dict):
                for child in properties.values():
                    visit(child)
                value["required"] = list(properties)
            else:
                # The demo's free-form metadata dictionaries are deliberately empty.
                value["properties"] = {}
                value["required"] = []
            value["additionalProperties"] = False
        for key, child in list(value.items()):
            if key not in {"properties"}:
                visit(child)

    visit(schema)
    return schema


class CodexBrainAdapter:
    """Uses the local Codex CLI as the demo brain; provider APIs stay outside the product."""

    def __init__(self, timeout_seconds: int = 240, codex_executable: str | None = None):
        self.timeout_seconds = timeout_seconds
        self.codex_executable = codex_executable or os.environ.get("CODEX_CLI_PATH") or shutil.which("codex")
        self.repo_root = Path(__file__).resolve().parents[1]

    @property
    def available(self) -> bool:
        return bool(self.codex_executable)

    def _run(self, prompt: str, schema: dict[str, Any], images: list[Path] | None = None) -> dict[str, Any]:
        if not self.codex_executable:
            raise BrainUnavailable("Codex CLI is not available. The job package is ready for Codex Job Mode.")
        schema_path = self.repo_root / "runtime" / "brain-schema" / f"{uuid.uuid4().hex}.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        command = [self.codex_executable, "--ask-for-approval", "never"]
        for image in images or []:
            command.extend(["--image", str(image.resolve())])
        command.extend([
            "exec", "--ignore-user-config", "--ephemeral", "--json", "--sandbox", "read-only",
            "--output-schema", str(schema_path), "-C", str(self.repo_root), "-",
        ])
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=self.timeout_seconds,
                cwd=self.repo_root,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise BrainUnavailable(f"Codex did not finish within {self.timeout_seconds} seconds; the job remains available in Job Mode.") from error
        finally:
            schema_path.unlink(missing_ok=True)
        final_text = ""
        for line in completed.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item", {})
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                final_text = str(item.get("text", ""))
        if completed.returncode != 0 or not final_text:
            detail = completed.stderr.strip()[-1600:] or completed.stdout.strip()[-1600:]
            raise BrainUnavailable(detail or "Codex CLI returned no structured result; the job remains available in Job Mode.")
        try:
            result = json.loads(final_text)
        except json.JSONDecodeError as error:
            raise BrainUnavailable("Codex returned invalid JSON; the job remains available in Job Mode.") from error
        if not isinstance(result, dict):
            raise BrainUnavailable("Codex returned a non-object result; the job remains available in Job Mode.")
        return result

    def prepare(self, context: ProjectContext, images: list[Path] | None = None) -> tuple[DesignIR, BuildPlan, str]:
        schema = _schema_for(
            DesignIR,
            BuildPlan,
            root={
                "type": "object",
                "properties": {
                    "design_ir": {"$ref": "#/$defs/DesignIR"},
                    "build_plan": {"$ref": "#/$defs/BuildPlan"},
                    "decision_summary": {"type": "string"},
                },
                "required": ["design_ir", "build_plan", "decision_summary"],
                "additionalProperties": False,
            },
        )
        prompt = f"""You are the temporary Codex brain for AI Architecture Studio Demo v0.1.
Turn the project context below into a compact, editable SketchUp massing plan.

Hard requirements:
- Return only the schema-shaped JSON object.
- Use meters, ground plane XY, height Z. Use axis-aligned rectangular footprints.
- Include a site/base object, at least three building_mass objects, and at least one circulation object.
- Give every object a unique stable ID and a short, human-readable name.
- The site and masses must fit in the stated boundary. Keep all geometry within it.
- Give building masses positive floors, floor_height, and height = floors * floor_height.
- BuildPlan must contain one create_mass for each site_base/building_mass, one create_circulation for each circulation, then capture_view and save_model.
- BuildPlan validation.required_ids must list every geometry object ID; expected_object_count_min must match the geometry object count.
- Keep the geometry schematic and plausible. Record inferred choices in assumptions; do not claim you inspected references unless their content was provided.
- project_id must exactly equal the project context ID.

Project context:
{json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)}
"""
        last_error = ""
        for attempt in range(2):
            result = self._run(prompt, schema, images)
            try:
                design = DesignIR.model_validate(result["design_ir"])
                plan = BuildPlan.model_validate(result["build_plan"])
                if design.project_id != context.project_id or plan.project_id != context.project_id:
                    raise ValueError("DesignIR and BuildPlan project_id must match the requested project_id.")
                geometry = [obj for obj in design.objects if obj.type in {"site_base", "building_mass", "circulation"}]
                geometry_ids = {obj.id for obj in geometry}
                if len([obj for obj in geometry if obj.type == "building_mass"]) < 3:
                    raise ValueError("DesignIR must contain at least three named building masses.")
                if not any(obj.type == "circulation" for obj in geometry):
                    raise ValueError("DesignIR must contain at least one circulation object.")
                # Compile geometry operations against the validated IR. This keeps the
                # model output editable while preventing a hallucinated target ID from
                # ever reaching the local SketchUp connector.
                plan.operations = [
                    BuildOperation(
                        op_id=f"create-{index:02d}-{obj.id}",
                        action="create_circulation" if obj.type == "circulation" else "create_mass",
                        target_id=obj.id,
                    )
                    for index, obj in enumerate(geometry, start=1)
                ] + [
                    BuildOperation(op_id="capture-view", action="capture_view"),
                    BuildOperation(op_id="save-model", action="save_model"),
                ]
                plan.validation.required_ids = [obj.id for obj in geometry]
                plan.validation.expected_object_count_min = len(geometry)
                return design, plan, str(result["decision_summary"])
            except (KeyError, TypeError, ValueError, ValidationError) as error:
                last_error = str(error)
            if attempt == 0:
                prompt += (
                    "\n\nYour previous result failed deterministic validation: " + last_error +
                    " Regenerate the complete DesignIR and BuildPlan. Keep the DesignIR geometry IDs authoritative; "
                    "every create operation must target one of those IDs exactly once, with no extra create targets. "
                    "Set expected_object_count_min to the exact number of geometry objects."
                )
        raise BrainUnavailable(f"Codex output did not pass deterministic validation after one correction attempt: {last_error}")

    def plan_edit(self, context: ProjectContext, design: DesignIR, model_state: dict[str, Any], instruction: str) -> EditPlan:
        schema = _schema_for(
            EditPlan,
            root={
                "type": "object",
                "properties": {"edit_plan": {"$ref": "#/$defs/EditPlan"}},
                "required": ["edit_plan"],
                "additionalProperties": False,
            },
        )
        schema["$defs"]["EditPlan"]["properties"]["patch"] = {
            "type": "object",
            "properties": {
                "height": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                "floors": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "origin": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                        {"type": "null"},
                    ]
                },
            },
            "required": ["height", "floors", "origin"],
            "additionalProperties": False,
        }
        schema = _strict_response_schema(schema)
        prompt = f"""Create one minimal edit for an existing SketchUp model. Do not rebuild or replace any geometry.
Return only JSON matching the schema. Target an existing stable_id.
Allowed patch fields are exactly one of: height (meters), floors (integer), or origin ([x,y,z] meters).
When changing floors, also provide the matching height. Preserve the target object's footprint and stable ID.

Instruction: {instruction}
Project context: {json.dumps(context.model_dump(mode="json"), ensure_ascii=False)}
DesignIR: {json.dumps(design.model_dump(mode="json"), ensure_ascii=False)}
Current ModelState: {json.dumps(model_state, ensure_ascii=False)}
"""
        result = self._run(prompt, schema)
        edit = result["edit_plan"]
        edit["patch"] = {key: value for key, value in edit.get("patch", {}).items() if value is not None}
        return EditPlan.model_validate(edit)
