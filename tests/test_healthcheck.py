import json
import tempfile
import unittest
from pathlib import Path

from healthcheck import check_repository


class RepositoryHealthTests(unittest.TestCase):
    def _fixture(self, root: Path):
        (root / "site" / "audio").mkdir(parents=True)
        (root / "site" / "data").mkdir(parents=True)
        (root / "themes.json").write_text(json.dumps({"themes": [{"name": "IA", "query": "actualités IA"}]}), encoding="utf-8")
        (root / "site" / "audio" / "demo.mp3").write_bytes(b"audio")
        article = {
            "id": "demo-1", "date": "2026-11-17T12:00Z", "theme": "IA",
            "title": "Titre", "summary": "Résumé", "verdict": "Prudent",
            "tip": "Lire la source", "sources": [{"url": "https://example.org/article"}],
            "audio_url": "audio/demo.mp3"
        }
        (root / "site" / "articles.json").write_text(json.dumps([article]), encoding="utf-8")
        government = {"directors": [{} for _ in range(30)], "currency": {"real_value": 0}}
        (root / "site" / "data" / "gouvernement.json").write_text(json.dumps(government), encoding="utf-8")

    def test_valid_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            self.assertEqual(check_repository(root)["articles"], 1)

    def test_duplicate_article_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = root / "site" / "articles.json"
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles.append(dict(articles[0]))
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dupliqué"):
                check_repository(root)

    def test_missing_audio_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            (root / "site" / "audio" / "demo.mp3").unlink()
            with self.assertRaisesRegex(ValueError, "audio absent"):
                check_repository(root)

    def test_insecure_source_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = root / "site" / "articles.json"
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["sources"][0]["url"] = "javascript:alert(1)"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non sécurisée"):
                check_repository(root)


if __name__ == "__main__":
    unittest.main()
