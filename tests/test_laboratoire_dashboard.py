import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import atelier_produits
import roadmap_laboratoire
from atelier_produits import DIMENSIONS, evaluate_opportunity, save_opportunity
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

    def test_dashboard_generates_private_godot_project_without_running_code(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "laboratoire_dashboard.PROJECTS_DIR", Path(folder) / "prototypes"
        ):
            status, _, body = self.request(
                "/api/projects",
                method="POST",
                payload={"name": "DemoGodot", "template": "godot-3d"},
            )
            self.assertEqual(status, 201)
            result = json.loads(body)
            project = Path(result["directory"])
            self.assertEqual(result["template"], "godot-3d")
            self.assertFalse(result["code_executed"])
            self.assertFalse(result["published"])
            self.assertTrue((project / "project.godot").is_file())
            self.assertTrue((project / "scenes" / "main.tscn").is_file())
            self.assertTrue((project / "scripts" / "main.gd").is_file())

    def test_dashboard_project_generator_rejects_unknown_template(self):
        status, _, body = self.request(
            "/api/projects",
            method="POST",
            payload={"name": "DemoBad", "template": "unknown"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Modèle inconnu", json.loads(body)["error"])

    def test_dashboard_exposes_supported_project_templates(self):
        status, _, body = self.request("/api/templates")
        self.assertEqual(status, 200)
        templates = {item["id"] for item in json.loads(body)}
        self.assertTrue({"site", "webapp", "jeu-web", "godot-2d", "godot-3d", "logiciel-python", "video", "audio"}.issubset(templates))

    def test_loopback_only_page_and_security_headers(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        page = body.decode()
        self.assertIn("NEXORA · Laboratoire local", page)
        self.assertIn("Atelier de création de projets", page)
        for role in ("chercheur", "critique", "architecte", "redacteur", "auditeur", "planificateur"):
            self.assertIn('value="' + role + '"', page)
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

    def test_runs_a_bounded_batch_of_three_missions(self):
        ids = [
            self.queue.enqueue({
                "mission": "Mission locale " + str(index),
                "agents": ["chercheur"],
                "max_duration_seconds": 60,
            })
            for index in range(3)
        ]
        with patch(
            "gestionnaire_missions.orchestrateur.executer_mission",
            return_value={"status": "completed", "results": []},
        ):
            status, _, body = self.request(
                "/api/worker/run-batch",
                method="POST",
                payload={"max_items": 3},
            )
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["processed"], 3)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(all(self.queue.get_mission(item)["status"] == "completed" for item in ids))

    def test_batch_worker_rejects_more_than_three_missions(self):
        status, _, body = self.request(
            "/api/worker/run-batch",
            method="POST",
            payload={"max_items": 4},
        )
        self.assertEqual(status, 400)
        self.assertIn("entre 1 et 3", json.loads(body)["error"])

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

    def test_private_dashboard_lists_and_updates_product_opportunities(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            data = {
                "name": "Outil de test local",
                "problem": "Les créateurs manquent de temps pour tester.",
                "target_customer": "Créateurs indépendants",
                "proposed_solution": "Préparer des scénarios de test.",
                "product_type": "developer_tool",
                "evidence": [],
                "scores": {key: 3 for key in DIMENSIONS},
            }
            report = evaluate_opportunity(data)
            save_opportunity(report, directory)
            with patch.object(atelier_produits, "DEFAULT_PRODUCTS_DIR", directory):
                status, _, body = self.request("/api/opportunities")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)[0]["workflow_status"], "candidate")
                status, _, updated = self.request(
                    "/api/opportunities/" + report["id"] + "/status",
                    method="POST",
                    payload={"status": "research", "note": "Comparer deux solutions."},
                )
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(updated)["workflow_status"], "research")
                self.assertEqual(atelier_produits.list_opportunities(directory)[0]["workflow_status"], "research")

    def test_dashboard_lists_and_updates_private_roadmap(self):
        path = Path(self.temp.name) / ".laboratoire_prive" / "roadmap.json"
        with patch.object(roadmap_laboratoire, "DEFAULT_ROADMAP_PATH", path):
            status, _, body = self.request("/api/roadmap")
            self.assertEqual(status, 200)
            rows = json.loads(body)
            self.assertEqual(len(rows), 7)
            self.assertEqual(rows[0]["status"], "backlog")
            status, _, body = self.request(
                "/api/roadmap/translate_archive/status",
                method="POST",
                payload={"status": "in_progress", "due_at": "2026-12-01T12:00:00+00:00"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["status"], "in_progress")
            self.assertEqual(json.loads(body)["due_at"], "2026-12-01T12:00:00+00:00")
            self.assertEqual(roadmap_laboratoire.list_tasks(path)[0]["status"], "in_progress")

    def test_dashboard_can_manually_retry_failed_mission(self):
        mission_id = self.queue.enqueue({
            "mission": "Mission locale à relancer.",
            "agents": ["chercheur"],
            "max_duration_seconds": 60,
        })
        with patch("gestionnaire_missions.orchestrateur.executer_mission", side_effect=RuntimeError("provider failure")):
            self.queue.run_next()
        status, _, body = self.request(
            "/api/missions/" + mission_id + "/retry",
            method="POST",
            payload={},
        )
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["requeued"])
        self.assertEqual(self.queue.get_mission(mission_id)["status"], "pending")
        self.assertEqual(self.queue.get_mission(mission_id)["attempts"], 1)

    def test_private_dashboard_can_create_product_opportunity(self):
        with tempfile.TemporaryDirectory() as folder:
            data = {
                "name": "Assistant de veille de test",
                "problem": "Les créateurs ont du mal à suivre les changements.",
                "target_customer": "Créateurs indépendants",
                "proposed_solution": "Regrouper des sources vérifiables.",
                "product_type": "ai_agent",
                "evidence": ["Entretiens à réaliser"],
                "scores": {key: 3 for key in DIMENSIONS},
            }
            with patch.object(atelier_produits, "DEFAULT_PRODUCTS_DIR", Path(folder)):
                status, _, body = self.request("/api/opportunities", method="POST", payload=data)
                self.assertEqual(status, 201)
                result = json.loads(body)
                self.assertEqual(result["score_percent"], 60)
                self.assertEqual(len(atelier_produits.list_opportunities(Path(folder))), 1)

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
