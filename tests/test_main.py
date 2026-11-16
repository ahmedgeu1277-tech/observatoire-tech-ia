import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import main


class ThemeLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.theme = {
            "name": "Gaming",
            "query": "gaming",
            "lifecycle": {
                "start_at": "2026-11-16T00:00:00Z",
                "launch_at": "2026-11-18T17:00:00Z",
                "end_at": "2026-11-26T23:59:59Z",
                "before": {"name": "Avant lancement", "query": "préparation"},
                "after": {"name": "Après lancement", "query": "retours vérifiés"},
            },
        }

    def test_uses_before_variant_before_launch(self):
        now = datetime(2026, 11, 18, 16, 59, tzinfo=timezone.utc)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Avant lancement")
        self.assertEqual(result["query"], "préparation")

    def test_switches_to_after_variant_at_launch(self):
        now = datetime(2026, 11, 18, 17, 0, tzinfo=timezone.utc)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Après lancement")

    def test_returns_base_theme_after_campaign(self):
        now = datetime(2026, 11, 27, 0, 0, tzinfo=timezone.utc)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Gaming")
        self.assertEqual(result["query"], "gaming")

    def test_invalid_lifecycle_is_rejected(self):
        broken = {"name": "Gaming", "lifecycle": {"launch_at": "date"}}
        with self.assertRaises(ValueError):
            main.appliquer_cycle_vie(broken, datetime.now(timezone.utc))

    def test_event_theme_is_prioritized_only_during_its_window(self):
        themes = [self.theme, {"name": "IA", "query": "ia"}]
        before_window = datetime(2026, 11, 15, 23, 59, tzinfo=timezone.utc)
        during_window = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
        after_window = datetime(2026, 11, 27, 0, 0, tzinfo=timezone.utc)
        self.assertIsNone(main.get_priority_event_theme(themes, before_window))
        self.assertIs(main.get_priority_event_theme(themes, during_window), self.theme)
        self.assertIsNone(main.get_priority_event_theme(themes, after_window))


class ArticleValidationTests(unittest.TestCase):
    def setUp(self):
        self.theme = {"name": "Test"}
        self.sources = [
            {"title": "Source test", "url": "https://example.com/article"}
        ]

    @patch("main.generate_text", return_value=("pas du JSON", "groq"))
    def test_invalid_ai_json_is_not_published(self, _mock):
        with self.assertRaisesRegex(ValueError, "Aucun article publié"):
            main.create_article(self.theme, self.sources)

    @patch("main.generate_text")
    def test_invalid_source_index_is_rejected(self, mock_generate):
        payload = {
            "title": "Titre test",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Verdict prudent",
            "tip": "Consulter la source originale",
            "source_indices": [9],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        with self.assertRaisesRegex(ValueError, "indice de source invalide"):
            main.create_article(self.theme, self.sources)


class ArchiveSafetyTests(unittest.TestCase):
    def test_corrupted_archive_is_not_silently_replaced(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as folder:
            target = Path(folder) / "articles.json"
            target.write_text("{broken", encoding="utf-8")
            with patch.object(main, "ARTICLES_FILE", target):
                with self.assertRaisesRegex(RuntimeError, "préserver les archives"):
                    main.load_previous_articles()



class ThemeSelectionTests(unittest.TestCase):
    def test_event_theme_gets_alternating_priority(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        event = {
            "name": "GTA VI",
            "query": "GTA VI",
            "lifecycle": {
                "start_at": "2026-11-16T00:00:00Z",
                "launch_at": "2026-11-18T17:00:00Z",
                "end_at": "2026-11-26T23:59:59Z",
                "before": {"name": "GTA VI avant", "query": "GTA VI préparation"},
                "after": {"name": "GTA VI après", "query": "GTA VI tests"},
            },
        }
        other = {"name": "IA", "query": "IA"}
        with TemporaryDirectory() as folder:
            with patch.object(main, "ROOT", Path(folder)):
                self.assertEqual(main.choose_theme([event, other])["name"], "GTA VI")
                self.assertEqual(main.choose_theme([event, other])["name"], "IA")


if __name__ == "__main__":
    unittest.main()
