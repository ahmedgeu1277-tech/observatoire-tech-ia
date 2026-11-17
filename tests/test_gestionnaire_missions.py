import json
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

    def test_no_work_returns_none(self):
        self.assertIsNone(self.queue.run_next())


if __name__ == "__main__":
    unittest.main()
