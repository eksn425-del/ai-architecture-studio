import hashlib
import json
from copy import deepcopy

import pytest

from app.native_graph_evidence import GRAPH_COLLECTOR, validate_definition_graph
from scripts.audit_native_delivery_stages import audit_stages
from scripts.compare_native_replay import compare


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def encode(value):
    raw = json.dumps(value, separators=(',', ':'))
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def graph(*, mirrored_second=False, leaf_color=None, omitted_boundary=False, normal_x=0, linear_offset=0, translation_offset=0, vertex_offset=0):
    points = [[0, 0, 0], [1000, 0, 0], [1000, 1000, 0], [0, 1000, 0]]
    points[2][0] += vertex_offset
    edges = [{'endpoints': sorted([points[i], points[(i+1) % 4]]), 'hidden': False, 'soft': False, 'smooth': False, 'tag': None} for i in range(4)]
    if omitted_boundary:
        edges.pop()
    leaf = {'definition_name': 'PanelDefinition', 'faces_local_mm': [{'loops': [{'outer': True, 'points': points}], 'normal': [normal_x, 0, 1], 'front': leaf_color, 'back': None, 'hidden': False, 'tag': None}], 'edges_local_mm': edges, 'sections': [], 'instances': []}
    leaf_raw, leaf_sha = encode(leaf)

    def instance(name, ref, mirrored=False):
        transform = IDENTITY.copy()
        transform[1] = linear_offset
        transform[12] = translation_offset
        if mirrored:
            transform[0] = -1
        return {'type': 'Group', 'name': name, 'definition_name': 'RootDefinition' if name == 'Architecture case' else 'PanelDefinition', 'definition_ref': ref, 'local_transform': transform, 'material': None, 'hidden': False, 'locked': False, 'tag': None}

    children = [instance('PANEL_0', leaf_sha), instance('PANEL_1', leaf_sha, mirrored_second)]
    root_proto = {'definition_name': 'RootDefinition', 'faces_local_mm': [], 'edges_local_mm': [], 'sections': [], 'instances': children}
    root_raw, root_sha = encode(root_proto)
    root_geometry = instance('Architecture case', root_sha)
    leaf_counts = {'faces': 1, 'edges': len(edges), 'instances': 0}
    counts = {'faces': 2, 'edges': len(edges)*2, 'instances': 2}

    def node(item, pid, count):
        raw, sha = encode({'instance': item, 'world_transform': item['local_transform']})
        return {'name': item['name'], 'pid': pid, 'definition_ref': item['definition_ref'], 'counts': count, 'canonical_geometry_json': raw, 'geometry_material_sha256': sha}

    root = node(root_geometry, 1, counts)
    doc_raw, doc_sha = encode({'faces': [], 'edges': [], 'sections': [], 'nodes': [root_geometry]})
    return {'collector': GRAPH_COLLECTOR, 'complete_reference_graph': True, 'unique_entities_visited': 8, 'definition_count': 2, 'definitions': {leaf_sha: {'canonical_payload_json': leaf_raw, 'counts': leaf_counts, 'depth': 0}, root_sha: {'canonical_payload_json': root_raw, 'counts': counts, 'depth': 1}}, 'document_canonical_json': doc_raw, 'document_geometry_material_sha256': doc_sha, 'document_instances': [{'pid': 1, 'geometry': root_geometry}], 'document_loose': {'faces': [], 'edges': [], 'sections': []}, 'root_instance': root, 'root_pid': 1, 'counts': counts, 'root_geometry_material_sha256': root['geometry_material_sha256'], 'groups': [node(child, i+2, leaf_counts) for i, child in enumerate(children)], 'presentation_sha256': 'a'*64}


def test_shared_prototype_preserves_every_instance_and_strict_three_stage_equality():
    before = graph()
    validate_definition_graph(before)
    assert before['counts'] == {'faces': 2, 'edges': 8, 'instances': 2}
    assert audit_stages(before, deepcopy(before), deepcopy(before), require_deep=True)['status'] == 'PASS'


def test_roundoff_diagnosis_does_not_override_strict_failure():
    from app.native_graph_roundoff import diagnose_roundoff
    before, after = graph(), graph(normal_x=2e-16, linear_offset=2e-16)
    result = diagnose_roundoff(before, after)
    assert result['status'] == 'DIMENSIONLESS_ROUNDOFF_ONLY'
    assert not result['strict_acceptance_overridden'] and not result['strict_equality']
    assert audit_stages(before, after, after, require_deep=True)['status'] == 'FAIL'


@pytest.mark.parametrize('kwargs', [{'linear_offset': 1e-9}, {'mirrored_second': True}, {'leaf_color': {'name': 'changed'}}])
def test_roundoff_diagnosis_rejects_real_changes(kwargs):
    from app.native_graph_roundoff import diagnose_roundoff
    result = diagnose_roundoff(graph(), graph(**kwargs))
    assert result['status'] == 'GEOMETRIC_OR_METADATA_DIFFERENCE'
    assert result['failures']


def test_stable_precision_is_separate_and_binds_all_raw_evidence():
    from app.native_stable_geometry import derive_stable_geometry, verify_stable_geometry, compare_stable_geometry
    before, after = graph(), graph(normal_x=2e-16, linear_offset=2e-16)
    assert compare_stable_geometry(before, after)['status'] == 'PASS'
    assert audit_stages(before, after, after, require_deep=True)['status'] == 'FAIL'
    receipt = derive_stable_geometry(after)
    verify_stable_geometry(receipt, after)
    assert receipt['normalization']['changed_fields'] > 0
    receipt['precision']['face_normal_decimals'] = 3
    with pytest.raises(ValueError):
        verify_stable_geometry(receipt, after)


@pytest.mark.parametrize('kwargs', [{'linear_offset': 1e-9}, {'mirrored_second': True}, {'leaf_color': {'name': 'changed'}}, {'translation_offset': 1e-16}, {'vertex_offset': 1e-9}])
def test_stable_precision_rejects_real_mutations(kwargs):
    from app.native_stable_geometry import compare_stable_geometry
    assert compare_stable_geometry(graph(), graph(**kwargs))['status'] == 'FAIL'


@pytest.mark.parametrize('fault', ['missing_definition', 'tampered_payload', 'wrong_counts', 'omitted_group', 'omitted_document_instance', 'false_complete', 'nonfinite', 'extra_definition'])
def test_partial_or_tampered_factored_evidence_cannot_pass(fault):
    bad = graph()
    ref = bad['groups'][0]['definition_ref']
    if fault == 'missing_definition':
        del bad['definitions'][ref]
        bad['definition_count'] -= 1
    elif fault == 'tampered_payload':
        bad['definitions'][ref]['canonical_payload_json'] += ' '
    elif fault == 'wrong_counts':
        bad['definitions'][ref]['counts']['faces'] = 999
    elif fault == 'omitted_group':
        bad['groups'].pop()
    elif fault == 'omitted_document_instance':
        bad['document_instances'].clear()
    elif fault == 'false_complete':
        bad['complete_reference_graph'] = False
    elif fault == 'nonfinite':
        bad['groups'][0]['canonical_geometry_json'], bad['groups'][0]['geometry_material_sha256'] = encode({'instance': json.loads(bad['groups'][0]['canonical_geometry_json'])['instance'], 'world_transform': [float('nan')]*16})
    else:
        bad['definitions']['f'*64] = deepcopy(bad['definitions'][ref])
        bad['definition_count'] += 1
    with pytest.raises(ValueError):
        validate_definition_graph(bad)
    assert audit_stages(graph(), bad, graph(), require_deep=True)['status'] == 'BLOCKED'


def test_face_edges_cannot_be_dropped_even_with_rehashed_graph_and_adjusted_counts():
    with pytest.raises(ValueError, match='boundary edges omitted'):
        validate_definition_graph(graph(omitted_boundary=True))


def test_same_counts_detect_one_instance_mirror_and_shared_definition_material_change():
    original = graph()
    mirrored = graph(mirrored_second=True)
    assert original['counts'] == mirrored['counts']
    result = compare(original, mirrored)
    assert result['status'] == 'FAIL'
    assert [x['name'] for x in result['changed_groups']] == ['PANEL_1']
    colored = graph(leaf_color={'name': 'red', 'rgba': [255, 0, 0, 1]})
    result = compare(original, colored)
    assert result['status'] == 'FAIL' and len(result['changed_groups']) == 2


def test_different_collectors_are_never_interchangeable():
    a = graph(); b = deepcopy(a); b['collector'] = 'KStudioNativeDeepFingerprint/1'
    result = audit_stages(a, b, a, require_deep=True)
    assert result['status'] == 'BLOCKED' and result['reason'] == 'native_fingerprint_representation_mismatch'
