"""Collect exact bundled MPL/LGPL source notices and immutable upstream references.

No downloads or legal clearance. This is a source-material index, with explicit
missing upstream source archives instead of claiming a homepage fulfils duties.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def collect(bundle: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    modules = bundle / '_internal/harness/node_modules'
    engine = modules / '@deepseek-ai/libreoffice-kit-win32-x64'
    entry = modules / '@deepseek-ai/libreoffice-kit'
    manifest = json.loads((engine / 'prebuilds.json').read_text())
    sharp_metadata = json.loads((modules / '@img/sharp-win32-x64/package.json').read_text())
    if manifest['version'] != '0.1.5' or sharp_metadata['version'] != '0.35.5':
        raise ValueError('Review source obligations again for changed upstream versions')
    mismatches = []
    selected = [p for p in engine.rglob('*') if p.is_file() and
                (p.relative_to(engine).parts[0] in ('sources', 'licenses') or p.name == 'prebuilds.json')]
    selected += [engine / 'program/NOTICE', engine / 'program/license.txt']
    rows = []
    for path in selected:
        relative = path.relative_to(engine).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = manifest['files'].get(relative)
        if expected and digest != expected: mismatches.append(relative)
        destination = output / 'libreoffice-kit-0.1.5' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        rows.append({'path': destination.relative_to(output).as_posix(), 'sha256': digest,
                     'bytes': path.stat().st_size, 'upstream_manifest_sha_verified': bool(expected and digest == expected)})
    if mismatches: raise ValueError('Bundled upstream source material hash mismatch: ' + ','.join(mismatches))
    for package, folder in [(entry, 'libreoffice-kit-adapter-0.1.5'), (modules / '@img/sharp-win32-x64', 'sharp-win32-x64-0.35.5')]:
        destination = output / folder; destination.mkdir()
        for path in package.iterdir():
            if path.is_file() and (path.name.startswith(('LICENSE', 'NOTICE', 'README')) or path.name in ('package.json', 'versions.json')):
                shutil.copyfile(path, destination / path.name)
    source = manifest['source']
    report = {'schema': 1, 'license_clearance': 'REVIEW_REQUIRED', 'local_modifications': 'No K Studio edits to these third-party engine/library binaries or sources',
              'libreoffice': {'package_version': manifest['version'], 'core_version': source['version'],
                             'core_revision': source['revision'], 'core_repository': source['repository'],
                             'core_source_archive_url': 'https://codeload.github.com/LibreOffice/core/tar.gz/' + source['revision'],
                             'bundled_patches_build_scripts': 'COLLECTED_AND_HASH_CHECKED',
                             'full_upstream_core_archive': 'NOT_YET_MIRRORED', 'source_files': rows},
              'sharp': {'package_version': '0.35.5', 'library_versions': json.loads((modules / '@img/sharp-win32-x64/versions.json').read_text()),
                        'build_source_repository': 'https://github.com/lovell/sharp-libvips',
                        'corresponding_dependency_source_archives': 'NOT_YET_MIRRORED'},
              'publication_requirement': 'Publish matching source materials alongside the approved binary release; a local kit or homepage URL is not a completed public source offer.'}
    (output / 'source-materials.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('bundle', type=Path); p.add_argument('output', type=Path); a = p.parse_args()
    r = collect(a.bundle, a.output)
    print(json.dumps({'source_files': len(r['libreoffice']['source_files']), 'core_revision': r['libreoffice']['core_revision']}))
