import json
import os
import stat
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

    def test_rejects_potential_api_secret_in_mission_or_context(self):
        with self.assertRaisesRegex(ValueError, "secret potentiel"):
            orchestrateur.valider_mission({
                "mission": "Analyser ce jeton gsk_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
            })
        with self.assertRaisesRegex(ValueError, "secret potentiel"):
            orchestrateur.valider_mission({
                "mission": "Analyser un système",
                "context": "api_key=abcdefghijklmnopqrstuvwx",
            })

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
        second_prompt = generate.call_args_list[1].args[0][1]["content"]
        self.assertIn("Analyse initiale", second_prompt)
        self.assertIn("Agent chercheur", second_prompt)
        self.assertGreater(generate.call_args_list[0].kwargs["timeout"], 0)
        self.assertLessEqual(generate.call_args_list[0].kwargs["timeout"], 60)
        self.assertFalse(saved["safety"]["code_execution"])
        self.assertFalse(saved["safety"]["automatic_publication"])

    @patch("orchestrateur.generate_text")
    def test_cooperative_cancellation_stops_before_next_agent(self, generate):
        cancelled = False
        def finish_first_agent(*args, **kwargs):
            nonlocal cancelled
            cancelled = True
            return "Analyse", "groq"
        generate.side_effect = finish_first_agent
        with tempfile.TemporaryDirectory() as folder:
            report = orchestrateur.executer_mission(
                {"mission": "Tester l'arrêt coopératif", "agents": ["chercheur", "critique"], "max_duration_seconds": 120},
                Path(folder), should_cancel=lambda: cancelled,
            )
        self.assertEqual(report["status"], "cancelled")
        self.assertEqual(generate.call_count, 1)

    @unittest.skipIf(os.name == "nt", "Les permissions POSIX ne sont pas disponibles sous Windows.")
    @patch("orchestrateur.generate_text", return_value=("Analyse privée", "groq"))
    def test_private_report_uses_restricted_directory_and_file_permissions(self, _generate):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "private"
            report = orchestrateur.executer_mission(
                {"mission": "Tester les permissions", "agents": ["chercheur"]},
                output,
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(Path(report["report_path"]).stat().st_mode), 0o600)

    @patch("orchestrateur.generate_text")
    def test_rejects_generated_output_containing_potential_secret(self, generate):
        secret = "gsk_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        generate.return_value = (f"Analyse contenant {secret}", "groq")
        with tempfile.TemporaryDirectory() as folder:
            report = orchestrateur.executer_mission(
                {"mission": "Tester le filtrage des sorties", "agents": ["chercheur"]},
                Path(folder),
            )
            saved_text = Path(report["report_path"]).read_text(encoding="utf-8")
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["results"][0]["status"], "failed")
        self.assertEqual(report["results"][0]["error_type"], "PotentialSecretDetected")
        self.assertNotIn(secret, saved_text)

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
