"""Explicit semantic precision contract over complete raw native evidence.

Raw full-double collector hashes remain immutable and independently reported.
Coordinates, topology, materials and translations are NOT rounded. Only native
dimensionless face-normal and affine-linear coefficients use 12 decimal places.
The raw evidence is required again when verifying a derived receipt.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .native_graph_evidence import validate_definition_graph

CONTRACT = 'KStudioNativeStableGeometry/1'
PRECISION = {'face_normal_decimals': 12, 'affine_linear_decimals': 12,
             'coordinates_mm': 'exact native doubles',
             'translations_mm': 'exact native doubles',
             'all_other_fields': 'exact'}


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def derive_stable_geometry(raw: dict) -> dict:
    validate_definition_graph(raw)
    names = {}
    definitions = {}
    for ref, record in raw['definitions'].items():
        payload = json.loads(record['canonical_payload_json'])
        name = payload['definition_name']
        if name in names.values():
            raise ValueError('Stable geometry requires unambiguous definition names; no inferred pairing')
        names[ref] = name
        definitions[name] = payload

    changed = []
    def normalize(value, path=()):
        if isinstance(value, dict):
            return {k: names[v] if k == 'definition_ref' else normalize(v, path + (k,))
                    for k, v in value.items()}
        if isinstance(value, list):
            return [normalize(v, path + (i,)) for i, v in enumerate(value)]
        normal = len(path) > 1 and path[-2] == 'normal' and path[-1] in (0, 1, 2)
        linear = len(path) > 1 and path[-2] in ('local_transform', 'world_transform') and path[-1] in (0, 1, 2, 4, 5, 6, 8, 9, 10)
        if (normal or linear) and type(value) in (int, float):
            result = round(float(value), 12)
            result = 0.0 if result == 0 else result
            if value != result:
                changed.append({'path': list(path), 'raw': value, 'canonical': result,
                                'absolute_delta': abs(value-result)})
            return result
        return value

    payload = normalize({'definitions': definitions,
                         'document': json.loads(raw['document_canonical_json']),
                         'counts': raw['counts'],
                         'presentation_sha256': raw['presentation_sha256']})
    canonical = encode(payload)
    return {'collector': CONTRACT, 'precision': PRECISION.copy(),
            'source_collector': raw['collector'],
            'raw_document_geometry_material_sha256': raw['document_geometry_material_sha256'],
            'raw_evidence_sha256': hashlib.sha256(encode(raw).encode()).hexdigest(),
            'canonical_geometry_json': canonical,
            'geometry_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
            'normalization': {'changed_fields': len(changed),
                              'maximum_dimensionless_adjustment': max((r['absolute_delta'] for r in changed), default=0),
                              'changes': changed},
            'root_pid': raw['root_pid'], 'counts': raw['counts'],
            'raw_strict_verdict_overridden': False,
            'limitation': 'Separate declared precision contract, not raw bit equality, source fidelity, structural certification or blank replay.'}


def verify_stable_geometry(receipt: dict, raw: dict) -> None:
    if receipt != derive_stable_geometry(raw):
        raise ValueError('Stable geometry receipt is incomplete, altered or not bound to raw native evidence')


def compare_stable_geometry(before: dict, after: dict) -> dict:
    # Derive directly from validated complete raw graphs; never trust supplied
    # auxiliary SHA fields or a caller-selected precision/tolerance.
    left, right = derive_stable_geometry(before), derive_stable_geometry(after)
    return {'contract': CONTRACT, 'precision': PRECISION.copy(),
            'status': 'PASS' if left['geometry_sha256'] == right['geometry_sha256'] else 'FAIL',
            'before_sha256': left['geometry_sha256'], 'after_sha256': right['geometry_sha256'],
            'raw_document_sha_equal': before['document_geometry_material_sha256'] == after['document_geometry_material_sha256'],
            'raw_strict_verdict_overridden': False,
            'source_fidelity': 'NOT_ASSESSED', 'blank_program_replay': 'NOT_ASSESSED'}
