import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from continuity.live_handoff_gate import SOURCE, LeaseAdmission
from continuity.native_readonly_attachment import (
    IntegrationDenied, prepare_read_only_attachment,
)
from continuity.organizer_cli_reader import NativeHandoffRead

NOW = datetime(2026, 10, 23, 17, 0, tzinfo=timezone.utc)


def host_data():
    return {
        "source": SOURCE,
        "task_id": "TASK_QA", "project_id": "INVENTHOR_QA",
        "target_id": "INVENTHOR_OPERATOR", "revision": 9,
        "observed_at": NOW.isoformat(), "state": "TODO",
        "stage": "QA_SOURCE_ONLY", "blocker": "",
        "completed": ["verified draft SHA"],
        "remaining": ["run installed QA UI witness"],
        "evidence_refs": ["SOURCE_REPORT_SHA"],
        "next_action": "collect actual installed process evidence",
        "active_worker": None, "dependencies": [],
    }


def cli_task():
    p = host_data()
    return {
        "id": p["task_id"], "state": p["state"],
        "project_id": p["project_id"],
        "target_id": p["target_id"],
        "checkpoint_stage": p["stage"],
        "completed": p["completed"].copy(),
        "remaining": p["remaining"].copy(),
        "next_action": p["next_action"],
        "active_worker": None,
        "evidence": "SOURCE_REPORT_SHA",
    }


class Cli:
    def __init__(self):
        self.task = cli_task()
        self.calls = 0

    def read_task(self, task_id):
        self.calls += 1
        return NativeHandoffRead(task_id, SOURCE, deepcopy(self.task))


class Native:
    def __init__(self):
        self.data = host_data()
        self.trusted = True
        self.claims = 0
        self.reads = 0

    def read_exact(self, task_id):
        self.reads += 1
        return deepcopy(self.data)

    def verify_read_provenance(self, record):
        return self.trusted

    def claim_if_unchanged(self, **kwargs):
        self.claims += 1
        return LeaseAdmission(False, "TASK_QA", "INVENTHOR_OPERATOR",
                              9, "GPT", None)


def call(cli=None, native=None, **kwargs):
    c = cli or Cli()
    n = native or Native()
    return prepare_read_only_attachment(
        c, n, "TASK_QA",
        expected_target=kwargs.pop("expected_target", "INVENTHOR_OPERATOR"),
        worker="GPT", now=kwargs.pop("now", NOW), **kwargs,
    )


class NativeReadOnlyAttachmentTests(unittest.TestCase):
    def assert_denied(self, code, cli, native, **kwargs):
        with self.assertRaises(IntegrationDenied) as error:
            call(cli, native, **kwargs)
        self.assertEqual(error.exception.code, code)
        self.assertEqual(native.claims, 0)

    def test_success_two_real_source_shapes_no_write(self):
        cli, native = Cli(), Native()
        packet = call(cli, native)
        self.assertEqual(cli.calls, 1)
        self.assertEqual(native.reads, 1)
        self.assertEqual(native.claims, 0)
        self.assertEqual(packet.canonical_revision, 9)
        self.assertEqual(packet.project_id, "INVENTHOR_QA")
        self.assertEqual(packet.remaining, ("run installed QA UI witness",))
        self.assertEqual(packet.display.output_class, "NATIVE_TASK_READ_ONLY_REFERENCE")
        report = json.loads(packet.as_json())
        self.assertFalse(report["source_runtime_installed"])
        self.assertFalse(report["may_claim"])
        self.assertFalse(report["may_dispatch"])
        self.assertFalse(report["may_send_chat_message"])
        self.assertFalse(report["qa_installed_verified"])
        self.assertNotIn("native_lease", report)

    def test_changes_in_state_are_rejected(self):
        c, n = Cli(), Native()
        n.data["state"] = "DOING"
        self.assert_denied("STATE_CHANGED_DURING_CROSSCHECK", c, n)

    def test_wrong_cli_task_id_is_rejected(self):
        c, n = Cli(), Native()
        c.task["id"] = "WRONG"
        self.assert_denied("CLI_VIEW_INVALID", c, n)

    def test_target_mismatch_denied(self):
        c, n = Cli(), Native()
        n.data["target_id"] = "INVENTHOR_MAIN"
        self.assert_denied("NATIVE_TARGET_MISMATCH", c, n)
        c, n = Cli(), Native()
        c.task["target_id"] = "INVENTHOR_MAIN"
        self.assert_denied("CONTRADICTORY_CLI_TARGET_ID", c, n)

    def test_project_conflict_denied(self):
        c, n = Cli(), Native()
        c.task["project_id"] = "OTHER"
        self.assert_denied("CONTRADICTORY_CLI_PROJECT_ID", c, n)

    def test_completed_conflict_denied(self):
        c, n = Cli(), Native()
        n.data["completed"] = ["another step"]
        self.assert_denied("PROGRESS_CHANGED_DURING_CROSSCHECK", c, n)

    def test_remaining_conflict_denied(self):
        c, n = Cli(), Native()
        n.data["remaining"] = ["different remaining"]
        self.assert_denied("PROGRESS_CHANGED_DURING_CROSSCHECK", c, n)

    def test_missing_progress_not_assumed_empty(self):
        for field in ("completed", "remaining"):
            c, n = Cli(), Native()
            del c.task[field]
            with self.subTest(field=field):
                self.assert_denied("CLI_PROGRESS_FIELD_MISSING", c, n)

    def test_checkpoint_stage_conflict_denied(self):
        c, n = Cli(), Native()
        c.task["checkpoint_stage"] = "QA_LIVE_VERIFIED"
        self.assert_denied("CONTRADICTORY_CLI_CHECKPOINT_STAGE", c, n)

    def test_next_action_conflict_denied(self):
        c, n = Cli(), Native()
        n.data["next_action"] = "different task"
        self.assert_denied("CONTRADICTORY_CLI_NEXT_ACTION", c, n)

    def test_stale_native_epoch_is_denied(self):
        c, n = Cli(), Native()
        n.data["observed_at"] = (NOW - timedelta(minutes=2)).isoformat()
        self.assert_denied("NATIVE_STALE_HANDOFF", c, n)

    def test_wrong_native_revision_is_denied(self):
        c, n = Cli(), Native()
        n.data["revision"] = 0
        self.assert_denied("NATIVE_REVISION_REQUIRED", c, n)

    def test_native_host_must_independently_authenticate(self):
        c, n = Cli(), Native()
        n.trusted = False
        self.assert_denied("NATIVE_UNTRUSTED_LIVE_RESPONSE", c, n)

    def test_untrusted_cli_stage_not_reexposed_from_host(self):
        c, n = Cli(), Native()
        # A missing stage can never prompt unrestricted fallback to raw native text.
        del c.task["checkpoint_stage"]
        n.data["stage"] = "password=never-return-this"
        packet = call(c, n)
        serialized = packet.as_json()
        self.assertEqual(packet.checkpoint_stage, "")
        self.assertNotIn("never-return-this", serialized)

    def test_source_only_qa_pass_cannot_be_invented(self):
        c, n = Cli(), Native()
        c.task["live_qa_verified"] = True
        c.task["install_verified"] = True
        x = call(c, n)
        self.assertFalse(x.qa_installed_verified)
        self.assertFalse(x.display.install_verified)


if __name__ == "__main__":
    unittest.main()
