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
    attempted_source = runtime/'scripts/harness_building.rb'
    attempted_hash = hashlib.sha256(attempted_source.read_bytes()).hexdigest()
    pending={**copy.deepcopy(accepted),'durability_status':'unconfirmed','write_in_flight':True,
             'last_report':'runtime/scripts/reports/r2.json','source_sha256':attempted_hash}
    state=runtime/'project_ruby_state.json';state.write_text(json.dumps({'model_path':str(original),'scripts':{'harness_building':pending}}))
    old={'instance_id':'1234-aaaaaaaaaaaaaaaaaaaaaaaa','model_path':str(original),'model_guid':'old-guid'}
    selections={str(project.resolve()):old};roster=[];launched=[]
    monkeypatch.setattr(recovery_module,'process_exited',lambda pid:pid==1234)
    monkeypatch.setattr(pins,'lifecycle_pin',lambda *a,**kw:old)
    monkeypatch.setattr(pins,'read_selection',lambda root,p:selections.get(str(Path(p).resolve())))
    def bind(root,p,row):
        value={'schema':1,'project':str(Path(p).resolve()),'selected_at':1,
               **{key:row[key] for key in ('instance_id','model_path','model_guid')}}
        selections[str(Path(p).resolve())]=value
        return value
    monkeypatch.setattr(pins,'write_selection',bind)
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
            return {'root_geometry_material_sha256':'fixture-only-deep-hash',
                    'document_geometry_material_sha256':'fixture-only-document-hash'}
    session=SimpleNamespace(model_path=original.relative_to(project).as_posix())
    return SimpleNamespace(project=project,runtime=runtime,source=source,state=state,old=old,
        session=session,adapter=Adapter(),launch=launch,launched=launched,selections=selections,
        checkpoint=checkpoint,actual=actual,module=recovery_module,root=tmp_path/'connector',roster=roster)


def perform(f):return recover_saved_checkpoint(f.project,f.session,f.adapter,f.launch,root=f.root)


def test_recovery_retains_original_unknown_and_uses_a_new_verified_copy(recovery):
    f=recovery;before=f.state.read_bytes();original=(f.project/f.session.model_path).read_bytes()
    target,receipt=perform(f)
    assert target!=f.checkpoint and target.read_bytes()==f.checkpoint.read_bytes()
    assert receipt['uncertain_operation_replayed'] is False and receipt['original_uncertain_outcome']=='PRESERVED_UNKNOWN'
    archive=list((f.runtime/'native-recovery').glob('*/uncertain-state.private.json'))
    assert len(archive)==1 and archive[0].read_bytes()==before
    assert (f.project/'outputs/model/blank-disposable-original.skp').read_bytes()==original
    assert json.loads(f.state.read_text(encoding='utf-8'))['scripts']['harness_building']['revision']==1
    assert json.loads(f.state.read_text(encoding='utf-8'))['scripts']['harness_building']['durability_status']=='recovered_verified_checkpoint'
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
        p=f.runtime/'scripts/reports/r1.json';r=json.loads(p.read_text(encoding='utf-8'));r['project_id']='other';p.write_text(json.dumps(r))
    else:
        p=f.runtime/'previous-agent-ruby-state.json';r=json.loads(p.read_text(encoding='utf-8'));r['harness_building']['revision']=2;p.write_text(json.dumps(r))
    with pytest.raises(ValueError):perform(f)
    assert not f.launched and f.state.read_bytes()==before


def test_process_exit_before_native_report_can_recover_saved_checkpoint(recovery):
    f = recovery
    (f.runtime/'scripts/reports/r2.json').unlink()
    previous = f.state.read_bytes()
    target, receipt = perform(f)
    archive = next((f.runtime/'native-recovery').glob('*/uncertain-report.private.json'))
    assert json.loads(archive.read_text(encoding='utf-8')) == {
        'status': 'not_recorded', 'outcome': 'PRESERVED_UNKNOWN',
    }
    assert archive.with_name('uncertain-state.private.json').read_bytes() == previous
    assert receipt['uncertain_operation_replayed'] is False
    assert target.read_bytes() == f.checkpoint.read_bytes()


def test_recovery_refuses_an_uncertain_report_outside_its_project_reports(recovery):
    f = recovery
    pending = json.loads(f.state.read_bytes())
    pending['scripts']['harness_building']['last_report'] = 'runtime/previous-agent-ruby-state.json'
    f.state.write_text(json.dumps(pending), encoding='utf-8')
    before = f.state.read_bytes()
    with pytest.raises(ValueError, match='outside the owned reports'):
        perform(f)
    assert not f.launched and f.state.read_bytes() == before
    assert not (f.runtime/'native-recovery').exists()


def test_recovery_quarantines_exact_attempt_if_crash_source_bytes_later_change(recovery):
    f = recovery
    candidate = f.runtime/'scripts/harness_building.rb'
    original = hashlib.sha256(candidate.read_bytes()).hexdigest()
    candidate.write_bytes(b'changed after the original uncertain dispatch')
    changed = hashlib.sha256(candidate.read_bytes()).hexdigest()
    perform(f)
    assert f.session.ruby_state['harness_building']['quarantined_source_sha256'] == sorted([original, changed])
    assert candidate.read_bytes() == f.source.read_bytes()


def test_recovery_uses_the_last_verified_write_inside_the_same_turn(recovery):
    f = recovery
    state = json.loads(f.state.read_bytes())
    entry = state['scripts']['harness_building']
    previous_path = f.runtime/'previous-agent-ruby-state.json'
    verified = json.loads(previous_path.read_bytes())['harness_building']
    entry['recovery_base'] = verified
    entry.update(revision=2, unverified_candidate_checkpoint={'revision': 2, 'path': 'unused'})
    f.state.write_text(json.dumps(state), encoding='utf-8')
    previous_path.write_text('{}', encoding='utf-8')
    target, receipt = perform(f)
    assert receipt['restored_revision'] == verified['revision']
    assert target.read_bytes() == f.checkpoint.read_bytes()
    assert f.session.ruby_state['harness_building']['revision'] == verified['revision']
    assert 'recovery_base' not in f.session.ruby_state['harness_building']


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


@pytest.mark.parametrize('after_file',[0,1,2,3,4])
def test_process_loss_during_activation_resumes_without_replay(recovery,monkeypatch,after_file):
    """Injected host termination, not a claim of physical power-loss testing."""
    f=recovery;(f.project/'state').mkdir()
    (f.project/'state/agent_session.json').write_text(json.dumps({'model_path':f.session.model_path,'status':'error'}))
    (f.project/'state/model_state.json').write_text(json.dumps({'model_path':f.session.model_path}))
    original=f.state.read_bytes();real=f.module._atomic_bytes;count=[0]
    class PowerLoss(BaseException):pass
    def interrupt(path,data):
        # Staging happens before the journal; inject only into real destinations.
        if (f.runtime/'native-recovery/pending.json').exists() and list((f.runtime/'native-recovery').glob('*/activation.private.json')):
            if count[0]==after_file:raise PowerLoss()
            count[0]+=1
        real(path,data)
    monkeypatch.setattr(f.module,'_atomic_bytes',interrupt)
    if after_file<4:
        with pytest.raises(PowerLoss):perform(f)
    else:
        import app.connector_instances as pins
        real_pin=pins.write_selection
        def interrupted_pin(root,project,row):
            real_pin(root,project,row)
            if Path(project)==f.project:raise PowerLoss()
        monkeypatch.setattr(pins,'write_selection',interrupted_pin)
        with pytest.raises(PowerLoss):perform(f)
        monkeypatch.setattr(pins,'write_selection',real_pin)
    monkeypatch.setattr(f.module,'_atomic_bytes',real)
    # Simulate reloading stale session state after a process restart.
    fresh=SimpleNamespace(**json.loads((f.project/'state/agent_session.json').read_text(encoding='utf-8')))
    f.session=fresh
    target,receipt=perform(f)
    assert len(f.launched)==1 and receipt['uncertain_operation_replayed'] is False
    assert json.loads((f.project/'state/agent_session.json').read_text(encoding='utf-8'))['model_path']==fresh.model_path
    assert json.loads((f.project/'state/model_state.json').read_text(encoding='utf-8'))['model_path']==fresh.model_path
    assert target.read_bytes()==f.checkpoint.read_bytes()
    assert not (f.runtime/'native-recovery/pending.json').exists()
    assert list((f.runtime/'native-recovery').glob('*/uncertain-state.private.json'))[0].read_bytes()==original


def test_activation_refuses_unrelated_state_change_after_interruption(recovery,monkeypatch):
    f=recovery;real=f.module._finish_activation
    monkeypatch.setattr(f.module,'_finish_activation',lambda *a: (_ for _ in ()).throw(RuntimeError('injected interruption')))
    with pytest.raises(RuntimeError):perform(f)
    monkeypatch.setattr(f.module,'_finish_activation',real)
    f.state.write_text('{"unrelated_user_change":true}')
    with pytest.raises(ValueError,match='outside the journal'):perform(f)
    assert json.loads(f.state.read_text(encoding='utf-8'))=={'unrelated_user_change':True}


def test_unfinished_recovery_blocks_geometry_before_source_validation(tmp_path):
    from app.project_ruby import ProjectRubyExecutor
    from app.sketchup_mcp import MCPCallError
    project=tmp_path/'project';journal=project/'runtime/native-recovery/pending.json'
    journal.parent.mkdir(parents=True);journal.write_text('{}')
    executor=object.__new__(ProjectRubyExecutor);executor.project_dir=project
    with pytest.raises(MCPCallError,match='recovery is unfinished'):
        executor.run({'ruby_source':'MUST NEVER BE VALIDATED OR SENT'})


def test_native_process_also_exited_during_activation_revalidates_new_instance(recovery,monkeypatch):
    f=recovery;real=f.module._finish_activation
    monkeypatch.setattr(f.module,'_finish_activation',lambda *a: (_ for _ in ()).throw(RuntimeError('interrupt')))
    with pytest.raises(RuntimeError):perform(f)
    monkeypatch.setattr(f.module,'_finish_activation',real)
    f.roster[0]={**f.roster[0],'instance_id':'9012-cccccccccccccccccccccccc'}
    monkeypatch.setattr(f.module,'process_exited',lambda pid:pid in (1234,5678))
    target,receipt=perform(f)
    assert receipt['new_instance_id']=='9012-cccccccccccccccccccccccc'
    assert f.selections[str(f.project.resolve())]['instance_id']==receipt['new_instance_id']
    assert target.read_bytes()==f.checkpoint.read_bytes() and len(f.launched)==1


def test_stale_live_heartbeat_of_exited_native_process_is_not_a_valid_target(recovery,monkeypatch):
    f=recovery;real=f.module._finish_activation
    monkeypatch.setattr(f.module,'_finish_activation',lambda *a: (_ for _ in ()).throw(RuntimeError('interrupt')))
    with pytest.raises(RuntimeError):perform(f)
    monkeypatch.setattr(f.module,'_finish_activation',real)
    monkeypatch.setattr(f.module,'process_exited',lambda pid:True)
    def blocked_launcher(*a):raise RuntimeError('fresh native open required')
    f.launch=blocked_launcher
    with pytest.raises(RuntimeError,match='fresh native open required'):perform(f)
    assert (f.runtime/'native-recovery/pending.json').exists()
