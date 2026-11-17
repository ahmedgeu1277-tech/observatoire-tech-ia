import tempfile
import unittest
from pathlib import Path

from studio_roblox import generate_project
from validateur_roblox import validate_project


class RobloxStaticValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        result = generate_project("SafeObby", self.temp.name)
        self.project = Path(result["directory"])

    def tearDown(self):
        self.temp.cleanup()

    def test_generated_project_passes(self):
        report = validate_project(self.project)
        self.assertEqual(report["status"], "passed")
        self.assertGreaterEqual(report["files_scanned"], 4)
        self.assertEqual(report["findings"], [])

    def test_detects_dynamic_code_execution(self):
        script = self.project / "src/server/PlayerSetup.server.lua"
        script.write_text(script.read_text(encoding="utf-8") + "\nloadstring(userInput)()\n", encoding="utf-8")
        report = validate_project(self.project)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("exécution dynamique" in item["message"] for item in report["findings"]))

    def test_detects_client_side_currency_write(self):
        script = self.project / "src/client/ClientStatus.client.lua"
        script.write_text(script.read_text(encoding="utf-8") + "\nplayer.leaderstats.Coins.Value += 100\n", encoding="utf-8")
        report = validate_project(self.project)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("client semble modifier" in item["message"] for item in report["findings"]))

    def test_detects_missing_required_file(self):
        (self.project / "src/server/CoinPickup.server.lua").unlink()
        report = validate_project(self.project)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("manquant" in item["message"] for item in report["findings"]))

    def test_missing_directory_fails_safely(self):
        report = validate_project(Path(self.temp.name) / "does-not-exist")
        self.assertEqual(report["status"], "failed")


if __name__ == "__main__":
    unittest.main()
