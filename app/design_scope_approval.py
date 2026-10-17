"""Host-only displayed-plan and current-reference approval binding.

No functions in this module are exposed as Builder tools. The conversation host
must capture after successful planning and call approval only for an explicit
user approval action, never an inferred auto/execution request.
"""
import hashlib
import json
from pathlib import Path
from .reference_roles import (parse_design_scope, record_approved_design_scope,
    load_approved_design_scope, reference_manifest, manifest_fingerprint, canonical_plan_text)


def _path(project, name):
    p = project / 'runtime' / name
    if p.is_symlink() or p.parent.is_symlink():
        raise ValueError('Unsafe approval state path.')
    return p


def _save(project, name, value):
    p = _path(project, name);p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix('.tmp')
    if temp.is_symlink():raise ValueError('Unsafe approval temporary path.')
    temp.write_text(json.dumps(value, ensure_ascii=False))
    temp.replace(p)


def current_reference_fingerprint(project: Path) -> str:
    context_path = project / 'state/project_context.json'
    if context_path.is_symlink():raise ValueError('Unsafe project context.')
    context = json.loads(context_path.read_text()) if context_path.exists() else {}
    paths = []
    for ref in context.get('references', []):
        if ref.get('type') != 'image':continue
        relative = ref.get('source', '')
        if not relative.startswith('inputs/reference/'):continue
        p = project / relative
        if p.is_symlink() or not p.resolve().is_relative_to(project.resolve()):
            raise ValueError('Unsafe reference path.')
        if not p.is_file():raise ValueError('Reference image missing; approval invalid.')
        paths.append(p)
    return manifest_fingerprint(reference_manifest(project, paths))


def _invalidate(project, reason):
    scope = load_approved_design_scope(project)
    if scope and (scope.get('features') or scope.get('valid', True)):
        # Preserve audit history and version; do not silently reset approval epoch.
        log = _path(project, 'design_scope_invalidations.jsonl')
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a') as stream:
            stream.write(json.dumps({'reason':reason,'previous_scope':scope}, ensure_ascii=False)+'\n')
        _save(project, 'approved_design_scope.json', {**scope,'features':[], 'valid':False,'invalidation_reason':reason})


def invalidate_stale_design_scope(project_dir: Path) -> bool:
    scope = load_approved_design_scope(project_dir)
    if not scope or not scope.get('features'):return False
    try:
        current = current_reference_fingerprint(project_dir)
    except (ValueError, OSError):
        _invalidate(project_dir, 'references_unavailable')
        raise
    if scope.get('reference_manifest_fingerprint') != current:
        _invalidate(project_dir, 'reference_or_role_changed')
        return True
    return False


def capture_pending_design_plan(project_dir: Path, plan_text: str, *, is_followup: bool) -> dict:
    plan_text = canonical_plan_text(plan_text)
    _invalidate(project_dir, 'new_plan_pending')
    features = parse_design_scope(plan_text) if is_followup else []
    snapshot = {'plan_sha256':hashlib.sha256(plan_text.encode()).hexdigest(),
                'features':features, 'is_followup':bool(is_followup),
                'reference_manifest_fingerprint':current_reference_fingerprint(project_dir)}
    _save(project_dir, 'pending_design_scope.json', snapshot)
    return snapshot


def approve_pending_design_plan(project_dir: Path, approval_message_id: str,
                                plan_text: str, approved_plan_sha256: str) -> dict:
    plan_text = canonical_plan_text(plan_text)
    path = _path(project_dir, 'pending_design_scope.json')
    if not path.exists():
        raise ValueError('Plan has no host snapshot; refresh and review the plan first.')
    snapshot = json.loads(path.read_text())
    digest = hashlib.sha256(plan_text.encode()).hexdigest()
    if digest != snapshot.get('plan_sha256') or approved_plan_sha256 != digest or not approval_message_id:
        _invalidate(project_dir, 'plan_approval_mismatch')
        raise ValueError('Approve the unchanged displayed plan; stale or missing approval hash.')
    if current_reference_fingerprint(project_dir) != snapshot.get('reference_manifest_fingerprint'):
        _invalidate(project_dir, 'reference_or_role_changed')
        raise ValueError('Reference images or roles changed after planning; refresh the plan.')
    if not snapshot.get('is_followup') or not snapshot.get('features'):
        _invalidate(project_dir, 'initial_or_unscoped_plan')
        return {}  # Initial approval never authorizes overriding historical intent.
    if parse_design_scope(plan_text) != snapshot['features']:
        raise ValueError('Displayed feature scope changed.')
    scope = record_approved_design_scope(project_dir, approval_message_id, plan_text, snapshot['features'])
    if scope.get('valid') is False:
        raise ValueError('This approval was invalidated; approve a fresh plan.')
    scope = {**scope,'reference_manifest_fingerprint':snapshot['reference_manifest_fingerprint'],'valid':True}
    _save(project_dir, 'approved_design_scope.json', scope)
    return scope
