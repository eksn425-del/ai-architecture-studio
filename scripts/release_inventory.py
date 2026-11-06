"""Produce file hashes and dependency evidence from the actual packaged tree."""
import argparse
import hashlib
import json
from pathlib import Path
from email.parser import Parser


def inventory(bundle):
    files, components = [], []
    for path in sorted(bundle.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(bundle).as_posix()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        files.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest})
        if path.name == 'package.json' and 'node_modules' in path.parts:
            try:
                value = json.loads(path.read_text(encoding='utf-8'))
                if value.get('name') and value.get('version'):
                    components.append({'type': 'npm', 'name': value['name'], 'version': value['version'],
                        'license': value.get('license', 'UNKNOWN'), 'metadata': relative})
            except (ValueError, UnicodeError):
                pass
        if path.name == 'METADATA' and path.parent.name.endswith('.dist-info'):
            meta = Parser().parsestr(path.read_text(encoding='utf-8'))
            components.append({'type': 'python', 'name': meta.get('Name'), 'version': meta.get('Version'),
                'license': meta.get('License-Expression') or meta.get('License') or 'UNKNOWN', 'metadata': relative})
    return {'schema': 1, 'files': files, 'components': components,
        'authenticode': 'NOT_SIGNED', 'clean_machine': 'NOT_RUN',
        'component_license_review': 'metadata_only_not_legal_certification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Preserve prior inventory; use a fresh output')
    data = inventory(args.bundle.resolve())
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(data['files']), 'components': len(data['components']),
                      'bytes': sum(f['bytes'] for f in data['files'])}))
