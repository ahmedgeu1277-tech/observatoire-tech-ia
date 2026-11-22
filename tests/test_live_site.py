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
        import re

        buttons = re.findall(r'data-challenge-index="(\\d+)"', self.html)
        self.assertEqual(buttons, [str(i) for i in range(6)])
        for index in range(6):
            self.assertIn(f'id="challenge-task-{index}"', self.html)
            self.assertIn(f'id="challenge-desc-{index}"', self.html)

    def test_challenge_points_total_one_hundred(self):
        import re

        match = re.search(r"const challengePoints=\\[([^]]+)\\]", self.html)
        self.assertIsNotNone(match, "La configuration des points est absente.")
        points = [int(value.strip()) for value in match.group(1).split(",")]
        self.assertEqual(len(points), 6)
        self.assertEqual(sum(points), 100)

    def test_all_seven_languages_define_six_challenge_tasks(self):
        import re

        match = re.search(r"const challengeUi=\\{(.*?)\\n\\};", self.html, re.DOTALL)
        self.assertIsNotNone(match, "Les traductions des défis sont absentes.")
        block = match.group(1)
        languages = re.findall(r"^([a-z]{2}):\\{", block, re.MULTILINE)
        self.assertEqual(set(languages), {"fr", "en", "es", "de", "pt", "ar", "zh"})
        for language in languages:
            section = re.search(
                rf"^{language}:\\{{(.*?)(?=^  [a-z]{{2}}:\\{{|\\Z)",
                block,
                re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(section)
            self.assertIn("tasks:", section.group(1))
            self.assertIn("extraTasks:", section.group(1))

    def test_progress_is_local_and_reset_clears_all_six(self):
        self.assertIn('localStorage.setItem("nexora-challenges-v1"', self.html)
        self.assertIn("challengeState=Array(6).fill(false)", self.html)
        self.assertIn("ce n'est pas un classement mondial", self.html)


