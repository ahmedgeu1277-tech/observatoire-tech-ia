import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import video_longue


class WeeklyDocumentaryTests(unittest.TestCase):
    def test_compiles_five_chapters_from_distinct_https_articles(self):
        articles = []
        for index, theme in enumerate(("GTA VI", "Roblox", "Cybersécurité"), 1):
            articles.append({
                "date": f"2026-11-17T0{index}:00:00Z",
                "theme": theme,
                "title": f"Dossier {theme}",
                "summary": "Résumé éditorial suffisamment long pour servir de base au chapitre documentaire.",
                "verdict": "Les détails restent à vérifier dans les sources originales.",
                "tip": "Consulter les sources officielles.",
                "sources": [{"publisher": "Source test", "url": f"https://example.org/{index}"}],
            })
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "articles.json"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with patch.object(video_longue, "ARTICLES_FILE", path):
                dossiers = video_longue.charger_dossiers()
        chapters = video_longue.construire_chapitres(dossiers)
        self.assertEqual(len(dossiers), 3)
        self.assertEqual(len(chapters), 5)
        self.assertEqual(chapters[0][3][0]["url"], "https://example.org/3")

    def test_rejects_articles_without_https_sources(self):
        articles = [{
            "date": "2026-11-17T00:00:00Z",
            "theme": f"Thème {index}",
            "title": f"Titre {index}",
            "summary": "Résumé assez long pour être pris en compte par le compilateur documentaire.",
            "verdict": "À vérifier",
            "tip": "Lire la source",
            "sources": [{"url": "http://example.org/article"}],
        } for index in range(3)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "articles.json"
            path.write_text(json.dumps(articles), encoding="utf-8")
            with patch.object(video_longue, "ARTICLES_FILE", path):
                with self.assertRaisesRegex(RuntimeError, "trois dossiers récents"):
                    video_longue.charger_dossiers()


if __name__ == "__main__":
    unittest.main()
