import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gestionnaire_missions import MissionQueue


class MissionQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = MissionQueue(Path(self.temp.name) / "queue.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def payload(self):
        return {
            "mission": "Évaluer la qualité du prototype.",
            "agents": ["chercheur"],
            "max_duration_seconds": 60,
        }

    def test_enqueue_and_list(self):
        mission_id = self.queue.enqueue(self.payload())
        items = self.queue.list_missions()
        self.assertEqual(items[0]["id"], mission_id)
        self.assertEqual(items[0]["status"], "pending")

    def test_rejects_invalid_mission(self):
        with self.assertRaises(ValueError):
            self.queue.enqueue({"mission": "", "agents": ["inconnu"]})

    def test_cancel_only_pending(self):
        mission_id = self.queue.enqueue(self.payload())
        self.assertTrue(self.queue.cancel(mission_id))
        self.assertFalse(self.queue.cancel(mission_id))
        self.assertEqual(self.queue.list_missions()[0]["status"], "cancelled")

    @patch("gestionnaire_missions.orchestrateur.executer_mission")
    def test_active_mission_can_be_cancelled_cooperatively(self, execute):
        mission_id = self.queue.enqueue({
            "mission": "Évaluer l'arrêt coopératif.",
            "agents": ["chercheur", "critique"],
            "max_duration_seconds": 120,
        })
        def cancel_during_agent(payload, should_cancel):
            self.assertFalse(should_cancel())
            self.assertTrue(self.queue.cancel(mission_id))
            self.assertTrue(should_cancel())
            self.assertEqual(self.queue.list_missions()[0]["status"], "running")
            return {"status": "cancelled", "results": []}
        execute.side_effect = cancel_during_agent
        result = self.queue.run_next()
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(self.queue.list_missions()[0]["status"], "cancelled")

    @patch("gestionnaire_missions.orchestrateur.executer_mission")
    def test_run_next_persists_result(self, execute):
        execute.return_value = {"status": "completed", "results": [{"agent": "chercheur"}]}
        mission_id = self.queue.enqueue(self.payload())
        result = self.queue.run_next()
        self.assertEqual(result["id"], mission_id)
        self.assertEqual(result["status"], "completed")
        item = self.queue.list_missions()[0]
        self.assertEqual(item["status"], "completed")
        with self.queue._connect() as db:
            saved = db.execute("SELECT result FROM missions WHERE id=?", (mission_id,)).fetchone()
        self.assertEqual(json.loads(saved["result"])["status"], "completed")

    @patch("gestionnaire_missions.orchestrateur.executer_mission")
    def test_worker_failure_does_not_store_exception_message(self, execute):
        execute.side_effect = RuntimeError("sensitive provider detail")
        self.queue.enqueue(self.payload())
        result = self.queue.run_next()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertNotIn("sensitive provider detail", json.dumps(self.queue.list_missions()))


    def test_recover_interrupted_marks_stale_running_missions(self):
        mission_id = self.queue.enqueue(self.payload())
        with self.queue._connect() as db:
            db.execute(
                "UPDATE missions SET status='running',started_at=? WHERE id=?",
                ("2000-01-01T00:00:00+00:00", mission_id),
            )
        self.assertEqual(self.queue.recover_interrupted(), 1)
        self.assertEqual(self.queue.list_missions()[0]["status"], "interrupted")

    def test_recovery_does_not_interrupt_recent_running_mission(self):
        mission_id = self.queue.enqueue(self.payload())
        with self.queue._connect() as db:
            db.execute(
                "UPDATE missions SET status='running',started_at=? WHERE id=?",
                ("2099-01-01T00:00:00+00:00", mission_id),
            )
        self.assertEqual(self.queue.recover_interrupted(), 0)
        self.assertEqual(self.queue.list_missions()[0]["status"], "running")

    def test_recovery_rejects_too_short_timeout(self):
        with self.assertRaises(ValueError):
            self.queue.recover_interrupted(30)

    @patch("gestionnaire_missions.orchestrateur.executer_mission")
    def test_run_next_recovers_stale_mission_automatically(self, execute):
        stale_id = self.queue.enqueue(self.payload())
        next_id = self.queue.enqueue(self.payload())
        with self.queue._connect() as db:
            db.execute(
                "UPDATE missions SET status='running',started_at=? WHERE id=?",
                ("2000-01-01T00:00:00+00:00", stale_id),
            )
        execute.return_value = {"status": "completed", "results": []}
        result = self.queue.run_next()
        statuses = {item["id"]: item["status"] for item in self.queue.list_missions()}
        self.assertEqual(statuses[stale_id], "interrupted")
        self.assertEqual(result["id"], next_id)
        self.assertEqual(statuses[next_id], "completed")

    def test_existing_database_is_migrated_with_cancel_request_column(self):
        database = Path(self.temp.name) / "old.sqlite3"
        with sqlite3.connect(database) as db:
            db.execute("""
                CREATE TABLE missions (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('pending','running','completed','partial','failed','cancelled','interrupted')),
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    result TEXT,
                    error_type TEXT
                )
            """)
        migrated = MissionQueue(database)
        with migrated._connect() as db:
            columns = {row["name"] for row in db.execute("PRAGMA table_info(missions)")}
        self.assertIn("cancel_requested_at", columns)

    @patch("gestionnaire_missions.orchestrateur.executer_mission")
    def test_cancel_request_keeps_worker_lock_until_worker_finishes(self, execute):
        first = self.queue.enqueue({
            "mission": "Mission active à annuler",
            "agents": ["chercheur"],
            "max_duration_seconds": 60,
        })
        second = self.queue.enqueue(self.payload())
        with self.queue._connect() as db:
            db.execute(
                "UPDATE missions SET created_at=? WHERE id=?",
                ("2000-01-01T00:00:00+00:00", first),
            )
        def cancel_and_check_lock(payload, should_cancel):
            self.assertTrue(self.queue.cancel(first))
            self.assertTrue(should_cancel())
            with self.assertRaises(RuntimeError):
                self.queue.run_next()
            return {"status": "cancelled", "results": []}
        execute.side_effect = cancel_and_check_lock
        result = self.queue.run_next()
        self.assertEqual(result["status"], "cancelled")
        statuses = {item["id"]: item["status"] for item in self.queue.list_missions()}
        self.assertEqual(statuses[first], "cancelled")
        self.assertEqual(statuses[second], "pending")

    def test_no_work_returns_none(self):
        self.assertIsNone(self.queue.run_next())


if __name__ == "__main__":
    unittest.main()
