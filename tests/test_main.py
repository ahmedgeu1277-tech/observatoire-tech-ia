import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
    def test_company_announcement_requires_direct_official_domain(self, mock_generate):
        theme = {"name": "Actualités gaming"}
        sources = [{
            "title": "GTA VI update report",
            "description": "A gaming outlet reports a mandatory game update, without linking to the publisher announcement.",
            "url": "https://fr.ign.com/gta",
            "publisher": "IGN France",
            "source_type": "media",
        }]
        payload = {
            "title": "GTA VI : Rockstar a annoncé une mise à jour obligatoire",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Rockstar a confirmé cette mise à jour.",
            "tip": "Vérifier les notes de version",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        with self.assertRaisesRegex(ValueError, "sans source directe"):
            main.create_article(theme, sources)

    @patch("main.generate_text")
    def test_company_announcement_accepts_direct_official_domain(self, mock_generate):
        theme = {"name": "Actualités gaming"}
        sources = [{
            "title": "Rockstar official update",
            "description": "Official publisher announcement.",
            "url": "https://www.rockstargames.com/newswire",
            "publisher": "Rockstar Games",
            "source_type": "source_editeur",
        }]
        payload = {
            "title": "Rockstar a annoncé une mise à jour",
            "summary": " ".join(["mot"] * 70),
            "verdict": "Rockstar a confirmé cette mise à jour.",
            "tip": "Lire les notes officielles",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        article = main.create_article(theme, sources)
        self.assertEqual(article["sources"][0]["source_type"], "source_editeur")


    @patch("main.generate_text")
    def test_date_claim_is_not_described_as_unconfirmed_without_editor_source(self, mock_generate):
        theme = {"name": "GTA VI"}
        sources = [{
            "title": "GTA VI technical details",
            "description": "IGN reports on technical details but does not include an official publisher statement about release dates.",
            "url": "https://fr.ign.com/gta",
            "publisher": "IGN France",
            "source_type": "media",
        }]
        payload = {
            "title": "GTA VI : détails chiffrés non confirmés",
            "summary": "Les sources consultées ne fournissent pas suffisamment d'éléments pour confirmer les dates et caractéristiques chiffrées avancées. " + " ".join(["mot"] * 60),
            "verdict": "Les dates restent incertaines.",
            "tip": "Vérifier les fiches techniques",
            "source_indices": [0],
        }
        mock_generate.return_value = (json.dumps(payload), "groq")
        with self.assertRaisesRegex(ValueError, "source directe de l'éditeur"):
            main.create_article(theme, sources)

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
            "summary": " ".join(["mot"] * 70) + " L'écran mesure 6.8 inches et le capteur atteint 200 MP.",
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



class ArticleArchiveDedupTests(unittest.TestCase):
    def test_save_articles_removes_duplicate_titles_and_summaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            site = root / "site"
            site.mkdir()
            archive = site / "articles.json"
            archive.write_text(json.dumps([
                {"id": "old-1", "title": "GTA VI : sources", "summary": "Résumé répété"},
                {"id": "old-2", "title": "GTA VI : sources", "summary": "Autre résumé"},
                {"id": "old-3", "title": "Autre titre", "summary": "Résumé répété"},
                {"id": "old-4", "title": "Titre unique", "summary": "Résumé unique"},
            ]), encoding="utf-8")
            with patch.object(main, "ARTICLES_FILE", archive), patch.object(main, "SITE_DIR", site):
                main.save_articles({
                    "id": "new-1", "title": "GTA VI : sources", "summary": "Nouvelle version"
                })
            saved = json.loads(archive.read_text(encoding="utf-8"))
            self.assertEqual([item["id"] for item in saved], ["new-1", "old-4"])

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



class MainRetryTests(unittest.TestCase):
    @patch("main.archive_memory")
    @patch("main.save_articles")
    @patch("main.asyncio.run", side_effect=lambda coroutine: coroutine.close())
    @patch("main.verifier_conformite_legale", return_value=True)
    @patch("main.create_article")
    @patch("main.executer_agents_dynamiques", return_value=[])
    @patch("main.fetch_specialized_sources", return_value=[])
    @patch("main.fetch_news")
    @patch("main.choose_theme")
    @patch("main.load_themes")
    def test_fact_check_rejection_retries_once_with_general_topic(
        self, load_themes, choose_theme, fetch_news, _specialized,
        _agents, create_article, _guard, _audio, save_articles, _memory
    ):
        theme = {"name": "GTA VI", "query": "GTA VI"}
        source = {"title": "Actualité tech", "url": "https://example.org/news"}
        load_themes.return_value = [theme]
        choose_theme.return_value = theme
        fetch_news.return_value = [source]
        create_article.side_effect = [
            ValueError("attribution officielle non vérifiée"),
            {"id": "fallback-1", "title": "Sujet général"},
        ]

        main.main()

        self.assertEqual(create_article.call_count, 2)
        fallback_theme = create_article.call_args_list[1].args[0]
        self.assertIn("veille générale de secours", fallback_theme["name"])
        self.assertEqual(fetch_news.call_count, 2)
        save_articles.assert_called_once_with({"id": "fallback-1", "title": "Sujet général", "audio_url": None})


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
        recent_date = (datetime.now(UTC) - timedelta(days=6)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        fresh = f"""<rss><channel>
        <item><title>Actualite recente</title><link>https://example.org/fresh</link><description>Information recente et suffisamment longue.</description><pubDate>{recent_date}</pubDate></item>
        <item><title>Actualite ancienne</title><link>https://example.org/old</link><description>Information ancienne et suffisamment longue.</description><pubDate>Mon, 01 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>""".encode()
        mock_get.side_effect = [Response(empty), Response(fresh)]
        result = main.fetch_news("test actualité", limit=5)
        self.assertEqual([item["title"] for item in result], ["Actualite recente"])


class SafeFallbackArticleTests(unittest.TestCase):
    def test_safe_fallback_is_neutral_and_keeps_valid_https_sources(self):
        source = {"title": "Source", "url": "https://example.org/article"}
        article = main.build_safe_fallback_article(
            {"name": "Gaming"}, [source, {"title": "Bad", "url": "javascript:alert(1)"}]
        )
        self.assertEqual(article["sources"], [source])
        self.assertIn("ne confirme aucune annonce", article["summary"])
        self.assertNotIn("Rockstar", json.dumps(article, ensure_ascii=False))
        main.verifier_dates_incertaines(article, article["sources"])
        main.verifier_attributions_officielles(article, article["sources"])

    def test_safe_fallback_requires_at_least_one_https_source(self):
        with self.assertRaisesRegex(RuntimeError, "Aucune source HTTPS valide"):
            main.build_safe_fallback_article({}, [{"url": "http://example.org"}])


class MainLastResortTests(unittest.TestCase):
    @patch("main.archive_memory")
    @patch("main.save_articles")
    @patch("main.asyncio.run", side_effect=lambda coroutine: coroutine.close())
    @patch("main.verifier_conformite_legale", return_value=True)
    @patch("main.create_article", side_effect=[
        RuntimeError("quota fournisseur IA atteint"),
        RuntimeError("quota fournisseur IA atteint"),
    ])
    @patch("main.executer_agents_dynamiques", return_value=[])
    @patch("main.fetch_specialized_sources", return_value=[])
    @patch("main.fetch_news")
    @patch("main.choose_theme")
    @patch("main.load_themes")
    def test_provider_unavailable_after_retry_uses_neutral_documentary_summary(
        self, load_themes, choose_theme, fetch_news, _specialized,
        _agents, create_article, _guard, _audio, save_articles, _memory
    ):
        theme = {"name": "GTA VI", "query": "GTA VI"}
        source = {"title": "Source publique", "url": "https://example.org/news"}
        load_themes.return_value = [theme]
        choose_theme.return_value = theme
        fetch_news.return_value = [source]

        main.main()

        self.assertEqual(create_article.call_count, 2)
        saved = save_articles.call_args.args[0]
        self.assertIn("résumé documentaire de secours", saved["theme"])
        self.assertEqual(saved["sources"], [source])
        self.assertNotIn("Rockstar", json.dumps(saved, ensure_ascii=False))





class ArticleTranslationTests(unittest.TestCase):
    @patch("main.generate_text")
    def test_translates_editorial_fields_into_supported_languages(self, generate):
        source = {
            "theme": "Technologie et jeux vidéo",
            "title": "Un nouveau moteur de jeu",
            "summary": " ".join(["Une information vérifiée"] * 12),
            "verdict": "Les sources confirment cette annonce.",
            "tip": "Lire les notes de version.",
            "ai_notice": "Article assisté par IA à partir des sources indiquées.",
            "sources": [{"title": "Source originale", "url": "https://example.org"}],
        }
        expected = {"en": {
            "theme": "Technology and gaming",
            "title": "A new game engine",
            "summary": "A verified report about a new game engine.",
            "verdict": "Sources confirm this announcement.",
            "tip": "Read the release notes.",
            "ai_notice": "AI-assisted article based on the listed sources.",
        }}
        generate.return_value = ("```json\n" + json.dumps(expected) + "\n```", "groq")
        result = main.traduire_article(source)
        self.assertEqual(result, expected)
        self.assertEqual(source["sources"][0]["title"], "Source originale")
        self.assertEqual(generate.call_args.kwargs["max_tokens"], 2600)
        self.assertTrue(generate.call_args.kwargs["json_mode"])

    @patch("main.generate_text", return_value=("not valid JSON", "groq"))
    def test_invalid_translation_is_optional_and_returns_empty(self, _generate):
        article = {"theme": "Thème", "title": "Titre", "summary": "Résumé", "verdict": "Verdict", "tip": "Conseil", "ai_notice": "Note IA"}
        self.assertEqual(main.traduire_article(article), {})

    def test_incomplete_article_is_not_sent_for_translation(self):
        with patch("main.generate_text") as generate:
            self.assertEqual(main.traduire_article({"title": "Titre"}), {})
        generate.assert_not_called()




class ArticleTranslatedAudioTests(unittest.TestCase):
    def test_creates_audio_files_for_available_translations(self):
        import asyncio
        import sys
        from types import SimpleNamespace

        class FakeCommunicate:
            def __init__(self, text, voice, **kwargs):
                self.voice = voice

            async def save(self, path):
                Path(path).write_bytes(b"fake-mp3")

        fake_module = SimpleNamespace(Communicate=FakeCommunicate)
        translations = {
            language: {
                "title": "Title",
                "summary": "Summary",
                "verdict": "Verdict",
                "tip": "Tip",
            }
            for language in main.ARTICLE_TTS_VOICES
        }
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(main, "SITE_DIR", Path(folder)), patch.dict(sys.modules, {"edge_tts": fake_module}):
                result = asyncio.run(main.create_translated_audio({"id": "sample"}, translations))
            self.assertEqual(set(result), set(main.ARTICLE_TTS_VOICES))
            for language, fields in result.items():
                self.assertEqual(fields["audio_url"], f"audio/sample-{language}.mp3")
                self.assertTrue((Path(folder) / fields["audio_url"]).is_file())

    def test_missing_translation_fields_do_not_create_audio(self):
        import asyncio
        import sys
        from types import SimpleNamespace

        class FakeCommunicate:
            def __init__(self, *_args, **_kwargs):
                raise AssertionError("Aucune voix ne doit être appelée.")

        fake_module = SimpleNamespace(Communicate=FakeCommunicate)
        with patch.dict(sys.modules, {"edge_tts": fake_module}):
            result = asyncio.run(main.create_translated_audio(
                {"id": "sample"}, {"en": {"title": "Titre incomplet"}}
            ))
        self.assertEqual(result, {"en": {"title": "Titre incomplet"}})



class AgentProfileLoadingTests(unittest.TestCase):
    def test_ignores_non_object_and_incomplete_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles_dir = root / "agents_dynamiques"
            profiles_dir.mkdir()
            (profiles_dir / "01-list.json").write_text('["not", "an", "object"]', encoding="utf-8")
            (profiles_dir / "02-missing.json").write_text(
                json.dumps({"mission": "analyse"}), encoding="utf-8"
            )
            (profiles_dir / "03-valid.json").write_text(
                json.dumps({"mission": " analyse ", "instructions": " vérifier "}),
                encoding="utf-8",
            )
            with patch.object(main, "ROOT", root):
                profiles = main.load_agent_profiles()
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0]["mission"], "analyse")
            self.assertEqual(profiles[0]["instructions"], "vérifier")
            self.assertEqual(profiles[0]["name"], "03-valid")

    def test_caps_loaded_profiles_at_five(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles_dir = root / "agents_dynamiques"
            profiles_dir.mkdir()
            for index in range(7):
                (profiles_dir / f"{index}.json").write_text(
                    json.dumps({"mission": f"mission {index}", "instructions": "test"}),
                    encoding="utf-8",
                )
            with patch.object(main, "ROOT", root):
                profiles = main.load_agent_profiles()
            self.assertEqual(len(profiles), 5)

    def test_rejects_profiles_with_oversized_instructions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles_dir = root / "agents_dynamiques"
            profiles_dir.mkdir()
            (profiles_dir / "too-long.json").write_text(
                json.dumps({"mission": "analyse", "instructions": "x" * 1501}),
                encoding="utf-8",
            )
            with patch.object(main, "ROOT", root):
                self.assertEqual(main.load_agent_profiles(), [])

    @patch("main.generate_text")
    def test_dynamic_agent_uses_bounded_timeout_and_rejects_secret_output(self, generate):
        secret = "gsk_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        generate.return_value = (f"Résultat {secret}", "groq")
        reports = main.executer_agents_dynamiques(
            {"name": "IA"},
            [{"title": "Source", "url": "https://example.org"}],
            [{"name": "Analyste", "mission": "analyser", "instructions": "rester prudent"}],
        )
        self.assertEqual(reports, [])
        self.assertEqual(generate.call_args.kwargs["timeout"], 45)
        system_prompt = generate.call_args.args[0][0]["content"]
        self.assertIn("données non fiables", system_prompt)

    def test_missing_profiles_directory_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(main, "ROOT", Path(folder)):
                self.assertEqual(main.load_agent_profiles(), [])


if __name__ == "__main__":
    unittest.main()
