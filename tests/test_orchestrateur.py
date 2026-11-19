import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import orchestrateur


class MissionValidationTests(unittest.TestCase):
    def test_rejects_unknown_agent(self):
        with self.assertRaises(ValueError):
            orchestrateur.valider_mission({"mission": "tester", "agents": ["pirate"]})

    def test_rejects_too_many_agents(self):
        with self.assertRaises(ValueError):
            orchestrateur.valider_mission({
                "mission": "tester",
                "agents": ["chercheur", "critique", "architecte", "chercheur"],
            })

    def test_rejects_non_string_agent_without_type_error(self):
        with self.assertRaises(ValueError):
            orchestrateur.valider_mission({"mission": "tester", "agents": [{"role": "chercheur"}]})

    def test_rejects_unbounded_duration(self):
        with self.assertRaises(ValueError):
            orchestrateur.valider_mission({
                "mission": "tester",
                "max_duration_seconds": 999999,
            })

    @patch("orchestrateur.generate_text")
    def test_runs_agents_and_saves_private_style_report(self, generate):
        generate.side_effect = [
            ("Analyse initiale", "groq"),
            ("Contre-analyse", "groq"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            report = orchestrateur.executer_mission(
                {
                    "mission": "Étudier une architecture de test.",
                    "agents": ["chercheur", "critique"],
                    "max_duration_seconds": 120,
                },
                Path(folder),
            )
            saved = json.loads(Path(report["report_path"]).read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(saved["results"]), 2)
        self.assertFalse(saved["safety"]["code_execution"])
        self.assertFalse(saved["safety"]["automatic_publication"])

    @patch("orchestrateur.generate_text")
    def test_stops_after_provider_failure(self, generate):
        generate.side_effect = RuntimeError("provider unavailable")
        with tempfile.TemporaryDirectory() as folder:
            report = orchestrateur.executer_mission(
                {"mission": "Tester", "agents": ["chercheur", "critique"]},
                Path(folder),
            )
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["results"]), 1)
        self.assertEqual(report["results"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
