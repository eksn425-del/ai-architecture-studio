"""Host-only, opt-in scope contract for project-owned Blender writes.

Not an Agent tool or inference approval. A host explicitly binds allowed IDs to
one scene revision and current user intent. Missing policy preserves legacy
behavior; malformed or stale policy fails closed. No authorization is inferred.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')

def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def _path(project):
    path = Path(project) / 'runtime/blender/edit_contract.json'
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Unsafe Blender edit contract path')
    return path

def _intent(project):
    from .design_scope_approval import current_execution_instruction, current_reference_fingerprint
    from .reference_roles import load_approved_design_scope
    p = Path(project) / 'state/project_context.json'
    if p.is_symlink():
        raise ValueError('Unsafe Blender project context')
    context = json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    users = [m for m in context.get('conversation', []) if m.get('role') == 'user']
    return _hash({'instruction': current_execution_instruction(Path(project)),
                  'latest_user': users[-1] if users else None,
                  'scope': load_approved_design_scope(Path(project)),
                  'references': context.get('references', []),
                  'reference_fingerprint': current_reference_fingerprint(Path(project))})

def _save(project, value):
    path = _path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    if tmp.is_symlink():
        raise ValueError('Unsafe Blender contract temporary path')
    tmp.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)

def install(project, scene, *, allowed_ids, keep_ids, expected_revision):
    if type(expected_revision) is not int or expected_revision != scene.get('revision', 0):
        raise ValueError('Blender edit contract scene revision mismatch')
    for values in (allowed_ids, keep_ids):
        if not isinstance(values, list) or len(values) > 2048 or any(not isinstance(v, str) or not _NAME.fullmatch(v) for v in values) or len(set(values)) != len(values):
            raise ValueError('Invalid Blender contract object IDs')
    if not allowed_ids or set(allowed_ids) & set(keep_ids):
        raise ValueError('Blender edit scope must be nonempty and disjoint from KEEP')
    objects = scene.get('objects', {})
    if not set(keep_ids) <= set(objects):
        raise ValueError('Blender KEEP object is missing')
    # Every pre-existing object outside allowed scope is protected, not just
    # the explicit KEEP list. New IDs must also be explicitly allowed.
    protected = sorted(set(objects) - set(allowed_ids))
    value = {'schema': 1, 'revision': expected_revision, 'allowed_ids': sorted(allowed_ids),
             'keep_ids': sorted(keep_ids), 'intent': _intent(project),
             'protected_specs': {k: _hash(objects[k]) for k in protected},
             'protected_geometry': {k: _hash(scene.get('geometry', {}).get(k)) for k in protected}}
    _save(project, value)
    return value

def validate(project, scene, touched):
    path = _path(project)
    if not path.exists():
        return None
    try:
        contract = json.loads(path.read_text(encoding='utf-8'))
        expected_keys = {'schema', 'revision', 'allowed_ids', 'keep_ids', 'intent', 'protected_specs', 'protected_geometry'}
        if not isinstance(contract, dict) or set(contract) != expected_keys:
            raise ValueError('Invalid Blender host edit contract fields')
        for name in ('allowed_ids', 'keep_ids'):
            ids = contract[name]
            if (not isinstance(ids, list) or len(ids) > 2048
                    or any(not isinstance(v, str) or not _NAME.fullmatch(v) for v in ids)
                    or len(ids) != len(set(ids))):
                raise ValueError('Invalid Blender host edit contract IDs')
        if (not contract['allowed_ids'] or set(contract['allowed_ids']) & set(contract['keep_ids'])
                or type(contract['revision']) is not int or contract['revision'] < 0
                or type(contract['schema']) is not int):
            raise ValueError('Invalid Blender host edit contract scope')
        protected = set(scene.get('objects', {})) - set(contract['allowed_ids'])
        if not set(contract['keep_ids']) <= protected:
            raise ValueError('Invalid Blender host KEEP binding')
        for name in ('protected_specs', 'protected_geometry'):
            hashes = contract[name]
            if (not isinstance(hashes, dict) or set(hashes) != protected
                    or any(not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{64}', v) for v in hashes.values())):
                raise ValueError('Invalid Blender protected object binding')
        valid = (contract['schema'] == 1 and contract['revision'] == scene.get('revision', 0)
                 and contract['intent'] == _intent(project))
        if not valid:
            raise ValueError('Blender edit contract is stale; host must rebind current intent and revision')
        if not set(touched) <= set(contract['allowed_ids']):
            raise ValueError('Blender write outside host-approved edit scope / KEEP')
        for key, expected in contract['protected_specs'].items():
            if key not in scene.get('objects', {}) or _hash(scene['objects'][key]) != expected:
                raise ValueError('Blender protected scene state changed')
        return contract
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid Blender host edit contract') from error

def verify_result(contract, objects, geometry):
    if contract is None:
        return
    for key, expected in contract['protected_specs'].items():
        if key not in objects or _hash(objects[key]) != expected:
            raise ValueError('Blender protected object changed; candidate not committed')
        if _hash(geometry.get(key)) != contract['protected_geometry'][key]:
            raise ValueError('Blender native KEEP geometry changed; candidate not committed')

def advance(project, contract, revision):
    if contract is not None:
        # Called after scene commit: a crash before this write leaves a stale
        # contract that blocks continuation, never silently broadens scope.
        _save(project, {**contract, 'revision': revision})
