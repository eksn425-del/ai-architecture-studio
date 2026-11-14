"""The child must outlive the connector's bounded native response window."""
from types import SimpleNamespace
import pytest
from app.sketchup_mcp import ConfiguredSketchUpMCP,_frame
from app.connector_deadlines import native_response_timeout


@pytest.mark.parametrize('tool',['sketchup_eval_project_file','sketchup_export_view_image','sketchup_health'])
def test_native_child_timeout_does_not_cut_off_its_response_window(monkeypatch,tool):
    observed=[]
    monkeypatch.setattr('app.sketchup_mcp._resolve_server',lambda:(['fixture'],{},None))
    def run(*args,**kwargs):
        observed.append(kwargs['timeout'])
        return SimpleNamespace(stdout=_frame({'id':3,'result':{'success':True}}),stderr=b'')
    monkeypatch.setattr('app.sketchup_mcp.subprocess.run',run)
    assert ConfiguredSketchUpMCP()._request([{'method':'tools/call','params':{'name':tool}}],3)['success']
    assert observed[0]>native_response_timeout(tool)


def test_explicit_diagnostic_timeout_is_preserved(monkeypatch):
    observed=[]
    monkeypatch.setattr('app.sketchup_mcp._resolve_server',lambda:(['fixture'],{},None))
    def run(*args,**kwargs):
        observed.append(kwargs['timeout'])
        return SimpleNamespace(stdout=_frame({'id':3,'result':{'success':True}}),stderr=b'')
    monkeypatch.setattr('app.sketchup_mcp.subprocess.run',run)
    ConfiguredSketchUpMCP(timeout_seconds=2)._request([{'method':'tools/call','params':{'name':'sketchup_eval_project_file'}}],3)
    assert observed==[2]
