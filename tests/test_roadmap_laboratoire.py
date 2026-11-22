import json
import tempfile
import unittest
from pathlib import Path

import roadmap_laboratoire


class RoadmapTests(unittest.TestCase):
    def test_default_tasks_are_available_without_writing_public_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".laboratoire_prive" / "roadmap.json"
            rows = roadmap_laboratoire.list_tasks(path)
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(row["status"] == "backlog" for row in rows))
            self.assertFalse(path.exists())

    def test_status_update_is_persisted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".laboratoire_prive" / "roadmap.json"
            row = roadmap_laboratoire.update_status(path, "translate_archive", "in_progress")
            self.assertEqual(row["status"], "in_progress")
            stored = roadmap_laboratoire.list_tasks(path)
            self.assertEqual(next(x for x in stored if x["id"] == "translate_archive")["status"], "in_progress")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[0]["status"], "in_progress")

    def test_due_date_requires_timezone_and_is_persisted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "roadmap.json"
            with self.assertRaises(ValueError):
                roadmap_laboratoire.update_status(path, "translate_archive", "in_progress", "2026-12-01T12:00")
            row = roadmap_laboratoire.update_status(
                path, "translate_archive", "in_progress", "2026-12-01T12:00:00+00:00"
            )
            self.assertEqual(row["due_at"], "2026-12-01T12:00:00+00:00")
            cleared = roadmap_laboratoire.update_status(path, "translate_archive", "in_progress", "")
            self.assertIsNone(cleared["due_at"])

    def test_unknown_task_and_status_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "roadmap.json"
            with self.assertRaises(ValueError):
                roadmap_laboratoire.update_status(path, "../secret", "done")
            with self.assertRaises(ValueError):
                roadmap_laboratoire.update_status(path, "translate_archive", "unknown")

    def test_corrupted_local_file_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "roadmap.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                roadmap_laboratoire.list_tasks(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
