import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gestionnaire_missions import MissionQueue
from laboratoire_dashboard import create_server


class LocalDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = MissionQueue(Path(self.temp.name) / "missions.sqlite3")
        self.token = "test-token-local-only"
        self.server = create_server(0, queue=self.queue, token=self.token)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, path, method="GET", payload=None, token=True, origin=True):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + self.token
        if origin:
            headers["Origin"] = self.base
        data = json.dumps(payload).encode() if payload is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def test_loopback_only_page_and_security_headers(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        page = body.decode()
        self.assertIn("NEXORA · Laboratoire local", page)
        self.assertNotIn("https://", page)

    def test_api_requires_bearer_token(self):
        status, _, body = self.request("/api/missions", token=False)
        self.assertEqual(status, 401)
        self.assertIn("Authentification", body.decode())

    def test_create_and_read_validated_mission(self):
        payload = {"mission": "Examiner un prototype.", "agents": ["chercheur"],
                   "max_duration_seconds": 60, "priority": "high",
                   "due_at": "2026-12-01T18:30:00+01:00"}
        status, _, body = self.request("/api/missions", method="POST", payload=payload)
        self.assertEqual(status, 201)
        mission_id = json.loads(body)["id"]
        status, _, detail = self.request("/api/missions/" + mission_id)
        self.assertEqual(status, 200)
        item = json.loads(detail)
        self.assertEqual(item["priority"], "high")
        self.assertEqual(item["payload"]["mission"], payload["mission"])

    def test_runs_one_bounded_mission_from_the_dashboard(self):
        mission_id = self.queue.enqueue({
            "mission": "Tester une mission locale.",
            "agents": ["chercheur"],
            "max_duration_seconds": 60,
        })
        from unittest.mock import patch
        with patch("gestionnaire_missions.orchestrateur.executer_mission",
                   return_value={"status": "completed", "results": []}):
            status, _, body = self.request("/api/worker/run-next", method="POST", payload={})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "completed")
        self.assertEqual(self.queue.get_mission(mission_id)["status"], "completed")

    def test_rejects_cross_origin_post(self):
        payload = {"mission": "Test", "agents": ["chercheur"], "max_duration_seconds": 60}
        req = Request(self.base + "/api/missions", data=json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + self.token,
                               "Origin": "http://evil.example", "Content-Type": "application/json"},
                      method="POST")
        with self.assertRaises(HTTPError) as caught:
            urlopen(req, timeout=3)
        self.assertEqual(caught.exception.code, 403)

    def test_invalid_mission_is_not_stored(self):
        status, _, _ = self.request("/api/missions", method="POST",
                                    payload={"mission": "", "agents": ["chercheur"],
                                             "max_duration_seconds": 60})
        self.assertEqual(status, 400)
        self.assertEqual(self.queue.list_missions(), [])


if __name__ == "__main__":
    unittest.main()
