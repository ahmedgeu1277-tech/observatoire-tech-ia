import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from traduire_archives import backfill_translations


class ArticleTranslationBackfillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "articles.json"
        self.items = [
            {"id": "new", "title": "Newest", "sources": [{"url": "https://new.example"}]},
            {"id": "old", "title": "Oldest", "sources": [{"url": "https://old.example"}]},
        ]
        self.path.write_text(json.dumps(self.items), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    @patch("traduire_archives.main.traduire_article")
    def test_translates_oldest_first_and_preserves_sources(self, translate):
        translate.return_value = {
            language: {
                "title": "Translated",
                "summary": "Translated summary",
                "verdict": "Translated verdict",
                "tip": "Translated tip",
            }
            for language in ("en", "es", "de", "pt", "ar", "zh")
        }
        with patch.object(main, "ARTICLES_FILE", self.path):
            result = backfill_translations(1)
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(result, {"translated": 1, "remaining": 1, "total": 2})
        self.assertIn("translations", saved[1])
        self.assertNotIn("translations", saved[0])
        self.assertEqual(saved[1]["sources"], self.items[1]["sources"])

    @patch("traduire_archives.main.traduire_article", return_value={})
    def test_provider_failure_stops_without_corrupting_archive(self, _translate):
        before = self.path.read_text(encoding="utf-8")
        with patch.object(main, "ARTICLES_FILE", self.path):
            result = backfill_translations()
        self.assertEqual(result["translated"], 0)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_rejects_oversized_batch(self):
        with patch.object(main, "ARTICLES_FILE", self.path):
            with self.assertRaises(ValueError):
                backfill_translations(6)


if __name__ == "__main__":
    unittest.main()
