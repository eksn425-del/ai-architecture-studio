"""Real local HTTP API and Blender, not paid/model-quality coverage."""
import shutil
import pytest
from scripts.verify_api_driven_blender import target_edits, run, run_detail_probe
from scripts.verify_cloud_blender_contracts import fixture_objects


def test_scripted_target_edits_are_bounded_and_do_not_mutate_fixture():
    objects={o['id']:o for o in fixture_objects()}
    edits=target_edits(objects)
    assert len(edits)==6
    assert all(o['dimensions'][2]==.45 for o in edits)
    assert all(objects[o['id']]['dimensions'][2]==.6 for o in edits)
    assert all('KEEP' not in o['id'] for o in edits)


@pytest.mark.skipif(not shutil.which('blender'),reason='real Blender required')
def test_api_drives_real_blender_through_product_router(tmp_path):
    pytest.importorskip('litellm')
    evidence=run(tmp_path/'api-blender')
    assert all(evidence['checks'].values())
    assert evidence['http_request_count']==13
    assert evidence['model_response_count']==13
    assert set(evidence['native_wire_receipts'])=={'build','read-build','edit-six','read-edit','render-edit'}
    assert all(row['native_reopen']=='PASS' for key,row in evidence['native_wire_receipts'].items() if key!='render-edit')
    assert all(row['objects_with_explicit_topology_omission']==74 for key,row in evidence['native_wire_receipts'].items() if key!='render-edit')
    assert len(evidence['raw_journal_receipts'])==4
    detail=run_detail_probe(tmp_path/'api-blender/project',tmp_path/'detail-probe')
    assert detail['http_request_count']==2 and detail['native_vertices']==8
    assert detail['primary_13_response_comparison_includes_this_probe'] is False
    assert evidence['native_render_forwarded_after_tool'] is True
    assert evidence['native_render_attachment_count']>0
    assert evidence['source_image_attachment_count']>0
    assert evidence['render_tool_image_attachment_count']==1
    assert evidence['estimated_input_tokens']>0
    assert evidence['operations']['native_revisions']==[1,2]
    assert evidence['paid_cost']=='NOT_INCURRED'
