"""Read Antigravity service credentials from the current Windows user vault."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


class _FileTime(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


class _CredentialAttribute(ctypes.Structure):
    _fields_ = [
        ("keyword", wintypes.LPWSTR),
        ("flags", wintypes.DWORD),
        ("value_size", wintypes.DWORD),
        ("value", ctypes.POINTER(wintypes.BYTE)),
    ]


class _Credential(ctypes.Structure):
    _fields_ = [
        ("flags", wintypes.DWORD),
        ("type", wintypes.DWORD),
        ("target_name", wintypes.LPWSTR),
        ("comment", wintypes.LPWSTR),
        ("last_written", _FileTime),
        ("credential_blob_size", wintypes.DWORD),
        ("credential_blob", ctypes.POINTER(wintypes.BYTE)),
        ("persist", wintypes.DWORD),
        ("attribute_count", wintypes.DWORD),
        ("attributes", ctypes.POINTER(_CredentialAttribute)),
        ("target_alias", wintypes.LPWSTR),
        ("user_name", wintypes.LPWSTR),
    ]


_TARGETS = {
    "aegis_vds": "Antigravity.Aegis.VDS.ApiKey",
    "codex_vds": "Antigravity.Codex.VDS.ApiKey",
    "codex_router": "Antigravity.Codex.Router.ApiKey",
}


def read_secret(name: str) -> str:
    """Return a configured secret; fail clearly if its vault entry is absent."""
    if os.name != "nt":
        raise RuntimeError("Windows Credential Manager is required for this secret.")
    try:
        target = _TARGETS[name]
    except KeyError as exc:
        raise ValueError("Unknown credential name.") from exc

    advapi = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    advapi.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_Credential)),
    ]
    advapi.CredReadW.restype = wintypes.BOOL
    advapi.CredFree.argtypes = [ctypes.c_void_p]
    advapi.CredFree.restype = None

    credential = ctypes.POINTER(_Credential)()
    if not advapi.CredReadW(target, 1, 0, ctypes.byref(credential)):
        error_code = ctypes.get_last_error()
        raise RuntimeError(
            f"Credential Manager entry is unavailable (Windows error {error_code})."
        )

    try:
        entry = credential.contents
        if not entry.credential_blob or not entry.credential_blob_size:
            raise RuntimeError("Credential Manager entry is empty.")
        raw = ctypes.string_at(entry.credential_blob, entry.credential_blob_size)
        value = raw.decode("utf-8")
        if not value:
            raise RuntimeError("Credential Manager entry is empty.")
        return value
    finally:
        advapi.CredFree(credential)
