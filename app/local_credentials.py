"""Current-Windows-user DPAPI storage; never fall back to plaintext."""
from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


class LocalCredentialStore:
    def __init__(self, runtime_root: Path):
        self.path = runtime_root / "local-settings" / "provider.dpapi"
        self.supported = os.name == "nt"

    @staticmethod
    def _crypt(payload: bytes, *, decrypt: bool = False) -> bytes:
        class Blob(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
        buffer = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        source = Blob(len(payload), buffer)
        result = Blob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
        fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        fn.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        # UI_FORBIDDEN; no LOCAL_MACHINE flag, so only this Windows user can decrypt.
        if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
            raise OSError("Windows 本机凭据加密失败；未保存 API Key。")
        try:
            return ctypes.string_at(result.data, result.size)
        finally:
            kernel.LocalFree(result.data)

    def save(self, settings: dict[str, str]) -> bool:
        if not self.supported:
            return False
        encrypted = self._crypt(json.dumps(settings, ensure_ascii=False).encode("utf-8"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_bytes(encrypted)
        temporary.replace(self.path)
        return True

    def load(self) -> dict[str, str] | None:
        if not self.supported or not self.path.is_file():
            return None
        settings = json.loads(self._crypt(self.path.read_bytes(), decrypt=True).decode("utf-8"))
        if not isinstance(settings, dict) or not all(isinstance(v, str) for v in settings.values()):
            raise ValueError("Invalid encrypted provider settings")
        return settings

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
