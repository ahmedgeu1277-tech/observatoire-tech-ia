import unittest
from unittest.mock import patch

from sources_specialisees import FEEDS, fetch_specialized_sources, parse_feed


class SpecializedFeedTests(unittest.TestCase):
    def test_parse_rss_feed(self):
        xml = b"""<?xml version='1.0'?><rss version='2.0'><channel><item><title>Annonce IA</title><link>https://example.org/news/1</link><description>Une nouveaute.</description><pubDate>Mon, 16 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
        result = parse_feed(xml, "Source test", "https://example.org/feed.xml")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["publisher"], "Source test")
        self.assertEqual(result[0]["title"], "Annonce IA")
        self.assertEqual(result[0]["source_type"], "flux_officiel")

    def test_game_engine_official_feeds_are_configured(self):
        publishers = {publisher for publisher, _ in FEEDS["gaming"]}
        self.assertTrue({"Unity", "Unreal Engine / Epic", "Godot", "GameMaker"}.issubset(publishers))

    @patch("sources_specialisees.requests.get")
    def test_game_engine_theme_collects_sources(self, mock_get):
        class Response:
            content = b"""<rss><channel><item><title>Engine update</title><link>https://example.org/update</link><description>Release notes</description></item></channel></rss>"""
            def raise_for_status(self):
                pass
        mock_get.return_value = Response()
        result = fetch_specialized_sources("Moteurs et logiciels de création de jeux", limit=10)
        self.assertEqual(len(result), 1)
        self.assertEqual(mock_get.call_count, 4)

    def test_rejects_non_http_links(self):
        xml = b"""<rss><channel><item><title>Bad</title><link>javascript:alert(1)</link></item></channel></rss>"""
        self.assertEqual(parse_feed(xml, "Test", "https://example.org/feed.xml"), [])

if __name__ == "__main__":
    unittest.main()


    @patch("sources_specialisees.requests.get")
    def test_roblox_theme_uses_filtered_gaming_feeds(self, mock_get):
        class Response:
            content = b"""<rss><channel>
            <item><title>Roblox Studio update</title><link>https://example.org/roblox</link><description>Roblox creation tools.</description></item>
            <item><title>Unrelated game news</title><link>https://example.org/other</link><description>Other game.</description></item>
            </channel></rss>"""
            def raise_for_status(self):
                pass
        mock_get.return_value = Response()
        result = fetch_specialized_sources("Roblox et création de jeux", limit=10)
        self.assertTrue(result)
        self.assertTrue(all("roblox" in (item["title"] + item["description"]).lower() for item in result))
        self.assertEqual(mock_get.call_count, 3)

    @patch("sources_specialisees.requests.get")
    def test_gta_theme_uses_gaming_feeds(self, mock_get):
        class Response:
            content = b"""<rss><channel><item><title>GTA VI news</title><link>https://example.org/gta</link><description>Rockstar update.</description></item></channel></rss>"""
            def raise_for_status(self):
                pass
        mock_get.return_value = Response()
        result = fetch_specialized_sources("GTA VI — préparation du lancement", limit=10)
        self.assertTrue(result)
        self.assertTrue(all("gta" in (item["title"] + item["description"]).lower() or
                            "rockstar" in (item["title"] + item["description"]).lower() for item in result))
