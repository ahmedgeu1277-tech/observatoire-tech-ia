"""Roadmap locale du laboratoire NEXORA.

Les statuts sont conservés hors du dépôt public, dans .laboratoire_prive.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_ROADMAP_PATH = ROOT / ".laboratoire_prive" / "roadmap.json"
STATUSES = {"backlog", "in_progress", "blocked", "done"}
TASKS = [
    {"id":"translate_archive","title":"Traduction intégrale des articles historiques","description":"Compléter progressivement les champs éditoriaux traduits, puis vérifier chaque langue et les lecteurs audio.","priority":"high"},
    {"id":"secure_global_ranking","title":"Classement communautaire sécurisé","description":"Étudier un backend authentifié, la modération, la protection anti-triche et la minimisation des données avant tout classement mondial.","priority":"normal"},
    {"id":"connected_city","title":"Simulation urbaine 3D","description":"Définir un prototype 3D léger, ses performances mobiles et des données explicitement fictives avant toute connexion réelle.","priority":"normal"},
    {"id":"private_hosting","title":"Laboratoire privé hébergé","description":"Étudier un hébergement avec authentification, autorisations, sauvegardes et séparation stricte des données publiques.","priority":"high"},
    {"id":"agent_sandbox","title":"Agents avec bac à sable et revue","description":"Faire proposer des changements dans des branches isolées, exécuter les tests et exiger une revue humaine avant fusion.","priority":"high"},
    {"id":"creative_suite","title":"Atelier de création logicielle et vidéo","description":"Assembler des outils gratuits et documenter les limites sur tablette et ordinateur.","priority":"normal"},
    {"id":"user_validation","title":"Tests avec de vrais utilisateurs","description":"Recueillir des retours volontaires, anonymisés et adaptés à l'âge, sans collecter de données sensibles.","priority":"normal"},
]

def _read(path: Path) -> list[dict]:
    if not path.exists():
        return [dict(task, status="backlog", updated_at=None) for task in TASKS]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Le fichier de feuille de route est illisible.") from exc
    if not isinstance(value, list) or len(value) != len(TASKS):
        raise ValueError("La feuille de route locale a un format invalide.")
    allowed = {task["id"] for task in TASKS}
    if any(not isinstance(row, dict) or row.get("id") not in allowed or row.get("status") not in STATUSES for row in value):
        raise ValueError("La feuille de route locale contient une tâche ou un statut invalide.")
    return value

def list_tasks(path: Path = DEFAULT_ROADMAP_PATH) -> list[dict]:
    """Retourne la feuille de route sans créer ni exposer de fichier public."""
    return _read(Path(path))

def update_status(path: Path, task_id: str, status: str) -> dict:
    """Met à jour un statut validé et écrit atomiquement dans le dossier privé."""
    if not isinstance(task_id, str) or task_id not in {task["id"] for task in TASKS}:
        raise ValueError("Identifiant de tâche inconnu.")
    if status not in STATUSES:
        raise ValueError("Statut de tâche invalide.")
    target = Path(path)
    rows = _read(target)
    from datetime import UTC, datetime
    for row in rows:
        if row["id"] == task_id:
            row["status"] = status
            row["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, target)
            if os.name == "posix":
                target.parent.chmod(0o700)
                target.chmod(0o600)
            return row
    raise ValueError("Tâche introuvable.")
