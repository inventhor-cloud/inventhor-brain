import json
import subprocess
import sys
import unittest

from shared_organizer.__main__ import evaluate_envelope

TIME = "2026-10-18T12:00:00Z"
CATALOG = {
    "schema_version": 1,
    "system_of_record": "INVENTHOR_MAIN",
    "snapshot_revision": "rev-1",
    "captured_at": TIME,
    "modules": [
        {"project_id": "MAIN", "module_id": "custom_module",
         "declared_capabilities": ["APP_OPEN"]},
    ],
}
OBS = {
    "schema_version": 1,
    "source": "WINDOWS_OPERATOR",
    "snapshot_revision": "rev-1",
    "captured_at": TIME,
    "modules": [
        {"project_id": "MAIN", "module_id": "custom_module",
         "status": "ACTIVE",
         "capabilities": [{"name": "APP_OPEN", "result": "PASS",
                           "evidence_ref": "QA-1"}]},
    ],
}


class BrainInventoryAdapterTests(unittest.TestCase):
    def common(self):
        return {
            "schema_version": 1,
            "catalog": CATALOG,
            "snapshot_revision": "rev-1",
            "host_time_iso": TIME,
        }

    def test_inventory_read_only_adapter(self):
        value = {
            **self.common(), "intent": "MODULE_INVENTORY_REVIEW",
            "observations": OBS,
        }
        r = evaluate_envelope(value)
        self.assertEqual(r["status"], "SOURCE_COVERAGE_REVIEW")
        self.assertEqual(r["summary"]["reported_complete"], 1)
        self.assertFalse(r["may_claim_live_verified"])
        self.assertFalse(r["may_update_registry"])

    def test_owner_open_module_advice_read_only_adapter(self):
        v = {
            **self.common(), "intent": "OWNER_MODULE_REQUEST",
            "module_request": {
                "schema_version": 1,
                "intent": "OWNER_MODULE_REQUEST",
                "requester_role": "OWNER",
                "project_id": "MAIN",
                "module_id": "personal_program",
                "capabilities": ["LOCAL_PROGRAM_RUN"],
            },
        }
        r = evaluate_envelope(v)
        self.assertEqual(r["status"], "OWNER_CHOICE_READY_FOR_HOST_VALIDATION")
        self.assertFalse(r["may_install"])
        self.assertFalse(r["may_claim_owner_authenticated"])
        self.assertTrue(r["requires_main_authenticated_owner"])

    def test_owner_extension_still_requires_host(self):
        v = {
            **self.common(), "intent": "OWNER_MODULE_REQUEST",
            "module_request": {
                "schema_version": 1, "intent": "OWNER_MODULE_REQUEST",
                "requester_role": "OWNER", "project_id": "MAIN",
                "module_id": "custom_module", "capabilities": ["APP_OPEN", "APP_EDIT"],
            },
        }
        r = evaluate_envelope(v)
        self.assertEqual(r["status"], "REVIEW_EXISTING_MODULE_EXTENSION")
        self.assertFalse(r["may_install"])

    def test_malformed_input_never_executes(self):
        value = {
            **self.common(), "intent": "OWNER_MODULE_REQUEST",
            "module_request": {"schema_version": 1, "intent": "OWNER_MODULE_REQUEST"},
            "execute": True,
        }
        self.assertEqual(evaluate_envelope(value)["status"], "UNTRUSTED_EXECUTION_FLAGS")

    def test_missing_observation_has_fail_closed_status(self):
        v = {**self.common(), "intent": "MODULE_INVENTORY_REVIEW"}
        self.assertEqual(evaluate_envelope(v)["status"], "MISSING_MAIN_CONTEXT")

    def test_shell_command_not_recognized_as_brain_intent(self):
        v = {**self.common(), "intent": "RUN_ANYTHING"}
        self.assertEqual(evaluate_envelope(v)["status"], "NOT_A_CANONICAL_CONTINUE_INTENT")

    def test_cli_module_inventory_returns_one_json_and_exit_zero(self):
        v = {**self.common(), "intent": "MODULE_INVENTORY_REVIEW",
             "observations": OBS}
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(v), capture_output=True, text=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(done.stdout.splitlines()), 1)
        self.assertEqual(json.loads(done.stdout)["status"], "SOURCE_COVERAGE_REVIEW")

    def test_cli_owner_custom_module_advisory_exit_zero(self):
        v = {
            **self.common(), "intent": "OWNER_MODULE_REQUEST",
            "module_request": {
                "schema_version": 1, "intent": "OWNER_MODULE_REQUEST",
                "requester_role": "OWNER", "project_id": "MAIN",
                "module_id": "owner_app", "capabilities": ["APP_LAUNCH"],
            },
        }
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(v), capture_output=True, text=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse(json.loads(done.stdout)["may_install"])

    def test_cli_missing_fields_return_nonzero(self):
        v = {**self.common(), "intent": "OWNER_MODULE_REQUEST"}
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(v), capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["status"], "MISSING_MAIN_CONTEXT")
