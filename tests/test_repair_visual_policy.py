import unittest
from dataclasses import replace

from education.repair_visual_policy import (
    RepairVisualContext, choose_repair_visual,
)


class RepairVisualPolicyTests(unittest.TestCase):
    def context(self, **changes):
        data = dict(case_id="case-1", step_id="step-2",
                    authorized_session=True, needs_visual=True,
                    visual_goal="GENERAL_CONCEPT",
                    low_risk_disconnected=True,
                    illustration_adds_clarity=True)
        data.update(changes)
        return RepairVisualContext(**data)

    def test_generation_only_when_generic_diagram_adds_clarity(self):
        a = choose_repair_visual(self.context())
        self.assertEqual(a.next_visual_action, "GENERATE_LABELED_CONCEPT_DIAGRAM")
        self.assertTrue(a.can_generate_illustrative_image)
        self.assertTrue(a.image_must_be_labeled_illustrative)
        self.assertFalse(a.may_claim_hardware_verified)
        self.assertFalse(a.may_edit_original_photo)
        self.assertFalse(a.may_access_camera)
        self.assertFalse(a.may_upload_photo)
        self.assertFalse(a.may_instruct_physical_repair)

    def test_no_visual_needed_means_no_image(self):
        a = choose_repair_visual(self.context(needs_visual=False))
        self.assertEqual(a.next_visual_action, "TEXT_GUIDANCE")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_user_photo_annotated_as_copy_instead_of_generated_image(self):
        a = choose_repair_visual(self.context(
            user_photo_exists=True, user_photo_authorized=True,
            photo_shows_required_area=True))
        self.assertEqual(a.next_visual_action, "ANNOTATE_COPY_OF_USER_PHOTO")
        self.assertFalse(a.can_generate_illustrative_image)
        self.assertFalse(a.may_edit_original_photo)

    def test_photo_not_consented_is_not_accessed(self):
        a = choose_repair_visual(self.context(
            user_photo_exists=True, user_photo_authorized=False,
            photo_shows_required_area=True))
        self.assertEqual(a.status, "BLOCKED")
        self.assertEqual(a.next_visual_action, "REQUEST_PHOTO_CONSENT")
        self.assertFalse(a.may_upload_photo)

    def test_verified_service_image_requires_exact_revision(self):
        a = choose_repair_visual(self.context(
            visual_goal="CONNECTOR_PINOUT",
            verified_service_visual_exists=True,
            device_identity_verified=True, device_revision_verified=True))
        self.assertEqual(a.next_visual_action, "SHOW_VERIFIED_SERVICE_VISUAL")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_mismatched_revision_never_promotes_a_manual(self):
        a = choose_repair_visual(self.context(
            visual_goal="CONNECTOR_PINOUT",
            verified_service_visual_exists=True,
            device_identity_verified=True, device_revision_verified=False))
        self.assertEqual(a.next_visual_action,
                         "REQUEST_REAL_PHOTO_OR_VERIFIED_MANUAL")

    def test_never_invent_pinout_wiring_disassembly_or_test_points(self):
        for goal in (
            "COMPONENT_LOCATION", "CIRCUIT_CONNECTION", "CONNECTOR_PINOUT",
            "MEASUREMENT_POINT", "DISASSEMBLY_ORIENTATION",
        ):
            with self.subTest(goal=goal):
                a = choose_repair_visual(self.context(visual_goal=goal))
                self.assertEqual(a.status, "REVIEW_REQUIRED")
                self.assertEqual(a.next_visual_action,
                                 "REQUEST_REAL_PHOTO_OR_VERIFIED_MANUAL")
                self.assertFalse(a.can_generate_illustrative_image)

    def test_reuse_existing_visual_avoids_generation(self):
        a = choose_repair_visual(self.context(
            approved_existing_visual_sufficient=True))
        self.assertEqual(a.next_visual_action, "REUSE_EXISTING_VISUAL")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_image_generation_not_justified_uses_text(self):
        a = choose_repair_visual(self.context(illustration_adds_clarity=False))
        self.assertEqual(a.next_visual_action, "TEXT_GUIDANCE")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_stop_for_mains_energy_and_battery_hazards(self):
        for hazard in (
            "MAINS_POWER", "ENERGIZED", "HIGH_VOLTAGE",
            "UNKNOWN_STORED_ENERGY", "LARGE_CAPACITOR",
            "SWOLLEN_BATTERY", "DAMAGED_LITHIUM_CELL",
            "BATTERY_LEAK", "FIRE_SMOKE", "EXPOSED_WIRING",
            "UNKNOWN_HAZARD",
        ):
            with self.subTest(hazard=hazard):
                a = choose_repair_visual(self.context(hazard_flags=(hazard,)))
                self.assertEqual(a.status, "STOP_REFER")
                self.assertEqual(a.next_visual_action, "SAFETY_NOTICE")
                self.assertFalse(a.can_generate_illustrative_image)
                self.assertFalse(a.may_instruct_physical_repair)

    def test_unsafe_energy_state_never_generates(self):
        a = choose_repair_visual(self.context(low_risk_disconnected=False))
        self.assertEqual(a.next_visual_action, "SAFE_PRECHECK")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_missing_authorization_rejects_even_harmless_diagram(self):
        a = choose_repair_visual(self.context(authorized_session=False))
        self.assertEqual(a.status, "BLOCKED")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_invalid_hazard_cannot_be_ignored(self):
        a = choose_repair_visual(self.context(hazard_flags=("NOT_SURE",)))
        self.assertEqual(a.reason, "UNKNOWN_HAZARD_STATUS")

    def test_boolean_metadata_must_be_real_bool(self):
        a = choose_repair_visual(self.context(low_risk_disconnected="yes"))
        self.assertEqual(a.reason, "INVALID_POLICY_FLAGS")

    def test_invalid_scope_blocks(self):
        a = choose_repair_visual(self.context(step_id=""))
        self.assertEqual(a.reason, "INVALID_SCOPE")

    def test_another_profile_or_case_must_not_be_claimed_attested(self):
        a = choose_repair_visual(self.context())
        self.assertTrue(a.source_only)
        self.assertFalse(a.may_claim_hardware_verified)

    def test_real_photo_not_in_area_does_not_fake_precise_instruction(self):
        a = choose_repair_visual(self.context(
            visual_goal="MEASUREMENT_POINT",
            user_photo_exists=True, user_photo_authorized=True,
            photo_shows_required_area=False))
        self.assertEqual(a.next_visual_action,
                         "REQUEST_REAL_PHOTO_OR_VERIFIED_MANUAL")

    def test_bad_goal_blocks(self):
        a = choose_repair_visual(self.context(visual_goal="UNKNOWN_OPERATION"))
        self.assertEqual(a.status, "BLOCKED")
        self.assertFalse(a.can_generate_illustrative_image)

    def test_multiple_repair_domains_use_one_image_preference(self):
        for domain in ("AUTOMOTIVE", "BICYCLE", "HOME_APPLIANCE", "PLUMBING",
                       "INDUSTRIAL", "COMPUTER", "MOTORCYCLE"):
            with self.subTest(domain=domain):
                a = choose_repair_visual(self.context(
                    domain=domain, user_photo_exists=True,
                    user_photo_authorized=True, photo_shows_required_area=True))
                self.assertEqual(a.next_visual_action, "ANNOTATE_COPY_OF_USER_PHOTO")
                self.assertFalse(a.can_generate_illustrative_image)

    def test_vehicle_safety_hazard_stops_illustration_workflow(self):
        a = choose_repair_visual(self.context(
            domain="AUTOMOTIVE", hazard_flags=("CRITICAL_BRAKE_STEERING",)))
        self.assertEqual(a.status, "STOP_REFER")
        self.assertFalse(a.may_instruct_physical_repair)
