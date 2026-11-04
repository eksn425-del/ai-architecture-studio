"""Authenticated candidate/stable manifests and reversible installation pointers.

Only trusted, pinned public keys verify metadata. This module never executes a
download or migrates user data. Authenticode signing remains a separate gate.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import tempfile
import zipfile
import shutil
import stat
from contextlib import contextmanager, ExitStack
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def verify_manifest(envelope, trusted_keys, *, channel, platform='windows-x64', now=None):
    payload = envelope['payload']
    key = trusted_keys.get(envelope.get('key_id'))
    if key is None:
        raise ValueError('Unknown release signing key')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(key, validate=True)).verify(
        base64.b64decode(envelope['signature'], validate=True), canonical(payload))
    if payload.get('schema') != 1 or payload.get('channel') != channel or channel not in {'candidate', 'stable'}:
        raise ValueError('Release channel mismatch')
    if payload.get('platform') != platform:
        raise ValueError('Unsupported platform')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,79}', payload.get('version', '')):
        raise ValueError('Invalid release version')
    if type(payload.get('sequence')) is not int or payload['sequence'] < 1:
        raise ValueError('Invalid release sequence')
    expiry=datetime.fromisoformat(payload['expires_at'])
    if expiry.tzinfo is None:raise ValueError('Release expiry must specify timezone')
    if expiry.astimezone(timezone.utc) <= (now or datetime.now(timezone.utc)):
        raise ValueError('Expired release metadata')
    if not re.fullmatch(r'[a-f0-9]{64}', payload.get('sha256', '')) or type(payload.get('bytes')) is not int or payload['bytes'] <= 0:
        raise ValueError('Invalid artifact digest or size')
    url=urlparse(payload.get('url',''))
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.port not in (None,443) or url.fragment:
        raise ValueError('Release URL must use HTTPS')
    if payload['bytes']>4*1024**3:raise ValueError('Release archive too large')
    if payload.get('data_schema') != 1:
        raise ValueError('Data migration requires a separately validated migration')
    if payload.get('min_updater_schema',1)!=1:
        raise ValueError('A newer updater is required')
    if channel == 'stable' and (payload.get('acceptance') != 'passed' or payload.get('authenticode') != 'verified'):
        raise ValueError('Stable release acceptance/signature incomplete')
    return payload


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.release-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def safe_root(root):
    root=Path(root).absolute()
    # Reject redirects in any existing ancestor, including versions/current paths.
    for path in (root,*root.parents):
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
            raise ValueError('Installation root must not redirect')
    return root


def installed_inventory(target):
    result={}
    for path in sorted(target.rglob('*')):
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('Installed redirect rejected')
        relative=path.relative_to(target).as_posix()
        if relative in ('release-manifest.json','release-inventory.json'):continue
        if path.is_file():
            with path.open('rb') as f:result[relative]=hashlib.file_digest(f,'sha256').hexdigest()
    return result


def verify_installed(root,version):
    if not isinstance(version,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,79}',version):raise ValueError('Invalid installed version')
    target=safe_root(Path(root)/'versions'/version)
    if not (target/'KStudio.exe').is_file():raise ValueError('Desktop executable missing')
    expected=json.loads((target/'release-inventory.json').read_text(encoding='utf-8'))
    if installed_inventory(target)!=expected:raise ValueError('Installed files changed; activation refused')
    return json.loads((target/'release-manifest.json').read_text(encoding='utf-8'))


def stage_archive(archive, install_root, manifest, *, busy=False):
    if busy:
        raise ValueError('Model task active; update deferred')
    archive, root = Path(archive), safe_root(install_root)
    safe_root(root/'versions')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,79}',manifest.get('version','')):raise ValueError('Invalid release version')
    if archive.stat().st_size != manifest['bytes']:
        raise ValueError('Artifact size mismatch')
    with archive.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != manifest['sha256']:
            raise ValueError('Artifact digest mismatch')
    target = root / 'versions' / manifest['version']
    if target.exists():
        raise ValueError('Version already exists; original preserved')
    root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='staging-', dir=root))
    try:
        with zipfile.ZipFile(archive) as package:
            entries = package.infolist()
            if sum(e.file_size for e in entries) > 8 * 1024**3 or len(entries) > 200000:
                raise ValueError('Archive expansion limit exceeded')
            seen = set()
            for entry in entries:
                name = entry.filename.replace('\\', '/')
                parts=name.rstrip('/').split('/')
                if ':' in name or name.startswith('/') or any(x in ('','..','.') for x in parts):
                    raise ValueError('Archive path escapes installation')
                if any(x.endswith((' ','.')) or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',x,re.I) for x in parts):
                    raise ValueError('Archive Windows reserved path')
                if parts[0].casefold() in ('data','release-manifest.json','release-inventory.json'):
                    raise ValueError('Archive contains installer-owned path')
                mode=(entry.external_attr>>16)&0o170000
                if mode not in (0,stat.S_IFREG,stat.S_IFDIR):raise ValueError('Archive symlink or special file rejected')
                key = name.rstrip('/').casefold()
                if key in seen:raise ValueError('Duplicate archive path')
                seen.add(key)
                destination = (stage / name).resolve()
                if not destination.is_relative_to(stage.resolve()):raise ValueError('Invalid archive destination')
            package.extractall(stage)
        if not (stage / 'KStudio.exe').is_file():raise ValueError('Desktop executable missing')
        atomic_json(stage/'release-inventory.json',installed_inventory(stage))
        atomic_json(stage/'release-manifest.json',manifest)
        target.parent.mkdir(exist_ok=True)
        stage.rename(target)
    finally:
        # Only this invocation's newly allocated staging path; never user data.
        if stage.exists() and stage.parent==root and stage.name.startswith('staging-'):
            shutil.rmtree(stage)
    return target


def activate(install_root, manifest, *, busy=False):
    root = safe_root(install_root)
    if busy:
        raise ValueError('Model task active; update deferred')
    target = root / 'versions' / manifest['version']
    saved = verify_installed(root,manifest['version'])
    if saved != manifest or not (target / 'KStudio.exe').is_file():
        raise ValueError('Staged release does not match')
    current_file = root / 'current.json'
    current = json.loads(current_file.read_text(encoding='utf-8')) if current_file.exists() else None
    minimum=manifest.get('min_current_sequence',0)
    if type(minimum) is not int or minimum<0 or (current['sequence'] if current else 0)<minimum:
        raise ValueError('Current version is below the required upgrade baseline')
    high_file=root/'highest-sequence.json'
    high=max(json.loads(high_file.read_text()) if high_file.exists() else 0,current['sequence'] if current else 0)
    if manifest['sequence'] <= high:
        raise ValueError('Stale release; use explicit rollback')
    atomic_json(root / 'previous.json', current)
    atomic_json(current_file, {'version': manifest['version'], 'sequence': manifest['sequence'], 'data_schema': 1})
    atomic_json(high_file,manifest['sequence'])
    return {'status': 'activated', 'version': manifest['version'], 'user_data_changed': False}


def rollback(install_root, *, busy=False):
    root = safe_root(install_root)
    if busy:
        raise ValueError('Model task active; rollback deferred')
    previous = json.loads((root / 'previous.json').read_text(encoding='utf-8'))
    if not previous or not (root / 'versions' / previous['version'] / 'KStudio.exe').is_file():
        raise ValueError('Previous release unavailable')
    saved=verify_installed(root,previous['version'])
    if saved.get('data_schema')!=previous.get('data_schema') or saved.get('data_schema')!=1:raise ValueError('Rollback data schema mismatch')
    atomic_json(root / 'current.json', previous)
    return {'status': 'rolled_back', 'version': previous['version'], 'user_data_changed': False}


@contextmanager
def installation_guard(install_root,data_dir,runtime_dir=None):
    """OS locks shared with the real desktop/server, held through pointer change."""
    from .runtime_safety import LocalRuntimeLease
    root=safe_root(install_root)
    with ExitStack() as stack:
        try:
            stack.enter_context(LocalRuntimeLease(root/'installer-lock'))
            stack.enter_context(LocalRuntimeLease(Path(data_dir)/'desktop-instance'))
            stack.enter_context(LocalRuntimeLease(Path(runtime_dir) if runtime_dir else Path(data_dir)/'runtime'))
        except RuntimeError as exc:raise ValueError('K Studio or another installer is active; close it normally before updating') from exc
        yield
