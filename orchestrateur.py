"""Orchestrateur de missions IA bornées.

Les agents produisent des analyses textuelles uniquement. Aucun code généré
n'est exécuté, aucune publication ni action sur un compte n'est autorisée.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from agent_gardien import contient_secret_potentiel
from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent
PRIVATE_DIR = ROOT / ".laboratoire_prive" / "missions"
MAX_MISSION_CHARS = 12_000
MAX_CONTEXT_CHARS = 8_000
MAX_AGENT_HANDOFF_CHARS = 3_000
MAX_AGENTS = 3
MAX_DURATION_SECONDS = 180
MAX_TOKENS_PER_AGENT = 900

AGENTS = {
    "chercheur": (
        "Agent chercheur",
        "Analyse le problème, distingue faits, hypothèses et inconnues. "
        "Propose des pistes vérifiables et cite les éléments du contexte fourni."
    ),
    "critique": (
        "Agent critique",
        "Cherche les erreurs, risques, contradictions, coûts, limites et solutions "
        "déjà connues. Ne prétends jamais qu'une idée est inédite sans preuve."
    ),
    "architecte": (
        "Agent architecte",
        "Transforme les pistes en plan technique progressif, avec étapes, critères "
        "de réussite, tests, limites de sécurité et dépendances."
    ),
}


def valider_mission(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("La mission doit être un objet JSON.")
    mission = data.get("mission")
    context = data.get("context", "")
    agents = data.get("agents", ["chercheur", "critique", "architecte"])
    duration = data.get("max_duration_seconds", 180)
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("Le champ mission est obligatoire.")
    if len(mission) > MAX_MISSION_CHARS:
        raise ValueError("Mission trop longue.")
    if not isinstance(context, str) or len(context) > MAX_CONTEXT_CHARS:
        raise ValueError("Contexte invalide ou trop long.")
    if contient_secret_potentiel(mission) or contient_secret_potentiel(context):
        raise ValueError("Mission refusée : un secret potentiel a été détecté. Retire-le avant de continuer.")
    if not isinstance(agents, list) or not 1 <= len(agents) <= MAX_AGENTS:
        raise ValueError(f"Choisis entre 1 et {MAX_AGENTS} agents.")
    if any(not isinstance(agent, str) or agent not in AGENTS for agent in agents):
        raise ValueError("Un agent demandé est inconnu ou invalide.")
    if len(set(agents)) != len(agents):
        raise ValueError("Un agent demandé est inconnu ou répété.")
    if isinstance(duration, bool) or not isinstance(duration, int):
        raise ValueError("La durée doit être un nombre entier de secondes.")
    if not 60 * len(agents) <= duration <= MAX_DURATION_SECONDS:
        raise ValueError(f"La durée doit couvrir au moins 60 secondes par agent et ne pas dépasser {MAX_DURATION_SECONDS} secondes.")
    return {
        "mission": mission.strip(),
        "context": context.strip(),
        "agents": agents,
        "max_duration_seconds": duration,
    }


def executer_mission(
    data: object,
    output_dir: Path | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict:
    mission = valider_mission(data)
    started = time.monotonic()
    deadline = started + mission["max_duration_seconds"]
    results = []
    for agent_id in mission["agents"]:
        if should_cancel is not None and should_cancel():
            results.append({"agent": agent_id, "status": "cancelled"})
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            results.append({"agent": agent_id, "status": "stopped_deadline"})
            break
        role, instructions = AGENTS[agent_id]
        messages = [
            {
                "role": "system",
                "content": (
                    f"{role}. {instructions} "
                    "Règles : analyse textuelle seulement ; ne demande aucun secret ; "
                    "ne produis pas de commandes dangereuses ; ne prétends pas avoir "
                    "effectué des actions ou tests non réalisés."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"MISSION :\n{mission['mission']}\n\n"
                    f"CONTEXTE FOURNI :\n{mission['context'] or 'Aucun'}\n\n"
                    f"ANALYSES PRÉCÉDENTES DES AUTRES AGENTS :\n"
                    + (
                        "\n\n".join(
                            f"{AGENTS[item['agent']][0]} : {item['output'][:MAX_AGENT_HANDOFF_CHARS]}"
                            for item in results
                            if item["status"] == "completed"
                        )[-MAX_CONTEXT_CHARS:]
                        or "Aucune analyse précédente."
                    )
                ),
            },
        ]
        try:
            answer, provider = generate_text(
                messages,
                max_tokens=MAX_TOKENS_PER_AGENT,
                temperature=0.2,
                timeout=min(60, max(1, remaining)),
            )
            results.append({
                "agent": agent_id,
                "status": "completed",
                "provider": provider,
                "output": answer[:12_000],
            })
            if should_cancel is not None and should_cancel():
                results.append({"agent": agent_id, "status": "cancelled"})
                break
        except Exception as exc:  # noqa: BLE001
            results.append({
                "agent": agent_id,
                "status": "failed",
                "error_type": type(exc).__name__,
            })
            break

    report = {
        "id": uuid4().hex,
        "created_at": datetime.now(UTC).isoformat(),
        "mission": mission["mission"],
        "agents_requested": mission["agents"],
        "duration_limit_seconds": mission["max_duration_seconds"],
        "duration_seconds": round(time.monotonic() - started, 2),
        "status": (
            "cancelled"
            if any(item["status"] == "cancelled" for item in results)
            else "completed"
            if len(results) == len(mission["agents"])
            and all(item["status"] == "completed" for item in results)
            else "partial"
        ),
        "results": results,
        "safety": {
            "code_execution": False,
            "external_actions": False,
            "automatic_publication": False,
            "human_review_required": True,
        },
    }
    destination = output_dir or PRIVATE_DIR
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.chmod(destination, 0o700)
    target = destination / f"{report['id']}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    temporary.replace(target)
    report["report_path"] = str(target)
    return report


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage : python orchestrateur.py chemin/mission.json")
        return 2
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        report = executer_mission(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Mission refusée : {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps({
        "id": report["id"],
        "status": report["status"],
        "agents": report["agents_requested"],
        "report_path": report["report_path"],
    }, ensure_ascii=False))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
