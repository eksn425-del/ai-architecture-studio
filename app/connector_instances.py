"""Host-selected SketchUp process and document pins, never a global window switch.

Signed heartbeats are discovery, not native modeling/ownership proof. A process
pin survives document GUID changes; a document pin changes only after explicit
selection or a verified completed native operation. These are local same-user
transport guards, not an OS security sandbox.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import re
import time

HEARTBEAT_TTL = 8.0
_project = ContextVar('kstudio_connector_project', default='')
_instance_id = re.compile(r'^[0-9]+-[a-f0-9]{24}$')


@contextmanager
def project_scope(project):
    token = _project.set(str(Path(project).resolve()))
    try:
        yield
    finally:
        _project.reset(token)


def current_project():
    return _project.get()


def path_key(value):
    return os.path.normcase(str(Path(value).resolve())).replace('\\', '/') if value else ''


def _config(root):
    value = json.loads((Path(root) / 'pairing.json').read_text(encoding='utf-8'))
    if not value.get('enabled'):
        raise ValueError('连接器配对已停用。')
    return value


def selection_file(root, project):
    key = hashlib.sha256(path_key(project).encode()).hexdigest()
    return Path(root) / 'selections' / (key + '.json')


def read_selection(root, project):
    from .public_connector import verified
    if not project:
        return None
    path = selection_file(root, project)
    if not path.exists():
        return None
    value = verified(json.loads(path.read_text(encoding='utf-8')), _config(root)['token'])
    if path_key(value.get('project')) != path_key(project):
        raise ValueError('会话连接绑定与当前项目不一致。')
    return value


def write_selection(root, project, instance):
    from .public_connector import atomic_write, signed
    value = {'schema': 1, 'project': str(Path(project).resolve()),
             'instance_id': instance['instance_id'], 'model_path': instance['model_path'],
             'model_guid': instance['model_guid'], 'selected_at': time.time()}
    path = selection_file(root, project)
    path.parent.mkdir(exist_ok=True)
    atomic_write(path, signed(value, _config(root)['token']))
    return value


def lifecycle_pin(project, *, root=None):
    """Snapshot before an already-authorized host open/recovery operation."""
    from .public_connector import root_dir
    root = Path(root or root_dir())
    return read_selection(root, project) if (root / 'pairing.json').is_file() else None


def bind_verified_lifecycle(project, identity, previous, expected_path, *, root=None):
    """Bind only a successful host lifecycle readback; never select another PID.

    The caller has already checked native recovery/save/copy authorization and
    pending-write gates. This adds signed discovery + selection CAS, not ownership.
    """
    from .public_connector import root_dir
    root = Path(root or root_dir())
    iid = identity.get('instance_id')
    if not iid:
        if previous:
            raise ValueError('已选实例未返回实例身份，不能改用旧连接。')
        return False  # Existing legacy adapter: do not manufacture a process pin.
    if (path_key(identity.get('model_path')) != path_key(expected_path) or
        not disposable(identity.get('model_path'), project) or not identity.get('model_guid') or
        identity.get('active_context') or identity.get('main_thread') is not True):
        raise ValueError('生命周期读回没有确认本会话的安全副本。')
    live = [i for i in instances(root) if i['status'] == 'live']
    current = next((i for i in live if i['instance_id'] == iid), None)
    if (not current or current.get('model_guid') != identity['model_guid'] or
        path_key(current.get('model_path')) != path_key(expected_path)):
        raise ValueError('生命周期读回与当前签名实例记录不一致。')
    if read_selection(root, project) != previous:
        raise ValueError('生命周期操作期间会话连接绑定已变化。')
    if previous:
        if previous['instance_id'] != iid:
            raise ValueError('生命周期操作不能静默改用另一个 SketchUp 窗口。')
    elif len(live) != 1:
        raise ValueError('存在多个 SketchUp 窗口，请明确选择后连接。')
    write_selection(root, project, current)
    return True


def instances(root, *, now=None):
    from .public_connector import verified
    root = Path(root)
    token = _config(root)['token']
    now = time.time() if now is None else now
    result = []
    for path in sorted((root / 'instances').glob('*.json')):
        try:
            if path.is_symlink() or path.stat().st_size > 65536:
                continue
            value = verified(json.loads(path.read_text(encoding='utf-8')), token)
            iid = value.get('instance_id', '')
            if not _instance_id.fullmatch(iid) or path.stem != iid or str(value.get('pid')) != iid.split('-')[0]:
                continue
            age = now - float(value['last_seen'])
            value['status'] = ('stopped' if value.get('state') == 'stopped' else
                               'live' if 0 <= age <= HEARTBEAT_TTL else 'stale')
            result.append(value)
        except (ValueError, OSError, KeyError, TypeError):
            continue
    return result


def target_for_request(root, project, *, identity_only=False):
    """Legacy only when no modern roster has ever been created. Never downgrade."""
    root = Path(root)
    selected = read_selection(root, project)
    if not (root / 'instances').exists():
        if selected:
            raise ValueError('选中的 SketchUp 实例已失联；未改用其他窗口。')
        return None
    roster = instances(root)
    live = [i for i in roster if i['status'] == 'live']
    if selected:
        current = next((i for i in live if i['instance_id'] == selected['instance_id']), None)
        if not current:
            raise ValueError('选中的 SketchUp 实例已退出、过期或重启；请重新选择。')
        changed = (path_key(current.get('model_path')) != path_key(selected['model_path']) or
                   current.get('model_guid') != selected['model_guid'])
        if changed and not identity_only:
            raise ValueError('选中窗口的模型路径或 GUID 已变化；未执行请求，请核对后重新连接。')
        return {**selected, 'identity_only': identity_only}
    if len(live) != 1:
        raise ValueError('请在建模工具中明确选择 SketchUp 窗口。' if live else '未发现有效的 SketchUp 连接器，请打开已安装连接器的 SketchUp。')
    # Preserve the existing explicit single-window copy preparation workflow.
    # A second live process removes this fallback; it never changes a saved pin.
    return {**{k: live[0].get(k, '') for k in ('instance_id', 'model_path', 'model_guid')},
            'identity_only': identity_only}


def advance_document_pin(project, model_path, old_guid, new_guid, *, root=None, checkpoint=None):
    """CAS only with a signed successful operation spanning exactly this change.

    Called after host native commit/save validation, never on ordinary health.
    Unknown/error replies and another process or document cannot advance a pin.
    """
    from .public_connector import root_dir, verified, atomic_write, signed
    root = Path(root or root_dir())
    selected = read_selection(root, project) if (root / 'pairing.json').exists() else None
    if not selected or old_guid == new_guid:
        return False
    if selected['model_guid'] != old_guid or path_key(selected['model_path']) != path_key(model_path):
        raise ValueError('模型连接绑定已变化，不能更新 GUID。')
    token = _config(root)['token']
    proof_path = root / 'instance-receipts' / (selected['instance_id'] + '.json')
    proof = verified(json.loads(proof_path.read_text(encoding='utf-8')), token)
    before, after = proof.get('identity_before', {}), proof.get('identity_after', {})
    if (proof.get('error') or not proof.get('completed') or proof.get('instance_id') != selected['instance_id'] or
        float(proof.get('at', 0)) < selected['selected_at'] or
        before.get('model_guid') != old_guid or after.get('model_guid') != new_guid or
        any(path_key(i.get('model_path')) != path_key(model_path) for i in (before, after))):
        raise ValueError('缺少此实例完成操作的 GUID 变更回执；未重绑模型。')
    if checkpoint and any(proof.get(key) != checkpoint.get(key) for key in ('operation_id', 'instance_id', 'project_id', 'root_pid', 'revision')):
        raise ValueError('保存回执的实例、操作或原生版本不匹配；未重绑模型。')
    # caller holds the application's single writer lock; repeat CAS before write
    if read_selection(root, project) != selected:
        raise ValueError('模型连接绑定在更新期间变化。')
    selected['model_guid'] = new_guid
    atomic_write(selection_file(root, project), signed(selected, token))
    return True


def unresolved(project, session):
    states = list(session.ruby_state.values())
    file = Path(project) / 'runtime/project_ruby_state.json'
    if file.exists():
        states += list(json.loads(file.read_text(encoding='utf-8')).get('scripts', {}).values())
    return any(s.get('write_in_flight') or s.get('durability_status') == 'unconfirmed' for s in states)


def disposable(path, project):
    candidate = Path(path).resolve() if path else None
    return bool(candidate and candidate.is_file() and candidate.suffix.lower() == '.skp' and
                candidate.name.lower().startswith('blank-disposable-') and
                candidate.is_relative_to((Path(project) / 'outputs/model').resolve()))


def describe(root, project=None, session=None):
    roster = instances(root)
    selected = read_selection(root, project) if project else None
    pending = bool(project and session and unresolved(project, session))
    for item in roster:
        reason = ('窗口连接已过期或停止' if item['status'] != 'live' else
                  '上次写入结果未确认，请先在恢复面板核对' if pending else
                  '请先退出群组或组件编辑' if item.get('active_context') else
                  '请在此窗口打开本会话的安全副本' if not project or not disposable(item.get('model_path'), project) else
                  '请打开本会话当前绑定的副本；更换版本请使用恢复面板' if session and session.ruby_state and session.model_path and path_key(item.get('model_path')) != path_key(Path(project) / session.model_path) else
                  '缺少模型 GUID' if not item.get('model_guid') else '')
        item.update(selectable=not bool(reason), reason=reason)
    status, detail = 'none', '请选择打开本会话安全副本的 SketchUp 窗口。'
    if selected:
        current = next((i for i in roster if i['instance_id'] == selected['instance_id']), None)
        if pending:
            status, detail = 'unknown', '上次写入结果未确认，选择窗口不能解除恢复保护。'
        elif not current or current['status'] != 'live':
            status, detail = 'stale', '选中窗口已退出、过期或重启，请重新连接。'
        elif (path_key(current.get('model_path')) != path_key(selected['model_path']) or current.get('model_guid') != selected['model_guid']):
            status, detail = 'document_changed', '选中窗口的模型已变化，请核对安全副本后重新连接。'
        else:
            status, detail = 'selected', '已选择该窗口；实际连接状态仍需原生读回确认。'
    return {'instances': roster, 'selected_instance_id': selected['instance_id'] if selected else None,
            'selection_status': status, 'detail': detail}


def register_routes(app, store, agent_lock):
    from fastapi import HTTPException, Request
    from .models import AgentSession, ModelState
    from .public_connector import root_dir
    from .store import utc_now

    @app.middleware('http')
    async def project_connector_scope(request: Request, call_next):
        match = re.match(r'^/api/projects/([a-z0-9-]+)(?:/|$)', request.url.path)
        if not match:
            return await call_next(request)
        try:
            directory = store.project_dir(match[1])
        except ValueError:
            return await call_next(request)
        with project_scope(directory):
            return await call_next(request)

    @app.get('/api/connectors/sketchup/instances')
    def list_instances(project_id: str = ''):
        try:
            project = store.project_dir(project_id) if project_id else None
            session = store.load_state(project_id, 'agent_session.json', AgentSession) if project else None
            return describe(root_dir(), project, session)
        except FileNotFoundError:
            return {'instances': [], 'selected_instance_id': None, 'selection_status': 'none',
                    'detail': '尚未配对本机连接器，请先完成连接器设置。'}
        except (OSError, ValueError) as error:
            raise HTTPException(409, str(error)) from error

    @app.post('/api/projects/{project_id}/connector/instance')
    def select_instance(project_id: str, body: dict):
        if not agent_lock.acquire(blocking=False):
            raise HTTPException(409, '当前任务正在运行，请结束后再更换窗口。')
        try:
            project = store.project_dir(project_id)
            if not (project / 'state/project_context.json').is_file():
                raise HTTPException(404, '会话不存在。')
            session = store.load_state(project_id, 'agent_session.json', AgentSession)
            if session.modeling_backend != 'sketchup':
                raise ValueError('当前会话未选择 SketchUp。')
            rows = describe(root_dir(), project, session)['instances']
            row = next((i for i in rows if i['instance_id'] == body.get('instance_id')), None)
            if not row or not row['selectable']:
                raise ValueError(row['reason'] if row else '该 SketchUp 实例已失效。')
            if (path_key(row['model_path']) != path_key(body.get('expected_model_path')) or
                    row['model_guid'] != body.get('expected_model_guid')):
                raise ValueError('窗口模型在选择期间已变化，请刷新后重试。')
            write_selection(root_dir(), project, row)
            with project_scope(project):
                identity = app.state.sketchup.get_active_model_identity()
            if (path_key(identity.get('model_path')) != path_key(row['model_path']) or
                    identity.get('model_guid') != row['model_guid'] or identity.get('active_context') or
                    identity.get('main_thread') is not True):
                raise ValueError('原生读回与已选模型不一致，尚未启用建模。')
            session.model_path = Path(row['model_path']).resolve().relative_to(project.resolve()).as_posix()
            session.model_guid = row['model_guid']
            session.status = 'ready'
            session.last_model_info = identity
            session.started_at = session.started_at or utc_now()
            session.updated_at = utc_now()
            # Existing error/ownership/approval/ruby_state are intentionally retained.
            store.save_state(project_id, session, 'agent_session.json')
            model_state = store.load_state(project_id, 'model_state.json', ModelState)
            model_state.connector_readback = identity
            store.save_state(project_id, model_state, 'model_state.json')
            return {'session': session, 'project': store.load_project(project_id),
                    'selection_status': 'selected', 'selected_instance_id': row['instance_id']}
        except (ValueError, OSError, RuntimeError) as error:
            raise HTTPException(409, str(error)) from error
        finally:
            agent_lock.release()
