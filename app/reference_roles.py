"""Host-owned image provenance. Unknown legacy images are never target truth."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROLES = {"target_building", "defect_location", "supporting", "unknown"}



def current_model_revisions(project_dir: Path, fallback: dict | None = None) -> dict[str, int]:
    backend_path = project_dir / "state/modeling_backend.json"
    if backend_path.is_file() and json.loads(backend_path.read_text()).get("backend") == "blender":
        scene = project_dir / "runtime/blender/scene.json"
        if scene.is_symlink():
            raise ValueError("Unsafe model revision state.")
        revision = int(json.loads(scene.read_text()).get("revision", 0)) if scene.exists() else 0
        return {"blender_scene": revision} if revision > 0 else {}
    path = project_dir / "runtime/project_ruby_state.json"
    if path.is_symlink():
        raise ValueError("Unsafe model revision state.")
    state = json.loads(path.read_text(encoding="utf-8"))["scripts"] if path.exists() else (fallback or {})
    return {key: int(value.get("revision", 0)) for key, value in state.items() if int(value.get("revision", 0)) > 0}


def reference_manifest(project_dir: Path, paths: list[Path]) -> list[dict]:
    root = project_dir.resolve()
    try:
        context = json.loads((root / "state/project_context.json").read_text(encoding="utf-8"))
        refs = context.get("references", []) if isinstance(context, dict) else []
        if not isinstance(refs, list):
            refs = []
    except (OSError, ValueError):
        refs = []
    records = {}
    for ref in refs:
        if isinstance(ref, dict) and isinstance(ref.get("source"), str):
            records.setdefault(ref["source"], []).append(ref)
    result = []
    for path in paths:
        relative = path.resolve().relative_to(root).as_posix()
        matches = records.get(relative, [])
        # Conflicting/duplicate metadata is not silently resolved by list order.
        ref = matches[0] if len(matches) == 1 else {}
        role = ref.get("evidence_role", "unknown")
        if role not in ROLES:
            role = "unknown"
        result.append({"source": relative, "role": role,
                       "turn_id": ref.get("evidence_turn_id", ""),
                       "model_revisions": ref.get("evidence_model_revisions", {}),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def manifest_fingerprint(manifest: list[dict]) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def role_labels(manifest: list[dict]) -> list[str]:
    labels = {"target_building": "SOURCE TARGET", "defect_location": "ISSUE LOCATION (historical model; NOT target truth)",
              "supporting": "SUPPORTING (NOT target truth)", "unknown": "UNKNOWN ROLE (NOT target truth; clarify before fidelity judgment)"}
    return [f"{labels[item['role']]} {item['source']} [turn={item['turn_id'] or 'unknown'}; model revisions={json.dumps(item['model_revisions'], sort_keys=True)}]" for item in manifest]


def validate_review_requirements(reply: str, *, manifest: list[dict], revisions: dict, issue_count: int,
                                 history: list[dict]) -> list[dict]:
    """Fail closed on stale/conflicting machine-readable critic correction intent.

    This is an exact feature/state guard, not a semantic contradiction detector.
    The critic must reuse stable feature IDs; paraphrases cannot be safely inferred.
    """
    match = re.search(r"<review_requirements>\s*(.*?)\s*</review_requirements>", reply, re.S)
    if not match:
        raise ValueError("Review requires revision-bound review_requirements; do not blindly apply unbound corrections.")
    requirements = json.loads(match.group(1))
    if not isinstance(requirements, list) or len(requirements) != issue_count:
        raise ValueError("Each review issue requires exactly one bound correction requirement.")
    targets = {item['source'] for item in manifest if item['role'] == 'target_building'}
    prior = {}
    for receipt in history:
        for item in receipt.get('requirements', []):
            prior.setdefault(item['feature_id'], set()).add(item['desired_state'])
    seen = {}
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("Invalid correction requirement.")
        feature = item.get('feature_id')
        desired = item.get('desired_state')
        if not isinstance(feature, str) or not re.fullmatch(r'[a-z0-9_.:/-]{1,160}', feature):
            raise ValueError("Correction requires a stable feature_id.")
        if not isinstance(desired, str) or not desired.strip() or len(desired) > 400:
            raise ValueError("Correction requires an explicit desired_state.")
        if item.get('model_revisions') != revisions:
            raise ValueError("Stale review model revision; recapture before correction.")
        if item.get('source_ref') not in targets:
            raise ValueError("Correction target proof must cite target_building, never defect/unknown screenshots.")
        if feature in seen and seen[feature] != desired:
            raise ValueError("Conflicting correction requirements; reconcile evidence before any geometry write.")
        if prior.get(feature) and desired not in prior[feature]:
            raise ValueError("Correction reverses an unresolved requirement; reconcile evidence instead of blind oscillation.")
        seen[feature] = desired
    return requirements


def load_review_history(project_dir: Path, fingerprint: str) -> list[dict]:
    path = project_dir / 'runtime/reference_role_review_history.jsonl'
    if not path.exists():
        return []
    if path.is_symlink():
        raise ValueError('Unsafe role review history.')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return [row for row in rows if row.get('manifest_fingerprint') == fingerprint]
