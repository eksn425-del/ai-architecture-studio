"""Freeze scoped raw journals and derive stage metrics without inference."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, shutil

ROOT=Path(__file__).resolve().parent
rounds=[]
previous_tokens=Counter()
previous_events=set()
for number in (1,2,3):
    folder=ROOT/f'round-{number}'
    audit=json.loads((folder/'audit.json').read_text(encoding='utf8'))
    tokens=Counter(audit['actual_local_token_counters'])
    rows=[]
    for turn in audit['turns']:
        event=turn['event_file']
        if event not in previous_events:
            rows.append(turn)
        previous_events.add(event)
    calls=Counter()
    commands=Counter()
    errors=[]
    for turn in rows:
        calls.update(turn['tool_starts'])
        events=[json.loads(line) for line in (folder/'project'/turn['event_file']).read_text(encoding='utf8').splitlines()]
        commands.update(row.get('tool') for row in events if row.get('event')=='tool_result' and row.get('tool') in ('codex_commandExecution','codex_fileChange'))
        errors += [dict(event_file=turn['event_file'],**error) for error in turn['tool_errors']]
    actual=tokens-previous_tokens
    estimate=audit['reference_api_estimate_usd_with_observed_cache']
    prior_estimate=rounds[-1]['cumulative_reference_api_usd'] if rounds else 0
    rounds.append({'round':number,'revision':{1:6,2:8,3:10}[number], 'subjective_score':{1:72,2:76,3:78}[number],
      'tokens_delta':dict(actual),'cumulative_tokens':dict(tokens),
      'reference_api_usd_delta':round(estimate-prior_estimate,6),'cumulative_reference_api_usd':estimate,
      'new_native_thread_runs':len(rows),'tool_starts_by_name':dict(calls),
      'total_tool_starts':sum(calls.values()),
      'native_model_tool_starts':sum(count for name,count in calls.items() if name and name.startswith('sketchup_')),
      'local_coding_tool_results':dict(commands),
      'tool_errors':errors,'completion':'owner-style UI stop after over-refinement' if number==1 else 'normal, scope complete and stopped for review'})
    previous_tokens=tokens

rollout_folder=ROOT/'private-native-journals'
rollout_folder.mkdir(exist_ok=True)
last=json.loads((ROOT/'round-3/audit.json').read_text(encoding='utf8'))
usage_samples=[]
for rollout in last['rollouts']:
    source=Path(rollout['path'])
    dest=rollout_folder/source.name
    if dest.exists():
        assert dest.read_bytes()==source.read_bytes(), 'Never overwrite changed evidence'
    else:
        shutil.copy2(source,dest)
    seen=set()
    for line in source.read_text(encoding='utf8').splitlines():
        event=json.loads(line)
        payload=event.get('payload',{})
        if event.get('type')!='event_msg' or payload.get('type')!='token_count' or not payload.get('info'):
            continue
        info=payload['info']
        stamp=json.dumps(info.get('total_token_usage'),sort_keys=True)
        if stamp in seen:
            continue
        seen.add(stamp)
        usage_samples.append({'native_thread_file':dest.name,'timestamp':event.get('timestamp'),
                             'usage':info.get('last_token_usage'),'total':info.get('total_token_usage'),
                             'model_context_window':info.get('model_context_window')})

result={'as_of_utc':datetime.now(timezone.utc).isoformat(),'project_id':'architecture-project-16c07',
 'rounds':rounds,'distinct_native_usage_updates':len(usage_samples),
 'peak_observed_last_input_tokens':max(x['usage'].get('input_tokens',0) for x in usage_samples),
 'native_usage_samples':usage_samples,
 'cost_basis':'Standard Sol reference prices with observed native cache, not an API invoice or guaranteed provider parity',
 'model_request_count_limitation':'Distinct native counter updates are response observations, not exact paid HTTP requests',
 'raw_journals_private':True,'paid_provider_calls_this_run':0,'original_source_and_old_models_preserved':True}
(ROOT/'final-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
for row in rounds:
    print(json.dumps({k:row[k] for k in ['round','revision','subjective_score','tokens_delta','reference_api_usd_delta','new_native_thread_runs','total_tool_starts','native_model_tool_starts','local_coding_tool_results','completion']},ensure_ascii=False))
print(json.dumps({'native_usage_updates':len(usage_samples),'peak_input':result['peak_observed_last_input_tokens']},ensure_ascii=False))
