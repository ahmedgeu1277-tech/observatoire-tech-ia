import tempfile
import unittest
from pathlib import Path

from laboratoire_invention import create_idea, list_ideas, update_status


class InventionRegistryTests(unittest.TestCase):
    def test_create_and_list_idea(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ideas.json"
            item = create_idea("Réduire le temps de test", "Créer un banc de tests modulaire", "logiciel", path)
            self.assertEqual(item["status"], "idee")
            self.assertFalse(item["prior_art_checked"])
            self.assertEqual(list_ideas(path)[0]["id"], item["id"])

    def test_rejects_empty_fields(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaises(ValueError),
        ):
            create_idea("", "proposition", "logiciel", Path(folder) / "ideas.json")

    def test_corrupt_registry_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ideas.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                create_idea("problème", "proposition", "logiciel", path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_status_update(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ideas.json"
            item = create_idea("problème", "proposition", "logiciel", path)
            changed = update_status(item["id"], "documentee", path)
            self.assertEqual(changed["status"], "documentee")


if __name__ == "__main__":
    unittest.main()
