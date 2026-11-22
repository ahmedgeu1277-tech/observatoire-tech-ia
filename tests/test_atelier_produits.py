import tempfile
import unittest
from pathlib import Path

from atelier_produits import DIMENSIONS, evaluate_opportunity, save_opportunity


def sample():
    return {
        "name": "Assistant de tests pour jeux",
        "problem": "Les petits créateurs passent trop de temps à tester manuellement.",
        "target_customer": "Créateurs indépendants de jeux",
        "proposed_solution": "Un outil qui prépare des scénarios de test et organise les résultats.",
        "product_type": "game_tool",
        "evidence": ["Entretiens utilisateurs à réaliser"],
        "scores": {key: 4 for key in DIMENSIONS},
    }


class ProductWorkshopTests(unittest.TestCase):
    def test_score_and_guardrails(self):
        report = evaluate_opportunity(sample())
        self.assertEqual(report["score_percent"], 80)
        self.assertEqual(report["decision"], "priorite_prototype")
        self.assertEqual(report["novelty_status"], "non_verifiee")
        self.assertFalse(report["safety"]["automatic_sale"])
        self.assertFalse(report["safety"]["automatic_publication"])

    def test_rejects_missing_dimension(self):
        data = sample()
        del data["scores"]["feasibility"]
        with self.assertRaises(ValueError):
            evaluate_opportunity(data)

    def test_rejects_invalid_score(self):
        data = sample()
        data["scores"]["customer_pain"] = 6
        with self.assertRaises(ValueError):
            evaluate_opportunity(data)

    def test_rejects_unknown_product_type(self):
        data = sample()
        data["product_type"] = "magic"
        with self.assertRaises(ValueError):
            evaluate_opportunity(data)

    def test_list_opportunities_sorts_by_score_and_skips_invalid_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = evaluate_opportunity(sample())
            second_data = sample()
            second_data["name"] = "Assistant de documentation"
            second_data["scores"] = {key: 2 for key in DIMENSIONS}
            second = evaluate_opportunity(second_data)
            save_opportunity(first, root)
            save_opportunity(second, root)
            (root / "broken.json").write_text("{invalid", encoding="utf-8")
            ranked = __import__("atelier_produits").list_opportunities(root)
            self.assertEqual([item["score_percent"] for item in ranked], [80, 40])
            self.assertEqual(ranked[0]["id"], first["id"])

    def test_list_opportunities_rejects_non_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "file.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                __import__("atelier_produits").list_opportunities(path)

    def test_saves_report(self):
        report = evaluate_opportunity(sample())
        with tempfile.TemporaryDirectory() as folder:
            path = save_opportunity(report, Path(folder))
            self.assertTrue(path.exists())
            self.assertIn('"automatic_sale": false', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
