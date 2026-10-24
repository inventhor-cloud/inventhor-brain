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
            "id": "TASK_QA", "state": "TODO",
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

    def read_exact(self, task_id):
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
        return self.plan_verified

    def read_actor_context(self, task_id, worker):
        self.actor_calls += 1
        return self.actor

    def verify_actor_context(self, context):
        return self.actor_verified


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

    def test_expired_actor_cannot_propose(self):
        from continuity.agent_action_origin import OriginDenied
        h = TestHost()
        h.actor = replace(h.actor, expires_at=NOW)
        with self.assertRaises(OriginDenied) as ex:
            run(host=h)
        self.assertEqual(ex.exception.code, "NATIVE_CONTEXT_EXPIRED")


if __name__ == "__main__":
    unittest.main()
