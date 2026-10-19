import unittest
from dataclasses import replace

from repair.obd_metrics import decode_obd_mode01
from repair.platform_link_policy import LinkOption, VehicleLinkContext, plan_vehicle_link


class OfflineObdDecoderTests(unittest.TestCase):
    def test_mode01_rpm(self):
        result = decode_obd_mode01(bytes([0x41, 0x0C, 0x1A, 0xF8]))
        self.assertEqual((result.value, result.unit), (1726.0, "rpm"))
        self.assertEqual(result.status, "SOURCE_DECODE_ONLY")
        self.assertFalse(result.may_send_vehicle_commands)
        self.assertFalse(result.diagnosis_confirmed)
        self.assertFalse(result.sensor_calibration_verified)

    def test_coolant_temperature(self):
        result = decode_obd_mode01(bytes([0x41, 0x05, 0x7B]))
        self.assertEqual((result.value, result.unit), (83, "degC"))

    def test_vehicle_speed(self):
        result = decode_obd_mode01(bytes([0x41, 0x0D, 0x64]))
        self.assertEqual((result.value, result.unit), (100, "km/h"))

    def test_throttle_percent(self):
        result = decode_obd_mode01(bytes([0x41, 0x11, 0x80]))
        self.assertAlmostEqual(result.value or 0, 50.196, places=3)

    def test_unknown_pid_rejected(self):
        result = decode_obd_mode01(bytes([0x41, 0x22, 0x00]))
        self.assertEqual(result.reason, "UNSUPPORTED_PID")

    def test_negative_response_and_wrong_mode_rejected(self):
        for data in (bytes([0x7F, 0x01, 0x11]),
                     bytes([0x42, 0x0D, 0x30])):
            with self.subTest(data=data):
                result = decode_obd_mode01(data)
                self.assertEqual(result.reason, "NOT_POSITIVE_MODE01_RESPONSE")

    def test_length_and_transport_frame_rejected(self):
        for data in (
            bytes([0x41, 0x0C, 0x1A]),
            bytes([0x41, 0x0D, 0x01, 0x01]),
            bytes([0x7E, 0x8F, 0x41, 0x0C]),
        ):
            with self.subTest(data=data):
                result = decode_obd_mode01(data)
                self.assertEqual(result.status, "REJECTED")

    def test_binary_only_never_decode_untrusted_console_text(self):
        for raw in ("410C1AF8", None, True, 123, [0x41, 0x0C, 0x1A, 0xF8]):
            with self.subTest(raw=raw):
                self.assertEqual(decode_obd_mode01(raw).reason,
                                 "BYTE_PAYLOAD_REQUIRED")


class CrossPlatformLinkSourceTests(unittest.TestCase):
    def option(self, kind, **changes):
        data = dict(kind=kind, adapter_supports_link=True,
                    host_driver_or_api_available=True,
                    app_permission_granted=True,
                    accessory_protocol_verified=True,
                    link_ready=True, read_service_supported=True,
                    host_compatibility_attested=True,
                    platform_accessory_authorized=False)
        data.update(changes)
        return LinkOption(**data)

    def ctx(self, **changes):
        data = dict(session_id="case-1", platform="ANDROID",
                    preference="AUTO", main_authorized=True,
                    user_consented=True, adapter_identity_verified=True,
                    vehicle_identity_verified=True,
                    options=(self.option("BLUETOOTH_LE"),))
        data.update(changes)
        return VehicleLinkContext(**data)

    def test_android_ble_candidate_but_not_real_connection(self):
        plan = plan_vehicle_link(self.ctx())
        self.assertEqual(plan.state if hasattr(plan, "state") else plan.status,
                         "SOURCE_PLAN_ONLY")
        self.assertEqual(plan.selected_kind, "BLUETOOTH_LE")
        self.assertEqual(plan.selected_medium, "WIRELESS")
        self.assertFalse(plan.may_open_connection)
        self.assertFalse(plan.may_claim_device_visible)
        self.assertFalse(plan.may_claim_connected)
        self.assertFalse(plan.may_send_vehicle_commands)

    def test_all_platforms_support_candidate_when_host_attests(self):
        for platform in ("ANDROID", "IOS", "WINDOWS", "LINUX", "MACOS"):
            with self.subTest(platform=platform):
                plan = plan_vehicle_link(self.ctx(platform=platform))
                self.assertEqual(plan.status, "SOURCE_PLAN_ONLY")

    def test_ios_classic_requires_accessory_authorization(self):
        plan = plan_vehicle_link(self.ctx(
            platform="IOS",
            options=(self.option("BLUETOOTH_CLASSIC"),)))
        self.assertEqual(plan.reason, "NO_COMPATIBLE_ATTESTED_LINK")
        permitted = plan_vehicle_link(self.ctx(
            platform="IOS",
            options=(self.option("BLUETOOTH_CLASSIC",
                                 platform_accessory_authorized=True),)))
        self.assertEqual(permitted.selected_kind, "BLUETOOTH_CLASSIC")

    def test_ios_usb_requires_device_entitlement_not_just_usb_port(self):
        plan = plan_vehicle_link(self.ctx(
            platform="IOS", preference="WIRED",
            options=(self.option("USB_SERIAL"),)))
        self.assertEqual(plan.status, "REVIEW_REQUIRED")
        plan = plan_vehicle_link(self.ctx(
            platform="IOS", preference="WIRED",
            options=(self.option("USB_SERIAL",
                                 platform_accessory_authorized=True),)))
        self.assertEqual(plan.selected_kind, "USB_SERIAL")

    def test_wired_preference_chooses_usb_before_wireless(self):
        plan = plan_vehicle_link(self.ctx(
            platform="WINDOWS", preference="WIRED",
            options=(self.option("BLUETOOTH_LE"),
                     self.option("USB_SERIAL"))))
        self.assertEqual(plan.selected_kind, "USB_SERIAL")
        self.assertEqual(plan.selected_medium, "WIRED")

    def test_auto_preference_returns_fallback_candidates(self):
        plan = plan_vehicle_link(self.ctx(options=(
            self.option("WIFI"),
            self.option("BLUETOOTH_LE"),
            self.option("USB_SERIAL"),
        )))
        self.assertEqual(plan.selected_kind, "USB_SERIAL")
        self.assertEqual(plan.alternative_kinds, ("BLUETOOTH_LE", "WIFI"))

    def test_actual_host_attestation_is_required(self):
        plan = plan_vehicle_link(self.ctx(
            options=(self.option("BLUETOOTH_LE",
                                 host_compatibility_attested=False),)))
        self.assertEqual(plan.status, "REVIEW_REQUIRED")
        self.assertIsNone(plan.selected_kind)

    def test_missing_permissions_never_initiates_transport(self):
        plan = plan_vehicle_link(self.ctx(user_consented=False))
        self.assertEqual(plan.next_step, "REQUEST_LINK_CONSENT")
        self.assertFalse(plan.may_open_connection)
        plan = plan_vehicle_link(self.ctx(main_authorized=False))
        self.assertEqual(plan.next_step, "AUTHORIZE_MAIN")

    def test_duplicate_link_claims_rejected(self):
        plan = plan_vehicle_link(self.ctx(options=(
            self.option("BLUETOOTH_LE"), self.option("BLUETOOTH_LE"),
        )))
        self.assertEqual(plan.reason, "DUPLICATE_LINK_DECLARATION")

    def test_unknown_platform_and_unknown_transport(self):
        self.assertEqual(plan_vehicle_link(self.ctx(
            platform="SYMBIAN")).reason, "UNKNOWN_PLATFORM")
        self.assertEqual(plan_vehicle_link(self.ctx(
            options=(self.option("RAW_OBD_ON_ANYTHING"),))).reason,
            "UNKNOWN_LINK_TYPE")

    def test_false_permission_metadata_must_not_be_string(self):
        plan = plan_vehicle_link(self.ctx(
            options=(self.option("BLUETOOTH_LE",
                                 app_permission_granted="yes"),)))
        self.assertEqual(plan.reason, "INVALID_LINK_FLAGS")

    def test_hardware_not_supported_does_not_make_active(self):
        plan = plan_vehicle_link(self.ctx(
            options=(self.option("BLUETOOTH_LE",
                                 read_service_supported=False),)))
        self.assertEqual(plan.status, "REVIEW_REQUIRED")
        self.assertFalse(plan.may_claim_connected)
