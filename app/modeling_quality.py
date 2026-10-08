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
import math
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
        if "objects_total" in owned_after and "objects_total" in readback:
            check("objects_total", owned_after["objects_total"], readback["objects_total"])
        if "bounds_mm" in owned_after and "bounds_mm" in readback:
            check("bounds_mm", owned_after["bounds_mm"], readback["bounds_mm"])

    return {
        "schema_version": 1,
        "verified": True,
        "source": "post_commit_owned_root_readback",
        "checks": checks,
    }
