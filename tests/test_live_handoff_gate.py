import unittest
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from continuity.live_handoff_gate import (
    SOURCE, HandoffDenied, LeaseAdmission, resume, draft_next_checkpoint
)

NOW = datetime(2026, 10, 22, 17, 0, tzinfo=timezone.utc)

def record():
    return {
        "source": SOURCE, "task_id": "QA_TASK", "project_id": "INVENTHOR_QA",
        "target_id": "INVENTHOR_OPERATOR", "revision": 7,
        "observed_at": NOW.isoformat(), "state": "TODO",
        "stage": "SOURCE_TESTED_NOT_INSTALLED",
        "completed": ["signed QA draft hash independently verified"],
        "remaining": ["real installed UI effect witness"],
        "evidence_refs": ["canonical QA preflight reference"],
        "blocker": "", "next_action": "run exact live UI witness preflight",
        "dependencies": [{"task_id": "TEST_PREP", "state": "DONE"}],
        "active_worker": None,
    }

class NativeFake:
    """Simulated trusted host; NEVER claimed to be installed runtime."""
    def __init__(self, data=None):
        self.data = record() if data is None else data
        self.trusted = True
        self.claims = 0
        self.existing_lease = None

    def read_exact(self, task_id):
        return deepcopy(self.data)

    def verify_read_provenance(self, data):
        return self.trusted

    def claim_if_unchanged(self, *, task_id, target_id, revision, worker):
        self.claims += 1
        if self.existing_lease or revision != self.data["revision"]:
            return LeaseAdmission(False, task_id, target_id, revision, worker, None)
        self.existing_lease = worker
        return LeaseAdmission(True, task_id, target_id, revision,
                              worker, NOW + timedelta(minutes=2))

def run(port, **kw):
    return resume(port, "QA_TASK", now=NOW, worker="GPT",
                  expected_target="INVENTHOR_OPERATOR", **kw)

class GateTests(unittest.TestCase):
    def deny(self, reason, port, **kw):
        with self.assertRaises(HandoffDenied) as ctx:
            run(port, **kw)
        self.assertEqual(ctx.exception.code, reason)

    def test_read_does_not_lease(self):
        p = NativeFake()
        view = run(p)
        self.assertEqual(view.mode, "READ_ONLY")
        self.assertEqual(view.remaining, ("real installed UI effect witness",))
        self.assertEqual(p.claims, 0)

    def test_native_lease_required(self):
        p = NativeFake()
        self.assertEqual(run(p, write=True).mode, "WRITE_CLAIMED")
        self.deny("NATIVE_CLAIM_DENIED", p, write=True)

    def test_old_cloud_not_current(self):
        p = NativeFake(); p.data["source"] = "GITHUB_SNAPSHOT"
        self.deny("NON_CANONICAL_SOURCE", p, write=True)
        p = NativeFake(); p.data["observed_at"] = (NOW - timedelta(hours=1)).isoformat()
        self.deny("STALE_HANDOFF", p, write=True)

    def test_not_from_trusted_host(self):
        p = NativeFake(); p.trusted = False
        self.deny("UNTRUSTED_LIVE_RESPONSE", p, write=True)

    def test_wrong_task_or_target(self):
        p = NativeFake(); p.data["task_id"] = "OTHER"
        self.deny("TASK_MISMATCH", p, write=True)
        p = NativeFake(); p.data["target_id"] = "DIFFERENT"
        self.deny("TARGET_MISMATCH", p, write=True)

    def test_unmet_dependency(self):
        p = NativeFake(); p.data["dependencies"][0]["state"] = "TODO"
        self.deny("DEPENDENCY_NOT_DONE", p, write=True)
        self.assertEqual(p.claims, 0)

    def test_never_steal_expired_or_unknown_lease(self):
        p = NativeFake(); p.data["active_worker"] = "CODEX"
        self.deny("LEASE_REQUIRES_RECONCILIATION", p, write=True)
        self.assertEqual(p.claims, 0)

    def test_orphan_doing_is_never_reclaimed_from_source_projection(self):
        p = NativeFake()
        p.data["state"] = "DOING"
        p.data["active_worker"] = None
        self.deny("ACTIVE_TASK_REQUIRES_NATIVE_RECONCILIATION", p, write=True)
        self.assertEqual(p.claims, 0)

    def test_doing_already_owned_requires_reconciliation_even_if_same_worker(self):
        p = NativeFake()
        p.data["state"] = "DOING"
        p.data["active_worker"] = "GPT"
        self.deny("ACTIVE_TASK_REQUIRES_NATIVE_RECONCILIATION", p, write=True)
        self.assertEqual(p.claims, 0)

    def test_terminal_no_replay(self):
        for state in ("DONE", "BLOCKED", "VERIFY", "ARCHIVED", "IDEA"):
            p = NativeFake(); p.data["state"] = state
            self.deny("NOT_WRITABLE_STATE", p, write=True)

    def test_invalid_revision_rejected(self):
        for rev in (None, 0, True, "7"):
            p = NativeFake(); p.data["revision"] = rev
            self.deny("REVISION_REQUIRED", p, write=True)

    def test_no_new_work_invented(self):
        p = NativeFake(); p.data["remaining"] = []
        self.deny("NO_EXPLICIT_REMAINING_WORK", p, write=True)

    def test_missing_dependency_proof(self):
        p = NativeFake(); del p.data["dependencies"]
        self.deny("DEPENDENCIES_MISSING_OR_INVALID", p, write=True)

    def test_bad_native_claim_rejected(self):
        class Forged(NativeFake):
            def claim_if_unchanged(self, **kw):
                return LeaseAdmission(True, "OTHER", "WRONG", 50,
                                      "FAKE", NOW + timedelta(minutes=2))
        self.deny("NATIVE_CLAIM_MISMATCH", Forged(), write=True)

    def test_source_pass_not_live_qa(self):
        self.assertEqual(run(NativeFake()).stage, "SOURCE_TESTED_NOT_INSTALLED")

    def test_interrupt_does_not_replay(self):
        p = NativeFake()
        run(p, write=True)
        p.data["revision"] += 1
        self.deny("NATIVE_CLAIM_DENIED", p, write=True)

    def test_checkpoint_draft_no_implicit_write(self):
        p = NativeFake()
        packet = run(p, write=True)
        draft = draft_next_checkpoint(packet,
            verified_completed=["operator version inspected"],
            still_remaining=["real UI check"], evidence_refs=["sha256:fixture"],
            stage="SOURCE_TESTED", next_action="verify installed UI")
        self.assertEqual(draft.expected_revision, 7)
        self.assertEqual(p.claims, 1)

    def test_checkpoint_requires_native_claim_and_evidence(self):
        packet = run(NativeFake())
        with self.assertRaises(HandoffDenied) as ctx:
            draft_next_checkpoint(packet, verified_completed=["x"],
                still_remaining=["y"], evidence_refs=["z"],
                stage="SOURCE_TESTED", next_action="next")
        self.assertEqual(ctx.exception.code, "HANDOFF_WITHOUT_NATIVE_CLAIM")
        claimed = run(NativeFake(), write=True)
        for done, remaining, refs in (([], ["y"], ["z"]),
                                      (["x"], ["y"], []),
                                      (["x"], [], ["z"])):
            with self.assertRaises(HandoffDenied):
                draft_next_checkpoint(claimed, verified_completed=done,
                    still_remaining=remaining, evidence_refs=refs,
                    stage="SOURCE_TESTED", next_action="next")

    def test_forged_live_qa_completion_denied(self):
        claimed = run(NativeFake(), write=True)
        with self.assertRaises(HandoffDenied) as ctx:
            draft_next_checkpoint(claimed, verified_completed=["x"],
                still_remaining=["y"], evidence_refs=["z"],
                stage="LIVE_QA_VERIFIED", next_action="next")
        self.assertEqual(ctx.exception.code, "TRUSTED_RELEASE_GATE_REQUIRED")

if __name__ == "__main__":
    unittest.main()
