import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from continuity.focus_adviser import (
    FocusEnvelope, FocusDenied, propose_next
)
from continuity.decision_trace import make_advisory_trace

NOW = datetime(2026, 10, 23, 11, 0, tzinfo=timezone.utc)


def scenario():
    focus = FocusEnvelope(
        plan_id="QA_OWNER_PLAN", plan_revision=11, plan_state="ACTIVE",
        remaining_dispatches=1, observed_at=NOW,
        project_id="INVENTHOR_QA", target_id="INVENTHOR_OPERATOR",
        focus_task_id="QA_PARENT",
        authorized_work_ids=("QA_SMALL_TASK",),
        allowed_capabilities=("SYSTEM_STATUS",),
    )
    tasks = [{
        "task_id": "QA_SMALL_TASK", "project_id": "INVENTHOR_QA",
        "target_id": "INVENTHOR_OPERATOR", "parent_id": "QA_PARENT",
        "state": "TODO", "task_kind": "TASK", "active_worker": None,
        "capability": "SYSTEM_STATUS", "dependencies": [],
        "priority": 0, "estimated_steps": 1,
    }]
    advisory = propose_next(focus, tasks, now=NOW, native_snapshot_verified=True)
    return focus, advisory


class DecisionTraceTests(unittest.TestCase):
    def test_trace_is_deterministic_and_not_receipt(self):
        focus, advisory = scenario()
        a = make_advisory_trace(focus, advisory)
        b = make_advisory_trace(focus, advisory)
        self.assertEqual(a.fingerprint, b.fingerprint)
        self.assertEqual(a.canonical_json, b.canonical_json)
        data = json.loads(a.as_json())
        self.assertFalse(data["dispatch_authorized"])
        self.assertFalse(data["qa_verified"])
        self.assertEqual(data["advisory"]["proposed_task_id"], "QA_SMALL_TASK")
        self.assertNotIn("signature", data)
        self.assertIn("NOT_NATIVE_RECEIPT", data["source_class"])

    def test_plan_revision_change_invalidates_decision(self):
        focus, advisory = scenario()
        old = make_advisory_trace(focus, advisory)
        new_focus = replace(focus, plan_revision=focus.plan_revision+1)
        with self.assertRaisesRegex(FocusDenied, "FORGED_PROPOSAL"):
            make_advisory_trace(new_focus, advisory)
        new_advisory = propose_next(
            new_focus, [{
                "task_id":"QA_SMALL_TASK", "project_id":"INVENTHOR_QA",
                "target_id":"INVENTHOR_OPERATOR", "parent_id":"QA_PARENT",
                "state":"TODO", "task_kind":"TASK", "active_worker":None,
                "capability":"SYSTEM_STATUS", "dependencies":[],
                "priority":0, "estimated_steps":1,
            }], now=NOW, native_snapshot_verified=True)
        self.assertNotEqual(
            old.fingerprint,
            make_advisory_trace(new_focus, new_advisory).fingerprint
        )

    def test_rejects_foreign_plan_or_forged_task(self):
        focus, advisory = scenario()
        with self.assertRaisesRegex(FocusDenied, "ADVISORY_PLAN_MISMATCH"):
            make_advisory_trace(
                replace(focus, plan_id="OTHER_PLAN"), advisory
            )
        with self.assertRaisesRegex(FocusDenied, "FORGED_PROPOSAL"):
            make_advisory_trace(
                focus, replace(advisory,
                    next_step=replace(advisory.next_step,
                                      task_id="NEW_UNAUTHORIZED_JOB"))
            )

    def test_cannot_mark_authorized(self):
        focus, advisory = scenario()
        with self.assertRaisesRegex(FocusDenied, "FORGED_DISPATCH_AUTHORITY"):
            make_advisory_trace(focus, replace(advisory, claim_authorized=True))

    def test_no_ready_step_still_has_a_trace(self):
        focus, advisory = scenario()
        amended = replace(advisory, next_step=None,
                          disposition="NO_AUTHORIZED_READY_WORK")
        r = make_advisory_trace(focus, amended)
        self.assertIsNone(json.loads(r.canonical_json)["proposed_task_id"])


if __name__ == "__main__":
    unittest.main()
