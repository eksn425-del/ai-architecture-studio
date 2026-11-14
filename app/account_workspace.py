"""Local account partitions without moving or importing the owner's old workspace.

This is application isolation under one Windows user, not an OS security boundary.
The original anonymous runtime remains untouched and is never auto-imported.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


class WorkspaceSwitchError(RuntimeError):
    pass


class AccountWorkspaceScopes:
    def __init__(self, app, original_root, cloud_base):
        self.app = app
        self.original_root = Path(original_root).resolve()
        self.cloud_base = cloud_base
        self.scope = None

    def path_for(self, user_id):
        name = hashlib.sha256((self.cloud_base+'|'+user_id).encode()).hexdigest() if user_id else 'signed-out'
        target = self.original_root/'accounts'/name
        # A reparse/symlinked account folder must not redirect data into another user.
        for node in (target.parent,target):
            if node.is_symlink() or (node.exists() and node.resolve()!=node.absolute()):
                raise WorkspaceSwitchError('账户工作区路径无法验证，原文件保持不变。')
        return target

    def activate(self, user_id, *, lock_held=False):
        user_id = user_id or ''
        if self.scope == user_id:
            return False
        app=self.app
        acquired=False
        if not lock_held:
            acquired=app.state.agent_lock.acquire(blocking=False)
            if not acquired: raise WorkspaceSwitchError('请先结束当前建模回合，再切换账户。')
        try:
            for turn in getattr(app.state,'active_turns',{}).values():
                if turn.get('outcome') not in ('completed','failed','cancelled','interrupted'):
                    raise WorkspaceSwitchError('当前任务尚未完成，不能切换账户工作区。')
            # Even after a crashed provider turn, unknown native writes cannot be abandoned.
            for state_file in app.state.store.projects_root.glob('*/state/agent_session.json'):
                import json
                try:
                    state=json.loads(state_file.read_text(encoding='utf8'))
                    native_states=state.get('ruby_state',{}).values()
                    if any(isinstance(native,dict) and (native.get('write_in_flight') or native.get('durability_status')=='unconfirmed') for native in native_states):
                        raise WorkspaceSwitchError('存在尚未核对的原生写入，请先恢复该任务，再切换账户。')
                except (OSError,ValueError):
                    raise WorkspaceSwitchError('原项目状态无法核对，暂不切换账户。') from None
            target=self.path_for(user_id)
            factory=getattr(app.state,'account_runtime_factory',None)
            if factory:
                native_agent=factory(target)
            else:
                from .native_agent import CodexAppServerRuntime
                old=app.state.native_agent
                native_agent=CodexAppServerRuntime(target,
                    codex_executable=getattr(old,'codex_executable',None),
                    model=getattr(old,'model',None),
                    timeout_seconds=getattr(old,'timeout_seconds',None),
                    reasoning_effort=getattr(old,'reasoning_effort',None),
                    sketchup_mcp=getattr(old,'sketchup_mcp',None),
                    home_root=target/'harness-home')
            # Prepare the empty router before publishing any new account paths. A
            # runtime initialization failure must never leave the old key active
            # against the new account's project tree.
            from types import SimpleNamespace
            from .local_connections import connection_router
            shadow=SimpleNamespace(state=SimpleNamespace(native_agent=native_agent,store=SimpleNamespace(root=target)))
            new_router=connection_router(shadow,None)
            # Preserve the ProjectStore instance captured by main/connector route closures.
            store=app.state.store
            store.root=target;store.projects_root=target/'projects';store.jobs_root=target/'jobs'
            app.state.native_agent=native_agent
            app.state.credentials.path=target/'local-settings'/'provider.dpapi'
            vault=getattr(app.state,'connection_vault',None)
            if vault is not None: vault.storage.path=target/'connections.dpapi'
            app.state.model_router=new_router
            app.state.active_turns.clear()
            app.state.credential_restore_error=False
            self.scope=user_id
            return True
        finally:
            if acquired:app.state.agent_lock.release()

    def public(self):
        return {'account_partitioned':True,'scope':'account' if self.scope else 'signed-out',
                'anonymous_history_imported':False,'isolation_boundary':'application_not_os_user'}
