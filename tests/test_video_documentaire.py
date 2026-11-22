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


    def test_documentary_page_template_has_mobile_overflow_guards(self):
        source = Path(__file__).resolve().parents[1] / "templates" / "documentaire.html.tpl"
        template = source.read_text(encoding="utf-8")
        self.assertIn("*{box-sizing:border-box;min-width:0}", template)
        self.assertIn("overflow-x:hidden", template)
        self.assertIn("<video controls", template)

    def test_generated_documentary_template_supports_seven_ui_languages(self):
        source = Path(__file__).resolve().parents[1] / "templates" / "documentaire.html.tpl"
        template = source.read_text(encoding="utf-8")
        for language in ("fr", "en", "es", "de", "pt", "ar", "zh"):
            self.assertIn(language + ":", template)
        self.assertIn('id="language"', template)
        self.assertIn('class="sources-heading"', template)
        self.assertIn('localStorage.setItem("observatoire-doc-language"', template)
        self.assertIn('lang === "ar" ? "rtl" : "ltr"', template)

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
