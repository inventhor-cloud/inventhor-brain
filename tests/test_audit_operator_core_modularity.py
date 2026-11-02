"""Regression coverage for the read-only optional-plugin dependency audit."""
import tempfile
import unittest
from pathlib import Path

from tools.audit_operator_core_modularity import (
    MANDATORY_FILES, RETIRED_FILES, audit_source,
)

WORKER = "windows/src/Inventhor.Operator.Service/OperatorWorker.cs"
SERVICE = "windows/src/Inventhor.Operator.Service/Program.cs"
ENGINE = "windows/src/Inventhor.Operator.Core/TaskEngine.cs"
DEPLOY = "windows/bootstrap/Build-Deploy-V2_1.ps1"
UI = "windows/src/Inventhor.Operator.Desktop/MainWindow.Modules.cs"


class AuditOperatorModularityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in MANDATORY_FILES:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("// empty synthetic core implementation\n", encoding="utf-8")

    def put(self, filename, data):
        (self.root / filename).write_text(data, encoding="utf-8")

    def test_missing_root_fails_without_guessing_clean(self):
        result = audit_source(self.root / "not_present")
        self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
        self.assertFalse(result["native_clean_boot_verified"])

    def test_missing_required_file_cannot_pass(self):
        (self.root / SERVICE).unlink()
        result = audit_source(self.root)
        self.assertEqual(result["status"], "SOURCE_INCOMPLETE")
        self.assertIn(SERVICE, result["missing_files"])

    def test_synthetic_plugin_free_source_not_mistaken_for_native_smoke(self):
        result = audit_source(self.root)
        self.assertEqual(result["status"],
                         "STATIC_SOURCE_SIGNATURES_CLEAN_NATIVE_VALIDATION_REQUIRED")
        self.assertEqual(result["findings"], [])
        self.assertEqual(set(result["absent_retired_files"]), RETIRED_FILES)
        self.assertFalse(result["native_clean_boot_verified"])
        self.assertFalse(result["native_organizer_updated"])

    def test_core_worker_dependency_on_plugin_loader_detected(self):
        self.put(WORKER, '''var plugins = pluginCatalog.Load(modulesRoot);
var executors = plugins
    .Where(p => p.Executor is not null).ToArray();
var transports = plugins
    .Where(p => p.Transport is not null).ToArray();
''')
        report = audit_source(self.root)
        self.assertEqual(report["status"], "SOURCE_COUPLING_DETECTED")
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("SERVICE_LOADS_LEGACY_PLUGIN_CATALOG", codes)
        self.assertIn("CORE_EXECUTORS_FROM_PLUGINS", codes)
        self.assertIn("CORE_TRANSPORTS_FROM_PLUGINS", codes)
        self.assertTrue(all(x["line"] > 0 for x in report["findings"]))

    def test_legacy_release_module_gate_and_registration_detected(self):
        self.put(SERVICE, 'builder.Services.AddSingleton<PluginCatalog>();\n')
        self.put(ENGINE, 'return Failure("CAPABILITY_UNAVAILABLE");\n')
        self.put(DEPLOY, '''Write-Output "=== BUILD MODULES ==="
if(@($j.modules).Count -lt 16){throw "MODULE_COUNT_TOO_LOW"}
if(@($j.capabilities).Count -lt 41){throw "CAPABILITY_COUNT_TOO_LOW"}
''')
        self.put(UI, 'EnterRoute("operator:modules");\n')
        result = audit_source(self.root)
        codes = {x["code"] for x in result["findings"]}
        self.assertIn("CORE_SERVICE_REGISTERS_LEGACY_CATALOG", codes)
        # Rejecting UNKNOWN capabilities is a correct fail-closed behavior,
        # not evidence that core requires a legacy plugin.
        self.assertNotIn("CORE_TASK_ENGINE_FAILS_IF_NO_EXECUTOR", codes)
        self.assertIn("DEPLOY_PUBLISHES_LEGACY_MODULE_SET", codes)
        self.assertIn("DEPLOY_REQUIRES_SIXTEEN_MODULES", codes)
        self.assertIn("DEPLOY_REQUIRES_LEGACY_CAPABILITY_COUNT", codes)
        self.assertIn("DESKTOP_EXPOSES_LEGACY_MODULE_CENTER", codes)

    def test_compiled_transports_do_not_hide_transitional_plugin_loader(self):
        # Mirrors the newer Operator PR where transport and build/test/run
        # were moved to core but other executors still came from plugins.
        self.put(WORKER, """var plugins = pluginCatalog.Load(
    modulesRoot,
    includeTransports: false,
    includeLegacySoftwareFactory: false);
var executors = plugins
    .Where(p => p.Executor is not null)
    .Select(p => p.Executor!)
    .Append(new CoreSoftwareProcessExecutor()).ToArray();
""")
        report = audit_source(self.root)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("SERVICE_LOADS_LEGACY_PLUGIN_CATALOG", codes)
        self.assertIn("CORE_EXECUTORS_FROM_PLUGINS", codes)
        self.assertFalse(report["native_clean_boot_verified"])

    def test_empty_module_loader_folder_is_still_a_source_dependency(self):
        self.put(WORKER, "var plugins = pluginCatalog.Load(modulesRoot, includeTransports: false);")
        report = audit_source(self.root)
        self.assertEqual(report["status"], "SOURCE_COUPLING_DETECTED")
        self.assertIn("SERVICE_LOADS_LEGACY_PLUGIN_CATALOG",
                      {item["code"] for item in report["findings"]})

    def test_deleted_retired_installer_and_module_ui_not_missing_core(self):
        report = audit_source(self.root)
        self.assertEqual(report["status"],
                         "STATIC_SOURCE_SIGNATURES_CLEAN_NATIVE_VALIDATION_REQUIRED")
        self.assertEqual(set(report["absent_retired_files"]), RETIRED_FILES)
        self.assertEqual(report["missing_files"], [])
        self.assertEqual(report["unreadable_files"], [])
        self.assertFalse(report["native_clean_boot_verified"])

    def test_actual_stacked_operator_factory_migration_still_has_plugin_loader(self):
        self.put(WORKER, """var plugins = pluginCatalog.Load(
    modulesRoot, includeTransports:false,
    includeLegacySoftwareFactory:false, includeLegacyTransfer:false);
var executors = plugins.Where(p => p.Executor is not null)
    .Select(p => p.Executor!).Append(new CoreSoftwareProcessExecutor())
    .Append(new CoreArtifactTransferExecutor()).ToArray();
""")
        self.put(SERVICE, "builder.Services.AddSingleton<PluginCatalog>();")
        report = audit_source(self.root)
        self.assertEqual(report["status"], "SOURCE_COUPLING_DETECTED")
        self.assertEqual(set(report["absent_retired_files"]), RETIRED_FILES)
        self.assertIn("SERVICE_LOADS_LEGACY_PLUGIN_CATALOG",
                      {x["code"] for x in report["findings"]})
        self.assertIn("CORE_SERVICE_REGISTERS_LEGACY_CATALOG",
                      {x["code"] for x in report["findings"]})

    def test_unreadable_retired_source_is_not_assumed_deleted(self):
        # A directory at the path of an obsolete installer is NOT proof of
        # physical removal; report incomplete and never authorize deletion.
        path = self.root / DEPLOY
        path.mkdir(parents=True)
        report = audit_source(self.root)
        self.assertEqual(report["status"], "SOURCE_INCOMPLETE")
        self.assertIn(DEPLOY, report["unreadable_files"])
        self.assertNotIn(DEPLOY, report["absent_retired_files"])
        self.assertFalse(report["native_clean_boot_verified"])

    def test_legitimate_unknown_capability_denial_is_not_plugin_coupling(self):
        self.put(ENGINE, 'return Failure("CAPABILITY_UNAVAILABLE");')
        report = audit_source(self.root)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["status"],
                         "STATIC_SOURCE_SIGNATURES_CLEAN_NATIVE_VALIDATION_REQUIRED")

    def test_comment_only_mention_does_not_match_real_load_operation(self):
        self.put(WORKER, "// no legacy plugins here\n")
        result = audit_source(self.root)
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
