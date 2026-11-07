"""Application account boundaries and explicit DPAPI restore (not OS separation)."""
import json
import os
import threading
from types import SimpleNamespace

import httpx
import pytest

from app.account_workspace import AccountWorkspaceScopes, WorkspaceSwitchError
from app.cloud_account import CloudAccount, CloudAccountError
from app.local_credentials import LocalCredentialStore
from app.local_connections import ConnectionVault
from app.store import ProjectStore


class MemoryStore:
    def __init__(self):self.value=None
    def load(self):return self.value
    def save(self,value):self.value=dict(value);return True


def fake_app(root,monkeypatch):
    store=ProjectStore(root)
    state=SimpleNamespace(store=store,agent_lock=threading.Lock(),active_turns={},
        credentials=LocalCredentialStore(root),connection_vault=ConnectionVault(root),
        native_agent=SimpleNamespace(runtime_root=root),model_router=SimpleNamespace(),
        account_runtime_factory=lambda r:SimpleNamespace(runtime_root=r))
    monkeypatch.setattr('app.local_connections.connection_router',lambda app,item:SimpleNamespace(active=item,runtime_root=app.state.store.root))
    return SimpleNamespace(state=state)


def test_account_switch_preserves_anonymous_and_isolates_history_and_credentials(tmp_path,monkeypatch):
    app=fake_app(tmp_path,monkeypatch)
    original=app.state.store;old=tmp_path/'projects'/'owner'/'state';old.mkdir(parents=True)
    (old/'private.json').write_text('owner data')
    scopes=AccountWorkspaceScopes(app,tmp_path,'https://cloud.example')
    scopes.activate('alice');a_root=app.state.store.root
    (a_root/'projects'/'alice-project').mkdir(parents=True)
    assert app.state.store is original and app.state.store.projects_root!=tmp_path/'projects'
    scopes.activate('bob');b_root=app.state.store.root
    assert b_root!=a_root and not (b_root/'projects'/'alice-project').exists()
    assert app.state.connection_vault.storage.path.parent==b_root
    assert app.state.native_agent.runtime_root==b_root and app.state.model_router.active is None
    scopes.activate(None)
    assert app.state.store.root.name=='signed-out' and (old/'private.json').read_text()=='owner data'
    scopes.activate('alice')
    assert (app.state.store.projects_root/'alice-project').exists()


def test_scope_switch_refuses_active_turn_and_unknown_native_commit(tmp_path,monkeypatch):
    app=fake_app(tmp_path,monkeypatch);scopes=AccountWorkspaceScopes(app,tmp_path,'https://cloud.example')
    app.state.active_turns['one']={'started':1}
    with pytest.raises(WorkspaceSwitchError):scopes.activate('bob')
    app.state.active_turns.clear()
    state=tmp_path/'projects'/'one'/'state';state.mkdir(parents=True)
    (state/'agent_session.json').write_text(json.dumps({'ruby_state':{'harness_building':{'write_in_flight':{'id':'pending'}}}}))
    with pytest.raises(WorkspaceSwitchError):scopes.activate('bob')
    assert app.state.store.root==tmp_path


def test_failed_new_runtime_router_never_publishes_new_scope_with_old_key(tmp_path,monkeypatch):
    app=fake_app(tmp_path,monkeypatch);scopes=AccountWorkspaceScopes(app,tmp_path,'https://cloud.example')
    original=app.state.model_router
    def fail(*args):raise ValueError('runtime failed')
    monkeypatch.setattr('app.local_connections.connection_router',fail)
    with pytest.raises(ValueError):scopes.activate('bob')
    assert app.state.store.root==tmp_path and app.state.model_router is original and scopes.scope is None


@pytest.mark.skipif(os.name!='nt',reason='Actual Windows DPAPI integration')
def test_explicit_account_restore_is_dpapi_no_activation_and_deleted_cache_clears(tmp_path,monkeypatch):
    app=fake_app(tmp_path,monkeypatch);storage=MemoryStore()
    secret='fixture-only-cloud-key-never-published'
    remote={'id':'cloud-connection','label':'BAI fixture','provider':'BAI','protocol':'responses',
        'base_url':'https://api.b.ai/v1','model_id':'deepseek-v4.1-flash','reasoning_effort':'low',
        'updated_at':123,'api_key':secret}
    alive=[True]
    def transport(request):
        if request.url.path=='/api/auth/me':return httpx.Response(200,json={'authenticated':True,'user':{'id':'alice'}})
        if request.url.path=='/api/account/connections/restore':
            assert json.loads(request.content)['sync_token']=='opaque-grant'
            return httpx.Response(200,json={'connection':remote,'user_id':'alice','device_id':'this-device'})
        if request.url.path=='/api/account/connections':return httpx.Response(200,json={'connections':[remote] if alive[0] else []})
        raise AssertionError(request.url)
    account=CloudAccount(tmp_path,'https://cloud.example',storage=storage,transport=httpx.MockTransport(transport))
    account.attach_workspace(app,tmp_path)
    account.state.update(token='fixture',refresh_token='refresh',expires=9999999999)
    with pytest.raises(CloudAccountError):account.restore_connection({'sync_token':'opaque-grant'})
    result=account.restore_connection({'sync_token':'opaque-grant','confirm_local_restore':True})
    assert result['restored'] and result['activated'] is False and secret not in json.dumps(result)
    vault=app.state.connection_vault
    assert secret.encode() not in vault.storage.path.read_bytes()
    saved=vault.load();assert saved['connections'][0]['api_key']==secret and saved['active_id'] is None
    alive[0]=False;account.ensure_session()
    assert vault.load()['connections']==[]


def test_fresh_cloud_install_defaults_platform_but_standalone_preserved(tmp_path):
    assert CloudAccount(tmp_path,'',storage=MemoryStore()).state['source_mode']=='byok'
    assert CloudAccount(tmp_path,'https://cloud.example',storage=MemoryStore()).state['source_mode']=='platform'
