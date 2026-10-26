"""Regression tests for the 2026-10-26 five-system owner product focus."""
import json
import unittest
from pathlib import Path

from continuity.core_activation_gate import CORE, REQUIRED_LINKS

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json"


class CurrentOwnerArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exactly_five_named_components_not_four_or_six(self):
        ids = [item["id"] for item in self.policy["core_systems"]]
        self.assertEqual(ids, [
            "INVENTHOR", "OPERATOR", "ORGANIZER", "STUDIO_DESIGN", "QA_FACTORY",
        ])
        self.assertEqual(tuple(ids), CORE)
        self.assertEqual(len(ids), len(set(ids)))

    def test_qa_and_factory_are_one_system(self):
        aliases = self.policy["aliases"]
        for label in ("QA", "FACTORY", "FABRIKA", "KALITE_FABRIKASI"):
            self.assertEqual(aliases[label], "QA_FACTORY")
        self.assertNotIn("FACTORY", CORE)
        self.assertNotIn("QA", CORE)

    def test_organizer_remains_single_canonical_ledger(self):
        roles = [x["role"] for x in self.policy["core_systems"]
                 if x["id"] == "ORGANIZER"]
        self.assertEqual(len(roles), 1)
        self.assertIn("One canonical", roles[0])
        self.assertTrue(self.policy["execution_policy"]["reuse_ids"])
        self.assertTrue(self.policy["execution_policy"]["no_lease_takeover"])

    def test_product_loop_requires_studio_and_factory_retest(self):
        phases = self.policy["mandatory_workflow"]
        for needed in ("STUDIO_REAL_EDITABLE_DESIGN",
                       "STUDIO_TRUE_INTERACTIVE_PREVIEW",
                       "OPERATOR_REAL_PROGRAM_BUILD_AND_RUN",
                       "STUDIO_REPAIR_AND_NEW_BUILD_REVISION_IF_FAILED",
                       "SAME_QA_FACTORY_RETEST_CHANGED_ARTIFACT_IF_FAILED"):
            self.assertIn(needed, phases)
        self.assertIn("STUDIO_REAL_RENDER", REQUIRED_LINKS)

    def test_owner_latest_order_requires_total_live_detach(self):
        policy = self.policy
        order = policy["current_owner_operational_override"]
        self.assertEqual(order["instruction_id"], "OWNER_FULL_NONCORE_DETACH_20261026")
        self.assertTrue(order["complete_removal_not_equal_hide_or_disable"])
        self.assertTrue(order["protect_user_data_and_rollback_material"])
        self.assertTrue(order["native_organizer_exact_task_update_required"])
        self.assertEqual(order["status"], "SOURCE_POLICY_REGISTERED_NATIVE_UNVERIFIED")
        self.assertEqual(policy["version"], "1.2.0")
        self.assertTrue((ROOT / order["authoritative_human_handoff"]).is_file())

    def test_noncore_detach_must_have_zero_active_runtime_dependencies(self):
        detachment = self.policy["noncore_detachment_acceptance"]
        expected = detachment["complete_requires"]
        for item in (
            "active_noncore_module_count",
            "active_noncore_dependency_edges",
            "orphan_noncore_runtime_registration_count",
            "orphan_noncore_service_startup_task_menu_count",
            "orphan_noncore_updater_installer_ci_reference_count",
        ):
            self.assertEqual(expected[item], 0)
        self.assertTrue(expected["five_system_smoke_verified"])
        self.assertTrue(expected["studio_operator_factory_live_chain_verified"])
        self.assertTrue(expected["native_organizer_checkpoint_written_and_read_back"])
        self.assertTrue(detachment["unverified_runtime_is_not_success"])
        self.assertTrue(detachment["core_required_capabilities_move_to_existing_five_systems_before_old_plugin_identity_detach"])

    def test_new_ai_must_start_with_full_detach_handoff(self):
        start = self.policy["new_agent_startup"]
        self.assertIn("OWNER_NONCORE_TOTAL_DETACH_HANDOFF_20261026.md", start[0])
        self.assertTrue(any("EXACT" in line or "exact" in line for line in start))
        self.assertTrue(any("ZERO" in line.upper() for line in start))
        self.assertEqual(len(self.policy["core_systems"]), 5)

    def test_future_programs_are_separate_and_deferred(self):
        future = self.policy["future_program_architecture"]
        self.assertEqual(future["priority_now"],
                         "DEFERRED_NO_STANDALONE_PROGRAM_IMPLEMENTATION")
        self.assertTrue(future["installed_app_not_required_to_embed_inventhor"])
        self.assertTrue(future["remove_all_legacy_noncore_runtime_dependencies_now"])
        self.assertTrue(future["no_duplicate_brain_operator_organizer_design_studio_factory"])
        self.assertFalse(future["native_installed_computer_access_verified"])
        self.assertTrue(future["source_contract_only"])

    def test_no_expansion_or_installed_success_from_source(self):
        paused = self.policy["out_of_scope_now"]
        self.assertTrue(any("Converting legacy modules" in x for x in paused))
        self.assertTrue(any("Second Brain" in x for x in paused))
        self.assertEqual(self.policy["native_organizer_goal_update_status"],
                         "NOT_VERIFIED")
        self.assertEqual(self.policy["installed_system_status"],"NOT_VERIFIED")
        self.assertTrue(self.policy["execution_policy"]["source_ci_not_installed_qa"])


if __name__ == "__main__":
    unittest.main()
