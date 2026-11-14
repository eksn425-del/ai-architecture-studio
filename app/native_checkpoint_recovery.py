"""Explicit recovery into a NEW copy after the old native process exited.

The uncertain operation, model, journal and failed source stay quarantined.
This never retries it or clears its original outcome. Only a hash-verified
previous durable checkpoint can become the current document after native proof.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
import re
import shutil
import time
import uuid
from pathlib import Path


def process_exited(pid):
    if os.name!='nt' or type(pid) is not int or pid<=0:return False
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x00100000,False,pid)  # SYNCHRONIZE, no mutation rights
    if not handle:return ctypes.get_last_error()==87  # invalid PID; access denied is NOT exit
    try:return kernel.WaitForSingleObject(handle,0)==0
    finally:kernel.CloseHandle(handle)


def regular(path,root):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Recovery file is missing or outside the project')
    return path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_bytes(path, data):
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def _finish_activation(project,session,adapter,root,pending_file,attempt,launcher):
    """Resume a journaled multi-file activation; never execute model source.

    All destinations must still contain either the journal's old or new bytes.
    A writer is blocked while this journal exists. Native identity/deep evidence
    is checked again on every continuation, including after a host restart.
    """
    from .connector_instances import instances,path_key,read_selection,write_selection,project_scope
    from .public_connector import atomic_write
    folder=(project/attempt['folder']).resolve()
    journal=json.loads(regular(folder/'activation.private.json',project/'runtime').read_text(encoding='utf8'))
    target=regular(project/attempt['target'],project/'outputs/model')
    checkpoint=regular(project/journal['checkpoint'],project/'outputs/model/committed-revisions')
    if sha(target)!=attempt['checkpoint_sha256'] or sha(checkpoint)!=attempt['checkpoint_sha256']:
        raise ValueError('Recovery activation model/checkpoint bytes changed')
    old=journal['old_selection'];candidate=journal['candidate']
    if not process_exited(int(old['instance_id'].split('-')[0])):
        raise ValueError('Original uncertain process has not exited')
    selected=read_selection(root,project)
    def same_pin(left,right):
        return (isinstance(left,dict) and left.get('instance_id')==right.get('instance_id')
            and left.get('model_guid')==right.get('model_guid')
            and path_key(left.get('model_path'))==path_key(right.get('model_path')))
    if selected!=old and not any(same_pin(selected,row) for row in [candidate,*journal.get('prior_candidates',[])]):
        raise ValueError('Recovery activation selection changed')
    rows=[r for r in instances(root) if r['status']=='live' and r['instance_id']==candidate['instance_id']
          and path_key(r.get('model_path'))==path_key(target) and r.get('model_guid')==candidate['model_guid']]
    # Signed heartbeats can remain within their TTL after a process exits.
    # Do not send an audit to a dead process solely because discovery is fresh.
    if process_exited(int(candidate['instance_id'].split('-')[0])):rows=[]
    if len(rows)>1:raise ValueError('Ambiguous recovery native instance')
    replacement=None
    if not rows:
        if not process_exited(int(candidate['instance_id'].split('-')[0])):
            raise ValueError('Recovery native process is alive but unavailable; no second writer')
        def matching():return [r for r in instances(root) if r['status']=='live' and path_key(r.get('model_path'))==path_key(target)
            and not process_exited(int(r['instance_id'].split('-')[0]))]
        rows=matching()
        if not rows:
            launcher(project.name,project.parent.parent,target)
            deadline=time.monotonic()+50
            while time.monotonic()<deadline:
                rows=matching()
                if rows:break
                time.sleep(.25)
        if len(rows)!=1 or rows[0]['model_guid']!=candidate['model_guid']:
            raise ValueError('Restarted recovery needs one unchanged checkpoint document')
        replacement=rows[0]
    active_candidate=replacement or candidate
    staged=[]
    for item in journal['files']:
        destination=regular(project/item['destination'],project)
        new=regular(folder/item['new_file'],folder).read_bytes()
        if hashlib.sha256(new).hexdigest()!=item['new_sha256']:
            raise ValueError('Recovery activation staged bytes changed')
        if sha(destination) not in (item['old_sha256'],item['new_sha256']):
            raise ValueError('Recovery activation destination changed outside the journal')
        staged.append((destination,new))
    probe=folder/'probe';write_selection(root,probe,active_candidate)
    with project_scope(probe):
        identity=adapter.get_active_model_identity()
        if (path_key(identity.get('model_path'))!=path_key(target) or identity.get('model_guid')!=active_candidate['model_guid']
            or identity.get('instance_id')!=active_candidate['instance_id'] or identity.get('active_context')
            or identity.get('main_thread') is not True):raise ValueError('Recovery activation native identity changed')
        deep=adapter.capture_native_deep_fingerprint(expected_model_path=target,expected_guid=identity['model_guid'],
            root_pid=journal['receipt']['native_readback']['persistent_id'],
            output_path=folder/('activation-deep-'+uuid.uuid4().hex+'.private.json'))
        if deep['root_geometry_material_sha256']!=journal['receipt']['root_geometry_material_sha256']:
            raise ValueError('Recovery activation native geometry changed')
        expected_document=journal['receipt'].get('document_geometry_material_sha256')
        if not expected_document or deep.get('document_geometry_material_sha256')!=expected_document:
            raise ValueError('Recovery activation complete document changed or is unverified')
        if adapter.get_active_model_identity()!=identity:raise ValueError('Native identity changed during activation audit')
    if (sha(target)!=attempt['checkpoint_sha256'] or sha(checkpoint)!=attempt['checkpoint_sha256']
        or read_selection(root,project)!=selected or not process_exited(int(old['instance_id'].split('-')[0]))):
        raise ValueError('Recovery activation evidence changed before persistence')
    for item,(destination,_) in zip(journal['files'],staged):
        if sha(destination) not in (item['old_sha256'],item['new_sha256']):
            raise ValueError('Recovery activation destination changed during native verification')
    if replacement:
        journal.setdefault('prior_candidates',[]).append(candidate)
        journal['candidate']=replacement
        journal['receipt']['new_instance_id']=replacement['instance_id']
        atomic_write(folder/'activation.private.json',journal)
        candidate=replacement
    for destination,new in staged:_atomic_bytes(destination,new)
    write_selection(root,project,candidate)
    for key,value in journal['session_patch'].items():setattr(session,key,value)
    atomic_write(folder/'activation-completed.private.json',{'status':'complete','at':time.time()})
    pending_file.rename(folder/'completed-request.private.json')
    return target,journal['receipt']


def recover_saved_checkpoint(project,session,adapter,launcher,*,root=None):
    from .connector_instances import lifecycle_pin,instances,path_key,write_selection,read_selection,project_scope
    from .public_connector import root_dir,atomic_write
    from .project_ruby import SCRIPT_ID_RE, ProjectRubyExecutor
    project=Path(project).resolve();root=Path(root or root_dir())
    pending_file=project/'runtime/native-recovery/pending.json'
    if pending_file.exists():
        attempt=json.loads(regular(pending_file,project/'runtime').read_text(encoding='utf8'))
        folder=(project/attempt['folder']).resolve()
        if not folder.is_relative_to((project/'runtime/native-recovery').resolve()):
            raise ValueError('Invalid recovery journal folder')
        if (folder/'activation.private.json').exists():
            return _finish_activation(project,session,adapter,root,pending_file,attempt,launcher)
    old=lifecycle_pin(project,root=root)
    if not old:raise ValueError('Recovery requires the original signed instance selection')
    old_pid=int(old['instance_id'].split('-')[0])
    if not process_exited(old_pid):raise ValueError('The uncertain native process is still running; do not reopen or replay')
    state_path=regular(project/'runtime/project_ruby_state.json',project/'runtime')
    state_sha=sha(state_path);uncertain=json.loads(state_path.read_text(encoding='utf8'))
    current=(project/session.model_path).resolve()
    if path_key(current)!=path_key(old['model_path']) or path_key(uncertain.get('model_path'))!=path_key(current):
        raise ValueError('Uncertain document identity changed')
    scripts=uncertain.get('scripts',{})
    if len(scripts)!=1:raise ValueError('Recovery currently requires one owned building root')
    script_id,pending=next(iter(scripts.items()))
    if not isinstance(script_id, str) or not SCRIPT_ID_RE.fullmatch(script_id):
        raise ValueError('Uncertain script identity is invalid')
    if pending.get('durability_status')!='unconfirmed':raise ValueError('No uncertain native write to recover')
    saved=pending.get('durable_checkpoint',{})
    if saved.get('status')!='saved_unverified_reopen' or not isinstance(saved.get('sha256'),str):
        raise ValueError('No previously confirmed durable checkpoint')
    checkpoint=regular(project/saved.get('path',''),project/'outputs/model/committed-revisions')
    if sha(checkpoint)!=saved['sha256']:raise ValueError('Durable checkpoint hash changed')
    previous_revision = pending.get('recovery_base')
    if previous_revision is not None:
        previous = {script_id: previous_revision}
    else:
        # Previously installed clients only recorded the pre-turn snapshot.
        previous_path=regular(project/'runtime/previous-agent-ruby-state.json',project/'runtime')
        previous=json.loads(previous_path.read_text(encoding='utf8'))
    accepted=previous.get(script_id,{})
    if (set(previous)!={script_id} or not isinstance(accepted, dict)
        or accepted.get('durability_status')=='unconfirmed'
        or accepted.get('write_in_flight') or accepted.get('revision')!=saved.get('revision')
        or accepted.get('root_pid')!=saved.get('root_pid')
        or accepted.get('last_verification',{}).get('verified') is not True
        or accepted.get('durable_checkpoint',{}).get('sha256')!=saved['sha256']):
        raise ValueError('Previous state does not match the durable checkpoint')
    report=regular(project/accepted.get('last_report',''),project/'runtime/scripts/reports')
    committed=json.loads(report.read_text(encoding='utf8'))
    if (committed.get('status')!='committed' or committed.get('project_id')!=project.name
        or committed.get('revision')!=saved['revision'] or committed.get('root_pid')!=saved['root_pid']):
        raise ValueError('Checkpoint ownership/commit evidence missing')
    source_candidates=list((project/'runtime/scripts/reports').glob('*.committed.rb'))
    source=next((f for f in source_candidates if not f.is_symlink() and sha(f)==accepted.get('source_sha256')),None)
    if source is None:raise ValueError('Accepted checkpoint source is unavailable')
    attempted_sha = pending.get('source_sha256')
    if not isinstance(attempted_sha, str) or not re.fullmatch(r'[a-f0-9]{64}', attempted_sha):
        raise ValueError('Uncertain source digest is unavailable')
    # The host persists intent before SketchUp creates its report. Validate
    # the path first so a failure leaves the previous state and no orphan copy.
    report_path = project / str(pending.get('last_report') or '')
    report_root = project / 'runtime/scripts/reports'
    if (report_path.is_symlink() or not report_path.resolve().is_relative_to(report_root.resolve())
            or not report_root.resolve().is_relative_to(project)
            or report_path == report_root or report_path.suffix != '.json'):
        raise ValueError('Uncertain report path is outside the owned reports')
    failed_source = regular(project/'runtime/scripts'/f'{script_id}.rb', project/'runtime/scripts')
    pending_file=project/'runtime/native-recovery/pending.json'
    if pending_file.exists():
        attempt=json.loads(regular(pending_file,project/'runtime').read_text(encoding='utf8'))
        if attempt.get('uncertain_state_sha256')!=state_sha or attempt.get('checkpoint_sha256')!=saved['sha256']:
            raise ValueError('A different recovery is already pending')
        folder=(project/attempt['folder']).resolve();target=(project/attempt['target']).resolve()
        regular(target,project/'outputs/model')
    else:
        identifier=uuid.uuid4().hex
        folder=project/'runtime/native-recovery'/identifier;folder.mkdir(parents=True)
        target=project/'outputs/model'/('blank-disposable-recovery-'+identifier+'.skp')
        shutil.copyfile(checkpoint,target)
        attempt={'schema_version':1,'folder':folder.relative_to(project).as_posix(),
            'target':target.relative_to(project).as_posix(),'uncertain_state_sha256':state_sha,
            'checkpoint_sha256':saved['sha256'],'old_instance_id':old['instance_id'],'old_process_exited':True}
        shutil.copyfile(state_path,folder/'uncertain-state.private.json')
        if report_path.exists():
            shutil.copyfile(regular(report_path, report_root), folder/'uncertain-report.private.json')
        else:
            atomic_write(folder/'uncertain-report.private.json', {
                'status': 'not_recorded', 'outcome': 'PRESERVED_UNKNOWN',
            })
        shutil.copyfile(failed_source,folder/'failed-source.rb')
        atomic_write(pending_file,attempt)
    if sha(target)!=saved['sha256'] or sha(checkpoint)!=saved['sha256']:
        raise ValueError('Recovery copy no longer matches the durable checkpoint')
    def candidates():return [i for i in instances(root) if i['status']=='live' and path_key(i.get('model_path'))==path_key(target)]
    rows=candidates()
    if not rows:launcher(project.name,project.parent.parent,target)
    deadline=time.monotonic()+50
    while time.monotonic()<deadline:
        rows=candidates()
        if rows:break
        time.sleep(.25)
    if len(rows)!=1 or rows[0]['instance_id']==old['instance_id']:
        raise ValueError('The new recovery document has not opened in a unique fresh instance')
    candidate=rows[0];probe=folder/'probe';probe.mkdir(exist_ok=True)
    write_selection(root,probe,candidate)
    recovered=copy.deepcopy(previous)
    blocked=set(recovered[script_id].get('quarantined_source_sha256',[]))
    blocked.update((attempted_sha, sha(regular(folder/'failed-source.rb', folder))))
    recovered[script_id]['quarantined_source_sha256']=sorted(blocked)
    with project_scope(probe):
        identity=adapter.get_active_model_identity()
        if (path_key(identity.get('model_path'))!=path_key(target) or identity.get('model_guid')!=candidate['model_guid']
            or identity.get('instance_id')!=candidate['instance_id'] or identity.get('active_context')
            or identity.get('main_thread') is not True):raise ValueError('Native recovery identity differs from the new signed instance')
        executor=ProjectRubyExecutor(project.parent.parent,project.name,expected_model_path=target,
            expected_model_guid=identity['model_guid'],mcp=adapter.client,ruby_state=recovered,adapter=adapter)
        result=executor.inspect_owned({'script_id':script_id,'path':[],'limit':100})
        actual=json.loads(result['contentItems'][0]['text'])
        checks={c['check']:c['actual'] for c in accepted['last_verification']['checks']}
        if (actual.get('read_only') is not True or actual.get('revision')!=saved['revision']
            or actual.get('persistent_id')!=saved['root_pid'] or actual.get('objects_total')!=checks.get('objects_total')
            or actual.get('bounds_mm')!=checks.get('bounds_mm')):
            raise ValueError('Native checkpoint readback differs from accepted revision')
        deep=adapter.capture_native_deep_fingerprint(expected_model_path=target,expected_guid=identity['model_guid'],
            root_pid=saved['root_pid'],output_path=folder/'reopened-deep.private.json')
        if adapter.get_active_model_identity()!=identity:raise ValueError('Recovery document changed during verification')
    if (sha(state_path)!=state_sha or sha(checkpoint)!=saved['sha256'] or sha(target)!=saved['sha256']
        or read_selection(root,project)!=old or not process_exited(old_pid)):
        raise ValueError('Recovery evidence changed before activation')
    recovered[script_id].update(model_guid=identity['model_guid'],durability_status='recovered_verified_checkpoint')
    receipt={**attempt,'status':'recovered_from_verified_durable_bytes','restored_revision':saved['revision'],
        'new_instance_id':candidate['instance_id'],'root_geometry_material_sha256':deep['root_geometry_material_sha256'],
        'document_geometry_material_sha256':deep.get('document_geometry_material_sha256'),
        'uncertain_operation_replayed':False,'original_uncertain_outcome':'PRESERVED_UNKNOWN',
        'native_readback':actual,'at':time.time()}
    atomic_write(folder/'recovery-receipt.private.json',receipt)
    patch={'model_path':target.relative_to(project).as_posix(),'model_guid':identity['model_guid'],
        'ruby_state':recovered,'status':'ready','error':'',
        'last_reply':f'已核验并恢复已保存的第 {saved["revision"]} 版。未确认的操作及失败记录已保留，没有重跑。'}
    files=[]
    def stage(destination,data):
        destination=regular(destination,project)
        name='activation-file-'+str(len(files))+'.private'
        _atomic_bytes(folder/name,data)
        files.append({'destination':destination.relative_to(project).as_posix(),'new_file':name,
                      'old_sha256':sha(destination),'new_sha256':hashlib.sha256(data).hexdigest()})
    def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf8')
    stage(project/'runtime/scripts'/f'{script_id}.rb',source.read_bytes())
    stage(state_path,encoded({'model_path':str(target),'scripts':recovered}))
    # Persist the user-facing model identity within the same restartable journal.
    # Legacy diagnostic fixtures may not have UI state; the application does.
    for name in ('agent_session.json','model_state.json'):
        destination=project/'state'/name
        if destination.exists():
            value=json.loads(regular(destination,project/'state').read_text(encoding='utf8'))
            if name=='agent_session.json':value.update(patch)
            else:
                value['model_path']=patch['model_path']
                value['last_operation']={'action':'recover_durable_checkpoint','status':'recovered',
                    'restored_revision':saved['revision'],'uncertain_operation_replayed':False}
            stage(destination,encoded(value))
    atomic_write(folder/'activation.private.json',{'schema_version':1,'files':files,
        'old_selection':old,'candidate':candidate,'checkpoint':saved['path'],
        'session_patch':patch,'receipt':receipt})
    return _finish_activation(project,session,adapter,root,pending_file,attempt,launcher)
