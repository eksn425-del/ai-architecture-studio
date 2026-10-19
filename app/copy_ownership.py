"""Explicit host-only adoption of a known independent SketchUp project copy.

Normal ProjectRuby identity checks remain unchanged. This lifecycle operation
is serialized by the application's existing single-writer lock.
"""
from __future__ import annotations
import hashlib
import base64
import json
import os
import time
import uuid
from pathlib import Path
from .models import AgentSession
from .sketchup_mcp import MCPCallError, _generated_script_dir
from .store import safe_project_id


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


class CopyOwnership:
    def __init__(self, store, adapter):
        self.store, self.adapter = store, adapter

    def idle(self):
        for path in (self.store.root / 'projects').glob('*/state/agent_session.json'):
            if read(path).get('status') not in {'ready','idle','conversation','failed','error','blocked','cancelled'}:
                raise ValueError('A project is running; copy ownership cannot change.')

    def binding(self, target_id):
        safe_project_id(target_id)
        project = self.store.project_dir(target_id).resolve()
        if not (project/'state'/'agent_session.json').is_file():
            raise ValueError('Target project must already exist and have a model binding.')
        session = self.store.load_state(target_id, 'agent_session.json', AgentSession)
        path = (project / session.model_path).resolve()
        if not session.model_path or not path.is_relative_to(project / 'outputs' / 'model'):
            raise ValueError('Copy must be bound inside the target project model folder.')
        if not path.is_file() or path.suffix.lower() != '.skp' or not path.name.startswith('blank-disposable-'):
            raise ValueError('A saved disposable copy is required.')
        live = self.adapter.get_active_model_identity()
        if (Path(live['model_path']).resolve() != path or live.get('model_guid') != session.model_guid
                or live.get('active_context') or live.get('main_thread') is not True):
            raise ValueError('Active model path, GUID or editing context does not match target binding.')
        scripts = read(project / 'runtime' / 'project_ruby_state.json')
        if Path(scripts['model_path']).resolve() != path or not scripts.get('scripts'):
            raise ValueError('Persisted owned root binding is missing or points elsewhere.')
        return project, session, path, scripts

    def native(self, action, plan):
        helper = Path(__file__).with_suffix('.rb').resolve()
        directory = _generated_script_dir().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        script = directory / f'studio-copy-ownership-{uuid.uuid4().hex}.rb'
        if action not in {'inspect','migrate'}:
            raise ValueError('Unknown host lifecycle operation.')
        helper64 = base64.b64encode(str(helper).encode('utf-8')).decode('ascii')
        plan64 = base64.b64encode(json.dumps(plan).encode('utf-8')).decode('ascii')
        script.write_text('# ARCHFLOW_GENERATED_SCRIPT\nrequire "base64"\n' +
            f"load Base64.strict_decode64('{helper64}').force_encoding('UTF-8')\n" +
            f"KStudioCopyOwnership.{action}(Sketchup.active_model, JSON.parse(Base64.strict_decode64('{plan64}').force_encoding('UTF-8')))\n", encoding='utf-8')
        try:
            result = self.adapter.client.call('sketchup_eval_project_file', {
                'script_path':str(script),'operation_name':'Inspect independent copy ownership' if action=='inspect' else 'Adopt independent copy ownership'})
        finally:
            script.unlink(missing_ok=True)
        value = result.get('result') if isinstance(result,dict) else None
        if not isinstance(value,dict):
            raise MCPCallError('Native ownership operation returned no receipt; preserve recovery copy and inspect before retrying.')
        return value

    def prepare(self, target_id):
        self.idle()
        project, session, path, state = self.binding(target_id)
        if (project / 'runtime' / 'copy_ownership_receipt.json').exists():
            raise ValueError('This copy has already been migrated; repeated migration is forbidden.')
        plan = {'target_project_id':target_id,'target_path':str(path),'expected_guid':session.model_guid}
        probe = self.native('inspect',plan)
        roots = probe['roots']
        sources = {r['project_id'] for r in roots}
        if len(sources)!=1 or target_id in sources:
            raise ValueError('Copy roots must belong to one distinct, explicit source project.')
        source_id = safe_project_id(next(iter(sources)))
        source_project = self.store.project_dir(source_id).resolve()
        if not (source_project/'state'/'agent_session.json').is_file():
            raise ValueError('Source project must already exist; arbitrary model adoption is forbidden.')
        source_session = self.store.load_state(source_id,'agent_session.json',AgentSession)
        source = (source_project / source_session.model_path).resolve()
        if (not source_session.model_path or not source.is_file() or
                not source.is_relative_to(source_project / 'outputs' / 'model') or
                path == source or os.path.samefile(path,source)):
            raise ValueError('Original model migration is forbidden; independent target bytes are required.')
        expected = sorted((v['root_pid'],v['revision']) for v in state['scripts'].values())
        original_state = read(source_project/'runtime'/'project_ruby_state.json')
        source_roots = sorted((v['root_pid'],v['revision']) for v in original_state['scripts'].values())
        actual = sorted((r['root_pid'],r['revision']) for r in roots)
        if actual != expected or actual != source_roots:
            raise ValueError('Source/target root PID and revision bindings differ.')
        receipt_id = uuid.uuid4().hex
        plan.update(source_project_id=source_id,source_path=str(source),source_sha256=sha(source),
            target_sha256=sha(path),roots=roots,fingerprint=probe['fingerprint'],created_at=time.time(),
            receipt_id=receipt_id,native_backup_path=str(project/'runtime'/f'copy-ownership-before-{receipt_id}.skp'))
        (project/'runtime'/'copy_ownership_preview.json').write_text(json.dumps(plan),encoding='utf-8')
        return {'receipt_id':receipt_id,'source_project_id':source_id,'target_project_id':target_id,
            'source_project_name':self.store.load_context(source_id).project_name,
            'target_project_name':self.store.load_context(target_id).project_name,
            'roots':roots,'fingerprint':probe['fingerprint'],'geometry_change':False}

    def apply(self,target_id,receipt_id):
        self.idle()
        project, session, path, state = self.binding(target_id)
        receipt_path = project/'runtime'/'copy_ownership_receipt.json'
        if receipt_path.exists():
            raise ValueError('This copy has already been migrated; repeated migration is forbidden.')
        plan = read(project/'runtime'/'copy_ownership_preview.json')
        if (plan['target_project_id']!=target_id or plan['target_path']!=str(path) or
                plan['receipt_id']!=receipt_id or time.time()-plan['created_at']>900 or
                plan['expected_guid']!=session.model_guid):
            raise ValueError('Ownership preview expired or binding changed; inspect the copy again.')
        source = Path(plan['source_path'])
        if path==source or os.path.samefile(path,source) or sha(source)!=plan['source_sha256'] or sha(path)!=plan['target_sha256']:
            raise ValueError('Original or target copy changed since preview.')
        result = self.native('migrate',plan)
        (project/'runtime'/f'copy_ownership_attempt-{receipt_id}.json').write_text(json.dumps(result),encoding='utf-8')
        if result.get('status')!='saved' or result.get('geometry_unchanged') is not True or result.get('before')!=result.get('after'):
            raise MCPCallError(str(result.get('error') or 'Copy ownership migration failed.'))
        if sha(source)!=plan['source_sha256']:
            raise MCPCallError('Source changed during migration; stopped before enabling modeling.')
        live = self.adapter.get_active_model_identity()
        if Path(live['model_path']).resolve()!=path or live['model_guid']!=result['model_guid']:
            raise MCPCallError('Active model changed after migration; do not resume modeling.')
        session.model_guid = result['model_guid']
        for value in session.ruby_state.values():
            value['model_guid'] = result['model_guid']
        for value in state['scripts'].values():
            value['model_guid'] = result['model_guid']
        (project/'runtime'/'project_ruby_state.json').write_text(json.dumps(state),encoding='utf-8')
        self.store.save_state(target_id,session,'agent_session.json')
        receipt = {**result,'source_project_id':plan['source_project_id'],'target_project_id':target_id,
            'source_sha256':plan['source_sha256'],'target_saved_sha256':sha(path),'source_unchanged':True}
        receipt_path.write_text(json.dumps(receipt),encoding='utf-8')
        return receipt
