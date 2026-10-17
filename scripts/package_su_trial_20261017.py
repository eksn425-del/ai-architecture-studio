"""Publish the owner-authorized frozen SU trial; never read credential stores.

Copies evidence, does not run SketchUp, inference, or change project data.
Original records remain immutable in runtime. Publication provenance identifies
the only text substitution: the local Windows profile name is anonymized.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runtime/su-trial-20261017'
OUT = ROOT / 'docs/test-results/windows/2026-10-17-local-su-trial'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    records = OUT / 'records'
    provenance = []
    sensitive = re.compile(
        rb'(?<![A-Za-z0-9])(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}'
        rb'|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'
        rb'|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})'
        rb'|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
    )
    files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    for source in files:
        relative = source.relative_to(SOURCE)
        if source.is_symlink():
            raise ValueError('Symlink is not evidence')
        if any(x.lower() in {'auth.json', '.env', 'provider.dpapi', 'cookies'} for x in relative.parts):
            raise ValueError('Unexpected credential container in frozen records')
        original = source.read_bytes()
        if sensitive.search(original):
            raise ValueError(f'Credential-like bytes require review: {relative}')
        published = original
        if source.suffix.lower() not in {'.png', '.skp', '.skb'}:
            published = original.decode('utf-8').replace('\u6d2a\u7984', 'LOCAL_USER').encode('utf-8')
        target = records / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(published)
        provenance.append({
            'path': relative.as_posix(), 'original_bytes': len(original),
            'original_sha256': sha(original), 'published_bytes': len(published),
            'published_sha256': sha(published),
            'redaction': 'Windows profile name -> LOCAL_USER' if published != original else None,
        })
    dump(OUT / 'publication-provenance.json', {
        'schema_version': 1, 'owner_authorized_publication': '2026-10-17 explicit follow-up',
        'source_file_count': len(files), 'published_file_count': len(provenance),
        'excluded_trial_files': [], 'files': provenance,
        'credential_stores': 'Never collected; DPAPI provider, auth home, passwords, cookies excluded by source scope',
        'historical_manifests': 'records/artifacts.json and nested manifests are original historical inventories, not the public manifest',
    })

    def copy(source, destination):
        target = OUT / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(records / source, target)

    final = 'final-project-record/'
    qa = load(records / final / 'runtime/agent_workspace/qa/visual_review.json')
    for view, info in qa['views'].items():
        if view not in ('front', 'rear', 'left', 'right', 'roof', 'oblique'):
            continue
        source = final + info['path']
        copy(source, f'views/{view}.png')
        copy(str(Path(source).with_suffix('.evidence.json')).replace('\\', '/'), f'views/{view}.evidence.json')
    copy(final + 'outputs/renders/agent-view-29454d0b07.png', 'source-perspective.png')
    copy(final + 'runtime/agent_workspace/qa/visual_review.json', 'review/critique.json')
    copy('actual-r4-writer.json', 'model/write-verifications.json')
    copy('edited-r4-before-final-save.json', 'model/geometry-readback.json')
    copy('native-delivery-declared-precision.json', 'model/native-reopen.json')
    copy('trial-r4-actual-browser-download.skp', 'model/SU-trial-r4-browser-download.skp')
    copy('r3-record/initial-r3.skp', 'model/SU-trial-r3-before-edit.skp')
    writer = load(records / 'actual-r4-writer.json')
    dump(OUT / 'model/oss-method-ledger.json', writer['last_oss_method_ledger'])
    dump(OUT / 'model/oss-method-adoption.json', writer['last_oss_method_adoption'])
    copy('review/review.md', 'review/review.md')
    copy('errors.json', 'errors.json')

    run = load(OUT / 'run.json')
    run.update({
        'schema_version': 1, 'test_id': OUT.name, 'status': 'PARTIAL',
        'public_raw_evidence': 'OWNER_AUTHORIZED_PUBLISHED_WITH_PROFILE_NAME_REDACTION',
        'source_case': 'cloud-villa/villa-single-view.png; pixel-identical uploaded 2fc62f9b95-villa-single-view.png',
        'model': {'actual': 'gpt-6.1-sol', 'runtime': 'codex-app-server', 'reasoning_effort': 'medium'},
        'environment': {'os': 'Windows', 'sketchup': '24.0.484', 'bridge': '0.1.0', 'site': 'http://127.0.0.1:8787/'},
        'qa': {'source_fidelity': 'NEEDS_FIX', 'local_edit': 'PASS', 'protected_geometry': 'PASS',
               'native_delivery': 'PASS_WITH_DECLARED_PRECISION', 'raw_strict_double': 'FAIL',
               'strict_program_replay': 'NOT_RUN', 'independent_commercial_api': 'NOT_RUN'},
        'engineering_commit': '9ae94384a419deaccbdfdd4b867fb297666defec',
        'publication_note': 'Owner subsequently requested ALL trial records on GitHub. Branch publication only; main unchanged.',
    })
    dump(OUT / 'run.json', run)
    metrics = load(records / 'metrics.json')
    metrics.update({
        'schema_version': 1, 'elapsed_ms': sum(t['latency_ms'] for t in metrics['actual_site_turns']),
        'tool_call_count': metrics['site_tool_calls'], 'failed_tool_calls': metrics['site_failed_tool_calls'],
        'committed_writes': 4, 'full_root_rebuilds': 0, 'targeted_corrections': 3,
        'input_tokens': metrics['site_turn_input_tokens'], 'output_tokens': metrics['site_turn_output_tokens'],
        'token_source': 'Actual five website turns in project_context; independent Critic shown separately; controller tokens unavailable.',
        'counter_notes': 'Four commits: initial build + two bounded initial corrections + one owner local edit. No whole-root rebuild after initial creation. targeted_corrections=3 counts all three correction writes.',
        'outer_controller_input_tokens': None, 'outer_controller_output_tokens': None,
    })
    dump(OUT / 'metrics.json', metrics)
    print(json.dumps({'copied_files': len(provenance), 'redacted_files': sum(x['redaction'] is not None for x in provenance),
                      'source_bytes': sum(x['original_bytes'] for x in provenance)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
