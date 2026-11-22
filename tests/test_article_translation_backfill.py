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

    @patch(
        "traduire_archives.main.create_translated_audio",
        side_effect=lambda article, data: {
            lang: {**fields, "audio_url": f"audio/{lang}.mp3"}
            for lang, fields in data.items()
        },
    )
    @patch("traduire_archives.main.traduire_article")
    def test_translates_oldest_first_and_preserves_sources(self, translate, _audio):
        translate.return_value = {
            language: {
                "theme": "Translated theme",
                "title": "Translated",
                "summary": "Translated summary",
                "verdict": "Translated verdict",
                "tip": "Translated tip",
                "ai_notice": "Translated AI note",
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

    @patch(
        "traduire_archives.main.create_translated_audio",
        side_effect=lambda article, data: {
            lang: {**fields, "audio_url": f"audio/{lang}.mp3"}
            for lang, fields in data.items()
        },
    )
    @patch("traduire_archives.main.traduire_article")
    def test_accepts_five_articles_in_one_bounded_batch(self, translate, _audio):
        self.items = [
            {"id": str(index), "title": f"Article {index}", "sources": []}
            for index in range(6)
        ]
        self.path.write_text(json.dumps(self.items), encoding="utf-8")
        translate.return_value = {
            language: {
                "theme": "Thème", "title": "Titre", "summary": "Résumé",
                "verdict": "Verdict", "tip": "Conseil", "ai_notice": "IA",
            }
            for language in ("en", "es", "de", "pt", "ar", "zh")
        }
        with patch.object(main, "ARTICLES_FILE", self.path):
            result = backfill_translations(5)
        self.assertEqual(result, {"translated": 5, "remaining": 1, "total": 6})

    def test_rejects_oversized_batch(self):
        with patch.object(main, "ARTICLES_FILE", self.path):
            with self.assertRaises(ValueError):
                backfill_translations(6)


if __name__ == "__main__":
    unittest.main()
