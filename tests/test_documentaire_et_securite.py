import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import agent_gardien
import nettoyer_documentaire_test as cleanup


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.site = self.root / "site"
        self.audio = self.site / "audio"
        self.video = self.site / "video"
        self.archive = self.site / "archives"
        for folder in (self.site, self.audio, self.video, self.archive):
            folder.mkdir(parents=True, exist_ok=True)
        self.manifest = self.site / "documentaire-test.json"
        self.page = self.site / "documentaire-test.html"
        self.script = self.site / "documentaire-test.md"
        self.page.write_text("documentaire", encoding="utf-8")
        self.script.write_text("script", encoding="utf-8")
        self.manifest.write_text(json.dumps({
            "expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat()
        }), encoding="utf-8")
        self.patches = patch.multiple(cleanup, MANIFEST=self.manifest, PAGE=self.page,
            SCRIPT=self.script, AUDIO_DIR=self.audio, VIDEO_DIR=self.video,
            ARCHIVE_DIR=self.archive)

    def tearDown(self):
        self.temp.cleanup()

    def test_recent_audio_video_and_written_archive_are_kept(self):
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        audio = self.audio / f"documentaire-test-{stamp}.mp3"
        video = self.video / f"documentaire-test-{stamp}.mp4"
        archive = self.archive / f"documentaire-test-{stamp}.md"
        for path in (audio, video, archive):
            path.write_text("recent", encoding="utf-8")
        with self.patches:
            cleanup.main()
        self.assertTrue(audio.exists())
        self.assertTrue(video.exists())
        self.assertTrue(archive.exists())
        self.assertTrue(self.page.exists())

    def test_only_archives_older_than_30_days_are_removed(self):
        old_stamp = (datetime.now(UTC) - timedelta(days=31)).strftime("%Y%m%dT%H%M%SZ")
        recent_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        old_video = self.video / f"documentaire-test-{old_stamp}.mp4"
        recent_video = self.video / f"documentaire-test-{recent_stamp}.mp4"
        old_video.write_text("old", encoding="utf-8")
        recent_video.write_text("recent", encoding="utf-8")
        with self.patches:
            cleanup.main()
        self.assertFalse(old_video.exists())
        self.assertTrue(recent_video.exists())
        self.assertTrue(self.manifest.exists())

    def test_expired_current_page_is_replaced_but_recent_media_remains(self):
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        audio = self.audio / f"documentaire-test-{stamp}.mp3"
        video = self.video / f"documentaire-test-{stamp}.mp4"
        audio.write_text("audio", encoding="utf-8")
        video.write_text("video", encoding="utf-8")
        self.manifest.write_text(json.dumps({
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
        }), encoding="utf-8")
        with self.patches:
            cleanup.main()
        self.assertTrue(audio.exists())
        self.assertTrue(video.exists())
        self.assertFalse(self.script.exists())
        self.assertFalse(self.manifest.exists())
        self.assertIn("archives de moins de 30 jours", self.page.read_text(encoding="utf-8"))

    def test_invalid_manifest_fails_closed(self):
        self.manifest.write_text("{invalid", encoding="utf-8")
        with self.patches, self.assertRaises(RuntimeError):
            cleanup.main()


class GuardTests(unittest.TestCase):
    def test_blocks_common_api_token(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "guard.log"
            with patch.object(agent_gardien, "LOG_FILE", log):
                self.assertFalse(agent_gardien.verifier_conformite_legale(
                    "token gsk_abcdefghijklmnopqrstuvwxyz123456", "TEST"
                ))
            self.assertTrue(log.exists())

    def test_blocks_email_address(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "guard.log"
            with patch.object(agent_gardien, "LOG_FILE", log):
                self.assertFalse(agent_gardien.verifier_conformite_legale(
                    "Contact: private@example.com", "TEST"
                ))

    def test_accepts_plain_safe_text(self):
        self.assertTrue(agent_gardien.verifier_conformite_legale(
            "Résumé public : cette mise à jour ajoute un mode de jeu.", "TEST"
        ))

    def test_blocks_bearer_token(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "guard.log"
            with patch.object(agent_gardien, "LOG_FILE", log):
                self.assertFalse(agent_gardien.verifier_conformite_legale(
                    "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890", "TEST"
                ))

    def test_blocks_secret_assignment(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "guard.log"
            with patch.object(agent_gardien, "LOG_FILE", log):
                self.assertFalse(agent_gardien.verifier_conformite_legale(
                    "api_key=abcdefghijklmnopqrstuvwxyz123456", "TEST"
                ))


if __name__ == "__main__":
    unittest.main()
