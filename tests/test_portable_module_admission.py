import base64
import tempfile
import unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from continuity.portable_module_admission import (
    ModuleAdmissionDenied, verify_portable_module,
)


def candidate(payload=b"test-module-code"):
    return {
        "schema_version": 1,
        "module_id": "inventhor.test",
        "version": "1.2.3",
        "host_api": 1,
        "capabilities": ["readonly.status"],
        "publisher_key_id": "inventhor.publisher",
        "files": [{"path": "module.dll", "sha256": sha256(payload).hexdigest()}],
        "signature": base64.b64encode(b"x" * 64).decode("ascii"),
    }


def check(manifest, root=None, verifier=None, **kwargs):
    # verifier is a deliberately SIMULATED host callback, not a real signature
    # service or enrolled QA signer. Never use this in production.
    return verify_portable_module(
        manifest, host_api=kwargs.get("host_api", 1),
        trusted_publisher_key_ids=kwargs.get(
            "trust", frozenset({"inventhor.publisher"})),
        allowed_capabilities=kwargs.get(
            "capabilities", frozenset({"readonly.status"})),
        verify_publisher_signature=(
            (lambda key_id, data, signature: key_id == "inventhor.publisher"
             and len(data) > 0 and len(signature) == 64)
            if verifier is None else verifier
        ),
        staged_root=root,
    )


class PortableModuleAdmissionTests(unittest.TestCase):
    def reject(self, code, manifest, **kwargs):
        with self.assertRaises(ModuleAdmissionDenied) as ctx:
            check(manifest, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_signed_fixture_is_still_not_install_authorization(self):
        result = check(candidate())
        self.assertEqual(result.module_id, "inventhor.test")
        self.assertEqual(result.version, "1.2.3")
        self.assertFalse(result.may_activate)
        self.assertIn("NATIVE_SIGNATURE_INSTALL_REQUIRED", result.disposition)

    def test_requires_actual_host_verifier_result(self):
        self.reject("PUBLISHER_SIGNATURE_REJECTED", candidate(),
                    verifier=lambda *args: False)

    def test_untrusted_signer_denied(self):
        self.reject("PUBLISHER_NOT_TRUSTED", candidate(),
                    trust=frozenset())

    def test_extra_capability_denied(self):
        m = candidate()
        m["capabilities"] = ["readonly.status", "production.sign"]
        self.reject("CAPABILITY_NOT_GRANTED", m)

    def test_wrong_host_api_denied(self):
        self.reject("HOST_API_INCOMPATIBLE", candidate(), host_api=2)

    def test_unknown_manifest_field_denied(self):
        m = candidate()
        m["tenant_secrets"] = "forbidden"
        self.reject("UNKNOWN_OR_MISSING_MANIFEST_FIELD", m)

    def test_path_escape_denied(self):
        for bad in ("../secrets.dll", "/root/module.dll", "folder/../module.dll",
                    "folder\\module.dll", "folder//module.dll"):
            m = candidate()
            m["files"][0]["path"] = bad
            with self.subTest(bad=bad):
                with self.assertRaises(ModuleAdmissionDenied):
                    check(m)

    def test_duplicate_files_denied(self):
        m = candidate()
        m["files"].append(deepcopy(m["files"][0]))
        self.reject("DUPLICATE_FILE", m)

    def test_missing_dll_denied(self):
        m = candidate()
        m["files"][0]["path"] = "config.json"
        self.reject("MODULE_DLL_REQUIRED", m)

    def test_requires_real_staged_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "module.dll").write_bytes(b"test-module-code")
            self.assertEqual(check(candidate(), root).version, "1.2.3")
            (root / "module.dll").write_bytes(b"modified")
            self.reject("STAGED_FILE_HASH_MISMATCH", candidate(), root=root)

    def test_cannot_accept_external_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.dll"
            outside.write_bytes(b"test-module-code")
            staging = root / "stage"
            staging.mkdir()
            try:
                (staging / "module.dll").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("local filesystem cannot create symlink")
            self.reject("STAGED_FILE_MISSING_OR_LINK", candidate(), root=staging)

    def test_bad_signature_encoding_denied(self):
        m = candidate()
        m["signature"] = "not-base64!?$"
        self.reject("SIGNATURE_INVALID", m)


if __name__ == "__main__":
    unittest.main()
