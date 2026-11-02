import json
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.agent_action_origin import NativeActorContext
from continuity.brain_turn_integration import (
    AgentTurnDenied, prepare_brain_turn,
)
from continuity.focus_adviser import FocusEnvelope, FocusDenied
from continuity.live_handoff_gate import SOURCE
from continuity.native_readonly_attachment import IntegrationDenied
from continuity.organizer_cli_reader import NativeHandoffRead

NOW = datetime(2026, 10, 23, 17, 30, tzinfo=timezone.utc)


class TestCli:
    def __init__(self):
        self.task = {
            "id": "TASK_QA", "state": "TODO", "owner": "MAIN",
            "project_id": "INVENTHOR_QA", "target_id": "INVENTHOR_OPERATOR",
            "checkpoint_stage": "QA_SOURCE_ONLY",
            "completed": ["draft verified"],
            "remaining": ["independent installed witness"],
            "next_action": "native QA preflight",
        }
        self.calls = 0

    def read_task(self, task_id):
        self.calls += 1
        return NativeHandoffRead(task_id, SOURCE, deepcopy(self.task))


class TestHost:
    def __init__(self):
        self.task = {
            "source": SOURCE, "task_id": "TASK_QA", "project_id": "INVENTHOR_QA",
            "owner": "MAIN",
            "target_id": "INVENTHOR_OPERATOR", "revision": 12,
            "observed_at": NOW.isoformat(), "state": "TODO",
            "stage": "QA_SOURCE_ONLY", "completed": ["draft verified"],
            "remaining": ["independent installed witness"],
            "evidence_refs": [], "blocker": "",
            "next_action": "native QA preflight", "dependencies": [],
            "active_worker": None,
        }
        self.focus = FocusEnvelope(
            plan_id="PLAN_QA", project_id="INVENTHOR_QA",
            focus_task_id="TASK_QA", target_id="INVENTHOR_OPERATOR",
            plan_revision=7, plan_state="ACTIVE", remaining_dispatches=1,
            observed_at=NOW, authorized_work_ids=("QA_SAFE_STEP",),
            allowed_capabilities=("readonly.status",),
        )
        self.tasks = [{
            "task_id": "QA_SAFE_STEP", "project_id": "INVENTHOR_QA",
            "target_id": "INVENTHOR_OPERATOR", "parent_id": "TASK_QA",
            "state": "TODO", "task_kind": "TASK", "active_worker": None,
            "capability": "readonly.status", "dependencies": [],
            "priority": 0, "estimated_steps": 1,
        }]
        self.actor = NativeActorContext(
            task_id="TASK_QA", plan_id="PLAN_QA", plan_revision=7,
            actor_agent="GPT", worker_id="GPT_SOURCE_WORKER",
            session_id="SOURCE_TEST_SESSION", observed_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            native_evidence_ref="SIMULATED_HOST_ONLY",
        )
        self.plan_verified = True
        self.actor_verified = True
        self.source_verified = True
        self.claims = 0
        self.focus_calls = 0
        self.actor_calls = 0
        self.native_reads = 0
        self.plan_verifications = 0
        self.epoch_calls = 0
        self.epoch_ok = True
        self.last_epoch = None

    def read_exact(self, task_id):
        self.native_reads += 1
        return deepcopy(self.task)

    def verify_read_provenance(self, record):
        return self.source_verified

    def claim_if_unchanged(self, **kwargs):
        self.claims += 1
        raise AssertionError("READ_ONLY_MUST_NEVER_CLAIM")

    def read_focus_snapshot(self, task_id):
        self.focus_calls += 1
        return self.focus, deepcopy(self.tasks)

    def verify_focus_snapshot(self, read, focus, tasks):
        self.plan_verifications += 1
        return self.plan_verified

    def read_actor_context(self, task_id, worker):
        self.actor_calls += 1
        return self.actor

    def verify_actor_context(self, context):
        return self.actor_verified

    def verify_canonical_epoch(self, scope):
        # Synthetic native test host only. Real Main MUST compare under
        # its original Organizer lock, not trust incoming scope as proof.
        self.epoch_calls += 1
        self.last_epoch = scope
        return self.epoch_ok


def run(cli=None, host=None, **kwargs):
    return prepare_brain_turn(
        cli or TestCli(), host or TestHost(), "TASK_QA",
        worker=kwargs.pop("worker", "GPT_SOURCE_WORKER"),
        expected_target="INVENTHOR_OPERATOR", now=kwargs.pop("now", NOW),
        **kwargs,
    )


class BrainTurnIntegrationTests(unittest.TestCase):
    def denied(self, reason, cli=None, host=None):
        with self.assertRaises(AgentTurnDenied) as ex:
            run(cli, host)
        self.assertEqual(ex.exception.code, reason)
        if host:
            self.assertEqual(host.claims, 0)

    def test_complete_chain_one_safe_step_with_no_side_effect(self):
        cli, host = TestCli(), TestHost()
        result = run(cli, host)
        body = json.loads(result.as_json())
        self.assertEqual(result.attachment.task_id, "TASK_QA")
        self.assertEqual(result.advisory.next_step.task_id, "QA_SAFE_STEP")
        self.assertEqual(result.actor.actor_agent, "GPT")
        self.assertEqual(result.actor.origin, "AUTOMATED_AGENT")
        self.assertEqual(result.trace.fingerprint.__len__(), 64)
        self.assertFalse(body["may_claim"])
        self.assertFalse(body["may_install"])
        self.assertFalse(body["may_send_message"])
        self.assertFalse(body["native_runtime_installed_verified"])
        self.assertEqual(host.claims, 0)
        self.assertEqual(host.focus_calls, 1)
        self.assertEqual(host.actor_calls, 1)
        self.assertEqual(host.native_reads, 2)
        self.assertEqual(host.plan_verifications, 2)
        self.assertEqual(host.epoch_calls, 1)
        self.assertEqual(host.last_epoch.task_id, "TASK_QA")
        self.assertEqual(host.last_epoch.task_revision, 12)
        self.assertEqual(host.last_epoch.plan_id, "PLAN_QA")
        self.assertEqual(host.last_epoch.plan_revision, 7)
        self.assertEqual(host.last_epoch.worker_id, "GPT_SOURCE_WORKER")
        self.assertEqual(host.last_epoch.actor_session_id, "SOURCE_TEST_SESSION")
        self.assertEqual(host.last_epoch.task_state_sha256,
                         result.attachment.native_task_state_sha256)
        self.assertEqual(cli.calls, 1)

    def test_wrong_owner_scope_rejected_before_decision(self):
        h = TestHost()
        h.focus = replace(h.focus, focus_task_id="OTHER_TASK")
        self.denied("FOCUS_TASK_SCOPE_MISMATCH", host=h)
        self.assertEqual(h.actor_calls, 0)

    def test_wrong_project_rejected(self):
        h = TestHost()
        h.focus = replace(h.focus, project_id="OTHER_PROJECT")
        self.denied("FOCUS_TASK_SCOPE_MISMATCH", host=h)

    def test_terminal_focus_cannot_reopen_child_work(self):
        for state in ("DONE", "ARCHIVED"):
            c, h = TestCli(), TestHost()
            c.task["state"] = state
            h.task["state"] = state
            with self.subTest(state=state):
                self.denied("FOCUS_TASK_TERMINAL_NO_REPLAY", cli=c, host=h)
            self.assertEqual(h.focus_calls, 0)
            self.assertEqual(h.actor_calls, 0)

    def test_orphan_doing_parent_requires_native_reconciliation(self):
        c, h = TestCli(), TestHost()
        c.task["state"] = "DOING"
        h.task["state"] = "DOING"
        self.denied("FOCUS_ORPHAN_REQUIRES_NATIVE_RECONCILIATION", cli=c, host=h)
        self.assertEqual(h.focus_calls, 0)
        self.assertEqual(h.actor_calls, 0)

    def test_untrusted_owner_plan_rejected(self):
        h = TestHost()
        h.plan_verified = False
        self.denied("FOCUS_PROVENANCE_NOT_VERIFIED", host=h)
        self.assertEqual(h.actor_calls, 0)

    def test_stale_plan_rejected_without_exec(self):
        h = TestHost()
        h.focus = replace(h.focus, observed_at=NOW - timedelta(minutes=5))
        with self.assertRaises(FocusDenied) as ex:
            run(host=h)
        self.assertEqual(ex.exception.code, "STALE_FOCUS_SNAPSHOT")
        self.assertEqual(h.claims, 0)
        self.assertEqual(h.actor_calls, 0)

    def test_previously_completed_plan_cannot_dispatch(self):
        h = TestHost()
        h.focus = replace(h.focus, plan_state="COMPLETED")
        with self.assertRaises(FocusDenied) as ex:
            run(host=h)
        self.assertEqual(ex.exception.code, "PLAN_NOT_ACTIVE")
        self.assertEqual(h.claims, 0)

    def test_actor_cannot_switch_task_or_plan(self):
        for proof in (
            replace(TestHost().actor, task_id="OTHER_TASK"),
            replace(TestHost().actor, plan_id="OTHER_PLAN"),
            replace(TestHost().actor, plan_revision=99),
            replace(TestHost().actor, worker_id="WRONG_WORKER"),
        ):
            h = TestHost()
            h.actor = proof
            with self.subTest(proof=proof):
                self.denied("ACTOR_TASK_PLAN_SCOPE_MISMATCH", host=h)

    def test_false_actor_provenance_denied(self):
        h = TestHost()
        h.actor_verified = False
        from continuity.agent_action_origin import OriginDenied
        with self.assertRaises(OriginDenied) as ex:
            run(host=h)
        self.assertEqual(ex.exception.code, "NATIVE_CONTEXT_NOT_VERIFIED")
        self.assertEqual(h.claims, 0)

    def test_changed_cli_state_blocks_chain_before_host_plan(self):
        h = TestHost()
        c = TestCli()
        c.task["state"] = "DOING"
        with self.assertRaises(IntegrationDenied):
            run(cli=c, host=h)
        self.assertEqual(h.focus_calls, 0)
        self.assertEqual(h.claims, 0)

    def test_native_read_not_self_attested(self):
        h = TestHost()
        h.source_verified = False
        with self.assertRaises(IntegrationDenied):
            run(host=h)
        self.assertEqual(h.focus_calls, 0)
        self.assertEqual(h.claims, 0)

    def test_no_next_step_does_not_invent_or_send_work(self):
        h = TestHost()
        h.tasks[0]["state"] = "DONE"
        result = run(host=h)
        self.assertIsNone(result.advisory.next_step)
        self.assertFalse(result.may_claim)
        self.assertFalse(result.actor.may_send_chat_message)

    def test_task_revision_changed_during_actor_lookup_blocks_advice(self):
        class RacingHost(TestHost):
            def read_actor_context(self, task_id, worker):
                proof = super().read_actor_context(task_id, worker)
                self.task["revision"] += 1
                return proof

        h = RacingHost()
        self.denied("NATIVE_TASK_CHANGED_DURING_ADVICE", host=h)
        self.assertEqual(h.native_reads, 2)
        self.assertEqual(h.claims, 0)

    def test_lease_owner_or_task_state_changed_during_advice_blocks(self):
        for name, value in (
            ("active_worker", "CODEX"),
            ("state", "DOING"),
            ("project_id", "OTHER_PROJECT"),
        ):
            class RacingHost(TestHost):
                def read_actor_context(self, task_id, worker):
                    proof = super().read_actor_context(task_id, worker)
                    self.task[name] = value
                    return proof

            h = RacingHost()
            with self.subTest(name=name):
                self.denied("NATIVE_TASK_CHANGED_DURING_ADVICE", host=h)
            self.assertEqual(h.claims, 0)

    def test_final_native_read_must_still_authenticate(self):
        class RevokedHost(TestHost):
            def read_actor_context(self, task_id, worker):
                proof = super().read_actor_context(task_id, worker)
                self.source_verified = False
                return proof

        h = RevokedHost()
        self.denied("NATIVE_FINAL_TASK_RECHECK_DENIED", host=h)
        self.assertEqual(h.claims, 0)

    def test_final_owner_plan_verification_catches_superseded_plan(self):
        class SupersededHost(TestHost):
            def verify_focus_snapshot(self, read, focus, tasks):
                self.plan_verifications += 1
                return self.plan_verifications == 1

        h = SupersededHost()
        self.denied("FOCUS_CHANGED_DURING_ADVICE", host=h)
        self.assertEqual(h.plan_verifications, 2)
        self.assertEqual(h.claims, 0)

    def test_raw_evidence_and_checkpoint_drift_block_even_same_revision(self):
        # A provider-redacted display may conceal the difference between
        # two private evidence references. Compare trusted RAW digest.
        for field, replacement in (
            ("evidence_refs", ["https://example.test/a?sig=second"]),
            ("completed", ["different proof"]),
            ("remaining", ["another pending native step"]),
            ("stage", "DIFFERENT_QA_STAGE"),
            ("blocker", "NEW_NATIVE_BLOCKER"),
            ("owner", "CODEX"),
            ("next_action", "different native work"),
        ):
            class RacingHost(TestHost):
                def read_actor_context(self, task_id, worker):
                    proof = super().read_actor_context(task_id, worker)
                    self.task[field] = replacement
                    return proof

            h = RacingHost()
            if field == "evidence_refs":
                h.task["evidence_refs"] = ["https://example.test/a?sig=first"]
                # The CLI's legacy evidence must match initial native data.
                cli = TestCli()
                cli.task["evidence"] = h.task["evidence_refs"][0]
            else:
                cli = TestCli()
            with self.subTest(field=field):
                self.denied("NATIVE_TASK_CHANGED_DURING_ADVICE",
                            cli=cli, host=h)
            self.assertEqual(h.claims, 0)

    def test_task_assignment_owner_changes_without_lease_denied(self):
        class RacingHost(TestHost):
            def read_actor_context(self, task_id, worker):
                proof = super().read_actor_context(task_id, worker)
                self.task["owner"] = "OTHER_OWNER"
                return proof

        host = RacingHost()
        self.denied("NATIVE_TASK_CHANGED_DURING_ADVICE", host=host)
        self.assertEqual(host.claims, 0)

    def test_dependency_state_change_without_revision_increment_blocks(self):
        class RacingHost(TestHost):
            def read_actor_context(self, task_id, worker):
                proof = super().read_actor_context(task_id, worker)
                self.task["dependencies"] = [
                    {"task_id": "NEW_DEP", "state": "TODO"}]
                return proof

        h = RacingHost()
        self.denied("NATIVE_TASK_CHANGED_DURING_ADVICE", host=h)
        self.assertEqual(h.claims, 0)

    def test_last_read_timestamp_must_not_go_backwards(self):
        class ReplayedHost(TestHost):
            def read_actor_context(self, task_id, worker):
                proof = super().read_actor_context(task_id, worker)
                self.task["observed_at"] = (
                    NOW - timedelta(seconds=2)).isoformat()
                return proof

        h = ReplayedHost()
        self.denied("NATIVE_TASK_OBSERVATION_ROLLED_BACK", host=h)
        self.assertEqual(h.claims, 0)

    def test_missing_canonical_epoch_adapter_cannot_return_advice(self):
        class MissingEpochPort(TestHost):
            verify_canonical_epoch = None

        h = MissingEpochPort()
        self.denied("NATIVE_CANONICAL_EPOCH_VERIFIER_UNAVAILABLE", host=h)
        self.assertEqual(h.claims, 0)

    def test_canonical_epoch_denial_rejects_stale_snapshot(self):
        h = TestHost()
        h.epoch_ok = False
        self.denied("NATIVE_CANONICAL_EPOCH_NOT_VERIFIED", host=h)
        self.assertEqual(h.epoch_calls, 1)
        self.assertEqual(h.claims, 0)

    def test_native_epoch_boolean_is_strict_not_truthiness(self):
        for false_proof in (1, "true", None, object()):
            h = TestHost()
            h.epoch_ok = false_proof
            with self.subTest(proof_type=type(false_proof).__name__):
                self.denied("NATIVE_CANONICAL_EPOCH_NOT_VERIFIED", host=h)
            self.assertEqual(h.claims, 0)

    def test_epoch_check_must_not_raise_or_relabel_failure_as_success(self):
        class BrokenEpochHost(TestHost):
            def verify_canonical_epoch(self, scope):
                raise OSError("native lock unavailable")

        h = BrokenEpochHost()
        self.denied("NATIVE_CANONICAL_EPOCH_VERIFIER_UNAVAILABLE", host=h)
        self.assertEqual(h.claims, 0)

    def test_epoch_proof_happens_after_second_provenance_check(self):
        class OrderHost(TestHost):
            def verify_canonical_epoch(self, scope):
                self.epoch_calls += 1
                if self.native_reads != 2 or self.plan_verifications != 2:
                    raise AssertionError("NOT_FINAL_NATIVE_EPOCH")
                return True

        h = OrderHost()
        out = run(host=h)
        self.assertEqual(out.advisory.next_step.task_id, "QA_SAFE_STEP")
        self.assertEqual(h.epoch_calls, 1)
        self.assertEqual(h.claims, 0)

    def test_final_host_exception_never_yields_advice(self):
        class DisconnectedHost(TestHost):
            def read_exact(self, task_id):
                if self.native_reads:
                    raise OSError("native connection lost")
                return super().read_exact(task_id)

        h = DisconnectedHost()
        self.denied("NATIVE_FINAL_TASK_READ_UNAVAILABLE", host=h)
        self.assertEqual(h.claims, 0)

    def test_expired_actor_cannot_propose(self):
        from continuity.agent_action_origin import OriginDenied
        h = TestHost()
        h.actor = replace(h.actor, expires_at=NOW)
        with self.assertRaises(OriginDenied) as ex:
            run(host=h)
        self.assertEqual(ex.exception.code, "NATIVE_CONTEXT_EXPIRED")


if __name__ == "__main__":
    unittest.main()
