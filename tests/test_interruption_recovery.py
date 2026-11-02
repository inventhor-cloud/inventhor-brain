import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.interruption_recovery import (
    RecoverySnapshot, RecoveryDenied, advise_recovery,
)

NOW = datetime(2026, 10, 24, 9, 0, tzinfo=timezone.utc)


def snap():
    return RecoverySnapshot(
        task_id="TASK_BRAIN_SAFE", project_id="INVENTHOR_BRAIN",
        target_id="INVENTHOR_MAIN", revision=13,
        state="TODO", active_worker=None, observed_at=NOW,
        last_attempt="NONE", last_attempt_id=None,
        attempts_recorded=0, remaining_retry_budget=2,
        last_attempt_receipt_ref=None,
    )


class FakeNative:
    def __init__(self, fact=None):
        self.fact = snap() if fact is None else fact
        self.authenticated = True
        self.reads = 0
    def read_recovery(self, task_id):
        self.reads += 1
        return self.fact
    def verify_recovery(self, fact):
        return self.authenticated


def run(fact=None, host=None, **kw):
    return advise_recovery(
        host or FakeNative(fact), "TASK_BRAIN_SAFE",
        now=kw.pop("now", NOW),
        expected_project=kw.pop("expected_project", "INVENTHOR_BRAIN"),
        expected_target=kw.pop("expected_target", "INVENTHOR_MAIN"),
        expected_revision=kw.pop("expected_revision", 13), **kw,
    )


class RecoveryTests(unittest.TestCase):
    def denied(self, expected, fact=None, **kw):
        with self.assertRaises(RecoveryDenied) as e:
            run(fact, **kw)
        self.assertEqual(e.exception.code, expected)

    def test_first_task_requires_new_native_preflight(self):
        r = run()
        self.assertEqual(r.disposition, "FRESH_PREFLIGHT_REQUIRED")
        self.assertFalse(r.can_retry)
        self.assertFalse(r.can_claim)
        self.assertFalse(r.can_dispatch)

    def test_terminal_and_archived_never_replayed(self):
        for state in ("DONE", "ARCHIVED"):
            r = run(replace(snap(), state=state))
            self.assertEqual(r.disposition, "TERMINAL_NO_REPLAY")

    def test_unknown_outcome_requires_reconciliation(self):
        for status in ("PREPARED", "STARTED", "UNKNOWN", "CONFIRMED_SUCCEEDED"):
            s = replace(snap(), last_attempt=status, last_attempt_id="ATTEMPT_A",
                        attempts_recorded=1,
                        last_attempt_receipt_ref=("HOST_RECEIPT" if status == "CONFIRMED_SUCCEEDED" else None))
            r = run(s)
            self.assertEqual(r.disposition, "NATIVE_RECONCILIATION_REQUIRED")
            self.assertFalse(r.can_retry)

    def test_failed_with_receipt_still_not_auto_retry(self):
        f = replace(snap(), last_attempt="CONFIRMED_FAILED",
                    attempts_recorded=1, last_attempt_id="ATTEMPT_A",
                    last_attempt_receipt_ref="HOST_FAILURE_RECEIPT")
        r = run(f)
        self.assertEqual(r.disposition, "NATIVE_RETRY_POLICY_RECHECK")
        self.assertFalse(r.can_retry)
        self.assertEqual(
            run(replace(f, remaining_retry_budget=0)).reason,
            "RETRY_BUDGET_EXHAUSTED",
        )

    def test_foreign_owner_always_blocks(self):
        f = replace(snap(), active_worker="CODEX")
        self.assertEqual(run(f).disposition, "HOLD_ACTIVE_OWNER")

    def test_orphaned_running_does_not_resume_blindly(self):
        f = replace(snap(), state="DOING")
        self.assertEqual(run(f).reason, "ORPHAN_RUNNING_TASK")

    def test_blocked_or_verify_state_never_requeued(self):
        for state in ("BLOCKED", "VERIFY", "IDEA"):
            self.assertEqual(
                run(replace(snap(), state=state)).disposition,
                "HOLD_NOT_RUNNABLE",
            )

    def test_untrusted_native_proof_denied(self):
        host = FakeNative()
        host.authenticated = False
        self.denied("UNTRUSTED_RECOVERY_PROVENANCE", host=host)

    def test_version_or_scope_conflict(self):
        self.denied("RECOVERY_REVISION_CHANGED", replace(snap(), revision=14))
        self.denied("RECOVERY_SCOPE_MISMATCH",
                    replace(snap(), target_id="DIFFERENT"))
        self.denied("INVALID_EXPECTED_REVISION", expected_revision=True)

    def test_stale_or_future_denied(self):
        self.denied("RECOVERY_SNAPSHOT_STALE_OR_FUTURE",
                    replace(snap(), observed_at=NOW - timedelta(minutes=2)))
        self.denied("RECOVERY_SNAPSHOT_STALE_OR_FUTURE",
                    replace(snap(), observed_at=NOW + timedelta(seconds=10)))

    def test_fake_success_without_receipt_denied(self):
        self.denied("CONFIRMED_ATTEMPT_WITHOUT_RECEIPT",
                    replace(snap(), last_attempt="CONFIRMED_SUCCEEDED",
                            attempts_recorded=1, last_attempt_id="A"))

    def test_unrecognized_status_and_budgets_denied(self):
        self.denied("UNKNOWN_ATTEMPT_STATUS",
                    replace(snap(), last_attempt="DO_IT_AGAIN"))
        self.denied("RETRY_BUDGET_INVALID",
                    replace(snap(), remaining_retry_budget=-1))
        self.denied("RETRY_BUDGET_INVALID",
                    replace(snap(), remaining_retry_budget=True))

    def test_impossible_unconfirmed_receipt_denied(self):
        self.denied("UNCONFIRMED_ATTEMPT_RECEIPT_CONTRADICTION",
                    replace(snap(), last_attempt="UNKNOWN",
                            last_attempt_id="A", attempts_recorded=1,
                            last_attempt_receipt_ref="FAKE_RECEIPT"))

    def test_no_attempt_with_ghost_history_denied(self):
        self.denied("CONTRADICTORY_NO_ATTEMPT_HISTORY",
                    replace(snap(), attempts_recorded=1))
        self.denied("MISSING_ATTEMPT_HISTORY",
                    replace(snap(), last_attempt="STARTED"))


if __name__ == "__main__":
    unittest.main()
