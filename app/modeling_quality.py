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



def load_facade_schedule(project_dir: Path) -> dict[str, Any] | None:
    """Load the compact project-local facade/roof schedule for visual review."""
    path = project_dir.resolve() / "runtime" / "agent_workspace" / "notes" / "facade_schedule.json"
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


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
    reviewer = arguments.get("reviewer")
    if reviewer is None:
        reviewer = {"kind": "builder_self_review", "status": "provisional"}
    if not isinstance(reviewer, dict):
        raise ValueError("reviewer metadata must be an object when provided.")
    reviewer = {
        "kind": str(reviewer.get("kind") or "builder_self_review")[:80],
        "status": str(reviewer.get("status") or "provisional")[:40],
        "provider": str(reviewer.get("provider") or "")[:80],
        "model": str(reviewer.get("model") or "")[:120],
    }
    if not isinstance(views, dict) or set(views) != set(CANONICAL_REVIEW_VIEWS):
        raise ValueError(
            "views must contain exactly front, rear, left, right, roof and oblique."
        )
    if not isinstance(critique_text, str) or not critique_text.strip():
        raise ValueError("critique must contain the bounded visual review.")

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
        resolved_views[view_name] = {
            "path": image_path.relative_to(project_dir).as_posix(),
            "width": evidence.get("width"),
            "height": evidence.get("height"),
            "model_revisions": evidence_revisions,
        }

    critique = parse_visual_critique_response(critique_text)
    if critique.malformed or critique.needs_fix is None:
        raise ValueError(
            "Visual review must use NEEDS_FIX plus a parseable assessment/issues/KEEP envelope."
        )

    receipt = {
        "schema_version": 1,
        "advisory": True,
        "quality_status": "needs_fix" if critique.needs_fix else "accepted",
        "reviewer": reviewer,
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
        "## Writer verification",
        "",
        f"- model_revisions: {json.dumps(current_revisions, ensure_ascii=False)}",
        f"- reviewer: {reviewer['kind']} / {reviewer['status']} / {reviewer['model'] or 'unspecified'}",
        "- all current writer receipts verified: true",
        "",
    ])
    (qa_dir / "visual_qa.md").write_text(markdown, encoding="utf-8")
    return receipt
