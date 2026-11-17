import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent_architecte


class AgentPublicIndexTests(unittest.TestCase):
    def test_exports_profiles_as_configured_not_running(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles = root / "profiles"
            profiles.mkdir()
            (profiles / "veilleur.json").write_text(json.dumps({
                "name": "veilleur",
                "role": "Analyste",
                "mission": "Surveiller les sources publiques.",
                "instructions": "Ne jamais exécuter de code.",
            }), encoding="utf-8")
            index = root / "site" / "data" / "agents.json"
            with patch.object(agent_architecte, "PROFILE_DIR", profiles), patch.object(agent_architecte, "PUBLIC_INDEX", index):
                exported = agent_architecte.exporter_index_public()
            saved = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(len(exported), 1)
        self.assertEqual(saved["profiles"][0]["name"], "veilleur")
        self.assertIn("non exécuté", saved["profiles"][0]["status"])


if __name__ == "__main__":
    unittest.main()
