"""Exclude a reviewed development-only subtree from a fresh dependency stage.

Never walks an installed application or the owner's dependency source. The build
passes its new harness-stage and this script rejects links before removing files.
Upstream skills, templates, runtime files and licenses are deliberately retained.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import stat
from pathlib import Path


def linked(path: Path) -> bool:
    if path.is_symlink():
        return True
    if path.exists():
        return bool(getattr(path.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def prepare(stage: Path) -> dict:
    stage = stage.absolute()
    if stage.name != 'harness-stage' or linked(stage):
        raise ValueError('Expected a physical new harness-stage directory')
    package = stage / 'node_modules/fast-uri'
    target = package / 'benchmark'
    for path in (stage / 'node_modules', package, target):
        if linked(path):
            raise ValueError('Linked dependency stage is not allowed')
    metadata = json.loads((package / 'package.json').read_text(encoding='utf-8'))
    if (metadata.get('name'), metadata.get('version'), metadata.get('main')) != ('fast-uri', '3.1.9', 'index.js'):
        raise ValueError('Review exclusion again for this upstream release')
    if 'benchmark' in json.dumps(metadata.get('exports', {})):
        raise ValueError('Benchmark is now exported; cannot exclude')
    removed = []
    if target.exists():
        for path in sorted(target.rglob('*')):
            if linked(path):
                raise ValueError('Linked subtree is not allowed')
            if path.is_file():
                data = path.read_bytes()
                removed.append({'path': path.relative_to(stage).as_posix(), 'bytes': len(data),
                                'sha256': hashlib.sha256(data).hexdigest()})
        if target.resolve().parent != package.resolve() or not target.resolve().is_relative_to(stage.resolve()):
            raise ValueError('Exclusion escaped intended stage')
        shutil.rmtree(target)
    return {'schema': 1, 'scope': 'fresh_stage_only', 'component': 'fast-uri@3.1.9',
            'reason': 'Non-runtime private benchmark sample; keep production entry, licenses and all Harness skills',
            'removed': removed}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', type=Path)
    args = parser.parse_args()
    report = prepare(args.stage)
    (args.stage.parent / 'dependency-stage-exclusions.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'removed_files': len(report['removed'])}))
