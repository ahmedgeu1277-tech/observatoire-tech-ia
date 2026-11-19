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
        profile_index = {"profiles": [{
            "name": "veilleur", "role": "Analyste", "mission": "Veille publique",
            "status": "profil configuré — non exécuté en continu"
        }]}
        (root / "site" / "data" / "agents.json").write_text(json.dumps(profile_index), encoding="utf-8")

    def _articles_path(self, root):
        return root / "site" / "articles.json"

    def test_valid_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            self.assertEqual(check_repository(root)["articles"], 1)
            self.assertEqual(check_repository(root)["agent_profiles"], 1)

    def test_private_city_state_must_not_be_published(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            (root / "site" / "data" / "gouvernement.json").write_text(json.dumps({"private": True}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Données internes interdites"):
                check_repository(root)

    def test_duplicate_article_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = self._articles_path(root)
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

    def test_profiles_cannot_be_marked_as_running_agents(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = root / "site" / "data" / "agents.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["profiles"][0]["status"] = "actif"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ne doit pas être présenté"):
                check_repository(root)

    def test_insecure_source_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = self._articles_path(root)
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["sources"][0]["url"] = "javascript:alert(1)"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non sécurisée"):
                check_repository(root)

    def test_source_url_with_embedded_credentials_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = self._articles_path(root)
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["sources"][0]["url"] = "https://user:password@example.org/article"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non sécurisée"):
                check_repository(root)

    def test_source_url_with_invalid_port_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = self._articles_path(root)
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["sources"][0]["url"] = "https://example.org:invalid/article"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non sécurisée"):
                check_repository(root)

    def test_audio_symlink_cannot_escape_public_audio_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            outside = root / "private.mp3"
            outside.write_bytes(b"private")
            link = root / "site" / "audio" / "outside.mp3"
            link.symlink_to(outside)
            path = self._articles_path(root)
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["audio_url"] = "audio/outside.mp3"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hors du dossier"):
                check_repository(root)

    def test_non_string_article_id_is_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._fixture(root)
            path = self._articles_path(root)
            articles = json.loads(path.read_text(encoding="utf-8"))
            articles[0]["id"] = ["not", "an", "id"]
            path.write_text(json.dumps(articles), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Article incomplet"):
                check_repository(root)


if __name__ == "__main__":
    unittest.main()
