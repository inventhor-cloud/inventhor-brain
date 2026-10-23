import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from continuity.focus_adviser import (
    Advisory, FocusDenied, FocusEnvelope, propose_next
)

NOW = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)


def focus():
    return FocusEnvelope(
        plan_id="QA_070_OWNER_PLAN", project_id="INVENTHOR_QA",
        focus_task_id="IDEA_QA_CANONICAL", target_id="INVENTHOR_OPERATOR",
        plan_revision=4, plan_state="ACTIVE", remaining_dispatches=2,
        observed_at=NOW,
        authorized_work_ids=("STEP_A", "STEP_B"),
        allowed_capabilities=("SYSTEM_STATUS", "HASH"),
    )


def tasks():
    return [
        {
            "task_id": "STEP_A", "project_id": "INVENTHOR_QA",
            "target_id": "INVENTHOR_OPERATOR",
            "parent_id": "IDEA_QA_CANONICAL", "state": "TODO",
            "task_kind": "TASK", "active_worker": None,
            "capability": "SYSTEM_STATUS",
            "dependencies": [], "priority": 0, "estimated_steps": 1,
        },
        {
            "task_id": "STEP_B", "project_id": "INVENTHOR_QA",
            "target_id": "INVENTHOR_OPERATOR",
            "parent_id": "IDEA_QA_CANONICAL", "state": "TODO",
            "task_kind": "TASK", "active_worker": None,
            "capability": "HASH",
            "dependencies": [{"task_id": "STEP_A", "state": "TODO"}],
            "priority": 1, "estimated_steps": 2,
        },
    ]


def rank(ts=None, plan=None, now=NOW, verified=True):
    return propose_next(
        focus() if plan is None else plan,
        tasks() if ts is None else ts,
        now=now, native_snapshot_verified=verified,
    )


class FocusAdviserTests(unittest.TestCase):
    def denied(self, expected, *, ts=None, plan=None, now=NOW, verified=True):
        with self.assertRaises(FocusDenied) as ctx:
            rank(ts=ts, plan=plan, now=now, verified=verified)
        self.assertEqual(ctx.exception.code, expected)

    def test_picks_first_existing_small_safe_step(self):
        a = rank()
        self.assertIsInstance(a, Advisory)
        self.assertEqual(a.next_step.task_id, "STEP_A")
        self.assertEqual(a.next_step.plan_revision, 4)
        self.assertFalse(a.claim_authorized)
        self.assertFalse(a.next_step.can_execute_from_proposal)
        self.assertTrue(a.next_step.requires_fresh_native_claim)
        self.assertIn(("STEP_B", "DEPENDENCY_NOT_CONFIRMED_DONE"), a.deferred)

    def test_moves_to_next_after_verified_done(self):
        t = tasks()
        t[0]["state"] = "DONE"
        t[1]["dependencies"][0]["state"] = "DONE"
        result = rank(ts=t)
        self.assertEqual(result.next_step.task_id, "STEP_B")
        self.assertIn(("STEP_A", "NOT_READY_STATE_DONE"), result.deferred)

    def test_never_replays_done_work(self):
        t = tasks()
        t[0]["state"] = "DONE"
        out = rank(ts=t)
        self.assertIsNone(out.next_step)
        self.assertEqual(out.disposition, "NO_AUTHORIZED_READY_WORK")

    def test_denies_public_mirror_without_trusted_host(self):
        self.denied("NATIVE_SNAPSHOT_REQUIRED", verified=False)

    def test_completed_or_paused_plan_not_selected(self):
        for state in ("COMPLETED", "PAUSED", "CANCELLED", "UNKNOWN"):
            d = dict(focus().__dict__)
            d["plan_state"] = state
            self.denied("PLAN_NOT_ACTIVE", plan=FocusEnvelope(**d))

    def test_plan_dispatch_budget_must_be_available(self):
        for budget in (0, -1, 65, True, "2", None):
            d = dict(focus().__dict__)
            d["remaining_dispatches"] = budget
            self.denied("PLAN_BUDGET_EXHAUSTED_OR_INVALID",
                        plan=FocusEnvelope(**d))

    def test_stale_and_future_plan(self):
        self.denied("STALE_FOCUS_SNAPSHOT",
                    now=NOW + timedelta(minutes=2))
        self.denied("STALE_FOCUS_SNAPSHOT",
                    now=NOW - timedelta(seconds=10))

    def test_plan_identity_and_revision_required(self):
        f = focus()
        d = dict(f.__dict__)
        d["plan_revision"] = "4"
        self.denied("INVALID_PLAN_REVISION", plan=FocusEnvelope(**d))
        d["plan_revision"] = 4
        d["plan_id"] = "../plan"
        self.denied("UNSAFE_PLAN_ID", plan=FocusEnvelope(**d))

    def test_duplicates_rejected_not_last_writer_wins(self):
        t = tasks()
        t.append(deepcopy(t[0]))
        self.denied("DUPLICATE_TASK_ID", ts=t)

    def test_out_of_focus_does_not_preempt(self):
        t = tasks()
        t[0]["parent_id"] = "OTHER_GOAL"
        out = rank(ts=t)
        self.assertIsNone(out.next_step)
        self.assertIn(("STEP_A", "OUTSIDE_OWNER_FOCUS"), out.deferred)

    def test_wrong_project_does_not_dispatch(self):
        t = tasks()
        t[0]["project_id"] = "UNRELATED_PROJECT"
        out = rank(ts=t)
        self.assertIn(("STEP_A", "OUTSIDE_OWNER_FOCUS"), out.deferred)

    def test_wrong_target_does_not_dispatch(self):
        t = tasks()
        t[0]["target_id"] = "INVENTHOR_MAIN"
        out = rank(ts=t)
        self.assertIn(("STEP_A", "OUTSIDE_OWNER_FOCUS"), out.deferred)

    def test_owner_or_lease_blocks_step(self):
        t = tasks()
        t[0]["active_worker"] = "CODEX"
        out = rank(ts=t)
        self.assertIn(("STEP_A", "OWNER_OR_LEASE_PRESENT"), out.deferred)

    def test_no_unsafe_capability(self):
        t = tasks()
        t[0]["capability"] = "UAC_SIGN_PRODUCTION"
        out = rank(ts=t)
        self.assertIn(("STEP_A", "CAPABILITY_NOT_IN_APPROVED_PLAN"),
                      out.deferred)

    def test_missing_dependency_proof(self):
        t = tasks()
        t[0]["dependencies"] = None
        out = rank(ts=t)
        self.assertIn(("STEP_A", "DEPENDENCY_PROOF_MISSING"), out.deferred)

    def test_dependency_not_done_is_blocked(self):
        t = tasks()
        t[0]["dependencies"] = [{"task_id": "STEP_B", "state": "TODO"}]
        out = rank(ts=t)
        self.assertIsNone(out.next_step)

    def test_submitted_dependency_state_is_not_authority(self):
        t = tasks()
        t[0]["dependencies"] = [{"task_id": "NO_SUCH_TASK", "state": "DONE"}]
        out = rank(ts=t)
        self.assertIn(("STEP_A", "DEPENDENCY_NOT_CONFIRMED_DONE"),
                      out.deferred)

    def test_nonfinite_and_unbounded_work_not_selected(self):
        for bad in (0, 9, 100, "1"):
            t = tasks()
            t[0]["estimated_steps"] = bad
            out = rank(ts=t)
            self.assertIn(("STEP_A", "UNBOUNDED_STEPS"), out.deferred)
        t = tasks()
        t[0]["task_kind"] = "PROJECT"
        out = rank(ts=t)
        self.assertIn(("STEP_A", "NOT_FINITE_TASK"), out.deferred)

    def test_ideas_not_auto_started(self):
        t = tasks()
        t[0]["state"] = "IDEA"
        result = rank(ts=t)
        self.assertIsNone(result.next_step)

    def test_explicit_plan_work_ids_required(self):
        f = focus()
        d = dict(f.__dict__)
        d["authorized_work_ids"] = ()
        self.denied("EXPLICIT_WORK_IDS_REQUIRED", plan=FocusEnvelope(**d))

    def test_duplicate_approved_ids_denied(self):
        f = focus()
        d = dict(f.__dict__)
        d["authorized_work_ids"] = ("STEP_A", "STEP_A")
        self.denied("DUPLICATE_POLICY_ENTRY", plan=FocusEnvelope(**d))

    def test_unknown_state_fails_closed(self):
        t = tasks()
        t[0]["state"] = "FAKE_LIVE_QA"
        self.denied("UNKNOWN_TASK_STATE", ts=t)

    def test_bounded_inputs(self):
        self.denied("TASK_SET_TOO_LARGE", ts=tasks() * 40)

    def test_priority_bounded_and_deterministic(self):
        t = tasks()
        t[0]["priority"] = True
        out = rank(ts=t)
        self.assertIn(("STEP_A", "PRIORITY_NOT_VALIDATED"), out.deferred)
        t = tasks()
        t[1]["dependencies"] = []
        t[1]["priority"] = 0
        t[1]["estimated_steps"] = 1
        self.assertEqual(rank(ts=t).next_step.task_id, "STEP_A")

    def test_missing_allowed_entry_does_not_invent_task(self):
        t = tasks()
        t.pop(0)
        result = rank(ts=t)
        self.assertIn(("STEP_A", "NOT_IN_LIVE_SNAPSHOT"),
                      result.deferred)


if __name__ == "__main__":
    unittest.main()
