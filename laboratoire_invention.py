"""Registre sûr pour les idées et prototypes du laboratoire d'invention.

Ce module ne génère ni n'exécute du code arbitraire. Il conserve des fiches
de recherche dans un dossier utilisateur privé, hors du dépôt Git.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

DEFAULT_DATA_DIR = Path.home() / ".observatoire_tech_gaming" / "laboratoire"
DATA_FILE = Path(os.environ.get("LABORATOIRE_DATA_DIR", str(DEFAULT_DATA_DIR))) / "idees.json"
STATUSES = {"idee", "documentee", "prototype", "testee", "candidate_produit", "abandonnee"}
FIELDS = ("problem", "proposal", "domain")


def _load(path: Path = DATA_FILE) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Registre illisible : aucune donnée ne sera écrasée.") from exc
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise RuntimeError("Format du registre invalide : aucune donnée ne sera écrasée.")
    return data


def _save(items: list[dict], path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def create_idea(problem: str, proposal: str, domain: str, path: Path = DATA_FILE) -> dict:
    values = {"problem": problem.strip(), "proposal": proposal.strip(), "domain": domain.strip()}
    if any(not value for value in values.values()):
        raise ValueError("Le problème, la proposition et le domaine sont obligatoires.")
    if any(len(value) > 2000 for value in values.values()):
        raise ValueError("Chaque champ est limité à 2 000 caractères.")
    item = {
        "id": uuid4().hex[:12],
        **values,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "idee",
        "prior_art_checked": False,
        "novelty_claim": "non_verifiee",
        "prototype_path": None,
        "test_results": [],
        "notes": [],
    }
    items = _load(path)
    items.append(item)
    _save(items, path)
    return item


def list_ideas(path: Path = DATA_FILE) -> list[dict]:
    return _load(path)


def update_status(idea_id: str, status: str, path: Path = DATA_FILE) -> dict:
    if status not in STATUSES:
        raise ValueError("Statut inconnu.")
    items = _load(path)
    for item in items:
        if item.get("id") == idea_id:
            item["status"] = status
            _save(items, path)
            return item
    raise KeyError("Idée introuvable.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Registre privé du laboratoire d'invention")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Enregistrer une idée")
    new.add_argument("--problem", required=True)
    new.add_argument("--proposal", required=True)
    new.add_argument("--domain", required=True)
    sub.add_parser("list", help="Afficher les idées enregistrées")
    args = parser.parse_args()
    if args.command == "new":
        result = create_idea(args.problem, args.proposal, args.domain)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(list_ideas(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
