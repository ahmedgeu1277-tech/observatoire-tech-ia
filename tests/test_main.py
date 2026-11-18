import json
import unittest
from datetime import UTC, datetime
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
        now = datetime(2026, 11, 18, 16, 59, tzinfo=UTC)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Avant lancement")
        self.assertEqual(result["query"], "préparation")

    def test_switches_to_after_variant_at_launch(self):
        now = datetime(2026, 11, 18, 17, 0, tzinfo=UTC)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Après lancement")

    def test_returns_base_theme_after_campaign(self):
        now = datetime(2026, 11, 27, 0, 0, tzinfo=UTC)
        result = main.appliquer_cycle_vie(self.theme, now)
        self.assertEqual(result["name"], "Gaming")
        self.assertEqual(result["query"], "gaming")

    def test_event_window_works_without_launch_at_when_start_at_exists(self):
        theme = {
            "name": "Événement",
            "lifecycle": {
                "start_at": "2026-11-16T00:00:00Z",
                "end_at": "2026-11-26T23:59:59Z",
            },
        }
        now = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
        self.assertIs(main.get_priority_event_theme([theme], now), theme)

    def test_event_window_falls_back_to_launch_at_when_start_at_is_missing(self):
        theme = {
            "name": "Événement",
            "lifecycle": {
                "launch_at": "2026-11-18T17:00:00Z",
                "end_at": "2026-11-26T23:59:59Z",
            },
        }
        now = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
        self.assertIs(main.get_priority_event_theme([theme], now), theme)

    def test_invalid_lifecycle_is_rejected(self):
        broken = {"name": "Gaming", "lifecycle": {"launch_at": "date"}}
        with self.assertRaises(ValueError):
            main.appliquer_cycle_vie(broken, datetime.now(UTC))

    def test_event_theme_is_prioritized_only_during_its_window(self):
        themes = [self.theme, {"name": "IA", "query": "ia"}]
        before_window = datetime(2026, 11, 15, 23, 59, tzinfo=UTC)
        during_window = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
        after_window = datetime(2026, 11, 27, 0, 0, tzinfo=UTC)
        self.assertIsNone(main.get_priority_event_theme(themes, before_window))
        self.assertIs(main.get_priority_event_theme(themes, during_window), self.theme)
        self.assertIsNone(main.get_priority_event_theme(themes, after_window))


class ArticleValidationTests(unittest.TestCase):
    def test_news_source_classification_requires_direct_editor_domain(self):
        self.assertEqual(main.classify_news_source("www.rockstargames.com"), "source_editeur")
        self.assertEqual(main.classify_news_source("news.google.com"), "media")
        self.assertEqual(main.classify_news_source("fr.ign.com"), "media")


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
    def test_release_date_uncertainty_is_blocked_without_editor_source(self, mock_generate):
        theme = {"name": "Jeux vidéo annoncés pour 2027"}
        sources = [{
            "title": "GTA VI streaming records",
            "description": "IGN reports on a streaming record and preview impressions, but this article contains no statement from the game publisher about its release date.",
            "url": "https://example.com/gta",
            "publisher": "IGN France",
            "source_type": "media",
        }]
        payload = {
            "title": "GTA VI : dates de sortie toujours incertaines",
            "summary": " ".join(["mot"] * 70),
            "verdict": "La date officielle n'est pas encore communiquée.",
            "tip": "Vérifier les annonces",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        with self.assertRaisesRegex(ValueError, "source directe de l'éditeur"):
            main.create_article(theme, sources)

    @patch("main.generate_text")
    def test_release_date_uncertainty_requires_and_accepts_editor_source(self, mock_generate):
        theme = {"name": "GTA VI"}
        sources = [{
            "title": "GTA VI release update",
            "description": "The publisher says the date is not yet fixed.",
            "url": "https://www.rockstargames.com/VI",
            "publisher": "Rockstar Games",
            "source_type": "source_editeur",
        }]
        payload = {
            "title": "GTA VI : date de sortie incertaine selon Rockstar",
            "summary": " ".join(["mot"] * 70),
            "verdict": "L'éditeur n'a pas encore communiqué la date.",
            "tip": "Suivre la page officielle",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertEqual(article["sources"][0]["source_type"], "source_editeur")

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


    @patch("main.generate_text")
    def test_unverified_country_availability_is_rewritten_safely(self, mock_generate):
        theme = {"name": "GTA VI — préparation du lancement en Thaïlande"}
        sources = [{
            "title": "GTA VI release date and preload",
            "description": "The release timing and preload schedule.",
            "url": "https://example.com/gta",
            "publisher": "Example",
        }]
        payload = {
            "title": "GTA VI disponible en Thaïlande le 19 novembre",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Confirmé",
            "tip": "Consulter les annonces",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertIn("ne précisent pas la Thaïlande", article["title"])
        self.assertIn("aucune ne mentionne", article["summary"])
        self.assertIn("non confirmée", article["verdict"])


    @patch("main.generate_text")
    def test_unverified_engine_version_is_rewritten_safely(self, mock_generate):
        theme = {"name": "Moteurs et logiciels de création de jeux"}
        sources = [{
            "title": "Un projet européen veut concurrencer Unreal et Unity",
            "description": "Un nouveau moteur 3D est en développement.",
            "url": "https://example.com/engine",
        }]
        payload = {
            "title": "Unreal Engine 6 ajoute une IA générative",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Nouvelle version annoncée",
            "tip": "Consulter la documentation",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertEqual(article["title"], "Moteurs de jeu : versions non confirmées par les sources")
        self.assertIn("ne confirment pas", article["summary"])


    @patch("main.generate_text")
    def test_unsupported_technical_numbers_are_rewritten_safely(self, mock_generate):
        theme = {"name": "Matériel et smartphones"}
        sources = [{
            "title": "Galaxy S25 et iOS 28 : nouveautés attendues en 2027",
            "description": "Présentation détaillée des prochains appareils, des composants internes, des performances et des capacités photographiques.",
            "url": "https://example.com/phones",
        }]
        payload = {
            "title": "Galaxy S25 : Snapdragon 8 Gen 3 et capteur 200 MP",
            "summary": " ".join(["mot"] * 70) + " L'écran mesure 6.8 inches et la sortie est prévue le 1 janvier 2027.",
            "verdict": "Caractéristiques confirmées",
            "tip": "Acheter le modèle",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertIn("détails chiffrés non confirmés", article["title"])
        self.assertIn("ne fournissent pas suffisamment", article["summary"])


    @patch("main.generate_text")
    def test_title_only_source_does_not_produce_detailed_claims(self, mock_generate):
        theme = {"name": "Sécurité numérique"}
        title = "Scality devient autorité de numérotation des vulnérabilités"
        sources = [{
            "title": title,
            "description": title + "  it social",
            "url": "https://example.com/scality",
        }]
        payload = {
            "title": "Scality améliore la coordination européenne des failles",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Impact majeur",
            "tip": "Suivre les annonces",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertIn("détails insuffisants dans les sources", article["title"])
        self.assertIn("reprennent surtout les titres", article["summary"])


class ArchiveSafetyTests(unittest.TestCase):
    def test_corrupted_archive_is_not_silently_replaced(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            target = Path(folder) / "articles.json"
            target.write_text("{broken", encoding="utf-8")
            with (
                patch.object(main, "ARTICLES_FILE", target),
                self.assertRaisesRegex(RuntimeError, "préserver les archives"),
            ):
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
        with (
            TemporaryDirectory() as folder,
            patch.object(main, "ROOT", Path(folder)),
        ):
            self.assertEqual(main.choose_theme([event, other])["name"], "GTA VI")
            self.assertEqual(main.choose_theme([event, other])["name"], "IA")


if __name__ == "__main__":
    unittest.main()


class NewsFallbackTests(unittest.TestCase):
    @patch("main.requests.get")
    def test_bing_is_used_when_google_news_fails(self, mock_get):
        import requests

        class Response:
            content = b"""<rss><channel><item><title>Actualite de secours</title><link>https://example.org/news</link><description>Information de test.</description></item></channel></rss>"""
            def raise_for_status(self):
                return None

        mock_get.side_effect = [requests.ConnectionError("Google indisponible"), Response()]
        result = main.fetch_news("test actualité", limit=2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Actualite de secours")
        self.assertEqual(mock_get.call_count, 2)


    @patch("main.requests.get")
    def test_bing_tracking_link_is_replaced_with_https_article_url(self, mock_get):
        class Response:
            content = b"""<rss><channel><item><title>Actualite</title><link>http://www.bing.com/news/apiclick?url=https%3A%2F%2Fexample.org%2Farticle</link><description>Resume.</description></item></channel></rss>"""
            def raise_for_status(self):
                return None

        mock_get.side_effect = [Response()]
        result = main.fetch_news("test", limit=1)
        self.assertEqual(result[0]["url"], "https://example.org/article")
        self.assertEqual(result[0]["domain"], "example.org")


    @patch("main.generate_text")
    def test_invalid_source_selection_is_repaired_once(self, mock_generate):
        payload = {
            "title": "Titre test",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Verdict prudent",
            "tip": "Consulter la source originale",
            "source_indices": [9],
        }
        mock_generate.side_effect = [
            (json.dumps(payload), "groq"),
            (json.dumps({"source_indices": [0]}), "groq"),
        ]
        theme = {"name": "Test"}
        sources = [{"title": "Source test", "url": "https://example.com/article"}]
        article = main.create_article(theme, sources)
        self.assertEqual(article["sources"], sources)
        self.assertEqual(mock_generate.call_count, 2)


    @patch("main.requests.get")
    def test_news_search_discards_items_older_than_seven_days(self, mock_get):
        class Response:
            def __init__(self, content):
                self.content = content
            def raise_for_status(self):
                return None

        empty = b"<rss><channel></channel></rss>"
        fresh = b"""<rss><channel>
        <item><title>Actualite recente</title><link>https://example.org/fresh</link><description>Information recente et suffisamment longue.</description><pubDate>Mon, 16 Nov 2026 10:00:00 GMT</pubDate></item>
        <item><title>Actualite ancienne</title><link>https://example.org/old</link><description>Information ancienne et suffisamment longue.</description><pubDate>Mon, 01 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        mock_get.side_effect = [Response(empty), Response(fresh)]
        result = main.fetch_news("test actualité", limit=5)
        self.assertEqual([item["title"] for item in result], ["Actualite recente"])
