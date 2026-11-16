from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
LATEST=Path('E:/K Studio/latest')
cfg=json.loads((LATEST/'version.json').read_text(encoding='utf-8-sig'))
cfg.update(api_test_mode=False,local_model='gpt-6.1-sol',local_reasoning_effort='high',execution_limits='off')
cfg['codex_executable']=json.loads((ROOT/'resolved-cli.json').read_text(encoding='utf-8'))['path']
p=LATEST/'Start-KStudioBackend.ps1'
s=p.read_text(encoding='utf-8-sig')
s=s.replace("$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT='medium'", "$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT=$config.local_reasoning_effort\nif(-not $env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT){$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT='medium'}")
s=s.replace("$env:ARCH_STUDIO_CODEX_REASONING_EFFORT='medium'", "$env:ARCH_STUDIO_CODEX_REASONING_EFFORT=$env:ARCH_STUDIO_ECONOMY_REASONING_EFFORT")
s=s.replace("$env:WEB_CONCURRENCY='1'", "$env:WEB_CONCURRENCY='1'\n$env:KSTUDIO_EXECUTION_LIMITS='off'\n$env:ARCH_STUDIO_CODEX_MAX_PROJECT_INPUT_TOKENS='0'\n$env:ARCH_STUDIO_CODEX_PROJECT_DELIVERY_RESERVE='0'\n$env:ARCH_STUDIO_CODEX_MAX_TURN_INPUT_TOKENS='0'\n$env:ARCH_STUDIO_CODEX_MAX_TURN_TOOL_CALLS='0'\nif($config.api_test_mcp_config){$env:ARCH_STUDIO_MCP_CONFIG=$config.api_test_mcp_config}")
p.write_text(s,encoding='utf-8-sig')
p=LATEST/'Open-KStudio-v2.ps1'
s=p.read_text(encoding='utf-8-sig')
old="}elseif($status.native_agent_model -ne 'gpt-6.1-sol' -or $status.native_agent_reasoning_effort -ne 'medium'){throw 'The local model profile differs from the approved Sol / medium profile.'}"
new="}else{$expectedEffort=if($config.local_reasoning_effort){$config.local_reasoning_effort}else{'medium'};if($status.native_agent_model -ne 'gpt-6.1-sol' -or $status.native_agent_reasoning_effort -ne $expectedEffort){throw 'The local model profile differs from the explicitly configured Sol effort.'}}"
assert old in s,'Unexpected launcher, stopped.'
p.write_text(s.replace(old,new),encoding='utf-8-sig')
(LATEST/'version.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'activated-profile.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared exact Sol / high local launcher; saved API credential untouched.')
