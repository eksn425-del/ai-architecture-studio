"""Host-owned image provenance. Unknown legacy images are never target truth."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROLES = {"target_building", "defect_location", "supporting", "unknown"}



def current_model_revisions(project_dir: Path, fallback: dict | None = None) -> dict[str, int]:
    backend_path = project_dir / "state/modeling_backend.json"
    if backend_path.is_file() and json.loads(backend_path.read_text(encoding="utf-8")).get("backend") == "blender":
        scene = project_dir / "runtime/blender/scene.json"
        if scene.is_symlink():
            raise ValueError("Unsafe model revision state.")
        revision = int(json.loads(scene.read_text(encoding="utf-8")).get("revision", 0)) if scene.exists() else 0
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


def requirement_id(item: dict) -> str:
    """Host-derived identity; changing prose/revision creates a traceable successor."""
    body = {k: item.get(k) for k in ('feature_id', 'desired_state', 'source_ref', 'model_revisions')}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]


def requirement_states(history: list[dict]) -> dict[str, dict]:
    active = {}
    for row in history:
        for resolution in row.get('resolutions', []):
            old = active.get(resolution.get('feature_id'))
            if old and old['requirement_id'] == resolution.get('prior_requirement_id'):
                active[resolution['feature_id']] = {**old, 'status':'resolved'}
        for raw in row.get('requirements', []):
            item = dict(raw)
            item['requirement_id'] = requirement_id(item)
            item['status'] = 'active'
            active[item['feature_id']] = item
    return active


def active_requirements(history: list[dict]) -> dict[str, dict]:
    return {key:item for key,item in requirement_states(history).items() if item['status']=='active'}


def parse_design_scope(plan_text: str) -> list[dict]:
    matches = re.findall(r'<design_scope>\s*(.*?)\s*</design_scope>', plan_text, re.S)
    if not matches:
        return []
    if len(matches) != 1:
        raise ValueError('Plan must contain one explicit design scope.')
    values = json.loads(matches[0])
    if not isinstance(values, list) or not 1 <= len(values) <= 64:
        raise ValueError('Design scope requires 1..64 explicitly displayed features.')
    seen = set()
    for value in values:
        if not isinstance(value, dict) or set(value) != {'feature_id', 'requested_state'}:
            raise ValueError('Design scope requires feature_id and requested_state only.')
        if not isinstance(value['feature_id'], str) or not re.fullmatch(r'[a-z0-9_.:/-]{1,160}', value['feature_id']) or value['feature_id'] in seen:
            raise ValueError('Invalid or duplicate design feature.')
        if not isinstance(value['requested_state'], str) or not 1 <= len(value['requested_state'].strip()) <= 400:
            raise ValueError('Design feature requires explicit requested state.')
        seen.add(value['feature_id'])
    return values


def load_approved_design_scope(project_dir: Path) -> dict:
    path = project_dir / 'runtime/approved_design_scope.json'
    if path.is_symlink():
        raise ValueError('Unsafe approved design scope.')
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def canonical_plan_text(text: str) -> str:
    """UTF-8 hash contract shared with browser: CRLF and CR become LF only."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def record_approved_design_scope(project_dir: Path, approval_message_id: str,
                                 plan_text: str, displayed_features: list[dict]) -> dict:
    """Host UI approval only. Never call from a Builder tool or inferred intent.

    Caller must check explicit approval of the unchanged host-snapshotted plan and
    that displayed_features were actually shown before this approval.
    """
    plan_text = canonical_plan_text(plan_text)
    features = parse_design_scope(plan_text)
    if not features or features != displayed_features or not approval_message_id:
        raise ValueError('An unchanged displayed scoped plan and explicit approval are required.')
    previous = load_approved_design_scope(project_dir)
    digest = hashlib.sha256(plan_text.encode()).hexdigest()
    if previous.get('approval_message_id') == approval_message_id:
        if previous.get('plan_sha256') != digest:
            raise ValueError('Approval message cannot authorize a changed plan.')
        return previous
    value = {'version': previous.get('version', 0) + 1, 'approval_message_id': approval_message_id,
             'plan_sha256': digest, 'plan_text': plan_text, 'features': features}
    path = project_dir / 'runtime/approved_design_scope.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    if temporary.is_symlink():
        raise ValueError('Unsafe design scope temporary file.')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return value


def validate_review_resolutions(reply: str, *, manifest: list[dict], revisions: dict,
                                history: list[dict]) -> list[dict]:
    matches = re.findall(r'<requirement_resolutions>\s*(.*?)\s*</requirement_resolutions>', reply, re.S)
    if not matches:
        return []  # Omission never resolves an old requirement.
    if len(matches) != 1:
        raise ValueError('Duplicate requirement resolutions.')
    values = json.loads(matches[0]); active = active_requirements(history)
    targets = {item['source'] for item in manifest if item['role'] == 'target_building'}
    if not isinstance(values, list) or len(values) > 64:
        raise ValueError('Invalid requirement resolutions.')
    seen = set()
    for item in values:
        if not isinstance(item, dict):
            raise ValueError('Invalid resolution.')
        prior = active.get(item.get('feature_id'))
        if (not prior or item.get('prior_requirement_id') != prior['requirement_id']
                or item.get('feature_id') in seen or item.get('status') != 'resolved'
                or item.get('source_ref') not in targets or item.get('model_revisions') != revisions
                or not isinstance(item.get('evidence'), str) or not item['evidence'].strip()):
            raise ValueError('Resolution requires current independent evidence and exact active requirement identity.')
        seen.add(item['feature_id'])
    return values


def validate_review_requirements(reply: str, *, manifest: list[dict], revisions: dict, issue_count: int,
                                 history: list[dict], approved_scope: dict | None = None) -> list[dict]:
    """Validate independent Critic relations, not exact prose equality.

    Evidence-backed equivalent/refines relations are Critic judgments, not a host
    semantic proof. Typed intent changes and explicit conflicts require a scoped
    host user approval. Builder-supplied approval fields are never trusted.
    """
    matches = re.findall(r'<review_requirements>\s*(.*?)\s*</review_requirements>', reply, re.S)
    if len(matches) != 1:
        raise ValueError('Review requires revision-bound review_requirements; do not blindly apply unbound corrections.')
    requirements = json.loads(matches[0])
    if not isinstance(requirements, list) or len(requirements) != issue_count:
        raise ValueError('Each review issue requires exactly one bound correction requirement.')
    targets = {item['source'] for item in manifest if item['role'] == 'target_building'}
    prior = requirement_states(history)
    scope = approved_scope or {}
    features = {item['feature_id']: item['requested_state'] for item in scope.get('features', [])}
    seen = set()
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError('Invalid correction requirement.')
        feature, desired = item.get('feature_id'), item.get('desired_state')
        if not isinstance(feature, str) or not re.fullmatch(r'[a-z0-9_.:/-]{1,160}', feature):
            raise ValueError('Correction requires a stable feature_id.')
        if not isinstance(desired, str) or not desired.strip() or len(desired) > 400:
            raise ValueError('Correction requires an explicit desired_state.')
        if item.get('model_revisions') != revisions:
            raise ValueError('Stale review model revision; recapture before correction.')
        if item.get('source_ref') not in targets:
            raise ValueError('Correction target proof must cite target_building, never defect/unknown screenshots.')
        if feature in seen:
            raise ValueError('Conflicting correction requirements; one active requirement per feature is allowed.')
        seen.add(feature)
        intent = item.get('intent')
        if intent is not None and (not isinstance(intent, dict) or set(intent) != {'property', 'value'}
                or not isinstance(intent['property'], str) or not isinstance(intent['value'], (str, bool, int, float))):
            raise ValueError('Intent must be a stable property/value pair.')
        old = prior.get(feature)
        relation = item.get('relation', 'unchanged' if old and desired == old['desired_state'] else 'new')
        if old:
            changed = desired != old['desired_state'] or (old.get('intent') is not None and intent != old.get('intent'))
            if changed:
                if item.get('prior_requirement_id') != old['requirement_id'] or not isinstance(item.get('evidence'), str) or not item['evidence'].strip():
                    raise ValueError('Correction reverses or refines an unresolved requirement; supply exact prior identity and current evidence.')
                intent_changed = old.get('intent') is not None and intent != old.get('intent')
                if relation in {'equivalent', 'refines'} and not intent_changed:
                    pass
                elif (relation == 'supersedes' and scope.get('version', 0) > old.get('design_scope_version', 0)
                      and item.get('design_scope_version') == scope.get('version')
                      and feature in features and item.get('approved_requested_state') == features[feature]):
                    pass
                else:
                    raise ValueError(
                        'Correction reverses an unresolved requirement; reconcile evidence or approve a scoped design change. '
                        f'feature={feature}; relation={relation}; desired_state_changed={desired != old["desired_state"]}; '
                        f'intent_changed={intent_changed}; prior_requirement_id={old["requirement_id"]}; '
                        f'prior_revisions={json.dumps(old.get("model_revisions", {}), sort_keys=True)}; '
                        f'current_revisions={json.dumps(revisions, sort_keys=True)}. '
                        'For the same intent with changed wording, the independent reviewer must explicitly use '
                        'equivalent/refines with the exact prior identity and current evidence; do not bypass approval for changed intent.'
                    )
            elif relation not in {'unchanged', 'equivalent', 'refines', 'regression'}:
                raise ValueError('Invalid relation to active requirement.')
            item['prior_requirement_id'] = old['requirement_id']
        elif relation != 'new':
            raise ValueError('No active prior requirement for this relation.')
        if relation == 'regression' and (not old or old.get('status') != 'resolved' or not item.get('evidence')):
            raise ValueError('Regression requires a previously resolved feature and current evidence.')
        item['relation'] = relation
        item['status'] = 'active'
        item['design_scope_version'] = scope.get('version', 0) if relation == 'supersedes' or old is None else old.get('design_scope_version', 0)
        item['requirement_id'] = requirement_id(item)
    return requirements


def load_review_history(project_dir: Path, fingerprint: str) -> list[dict]:
    path = project_dir / 'runtime/reference_role_review_history.jsonl'
    if not path.exists():
        return []
    if path.is_symlink():
        raise ValueError('Unsafe role review history.')
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return [row for row in rows if row.get('manifest_fingerprint') == fingerprint]
