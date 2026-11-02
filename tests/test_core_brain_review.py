import json
import unittest
from dataclasses import replace
from datetime import timedelta

from continuity.core_brain_review import (
    CoreReviewDenied, prepare_core_brain_review,
)
from continuity.core_activation_gate import (
    CORE, REQUIRED_LINKS, ActivationInvalid, ComponentObservation,
    LinkObservation, CoreActivationSnapshot,
)
from test_brain_turn_integration import NOW, TestCli, TestHost


def activation():
    return CoreActivationSnapshot(
        task_id="TASK_QA",
        native_revision=12,
        observed_at=NOW,
        components=tuple(ComponentObservation(
            component_id=name, state="ACTIVE", artifact_sha256="a" * 64,
            signature_verified=True, rollback_verified=True,
            heartbeat_fresh=True,
        ) for name in CORE),
        links=tuple(LinkObservation(name, True, True)
                    for name in REQUIRED_LINKS),
        active_noncore_ids=(),
        unresolved_conflicts=(),
        qa_live_witness_verified=True,
    )


def check(snap=None, *, cli=None, host=None):
    return prepare_core_brain_review(
        cli or TestCli(), host or TestHost(), "TASK_QA",
        worker="GPT_SOURCE_WORKER", expected_target="INVENTHOR_OPERATOR",
        now=NOW, activation_snapshot=activation() if snap is None else snap,
    )


class CoreBrainReviewTests(unittest.TestCase):
    def test_complete_chain_still_cannot_dispatch_or_activate(self):
        host = TestHost()
        out = check(host=host)
        body = json.loads(out.as_json())
        self.assertEqual(out.task_id, "TASK_QA")
        self.assertEqual(out.canonical_revision, 12)
        self.assertEqual(
            out.brain_turn.advisory.next_step.task_id, "QA_SAFE_STEP"
        )
        self.assertEqual(out.activation.disposition, "NATIVE_REVIEW_REQUIRED")
        self.assertFalse(out.activation_performed)
        self.assertFalse(out.claim_authorized)
        self.assertFalse(out.can_dispatch)
        self.assertFalse(out.can_install)
        self.assertFalse(out.qa_live_verified)
        self.assertFalse(body["brain_turn"]["may_claim"])
        self.assertFalse(body["activation"]["native_snapshot_authenticated"])
        self.assertEqual(host.claims, 0)

    def test_missing_live_qa_blocks_even_if_brain_has_safe_advice(self):
        snap = replace(activation(), qa_live_witness_verified=False)
        out = check(snap)
        self.assertEqual(out.activation.disposition, "BLOCKED")
        self.assertIn("QA:LIVE_WITNESS_MISSING", out.activation.blockers)
        self.assertFalse(out.can_dispatch)

    def test_exact_task_identity_must_match(self):
        snap = replace(activation(), task_id="ANOTHER_TASK")
        with self.assertRaises(CoreReviewDenied) as error:
            check(snap)
        self.assertEqual(error.exception.code, "ACTIVATION_TASK_SCOPE_MISMATCH")

    def test_same_task_must_have_same_canonical_revision(self):
        snap = replace(activation(), native_revision=11)
        with self.assertRaises(CoreReviewDenied) as error:
            check(snap)
        self.assertEqual(
            error.exception.code, "ACTIVATION_NATIVE_REVISION_MISMATCH"
        )

    def test_stale_activation_facts_not_accepted(self):
        snap = replace(activation(), observed_at=NOW-timedelta(minutes=3))
        with self.assertRaises(ActivationInvalid) as error:
            check(snap)
        self.assertEqual(error.exception.code, "STALE_OR_FUTURE_SNAPSHOT")

    def test_one_noncore_module_blocks_not_deleted(self):
        snap = replace(activation(), active_noncore_ids=("CLEANUP",))
        out = check(snap)
        self.assertEqual(out.activation.disposition, "BLOCKED")
        self.assertIn("NONCORE_ACTIVE:CLEANUP", out.activation.blockers)
        self.assertFalse(out.activation.deletion_authorized)

    def test_brain_terminal_task_still_rejected(self):
        from continuity.brain_turn_integration import AgentTurnDenied
        cli, host = TestCli(), TestHost()
        cli.task["state"] = "DONE"
        host.task["state"] = "DONE"
        with self.assertRaises(AgentTurnDenied):
            check(activation(), cli=cli, host=host)
        self.assertEqual(host.claims, 0)

    def test_no_ready_task_does_not_create_work(self):
        host = TestHost()
        host.tasks[0]["state"] = "DONE"
        out = check(host=host)
        self.assertIsNone(out.brain_turn.advisory.next_step)
        self.assertFalse(out.can_dispatch)
        self.assertEqual(host.claims, 0)

    def test_untrusted_native_plan_does_not_get_activation(self):
        from continuity.brain_turn_integration import AgentTurnDenied
        host = TestHost()
        host.plan_verified = False
        with self.assertRaises(AgentTurnDenied):
            check(host=host)
        self.assertEqual(host.claims, 0)

    def test_fake_unsupported_snapshot_type_rejected(self):
        with self.assertRaises(CoreReviewDenied) as error:
            check({"task_id": "TASK_QA"})
        self.assertEqual(error.exception.code, "ACTIVATION_SNAPSHOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
