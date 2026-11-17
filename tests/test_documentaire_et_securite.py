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
        self.site.mkdir()
        self.audio.mkdir()
        self.manifest = self.site / "documentaire-test.json"
        self.page = self.site / "documentaire-test.html"
        self.script = self.site / "documentaire-test.md"
        self.audio_file = self.audio / "documentaire-test-example.mp3"
        self.audio_file.write_bytes(b"audio-test")
        self.script.write_text("script", encoding="utf-8")
        self.page.write_text("documentaire", encoding="utf-8")
        self.manifest.write_text(json.dumps({
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "audio_file": self.audio_file.name
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_expired_documentary_is_removed_and_page_replaced(self):
        with patch.multiple(cleanup, MANIFEST=self.manifest, PAGE=self.page,
                            SCRIPT=self.script, AUDIO_DIR=self.audio):
            cleanup.main()
        self.assertFalse(self.audio_file.exists())
        self.assertFalse(self.script.exists())
        self.assertFalse(self.manifest.exists())
        self.assertIn("période de test est terminée", self.page.read_text(encoding="utf-8"))

    def test_unexpired_documentary_is_kept(self):
        self.manifest.write_text(json.dumps({
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "audio_file": self.audio_file.name
        }), encoding="utf-8")
        with patch.multiple(cleanup, MANIFEST=self.manifest, PAGE=self.page,
                            SCRIPT=self.script, AUDIO_DIR=self.audio):
            cleanup.main()
        self.assertTrue(self.audio_file.exists())
        self.assertTrue(self.script.exists())
        self.assertTrue(self.manifest.exists())

    def test_invalid_audio_filename_cannot_escape_audio_folder(self):
        self.manifest.write_text(json.dumps({
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "audio_file": "../../important.txt"
        }), encoding="utf-8")
        with patch.multiple(cleanup, MANIFEST=self.manifest, PAGE=self.page,
                            SCRIPT=self.script, AUDIO_DIR=self.audio):
            cleanup.main()
        self.assertTrue(self.audio_file.exists())
        self.assertFalse(self.script.exists())

    def test_invalid_manifest_fails_closed(self):
        self.manifest.write_text("{invalid", encoding="utf-8")
        with (
            patch.multiple(cleanup, MANIFEST=self.manifest, PAGE=self.page,
                           SCRIPT=self.script, AUDIO_DIR=self.audio),
            self.assertRaises(RuntimeError),
        ):
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
