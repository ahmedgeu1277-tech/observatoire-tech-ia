"""File de missions persistante, locale et bornée pour l'orchestrateur IA.

La file conserve uniquement les missions et rapports dans .laboratoire_prive/.
Elle ne lance aucune commande arbitraire et n'effectue aucune action externe.
Un seul worker doit exécuter la file à la fois.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import orchestrateur

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / ".laboratoire_prive" / "queue" / "missions.sqlite3"
MAX_PENDING = 50


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class MissionQueue:
    def __init__(self, database: Path | str = DEFAULT_DB):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
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
                    error_type TEXT
                )
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(missions)")}
            if "cancel_requested_at" not in columns:
                db.execute("ALTER TABLE missions ADD COLUMN cancel_requested_at TEXT")
            db.execute("CREATE INDEX IF NOT EXISTS idx_missions_status_created ON missions(status, created_at)")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
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
                "INSERT INTO missions(id,payload,status,created_at) VALUES(?,?,?,?)",
                (mission_id, json.dumps(mission, ensure_ascii=False), "pending", now()),
            )
        return mission_id

    def list_missions(self, limit: int = 50) -> list[dict]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("La limite doit être comprise entre 1 et 100.")
        with self._session() as db:
            rows = db.execute(
                "SELECT id,status,created_at,started_at,finished_at,error_type "
                "FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

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

    def run_next(self) -> dict | None:
        """Récupère les missions expirées, puis réserve atomiquement la suivante."""
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
                "ORDER BY created_at,id LIMIT 1"
            ).fetchone()
            if row is None:
                db.commit()
                return None
            db.execute(
                "UPDATE missions SET status='running',started_at=? WHERE id=? AND status='pending'",
                (now(), row["id"]),
            )
            db.commit()

        try:
            payload = json.loads(row["payload"])
            result = orchestrateur.executer_mission(
                payload, should_cancel=lambda: self._is_cancelled(row["id"])
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
    add = sub.add_parser("add", help="Ajouter une mission depuis un fichier JSON.")
    add.add_argument("json_file")
    sub.add_parser("run-next", help="Exécuter une mission en attente.")
    sub.add_parser("recover", help="Classer les missions restées actives après un arrêt brutal.")
    cancel = sub.add_parser("cancel", help="Annuler une mission en attente.")
    cancel.add_argument("mission_id")
    args = parser.parse_args()
    queue = MissionQueue()

    if args.command == "list":
        print(json.dumps(queue.list_missions(), ensure_ascii=False, indent=2))
    elif args.command == "add":
        payload = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        print(queue.enqueue(payload))
    elif args.command == "run-next":
        print(json.dumps(queue.run_next(), ensure_ascii=False, indent=2))
    elif args.command == "cancel":
        print("annulée" if queue.cancel(args.mission_id) else "introuvable ou déjà démarrée")
    elif args.command == "recover":
        print(f"{queue.recover_interrupted()} mission(s) classée(s) comme interrompue(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
