import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / 'release-source.json').read_text(encoding='utf-8-sig'))
if manifest['commit'] != sys.argv[2]:
    raise SystemExit('Release commit does not match the launcher.')
for relative, expected in manifest['files'].items():
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit('Release file missing or outside the installation.')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Release file checksum differs: ' + relative)
print('Verified K Studio source release ' + manifest['commit'][:7])
