from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from PIL import Image

from .codex_parity import prepare_codex_parity_workspace
from .oss_backends import discover_oss_backends
from .project_ruby import ProjectRubyExecutor
from .repair_memory import finalize_latest_repair_attempt, record_repair_attempt
from .modeling_quality import (
    owned_inspection_fingerprint,
    submit_visual_review,
    verify_preserved_owned_paths,
)
from .sketchup_mcp import ConfiguredSketchUpMCP, ConnectorUnavailable, MCPCallError
from .workspace_ruby import run_workspace_ruby
from .workspace_files import workspace_file_tools, workspace_file_call


ToolProfile = Literal["full", "reconstruction_coding"]

_CANONICAL_REVIEW_VIEWS = ("front", "rear", "left", "right", "roof", "oblique")


def canonical_camera_from_bounds_mm(bounds_mm: dict[str, Any], view_name: str) -> dict[str, list[float]]:
    """Return a deterministic camera around one owned reconstruction root.

    The reconstruction coordinate convention is X=east, Y=north, Z=up, so
    front looks from -Y, rear from +Y, left from -X and right from +X.
    """
    if view_name not in _CANONICAL_REVIEW_VIEWS:
        raise ValueError("view_name must be front, rear, left, right, roof or oblique.")
    low = bounds_mm.get("min") if isinstance(bounds_mm, dict) else None
    high = bounds_mm.get("max") if isinstance(bounds_mm, dict) else None
    if (
        not isinstance(low, list) or not isinstance(high, list)
        or len(low) != 3 or len(high) != 3
    ):
        raise ValueError("Canonical review capture requires owned-root min/max bounds in millimeters.")
    try:
        lo = [float(value) / 1000.0 for value in low]
        hi = [float(value) / 1000.0 for value in high]
    except (TypeError, ValueError) as error:
        raise ValueError("Canonical review bounds must contain numeric millimeter coordinates.") from error
    if any(not (-1_000_000.0 < value < 1_000_000.0) for value in (*lo, *hi)):
        raise ValueError("Canonical review bounds are outside the supported coordinate range.")
    if any(hi[index] < lo[index] for index in range(3)):
        raise ValueError("Canonical review bounds min/max are inverted.")

    center = [(lo[index] + hi[index]) / 2.0 for index in range(3)]
    spans = [max(hi[index] - lo[index], 0.001) for index in range(3)]
    distance = max(max(spans) * 2.4, 6.0)
    target = [center[0], center[1], lo[2] + spans[2] * 0.52]

    if view_name == "front":
        eye, up = [center[0], lo[1] - distance, target[2]], [0.0, 0.0, 1.0]
    elif view_name == "rear":
        eye, up = [center[0], hi[1] + distance, target[2]], [0.0, 0.0, 1.0]
    elif view_name == "left":
        eye, up = [lo[0] - distance, center[1], target[2]], [0.0, 0.0, 1.0]
    elif view_name == "right":
        eye, up = [hi[0] + distance, center[1], target[2]], [0.0, 0.0, 1.0]
    elif view_name == "roof":
        eye, target, up = [center[0], center[1], hi[2] + distance], center, [0.0, 1.0, 0.0]
    else:
        eye, up = [
            hi[0] + distance * 0.78,
            lo[1] - distance * 0.78,
            hi[2] + distance * 0.48,
        ], [0.0, 0.0, 1.0]
    return {"eye_m": eye, "target_m": target, "up_m": up}


_RECONSTRUCTION_KONGXING_KEYWORDS = (
    "health", "context", "inspect", "select", "view", "camera",
)
# Reconstruction uses a single verified writer: persistent ProjectRuby.
# Optional backends remain read-only evidence helpers in this profile so they
# cannot bypass the same write budget, owned-root identity or verification.
_RECONSTRUCTION_SAIE_TOOLS = {
    "scene_summary",
    "inspect_entity",
    "verify_model",
    "view_snapshot",
    "capture_canonical",
    "deep_scan",
    "export_model_json",
}


@dataclass
class AgentToolContext:
    """The shared project-scoped SketchUp tool surface used by every model provider."""

    dynamic_tools: list[dict[str, Any]]
    dispatch: Callable[[str, dict[str, Any]], dict[str, Any]]
    quality_state: dict[str, Any] = field(default_factory=dict)


class AgentToolSurface:
    """Compose the existing SketchUp bridge with reusable OSS execution engines.

    ``full`` preserves the broad architecture tool surface.
    ``reconstruction_coding`` intentionally keeps a much smaller Direct-Codex-like
    surface: persistent Ruby is primary, the connector handles view/readback/lifecycle,
    and selected SAIE semantic tools remain available as helpers. This prevents a cheap
    model from spending its context choosing among dozens of overlapping operations.
    """

    def __init__(self, runtime_root: Path, sketchup_mcp: ConfiguredSketchUpMCP,
                 oss_backends: dict[str, Any] | None = None):
        self.runtime_root = runtime_root.resolve()
        self.sketchup_mcp = sketchup_mcp
        self.oss_backends = discover_oss_backends() if oss_backends is None else dict(oss_backends)

    def prepare(self, *, project_dir: Path, mcp_enabled: bool, model_path: Path | None,
                model_guid: str, ruby_enabled: bool,
                ruby_state: dict[str, dict[str, Any]] | None,
                tool_profile: ToolProfile = "full", workspace_tools_enabled: bool = False) -> AgentToolContext:
        resolved_project_dir = project_dir.resolve()
        prepare_codex_parity_workspace(resolved_project_dir / "runtime" / "agent_workspace")

        executor = None
        if mcp_enabled and ruby_enabled:
            if model_path is None or not model_guid:
                raise ValueError("The guarded project Ruby tool requires a verified disposable model path and GUID.")
            executor = ProjectRubyExecutor(
                self.runtime_root, project_dir.name, expected_model_path=model_path,
                expected_model_guid=model_guid, mcp=self.sketchup_mcp, ruby_state=ruby_state,
            )
        dynamic_tools = self.dynamic_tools(
            ruby_enabled=executor is not None,
            tool_profile=tool_profile,
        ) if mcp_enabled else []
        if workspace_tools_enabled:
            dynamic_tools.extend(workspace_file_tools())
        writes = 0
        # One primary build plus two corrections; an existing model gets two
        # corrections. A committed write consumes budget even if capture fails.
        write_limit = 2 if executor and executor.ruby_state else 3
        quality_state: dict[str, Any] = {
            "writes": 0,
            "write_limit": write_limit,
            "review": None,
            "preservation": None,
            "repair_memory": None,
        }

        def preserve_snapshot(script_id: str, paths: Any) -> dict[str, dict[str, Any]]:
            if executor is None:
                raise MCPCallError("KEEP preservation requires a verified project writer.")
            if not isinstance(paths, list) or not paths or len(paths) > 24:
                raise MCPCallError("preserve_paths must contain 1..24 exact owned-group paths.")
            snapshots: dict[str, dict[str, Any]] = {}
            for index, path in enumerate(paths):
                if (
                    not isinstance(path, list) or not 1 <= len(path) <= 8
                    or any(not isinstance(segment, str) or not segment or len(segment) > 200 for segment in path)
                ):
                    raise MCPCallError(
                        f"preserve_paths[{index}] must contain 1..8 exact nonempty owned-group name segments."
                    )
                key = "/".join(path)
                if key in snapshots:
                    raise MCPCallError(f"Duplicate preserve path: {key}")
                result = executor.inspect_owned({
                    "script_id": script_id,
                    "path": path,
                    "offset": 0,
                    "limit": 1,
                })
                try:
                    payload = json.loads(result["contentItems"][0]["text"])
                    snapshots[key] = owned_inspection_fingerprint(payload)
                except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as error:
                    raise MCPCallError(f"Could not fingerprint protected KEEP path {key!r}: {error}") from error
            return snapshots

        def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            nonlocal writes
            if workspace_tools_enabled and name in {"workspace_read", "workspace_write"}:
                return workspace_file_call(resolved_project_dir / "runtime" / "agent_workspace", name, arguments)
            if name == "sketchup_submit_visual_review":
                if executor is None:
                    raise MCPCallError("Visual review requires a verified disposable model and committed writer state.")
                receipt = submit_visual_review(resolved_project_dir, executor.ruby_state, arguments)
                finalized_repair = finalize_latest_repair_attempt(resolved_project_dir, receipt)
                quality_state["review"] = receipt
                quality_state["repair_memory"] = finalized_repair
                payload = {"visual_review": receipt}
                if finalized_repair is not None:
                    payload["repair_memory"] = finalized_repair
                return {
                    "success": True,
                    "visual_review": receipt,
                    "repair_memory": finalized_repair,
                    "contentItems": [{
                        "type": "inputText",
                        "text": json.dumps(payload, ensure_ascii=False),
                    }],
                }

            bounded = executor is not None and tool_profile == "reconstruction_coding" and name in {
                "sketchup_run_workspace_ruby", "sketchup_run_project_ruby"}
            before = {key: state.get("revision", 0) for key, state in executor.ruby_state.items()} if bounded else {}
            if bounded and writes >= write_limit:
                raise MCPCallError("本轮建模写入预算已用完（首建一次、定向修正最多两次）。停止写几何；继续只读回读/当前六视图QA并报告未解决问题，不要换script_id或重建来绕过限制。")
            preservation_before: dict[str, dict[str, Any]] = {}
            preservation_script_id = ""
            review_before_write: dict[str, Any] | None = None
            if bounded and writes > 0:
                review = quality_state.get("review")
                if not isinstance(review, dict):
                    raise MCPCallError(
                        "上一次已提交几何后还没有完成当前六视图视觉审查。先取得 front/rear/left/right/roof/oblique "
                        "六张当前修订截图并调用 sketchup_submit_visual_review；不要盲目连续重写模型。"
                    )
                review_before_write = review
                if review.get("needs_fix") is False:
                    raise MCPCallError(
                        "当前六视图审查为 NEEDS_FIX: NO，本轮不再接受额外几何写入。"
                        "如用户提出新修改，请在下一回合按新要求执行。"
                    )
                if str(arguments.get("update_mode") or "replace") != "edit" or arguments.get("allow_full_rebuild") is True:
                    raise MCPCallError(
                        "视觉审查后的修正必须使用 update_mode=edit；本轮禁止整根 replace/full rebuild。"
                        "请只修改 critic 指出的命名对象，保留 KEEP 几何。"
                    )
                preservation_script_id = str(arguments.get("script_id") or "")
                preserve_paths = arguments.get("preserve_paths")
                if review.get("keep") and not preserve_paths:
                    raise MCPCallError(
                        "当前视觉审查包含 KEEP 项。执行修正前请先用 sketchup_inspect_owned 将 KEEP 映射为 exact named paths，"
                        "并在本次 writer 调用中传 preserve_paths；host 会在写入后核对 persistent ID / 对象数 / mm bounds。"
                    )
                if preserve_paths:
                    preservation_before = preserve_snapshot(preservation_script_id, preserve_paths)
            try:
                dispatch_arguments = arguments
                if bounded and preservation_before:
                    dispatch_arguments = dict(arguments)
                    dispatch_arguments["_keep_expectations"] = [
                        {
                            "path": list(path),
                            **preservation_before["/".join(path)],
                        }
                        for path in arguments.get("preserve_paths", [])
                    ]
                output = self.dispatch(name, dispatch_arguments, project_dir=resolved_project_dir, project_ruby=executor)
                preservation: dict[str, Any] | None = None
                if bounded and preservation_before:
                    preservation_after = preserve_snapshot(
                        preservation_script_id, arguments.get("preserve_paths")
                    )
                    try:
                        preservation = verify_preserved_owned_paths(
                            preservation_before, preservation_after
                        )
                    except ValueError as error:
                        quality_state["preservation"] = {
                            "verified": False,
                            "error": str(error),
                            "paths": sorted(preservation_before),
                        }
                        raise MCPCallError(
                            "定向修正破坏了 reviewer KEEP 几何。正常情况下 pre-commit KEEP guard 会在提交前回滚；"
                            "这里的 post-commit 检查是第二道防线，说明实际状态仍与保护指纹不一致。"
                            f" {error} 请停止宣称质量通过并检查当前模型。"
                        ) from error
                    quality_state["preservation"] = preservation
                    qa_dir = resolved_project_dir / "runtime" / "agent_workspace" / "qa"
                    qa_dir.mkdir(parents=True, exist_ok=True)
                    receipt_path = qa_dir / f"keep-preservation-write-{writes + 1}.json"
                    receipt_path.write_text(
                        json.dumps(preservation, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    if isinstance(output, dict):
                        output["preservation_verification"] = preservation
                        output.setdefault("contentItems", []).append({
                            "type": "inputText",
                            "text": "KEEP preservation receipt: "
                                    + json.dumps(preservation, ensure_ascii=False),
                        })
                if bounded and review_before_write is not None:
                    script_id = str(arguments.get("script_id") or "")
                    state = executor.ruby_state.get(script_id, {})
                    writer_memory = {
                        "script_id": script_id,
                        "revision": int(state.get("revision", 0) or 0),
                        "relative_path": str(arguments.get("relative_path") or ""),
                        "update_mode": str(arguments.get("update_mode") or "replace"),
                        "source_sha256": str(state.get("source_sha256") or ""),
                        "precommit_keep_guard": state.get("last_precommit_keep_guard"),
                        "preservation_verification": preservation,
                    }
                    try:
                        repair_entry = record_repair_attempt(
                            resolved_project_dir,
                            review_before_write,
                            writer_memory,
                        )
                        quality_state["repair_memory"] = repair_entry
                        if isinstance(output, dict):
                            output["repair_memory"] = repair_entry
                            output.setdefault("contentItems", []).append({
                                "type": "inputText",
                                "text": "Host repair-memory attempt: "
                                        + json.dumps(repair_entry, ensure_ascii=False),
                            })
                    except (OSError, ValueError) as error:
                        # Repair memory is advisory. Do not invalidate geometry
                        # that already passed transaction/write verification.
                        quality_state["repair_memory"] = {
                            "status": "memory_write_failed",
                            "error": str(error),
                        }
                return output
            finally:
                if bounded and any(state.get("revision", 0) > before.get(key, 0) for key, state in executor.ruby_state.items()):
                    writes += 1
                    quality_state["writes"] = writes
                    quality_state["review"] = None
        return AgentToolContext(dynamic_tools=dynamic_tools, dispatch=dispatch, quality_state=quality_state)

    @staticmethod
    def _dynamic_tool(name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"type": "function", "name": name, "description": description, "inputSchema": schema}

    @staticmethod
    def _allow_kongxing(name: str, tool_profile: ToolProfile) -> bool:
        if tool_profile == "full":
            return True
        folded = name.casefold()
        if name in {"sketchup_eval_project_file", "sketchup_create_mass", "sketchup_create_road"}:
            return False
        return any(keyword in folded for keyword in _RECONSTRUCTION_KONGXING_KEYWORDS)

    @staticmethod
    def _allow_backend_tool(backend_id: str, raw_name: str, tool_profile: ToolProfile) -> bool:
        if tool_profile == "full":
            return True
        if backend_id == "saie":
            return raw_name in _RECONSTRUCTION_SAIE_TOOLS
        # ArchFlow and other broad backends are useful later, but they add noise to
        # the single-image reconstruction loop and are therefore hidden here.
        return False

    def dynamic_tools(self, *, ruby_enabled: bool = False,
                      tool_profile: ToolProfile = "full") -> list[dict[str, Any]]:
        try:
            discovered = self.sketchup_mcp.list_tools()
        except (ConnectorUnavailable, MCPCallError) as error:
            raise RuntimeError(f"The configured Kongxing SketchUp MCP could not list its tools: {error}") from error
        tools: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in discovered:
            name = item.get("name")
            schema = item.get("inputSchema")
            if not isinstance(name, str) or not isinstance(schema, dict) or name in seen:
                continue
            if name == "sketchup_eval_project_file" or name.startswith("archflow_"):
                continue
            if not self._allow_kongxing(name, tool_profile):
                continue
            seen.add(name)
            tools.append(self._dynamic_tool(
                name,
                str(item.get("description") or f"Call the existing Kongxing SketchUp MCP tool {name}."),
                schema,
            ))

        for backend_id, backend in sorted(self.oss_backends.items()):
            try:
                backend_tools = backend.list_tools()
            except Exception:
                # Optional reuse must never break the already-working Kongxing-only path.
                continue
            for item in backend_tools:
                raw_name = item.get("name")
                schema = item.get("inputSchema")
                if not isinstance(raw_name, str) or not isinstance(schema, dict):
                    continue
                if not self._allow_backend_tool(backend_id, raw_name, tool_profile):
                    continue
                public_name = f"{backend_id}__{raw_name}"
                if public_name in seen:
                    continue
                seen.add(public_name)
                tools.append(self._dynamic_tool(
                    public_name,
                    f"[{backend_id} reusable OSS helper] {str(item.get('description') or raw_name)}",
                    schema,
                ))

        if ruby_enabled:
            tools.append(self._dynamic_tool(
                "sketchup_inspect_owned", "Read-only nested owned-group inspection with actual persistent IDs and XYZ millimeter bounds; no geometry/diagnostic objects, source writes or revision change. Use exact path name segments; [] lists the owned root. Page until next_offset is null when proving full object preservation. Bounds are explicitly relative to each parent, not global.",
                {"type": "object", "required": ["script_id"], "properties": {
                    "script_id": {"type": "string"},
                    "path": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 200}, "maxItems": 8},
                    "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                }, "additionalProperties": False},
            ))
            if tool_profile == "reconstruction_coding":
                tools.append(self._dynamic_tool(
                    "sketchup_capture_canonical_view",
                    "READ-ONLY deterministic review capture. Use this, not a hand-labeled arbitrary camera, for the six canonical "
                    "front/rear/left/right/roof/oblique quality-gate images. The host reads the selected persistent ProjectRuby root "
                    "bounds, sets a deterministic X/Y/Z camera, captures a fresh PNG, and records camera + current-revision provenance. "
                    "This does not edit geometry. For source-perspective/interior detail pairs, the normal camera/export tools may still "
                    "be used and submitted separately as evidence_pairs.",
                    {
                        "type": "object",
                        "required": ["script_id", "view_name"],
                        "properties": {
                            "script_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,47}$"},
                            "view_name": {"type": "string", "enum": list(_CANONICAL_REVIEW_VIEWS)},
                        },
                        "additionalProperties": False,
                    },
                ))
                tools.append(self._dynamic_tool(
                    "sketchup_submit_visual_review",
                    "READ-ONLY quality gate. After every committed reconstruction pass, use sketchup_capture_canonical_view to create "
                    "six DISTINCT CURRENT front/rear/left/right/roof/oblique agent-view PNGs, then submit the exact actual paths plus the "
                    "bounded fallback critique. When the source camera is not represented by a canonical view, or when interior/detail references exist, add evidence_pairs mapping real source images to current agent-view captures. On the LiteLLM/DeepSeek route the host runs a separate compact read-only critic over source images plus "
                    "the six validated current views and any validated source-matched/interior pairs, then replaces any model-authored verdict before persisting the review. "
                    "Other runtimes may supply the same bounded NEEDS_FIX envelope as critique. The host rejects stale revision "
                    "captures. This tool never edits SketchUp. A NEEDS_FIX review permits the next targeted writer pass; "
                    "NEEDS_FIX:NO ends geometry writes for this turn.",
                    {
                        "type": "object",
                        "required": ["views", "critique"],
                        "properties": {
                            "views": {
                                "type": "object",
                                "required": ["front", "rear", "left", "right", "roof", "oblique"],
                                "properties": {
                                    name: {"type": "string", "pattern": "^outputs/renders/agent-view-[A-Za-z0-9_.-]+\\.png$"}
                                    for name in ("front", "rear", "left", "right", "roof", "oblique")
                                },
                                "additionalProperties": False,
                            },
                            "critique": {"type": "string", "minLength": 20, "maxLength": 12000, "description": "Optional fallback verdict for runtimes without a host-side dedicated critic; ignored/replaced by LiteLLM host critic."},
                            "evidence_pairs": {
                                "type": "array",
                                "maxItems": 12,
                                "description": "Optional source-matched exterior/interior/detail comparisons using current-revision agent-view PNGs.",
                                "items": {
                                    "type": "object",
                                    "required": ["source_ref", "current_view"],
                                    "properties": {
                                        "source_ref": {"type": "string", "pattern": "^inputs/(?:reference|site|brief)/.+\\.(?:png|jpg|jpeg|webp|gif)$"},
                                        "current_view": {"type": "string", "pattern": "^outputs/renders/agent-view-[A-Za-z0-9_.-]+\\.png$"},
                                        "label": {"type": "string", "maxLength": 200},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "additionalProperties": False,
                    },
                ))
            tools.append({
                "type": "function",
                "name": "sketchup_run_workspace_ruby",
                "description": (
                    "PRIMARY project-specific modeling tool. Execute a persistent Ruby file authored under "
                    "agent_workspace/scripts. For image reconstruction, prefer this for repeated/custom geometry, "
                    "components, facade systems, canopies, louvers and other source-specific work. Revise and rerun the "
                    "same file so the project keeps an inspectable coding history. The guarded transaction returns "
                    "model readback plus a screenshot. update_mode=replace (default) CLEARS the owned root before running "
                    "the complete reconstruction script. An existing root requires allow_full_rebuild=true for an intentional "
                    "complete rebuild; local corrections must use edit. After a visual review, correction writes are host-forced to edit mode; "
                    "map reviewer KEEP items to exact named paths and pass preserve_paths so the host proves their persistent IDs, "
                    "object counts and mm bounds did not change. update_mode=edit retains that existing script_id root for "
                    "local patches. Injected remove_owned_group.call(exact_name) removes exactly one unlocked direct-child "
                    "group/component instance, never the root or unrelated objects. For nested corrections pass an ARRAY of exact name segments, e.g. ['SHELL','LEFT_WALL']; locked/shared ancestors are rejected. Recreate only that affected child. "
                    "Never use replace with inspection-only or partial patch code; use readback "
                      "tools for inspection. edit requires the same existing script_id. "
                      "Ruby runs inside a host-owned transaction with injected model and root (Sketchup::Group). "
                      "Injected saie_wall.call(params), with keys name, centerline:[[x1,y1],[x2,y2]], thickness_mm, height_mm, elevation_mm, "
                    "uses STRING keys and all coordinates/dimensions in mm to create one SAIE solid wall inside the owned root. "
                    "For a facade wall with rectangular openings, prefer injected saie_wall_with_openings.call(params): the same wall keys plus "
                    "openings:[{offset_mm,width_mm,height_mm,sill_mm},...]. It adapts SAIE's one-combined-cutter/one-subtract batch-opening pattern "
                    "inside the owned root so a facade need not be assembled from many visible wall-segment groups. "
                    "Local SketchUp validation remains required if a boolean subtract fails. "
                    "Transaction returns owned_before/owned_after child IDs and XYZ bounds in mm. "
                    "Create geometry only under root.entities, e.g. g=root.entities.add_group; "
                      "g.entities.add_face(...). Do not redefine root, use Sketchup.active_model/active_entities, "
                      "or call start_operation/commit_operation/abort_operation/save/export: the host owns these. "
                      "A Group has .entities; Sketchup::Entities does not. "
                      "Isolate adjacent solids in child groups/components: pushpull can merge/delete coplanar faces. "
                      "Do not reuse a Face after pushpull unless valid?. Pass model explicitly into Ruby def helpers."
                ),
                "inputSchema": {
                    "type": "object",
                    "required": ["script_id", "relative_path"],
                    "properties": {
                        "script_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,47}$"},
                        "relative_path": {"type": "string", "pattern": "^scripts/[A-Za-z0-9_.-]+\\.rb$", "maxLength": 160},
                        "update_mode": {"type": "string", "enum": ["replace", "edit"], "default": "replace"},
                        "allow_full_rebuild": {"type": "boolean", "description": "Explicit intentional whole-root rebuild only; do not set for local modifications."},
                        "preserve_paths": {
                            "type": "array",
                            "maxItems": 24,
                            "description": "For a post-review targeted correction, exact named owned-group paths that must remain unchanged. Map reviewer KEEP items to these paths with sketchup_inspect_owned first. The host snapshots them, verifies the same fingerprints inside the SketchUp transaction before commit (abort on regression), then rechecks persistent ID, object count and mm bounds after commit as defense in depth.",
                            "items": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 8,
                                "items": {"type": "string", "minLength": 1, "maxLength": 200}
                            }
                        },
                    },
                    "additionalProperties": False,
                },
            })
            if tool_profile == "full":
                tools.append({
                    "type": "function",
                    "name": "sketchup_run_project_ruby",
                    "description": (
                        "Run a short task-specific Ruby snippet inside SketchUp on this verified disposable project model. "
                        "For non-trivial or revisable work prefer sketchup_run_workspace_ruby. Source is stored only in the "
                        "ignored project runtime. Use the same script_id to revise the existing script/model."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "required": ["script_id", "ruby_source"],
                        "properties": {
                            "script_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,47}$"},
                            "ruby_source": {"type": "string", "maxLength": 120000},
                        },
                        "additionalProperties": False,
                    },
                })
        if not tools:
            raise RuntimeError("The configured SketchUp tool stack returned no callable schemas.")
        return tools

    def dispatch(self, name: str, arguments: dict[str, Any], *, project_dir: Path,
                 project_ruby: ProjectRubyExecutor | None) -> dict[str, Any]:
        if name == "sketchup_inspect_owned":
            if project_ruby is None:
                raise MCPCallError("Owned inspection requires a verified disposable model and existing owned root.")
            return project_ruby.inspect_owned(arguments)
        if name == "sketchup_capture_canonical_view":
            if project_ruby is None:
                raise MCPCallError("Canonical review capture requires a verified disposable model and existing owned root.")
            script_id = str(arguments.get("script_id") or "")
            view_name = str(arguments.get("view_name") or "")
            snapshot_result = project_ruby.inspect_owned({
                "script_id": script_id,
                "path": [],
                "offset": 0,
                "limit": 1,
            })
            try:
                snapshot = json.loads(snapshot_result["contentItems"][0]["text"])
                bounds_mm = snapshot["bounds_mm"]
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
                raise MCPCallError("Canonical review capture could not read owned-root bounds.") from error
            camera = canonical_camera_from_bounds_mm(bounds_mm, view_name)
            project_ruby.adapter.set_camera(camera["eye_m"], camera["target_m"], camera["up_m"])
            output_path = project_dir / "outputs" / "renders" / f"agent-view-{view_name}-{uuid.uuid4().hex[:10]}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Keep the host-set direction/target stable; a connector-side zoom_extents
            # may rewrite the camera after we have certified its role.
            project_ruby.adapter.capture_view(output_path, width=1500, height=950, zoom_extents=False)
            project_ruby.refresh_active_model_snapshot()
            if output_path.is_symlink() or not output_path.is_file():
                raise MCPCallError("SketchUp did not write the canonical review screenshot.")
            if not 0 < output_path.stat().st_size <= 8 * 1024 * 1024:
                raise MCPCallError("Canonical review screenshot is empty or exceeds the 8 MB payload limit.")
            try:
                with Image.open(output_path) as captured:
                    if captured.format != "PNG":
                        raise ValueError("Expected PNG")
                    width, height = captured.size
                    captured.verify()
            except (OSError, ValueError) as error:
                raise MCPCallError("Canonical review screenshot is not a readable PNG.") from error
            revisions = {
                sid: int(state.get("revision", 0))
                for sid, state in project_ruby.ruby_state.items()
                if int(state.get("revision", 0)) > 0
            }
            evidence = {
                "path": output_path.relative_to(project_dir).as_posix(),
                "width": width,
                "height": height,
                "quality_status": "not_accepted",
                "model_revisions": revisions,
                "camera_contract_version": 1,
                "canonical_view": view_name,
                "canonical_script_id": script_id,
                "camera": camera,
                "focus_bounds_mm": bounds_mm,
            }
            output_path.with_suffix(".evidence.json").write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return {
                "success": True,
                "visual_evidence": evidence,
                "contentItems": [
                    {
                        "type": "inputText",
                        "text": "Deterministic canonical capture receipt: " + json.dumps(evidence, ensure_ascii=False),
                    },
                    {
                        "type": "inputImage",
                        "imageUrl": "data:image/png;base64," + base64.b64encode(output_path.read_bytes()).decode("ascii"),
                    },
                ],
            }
        if name == "sketchup_run_workspace_ruby":
            if project_ruby is None:
                raise MCPCallError("The workspace Ruby tool is not enabled for this session.")
            return run_workspace_ruby(
                project_ruby,
                agent_workspace=project_dir / "runtime" / "agent_workspace",
                arguments=arguments,
            )

        if name == "sketchup_run_project_ruby":
            if project_ruby is None:
                raise MCPCallError("The project Ruby tool is not enabled for this session.")
            return project_ruby.run(arguments)

        if "__" in name:
            backend_id, raw_name = name.split("__", 1)
            backend = self.oss_backends.get(backend_id)
            if backend is None:
                raise MCPCallError(f"Optional OSS backend {backend_id!r} is not active for this session.")
            try:
                return backend.call_for_agent(raw_name, arguments, project_dir=project_dir)
            finally:
                if project_ruby is not None:
                    project_ruby.refresh_active_model_snapshot()

        if name == "sketchup_export_view_image":
            output_path = project_dir / "outputs" / "renders" / f"agent-view-{uuid.uuid4().hex[:10]}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            safe_arguments = dict(arguments)
            safe_arguments["output_path"] = str(output_path.resolve())
            try:
                result = self.sketchup_mcp.call_for_agent(name, safe_arguments)
            finally:
                if project_ruby is not None:
                    project_ruby.refresh_active_model_snapshot()
            if result.get("success") is False or result.get("isError") is True:
                return result
            if output_path.is_symlink() or not output_path.is_file():
                raise MCPCallError("SketchUp did not write a review screenshot; visual QA remains pending.")
            if not 0 < output_path.stat().st_size <= 8 * 1024 * 1024:
                raise MCPCallError("SketchUp screenshot is empty or exceeds the 8 MB payload limit.")
            try:
                with Image.open(output_path) as captured:
                    if captured.format != "PNG":
                        raise ValueError("Expected PNG")
                    width, height = captured.size
                    captured.verify()
            except (OSError, ValueError) as error:
                raise MCPCallError("SketchUp screenshot is not a readable PNG; visual QA remains pending.") from error
            result["visual_evidence"] = {
                "path": output_path.relative_to(project_dir).as_posix(),
                "width": width, "height": height,
                "quality_status": "not_accepted",
                "model_revisions": {
                    script_id: state.get("revision")
                    for script_id, state in (project_ruby.ruby_state.items() if project_ruby else [])
                },
            }
            output_path.with_suffix(".evidence.json").write_text(
                json.dumps(result["visual_evidence"], ensure_ascii=False, indent=2), encoding="utf-8")
            result.setdefault("contentItems", []).append({
                "type": "inputText",
                "text": "Actual current capture receipt (use this path, not a requested/invented filename): "
                        + json.dumps(result["visual_evidence"], ensure_ascii=False),
            })
            result.setdefault("contentItems", []).append({
                "type": "inputImage",
                "imageUrl": "data:image/png;base64," + base64.b64encode(output_path.read_bytes()).decode("ascii"),
            })
            return result
        try:
            result = self.sketchup_mcp.call_for_agent(name, arguments)
        finally:
            if project_ruby is not None:
                project_ruby.refresh_active_model_snapshot()
        return result
