"""Finite host-owned execution budgets and conservative convergence checks."""
import json
import os


def geometry_stage_limit(existing: bool) -> tuple[str, int]:
    stage = 'targeted_repair' if existing else 'initial_build'
    key = 'KSTUDIO_REPAIR_GEOMETRY_LIMIT' if existing else 'KSTUDIO_INITIAL_GEOMETRY_LIMIT'
    raw = os.environ.get(key, '2' if existing else '3')
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise ValueError(f'{key} must be an integer in 1..12') from None
    if not 1 <= value <= 12:
        raise ValueError(f'{key} must be an integer in 1..12; unlimited geometry writes are not supported')
    return stage, value


def continuation_message(stage, writes, limit, reason='budget_exhausted'):
    why = '连续复核未发现问题减少' if reason == 'no_progress' else '本轮已达到安全修改上限，几何写入预算已用完'
    return (f'{why}（{stage}: {writes}/{limit}）。当前候选模型已保留，质量尚未通过验收。'
            '停止几何写入，继续只读检查并列出剩余问题；下一步须明确修复范围并确认计划后再继续。'
            '不要换对象编号、项目或重建来绕过限制。')


class ReviewProgress:
    """Exact repeated issue sets across distinct revisions, not a similarity score."""
    def __init__(self):
        self.previous = None
        self.revision = None
        self.unchanged = 0
        self.blocked = False

    def observe(self, receipt):
        if not isinstance(receipt, dict):
            return
        revision = json.dumps(receipt.get('model_revisions', {}), sort_keys=True)
        if revision == self.revision:
            return  # Re-reading one revision is not a failed correction.
        issues = receipt.get('issues') or []
        signature = sorted((str(i.get('view','')), ' '.join(str(i.get('problem','')).split())) for i in issues)
        self.unchanged = self.unchanged + 1 if receipt.get('needs_fix') is True and signature and signature == self.previous else 0
        self.previous, self.revision = signature, revision
        self.blocked = self.unchanged >= 2


def geometry_diagnostics(objects):
    """Diagnostic-only exact duplicate boxes / full coincident faces in world metres.

    Does not infer intended joins, topology, architectural meaning or fidelity.
    Shared touching faces may be intentional. Never repairs geometry.
    """
    boxes, faces, issues = {}, {}, []
    checked = 0
    truncated = False
    for name, obj in sorted(objects.items()):
        loc = obj['location']
        if 'dimensions' in obj:
            low = tuple(loc[i]-obj['dimensions'][i]/2 for i in range(3))
            high = tuple(loc[i]+obj['dimensions'][i]/2 for i in range(3))
            bounds = (low, high)
            if bounds in boxes:
                issues.append({'kind':'duplicate_box_volume','objects':[boxes[bounds],name], 'severity':'review_required'})
            boxes[bounds] = name
            vertices = [(x,y,z) for x in (low[0],high[0]) for y in (low[1],high[1]) for z in (low[2],high[2])]
            polygons = [[v for v in vertices if v[axis] == edge] for axis in range(3) for edge in (low[axis],high[axis])]
        else:
            vertices = [tuple(v[i]+loc[i] for i in range(3)) for v in obj['vertices']]
            polygons = [[vertices[i] for i in face] for face in obj['faces']]
        for polygon in polygons:
            if checked >= 50000:
                truncated = True
                break
            checked += 1
            key = tuple(sorted(set(polygon)))
            if key in faces:
                issues.append({'kind':'coincident_full_face','objects':[faces[key],name], 'severity':'review_required'})
            else:
                faces[key] = name
        if truncated:
            break
    return {'status':'review_required' if issues else 'no_findings_in_supported_checks',
            'issues':issues, 'checked_faces':checked, 'truncated':truncated,
            'candidate_status':'saved_candidate', 'quality_status':'unverified',
            'limitations':['Exact full-face matching only; no partial coplanar overlap detection.',
                          'Shared faces may be intended joins; gaps require explicit connection intent.',
                          'No image similarity, structural safety, watertightness or architectural acceptance.']}
