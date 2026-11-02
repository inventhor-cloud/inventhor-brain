import json
import subprocess
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from continuity.organizer_cli_reader import (
    OrganizerCliReader, NativeHandoffUnavailable, SOURCE
)


def native_result(item=None, *, source=SOURCE, task_count=None):
    record = {"id": "QA_TASK", "state": "TODO"} if item is None else item
    document = {"source": source, "tasks": [record]}
    if task_count is not None:
        document["task_count"] = task_count
    return subprocess.CompletedProcess([], 0, json.dumps(document), "")


class CliHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.tool = root / "safe-native-tool.exe"
        self.tool.write_bytes(b"trusted test-only fake, never deployed")
        self.root = root / "organizer"
        self.root.mkdir()
        self.sha = sha256(self.tool.read_bytes()).hexdigest()
        self.calls = []
        self.response = native_result()
        self.invoker = self.fake_run

    def fake_run(self, args, **opts):
        self.calls.append((args, opts))
        return self.response

    def reader(self, **kwargs):
        return OrganizerCliReader(
            tool_path=self.tool,
            organizer_root=self.root,
            expected_tool_sha256=self.sha,
            runner=self.invoker,
            **kwargs
        )

    def deny(self, code, method, *args, **kwargs):
        with self.assertRaises(NativeHandoffUnavailable) as ctx:
            method(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_read_exact_bounded_without_shell_or_mutation(self):
        data = self.reader().read_task("QA_TASK")
        self.assertEqual(data.task_id, "QA_TASK")
        self.assertEqual(data.task["state"], "TODO")
        self.assertEqual(len(self.calls), 1)
        argv, opts = self.calls[0]
        self.assertEqual(argv[1], "handoff")
        self.assertEqual(argv[3], "--task=QA_TASK")
        self.assertIs(opts["shell"], False)
        self.assertFalse(opts["check"])
        self.assertEqual(opts["timeout"], 10)

    def test_rejects_invalid_task_and_does_not_run(self):
        for task_id in ("../secret", "QA_TASK; rm -rf x", "", "--help"):
            self.deny("TASK_ID_INVALID", self.reader().read_task, task_id)
        self.assertEqual(self.calls, [])

    def test_requires_pinned_code_hash_and_rechecks_file(self):
        self.deny("PINNED_TOOL_SHA256_REQUIRED", OrganizerCliReader,
                  tool_path=self.tool, organizer_root=self.root, expected_tool_sha256="invalid")
        reader = self.reader()
        self.tool.write_bytes(b"new unknown executable")
        self.deny("PINNED_NATIVE_TOOL_CHANGED", reader.read_task, "QA_TASK")
        self.assertEqual(self.calls, [])

    def test_large_pinned_tool_reads_in_bounded_chunks(self):
        # The read-only reader must hash installed tools without allocating
        # an executable-sized byte string or changing any real PC resource.
        self.tool.write_bytes(b"trusted-fixture-" * 100000)
        self.sha = sha256(self.tool.read_bytes()).hexdigest()
        observed = self.reader().read_task("QA_TASK")
        self.assertEqual(observed.task_id, "QA_TASK")
        self.assertEqual(len(self.calls), 1)

    def test_tool_changed_during_invocation_is_rejected(self):
        def changed_binary_during_read(args, **opts):
            self.calls.append((args, opts))
            self.tool.write_bytes(b"replaced while running")
            return native_result()
        self.invoker = changed_binary_during_read
        self.deny("PINNED_NATIVE_TOOL_CHANGED",
                  self.reader().read_task, "QA_TASK")
        self.assertEqual(len(self.calls), 1)

    def test_rejects_noncanonical_and_wrong_task(self):
        self.response = native_result(source="GITHUB_OLD_SNAPSHOT")
        self.deny("NON_CANONICAL_HANDOFF", self.reader().read_task, "QA_TASK")
        self.response = native_result(item={"id": "OTHER", "state": "TODO"})
        self.deny("HANDOFF_TASK_ID_MISMATCH", self.reader().read_task, "QA_TASK")
        self.response = native_result(item={"id": "QA_TASK", "state": "TODO"}, task_count=2)
        self.deny("HANDOFF_COUNT_MISMATCH", self.reader().read_task, "QA_TASK")

    def test_refuses_lost_command_and_parse_failure(self):
        self.response = subprocess.CompletedProcess([], 2, "", "native error")
        self.deny("NATIVE_HANDOFF_REFUSED", self.reader().read_task, "QA_TASK")
        self.response = subprocess.CompletedProcess([], 0, "{broken", "")
        self.deny("NATIVE_HANDOFF_MALFORMED", self.reader().read_task, "QA_TASK")
        self.response = subprocess.CompletedProcess([], 0, "a" * 300000, "")
        self.deny("NATIVE_HANDOFF_OVERSIZED", self.reader().read_task, "QA_TASK")

    def test_reader_cannot_act_as_write_capable_live_port(self):
        reader = self.reader()
        self.assertFalse(hasattr(reader, "claim_if_unchanged"))
        self.assertFalse(hasattr(reader, "checkpoint"))
        self.assertFalse(hasattr(reader, "release"))

    def test_native_timeout_refuses(self):
        def timed_out(*args, **kwargs):
            raise subprocess.TimeoutExpired("native-tool", 10)
        self.invoker = timed_out
        self.deny("NATIVE_HANDOFF_UNAVAILABLE", self.reader().read_task, "QA_TASK")


if __name__ == "__main__":
    unittest.main()
