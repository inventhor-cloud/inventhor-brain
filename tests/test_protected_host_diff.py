"""Tests for source-only protected host file review; never touch live PC."""
import unittest

from tools.audit_protected_host_diff import (
    CoreBoundaryInputInvalid, inspect_protected_host_diff,
)


class ProtectedHostDiffTests(unittest.TestCase):
    def test_actual_operator_pr3_windows_main_ui_paths_are_reviewed(self):
        advice = inspect_protected_host_diff((
            "windows/src/Inventhor.Operator.Desktop/MainWindow.xaml.cs",
            "windows/src/Inventhor.Operator.Desktop/MainWindow.xaml",
            "windows/src/Inventhor.Operator.Core/PermissionEngine.cs",
        ))
        self.assertEqual(advice.disposition,
                         "PROTECTED_ENTRYPOINT_REVIEW_REQUIRED")
        self.assertEqual(advice.frozen_entrypoints_touched, 2)
        self.assertEqual(advice.core_host_paths_touched, 0)
        self.assertFalse(advice.safe_to_merge_or_deploy)
        self.assertFalse(advice.automatic_revert_allowed)

    def test_actual_operator_pr5_service_and_loader_require_review(self):
        advice = inspect_protected_host_diff((
            "windows/src/Inventhor.Operator.Service/OperatorWorker.cs",
            "windows/src/Inventhor.Operator.Core/PluginCatalog.cs",
            "windows/src/Inventhor.Operator.Service/CoreTransportFactory.cs",
        ))
        self.assertEqual(advice.disposition, "CORE_HOST_REVIEW_REQUIRED")
        self.assertEqual(advice.frozen_entrypoints_touched, 0)
        self.assertEqual(advice.core_host_paths_touched, 2)

    def test_android_activities_and_windows_bootstrap_stay_protected(self):
        advice = inspect_protected_host_diff((
            "app/src/main/java/com/inventhor/operatorcore/v3/OperatorCoreActivity.java",
            "app/src/main/java/com/acme/mobile/MainActivity.kt",
            "windows/src/Inventhor.Operator.Desktop/App.xaml.cs",
        ))
        self.assertEqual(advice.frozen_entrypoints_touched, 3)

    def test_gateway_aggregator_tree_extensions_do_not_trigger_core_freeze(self):
        advice = inspect_protected_host_diff((
            "src/Gateway/StudioUiGateway.cs",
            "src/Aggregator/OperatorCommandAggregator.cs",
            "src/Tree/StudioFeatures.cs",
            "tests/StudioUiGatewayTests.cs",
        ))
        self.assertEqual(advice.disposition,
                         "NO_PROTECTED_PATHS_IN_SUPPLIED_DIFF")
        self.assertEqual(advice.frozen_entrypoints_touched, 0)
        self.assertFalse(advice.owner_pc_current_sources_verified)
        self.assertFalse(advice.safe_to_merge_or_deploy)

    def test_similar_names_not_accidentally_frozen(self):
        advice = inspect_protected_host_diff((
            "src/MyMainActivity.java",
            "src/ModernMainWindow.xaml.cs",
            "src/App.xaml.cs.extra",
        ))
        self.assertEqual(advice.frozen_entrypoints_touched, 0)

    def test_windows_separators_and_case_are_supported(self):
        advice = inspect_protected_host_diff((
            r"APP\SRC\MAIN\JAVA\MainActivity.JAVA",
        ))
        self.assertEqual(advice.frozen_entrypoints_touched, 1)

    def test_traversal_and_absolute_paths_cannot_be_disguised(self):
        for invalid in (
            "../MainActivity.kt", "/src/MainActivity.kt",
            "C:\\work\\MainWindow.xaml.cs",
            "src//MainActivity.java", "src/./MainActivity.java",
            "src/../MainActivity.java", "src/FILE\x00.exe",
            "src/FILE\n.exe",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(CoreBoundaryInputInvalid):
                    inspect_protected_host_diff((invalid,))

    def test_duplicates_after_windows_case_normalization_denied(self):
        with self.assertRaisesRegex(CoreBoundaryInputInvalid,
                                    "DUPLICATE_CHANGED_PATH"):
            inspect_protected_host_diff((
                "src/MainActivity.java", r"SRC\MAINACTIVITY.JAVA",
            ))

    def test_bad_input_shape_denied(self):
        for x in ("src/MainActivity.java", None, ["src/MainActivity.java"]):
            with self.subTest(x=x):
                with self.assertRaises(CoreBoundaryInputInvalid):
                    inspect_protected_host_diff(x)

    def test_result_never_approves_change_or_native_lease(self):
        for changed_paths in ((), ("src/MainActivity.java",),
                              ("src/Gateway/NewFeature.cs",)):
            with self.subTest(paths=changed_paths):
                advice = inspect_protected_host_diff(changed_paths)
                self.assertIn("SOURCE_DIFF_ONLY", advice.source_class)
                self.assertFalse(advice.native_owner_lease_verified)
                self.assertFalse(advice.safe_to_merge_or_deploy)
                self.assertFalse(advice.automatic_revert_allowed)


if __name__ == "__main__":
    unittest.main()
