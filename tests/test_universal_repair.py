import unittest
from dataclasses import replace

from repair.triage import RepairTriageContext, plan_repair_triage
from repair.vehicle_policy import (
    VehicleDiagnosticContext, plan_vehicle_diagnostic, READ_SERVICES,
    CHANGE_SERVICES,
)


class UniversalRepairTriageTests(unittest.TestCase):
    def case(self, **changes):
        values = dict(
            case_id="repair-101", domain="AUTOMOTIVE",
            session_authorized=True, hazards_assessed=True,
            device_identity_verified=True, revision_verified=True,
            observed_symptom_present=True, objective_evidence_present=True,
            relevant_manual_verified=True,
        )
        values.update(changes)
        return RepairTriageContext(**values)

    def test_multiple_repair_domains_share_main_policy(self):
        for domain in (
            "AUTOMOTIVE", "MOTORCYCLE", "BICYCLE", "COMPUTER", "PHONE",
            "HOME_APPLIANCE", "HOME_ELECTRICAL", "HVAC", "PLUMBING",
            "INDUSTRIAL", "POWER_TOOL", "OTHER",
        ):
            with self.subTest(domain=domain):
                a = plan_repair_triage(self.case(domain=domain))
                self.assertEqual(a.next_step, "PROPOSE_TESTABLE_CAUSES")
                self.assertFalse(a.may_execute_repair)
                self.assertFalse(a.may_claim_diagnosis)

    def test_unknown_safety_state_needs_review(self):
        a = plan_repair_triage(self.case(hazards_assessed=False))
        self.assertEqual(a.next_step, "ASSESS_HAZARDS")

    def test_high_energy_and_safety_critical_need_qualified_review(self):
        for flag in ("HIGH_VOLTAGE", "HYBRID_EV_HV", "GAS_LEAK",
                     "PRESSURIZED_SYSTEM", "CRITICAL_BRAKE_STEERING",
                     "FIRE_SMOKE", "MOVING_MACHINERY", "UNKNOWN_HAZARD"):
            with self.subTest(flag=flag):
                a = plan_repair_triage(self.case(hazards=(flag,)))
                self.assertEqual(a.status, "SPECIALIST_REVIEW")
                self.assertFalse(a.may_access_device)

    def test_repair_session_must_be_main_authorized(self):
        self.assertEqual(plan_repair_triage(self.case(
            session_authorized=False)).reason, "MAIN_AUTH_REQUIRED")

    def test_identity_and_revision_before_accurate_parts(self):
        self.assertEqual(plan_repair_triage(self.case(
            device_identity_verified=False)).next_step, "IDENTIFY_DEVICE")
        self.assertEqual(plan_repair_triage(self.case(
            revision_verified=False)).next_step, "VERIFY_MODEL_REVISION")

    def test_observation_and_source_needed_before_specific_guidance(self):
        self.assertEqual(plan_repair_triage(self.case(
            objective_evidence_present=False)).next_step,
            "COLLECT_NONINVASIVE_EVIDENCE")
        self.assertEqual(plan_repair_triage(self.case(
            relevant_manual_verified=False)).next_step,
            "VERIFY_REPAIR_DOCUMENTATION")

    def test_illustrations_redirect_to_existing_image_selection_policy(self):
        a = plan_repair_triage(self.case(image_needed=True))
        self.assertEqual(a.next_step, "CONSULT_EXISTING_VISUAL_POLICY")
        self.assertFalse(a.may_generate_visual)

    def test_invalid_risk_flags_not_assumed_safe(self):
        a = plan_repair_triage(self.case(hazards=("GUESSED_SAFE",)))
        self.assertEqual(a.reason, "INVALID_HAZARD_CLASSIFICATION")


class VehicleConnectionPolicyTests(unittest.TestCase):
    def diagnostic(self, **changes):
        values = dict(
            session_id="vehicle-9", requested_service="READ_DTC",
            interface_type="OBD_GENERIC",
            main_session_authorized=True,
            user_consented_to_link=True, adapter_identified=True,
            adapter_trusted=True, vehicle_identified=True,
            vehicle_revision_confirmed=True,
            service_supported_by_adapter_and_vehicle=True,
        )
        values.update(changes)
        return VehicleDiagnosticContext(**values)

    def test_every_discovery_and_read_action_is_plannable_not_auto_executed(self):
        for service in READ_SERVICES:
            with self.subTest(service=service):
                a = plan_vehicle_diagnostic(self.diagnostic(
                    requested_service=service))
                self.assertEqual(a.status, "HOST_REVIEW_REQUIRED")
                self.assertTrue(a.read_only)
                self.assertFalse(a.may_execute)
                self.assertFalse(a.may_send_vehicle_commands)
                self.assertFalse(a.may_claim_connection_active)
                self.assertFalse(a.may_claim_dtc_cause_proven)

    def test_no_hardware_or_vehicle_compatibility_invented(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            service_supported_by_adapter_and_vehicle=False))
        self.assertEqual(a.next_step, "LOOK_UP_COMPATIBLE_INTERFACE")
        self.assertEqual(a.status, "UNSUPPORTED_HERE")

    def test_multibrand_interfaces_do_not_force_one_adapter_vendor(self):
        for interface in ("OBD_GENERIC", "OBDONUDS", "UDS_CAN", "DOIP",
                          "J2534", "J1939", "OEM_TOOL", "OTHER_VERIFIED"):
            with self.subTest(interface=interface):
                a = plan_vehicle_diagnostic(self.diagnostic(
                    interface_type=interface))
                self.assertEqual(a.next_step, "PREPARE_SCOPED_READ_SESSION")

    def test_wrong_interface_needs_discovery(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            interface_type="UNRECOGNIZED"))
        self.assertEqual(a.next_step, "IDENTIFY_INTERFACE")

    def test_no_main_authorization_or_vehicle_consent(self):
        self.assertEqual(plan_vehicle_diagnostic(self.diagnostic(
            main_session_authorized=False)).next_step,
            "AUTHORIZE_MAIN_SESSION")
        self.assertEqual(plan_vehicle_diagnostic(self.diagnostic(
            user_consented_to_link=False)).next_step,
            "REQUEST_VEHICLE_LINK_CONSENT")

    def test_adapter_identity_and_variant_must_be_confirmed(self):
        self.assertEqual(plan_vehicle_diagnostic(self.diagnostic(
            adapter_trusted=False)).next_step, "VERIFY_ADAPTER")
        self.assertEqual(plan_vehicle_diagnostic(self.diagnostic(
            vehicle_revision_confirmed=False)).next_step,
            "VERIFY_VEHICLE_AND_VARIANT")

    def test_advanced_operations_are_architecturally_present(self):
        for service in CHANGE_SERVICES:
            with self.subTest(service=service):
                a = plan_vehicle_diagnostic(self.diagnostic(
                    requested_service=service, vehicle_stationary_verified=True,
                    service_document_verified=True, explicit_owner_approval=True,
                    authorized_oem_access=True,
                    qualified_technician_present=True,
                    stable_power_supply_verified=True,
                    recovery_plan_verified=True))
                self.assertEqual(a.next_step,
                                 "PREPARE_SCOPED_MANUFACTURER_WORKFLOW")
                self.assertFalse(a.may_execute)
                self.assertFalse(a.may_send_vehicle_commands)

    def test_coding_without_approval_is_never_silently_authorized(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            requested_service="ECU_CODING", vehicle_stationary_verified=True,
            service_document_verified=True))
        self.assertEqual(a.next_step, "REQUEST_EXACT_ACTION_APPROVAL")

    def test_oem_access_and_qualified_safety_workflow(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            requested_service="ACTUATOR_TEST", vehicle_stationary_verified=True,
            service_document_verified=True, explicit_owner_approval=True))
        self.assertEqual(a.next_step, "VERIFY_MANUFACTURER_ACCESS")
        a = plan_vehicle_diagnostic(self.diagnostic(
            requested_service="ACTUATOR_TEST", vehicle_stationary_verified=True,
            service_document_verified=True, explicit_owner_approval=True,
            authorized_oem_access=True, safety_area="BRAKES"))
        self.assertEqual(a.status, "SPECIALIST_REVIEW")

    def test_programming_needs_stable_power_and_recovery(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            requested_service="ECU_PROGRAMMING",
            vehicle_stationary_verified=True,
            service_document_verified=True, explicit_owner_approval=True,
            authorized_oem_access=True))
        self.assertEqual(a.next_step, "VERIFY_STABLE_POWER_AND_RECOVERY")
        self.assertFalse(a.may_execute)

    def test_unknown_operation_never_becomes_generic_adb_or_bus_execution(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            requested_service="SEND_RAW_CAN"))
        self.assertEqual(a.reason, "UNKNOWN_SERVICE")
        self.assertFalse(a.may_send_vehicle_commands)

    def test_invalid_host_flag_fails_closed(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            adapter_trusted="true"))
        self.assertEqual(a.reason, "INVALID_TRUST_FLAGS")

    def test_unsafe_critical_category_requires_classification(self):
        a = plan_vehicle_diagnostic(self.diagnostic(
            safety_area="WHAT_IF_UNKNOWN"))
        self.assertEqual(a.next_step, "CLASSIFY_SAFETY_AREA")
