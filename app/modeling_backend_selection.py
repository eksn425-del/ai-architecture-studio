"""User-selected tool destination; native models are never converted or opened here."""
import json
from pathlib import Path
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

from .models import AgentSession, ModelState


class Selection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    backend: Literal['sketchup', 'blender']


def _read(path, default):
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Unsafe modeling selection path')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _save(path, value):
    _read(path, None)
    temporary = path.with_suffix('.tmp')
    if temporary.is_symlink():
        raise ValueError('Unsafe modeling selection temporary path')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def select_backend(store, project_id, backend):
    """Caller holds the existing single-writer lock, including on recovery."""
    context = store.load_context(project_id)
    project = store.project_dir(project_id)
    marker_path = project / 'state/modeling_backend.json'
    slots_path = project / 'state/modeling_backend_sessions.json'
    marker = _read(marker_path, {'backend': 'sketchup'})
    slots = _read(slots_path, {})
    # A crash cannot dispatch against a half-switched session. Restore the
    # preserved source slot before accepting another user selection.
    if marker.get('switch_in_progress'):
        source = marker['previous_backend']
        snapshot = slots[source]
        store.save_state(project_id, AgentSession.model_validate(snapshot['session']), 'agent_session.json')
        store.save_state(project_id, ModelState.model_validate(snapshot['model']), 'model_state.json')
        marker = {'backend': source}
        _save(marker_path, marker)
    session = store.load_state(project_id, 'agent_session.json', AgentSession)
    if marker.get('backend', 'sketchup') != session.modeling_backend:
        raise ValueError('工具选择与会话不一致，已停止切换；原模型未修改。')
    source = session.modeling_backend
    if source == backend:
        return False
    model = store.load_state(project_id, 'model_state.json', ModelState)
    slots[source] = {'session': session.model_dump(mode='json'), 'model': model.model_dump(mode='json')}
    saved = slots.get(backend)
    target = AgentSession.model_validate(saved['session']) if saved else AgentSession(
        project_id=project_id, modeling_backend=backend, workflow_mode=session.workflow_mode,
        model=session.model, provider=session.provider, reasoning_effort=session.reasoning_effort,
        region=session.region, routing_tier=session.routing_tier)
    target_model = ModelState.model_validate(saved['model']) if saved else ModelState(project_id=project_id)
    if target.project_id != project_id or target.modeling_backend != backend or target_model.project_id != project_id:
        raise ValueError('Saved modeling session identity mismatch')
    # Keep geometry identities/receipts and historical counters in each slot;
    # tool schemas, runtime threads and execution permission never cross tools.
    target.thread_id = ''
    target.runtime_identity = ''
    target.error = ''
    target.plan_started_ns = 0
    target.plan_request_message = ''
    target.backend_plan_required = True
    target.reconstruction_state = 'clarifying' if context.conversation or context.references else 'idle'
    target.status = 'ready' if target.model_path else 'conversation'
    _save(slots_path, slots)
    _save(marker_path, {'backend': source, 'switch_in_progress': True, 'previous_backend': source})
    from .design_scope_approval import _invalidate, _path, _save as save_approval
    _invalidate(project, 'modeling_backend_changed')
    pending = _read(_path(project, 'pending_design_scope.json'), None)
    if pending:
        save_approval(project, 'pending_design_scope.json', {
            **pending, 'consumed': True, 'invalidation_reason': 'modeling_backend_changed'})
    store.save_state(project_id, target, 'agent_session.json')
    store.save_state(project_id, target_model, 'model_state.json')
    _save(marker_path, {'backend': backend})
    return True


def install(app, store):
    @app.post('/api/projects/{project_id}/modeling/backend')
    def select(project_id: str, request: Selection):
        if not app.state.agent_lock.acquire(blocking=False):
            raise HTTPException(409, '本轮正在执行；结束或停止后才能切换建模工具。')
        try:
            changed = select_backend(store, project_id, request.backend)
            return {'backend': request.backend, 'changed': changed, 'geometry_writes': 0,
                    'requires_plan': changed, 'project': store.load_project(project_id)}
        except (ValueError, OSError, KeyError) as error:
            raise HTTPException(409, str(error)) from error
        finally:
            app.state.agent_lock.release()
