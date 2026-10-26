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
