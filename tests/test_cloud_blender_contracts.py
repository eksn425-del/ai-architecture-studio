"""Actual cloud Blender plus deterministic host/reviewer fixtures; no model calls."""
import json
import shutil
from pathlib import Path
import pytest
from scripts.verify_cloud_blender_contracts import fixture_objects, run_native, finish_native, progress_observation


def test_repeated_facade_fixture_has_explicit_recess_and_neighbor():
    objects={row['id']:row for row in fixture_objects()}
    assert len(objects)==74
    for floor in range(3):
        assert objects[f'bay_{floor}_2_rail']['location'][1] > objects[f'bay_{floor}_0_rail']['location'][1]
    assert 'KEEP_neighbor' in objects


def test_progress_measurements_use_native_receipt_not_builder_claim():
    receipt={'revision':9,'geometry':{'rail':{'dimensions':[1,.1,.45]}}}
    observed=progress_observation(receipt,['rail'])
    assert observed['model_revisions']=={'blender_scene':9}
    assert observed['needs_fix'] is False
    assert observed['feature_states'][0]['distance_to_target']==0


@pytest.mark.skipif(not shutil.which('blender'),reason='real Blender executable required')
def test_real_blender_shared_review_and_durable_progress(tmp_path):
    initial=run_native(tmp_path/'evidence')
    evidence=finish_native(tmp_path/'evidence',initial)
    assert all(evidence['checks'].values())
    assert all(row['scene_and_native_files_unchanged'] for row in evidence['contract_denials'].values())
    assert evidence['durable_progress']['persisted_records']==2
    assert evidence['provider_calls']==0
    assert evidence['independent_llm_visual_quality']=='NOT_RUN'
