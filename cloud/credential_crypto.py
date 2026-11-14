"""Versioned AES-256-GCM credentials; master keys never live in the database."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CredentialCryptoError(ValueError):
    pass


class CredentialCipher:
    def __init__(self, keys: dict[str, bytes], active_version: str):
        if (not isinstance(active_version, str) or active_version not in keys
                or not keys or any(not isinstance(k, str) or not k or len(k) > 40
                                   or not isinstance(v, bytes) or len(v) != 32
                                   for k, v in keys.items())):
            raise CredentialCryptoError('Account credential master-key configuration is invalid')
        self.keys = dict(keys)
        self.active_version = active_version

    @classmethod
    def from_file(cls, filename: str, active_version: str):
        try:
            path = Path(filename)
            if not filename or path.is_symlink() or path.stat().st_size > 32768:
                raise ValueError()
            raw = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                raise ValueError()
            keys = {key: base64.b64decode(value, validate=True) for key, value in raw.items()}
            return cls(keys, active_version)
        except (ValueError, OSError, TypeError):
            raise CredentialCryptoError('Account credential master-key file is unavailable or invalid') from None

    @staticmethod
    def aad(user_id: str, connection_id: str, version: str) -> bytes:
        return json.dumps(['kstudio-account-credential', 1, user_id, connection_id, version],
                          separators=(',', ':')).encode('utf-8')

    def encrypt(self, secret: str, user_id: str, connection_id: str) -> dict:
        version = self.active_version
        nonce = os.urandom(12)
        ciphertext = AESGCM(self.keys[version]).encrypt(
            nonce, secret.encode('utf-8'), self.aad(user_id, connection_id, version))
        return {'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
                'nonce': base64.b64encode(nonce).decode('ascii'), 'key_version': version}

    def decrypt(self, row: dict) -> str:
        try:
            version = row['key_version']
            return AESGCM(self.keys[version]).decrypt(
                base64.b64decode(row['nonce'], validate=True),
                base64.b64decode(row['ciphertext'], validate=True),
                self.aad(row['user_id'], row['id'], version)).decode('utf-8')
        except Exception:
            # No plaintext, key material, database contents or library error in diagnostics.
            raise CredentialCryptoError('Saved account credential cannot be authenticated') from None
