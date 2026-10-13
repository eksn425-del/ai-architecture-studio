from pathlib import Path

def test_committed_snapshot_is_after_commit_not_provisional():
    source=Path('app/vendor/sketchup_architect/scripts/model_session.rb').read_text(encoding='utf8')
    assert source.index('record[:owned_precommit]') < source.index('unless model.commit_operation')
    assert source.index('unless model.commit_operation') < source.index('record[:owned_after]')
    assert 'model.find_entity_by_persistent_id(committed_root_pid)' in source
    assert 'Committed owned root missing' in source

def test_recovery_checkpoint_refreshes_guid_before_agent_bootstrap():
    source=Path('app/main.py').read_text(encoding='utf8')
    checkpoint=source.index('"Pre-turn recovery checkpoint", expected_root_ids=roots')
    refresh=source.index('checkpoint_identity = adapter.get_active_model_identity()',checkpoint)
    invoke=source.index('result = app.state.model_router.respond(',checkpoint)
    assert checkpoint < refresh < invoke
    assert 'Checkpoint changed the active disposable document.' in source[refresh:invoke]
import copy
import pytest
from app.modeling_quality import recover_empty_container_verification

def test_recovery_only_accepts_missing_empty_containers():
    b={'min':[0,0,0],'max':[2,3,4],'size':[2,3,4]}
    good={'persistent_id':1,'name':'wall','locked':False,'bounds_mm':b}
    empty={'persistent_id':2,'name':'WALLS','locked':False,'bounds_mm':{'size':[0,0,0]}}
    tx={'status':'committed','owned_after':{'objects_total':2,'bounds_mm':b,'objects':[good,empty]}}
    rd={'persistent_id':10,'revision':1,'objects_total':1,'bounds_mm':b,'objects':[good]}
    assert recover_empty_container_verification(tx,rd,root_pid=10,revision=1)['verified']
    assert tx['owned_after']['objects_total']==2
    for mutation in ('nonempty','changed','added','revision','bounds'):
        t=copy.deepcopy(tx);r=copy.deepcopy(rd)
        if mutation=='nonempty': t['owned_after']['objects'][1]['bounds_mm']['size']=[1,1,1]
        if mutation=='changed': r['objects'][0]['name']='altered'
        if mutation=='added': r['objects'][0]['persistent_id']=999
        if mutation=='revision': r['revision']=2
        if mutation=='bounds': r['bounds_mm']['max']=[3,4,5]
        with pytest.raises(ValueError): recover_empty_container_verification(t,r,root_pid=10,revision=1)

def test_verified_model_turn_uses_compact_project_restart():
    from app.native_agent import _native_thread_can_resume, _thread_tool_fingerprint
    registered = {'old': _thread_tool_fingerprint([])}
    fingerprint = 'source-sha-bound'
    registry = {'old': fingerprint}
    # Preserve the legacy compact fresh-thread default after a committed root.
    assert not _native_thread_can_resume('old', registered, registry, [], fingerprint,
                                         compact_restart=True, native_mode=False)
    # Native pilot is explicit and only with verified same photos+tool inventory.
    assert _native_thread_can_resume('old', registered, registry, [], fingerprint,
                                     compact_restart=True, native_mode=True)
    assert not _native_thread_can_resume('old', registered, registry, [], 'changed',
                                         compact_restart=True, native_mode=True)
