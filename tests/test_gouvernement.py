import tempfile
import unittest
from pathlib import Path

import gouvernement as gov


class GovernmentTests(unittest.TestCase):
    def test_initial_state_has_30_unique_directors_and_zero_budget(self):
        state = gov.initial_state()
        self.assertEqual(len(state["directors"]), 30)
        self.assertEqual(len({a["personality"] for a in state["directors"]}), 30)
        self.assertEqual(len({a["taste"] for a in state["directors"]}), 30)
        self.assertEqual(state["treasury"], 0)
        self.assertFalse(state["currency"]["convertible"])

    def test_cannot_spend_without_virtual_credits(self):
        state = gov.initial_state()
        with self.assertRaises(ValueError):
            gov.allocate_budget(state, "Finances", 1, "test")

    def test_ledger_and_budget(self):
        state = gov.initial_state()
        gov.add_credits(state, 100, "simulation de récompense")
        gov.allocate_budget(state, "Technologie", 35, "prototype")
        self.assertEqual(state["treasury"], 65)
        self.assertEqual(len(state["ledger"]), 2)

    def test_meeting_vote(self):
        state = gov.initial_state()
        meeting = gov.convene_meeting(state, "urgence", "Incident simulé",
                                      [a["id"] for a in state["directors"][:3]])
        for director in meeting["participants"]:
            gov.cast_vote(state, meeting["id"], director, "pour")
        result = gov.close_vote(state, meeting["id"])
        self.assertEqual(result["result"], "adoptée")

    def test_social_events_are_simulated(self):
        state = gov.initial_state()
        event = gov.simulate_social_climate(state, "réforme budgétaire", -30)
        self.assertIn(event["type"], {"manifestation simulée", "grève simulée"})


if __name__ == "__main__":
    unittest.main()
