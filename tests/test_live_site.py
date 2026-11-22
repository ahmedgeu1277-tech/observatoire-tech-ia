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
