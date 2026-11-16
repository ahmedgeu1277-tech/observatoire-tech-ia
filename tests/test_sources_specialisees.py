import unittest
from sources_specialisees import parse_feed

class SpecializedFeedTests(unittest.TestCase):
    def test_parse_rss_feed(self):
        xml = b"""<?xml version='1.0'?><rss version='2.0'><channel><item><title>Annonce IA</title><link>https://example.org/news/1</link><description>Une nouveaute.</description><pubDate>Mon, 16 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
        result = parse_feed(xml, "Source test", "https://example.org/feed.xml")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["publisher"], "Source test")
        self.assertEqual(result[0]["title"], "Annonce IA")
        self.assertEqual(result[0]["source_type"], "flux_officiel")

    def test_rejects_non_http_links(self):
        xml = b"""<rss><channel><item><title>Bad</title><link>javascript:alert(1)</link></item></channel></rss>"""
        self.assertEqual(parse_feed(xml, "Test", "https://example.org/feed.xml"), [])

if __name__ == "__main__":
    unittest.main()
