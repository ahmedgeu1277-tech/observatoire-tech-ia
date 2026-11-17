"""File de missions persistante, locale et bornée pour l'orchestrateur IA.

La file conserve uniquement les missions et rapports dans .laboratoire_prive/.
Elle ne lance aucune commande arbitraire et n'effectue aucune action externe.
Un seul worker doit exécuter la file à la fois.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
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
        with self._connect() as db:
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
            db.execute("CREATE INDEX IF NOT EXISTS idx_missions_status_created ON missions(status, created_at)")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, payload: object) -> str:
        mission = orchestrateur.valider_mission(payload)
        with self._connect() as db:
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
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,status,created_at,started_at,finished_at,error_type "
                "FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def cancel(self, mission_id: str) -> bool:
        """Annule uniquement une mission en attente ; une mission active n'est pas interrompue."""
        with self._connect() as db:
            result = db.execute(
                "UPDATE missions SET status='cancelled', finished_at=? "
                "WHERE id=? AND status='pending'",
                (now(), mission_id),
            )
            return result.rowcount == 1

    def run_next(self) -> dict | None:
        """Réserve atomiquement la prochaine mission puis l'exécute avec les limites de l'orchestrateur."""
        with self._connect() as db:
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
            result = orchestrateur.executer_mission(payload)
            status = result.get("status")
            if status not in {"completed", "partial"}:
                status = "partial"
            with self._connect() as db:
                db.execute(
                    "UPDATE missions SET status=?,finished_at=?,result=? WHERE id=? AND status='running'",
                    (status, now(), json.dumps(result, ensure_ascii=False), row["id"]),
                )
            return {"id": row["id"], "status": status, "result": result}
        except Exception as exc:  # noqa: BLE001 - journalise uniquement le type, jamais le contenu sensible
            with self._connect() as db:
                db.execute(
                    "UPDATE missions SET status='failed',finished_at=?,error_type=? "
                    "WHERE id=? AND status='running'",
                    (now(), type(exc).__name__, row["id"]),
                )
            return {"id": row["id"], "status": "failed", "error_type": type(exc).__name__}

    def recover_interrupted(self) -> int:
        """À lancer au redémarrage du worker pour classer les missions restées actives après un crash."""
        with self._connect() as db:
            result = db.execute(
                "UPDATE missions SET status='interrupted',finished_at=? WHERE status='running'",
                (now(),),
            )
            return result.rowcount


def main() -> int:
    parser = argparse.ArgumentParser(description="File locale de missions IA bornées.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Lister les missions.")
    add = sub.add_parser("add", help="Ajouter une mission depuis un fichier JSON.")
    add.add_argument("json_file")
    sub.add_parser("run-next", help="Exécuter une mission en attente.")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
