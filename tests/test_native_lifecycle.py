import json
import re
from pathlib import Path
from types import SimpleNamespace
import pytest
import app.sketchup_mcp as module


def setup(tmp_path,monkeypatch,finish):
    monkeypatch.setattr(module,'_generated_script_dir',lambda:tmp_path/'scripts')
    original=tmp_path/'blank-disposable-original.skp';target=tmp_path/'blank-disposable-target.skp'
    original.touch();target.touch();state={'model_path':str(original),'model_guid':'guid-known','active_context':False}
    calls=[]
    def call(name,args):
        code=Path(args['script_path']).read_text(encoding='utf8');calls.append(code)
        status=re.search(r'File.write\((".*?\.status.json")',code).group(1)
        Path(json.loads(status)).write_text(json.dumps({'finished':True,'ok':True} if finish else {'opening':True}))
        if finish:state['model_path']=str(target)
    adapter=module.SketchUpAdapter(SimpleNamespace(call=call));monkeypatch.setattr(adapter,'get_active_model_identity',lambda:dict(state))
    return adapter,original,target,calls


def test_save_after_bridge_transaction_and_actual_identity(tmp_path,monkeypatch):
    a,old,target,calls=setup(tmp_path,monkeypatch,True)
    a.restore_disposable_model(target,old)
    assert calls[0].index('UI.start_timer')<calls[0].index('unless m.save')<calls[0].index('Sketchup.open_file')
    assert 'm.guid == "guid-known"' in calls[0]
    assert not (tmp_path/'scripts/studio-lifecycle.pending').exists()


def test_timeout_cancels_timer_and_quarantines_native_modal(tmp_path,monkeypatch):
    a,old,target,calls=setup(tmp_path,monkeypatch,False)
    ticks=iter([0,30]);monkeypatch.setattr(module.time,'monotonic',lambda:next(ticks))
    with pytest.raises(module.MCPCallError,match='quarantined'):a.restore_disposable_model(target,old)
    assert list((tmp_path/'scripts').glob('*.cancel'))
    with pytest.raises(module.MCPCallError,match='No new open queued'):a.restore_disposable_model(target,old)
    assert len(calls)==1
