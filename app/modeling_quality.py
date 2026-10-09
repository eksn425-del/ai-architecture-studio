"""Modeling quality loop helpers.

The visual-critique decision/parser shape is adapted from gaoypeng/3dcodebench
(core/visual_critique.py, Apache-2.0). The post-write expected/actual boundary
contract is adapted from dcc-mcp/dcc-mcp-sketchup (write_contract.py, MIT).

This module changes both ideas for K Studio: the critic is read-only and returns
at most three targeted architectural mismatches; the writer verification checks
the committed owned SketchUp root instead of trusting a success string.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable

from .reconstruction_evidence import load_reconstruction_evidence


CANONICAL_REVIEW_VIEWS = ("front", "rear", "left", "right", "roof", "oblique")
MAX_CRITIC_ISSUES = 3

_NEEDS_FIX_RE = re.compile(r"^\s*NEEDS_FIX\s*:\s*(YES|NO)\b", re.IGNORECASE | re.MULTILINE)
_ASSESSMENT_RE = re.compile(r"<assessment>(.*?)</assessment>", re.IGNORECASE | re.DOTALL)
_ISSUE_RE = re.compile(r"<issue(?P<attrs>[^>]*)>(?P<body>.*?)</issue>", re.IGNORECASE | re.DOTALL)
_KEEP_RE = re.compile(r"<keep>(.*?)</keep>", re.IGNORECASE | re.DOTALL)
_PRIORITY_RE = re.compile(r"priority\s*=\s*[\"']?(\d+)", re.IGNORECASE)
_VIEW_RE = re.compile(r"view\s*=\s*[\"']?([a-z0-9_-]+)", re.IGNORECASE)
_PROBLEM_RE = re.compile(r"(?:problem|问题)\s*[:：]\s*(.*?)(?=\n\s*(?:action|修正|建议)\s*[:：]|\Z)", re.IGNORECASE | re.DOTALL)
_ACTION_RE = re.compile(r"(?:action|修正|建议)\s*[:：]\s*(.*)", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class VisualIssue:
    priority: int
    view: str
    problem: str
    action: str


@dataclass(frozen=True)
class VisualCritique:
    needs_fix: bool | None
    assessment: str
    issues: tuple[VisualIssue, ...]
    keep: tuple[str, ...]
    malformed: bool
    raw: str


def build_visual_critic_prompt(
    reference_labels: Iterable[str],
    review_labels: Iterable[str],
    *,
    max_issues: int = MAX_CRITIC_ISSUES,
) -> str:
    """Build the compact read-only critic contract used after a modeling pass."""
    if max_issues < 1 or max_issues > MAX_CRITIC_ISSUES:
        raise ValueError(f"max_issues must be 1..{MAX_CRITIC_ISSUES}.")
    refs = ", ".join(reference_labels) or "attached source image(s)"
    reviews = ", ".join(review_labels) or "current SketchUp review views"
    return (
        "You are the read-only visual critic for an architectural SketchUp reconstruction. "
        "Compare the SOURCE evidence first, then the CURRENT model views. Tool success, a nonempty model, "
        "or a successful save is not visual success. Preserve geometry that already matches. "
        "First inventory every visible primary and attached volume, lower roof, setback and canopy across ALL sources; "
        "compare silhouette and height hierarchy to the model. Missing volumes outrank details or template clutter. "
        "Do not accept a dominant rectangular box when the source shows a lower annex, and do not propose extra plants to hide errors. "
        "KEEP must name only genuinely unchanged geometry. Do not protect an entire roof or volume that an issue requires correcting; "
        "distinguish preserving its material/character from freezing its dimensions. "
        f"Source: {refs}. Current views: {reviews}. "
        f"Return at most {max_issues} highest-impact mismatches, ordered by priority. "
        "Prefer silhouette, storey/bay count, opening count/position, recess/projection depth, roof/parapet, "
        "major material zones and obvious intersections over micro-detail. Do not write Ruby and do not propose a rebuild "
        "when a local patch is enough. Use exactly this response envelope:\n"
        "NEEDS_FIX: YES|NO\n"
        "<assessment>brief overall comparison</assessment>\n"
        "<issue priority=\"1\" view=\"front\">problem: ...\naction: ...</issue>\n"
        "<issue priority=\"2\" view=\"roof\">problem: ...\naction: ...</issue>\n"
        "<keep>one already-correct feature per line</keep>\n"
        "If no blocking mismatch remains, return NEEDS_FIX: NO and omit issue blocks."
    )


def _field(body: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(body)
    if match:
        return match.group(1).strip()
    return ""


def parse_visual_critique_response(text: str, *, max_issues: int = MAX_CRITIC_ISSUES) -> VisualCritique:
    """Parse the bounded critic envelope without letting the critic write geometry."""
    raw = text or ""
    decision = _NEEDS_FIX_RE.search(raw)
    needs_fix = None if decision is None else decision.group(1).upper() == "YES"
    assessment_match = _ASSESSMENT_RE.search(raw)
    assessment = assessment_match.group(1).strip() if assessment_match else ""

    issues: list[VisualIssue] = []
    for index, match in enumerate(_ISSUE_RE.finditer(raw), 1):
        attrs, body = match.group("attrs"), match.group("body").strip()
        priority_match, view_match = _PRIORITY_RE.search(attrs), _VIEW_RE.search(attrs)
        priority = int(priority_match.group(1)) if priority_match else index
        view = view_match.group(1).lower() if view_match else "unspecified"
        problem = _field(body, _PROBLEM_RE)
        action = _field(body, _ACTION_RE)
        if not problem:
            lines = [line.strip() for line in body.splitlines() if line.strip()]
            problem = lines[0] if lines else body
            if not action and len(lines) > 1:
                action = lines[1]
        issues.append(VisualIssue(priority=priority, view=view, problem=problem, action=action))
    issues = sorted(issues, key=lambda issue: issue.priority)[:max_issues]

    keep_match = _KEEP_RE.search(raw)
    keep = ()
    if keep_match:
        keep = tuple(
            line.strip(" -\t")
            for line in keep_match.group(1).splitlines()
            if line.strip(" -\t")
        )

    if needs_fix is None and issues:
        needs_fix = True
    malformed = needs_fix is None or (needs_fix is True and not issues)
    return VisualCritique(
        needs_fix=needs_fix,
        assessment=assessment,
        issues=tuple(issues),
        keep=keep,
        malformed=malformed,
        raw=raw,
    )


def _numbers_match(expected: Any, actual: Any, *, rel_tol: float = 1e-6, abs_tol: float = 0.01) -> bool:
    try:
        return math.isclose(float(expected), float(actual), rel_tol=rel_tol, abs_tol=abs_tol)
    except (TypeError, ValueError):
        return False


def _values_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return _numbers_match(expected, actual)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(_values_match(expected[key], actual[key]) for key in expected)
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return len(expected) == len(actual) and all(_values_match(a, b) for a, b in zip(expected, actual))
    return expected == actual


def require_post_write_verification(
    transaction: dict[str, Any],
    readback: dict[str, Any],
    *,
    expected_root_pid: int,
    expected_revision: int,
) -> dict[str, Any]:
    """Require a post-commit owned-root readback and return expected/actual evidence.

    K Studio persists the recoverable transaction first, then immediately re-reads
    the exact owned root. A failed verification is surfaced as an error while the
    committed checkpoint remains recoverable.
    """
    checks: list[dict[str, Any]] = []

    def check(name: str, expected: Any, actual: Any) -> None:
        record = {"check": name, "expected": expected, "actual": actual}
        checks.append(record)
        if not _values_match(expected, actual):
            raise ValueError(
                f"{name} read-back mismatch (expected {expected!r}, actual {actual!r})."
            )

    check("transaction_status", "committed", transaction.get("status"))
    check("root_persistent_id", expected_root_pid, readback.get("persistent_id"))
    check("revision", expected_revision, readback.get("revision"))

    owned_after = transaction.get("owned_after")
    if isinstance(owned_after, dict):
        for field in ("objects_total", "bounds_mm"):
            if field in owned_after:
                check(field, owned_after[field], readback.get(field))

    return {
        "schema_version": 1,
        "verified": True,
        "source": "post_commit_owned_root_readback",
        "checks": checks,
    }


def owned_inspection_fingerprint(payload: Any) -> dict[str, Any]:
    """Return the small identity/bounds fingerprint used for KEEP guards."""
    if not isinstance(payload, dict):
        raise ValueError("Owned inspection fingerprint requires an object payload.")
    persistent_id = payload.get("persistent_id")
    objects_total = payload.get("objects_total")
    bounds_mm = payload.get("bounds_mm")
    if type(persistent_id) is not int or persistent_id <= 0:
        raise ValueError("Owned inspection fingerprint requires a positive persistent_id.")
    if type(objects_total) is not int or objects_total < 0:
        raise ValueError("Owned inspection fingerprint requires a nonnegative objects_total.")
    if not isinstance(bounds_mm, dict):
        raise ValueError("Owned inspection fingerprint requires bounds_mm.")
    low, high = bounds_mm.get("min"), bounds_mm.get("max")
    if (
        not isinstance(low, list) or not isinstance(high, list)
        or len(low) != 3 or len(high) != 3
    ):
        raise ValueError("Owned inspection fingerprint bounds_mm must contain min/max XYZ triples.")
    for value in [*low, *high]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("Owned inspection fingerprint bounds_mm must be finite numeric XYZ values.")
    return {
        "persistent_id": persistent_id,
        "objects_total": objects_total,
        "bounds_mm": {
            "min": [float(value) for value in low],
            "max": [float(value) for value in high],
        },
    }


def verify_preserved_owned_paths(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Enforce a do-no-harm contract for reviewer KEEP geometry.

    This adapts the last-known-good principle used by 3DCodeBench and the
    structured visual-action boundary used by SketchUp Agent Harness. It does
    not decide what should be protected; the Builder maps reviewer KEEP items
    to exact owned-group paths before a targeted edit. The host then verifies
    identity, object count and millimeter bounds after the write.
    """
    if not before:
        raise ValueError("At least one preserved owned path is required.")
    if set(before) != set(after):
        missing = sorted(set(before) - set(after))
        extra = sorted(set(after) - set(before))
        raise ValueError(f"Preserved path set changed (missing={missing}, extra={extra}).")
    checks: list[dict[str, Any]] = []
    for path in sorted(before):
        expected = owned_inspection_fingerprint(before[path])
        actual = owned_inspection_fingerprint(after[path])
        for field in ("persistent_id", "objects_total", "bounds_mm"):
            check = {
                "path": path,
                "check": field,
                "expected": expected[field],
                "actual": actual[field],
            }
            checks.append(check)
            if not _values_match(expected[field], actual[field]):
                raise ValueError(
                    f"Protected KEEP path {path!r} changed {field}: "
                    f"expected {expected[field]!r}, actual {actual[field]!r}."
                )
    return {
        "schema_version": 1,
        "verified": True,
        "source": "keep_path_expected_actual_readback",
        "paths": sorted(before),
        "checks": checks,
    }



_FACADE_PROVENANCE = {"pending", "observed", "user_confirmed", "inferred", "mixed"}


def validate_facade_schedule_payload(value: Any) -> dict[str, Any]:
    """Validate the stable source-facing schedule without making it geometry truth.

    Extra fields are allowed for forward compatibility, but the fields used by
    the Builder/Critic contract must keep predictable types and provenance.
    """
    if not isinstance(value, dict):
        raise ValueError("facade schedule root must be an object.")
    if value.get("schema_version") != 1:
        raise ValueError("facade schedule schema_version must be 1.")

    dimensions = value.get("dimensions_mm", {})
    if not isinstance(dimensions, dict):
        raise ValueError("facade schedule dimensions_mm must be an object.")
    for key, number in dimensions.items():
        if number is None:
            continue
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)) or number < 0:
            raise ValueError(f"facade schedule dimension {key!r} must be null or a nonnegative finite number.")

    views = value.get("views", {})
    if not isinstance(views, dict):
        raise ValueError("facade schedule views must be an object.")
    for view_name in ("front", "rear", "left", "right"):
        item = views.get(view_name)
        if item is None:
            continue
        if not isinstance(item, dict):
            raise ValueError(f"facade schedule view {view_name!r} must be an object.")
        provenance = item.get("provenance", "pending")
        if provenance not in _FACADE_PROVENANCE:
            raise ValueError(f"facade schedule view {view_name!r} has invalid provenance.")
        for count_key in ("opening_count", "door_count"):
            count = item.get(count_key)
            if count is not None and (type(count) is not int or count < 0):
                raise ValueError(f"facade schedule {view_name}.{count_key} must be null or a nonnegative integer.")
        for list_key in ("features", "notes"):
            items = item.get(list_key, [])
            if not isinstance(items, list) or any(not isinstance(entry, str) for entry in items):
                raise ValueError(f"facade schedule {view_name}.{list_key} must be a string list.")

    roof = value.get("roof", {})
    if not isinstance(roof, dict):
        raise ValueError("facade schedule roof must be an object.")
    if roof.get("provenance", "pending") not in _FACADE_PROVENANCE:
        raise ValueError("facade schedule roof provenance is invalid.")
    for list_key in ("divisions", "notes"):
        items = roof.get(list_key, [])
        if not isinstance(items, list) or any(not isinstance(entry, str) for entry in items):
            raise ValueError(f"facade schedule roof.{list_key} must be a string list.")

    for list_key in ("global_features", "user_confirmed", "inferred"):
        items = value.get(list_key, [])
        if not isinstance(items, list) or any(not isinstance(entry, str) for entry in items):
            raise ValueError(f"facade schedule {list_key} must be a string list.")
    return value


def load_facade_schedule(project_dir: Path) -> dict[str, Any] | None:
    """Load the compact project-local facade/roof schedule for visual review."""
    path = project_dir.resolve() / "runtime" / "agent_workspace" / "notes" / "facade_schedule.json"
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return validate_facade_schedule_payload(value)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def validate_visual_review_views(
    project_dir: Path,
    ruby_state: dict[str, dict[str, Any]],
    views: Any,
) -> tuple[dict[str, int], dict[str, dict[str, Any]], dict[str, Path]]:
    """Resolve only trusted current-revision screenshots for a visual critic.

    This helper performs the provenance checks before any provider is allowed to
    read the images, so a model-supplied path cannot make the host read arbitrary
    project files. The same validation is reused when persisting the review.
    """
    if not isinstance(views, dict) or set(views) != set(CANONICAL_REVIEW_VIEWS):
        raise ValueError(
            "views must contain exactly front, rear, left, right, roof and oblique."
        )

    current_revisions = {
        script_id: int(state.get("revision", 0))
        for script_id, state in ruby_state.items()
        if int(state.get("revision", 0)) > 0
    }
    if not current_revisions:
        raise ValueError("Visual review requires at least one committed project Ruby revision.")
    for script_id, state in ruby_state.items():
        if int(state.get("revision", 0)) <= 0:
            continue
        verification = state.get("last_verification")
        if not isinstance(verification, dict) or verification.get("verified") is not True:
            raise ValueError(
                f"Current script {script_id!r} has no verified post-write readback receipt."
            )

    project_dir = project_dir.resolve()
    render_root = (project_dir / "outputs" / "renders").resolve()
    resolved_views: dict[str, dict[str, Any]] = {}
    image_paths: dict[str, Path] = {}
    seen_paths: set[Path] = set()
    for view_name in CANONICAL_REVIEW_VIEWS:
        relative = views.get(view_name)
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"{view_name} view path is required.")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"{view_name} view path must stay inside the project.")
        image_path = project_dir.joinpath(*pure.parts).resolve()
        if not image_path.is_relative_to(render_root):
            raise ValueError(f"{view_name} view must come from outputs/renders.")
        if not image_path.name.startswith("agent-view-") or image_path.suffix.lower() != ".png":
            raise ValueError(f"{view_name} must use an actual agent-view PNG capture.")
        if image_path in seen_paths:
            raise ValueError("Each canonical review view must use a distinct current screenshot.")
        seen_paths.add(image_path)
        if not image_path.is_file() or image_path.stat().st_size <= 0:
            raise ValueError(f"{view_name} screenshot is missing or empty.")

        evidence_path = image_path.with_suffix(".evidence.json")
        if not evidence_path.is_file():
            raise ValueError(f"{view_name} screenshot is missing its evidence sidecar.")
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"{view_name} screenshot evidence is unreadable.") from error
        evidence_revisions = {
            str(key): int(value)
            for key, value in (evidence.get("model_revisions") or {}).items()
        }
        if evidence_revisions != current_revisions:
            raise ValueError(
                f"{view_name} screenshot is stale: expected revisions "
                f"{current_revisions}, captured {evidence_revisions}."
            )
        if evidence.get("camera_contract_version") != 1 or evidence.get("canonical_view") != view_name:
            raise ValueError(
                f"{view_name} screenshot is not a host-certified canonical {view_name} capture. "
                "Use sketchup_capture_canonical_view for quality-gate front/rear/left/right/roof/oblique evidence."
            )
        camera = evidence.get("camera")
        if not isinstance(camera, dict) or not all(
            isinstance(camera.get(key), list) and len(camera[key]) == 3
            for key in ("eye_m", "target_m", "up_m")
        ):
            raise ValueError(f"{view_name} canonical screenshot is missing camera provenance.")
        resolved_views[view_name] = {
            "path": image_path.relative_to(project_dir).as_posix(),
            "width": evidence.get("width"),
            "height": evidence.get("height"),
            "model_revisions": evidence_revisions,
            "canonical_view": evidence.get("canonical_view"),
            "canonical_script_id": evidence.get("canonical_script_id"),
            "camera": camera,
        }
        image_paths[view_name] = image_path
    return current_revisions, resolved_views, image_paths



def validate_source_matched_pairs(
    project_dir: Path,
    current_revisions: dict[str, int],
    pairs: Any,
) -> list[dict[str, Any]]:
    """Validate optional source-to-current camera/detail pairs.

    Canonical six views prove broad model coverage. These pairs let the critic
    compare an arbitrary source perspective or an interior/detail reference
    against a current SketchUp camera from the same model revision.
    """
    if pairs in (None, []):
        return []
    if not isinstance(pairs, list) or len(pairs) > 12:
        raise ValueError("evidence_pairs must be a list of at most 12 source/current pairs.")

    project_root = project_dir.resolve()
    inputs_root = (project_root / "inputs").resolve()
    render_root = (project_root / "outputs" / "renders").resolve()
    resolved: list[dict[str, Any]] = []
    for index, item in enumerate(pairs):
        if not isinstance(item, dict):
            raise ValueError(f"evidence_pairs[{index}] must be an object.")
        source_ref = item.get("source_ref")
        current_ref = item.get("current_view")
        label = item.get("label", "")
        if not isinstance(source_ref, str) or not source_ref:
            raise ValueError(f"evidence_pairs[{index}].source_ref is required.")
        if not isinstance(current_ref, str) or not current_ref:
            raise ValueError(f"evidence_pairs[{index}].current_view is required.")
        if not isinstance(label, str):
            raise ValueError(f"evidence_pairs[{index}].label must be a string.")

        source_pure = PurePosixPath(source_ref)
        current_pure = PurePosixPath(current_ref)
        if source_pure.is_absolute() or ".." in source_pure.parts:
            raise ValueError(f"evidence_pairs[{index}] source path escaped the project.")
        if current_pure.is_absolute() or ".." in current_pure.parts:
            raise ValueError(f"evidence_pairs[{index}] current path escaped the project.")
        source_path = project_root.joinpath(*source_pure.parts).resolve()
        current_path = project_root.joinpath(*current_pure.parts).resolve()
        if not source_path.is_relative_to(inputs_root) or not source_path.is_file() or source_path.is_symlink():
            raise ValueError(f"evidence_pairs[{index}] source is not a real project input.")
        if source_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            raise ValueError(f"evidence_pairs[{index}] source must be a visual image.")
        if not current_path.is_relative_to(render_root) or not current_path.is_file() or current_path.is_symlink():
            raise ValueError(f"evidence_pairs[{index}] current view is not a real project render.")
        if not current_path.name.startswith("agent-view-") or current_path.suffix.lower() != ".png":
            raise ValueError(f"evidence_pairs[{index}] current view must be an actual agent-view PNG.")

        sidecar = current_path.with_suffix(".evidence.json")
        if not sidecar.is_file():
            raise ValueError(f"evidence_pairs[{index}] current view is missing its evidence sidecar.")
        try:
            evidence = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"evidence_pairs[{index}] current evidence is unreadable.") from error
        revisions = {
            str(key): int(value)
            for key, value in (evidence.get("model_revisions") or {}).items()
        }
        if revisions != current_revisions:
            raise ValueError(
                f"evidence_pairs[{index}] current view is stale: expected {current_revisions}, captured {revisions}."
            )
        resolved.append({
            "source_ref": source_path.relative_to(project_root).as_posix(),
            "current_view": current_path.relative_to(project_root).as_posix(),
            "label": label[:200],
            "model_revisions": revisions,
        })
    return resolved


def submit_visual_review(
    project_dir: Path,
    ruby_state: dict[str, dict[str, Any]],
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Validate and persist one current-revision six-view visual review.

    The review is advisory visual evidence, not geometry truth. Every referenced
    screenshot must be a real K Studio capture whose evidence sidecar names the
    exact current Ruby revisions. This follows the provenance/action boundary
    used by SketchUp Agent Harness while keeping the writer in ProjectRuby.
    """
    views = arguments.get("views")
    critique_text = arguments.get("critique")
    if not isinstance(critique_text, str) or not critique_text.strip():
        raise ValueError("critique must contain the bounded visual review.")

    current_revisions, resolved_views, _ = validate_visual_review_views(
        project_dir, ruby_state, views
    )
    evidence_pairs = validate_source_matched_pairs(
        project_dir, current_revisions, arguments.get("evidence_pairs")
    )

    critique = parse_visual_critique_response(critique_text)
    if critique.malformed or critique.needs_fix is None:
        raise ValueError(
            "Visual review must use NEEDS_FIX plus a parseable assessment/issues/KEEP envelope. "
            "Use plain text, not JSON: NEEDS_FIX: YES\n"
            '<assessment>source comparison</assessment>\n'
            '<issue priority="1" view="front">problem: actual visible mismatch\n'
            'action: targeted named-group fix</issue>\n<keep>correct group path</keep>. '
            "YES requires at least one issue block; NO omits issue blocks. "
            "Native fallback is agent_supplied, not an independent Critic."
        )

    reconstruction_evidence = load_reconstruction_evidence(project_dir, strict=True)
    receipt = {
        "schema_version": 3,
        "advisory": True,
        "fidelity_mode": (reconstruction_evidence or {}).get("fidelity_mode", "pending"),
        "reconstruction_evidence": reconstruction_evidence,
        "reviewer": arguments.get("_reviewer") or {"mode": "agent_supplied"},
        "quality_status": "needs_fix" if critique.needs_fix else "accepted",
        "needs_fix": bool(critique.needs_fix),
        "assessment": critique.assessment,
        "issues": [
            {
                "priority": issue.priority,
                "view": issue.view,
                "problem": issue.problem,
                "action": issue.action,
            }
            for issue in critique.issues
        ],
        "keep": list(critique.keep),
        "model_revisions": current_revisions,
        "views": resolved_views,
        "evidence_pairs": evidence_pairs,
        "writer_verifications": {
            script_id: state.get("last_verification")
            for script_id, state in ruby_state.items()
            if script_id in current_revisions
        },
        "source_images": sorted(
            path.relative_to(project_dir).as_posix()
            for path in (project_dir / "inputs" / "reference").glob("*")
            if path.is_file()
        ),
    }

    qa_dir = project_dir / "runtime" / "agent_workspace" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    if qa_dir.is_symlink() or not qa_dir.resolve().is_relative_to(project_dir):
        raise ValueError("Visual review directory escaped the project.")
    receipt_path = qa_dir / "visual_review.json"
    temporary = receipt_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(receipt_path)
    with (qa_dir / "visual_review_history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, ensure_ascii=False) + "\n")

    issue_lines = [
        f"{index}. [{item['view']}] {item['problem']} -> {item['action']}"
        for index, item in enumerate(receipt["issues"], 1)
    ] or ["1. 无阻断级差异。"]
    keep_lines = [f"- {item}" for item in receipt["keep"]] or ["- 未提供 KEEP 项。"]
    view_lines = [f"- {name}: {item['path']}" for name, item in receipt["views"].items()]
    pair_lines = [
        f"- {item['label'] or 'source match'}: {item['source_ref']} -> {item['current_view']}"
        for item in receipt["evidence_pairs"]
    ] or ["- 未提供额外 source-matched / interior detail pair。"]
    markdown = "\n".join([
        "# Visual QA",
        "",
        f"NEEDS_FIX: {'YES' if receipt['needs_fix'] else 'NO'}",
        "",
        "## Assessment",
        "",
        receipt["assessment"] or "未提供额外总结。",
        "",
        "## Highest-impact mismatches",
        "",
        *issue_lines,
        "",
        "## KEEP",
        "",
        *keep_lines,
        "",
        "## Current-revision evidence",
        "",
        *view_lines,
        "",
        "## Source-matched / interior evidence pairs",
        "",
        *pair_lines,
        "",
        "## Writer verification",
        "",
        f"- model_revisions: {json.dumps(current_revisions, ensure_ascii=False)}",
        "- all current writer receipts verified: true",
        "",
    ])
    (qa_dir / "visual_qa.md").write_text(markdown, encoding="utf-8")
    return receipt
