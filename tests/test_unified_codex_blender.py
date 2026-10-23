"""Scripted App Server transport + actual Blender; not actual model inference."""
import copy
import json
import os
import shutil

import pytest

from scripts.verify_cloud_blender_contracts import fixture_objects
from scripts.verify_unified_codex_blender import run, scenarios, target_edits


def test_controlled_unified_scenario_is_exact_and_does_not_mutate_source():
    objects = fixture_objects()
    original = copy.deepcopy(objects)
    edits = target_edits({obj['id']: obj for obj in objects})
    assert len(edits) == 6
    assert objects == original
    assert all(obj['dimensions'][2] == .45 for obj in edits)
    assert all('KEEP' not in obj['id'] for obj in edits)
    script = scenarios(objects)
    assert len(script) == 7
    assert script['EDIT'][0]['foreign'] is True
    assert {call['call_id'] for call in script['EDIT']} >= {'hostile-delete', 'hostile-update', 'hostile-add', 'render-edit', 'exact-detail'}


@pytest.mark.skipif(os.name != 'posix' or not shutil.which('blender'),
                    reason='POSIX scripted subprocess and actual Blender executable required')
def test_public_codex_responses_route_drives_real_blender(tmp_path):
    pytest.importorskip('litellm')
    evidence = run(tmp_path / 'unified-blender')
    assert all(evidence['checks'].values())
    assert evidence['route']['provider'] == 'codex-responses'
    assert evidence['operations']['native_revisions'] == [1, 2]
    assert evidence['operations']['objects'] == 74
    assert evidence['operations']['preserved'] == 68
    assert len(evidence['guard_denials']) == 7
    assert evidence['native_render_attachment_count'] == 1
    assert evidence['returned_image_sha256'] == [evidence['native_render_sha256']]
    assert evidence['paid_cost'] == 'NOT_INCURRED'
    assert evidence['responses_http_sse'] == 'NOT_TESTED_BY_THIS_SCRIPT'
    assert 'FIXTURE' in evidence['usage']['basis']
    recorded = json.loads((tmp_path / 'unified-blender/evidence.json').read_text())
    assert recorded == evidence


def test_rejects_overwriting_existing_evidence(tmp_path):
    (tmp_path / 'keep').write_text('immutable')
    with pytest.raises(ValueError, match='fresh output'):
        run(tmp_path)
    assert (tmp_path / 'keep').read_text() == 'immutable'
