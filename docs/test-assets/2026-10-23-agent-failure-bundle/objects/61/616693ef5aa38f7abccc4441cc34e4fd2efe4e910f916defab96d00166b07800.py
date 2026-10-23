import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(r'C:/Users/LOCAL_USER\.codex\worktrees\release-prep-20261019\K AI 产品建模网站')
ROOT = Path(r'E:\K AI 产品建模网站')
LATEST = Path(r'E:\K Studio\latest')
AUDIT = ROOT / 'outputs/deepseek-provider-test-20261021/compatibility-repair-20261021/upgrade-onboarding'
AUDIT.mkdir(exist_ok=False)

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def save(p, value):
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

old = json.loads((LATEST / 'version.json').read_text(encoding='utf-8-sig'))
shutil.copy2(LATEST / 'version.json', AUDIT / 'rollback-version.json')
for name in ('last-launch.json', 'Open-KStudio-v2.ps1', 'Start-KStudioBackend.ps1', 'verify-release.py', 'Rollback-KStudio.ps1'):
    if (LATEST / name).is_file():
        shutil.copy2(LATEST / name, AUDIT / name)

runtime = Path(old['runtime_directory'])
assert runtime.resolve() == (ROOT / 'runtime').resolve()
skps = {str(p.relative_to(runtime)): digest(p) for p in runtime.rglob('*.skp')}
save(AUDIT / 'native-models-before.json', skps)
credential_files = list((runtime / 'local-settings').glob('*'))
credentials = {str(p.relative_to(runtime)): digest(p) for p in credential_files if p.is_file()}
save(AUDIT / 'credential-fingerprints-before.json', credentials)
states = 0
for p in (runtime / 'projects').glob('*/state/*.json'):
    dest = AUDIT / 'project-state-before' / p.relative_to(runtime / 'projects')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    states += 1

sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
assert sha == '168e30ea33b46f4cf2be383b71121fcfa3070a33'
version = Path(r'E:\K Studio\versions') / ('20261021-' + sha[:7])
version.mkdir(exist_ok=False)
tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', sha], cwd=REPO, text=True).splitlines()
roots = {'AGENTS.md', 'README.md', 'THIRD_PARTY_NOTICES.md', 'requirements.txt', 'requirements-desktop.txt', 'requirements-model-providers.txt', 'examples/demo_project/project_context.json', 'examples/model_router_v1/input.json'}
files = {}
for relative in tracked:
    if not (relative.startswith(('app/', 'scripts/')) or relative in roots):
        continue
    raw = subprocess.check_output(['git', 'show', sha + ':' + relative], cwd=REPO)
    dest = version / relative
    assert dest.resolve().is_relative_to(version.resolve())
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    files[relative] = hashlib.sha256(raw).hexdigest()
# Private local connector payload, never committed or publicly distributed.
package = ROOT / 'outputs/connector-onboarding-20261021/package'
for payload in package.iterdir():
    if payload.is_file():
        relative = 'connector-distribution/' + payload.name
        dest = version / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(payload, dest)
        files[relative] = digest(dest)
save(version / 'release-source.json', {'commit': sha, 'distribution': 'verified-source-export', 'files': files})
subprocess.run([old['python_executable'], str(LATEST / 'verify-release.py'), str(version), sha], check=True)
new = {**old, 'commit': sha, 'code_directory': str(version), 'upgrade_audit': str(AUDIT)}
save(AUDIT / 'proposed-version.json', new)
save(AUDIT / 'prepared.json', {'prepared_at': datetime.now().astimezone().isoformat(), 'commit': sha, 'release_files': len(files), 'native_models_hashed': len(skps), 'state_files_backed_up': states, 'credential_containers_fingerprinted': len(credentials), 'runtime_directory': str(runtime), 'status': 'prepared_not_activated'})
print(json.dumps({'status': 'prepared_not_activated', 'commit': sha, 'files': len(files), 'models': len(skps), 'states': states}, ensure_ascii=False))
