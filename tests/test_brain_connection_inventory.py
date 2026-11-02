"""Regression for GitHub-only Brain wiring inventory, never live runtime QA."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from continuity.core_activation_gate import CORE, REQUIRED_LINKS

INVENTORY = (
    Path(__file__).resolve().parents[1]
    / "validation_reports"
    / "BRAIN_CONNECTION_SOURCE_INVENTORY_20261102.json"
)


class BrainConnectionInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(INVENTORY.read_text(encoding="utf-8"))

    def test_the_only_core_roster_is_the_existing_five(self):
        self.assertEqual(tuple(self.record["owner_scope"]), CORE)
        self.assertEqual(self.record["qa_alias"],
                         "QA_FACTORY_IS_SAME_AS_FABRIKA")

    def test_every_required_native_link_is_covered_once(self):
        links = self.record["required_native_links"]
        self.assertEqual(tuple(x["link_id"] for x in links), REQUIRED_LINKS)
        self.assertEqual(len(set(x["link_id"] for x in links)), len(links))

    def test_no_github_data_claims_installed_or_factory_verified(self):
        self.assertTrue(self.record["source_only"])
        self.assertEqual(self.record["authority"], "NOT_NATIVE_ORGANIZER_LEDGER")
        for key in ("native_owner_task_lease_verified",
                    "native_main_installed_verified",
                    "full_brain_connected_verified",
                    "cleanup_complete_verified",
                    "qa_factory_live_verified"):
            self.assertIs(self.record[key], False, key)
        for item in self.record["required_native_links"]:
            self.assertEqual(item["native_authenticated_ack"], "UNVERIFIED")

    def test_domain_references_are_exactly_seven_unique_source_drafts(self):
        sources = self.record["domain_sources"]
        self.assertEqual(
            {x["domain"] for x in sources},
            {"architecture", "design", "visual", "social",
             "language", "automation", "memory"},
        )
        self.assertEqual(len(sources), 7)
        self.assertEqual(len({x["repository"] for x in sources}), 7)
        for source in sources:
            self.assertEqual(source["source_status"], "DRAFT_NOT_MERGED")
            self.assertEqual(source["native_runtime_link"], "UNVERIFIED")
            self.assertEqual(len(source["source_sha"]), 40)
            self.assertEqual(source["source_pr"], 1)

    def test_operator_still_declares_remaining_legacy_dependencies(self):
        operator = self.record["operator_source"]
        self.assertIs(operator["legacy_plugin_loader_remaining"], True)
        self.assertIs(operator["legacy_module_manifests_in_source"], True)
        self.assertIs(
            operator["legacy_dependent_test_project_references_remaining"], True)
        self.assertEqual(operator["main_pairing_and_live_ack"], "UNVERIFIED")

    def test_native_finalization_is_explicitly_blocked(self):
        self.assertGreaterEqual(len(self.record["known_blockers"]), 5)
        self.assertGreaterEqual(len(self.record["safe_next_actions"]), 5)


if __name__ == "__main__":
    unittest.main()
