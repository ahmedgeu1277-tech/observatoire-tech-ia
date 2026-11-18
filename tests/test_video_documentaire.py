import tempfile
import unittest
from pathlib import Path

from PIL import Image

from video_documentaire import creer_diapositive, generer_video


class VideoDocumentaireTests(unittest.TestCase):
    def test_creates_original_16_9_slide(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "slide.png"
            result = creer_diapositive(
                "Dossier 1", "Un titre de démonstration",
                "Un résumé clair avec des informations à vérifier.", output
            )
            self.assertTrue(result.is_file())
            with Image.open(result) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertEqual(image.format, "PNG")

    def test_rejects_missing_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                generer_video(Path(folder) / "absent.mp3", [("Intro", "Titre", "Texte")],
                              Path(folder) / "resultat.mp4")

    def test_rejects_empty_slides(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "audio.mp3"
            audio.write_bytes(b"x" * 1500)
            with self.assertRaises(ValueError):
                generer_video(audio, [], Path(folder) / "resultat.mp4")


if __name__ == "__main__":
    unittest.main()
