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
                "godot-2d": "project.godot", "godot-3d": "project.godot",
            }.items():
                with self.subTest(kind=kind):
                    result = generate_project(f"Projet-{kind}", folder, kind)
                    self.assertTrue((Path(result["directory"]) / expected).is_file())
                    self.assertFalse(result["code_executed"])
                    self.assertFalse(result["published"])

    def test_godot_templates_include_scene_and_game_script(self):
        with tempfile.TemporaryDirectory() as folder:
            for kind, node_type in (("godot-2d", "Node2D"), ("godot-3d", "Node3D")):
                with self.subTest(kind=kind):
                    result = generate_project(f"Projet-{kind}", folder, kind)
                    root = Path(result["directory"])
                    self.assertTrue((root / "project.godot").is_file())
                    self.assertTrue((root / "scenes" / "main.tscn").is_file())
                    script = (root / "scripts" / "main.gd").read_text(encoding="utf-8")
                    self.assertIn(f"extends {node_type}", script)
                    self.assertFalse(result["code_executed"])

    def test_rejects_traversal_and_bad_names(self):
        for name in ("../escape", "1invalid", "", "x" * 51, "a" + chr(92) + "b"):
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
