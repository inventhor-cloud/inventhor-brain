"""Portable module admission for INVENTHOR's existing signed module host.

This is SOURCE-ONLY planning code. It is not a plugin loader, installer, key
authority or grant of OS privileges. A trusted native host must verify the
signature using pinned publisher keys, preflight owner-granted capabilities,
stage into a safe store and atomically activate with rollback.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import base64
import json
import re
from typing import Any, Callable, Mapping

_ID = re.compile(r"^[a-z][a-z0-9.-]{2,127}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_REL = re.compile(r"^[a-zA-Z0-9_-][a-zA-Z0-9_./-]{0,255}$")
MAX_BYTES = 65536
MAX_FILES = 64
MAX_CAPABILITIES = 24


class ModuleAdmissionDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ModuleAdmission:
    module_id: str
    version: str
    host_api: int
    capabilities: tuple[str, ...]
    digest: str
    files: tuple[tuple[str, str], ...]
    disposition: str = "SOURCE_ADMISSION_ONLY_NATIVE_SIGNATURE_INSTALL_REQUIRED"
    may_activate: bool = False


def _string(value: Any, *, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ModuleAdmissionDenied("INVALID_" + label)
    return value


def _relative_file(path: Any) -> str:
    p = _string(path, pattern=_REL, label="RELATIVE_PATH")
    parts = p.split("/")
    if any(x in ("", ".", "..") for x in parts):
        raise ModuleAdmissionDenied("TRAVERSAL_OR_EMPTY_PATH")
    if "\\" in p or p.startswith("/"):
        raise ModuleAdmissionDenied("UNSAFE_PATH")
    return p


def _canonical_unsigned(manifest: Mapping[str, Any]) -> bytes:
    m = {k: v for k, v in manifest.items() if k != "signature"}
    try:
        b = json.dumps(m, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ModuleAdmissionDenied("MANIFEST_NOT_CANONICAL") from e
    if len(b) > MAX_BYTES:
        raise ModuleAdmissionDenied("MANIFEST_TOO_LARGE")
    return b


def verify_portable_module(
    manifest: Mapping[str, Any],
    *,
    host_api: int,
    trusted_publisher_key_ids: frozenset[str],
    allowed_capabilities: frozenset[str],
    verify_publisher_signature: Callable[[str, bytes, bytes], bool] | None,
    staged_root: Path | None = None,
) -> ModuleAdmission:
    """Validate signed module metadata and optionally staged payload SHA-256.

    A host-supplied verifier must authenticate publisher signature using a
    separately pinned public key. Never trust the manifest's signer alone.
    NEVER call this with an LLM-provided trusted key list or verifier.
    """
    if not isinstance(manifest, Mapping):
        raise ModuleAdmissionDenied("MANIFEST_REQUIRED")
    if set(manifest) != {
        "schema_version", "module_id", "version", "host_api",
        "files", "capabilities", "publisher_key_id", "signature",
    }:
        raise ModuleAdmissionDenied("UNKNOWN_OR_MISSING_MANIFEST_FIELD")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ModuleAdmissionDenied("SCHEMA_UNSUPPORTED")
    module_id = _string(manifest["module_id"], pattern=_ID, label="MODULE_ID")
    version = _string(manifest["version"], pattern=_VERSION, label="VERSION")
    abi = manifest["host_api"]
    if type(abi) is not int or type(host_api) is not int or abi != host_api:
        raise ModuleAdmissionDenied("HOST_API_INCOMPATIBLE")
    if not isinstance(trusted_publisher_key_ids, frozenset) or not isinstance(
        allowed_capabilities, frozenset
    ):
        raise ModuleAdmissionDenied("TRUST_CONFIGURATION_NOT_PINNED")
    signer = _string(manifest["publisher_key_id"], pattern=_ID, label="PUBLISHER_ID")
    if signer not in trusted_publisher_key_ids:
        raise ModuleAdmissionDenied("PUBLISHER_NOT_TRUSTED")
    capabilities = manifest["capabilities"]
    if (not isinstance(capabilities, list) or len(capabilities) > MAX_CAPABILITIES
        or len(capabilities) != len(set(str(x) for x in capabilities))):
        raise ModuleAdmissionDenied("CAPABILITY_SET_INVALID")
    caps = tuple(_string(x, pattern=_ID, label="CAPABILITY") for x in capabilities)
    if not set(caps).issubset(allowed_capabilities):
        raise ModuleAdmissionDenied("CAPABILITY_NOT_GRANTED")
    raw_files = manifest["files"]
    if not isinstance(raw_files, list) or not 1 <= len(raw_files) <= MAX_FILES:
        raise ModuleAdmissionDenied("FILE_LIST_INVALID")
    files = []
    for f in raw_files:
        if not isinstance(f, dict) or set(f) != {"path", "sha256"}:
            raise ModuleAdmissionDenied("FILE_ENTRY_INVALID")
        files.append((
            _relative_file(f["path"]),
            _string(f["sha256"], pattern=_HASH, label="FILE_SHA256")
        ))
    if len(set(p for p, _ in files)) != len(files):
        raise ModuleAdmissionDenied("DUPLICATE_FILE")
    if files != sorted(files):
        raise ModuleAdmissionDenied("FILES_NOT_SORTED")
    # There must be code, not arbitrary unpacked installer scripts as payload.
    if not any(p.endswith(".dll") for p, _ in files):
        raise ModuleAdmissionDenied("MODULE_DLL_REQUIRED")
    sig = manifest["signature"]
    if not isinstance(sig, str) or len(sig) > 4096:
        raise ModuleAdmissionDenied("SIGNATURE_INVALID")
    try:
        signature_bytes = base64.b64decode(sig, validate=True)
    except (ValueError, base64.binascii.Error) as e:
        raise ModuleAdmissionDenied("SIGNATURE_INVALID") from e
    if len(signature_bytes) < 32:
        raise ModuleAdmissionDenied("SIGNATURE_INVALID")
    unsigned = _canonical_unsigned(manifest)
    if verify_publisher_signature is None:
        raise ModuleAdmissionDenied("HOST_SIGNATURE_VERIFIER_REQUIRED")
    # This callback is a trusted local host policy boundary, not a field in a
    # cloud JSON file, fake HMAC, or a signature self-verification.
    try:
        valid = verify_publisher_signature(signer, unsigned, signature_bytes)
    except Exception as e:
        raise ModuleAdmissionDenied("SIGNATURE_VERIFIER_FAILED") from e
    if valid is not True:
        raise ModuleAdmissionDenied("PUBLISHER_SIGNATURE_REJECTED")
    if staged_root is not None:
        root = Path(staged_root)
        if not root.is_dir() or root.is_symlink():
            raise ModuleAdmissionDenied("INVALID_STAGING_ROOT")
        resolved_root = root.resolve()
        for path, expected_hash in files:
            file = root.joinpath(*path.split("/"))
            if not file.is_file() or file.is_symlink():
                raise ModuleAdmissionDenied("STAGED_FILE_MISSING_OR_LINK")
            if not file.resolve().is_relative_to(resolved_root):
                raise ModuleAdmissionDenied("STAGED_FILE_ESCAPE")
            with file.open("rb") as handle:
                digest = sha256(handle.read()).hexdigest()
            if digest != expected_hash:
                raise ModuleAdmissionDenied("STAGED_FILE_HASH_MISMATCH")
    return ModuleAdmission(
        module_id=module_id, version=version, host_api=abi,
        capabilities=caps, digest=sha256(unsigned).hexdigest(), files=tuple(files)
    )
