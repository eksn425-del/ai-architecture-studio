"""Export selected public source/redistribution evidence, never private build maps."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def export(materials: Path, vendor: Path, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    # Deliberate allowlist: no credentials, private source-path inventory or downloaded binaries.
    selections = [
        (materials / 'reciprocal-notices', 'reciprocal-notices'),
        (materials / 'libreoffice-kit-0.1.5/licenses', 'libreoffice-licenses'),
        (materials / 'libreoffice-kit-0.1.5/program/NOTICE', 'LibreOffice-NOTICE.txt'),
        (materials / 'archives/manifest.json', 'core-source-archives.json'),
        (materials / 'archives/reciprocal-sources-manifest.json', 'library-source-archives.json'),
        (materials / 'ConPTY-MIT.nuget.html', 'ConPTY-MIT.nuget.html'),
        (vendor / 'webview2-1.0.3856.49-notices', 'webview2-1.0.3856.49'),
        (vendor / 'conpty-1.25.260303002-preview-notices', 'conpty-1.25.260303002-preview'),
        (vendor / 'CPython-bundled-LICENSE.txt', 'CPython-bundled-LICENSE.txt'),
        (vendor / 'vips-binary-match.json', 'vips-binary-match.json'),
    ]
    for source, relative in selections:
        if not source.exists():
            raise ValueError('Required actual notice material missing: ' + relative)
        target = output / relative
        if source.is_dir(): shutil.copytree(source, target)
        else: shutil.copyfile(source, target)
    (output / 'README.md').write_text(
        '# Corresponding source and vendor notices\n\n'
        'These are exact-version source acquisition records and original upstream notices. '
        'The full source archives are retained as a separate release companion, not embedded here. '
        'No public source-hosting endpoint has been established by this internal candidate. '
        'Publication must provide actual matching archives and resolve remaining source-form, '
        'relinking and Microsoft redistributable-origin conditions described in '
        'R2_RELEASE_SOURCE_MATERIALS_20261105.md. This collection is not legal clearance.\n', encoding='utf-8')
    manifest = [{'path': p.relative_to(output).as_posix(), 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(output.rglob('*')) if p.is_file()]
    (output / 'sha256-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return len(manifest)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('materials', type=Path); p.add_argument('vendor', type=Path); p.add_argument('output', type=Path); a = p.parse_args()
    print(json.dumps({'public_notice_files': export(a.materials, a.vendor, a.output)}))
