import tempfile
import unittest
from pathlib import Path

from atelier_creation import TEMPLATES, generate_project, project_slug


class AtelierCreationTests(unittest.TestCase):
    def test_generates_each_supported_project_type(self):
        with tempfile.TemporaryDirectory() as folder:
            for kind, expected in {
                "site": "index.html", "webapp": "app.js", "jeu-web": "game.js",
                "video": "storyboard.md", "audio": "script.md", "logiciel-python": "main.py",
            }.items():
                with self.subTest(kind=kind):
                    result = generate_project("Projet Test", folder, kind)
                    self.assertTrue((Path(result["directory"]) / expected).is_file())
                    self.assertFalse(result["code_executed"])
                    self.assertFalse(result["published"])

    def test_rejects_traversal_and_bad_names(self):
        for name in ("../escape", "1invalid", "", "x" * 51, "a\\\\b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                project_slug(name)

    def test_rejects_unknown_type(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            generate_project("ProjetTest", folder, "unknown")

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            generate_project("ProjetTest", folder, "site")
            with self.assertRaises(FileExistsError):
                generate_project("ProjetTest", folder, "site")

    def test_all_templates_are_nonempty(self):
        for kind, files in TEMPLATES.items():
            self.assertTrue(files)
            self.assertTrue(all(content.strip() for content in files.values()))


if __name__ == "__main__":
    unittest.main()
