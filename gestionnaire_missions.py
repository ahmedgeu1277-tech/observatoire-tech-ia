"""File de missions persistante, locale et bornée pour l'orchestrateur IA.

La file conserve uniquement les missions et rapports dans .laboratoire_prive/.
Elle ne lance aucune commande arbitraire et n'effectue aucune action externe.
Un seul worker doit exécuter la file à la fois.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import orchestrateur

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / ".laboratoire_prive" / "queue" / "missions.sqlite3"
MAX_PENDING = 50
MAX_ATTEMPTS = 3


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class MissionQueue:
    def __init__(self, database: Path | str = DEFAULT_DB):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            os.chmod(self.database.parent, 0o700)
        with self._session() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('pending','running','completed','partial','failed','cancelled','interrupted')),
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    result TEXT,
                    error_type TEXT,
                    priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high','critical')),
                    due_at TEXT
                )
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(missions)")}
            if "cancel_requested_at" not in columns:
                db.execute("ALTER TABLE missions ADD COLUMN cancel_requested_at TEXT")
            if "priority" not in columns:
                db.execute("ALTER TABLE missions ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'")
            if "due_at" not in columns:
                db.execute("ALTER TABLE missions ADD COLUMN due_at TEXT")
            if "attempts" not in columns:
                db.execute("ALTER TABLE missions ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")
            db.execute("CREATE INDEX IF NOT EXISTS idx_missions_status_created ON missions(status, created_at)")
        self._secure_database_file()

    def _secure_database_file(self):
        if os.name != "nt" and self.database.exists():
            os.chmod(self.database, 0o600)

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        self._secure_database_file()
        return db

    @contextmanager
    def _session(self):
        db = self._connect()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, payload: object) -> str:
        mission = orchestrateur.valider_mission(payload)
        with self._session() as db:
            # Verrouille l'écriture avant le comptage pour éviter que deux
            # workers ajoutent simultanément au-delà de la limite de la file.
            db.execute("BEGIN IMMEDIATE")
            pending = db.execute(
                "SELECT COUNT(*) FROM missions WHERE status='pending'"
            ).fetchone()[0]
            if pending >= MAX_PENDING:
                raise ValueError("File pleine : 50 missions en attente maximum.")
            mission_id = uuid4().hex
            db.execute(
                "INSERT INTO missions(id,payload,status,created_at,priority,due_at) VALUES(?,?,?,?,?,?)",
                (mission_id, json.dumps(mission, ensure_ascii=False), "pending", now(),
                 mission["priority"], mission["due_at"]),
            )
        return mission_id

    def list_missions(self, limit: int = 50) -> list[dict]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("La limite doit être comprise entre 1 et 100.")
        with self._session() as db:
            rows = db.execute(
                "SELECT id,status,created_at,started_at,finished_at,error_type,priority,due_at,attempts "
                "FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_mission(self, mission_id: str) -> dict | None:
        """Retourne le détail d'une mission locale, sans exposer d'autres missions."""
        if not isinstance(mission_id, str) or not mission_id or len(mission_id) > 64:
            raise ValueError("Identifiant de mission invalide.")
        with self._session() as db:
            row = db.execute(
                "SELECT id,payload,status,created_at,started_at,finished_at,result,error_type,priority,due_at,attempts "
                "FROM missions WHERE id=?",
                (mission_id,),
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        try:
            item["payload"] = json.loads(item["payload"])
            item["result"] = json.loads(item["result"]) if item["result"] else None
        except (TypeError, json.JSONDecodeError):
            item["payload"] = None
            item["result"] = None
            item["error_type"] = "StoredDataError"
        return item

    def retry(self, mission_id: str) -> bool:
        """Remet explicitement en file une mission échouée, partielle ou interrompue.

        Trois tentatives au total sont autorisées ; aucune relance n'est automatique.
        """
        if not isinstance(mission_id, str) or not mission_id or len(mission_id) > 64:
            raise ValueError("Identifiant de mission invalide.")
        with self._session() as db:
            result = db.execute(
                "UPDATE missions SET status='pending',started_at=NULL,finished_at=NULL,"
                "result=NULL,error_type=NULL,cancel_requested_at=NULL "
                "WHERE id=? AND status IN ('failed','partial','interrupted') AND attempts < ?",
                (mission_id, MAX_ATTEMPTS),
            )
            return result.rowcount == 1

    def cancel(self, mission_id: str) -> bool:
        """Annule une mission en attente ou signale l'arrêt coopératif d'une mission active."""
        with self._session() as db:
            pending = db.execute(
                "UPDATE missions SET status='cancelled', finished_at=? "
                "WHERE id=? AND status='pending'",
                (now(), mission_id),
            )
            if pending.rowcount == 1:
                return True
            active = db.execute(
                "UPDATE missions SET cancel_requested_at=? "
                "WHERE id=? AND status='running' AND cancel_requested_at IS NULL",
                (now(), mission_id),
            )
            return active.rowcount == 1

    def _is_cancelled(self, mission_id: str) -> bool:
        with self._session() as db:
            row = db.execute(
                "SELECT status,cancel_requested_at FROM missions WHERE id=?", (mission_id,)
            ).fetchone()
        return row is None or row["status"] != "running" or row["cancel_requested_at"] is not None

    def run_next(self, should_stop=None) -> dict | None:
        """Récupère les missions expirées, puis réserve atomiquement la suivante."""
        if should_stop is not None and should_stop():
            return None
        self.recover_interrupted()
        with self._session() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute(
                "SELECT id FROM missions WHERE status='running' LIMIT 1"
            ).fetchone()
            if active:
                raise RuntimeError("Une mission est déjà marquée en cours ; un seul worker est autorisé.")
            row = db.execute(
                "SELECT id,payload FROM missions WHERE status='pending' "
                "ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
                "WHEN 'normal' THEN 2 ELSE 3 END, "
                "CASE WHEN due_at IS NULL THEN 1 ELSE 0 END, due_at, created_at, id LIMIT 1"
            ).fetchone()
            if row is None:
                db.commit()
                return None
            db.execute(
                "UPDATE missions SET status='running',started_at=?,attempts=attempts+1 WHERE id=? AND status='pending'",
                (now(), row["id"]),
            )
            db.commit()

        try:
            payload = json.loads(row["payload"])
            result = orchestrateur.executer_mission(
                payload,
                should_cancel=lambda: (
                    self._is_cancelled(row["id"])
                    or (should_stop is not None and should_stop())
                ),
            )
            status = result.get("status")
            if status not in {"completed", "partial", "cancelled"}:
                status = "partial"
            with self._session() as db:
                db.execute(
                    "UPDATE missions SET status=CASE WHEN cancel_requested_at IS NOT NULL THEN 'cancelled' ELSE ? END,"
                    "finished_at=?,result=? WHERE id=? AND status='running'",
                    (status, now(), json.dumps(result, ensure_ascii=False), row["id"]),
                )
                current = db.execute("SELECT status FROM missions WHERE id=?", (row["id"],)).fetchone()
            if current and current["status"] == "cancelled":
                status = "cancelled"
            return {"id": row["id"], "status": status, "result": result}
        except Exception as exc:  # noqa: BLE001 - journalise uniquement le type, jamais le contenu sensible
            with self._session() as db:
                db.execute(
                    "UPDATE missions SET status=CASE WHEN cancel_requested_at IS NOT NULL THEN 'cancelled' ELSE 'failed' END,"
                    "finished_at=?,error_type=? WHERE id=? AND status='running'",
                    (now(), type(exc).__name__, row["id"]),
                )
                current = db.execute("SELECT status FROM missions WHERE id=?", (row["id"],)).fetchone()
            if current and current["status"] == "cancelled":
                return {"id": row["id"], "status": "cancelled"}
            return {"id": row["id"], "status": "failed", "error_type": type(exc).__name__}

    def run_worker(
        self,
        max_runtime_seconds: int = 3600,
        max_missions: int = MAX_PENDING,
        idle_timeout_seconds: int = 300,
        should_stop=None,
    ) -> list[dict]:
        """Traite une file bornée, avec arrêt coopératif à la fin d'un agent."""
        if (
            isinstance(max_runtime_seconds, bool)
            or not isinstance(max_runtime_seconds, int)
            or not 60 <= max_runtime_seconds <= 172800
        ):
            raise ValueError("La durée du worker doit être comprise entre 60 secondes et 48 heures.")
        if (
            isinstance(max_missions, bool)
            or not isinstance(max_missions, int)
            or not 1 <= max_missions <= MAX_PENDING
        ):
            raise ValueError(f"Le worker peut traiter entre 1 et {MAX_PENDING} missions par lancement.")
        if (
            isinstance(idle_timeout_seconds, bool)
            or not isinstance(idle_timeout_seconds, int)
            or not 1 <= idle_timeout_seconds <= 3600
        ):
            raise ValueError("Le délai d'inactivité doit être compris entre 1 seconde et 1 heure.")
        deadline = time.monotonic() + max_runtime_seconds
        idle_since = None
        results = []
        while len(results) < max_missions:
            def stop_requested():
                return (
                    time.monotonic() >= deadline
                    or (should_stop is not None and should_stop())
                )

            if stop_requested():
                break
            result = self.run_next(should_stop=stop_requested)
            if result is None:
                if stop_requested():
                    break
                if idle_since is None:
                    idle_since = time.monotonic()
                idle_remaining = idle_timeout_seconds - (time.monotonic() - idle_since)
                if idle_remaining <= 0:
                    break
                time.sleep(min(5, idle_remaining, max(0, deadline - time.monotonic())))
                continue
            idle_since = None
            results.append(result)
        return results

    def recover_interrupted(self, stale_after_seconds: int = 300) -> int:
        """Classe uniquement les missions dont le délai de travail est expiré.

        La durée maximale d'une mission étant de 180 secondes, cinq minutes
        laissent une marge aux ralentissements sans interrompre un worker actif.
        """
        if (
            isinstance(stale_after_seconds, bool)
            or not isinstance(stale_after_seconds, int)
            or stale_after_seconds < 180
        ):
            raise ValueError("Le délai de récupération doit être d'au moins 180 secondes.")
        cutoff = (datetime.now(UTC) - timedelta(seconds=stale_after_seconds)).isoformat(timespec="seconds")
        with self._session() as db:
            result = db.execute(
                "UPDATE missions SET status='interrupted',finished_at=? "
                "WHERE status='running' AND started_at IS NOT NULL AND started_at < ?",
                (now(), cutoff),
            )
            return result.rowcount


def main() -> int:
    parser = argparse.ArgumentParser(description="File locale de missions IA bornées.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Lister les missions.")
    show = sub.add_parser("show", help="Afficher le détail d'une mission.")
    show.add_argument("mission_id")
    add = sub.add_parser("add", help="Ajouter une mission depuis un fichier JSON.")
    add.add_argument("json_file")
    sub.add_parser("run-next", help="Exécuter une mission en attente.")
    sub.add_parser("recover", help="Classer les missions restées actives après un arrêt brutal.")
    worker = sub.add_parser("worker", help="Traiter une file de missions avec des limites strictes.")
    worker.add_argument("--max-runtime-seconds", type=int, default=3600)
    worker.add_argument("--max-missions", type=int, default=MAX_PENDING)
    worker.add_argument("--idle-timeout-seconds", type=int, default=300)
    cancel = sub.add_parser("cancel", help="Annuler une mission en attente.")
    cancel.add_argument("mission_id")
    args = parser.parse_args()
    queue = MissionQueue()

    if args.command == "list":
        print(json.dumps(queue.list_missions(), ensure_ascii=False, indent=2))
    elif args.command == "show":
        item = queue.get_mission(args.mission_id)
        if item is None:
            print("Mission introuvable.")
            return 1
        print(json.dumps(item, ensure_ascii=False, indent=2))
    elif args.command == "add":
        payload = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        print(queue.enqueue(payload))
    elif args.command == "run-next":
        print(json.dumps(queue.run_next(), ensure_ascii=False, indent=2))
    elif args.command == "cancel":
        print("annulée" if queue.cancel(args.mission_id) else "introuvable ou déjà démarrée")
    elif args.command == "recover":
        print(f"{queue.recover_interrupted()} mission(s) classée(s) comme interrompue(s).")
    elif args.command == "worker":
        stop_event = threading.Event()
        previous_handlers = {}

        def request_stop(_signum, _frame):
            stop_event.set()

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, request_stop)
        try:
            results = queue.run_worker(
                max_runtime_seconds=args.max_runtime_seconds,
                max_missions=args.max_missions,
                idle_timeout_seconds=args.idle_timeout_seconds,
                should_stop=stop_event.is_set,
            )
        finally:
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)
        summary = {
            "processed": len(results),
            "statuses": {
                status: sum(item.get("status") == status for item in results)
                for status in ("completed", "partial", "failed", "cancelled")
            },
            "mission_ids": [item["id"] for item in results],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
