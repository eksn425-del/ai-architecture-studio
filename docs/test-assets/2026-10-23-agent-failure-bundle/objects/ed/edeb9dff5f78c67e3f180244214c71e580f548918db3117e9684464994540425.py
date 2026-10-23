"""Passive, private closeout of the owner-rejected subject experiment."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
ORIGINAL = Path('E:/K AI 产品建模网站/outputs/sol-high-three-round-20261022')

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

previous = load(ORIGINAL / 'round-3/audit.json')
stages = []
for name, revision in [('cleanup-r11', 11), ('subject-correction-r13', 13)]:
    current = load(ROOT / name / 'audit.json')
    old_files = {x['event_file'] for x in previous['turns']}
    turns = [x for x in current['turns'] if x['event_file'] not in old_files]
    calls = Counter()
    errors = []
    for turn in turns:
        calls.update(turn['tool_starts'])
        errors.extend({'event_file': turn['event_file'], **e} for e in turn['tool_errors'])
    stages.append({
        'stage': name, 'revision': revision,
        'new_thread_runs': len(turns),
        'token_delta': dict(Counter(current['actual_local_token_counters']) - Counter(previous['actual_local_token_counters'])),
        'reference_usd_delta': round(current['reference_api_estimate_usd_with_observed_cache'] - previous['reference_api_estimate_usd_with_observed_cache'], 6),
        'tool_starts_by_name': dict(calls), 'all_tool_starts': sum(calls.values()),
        'native_model_tool_starts': sum(n for k, n in calls.items() if k.startswith('sketchup_')),
        'tool_errors': errors,
        'completion': 'normal; exact requested scope completed and stopped; whole-source fidelity still NEEDS_FIX',
    })
    previous = current

journals = ROOT / 'private-native-journals'
journals.mkdir(exist_ok=True)
samples = []
for rollout in current['rollouts']:
    source = Path(rollout['path'])
    dest = journals / source.name
    if dest.exists():
        assert dest.read_bytes() == source.read_bytes(), 'Frozen journal changed'
    else:
        shutil.copy2(source, dest)
    seen = set()
    for line in source.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        payload = event.get('payload', {})
        if event.get('type') != 'event_msg' or payload.get('type') != 'token_count' or not payload.get('info'):
            continue
        info = payload['info']
        signature = json.dumps(info.get('total_token_usage'), sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        samples.append({'thread_file': dest.name, 'timestamp': event.get('timestamp'), 'usage': info.get('last_token_usage')})

identities = [x['identity'] for x in current['turns']]
assert len(identities) == 30
all_high = all(x.get('requested_model') == 'gpt-6.1-sol' and x.get('reported_model') == 'gpt-6.1-sol' and x.get('requested_effort') == 'high' and x.get('reported_default_effort') == 'high' for x in identities)
assert all_high
result = {
    'as_of_utc': datetime.now(timezone.utc).isoformat(),
    'project_id': 'architecture-project-16c07', 'root_pid': 19, 'final_revision': 13,
    'owner_verdict_on_original_three_rounds': 'REJECTED',
    'previous_72_76_78_scores': 'historical; withdrawn as source-quality acceptance',
    'whole_source_fidelity': 'NEEDS_FIX', 'stages': stages,
    'requested_and_reported_thread_identities_checked': len(identities), 'all_sol_high': all_high,
    'identity_limitation': 'App Server request/response receipts; not cryptographic provider attestation',
    'cumulative_local_usage': current['actual_local_token_counters'],
    'cumulative_reference_usd_observed_cache': current['reference_api_estimate_usd_with_observed_cache'],
    'original_three_round_reference_usd': 6.312689,
    'new_paid_provider_calls': 0,
    'cost_limitations': current['pricing_limitations'],
    'distinct_native_usage_updates': len(samples),
    'usage_update_limitation': 'observed responses, not exact paid HTTP request count',
    'peak_last_input_tokens': max(x['usage'].get('input_tokens', 0) for x in samples),
    'current_native_delivery': 'Product save and real browser download captured; r13 GUI native reopen NOT_RUN due concurrent foreground use; r10 verdict cannot transfer',
    'strict_blank_replay': 'NOT_RUN', 'new_video': 'DEFERRED_BY_OWNER',
    'remaining_quality': ['source-exact loggia/solid-infill positions', 'fine material and planting fidelity', 'hidden dimensions/joints without source evidence'],
    'native_usage_samples': samples,
}
(ROOT / 'final-review-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
manifest = [{'path': str(p.relative_to(journals)), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in journals.iterdir() if p.is_file()]
(ROOT / 'private-journal-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in ('native_usage_samples', 'stages')}, ensure_ascii=False, indent=2))
print(json.dumps([{k: v for k, v in stage.items() if k != 'tool_errors'} for stage in stages], ensure_ascii=False, indent=2))
