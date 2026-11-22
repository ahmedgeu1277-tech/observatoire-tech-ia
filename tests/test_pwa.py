import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class ProgressiveWebAppTests(unittest.TestCase):
    def test_manifest_is_valid_and_scoped_to_site(self):
        manifest = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "./")
        self.assertEqual(manifest["scope"], "./")
        self.assertEqual(manifest["short_name"], "NEXORA")
        self.assertEqual(manifest["display"], "standalone")
        self.assertTrue((SITE / manifest["icons"][0]["src"]).is_file())

    def test_homepage_registers_service_worker_and_manifest(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="manifest" href="./manifest.webmanifest"', html)
        self.assertIn('navigator.serviceWorker.register("./sw.js"', html)
        self.assertIn('location.protocol === "https:"', html)
        self.assertIn('"127.0.0.1"', html)

    def test_service_worker_only_caches_same_origin_get_requests(self):
        worker = (SITE / "sw.js").read_text(encoding="utf-8")
        self.assertIn('request.method !== "GET"', worker)
        self.assertIn('new URL(request.url).origin !== self.location.origin', worker)
        self.assertIn('request.mode === "navigate"', worker)
        self.assertIn('caches.match("./offline.html")', worker)
        self.assertIn('nexora-public-v1', worker)
        self.assertIn('"./articles.json"', worker)
        self.assertIn("mp3|mp4|webm|m4a|ogg|wav", worker)
        self.assertIn("Ne pas mettre en cache les médias lourds", worker)

    def test_media_range_requests_bypass_cache_api(self):
        worker = (SITE / "sw.js").read_text(encoding="utf-8")
        self.assertIn('request.headers.has("range")', worker)
        self.assertIn('event.respondWith(fetch(request))', worker)
        self.assertIn("Cache API ne peut pas les stocker", worker)

    def test_offline_page_exists_and_does_not_claim_live_data(self):
        page = (SITE / "offline.html").read_text(encoding="utf-8")
        self.assertIn("MODE HORS LIGNE", page)
        self.assertIn("pas encore enregistrée", page)


if __name__ == "__main__":
    unittest.main()
