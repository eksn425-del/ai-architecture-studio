"""Archive the owner's actual 12:16 red-house session without model execution."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runtime/projects/architecture-project-fa471'
OUT = ROOT / 'docs/test-results/windows/2026-10-17-noon-red-house-fa471'
LOCAL = timezone(timedelta(hours=8))


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory():
    return {p.relative_to(SOURCE).as_posix(): sha(p.read_bytes())
            for p in sorted(SOURCE.rglob('*')) if p.is_file()}


def main():
    before = inventory()
    record = OUT / 'records'
    provenance = []
    patterns = [
        rb'(?<![A-Za-z0-9])(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})',
        rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    ]
    for name, original_sha in before.items():
        source = SOURCE / name
        if source.is_symlink() or source.name.lower() in {'auth.json', '.env', 'provider.dpapi', 'cookies'}:
            raise ValueError(f'Unexpected credential container or symlink: {name}')
        original = source.read_bytes()
        if any(re.search(p, original) for p in patterns):
            raise ValueError(f'Credential-like signature: {name}')
        public = original
        if source.suffix.lower() not in {'.png', '.skp', '.skb'}:
            public = original.decode('utf-8').replace('\u6d2a\u7984', 'LOCAL_USER').encode('utf-8')
        target = record / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(public)
        provenance.append({'path': name, 'original_sha256': original_sha,
                           'published_sha256': sha(public), 'bytes': len(public),
                           'redaction': 'Windows profile name -> LOCAL_USER' if public != original else None})
    after = inventory()
    if before != after:
        raise RuntimeError('Project changed while snapshotting; do not publish inconsistent copy')
    dump(OUT / 'publication-provenance.json', {
        'schema_version': 1, 'project_id': SOURCE.name,
        'snapshot_at': datetime.now(LOCAL).isoformat(),
        'source_inventory_before_equals_after': True,
        'source_file_count': len(before), 'published_file_count': len(provenance),
        'excluded_project_files': [], 'credentials': 'Never collected; source is this project only',
        'files': provenance,
    })

    context = load(record / 'state/project_context.json')
    session = load(record / 'state/agent_session.json')
    scripts = load(record / 'runtime/project_ruby_state.json')['scripts']
    writer = scripts['villa_reconstruction']
    qa = load(record / 'runtime/agent_workspace/qa/visual_review.json')
    history = [json.loads(line) for line in
               (record / 'runtime/agent_workspace/qa/visual_review_history.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    turns = [{'created_at': x['created_at'], **x.get('metadata', {})}
             for x in context['conversation'] if x['role'] == 'assistant']
    metrics = {'schema_version': 1,
               'elapsed_ms': sum(x.get('latency_ms', 0) for x in turns),
               'tool_call_count': sum(x.get('tool_call_count', 0) for x in turns),
               'failed_tool_calls': sum(x.get('failed_tool_calls', 0) for x in turns),
               'committed_writes': len(list((record / 'runtime/scripts/reports').glob('*.committed.rb'))),
               'full_root_rebuilds': None, 'targeted_corrections': None,
               'input_tokens': sum(x.get('input_tokens', 0) for x in turns),
               'output_tokens': sum(x.get('output_tokens', 0) for x in turns),
               'token_source': 'Actual seven assistant turn metadata in project_context.json; independent Critic usage separate.',
               'site_turns': turns, 'critics': [x['reviewer'] for x in history],
               'critic_count': len(history),
               'critic_input_tokens': sum(x['reviewer'].get('input_tokens', 0) for x in history),
               'critic_output_tokens': sum(x['reviewer'].get('output_tokens', 0) for x in history),
               'billing_usd': None, 'outer_controller_tokens': None,
               'latency_note': 'Sum of seven site calls, includes nested Critic wall time; excludes user pauses. Not invoice data.',
               'publication_model_calls': 0}
    dump(OUT / 'metrics.json', metrics)
    errors = []
    events = []
    for file in sorted((record / 'runtime/agent_events').glob('*.jsonl')):
        for line_no, line in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            event = json.loads(line)
            events.append(event)
            if event.get('event') == 'tool_result' and event.get('success') is False:
                errors.append({'file': file.relative_to(record).as_posix(), 'line': line_no, **event})
    dump(OUT / 'errors.json', errors)
    dump(OUT / 'run.json', {
        'schema_version': 1, 'test_id': OUT.name, 'status': 'PARTIAL',
        'geometry_committed': True,
        'base_commit': 'a510501d0593c55b461a260d9718cddcbcfd0164',
        'base_commit_note': 'Archive preparation Git base, not a certified live process code version for noon. Exact original session live code SHA was not captured.',
        'source_case': 'architecture-project-fa471: c0ab78b0c8-image.png original red-brick photo, five later owner model-problem screenshots',
        'model': {'actual': session['model'], 'runtime': session['provider'], 'reasoning_effort': session['reasoning_effort']},
        'environment': {'site': 'http://127.0.0.1:8787/', 'os': 'Windows',
                        'sketchup': '2024; exact build not independently rechecked in this archive operation'},
        'project_id': SOURCE.name, 'project_name': context['project_name'],
        'script_id': 'villa_reconstruction', 'root_pid': writer['root_pid'],
        'revision': writer['revision'], 'last_writer_model_guid': writer['model_guid'],
        'qa': {'visual_source_fidelity': qa['quality_status'],
               'browser_download': 'NOT_VERIFIED_IN_AVAILABLE_RECORDS',
               'native_reopen': 'UNVERIFIED_NATIVE_REOPEN', 'three_stage_deep': 'NOT_RUN',
               'strict_program_replay': 'NOT_RUN', 'independent_commercial_provider': 'NOT_RUN'},
        'actual_local_start': datetime.fromisoformat(context['conversation'][0]['created_at']).astimezone(LOCAL).isoformat(),
        'actual_local_end': datetime.fromisoformat(context['conversation'][-1]['created_at']).astimezone(LOCAL).isoformat(),
        'snapshot_session_status': session['status'],
        'archive_only': True, 'new_model_operations': 0,
        'scope_correction': 'Earlier296-file su-1017 publication was the wrong session for owner request; retain separately, do not transfer PASS verdicts.',
    })

    def copy(source, dest):
        target = OUT / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(record / source, target)

    for view, item in qa['views'].items():
        path = item['path']
        copy(path, f'views/{view}.png')
        copy(str(Path(path).with_suffix('.evidence.json')), f'views/{view}.evidence.json')
    copy(qa['evidence_pairs'][0]['current_view'], 'source-perspective.png')
    copy('runtime/agent_workspace/qa/visual_review.json', 'review/critique.json')
    copy('runtime/native_delivery_checkpoint.json', 'model/native-reopen.json')
    dump(OUT / 'model/write-verifications.json', writer)
    copy(writer['last_report'], 'model/geometry-readback.json')
    dump(OUT / 'model/oss-method-ledger.json', writer['last_oss_method_ledger'])
    dump(OUT / 'model/oss-method-adoption.json', writer['last_oss_method_adoption'])
    advertised = load(record / 'state/model_state.json')['model_path']
    copy(advertised, 'model/Red-house-r7-site-download-candidate.skp')
    checkpoint = load(record / 'runtime/native_delivery_checkpoint.json')
    discrepancies = []
    for key in ('bound_document', 'download_candidate'):
        info = checkpoint[key]
        b = (record / info['path']).read_bytes()
        discrepancies.append({'role': key, 'path': info['path'],
                              'receipt_sha256': info['sha256'], 'snapshot_sha256': sha(b),
                              'receipt_bytes': info['bytes'], 'snapshot_bytes': len(b),
                              'exact_bytes_match': info['sha256'] == sha(b)})
    dump(OUT / 'model/checkpoint-vs-snapshot.json', discrepancies)
    review = ('归档者实际查看了红砖原图、五张用户补充旧模型问题截图及当前r7原图机位。'
              '独立Critic记录最终needs_fix：首层受压、前围墙偏低、砖纹质感不足；'
              '隐藏背侧及屋顶细节属于推断。用户问题截图不是额外真实建筑照片。'
              '本次仅归档，不重新调用Critic，不执行建模、下载或原生重开；'
              '没有移用su-1017的KEEP、恢复或三阶段PASS。详见实际Critic原文及全部历史。\n')
    (OUT / 'review/review.md').write_text(review, encoding='utf-8')
    timeline = ['# 红房子完整网站对话与执行时间线（北京时间）\n',
                '从冻结project_context直接转录；原始元数据和工具事件在records中。\n']
    for message in context['conversation']:
        stamp = datetime.fromisoformat(message['created_at']).astimezone(LOCAL).strftime('%Y-%m-%d %H:%M:%S')
        timeline.append(f"## {stamp}｜{message['role']}\n\n{message['content']}\n")
        if message.get('metadata'):
            timeline.append('```json\n' + json.dumps(message['metadata'], ensure_ascii=False, indent=2) + '\n```\n')
    (OUT / 'EXECUTION_DETAILS.md').write_text('\n'.join(timeline), encoding='utf-8')
    print(json.dumps({'project_files': len(before), 'redacted_files': sum(x['redaction'] is not None for x in provenance),
                      'metrics': {k: metrics[k] for k in ('input_tokens','output_tokens','tool_call_count','failed_tool_calls','elapsed_ms','critic_count','critic_input_tokens','critic_output_tokens')},
                      'failed_events': len(errors), 'checkpoint_comparison': discrepancies}, ensure_ascii=True))


if __name__ == '__main__':
    main()
