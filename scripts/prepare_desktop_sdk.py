"""Apply the documented Windows GUI launch fix to a copied, pinned SDK only."""
from pathlib import Path
import hashlib
import json
import sys


def prepare(root):
    root = Path(root)
    path = root / 'deepseek_harness/client.py'
    original = path.read_bytes()
    text = original.decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    needle = '        self._proc = subprocess.Popen(\n            args,\n'
    if text.count(needle) != 1:
        raise ValueError('SDK startup changed upstream; review the Windows launch patch before building.')
    replacement = needle + '            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),\n'
    patched = text.replace(needle, replacement).replace('\n', newline).encode('utf-8')
    compile(patched, str(path), 'exec')
    path.write_bytes(patched)
    receipt = {'file': 'deepseek_harness/client.py', 'change': 'Windows GUI: suppress child console only; upstream agent loop unchanged',
               'original_sha256': hashlib.sha256(original).hexdigest(), 'patched_sha256': hashlib.sha256(patched).hexdigest()}
    (root / 'KSTUDIO-SDK-PATCH.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]))
