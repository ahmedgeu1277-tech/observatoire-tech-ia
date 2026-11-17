import json
import tempfile
import unittest
from pathlib import Path

from studio_roblox import generate_project, project_slug


class RobloxStarterGeneratorTests(unittest.TestCase):
    def test_generates_rojo_project(self):
        with tempfile.TemporaryDirectory() as folder:
            result = generate_project("Mon Obby", folder)
            project = Path(result["directory"])
            config = json.loads((project / "default.project.json").read_text(encoding="utf-8"))
            self.assertEqual(config["name"], "Mon_Obby")
            self.assertTrue((project / "src/server/PlayerSetup.server.lua").is_file())
            self.assertTrue((project / "src/server/CoinPickup.server.lua").is_file())
            self.assertFalse(result["code_executed"])
            self.assertFalse(result["game_published"])

    def test_server_owns_coin_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            result = generate_project("SecureObby", folder)
            project = Path(result["directory"])
            server = (project / "src/server/CoinPickup.server.lua").read_text(encoding="utf-8")
            client = (project / "src/client/ClientStatus.client.lua").read_text(encoding="utf-8")
            self.assertIn("Players:GetPlayerFromCharacter", server)
            self.assertIn("coins.Value +=", server)
            self.assertNotIn("Coins.Value", client)
            self.assertNotIn("leaderstats", client)

    def test_rejects_path_traversal_and_invalid_names(self):
        for name in ("../escape", "1bad", "", "x" * 41):
            with self.subTest(name=name), self.assertRaises(ValueError):
                project_slug(name)

    def test_rejects_unknown_template(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                generate_project("MyObby", folder, "unknown")

    def test_does_not_overwrite_existing_project(self):
        with tempfile.TemporaryDirectory() as folder:
            generate_project("MyObby", folder)
            with self.assertRaises(FileExistsError):
                generate_project("MyObby", folder)


if __name__ == "__main__":
    unittest.main()
