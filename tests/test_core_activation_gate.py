import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.core_activation_gate import (
    CORE, REQUIRED_LINKS, ActivationInvalid, ComponentObservation,
    LinkObservation, CoreActivationSnapshot, evaluate_core_activation,
)

NOW = datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def complete():
    return CoreActivationSnapshot(
        task_id="TASK_EXISTING_CANONICAL",
        native_revision=21,
        observed_at=NOW,
        components=tuple(ComponentObservation(
            component_id=cid, state="ACTIVE", artifact_sha256=HASH,
            signature_verified=True, rollback_verified=True,
            heartbeat_fresh=True,
        ) for cid in CORE),
        links=tuple(LinkObservation(lid, True, True) for lid in REQUIRED_LINKS),
        active_noncore_ids=(),
        unresolved_conflicts=(),
        qa_live_witness_verified=True,
    )


def review(**changes):
    return evaluate_core_activation(replace(complete(), **changes), now=NOW)


class CoreActivationGateTests(unittest.TestCase):
    def test_even_all_reported_green_cannot_activate(self):
        advice = review()
        self.assertEqual(advice.disposition, "NATIVE_REVIEW_REQUIRED")
        self.assertEqual(advice.blockers, ())
        self.assertFalse(advice.native_snapshot_authenticated)
        self.assertFalse(advice.activation_executed)
        self.assertFalse(advice.live_status_verified)
        self.assertFalse(advice.deployment_authorized)
        self.assertFalse(advice.deletion_authorized)

    def test_unknown_operator_does_not_look_active(self):
        c = list(complete().components)
        c[1] = replace(c[1], state="UNKNOWN")
        advice = review(components=tuple(c))
        self.assertIn("OPERATOR:NOT_ACTIVE", advice.blockers)
        self.assertEqual(advice.disposition, "BLOCKED")

    def test_missing_qa_witness_blocks_activation(self):
        advice = review(qa_live_witness_verified=False)
        self.assertIn("QA:LIVE_WITNESS_MISSING", advice.blockers)

    def test_missing_or_unverified_ack_blocks(self):
        links = list(complete().links)
        links[0] = replace(links[0], result_ack_verified=False)
        self.assertIn("BRAIN_OPERATOR:NO_AUTHENTICATED_ACK",
                      review(links=tuple(links)).blockers)
        self.assertIn("PROGRAM_ACTION_BRIDGE:MISSING",
                      review(links=tuple(links[:5] + links[6:])).blockers)

    def test_studio_design_is_mandatory_and_never_faked(self):
        incomplete = complete().components[:3] + complete().components[4:]
        self.assertIn("STUDIO_DESIGN:MISSING",
                      review(components=incomplete).blockers)
        self.assertIn("STUDIO_REAL_RENDER:MISSING",
                      review(links=complete().links[:-1]).blockers)

    def test_organizer_is_required_separately_no_second_ledger(self):
        incomplete = complete().components[:2] + complete().components[3:]
        self.assertIn("ORGANIZER:MISSING",
                      review(components=incomplete).blockers)
        self.assertEqual(CORE.count("ORGANIZER"), 1)
        self.assertEqual(CORE.count("QA_FACTORY"), 1)

    def test_noncore_is_not_reactivated_or_deleted(self):
        advice = review(active_noncore_ids=("VIKTORIJA", "CLEANUP"))
        self.assertIn("NONCORE_ACTIVE:VIKTORIJA", advice.blockers)
        self.assertIn("NONCORE_ACTIVE:CLEANUP", advice.blockers)
        self.assertFalse(advice.deletion_authorized)

    def test_local_merge_conflict_blocks_activation(self):
        advice = review(unresolved_conflicts=("OPERATOR_PR3_CLEANUP",))
        self.assertIn("UNRESOLVED_CONFLICT:OPERATOR_PR3_CLEANUP",
                      advice.blockers)

    def test_signature_rollback_and_freshness_are_separate(self):
        c = list(complete().components)
        c[0] = replace(c[0], signature_verified=False,
                       rollback_verified=False, heartbeat_fresh=False)
        blockers = review(components=tuple(c)).blockers
        for expected in ("INVENTHOR:SIGNER_NOT_VERIFIED",
                         "INVENTHOR:ROLLBACK_NOT_VERIFIED",
                         "INVENTHOR:HEARTBEAT_NOT_FRESH"):
            self.assertIn(expected, blockers)

    def test_missing_core_or_link_is_blocked(self):
        self.assertIn("QA_FACTORY:MISSING",
                      review(components=complete().components[:-1]).blockers)
        self.assertIn("QA_ORGANIZER:MISSING",
                      review(links=complete().links[:4]
                             + complete().links[5:]).blockers)

    def test_stale_snapshot_and_future_snapshot_are_rejected(self):
        for observed in (NOW - timedelta(minutes=2),
                         NOW + timedelta(seconds=6)):
            with self.subTest(observed=observed):
                with self.assertRaises(ActivationInvalid) as error:
                    review(observed_at=observed)
                self.assertEqual(error.exception.code,
                                 "STALE_OR_FUTURE_SNAPSHOT")

    def test_duplicates_and_unknown_components_rejected(self):
        for components in (
            complete().components + (complete().components[0],),
            complete().components[:-1] + (replace(
                complete().components[0], component_id="UNREGISTERED"),),
        ):
            with self.subTest(components=components):
                with self.assertRaises(ActivationInvalid):
                    review(components=components)

    def test_invalid_types_do_not_count_as_verified(self):
        components = list(complete().components)
        components[0] = replace(components[0], signature_verified=1)
        with self.assertRaises(ActivationInvalid):
            review(components=tuple(components))
        with self.assertRaises(ActivationInvalid):
            review(qa_live_witness_verified="true")
        with self.assertRaises(ActivationInvalid):
            review(native_revision=True)
        with self.assertRaises(ActivationInvalid):
            review(task_id="../task")

    def test_malformed_hash_and_noncore_duplicates_denied(self):
        c = list(complete().components)
        c[0] = replace(c[0], artifact_sha256="not-a-sha")
        with self.assertRaises(ActivationInvalid):
            review(components=tuple(c))
        with self.assertRaises(ActivationInvalid):
            review(active_noncore_ids=("SIDE_APP", "SIDE_APP"))


if __name__ == "__main__":
    unittest.main()
