"""Private, passive audit of this one owner-authorized real Studio case."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse, hashlib, json, shutil
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent
PROJECT=Path('E:/K AI 产品建模网站/runtime/projects/architecture-project-16c07')
HOME=Path('C:/Users/LOCAL_USER/AppData/Local/AI Architecture Studio/CodexHome/sessions')

def records(path):
    result=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        try:result.append(json.loads(line))
        except json.JSONDecodeError:pass # A live journal may have an incomplete last line.
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze');args=parser.parse_args()
    turns=[];thread_ids=set()
    for path in sorted((PROJECT/'runtime/agent_events').glob('*.jsonl'),key=lambda p:p.stat().st_mtime):
        rows=records(path);start=next((e for e in rows if e.get('event')=='turn_input'),{})
        identity=next((e for e in rows if e.get('event')=='thread_model_identity'),{})
        totals=[e for e in rows if e.get('event')=='project_budget_finished']
        usages=[e for e in rows if e.get('event')=='token_usage']
        usage=totals[-1] if totals else usages[-1] if usages else {}
        thread_ids.add(start.get('thread_id'))
        turns.append({'event_file':str(path.relative_to(PROJECT)),'thread_id':start.get('thread_id'),'role':start.get('role'),
            'identity':identity,'transition':start.get('thread_transition'),'resumed':start.get('resumed_native_harness'),
            'status':usage.get('status','running'),'input_tokens':usage.get('input_tokens'),'output_tokens':usage.get('output_tokens'),
            'tool_starts':dict(Counter(e.get('tool') for e in rows if e.get('event')=='tool_started')),
            'tool_errors':[{'tool':e.get('tool'),'error':e.get('error')} for e in rows if e.get('event')=='tool_result' and e.get('success') is False],
            'token_samples':len(usages),'latest_context_input':usages[-1].get('last_input_tokens') if usages else None})
    rollouts=[]
    for path in HOME.rglob('*.jsonl'):
        if not any(thread and thread in path.name for thread in thread_ids):continue
        token_events=[e for e in records(path) if e.get('type')=='event_msg' and e.get('payload',{}).get('type')=='token_count' and e.get('payload',{}).get('info')]
        if not token_events:continue
        first=token_events[0]['payload']['info'];last=token_events[-1]['payload']['info']
        base={k:v-first.get('last_token_usage',{}).get(k,0) for k,v in first.get('total_token_usage',{}).items()}
        delta={k:v-base.get(k,0) for k,v in last.get('total_token_usage',{}).items()}
        rollouts.append({'path':str(path),'token_notifications':len(token_events),'usage_delta':delta,
            'note':'Actual local Codex counters, not an API invoice; output includes reasoning.'})
    sums=Counter()
    for row in rollouts:sums.update(row['usage_delta'])
    inputs=sums.get('input_tokens',0);cached=sums.get('cached_input_tokens',0);writes=sums.get('cache_write_input_tokens',0);output=sums.get('output_tokens',0)
    # Official standard up-to-272K prompt example rates retrieved 2026-10-22.
    # Currency deliberately remains USD; no guessed exchange rate or guaranteed cache.
    priced=(max(0,inputs-cached-writes)*2+cached*.1+writes*2.5+output*10)/1_000_000
    result={'as_of_utc':datetime.now(timezone.utc).isoformat(),'project_id':PROJECT.name,'turns':turns,'rollouts':rollouts,
        'actual_local_token_counters':dict(sums),'reference_api_estimate_usd_with_observed_cache':round(priced,6),
        'reference_api_estimate_usd_if_all_input_uncached':round((inputs*2+output*10)/1_000_000,6),
        'price_source':'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
        'pricing_limitations':['not a paid API test or invoice','gateway/region/processing tier may differ','historical rollout cache is not guaranteed for a future provider','long prompt pricing needs per-request validation'],
        'credential_contents_read':False}
    state=PROJECT/'runtime/project_ruby_state.json'
    if state.exists():
        d=json.loads(state.read_text(encoding='utf-8'));result['models']={k:{'revision':v.get('revision'),'root_pid':v.get('root_pid'),'last_screenshot':v.get('last_screenshot'),'verification':v.get('last_verification'),'scope':v.get('last_edit_scope_receipt'),'keep':v.get('last_precommit_keep_guard')} for k,v in d.get('scripts',{}).items()}
    context=json.loads((PROJECT/'state/project_context.json').read_text(encoding='utf-8'))
    result['human_messages']=[{'role':m['role'],'content':m['content'],'created_at':m.get('created_at'),'attachments':m.get('metadata',{}).get('attachments',[])} for m in context.get('conversation',[]) if m.get('role')=='user']
    (ROOT/'live-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.freeze:
        with urlopen('http://127.0.0.1:8803/api/status',timeout=5) as response:
            status=json.load(response)
        assert status.get('active_project_id') is None,'Do not freeze while the single writer is active.'
        dest=ROOT/args.freeze
        assert not dest.exists(),'Never overwrite a frozen round.'
        shutil.copytree(PROJECT,dest/'project')
        (dest/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest=[{'path':str(p.relative_to(dest)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in dest.rglob('*') if p.is_file()]
        (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'turns':len(turns),'tokens':dict(sums),'reference_api_usd_observed_cache':round(priced,6),'models':result.get('models',{}),'frozen':args.freeze},ensure_ascii=False)[:2100])

if __name__=='__main__':main()
