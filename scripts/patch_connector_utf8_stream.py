"""Repair the known installed Kongxing TCP UTF-8 chunk decoder, with backup.

Does not read credentials or change the endpoint/authentication configuration.
The adapter is an existing external dependency; only this tiny patch is shipped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

MARKER = b'// KStudio UTF-8 stream boundary repair'


def patch_bytes(original: bytes) -> bytes:
    eol = b'\r\n' if b'\r\n' in original else b'\n'
    old = b'socket.on("data", (chunk) => {' + eol + b'      response += chunk.toString("utf8");'
    new = b'socket.setEncoding("utf8"); ' + MARKER + eol + b'    socket.on("data", (chunk) => {' + eol + b'      response += chunk;'
    if MARKER in original:
        if original.count(new) != 1 or old in original:
            raise ValueError('Existing UTF-8 patch is ambiguous or incomplete.')
        return original
    if original.count(old) != 1 or b'net.createConnection' not in original:
        raise ValueError('Unknown connector source; refusing an unreviewed replacement.')
    return original.replace(old, new, 1)


def apply_patch(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.suffix != '.mjs':
        raise ValueError('Expected the explicitly selected existing connector .mjs file.')
    path = path.resolve()
    original = path.read_bytes()
    updated = patch_bytes(original)
    sha = lambda data: hashlib.sha256(data).hexdigest()
    result = {'status': 'ALREADY_PATCHED' if updated == original else 'PATCHED', 'path': str(path),
              'before_sha256': sha(original), 'after_sha256': sha(updated), 'credentials_or_auth_changed': False}
    if updated != original:
        backup = path.with_name(path.name + '.kstudio-before-utf8-' + sha(original)[:16] + '.bak')
        if backup.exists():
            if backup.read_bytes() != original:
                raise ValueError('Existing backup has different bytes.')
        else:
            shutil.copy2(path, backup)
        temporary = path.with_name(path.name + '.kstudio-utf8.tmp')
        if temporary.exists() or temporary.is_symlink():
            raise ValueError('Patch temporary path already exists.')
        with temporary.open('xb') as stream:
            stream.write(updated)
        shutil.copystat(path, temporary)
        temporary.replace(path)
        result['backup'] = str(backup)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = apply_patch(args.path)
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
