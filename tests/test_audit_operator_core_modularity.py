"""Regression coverage for the read-only optional-plugin dependency audit."""
import tempfile
import unittest
from pathlib import Path

from tools.audit_operator_core_modularity import (
    MANDATORY_FILES, audit_source,
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
        self.assertIn("CORE_TASK_ENGINE_FAILS_IF_NO_EXECUTOR", codes)
        self.assertIn("DEPLOY_PUBLISHES_LEGACY_MODULE_SET", codes)
        self.assertIn("DEPLOY_REQUIRES_SIXTEEN_MODULES", codes)
        self.assertIn("DEPLOY_REQUIRES_LEGACY_CAPABILITY_COUNT", codes)
        self.assertIn("DESKTOP_EXPOSES_LEGACY_MODULE_CENTER", codes)

    def test_comment_only_mention_does_not_match_real_load_operation(self):
        self.put(WORKER, "// no legacy plugins here\n")
        result = audit_source(self.root)
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
