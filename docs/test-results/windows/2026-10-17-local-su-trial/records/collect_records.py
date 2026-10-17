from pathlib import Path
import json,hashlib,shutil
R=Path.cwd();D=R/'runtime/su-trial-20261017';P=R/'runtime/projects/su-1017'
context=json.loads((P/'state/project_context.json').read_text(encoding='utf8'))
turns=[m['metadata'] for m in context['conversation'] if m['role']=='assistant' and m.get('metadata',{}).get('model')]
fields=['agent_action','model','reasoning_effort','provider','input_tokens','output_tokens','latency_ms','tool_call_count','failed_tool_calls']
metrics={'actual_site_turns':[{k:m.get(k) for k in fields} for m in turns],
 'site_turn_input_tokens':sum(m['input_tokens'] for m in turns),
 'site_turn_output_tokens':sum(m['output_tokens'] for m in turns),
 'site_tool_calls':sum(m['tool_call_count'] for m in turns),
 'site_failed_tool_calls':sum(m['failed_tool_calls'] for m in turns),
 'paid_provider_inference_calls':0,'billing_usd':None,
 'latency_note':'Per website turn; Builder duration already includes nested Critic wall time. Do not add Critic duration to it.',
 'independent_critics':[]}
reviews=P/'runtime/agent_workspace/qa/visual_review_history.jsonl'
if reviews.exists():
 for line in reviews.read_text(encoding='utf8').splitlines():
  row=json.loads(line);reviewer=row.get('reviewer')
  if reviewer:metrics['independent_critics'].append(reviewer)
errors=[]
for f in (P/'runtime/agent_events').glob('*.jsonl'):
 for line in f.read_text(encoding='utf8').splitlines():
  row=json.loads(line)
  if row.get('event')=='tool_result' and row.get('success') is False:
   errors.append({'event_file':f.name,'tool':row.get('tool'),'error':row.get('error'),'exit_code':row.get('exit_code')})
errors.extend([{'phase':'initial_offline_tests','error':'8 failures: Node UTF-8 stdout decoded with Windows GBK. Fixed explicit UTF-8; 29 focused and final full suite pass.'},
 {'phase':'host_ui_automation','error':'App switch returned Invalid window handle; no dependent input performed. Recovered through observed SketchUp taskbar button and fresh foreground Snapshot.'}])
(D/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf8')
(D/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
shutil.copytree(P,D/'final-project-record',dirs_exist_ok=True)
manifest=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='artifacts.json':manifest.append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'artifacts.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in metrics.items() if k!='independent_critics'},ensure_ascii=False));print('Private manifest files:',len(manifest),'errors retained:',len(errors))
