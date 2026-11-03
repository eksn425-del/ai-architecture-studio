"""Inventory a distribution without reading or exporting any owner's profile."""
from pathlib import Path
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor


def file_receipt(item):
    root, path = item
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}


def audit(root):
    root = Path(root).resolve()
    rows = []
    files = []
    rejected = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            rejected.append(path.relative_to(root).as_posix())
        elif path.is_file():
            relative = path.relative_to(root).as_posix()
            forbidden = path.suffix.lower() in {'.dpapi', '.skp', '.skb', '.key'} or path.name.lower() in {'.env', 'connections.json', 'bridge.local.json'}
            if path.suffix.lower() == '.pem':
                pem = path.read_bytes()
                forbidden = b'PRIVATE KEY-----' in pem or not any(marker in pem for marker in (b'-----BEGIN CERTIFICATE-----', b'-----BEGIN PUBLIC KEY-----', b'-----BEGIN RSA PUBLIC KEY-----'))
            if forbidden:
                rejected.append(relative)
            files.append((root, path))
    with ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(file_receipt, files))
    return {'schema': 1, 'files': rows, 'rejected_paths': rejected,
            'inventory_pass': bool(rows) and not rejected,
            'signed': False, 'public_release_ready': False,
            'note': 'File inventory only; no clean-machine, provider or SU compatibility claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args()
    if args.receipt.resolve().is_relative_to(args.directory.resolve()):
        parser.error('Receipt must be outside the inventoried bundle.')
    result = audit(args.directory)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}))
    raise SystemExit(0 if result['inventory_pass'] else 1)
