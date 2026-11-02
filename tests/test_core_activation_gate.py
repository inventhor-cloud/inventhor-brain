import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.core_activation_gate import (
    CORE, REQUIRED_LINKS, ActivationInvalid, ComponentObservation,
    LegacyDependencyEdge,
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
        noncore_dependency_inventory_complete=True,
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


    def test_missing_native_dependency_inventory_blocks_even_green_source(self):
        out = review(noncore_dependency_inventory_complete=False)
        self.assertEqual(out.disposition, "BLOCKED")
        self.assertIn("NONCORE_DEPENDENCY_INVENTORY:NOT_VERIFIED", out.blockers)
        self.assertFalse(out.native_snapshot_authenticated)
        self.assertFalse(out.deployment_authorized)

    def test_required_core_to_old_factory_edge_blocks_clean_activation(self):
        out = review(core_to_noncore_dependency_edges=(
            LegacyDependencyEdge("OPERATOR", "windows.software-factory"),))
        self.assertIn(
            "CORE_NONCORE_DEPENDENCY:OPERATOR:windows.software-factory",
            out.blockers)
        self.assertFalse(out.deletion_authorized)

    def test_legacy_installer_and_startup_route_blocks_even_with_no_active_plugins(self):
        out = review(legacy_activation_routes=(
            "DEPLOYER_V2", "MODULE_STARTUP_DISCOVERY"))
        self.assertIn("LEGACY_ACTIVATION_ROUTE:DEPLOYER_V2", out.blockers)
        self.assertIn("LEGACY_ACTIVATION_ROUTE:MODULE_STARTUP_DISCOVERY",
                      out.blockers)

    def test_multiple_legacy_dependency_edges_are_reviewed_separately(self):
        edges = (
            LegacyDependencyEdge("OPERATOR", "windows.software-factory"),
            LegacyDependencyEdge("STUDIO_DESIGN", "windows.legacy-render"),
        )
        out = review(core_to_noncore_dependency_edges=edges)
        self.assertEqual(
            len([b for b in out.blockers
                 if b.startswith("CORE_NONCORE_DEPENDENCY:")]), 2)

    def test_duplicate_or_unknown_legacy_edges_are_rejected(self):
        e = LegacyDependencyEdge("OPERATOR", "windows.cleanup")
        for edges in (
            (e, e),
            (LegacyDependencyEdge("OUTSIDE", "windows.cleanup"),),
            (LegacyDependencyEdge("OPERATOR", "QA_FACTORY"),),
            (("OPERATOR", "windows.cleanup"),),
        ):
            with self.subTest(edges=edges):
                with self.assertRaises(ActivationInvalid):
                    review(core_to_noncore_dependency_edges=edges)

    def test_invalid_or_duplicate_legacy_routes_are_rejected(self):
        for routes in (
            ("MODULE_MENU", "MODULE_MENU"),
            ("../../legacy",),
            ("MODULE_MENU", 42),
        ):
            with self.subTest(routes=routes):
                with self.assertRaises(ActivationInvalid):
                    review(legacy_activation_routes=routes)

    def test_unverified_inventory_flag_cannot_be_forged_by_integer(self):
        with self.assertRaises(ActivationInvalid) as err:
            review(noncore_dependency_inventory_complete=1)
        self.assertEqual(err.exception.code,
                         "INVALID_NONCORE_DEPENDENCY_INVENTORY")

    def test_inventory_limits_and_tuple_type_are_required(self):
        for edges, routes in (
            ([LegacyDependencyEdge("OPERATOR", "windows.cleanup")], ()),
            ((), ["MODULE_MENU"]),
            ((LegacyDependencyEdge("OPERATOR", "windows.cleanup"),) * 65, ()),
            ((), ("MODULE_MENU",) * 65),
        ):
            with self.subTest(edges=edges, routes=routes):
                with self.assertRaises(ActivationInvalid):
                    review(core_to_noncore_dependency_edges=edges,
                           legacy_activation_routes=routes)

if __name__ == "__main__":
    unittest.main()
