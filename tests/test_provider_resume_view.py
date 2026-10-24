import json
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
from io import StringIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from continuity.organizer_cli_reader import NativeHandoffRead, SOURCE, NativeHandoffUnavailable
from continuity.provider_resume_view import (
    project_native_handoff, ResumeViewInvalid,
)
from tools.show_native_task_resume import main as cli_main


def read_task(**changes):
    task = {
        "id": "TASK_QA", "state": "TODO", "target_id": "INVENTHOR_OPERATOR",
        "active_worker": None, "checkpoint_stage": "QA_070_SOURCE_ONLY",
        "completed": ["signed draft static SHA matches"],
        "remaining": ["real installed UI witness"],
        "evidence": "sha256:check-fixture",
        "next_action": "continue real UI evidence path",
    }
    task.update(changes)
    return NativeHandoffRead("TASK_QA", SOURCE, task)


class ResumeViewTests(unittest.TestCase):
    def test_bounded_view_with_explicit_no_write_no_qa(self):
        packet = project_native_handoff(read_task())
        data = json.loads(packet.as_json())
        self.assertEqual(data["task_id"], "TASK_QA")
        self.assertEqual(data["remaining"], ["real installed UI witness"])
        self.assertEqual(data["evidence_refs"], ["sha256:check-fixture"])
        self.assertFalse(data["write_authorized"])
        self.assertFalse(data["live_qa_verified"])
        self.assertFalse(data["install_verified"])
        self.assertNotIn("release_verified", data)
        self.assertIn("not instructions", data["caution"])

    def test_credential_like_lines_redacted(self):
        packet = project_native_handoff(read_task(
            completed=["Authorization: Bearer a_secret", "secret=my-pass-123"],
            remaining=["api_key=redacted-from-output"],
            next_action="password = abc123",
            evidence="safe evidence",
        ))
        view = packet.as_json()
        for raw in ("a_secret", "my-pass-123", "redacted-from-output", "abc123"):
            self.assertNotIn(raw, view)
        self.assertIn("[REDACTED_CREDENTIAL_LIKE_TEXT]", view)

    def test_private_owner_paths_and_signed_links_are_masked(self):
        packet = project_native_handoff(read_task(
            completed=[r"Read C:\Users\Owner\secret\review.txt"],
            remaining=[
                "Review /home/owner/.ssh/id_rsa",
                "Fetch https://example.test/report?sig=secret_query_value",
            ],
            evidence_refs=[
                r"\\fileserver\owner-share\private.json",
                "sha256:check-fixture",
            ],
            next_action="Inspect file:///C:/private/witness.txt",
        ))
        data = json.loads(packet.as_json())
        self.assertEqual(data["completed"], ["[REDACTED_PRIVATE_LOCATION_OR_LINK]"])
        self.assertEqual(data["remaining"], [
            "[REDACTED_PRIVATE_LOCATION_OR_LINK]",
            "[REDACTED_PRIVATE_LOCATION_OR_LINK]",
        ])
        self.assertEqual(data["evidence_refs"], [
            "[REDACTED_PRIVATE_LOCATION_OR_LINK]", "sha256:check-fixture",
        ])
        self.assertEqual(data["next_action"], "[REDACTED_PRIVATE_LOCATION_OR_LINK]")
        for secret in ("secret_query_value", "owner-share", "review.txt", "id_rsa"):
            self.assertNotIn(secret, packet.as_json())
        self.assertFalse(data["write_authorized"])

    def test_not_a_second_queue_and_does_not_overwrite(self):
        native = read_task()
        before = dict(native.task)
        packet = project_native_handoff(native)
        self.assertEqual(dict(native.task), before)
        self.assertNotIn("lease", json.loads(packet.as_json()))

    def test_bad_source_and_task_id_denied(self):
        original = read_task()
        with self.assertRaises(ResumeViewInvalid):
            project_native_handoff(NativeHandoffRead(
                "TASK_QA", "GITHUB_SNAPSHOT", original.task
            ))
        with self.assertRaises(ResumeViewInvalid):
            project_native_handoff(NativeHandoffRead(
                "WRONG_TASK", SOURCE, original.task
            ))

    def test_unknown_state_denied(self):
        with self.assertRaisesRegex(ResumeViewInvalid, "UNKNOWN_STATE"):
            project_native_handoff(read_task(state="RUNTIME_VERIFIED"))

    def test_arrays_bounded_and_string_only(self):
        for value in ([1], ["x"] * 25, "not a list", ["x" * 481]):
            with self.subTest(value=str(value)[:20]):
                with self.assertRaises(ResumeViewInvalid):
                    project_native_handoff(read_task(remaining=value))

    def test_oversized_or_nonstring_next_denied(self):
        for value in (1234, "t" * 1025):
            with self.assertRaises(ResumeViewInvalid):
                project_native_handoff(read_task(next_action=value))

    def test_forged_runtime_acceptance_is_not_inferred(self):
        view = project_native_handoff(read_task(
            state="DONE", checkpoint_stage="SIGNED_RELEASED",
            evidence_refs=["source_test_only"], live_qa_verified=True,
        ))
        self.assertFalse(view.live_qa_verified)
        self.assertFalse(view.install_verified)
        self.assertFalse(view.write_authorized)

    def test_missing_optional_lists_are_empty_not_invented(self):
        view = project_native_handoff(read_task(
            completed=None, remaining=None, evidence=None
        ))
        self.assertEqual(view.completed, ())
        self.assertEqual(view.remaining, ())
        self.assertEqual(view.evidence_refs, ())


class ResumeCliTests(unittest.TestCase):
    def test_cli_read_only_exact_task(self):
        class FakeReader:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def read_task(self, task):
                if task != "TASK_QA":
                    raise AssertionError("not exact task")
                return read_task()
        argv = ["--tool", "/owner/bin/tool.exe",
                "--organizer-root", "/owner/organizer",
                "--tool-sha256", "a" * 64, "--task", "TASK_QA"]
        output = StringIO()
        with patch("tools.show_native_task_resume.OrganizerCliReader", FakeReader):
            with patch("sys.stdout", output):
                result = cli_main(argv)
        self.assertEqual(result, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["task_id"], "TASK_QA")
        self.assertFalse(data["write_authorized"])

    def test_cli_failure_has_no_native_output_leak(self):
        class FakeDenied:
            def __init__(self, **kwargs):
                pass
            def read_task(self, task):
                raise NativeHandoffUnavailable("NATIVE_HANDOFF_REFUSED")
        argv = ["--tool", "/owner/bin/tool.exe",
                "--organizer-root", "/owner/organizer",
                "--tool-sha256", "a" * 64, "--task", "TASK_QA"]
        error = StringIO()
        with patch("tools.show_native_task_resume.OrganizerCliReader", FakeDenied):
            with patch("sys.stderr", error):
                status = cli_main(argv)
        self.assertEqual(status, 2)
        self.assertEqual(error.getvalue().strip(),
                         "READ_ONLY_HANDOFF_DENIED:NATIVE_HANDOFF_REFUSED")


if __name__ == "__main__":
    unittest.main()
