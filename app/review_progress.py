"""Durable advisory convergence evidence, not a geometry or semantic oracle.

Structured reviewer feature identities survive paraphrasing. Legacy prose is only
matched after whitespace/case normalization: unknown equivalence never proves a
failed repair. Changing a measurement alone does not establish improvement.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile


def _key(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def current_progress_context_fingerprint(project_dir):
    """Goal/source scope, excluding per-turn IDs and starting model revisions.

    Review checkpoint reuse intentionally uses a stricter fingerprint. Progress
    continuity must not reset merely because the same request starts a new turn.
    Different instruction text is conservatively a different goal: this is not
    an attempt to infer arbitrary natural-language semantic equivalence.
    """
    from .review_context import review_intent_context, review_context_fingerprint
    from .reference_assets import discover_project_reference_images
    from .reference_roles import reference_manifest, manifest_fingerprint
    manifest = reference_manifest(project_dir,
        discover_project_reference_images(project_dir, categories=('reference',)))
    intent = review_intent_context(project_dir)
    instruction = intent['current_user_instruction']
    return review_context_fingerprint({
        'target_manifest_fingerprint': manifest_fingerprint(
            [row for row in manifest if row['role'] == 'target_building']),
        'approved_design_scope': intent['approved_design_scope'],
        'current_user_instruction': ' '.join(str(instruction.get('user_message', '')).split())})


def _features(receipt, previous):
    reviewer = receipt.get('reviewer') or {}
    rows = reviewer.get('review_requirements')
    if isinstance(rows, list):
        # Requirements are validated upstream by the independent-review contract.
        # Preserve omitted requirements: omission is not evidence of resolution.
        features = dict(previous or {})
        resolved = False
        for row in reviewer.get('requirement_resolutions') or []:
            fid = row.get('feature_id')
            old = features.get(fid)
            if (old and row.get('status') == 'resolved'
                    and row.get('model_revisions') == receipt['model_revisions']
                    and row.get('prior_requirement_id') == old.get('requirement_id')):
                del features[fid]
                resolved = True
        for row in rows:
            if (not isinstance(row, dict) or not row.get('feature_id')
                    or not row.get('desired_state') or not row.get('requirement_id')
                    or row.get('model_revisions') != receipt['model_revisions']):
                return None, False
            fid = row['feature_id']
            old = features.get(fid)
            identity = row.get('intent') or row['desired_state']
            if (old and row.get('relation') in {'unchanged', 'equivalent', 'refines'}
                    and row.get('prior_requirement_id') == old.get('requirement_id')):
                identity = old['identity']
            features[fid] = {'identity': identity, 'requirement_id': row['requirement_id']}
        return features, resolved
    # No guessed embedding/fuzzy semantic equivalence for old receipts.
    features = {}
    for issue in receipt.get('issues') or []:
        if not isinstance(issue, dict):
            return None, False
        problem = ' '.join(str(issue.get('problem', '')).casefold().split())
        if problem:
            key = _key(['legacy', str(issue.get('view', '')).casefold(), problem])
            features[key] = {'identity': key, 'requirement_id': None}
    return features, bool(previous and set(features) < set(previous))


class ReviewProgress:
    """Stop on evidenced stagnation/cycles, independent of optional write caps.

    A state file belongs to one host-selected goal/source fingerprint. Revisions
    are observation IDs, not scope keys. This preserves history across prepares
    and process restarts without counting repeated reads as repair attempts.
    """
    def __init__(self, state_path: Path | None = None, *, context_fingerprint='legacy'):
        self.path = Path(state_path) if state_path is not None else None
        self.context = str(context_fingerprint)
        self.records = []
        self.unchanged = 0
        self.blocked = False
        self.reason = None
        self.advisory_stagnation = False
        if self.path is not None and self.path.exists():
            try:
                self._safe_path()
                data = json.loads(self.path.read_text(encoding='utf-8'))
                if data['schema_version'] != 1:
                    raise ValueError('Unsupported progress schema')
                if data['context_fingerprint'] == self.context:
                    if (not isinstance(data['records'], list) or any(
                            not isinstance(row, dict) or not isinstance(row.get('revision'), str)
                            or not isinstance(row.get('signature'), str)
                            or not isinstance(row.get('features'), dict)
                            or any(not isinstance(feature, dict) or 'identity' not in feature
                                   for feature in row['features'].values())
                            for row in data['records'])):
                        raise ValueError('Invalid progress records')
                    self.records = data['records']
                    self.unchanged = int(data['unchanged'])
                    self.blocked = bool(data['blocked'])
                    self.reason = data.get('reason')
                    self.advisory_stagnation = bool(data.get('advisory_stagnation'))
            except (OSError, ValueError, KeyError, TypeError):
                self.blocked = True
                self.reason = 'progress_state_unreadable'

    def _safe_path(self):
        if any(p.is_symlink() for p in [self.path, *self.path.parents]):
            raise ValueError('Progress state must not use symlinks')

    def _save(self):
        if self.path is None:
            return
        self._safe_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {'schema_version': 1, 'context_fingerprint': self.context,
                'records': self.records, 'unchanged': self.unchanged,
                'blocked': self.blocked, 'reason': self.reason,
                'advisory_stagnation': self.advisory_stagnation}
        fd, temp = tempfile.mkstemp(prefix='.review-progress-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(data, stream, ensure_ascii=False, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def observe(self, receipt, *, host_observation=None):
        if self.reason == 'progress_state_unreadable' or not isinstance(receipt, dict):
            return
        revisions = receipt.get('model_revisions')
        if (not isinstance(revisions, dict) or not revisions
                or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in revisions.values())):
            return
        revision = _key(revisions)
        if any(row['revision'] == revision for row in self.records):
            return
        previous = self.records[-1]['features'] if self.records else None
        features, improved = _features(receipt, previous)
        if features is None or receipt.get('needs_fix') not in (True, False):
            return
        if receipt['needs_fix'] is False and features and isinstance((receipt.get('reviewer') or {}).get('review_requirements'), list):
            return  # ACCEPTED wording cannot silently resolve protected requirements.
        if receipt['needs_fix'] and not features:
            return  # Incomplete structured review cannot prove resolution.
        identities = {key: row['identity'] for key, row in features.items()}
        signature = hashlib.sha256(_key(identities).encode()).hexdigest()
        comparable = previous is not None and identities == {key: row['identity'] for key, row in previous.items()}
        geometry = None
        if (isinstance(host_observation, dict)
                and host_observation.get('model_revisions') == revisions
                and isinstance(host_observation.get('geometry_sha256'), str)
                and re.fullmatch(r'[0-9a-f]{64}', host_observation['geometry_sha256'])):
            geometry = host_observation['geometry_sha256']
        cycle = any(row['signature'] == signature for row in self.records[:-1])
        if receipt['needs_fix'] is False or improved:
            self.unchanged, self.blocked, self.reason = 0, False, None
            self.advisory_stagnation = False
        else:
            self.unchanged = self.unchanged + 1 if comparable else 0
            self.advisory_stagnation = self.unchanged >= 2 or cycle
            # Same unresolved goal/prose is NOT unchanged geometry. A host
            # current readback must independently establish the outcome repeat.
            matching = [row for row in self.records
                        if row['signature'] == signature and row.get('geometry') == geometry]
            self.blocked = bool(geometry and matching and self.advisory_stagnation)
            self.reason = 'verified_outcome_repeat' if self.blocked else None
        self.records.append({'revision': revision, 'signature': signature,
                             'features': features, 'geometry': geometry})
        try:
            self._save()
        except (OSError, ValueError):
            self.blocked, self.reason = True, 'progress_state_unreadable'
            raise
