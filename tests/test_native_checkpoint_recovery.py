"""Failure-injected host recovery contracts; opaque bytes are NOT native SKP proof."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.native_checkpoint_recovery import recover_saved_checkpoint


@pytest.fixture
def recovery(tmp_path,monkeypatch):
    import app.connector_instances as pins
    import app.native_checkpoint_recovery as recovery_module
    project=tmp_path/'projects/case';runtime=project/'runtime'
    reports=runtime/'scripts/reports';reports.mkdir(parents=True)
    checkpoint=project/'outputs/model/committed-revisions/r1.skp';checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'opaque durable checkpoint fixture, never a real SKP')
    original=checkpoint.parent.parent/'blank-disposable-original.skp';original.write_bytes(b'original uncertain model is retained')
    source=reports/'r1.committed.rb';source.write_text('accepted fixture source')
    (runtime/'scripts/harness_building.rb').write_text('failed candidate fixture source')
    bounds={'min':[0,0,0],'max':[1,2,3],'size':[1,2,3]}
    saved={'status':'saved_unverified_reopen','path':checkpoint.relative_to(project).as_posix(),
        'sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),'revision':1,'root_pid':19}
    accepted={'revision':1,'root_pid':19,'durability_status':'saved_unverified_reopen',
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'last_report':'runtime/scripts/reports/r1.json',
        'durable_checkpoint':saved,'last_verification':{'verified':True,'checks':[
            {'check':'objects_total','actual':8},{'check':'bounds_mm','actual':bounds}]}}
    (reports/'r1.json').write_text(json.dumps({'status':'committed','project_id':'case','revision':1,'root_pid':19}))
    (reports/'r2.json').write_text(json.dumps({'status':'prepared'}))
    (runtime/'previous-agent-ruby-state.json').write_text(json.dumps({'harness_building':accepted}))
    pending={**copy.deepcopy(accepted),'durability_status':'unconfirmed','write_in_flight':True,'last_report':'runtime/scripts/reports/r2.json'}
    state=runtime/'project_ruby_state.json';state.write_text(json.dumps({'model_path':str(original),'scripts':{'harness_building':pending}}))
    old={'instance_id':'1234-aaaaaaaaaaaaaaaaaaaaaaaa','model_path':str(original),'model_guid':'old-guid'}
    selections={str(project.resolve()):old};roster=[];launched=[]
    monkeypatch.setattr(recovery_module,'process_exited',lambda pid:True)
    monkeypatch.setattr(pins,'lifecycle_pin',lambda *a,**kw:old)
    monkeypatch.setattr(pins,'read_selection',lambda root,p:selections.get(str(Path(p).resolve())))
    monkeypatch.setattr(pins,'write_selection',lambda root,p,row:selections.update({str(Path(p).resolve()):row}))
    monkeypatch.setattr(pins,'instances',lambda root:roster)
    def launch(*args):
        target=args[-1];launched.append(target)
        roster.append({'status':'live','instance_id':'5678-bbbbbbbbbbbbbbbbbbbbbbbb','model_path':str(target),'model_guid':'new-guid'})
    actual={'read_only':True,'revision':1,'persistent_id':19,'objects_total':8,'bounds_mm':bounds}
    class Executor:
        def __init__(self,*args,**kwargs):assert kwargs['ruby_state']['harness_building']['revision']==1
        def inspect_owned(self,args):return {'contentItems':[{'text':json.dumps(actual)}]}
    monkeypatch.setattr('app.project_ruby.ProjectRubyExecutor',Executor)
    identity=lambda:{'model_path':roster[0]['model_path'],'model_guid':'new-guid','instance_id':roster[0]['instance_id'],'main_thread':True,'active_context':False}
    class Adapter:
        client=object()
        def get_active_model_identity(self):return identity()
        def capture_native_deep_fingerprint(self,**kwargs):
            kwargs['output_path'].write_text('{"fixture_only":true}')
            return {'root_geometry_material_sha256':'fixture-only-deep-hash'}
    session=SimpleNamespace(model_path=original.relative_to(project).as_posix())
    return SimpleNamespace(project=project,runtime=runtime,source=source,state=state,old=old,
        session=session,adapter=Adapter(),launch=launch,launched=launched,selections=selections,
        checkpoint=checkpoint,actual=actual,module=recovery_module,root=tmp_path/'connector')


def perform(f):return recover_saved_checkpoint(f.project,f.session,f.adapter,f.launch,root=f.root)


def test_recovery_retains_original_unknown_and_uses_a_new_verified_copy(recovery):
    f=recovery;before=f.state.read_bytes();original=(f.project/f.session.model_path).read_bytes()
    target,receipt=perform(f)
    assert target!=f.checkpoint and target.read_bytes()==f.checkpoint.read_bytes()
    assert receipt['uncertain_operation_replayed'] is False and receipt['original_uncertain_outcome']=='PRESERVED_UNKNOWN'
    archive=list((f.runtime/'native-recovery').glob('*/uncertain-state.private.json'))
    assert len(archive)==1 and archive[0].read_bytes()==before
    assert (f.project/'outputs/model/blank-disposable-original.skp').read_bytes()==original
    assert json.loads(f.state.read_text())['scripts']['harness_building']['revision']==1
    assert json.loads(f.state.read_text())['scripts']['harness_building']['durability_status']=='recovered_verified_checkpoint'
    assert (f.runtime/'scripts/harness_building.rb').read_bytes()==f.source.read_bytes()
    assert f.session.status=='ready' and len(f.launched)==1
    blocked=f.session.ruby_state['harness_building']['quarantined_source_sha256']
    assert hashlib.sha256(b'failed candidate fixture source').hexdigest() in blocked


@pytest.mark.parametrize('fault',['alive','checkpoint_hash','revision','source','report_owner'])
def test_invalid_recovery_fails_before_launch_and_preserves_quarantine(recovery,monkeypatch,fault):
    f=recovery;before=f.state.read_bytes()
    if fault=='alive':monkeypatch.setattr(f.module,'process_exited',lambda pid:False)
    elif fault=='checkpoint_hash':f.checkpoint.write_bytes(b'altered')
    elif fault=='source':f.source.unlink()
    elif fault=='report_owner':
        p=f.runtime/'scripts/reports/r1.json';r=json.loads(p.read_text());r['project_id']='other';p.write_text(json.dumps(r))
    else:
        p=f.runtime/'previous-agent-ruby-state.json';r=json.loads(p.read_text());r['harness_building']['revision']=2;p.write_text(json.dumps(r))
    with pytest.raises(ValueError):perform(f)
    assert not f.launched and f.state.read_bytes()==before


def test_failed_native_readback_preserves_guard_then_reuses_same_pending_copy(recovery):
    f=recovery;before=f.state.read_bytes();f.actual['revision']=2
    with pytest.raises(ValueError,match='readback'):perform(f)
    assert f.state.read_bytes()==before and f.selections[str(f.project.resolve())]==f.old
    f.actual['revision']=1;target,receipt=perform(f)
    assert len(f.launched)==1 and receipt['restored_revision']==1


def test_old_process_reappearing_before_activation_keeps_original_guard(recovery,monkeypatch):
    f=recovery;before=f.state.read_bytes();checks=iter([True,False])
    monkeypatch.setattr(f.module,'process_exited',lambda pid:next(checks))
    with pytest.raises(ValueError,match='changed'):perform(f)
    assert f.state.read_bytes()==before
