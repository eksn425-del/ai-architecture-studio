"""A six-view proposal cannot silently discard views or invalidate old approvals."""
import copy
import json

import pytest

from app.k_architecture import ArchitectureContext, digest, validate_graph, specs


def proposal(coverage=True):
    graph = {
        'summary': '同一栋建筑的多视角、楼梯细节和无标注屋顶总平图联合解读',
        'facts': [{'text': '外罩与后退玻璃为独立系统', 'basis': 'observed', 'source': 'source_1'}],
        'levels': [{'name': 'ground', 'z_mm': 0, 'role': 'ground'}],
        'parts': ['Shell', 'Glazing', 'Stairs', 'Roof'],
        'relationships': ['楼梯平台连接对应楼层，外罩与玻璃保持间距'],
        'edit_parts': ['Shell', 'Glazing', 'Stairs', 'Roof'],
    }
    if coverage:
        graph['source_coverage'] = [
            {'source': f'source_{i}', 'role': 'plan' if i == 6 else 'overall',
             'use': 'used', 'evidence': '屋顶平面用于外轮廓配准，无标注尺度' if i == 6 else '与同一外角和玻璃退界对应的建筑视角'}
            for i in range(1, 7)
        ]
    return graph


def context(tmp_path, stage='plan'):
    images = []
    for i in range(6):
        path = tmp_path / f'image-{i}.png'
        if not path.exists():
            path.write_bytes(f'reference-{i}'.encode())
        images.append(path)
    return ArchitectureContext(tmp_path, stage, images, [], {})


def test_new_six_view_plan_requires_every_source_before_persisting(tmp_path):
    ctx = context(tmp_path)
    with pytest.raises(ValueError, match='source_coverage'):
        ctx.save_graph(proposal(False))
    assert not ctx.graph_path.exists()
    graph = proposal()
    # An unreadable/occluded view is explicit uncertainty, not fabricated observation.
    graph['source_coverage'][4].update(use='unresolved', evidence='此视角被遮挡，无法确认背面开口和结构关系')
    ctx.save_graph(graph)
    ctx.card.parent.mkdir(parents=True, exist_ok=True)
    ctx.card.write_text('按六图核对的方案；尺度为推定。', encoding='utf-8')
    ctx.bind_plan()
    assert context(tmp_path, 'execute').execution_parts() == set(graph['parts'])


@pytest.mark.parametrize('mistake', ['omitted', 'duplicate', 'filename', 'empty_reason', 'invalid_role', 'invalid_use'])
def test_invalid_coverage_cannot_overwrite_accepted_proposal(tmp_path, mistake):
    ctx = context(tmp_path)
    ctx.save_graph(proposal())
    accepted = ctx.graph_path.read_bytes()
    bad = copy.deepcopy(proposal())
    rows = bad['source_coverage']
    if mistake == 'omitted': rows.pop()
    if mistake == 'duplicate': rows[-1]['source'] = 'source_1'
    if mistake == 'filename': rows[-1]['source'] = 'image-5.png'
    if mistake == 'empty_reason': rows[-1]['evidence'] = ' '
    if mistake == 'invalid_role': rows[-1]['role'] = []
    if mistake == 'invalid_use': rows[-1]['use'] = 'verified_geometry'
    with pytest.raises(ValueError): ctx.save_graph(bad)
    assert ctx.graph_path.read_bytes() == accepted


def test_legacy_multiview_approval_resumes_without_retroactive_schema_rejection(tmp_path):
    ctx = context(tmp_path, 'execute')
    old = proposal(False)
    ctx.graph_path.write_text(json.dumps(old), encoding='utf-8')
    ctx.card.parent.mkdir(parents=True, exist_ok=True)
    ctx.card.write_text('历史已批准方案', encoding='utf-8')
    ctx.receipt_path.write_text(json.dumps({
        'graph_sha256': digest(old), 'plan_sha256': digest(ctx.card.read_bytes()),
        'sources': ctx.images, 'edit_parts': old['edit_parts'], 'approval_granted': False}), encoding='utf-8')
    assert ctx.execution_parts() == set(old['edit_parts'])
    # New proposals cannot borrow that legacy exemption.
    with pytest.raises(ValueError, match='source_coverage'): context(tmp_path).save_graph(old)


def test_tool_schema_accepts_the_six_view_payload_without_granting_native_permission():
    from jsonschema import Draft202012Validator
    schema = next(s['inputSchema'] for s in specs('plan') if s['name'] == 'kstudio_save_design_graph')
    Draft202012Validator(schema).validate(proposal())
    validate_graph(proposal(), {f'source_{i}' for i in range(1, 7)}, require_source_coverage=True)
    assert not any(s['name'].startswith('sketchup_run') for s in specs('plan'))
