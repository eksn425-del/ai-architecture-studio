"""Quantify native reopen roundoff separately from strict hash acceptance.

This NEVER turns a strict delivery/replay FAIL into PASS. All vertices, topology,
materials and translations must remain exact. Only sub-1e-14 differences in face
normals and affine linear coefficients receive a separately named diagnosis.
"""
from __future__ import annotations

import json
from typing import Any

from .native_graph_evidence import validate_definition_graph


def diagnose_roundoff(before: dict, after: dict) -> dict:
    out: dict[str, Any] = {
        'status': 'BLOCKED', 'strict_equality': False,
        'strict_acceptance_overridden': False, 'dimensionless_absolute_limit': 1e-14,
        'differences': [], 'failures': [],
    }
    try:
        validate_definition_graph(before)
        validate_definition_graph(after)
        def pool(value):
            result = {}
            refs = {}
            for ref, record in value['definitions'].items():
                payload = json.loads(record['canonical_payload_json'])
                name = payload['definition_name']
                if name in result:
                    raise ValueError('Ambiguous definition names; no inferred pairing allowed')
                result[name] = payload
                refs[ref] = name
            return result, refs

        left, lrefs = pool(before)
        right, rrefs = pool(after)
        def resolve(value, refs):
            if isinstance(value, dict):
                return {k: refs[v] if k == 'definition_ref' else resolve(v, refs)
                        for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v, refs) for v in value]
            return value

        def compare(x, y, path=()):
            if isinstance(x, dict) and isinstance(y, dict) and x.keys() == y.keys():
                for k in sorted(x):
                    compare(x[k], y[k], path + (k,))
            elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
                for i, (u, v) in enumerate(zip(x, y)):
                    compare(u, v, path + (i,))
            elif x != y:
                numeric = (type(x) in (float, int) and type(y) in (float, int))
                normal = len(path) >= 2 and path[-2] == 'normal' and path[-1] in (0, 1, 2)
                linear = len(path) >= 2 and path[-2] in ('local_transform', 'world_transform') and path[-1] in (0, 1, 2, 4, 5, 6, 8, 9, 10)
                delta = abs(x-y) if numeric else None
                row = {'path': list(path), 'before': x, 'after': y, 'absolute_delta': delta}
                if numeric and (normal or linear) and delta <= 1e-14:
                    out['differences'].append(row)
                else:
                    out['failures'].append(row)

        compare(resolve(left, lrefs), resolve(right, rrefs), ('definitions',))
        compare(resolve(json.loads(before['document_canonical_json']), lrefs),
                resolve(json.loads(after['document_canonical_json']), rrefs), ('document',))
        for key in ('counts', 'root_pid', 'presentation_sha256'):
            compare(before[key], after[key], (key,))
        # Preserve the original graph SHA verdict independently of this diagnosis.
        out['strict_equality'] = before['document_geometry_material_sha256'] == after['document_geometry_material_sha256']
        out['difference_count'] = len(out['differences'])
        out['maximum_dimensionless_delta'] = max((r['absolute_delta'] for r in out['differences']), default=0)
        out['status'] = ('EXACT' if out['strict_equality'] else 'DIMENSIONLESS_ROUNDOFF_ONLY') if not out['failures'] else 'GEOMETRIC_OR_METADATA_DIFFERENCE'
        out['vertices_topology_materials_translation_exact'] = not out['failures']
        out['limitation'] = 'Diagnostic comparison only; strict replay/delivery SHA verdict remains unchanged. No visual, structural or customer-readiness acceptance.'
    except (ValueError, KeyError, TypeError) as exc:
        out['failures'].append(str(exc))
    return out
