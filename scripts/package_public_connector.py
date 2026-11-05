"""Build a credential-free RBZ from reviewed first-party source."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
target = output / 'KStudio-SketchUp-Connector.rbz'
with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
    for source in sorted((root / 'connectors/sketchup').rglob('*.rb')):
        archive.writestr(zipfile.ZipInfo(source.relative_to(root / 'connectors/sketchup').as_posix(),
            date_time=(2026, 11, 5, 0, 0, 0)), source.read_bytes())
(output / 'manifest.json').write_text(json.dumps({'schema': 2, 'version': '2026.11.05-r2',
    'kind': 'kstudio-public', 'publication': 'first_party_candidate', 'files': {target.name: {
    'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}},
    'native_verified_years': [], 'candidate_years': list(range(2019, 2028))}, indent=2), encoding='utf-8')
print(str(target))
