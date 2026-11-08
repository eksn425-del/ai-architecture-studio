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
from pathlib import Path
import shutil
import time
import uuid


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


def recover_saved_checkpoint(project,session,adapter,launcher,*,root=None):
    from .connector_instances import lifecycle_pin,instances,path_key,write_selection,read_selection,project_scope
    from .public_connector import root_dir,atomic_write
    from .project_ruby import ProjectRubyExecutor
    project=Path(project).resolve();root=Path(root or root_dir())
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
    if pending.get('durability_status')!='unconfirmed':raise ValueError('No uncertain native write to recover')
    saved=pending.get('durable_checkpoint',{})
    if saved.get('status')!='saved_unverified_reopen' or not isinstance(saved.get('sha256'),str):
        raise ValueError('No previously confirmed durable checkpoint')
    checkpoint=regular(project/saved.get('path',''),project/'outputs/model/committed-revisions')
    if sha(checkpoint)!=saved['sha256']:raise ValueError('Durable checkpoint hash changed')
    previous_path=regular(project/'runtime/previous-agent-ruby-state.json',project/'runtime')
    previous=json.loads(previous_path.read_text(encoding='utf8'))
    accepted=previous.get(script_id,{})
    if (set(previous)!={script_id} or accepted.get('durability_status')=='unconfirmed'
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
        shutil.copyfile(project/str(pending['last_report']),folder/'uncertain-report.private.json')
        shutil.copyfile(project/'runtime/scripts'/f'{script_id}.rb',folder/'failed-source.rb')
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
        'uncertain_operation_replayed':False,'original_uncertain_outcome':'PRESERVED_UNKNOWN',
        'native_readback':actual,'at':time.time()}
    atomic_write(folder/'recovery-receipt.private.json',receipt)
    shutil.copyfile(source,project/'runtime/scripts'/f'{script_id}.rb')
    atomic_write(state_path,{'model_path':str(target),'scripts':recovered})
    write_selection(root,project,candidate)  # Explicit crash recovery, not ordinary window switching.
    session.model_path=target.relative_to(project).as_posix();session.model_guid=identity['model_guid']
    session.ruby_state=recovered;session.status='ready';session.error=''
    session.last_reply=f'已核验并恢复已保存的第 {saved["revision"]} 版。未确认的操作及失败记录已保留，没有重跑。'
    pending_file.rename(folder/'completed-request.private.json')
    return target,receipt
