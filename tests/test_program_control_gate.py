import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.program_control_gate import (
    ProgramContext, ProgramControlDenied, prepare_program_action,
)

NOW = datetime(2026, 10, 25, 19, 0, tzinfo=timezone.utc)


def context():
    return ProgramContext(
        program_id="DESIGNER_APP", program_version="1.0.0",
        program_runtime="REAL_RUNNING", bridge_connected=True,
        document_id="DOCUMENT_A", document_revision=7,
        opened_project_id="PROJECT_A",
        native_task_id="TASK_A", native_task_revision=12, observed_at=NOW,
        published_capabilities=("DESIGN_EDIT", "QA_SUBMIT", "UNDO"),
        owner_allowed_capabilities=("DESIGN_EDIT", "QA_SUBMIT"),
    )


def check(ctx=None, **kw):
    args=dict(expected_program_id="DESIGNER_APP",
              expected_project_id="PROJECT_A",
              expected_task_id="TASK_A", expected_task_revision=12,
              requested_capability="DESIGN_EDIT", risk="SAFE_REVERSIBLE",
              now=NOW)
    args.update(kw)
    return prepare_program_action(context() if ctx is None else ctx, **args)


class ProgramControlGateTests(unittest.TestCase):
    def assertDenied(self, code, context_change=None, **kwargs):
        with self.assertRaises(ProgramControlDenied) as ex:
            check(replace(context(), **(context_change or {})), **kwargs)
        self.assertEqual(ex.exception.code, code)

    def test_source_proposal_never_grants_action_even_if_claimed_ready(self):
        result=check()
        self.assertEqual(result.disposition, "NATIVE_PREFLIGHT_REQUIRED")
        self.assertFalse(result.native_context_authenticated)
        self.assertFalse(result.owner_permission_authenticated)
        self.assertFalse(result.owner_approval_granted)
        self.assertFalse(result.lease_claimed)
        self.assertFalse(result.program_changed)
        self.assertFalse(result.can_dispatch)

    def test_disconnected_or_stopped_real_program_blocks(self):
        for change in ({"bridge_connected":False},
                       {"program_runtime":"STOPPED"},
                       {"program_runtime":"UNKNOWN"}):
            with self.subTest(change=change):
                result=check(replace(context(), **change))
                self.assertEqual(result.disposition, "BLOCKED")
                self.assertEqual(result.reason, "ACTUAL_PROGRAM_BRIDGE_NOT_RUNNING")

    def test_wrong_program_never_gets_targeted(self):
        self.assertDenied("WRONG_OPEN_PROGRAM",
                          context_change={"program_id":"OTHER_APP"})

    def test_wrong_project_never_crosses_project_boundary(self):
        self.assertDenied("WRONG_OPEN_PROJECT",
                          context_change={"opened_project_id":"OTHER_PROJECT"})

    def test_stale_native_task_revision_blocks(self):
        self.assertDenied("STALE_NATIVE_TASK_REVISION",
                          context_change={"native_task_revision":11})

    def test_wrong_native_task_blocks(self):
        self.assertDenied("WRONG_NATIVE_TASK",
                          context_change={"native_task_id":"TASK_B"})

    def test_capability_must_be_published_by_real_program(self):
        result=check(requested_capability="CMD_ADMIN")
        self.assertEqual(result.disposition,"BLOCKED")
        self.assertEqual(result.reason,"PROGRAM_CAPABILITY_NOT_EXPOSED")

    def test_capability_must_have_owner_permission(self):
        result=check(requested_capability="UNDO")
        self.assertEqual(result.disposition,"BLOCKED")
        self.assertEqual(result.reason,"OWNER_CAPABILITY_NOT_ALLOWED")

    def test_privileged_action_is_owner_gated(self):
        result=check(risk="OWNER_GATE_REQUIRED")
        self.assertEqual(result.disposition,"BLOCKED")
        self.assertEqual(result.reason,"FRESH_OWNER_APPROVAL_REQUIRED")
        self.assertFalse(result.can_dispatch)

    def test_context_must_be_fresh_not_future(self):
        for observed in (NOW-timedelta(minutes=2),
                         NOW+timedelta(seconds=6)):
            with self.subTest(observed=observed):
                self.assertDenied("STALE_OR_FUTURE_PROGRAM_CONTEXT",
                                  context_change={"observed_at":observed})

    def test_invalid_boolean_is_not_true_permission(self):
        self.assertDenied("INVALID_BRIDGE_CONNECTED",
                          context_change={"bridge_connected":1})

    def test_invalid_revision_and_ids_rejected(self):
        self.assertDenied("INVALID_DOCUMENT_REVISION",
                          context_change={"document_revision":True})
        self.assertDenied("INVALID_PROGRAM_ID",
                          context_change={"program_id":"../secret"})

    def test_duplicate_capability_disallowed(self):
        self.assertDenied("DUPLICATE_CAPABILITIES",
                          context_change={"published_capabilities":
                                          ("DESIGN_EDIT","DESIGN_EDIT")})

    def test_malformed_nonhashable_capability_fails_closed(self):
        self.assertDenied("INVALID_PUBLISHED_CAPABILITY",
                          context_change={"published_capabilities":
                                          (["INVALID"],)})

    def test_unknown_risk_never_authorizes(self):
        self.assertDenied("INVALID_RISK_CLASS",risk="SILENT_ADMIN")

    def test_missing_real_context_fails_closed(self):
        with self.assertRaises(ProgramControlDenied) as ex:
            check({})
        self.assertEqual(ex.exception.code,"PROGRAM_CONTEXT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
