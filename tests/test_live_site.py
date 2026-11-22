import unittest

from scripts.check_live_site import safe_article_audio_path


class SafeArticleAudioPathTests(unittest.TestCase):
    def test_accepts_simple_audio_filenames(self):
        self.assertEqual(
            safe_article_audio_path("audio/article-en.mp3"),
            "site/audio/article-en.mp3",
        )

    def test_rejects_external_or_traversal_paths(self):
        for value in (
            "https://evil.example/audio.mp3",
            "audio/../secret.mp3",
            "audio/subfolder/file.mp3",
            r"audio\\..\\secret.mp3",
            "audio/file.mp3?download=1",
            "site/audio/file.mp3",
        ):
            with self.subTest(value=value):
                self.assertIsNone(safe_article_audio_path(value))

    def test_rejects_non_string_values(self):
        for value in (None, 0, [], {}):
            with self.subTest(value=value):
                self.assertIsNone(safe_article_audio_path(value))


if __name__ == "__main__":
    unittest.main()


class PublicChallengeRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pathlib import Path

        cls.html = (Path(__file__).resolve().parents[1] / "site" / "index.html").read_text(
            encoding="utf-8"
        )

    def test_six_challenges_have_unique_buttons_and_content_ids(self):
        self.assertEqual(self.html.count('data-challenge-index="'), 6)
        for index in range(6):
            self.assertIn(f'data-challenge-index="{index}"', self.html)
            self.assertIn(f'id="challenge-task-{index}"', self.html)
            self.assertIn(f'id="challenge-desc-{index}"', self.html)

    def test_challenge_points_total_one_hundred(self):
        start = self.html.index("const challengePoints=[") + len("const challengePoints=[")
        end = self.html.index("];", start)
        points = [int(value.strip()) for value in self.html[start:end].split(",")]
        self.assertEqual(len(points), 6)
        self.assertEqual(sum(points), 100)

    def test_all_seven_languages_define_six_challenge_tasks(self):
        start = self.html.index("const challengeUi={") + len("const challengeUi={")
        end = self.html.index("\\n};", start)
        block = self.html[start:end]
        for language in ("fr", "en", "es", "de", "pt", "ar", "zh"):
            self.assertIn(f"{language}:{{", block)
        self.assertEqual(block.count("tasks:["), 7)
        self.assertEqual(block.count("extraTasks:["), 7)

    def test_progress_is_local_and_reset_clears_all_six(self):
        self.assertIn('localStorage.setItem("nexora-challenges-v1"', self.html)
        self.assertIn("challengeState=Array(6).fill(false)", self.html)
        self.assertIn("ce n'est pas un classement mondial", self.html)
