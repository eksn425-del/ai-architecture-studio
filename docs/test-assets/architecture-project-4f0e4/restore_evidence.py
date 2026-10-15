"""Restore owner-approved credential-scrubbed case files into a NEW directory.

Download this entire case directory, then:
python restore_evidence.py E:/review-eight-source-case
This does not run archived code or open/change any SketchUp model.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys
import zipfile


def main():
    source = Path(__file__).resolve().parent
    target = Path(sys.argv[1]).resolve()
    if target.exists():
        raise SystemExit('Choose a new, nonexistent destination directory.')
    index = json.loads((source / 'index.json').read_text(encoding='utf-8'))
    # Verify EVERY archive before writing any files.
    payloads = {}
    for row in index['files']:
        name = PurePosixPath(row['path'])
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('Unsafe indexed destination')
        destination = (target / str(name)).resolve()
        if not destination.is_relative_to(target):
            raise ValueError('Destination escapes target')
        key = row['export_sha256']
        if key not in payloads:
            with zipfile.ZipFile(source / row['archive']) as archive:
                data = archive.read(row['entry'])
            if hashlib.sha256(data).hexdigest() != key:
                raise ValueError('Archive SHA mismatch')
            payloads[key] = data
    for row in index['files']:
        destination = target / row['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payloads[row['export_sha256']])
    print(f"Restored {len(index['files'])} case files; no scripts executed.")


if __name__ == '__main__':
    main()
