import json
import pytest
from app.dsh_runtime import write_profile


def test_full_profile_keeps_official_capabilities_and_compaction(tmp_path, monkeypatch):
    monkeypatch.setenv('KSTUDIO_DSH_CAPABILITIES', 'full')
    monkeypatch.delenv('KSTUDIO_DSH_MCP_CONFIG', raising=False)
    monkeypatch.delenv('KSTUDIO_DSH_SKILL_DIRS', raising=False)
    path=tmp_path/'profile.json'
    write_profile(path,api_base='https://api.b.ai/v1',model='deepseek-v4.1-flash')
    rows=json.loads(path.read_text(encoding='utf-8'))
    from app.dsh_security import RESTRICTED_PLUGINS
    assert {r['id'] for r in rows if r.get('disabled')} == {'session-telemetry-otel',*RESTRICTED_PLUGINS}
    compaction=next(r for r in rows if r.get('id')=='compaction-basic')['config']
    model=next(r for r in rows if r.get('id')=='llm-pi-ai')['config']['providers']['kstudio-bai']['models'][0]
    remaining=model['contextWindow']-model['maxTokens']-compaction['headroomTokens']
    # Source + full native/MCP schemas and a retained summary must have usable
    # room after compression, rather than immediately triggering another one.
    assert remaining >= 65536
    assert compaction['retainTokens']+compaction['maxTokens'] < remaining
    assert next(r for r in rows if r.get('id')=='agent-default-model')['config']['provider']=='kstudio-bai'
    write_profile(path,api_base='https://api.b.ai/v1',model='deepseek-v4.1-flash',host_plan_mode=True)
    rows=json.loads(path.read_text(encoding='utf-8'))
    assert {'id':'plan-mode','disabled':True} in rows
    assert any(row.get('id')=='tool-subagent' for row in rows)


def test_mcp_and_skill_are_added_without_replacing_native_tools(tmp_path,monkeypatch):
    monkeypatch.setenv('KSTUDIO_DSH_CAPABILITIES','full')
    monkeypatch.setenv('KSTUDIO_DSH_EXECUTION_POLICY','trusted-development')
    monkeypatch.setenv('KSTUDIO_DSH_SKILL_DIRS',json.dumps([str(tmp_path)]))
    config=tmp_path/'mcp.json'
    config.write_text(json.dumps({'su':{'transport':'stdio','command':'node','args':['server.js']}}))
    monkeypatch.setenv('KSTUDIO_DSH_MCP_CONFIG',str(config))
    path=tmp_path/'profile.json'
    write_profile(path,api_base='https://example.invalid/v1',model='fixture-model')
    rows=json.loads(path.read_text(encoding='utf-8'))
    entries=[x for r in rows for x in r.get('insert',[])]
    assert next(x for x in entries if x['id']=='kstudio-mcp-su')['config']['serverName']=='su'
    assert next(r for r in rows if r.get('id')=='skill-filesystem')['config']['customSkillDirs']==[str(tmp_path)]
    config.write_text(json.dumps({'su':{'transport':'unknown'}}))
    with pytest.raises(ValueError,match='transport'):
        write_profile(path,api_base='https://example.invalid/v1',model='fixture-model')
