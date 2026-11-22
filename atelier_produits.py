"""Atelier de produits : transforme une opportunité documentée en fiche de décision.

Le score est une aide au tri, pas une étude de marché ni une preuve de nouveauté.
Aucune vente, publication ou exécution de code n'est déclenchée par ce module.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

DIMENSIONS = {
    "customer_pain": 25,
    "demand_evidence": 20,
    "feasibility": 20,
    "differentiation": 15,
    "affordability": 10,
    "market_access": 10,
}
MAX_TEXT = 2000
WORKFLOW_STATUSES = {"candidate", "research", "prototype", "validated", "rejected"}
ROOT = Path(__file__).resolve().parent
DEFAULT_PRODUCTS_DIR = ROOT / ".laboratoire_prive" / "produits"
PRODUCT_TYPES = {
    "software", "developer_tool", "ai_agent", "game_tool",
    "security_tool", "hardware_research", "digital_service",
}


def evaluate_opportunity(data: object) -> dict:
    """Valide et note une opportunité sur 100 à partir de notes humaines sourcées."""
    if not isinstance(data, dict):
        raise ValueError("L'opportunité doit être un objet JSON.")
    required_text = ("name", "problem", "target_customer", "proposed_solution", "product_type")
    values = {}
    for key in required_text:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
            raise ValueError(f"Champ texte obligatoire invalide : {key}.")
        values[key] = value.strip()
    if values["product_type"] not in PRODUCT_TYPES:
        raise ValueError("Type de produit inconnu.")
    evidence = data.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) > 20:
        raise ValueError("evidence doit être une liste de 20 références maximum.")
    clean_evidence = []
    for item in evidence:
        if not isinstance(item, str) or not item.strip() or len(item) > 1000:
            raise ValueError("Chaque preuve doit être une référence textuelle valide.")
        clean_evidence.append(item.strip())
    scores = data.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise ValueError("Fournis une note de 1 à 5 pour chacune des six dimensions.")
    clean_scores = {}
    for key in DIMENSIONS:
        value = scores[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"La note {key} doit être un entier de 1 à 5.")
        clean_scores[key] = value
    weighted = sum(clean_scores[key] * weight for key, weight in DIMENSIONS.items())
    score = round(weighted / 5)
    if score >= 80:
        decision = "priorite_prototype"
    elif score >= 65:
        decision = "etude_complementaire"
    elif score >= 50:
        decision = "a_retravailler"
    else:
        decision = "ne_pas_prioriser"
    return {
        "id": uuid4().hex[:12],
        **values,
        "scores": clean_scores,
        "weights_percent": DIMENSIONS.copy(),
        "score_percent": score,
        "decision": decision,
        "evidence": clean_evidence,
        "evidence_status": "references_fournies_a_verifier" if clean_evidence else "aucune_preuve_fournie",
        "novelty_status": "non_verifiee",
        "commercial_status": "aucune_vente_autorisee",
        "workflow_status": "candidate",
        "status_history": [{
            "status": "candidate",
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
            "note": "Fiche créée ; preuves et hypothèses à vérifier.",
        }],
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "next_steps": [
            "Interroger des utilisateurs potentiels et conserver leurs retours.",
            "Comparer au moins trois solutions concurrentes avec des sources datées.",
            "Vérifier les licences, la propriété intellectuelle, la sécurité et les coûts.",
            "Construire un prototype minimal sans données sensibles.",
            "Tester avec des critères mesurables et faire valider les résultats.",
            "Faire examiner les conditions commerciales et légales par un adulte responsable avant toute vente.",
        ],
        "commercial_model_hypotheses": [
            "version gratuite limitée puis offre payante",
            "licence par utilisateur ou par équipe",
            "paiement unique pour un outil autonome",
            "prestation d'installation ou de personnalisation",
        ],
        "safety": {
            "automatic_publication": False,
            "automatic_sale": False,
            "code_execution": False,
            "human_review_required": True,
        },
    }


def save_opportunity(report: dict, directory: Path) -> Path:
    """Sauvegarde localement, dans un dossier choisi hors du site public."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{report['id']}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target




def update_opportunity_status(directory: Path, opportunity_id: str, status: str, note: str | None = None) -> dict:
    """Fait évoluer explicitement le statut d'une opportunité locale, sans vente ni publication."""
    if not isinstance(opportunity_id, str) or not re.fullmatch(r"[a-f0-9]{12}", opportunity_id):
        raise ValueError("Identifiant d'opportunité invalide.")
    if not isinstance(status, str) or status not in WORKFLOW_STATUSES:
        raise ValueError("Statut inconnu.")
    if note is not None:
        if not isinstance(note, str) or len(note) > 1000:
            raise ValueError("La note doit être un texte de 1 000 caractères maximum.")
        from agent_gardien import contient_secret_potentiel
        if contient_secret_potentiel(note):
            raise ValueError("La note contient un secret potentiel ; elle n'a pas été enregistrée.")
        note = note.strip()
    root = Path(directory)
    path = root / f"{opportunity_id}.json"
    if not path.is_file() or path.resolve().parent != root.resolve():
        raise ValueError("Opportunité introuvable.")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Fiche d'opportunité illisible.") from exc
    if not isinstance(report, dict) or report.get("id") != opportunity_id:
        raise ValueError("Fiche d'opportunité invalide.")
    history = report.get("status_history")
    if not isinstance(history, list):
        history = []
    history.append({
        "status": status,
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "note": note or "",
    })
    report["status_history"] = history[-50:]
    report["workflow_status"] = status
    report["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return report

def list_opportunities(directory: Path) -> list[dict]:
    """Charge les fiches valides et les classe par score puis date, sans exécuter leur contenu."""
    root = Path(directory)
    if not root.exists():
        return []
    if not root.is_dir():
        raise ValueError("Le dossier des opportunités doit être un répertoire.")
    reports = []
    for path in root.glob("*.json"):
        try:
            if path.resolve().parent != root.resolve() or not path.is_file():
                continue
            item = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(item, dict) or item.get("id") != path.stem:
                continue
            score = item.get("score_percent")
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
                continue
            if item.get("decision") not in {
                "priorite_prototype", "etude_complementaire", "a_retravailler", "ne_pas_prioriser"
            }:
                continue
            if item.get("workflow_status") not in WORKFLOW_STATUSES:
                item["workflow_status"] = "candidate"
            reports.append(item)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return sorted(
        reports,
        key=lambda item: (item["score_percent"], str(item.get("created_at", ""))),
        reverse=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Atelier local de sélection et de classement des produits.")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("evaluate", help="Évaluer une opportunité depuis un fichier JSON.")
    evaluate.add_argument("json_file")
    evaluate.add_argument("--directory", type=Path, default=DEFAULT_PRODUCTS_DIR)
    listing = commands.add_parser("list", help="Classer les opportunités enregistrées.")
    listing.add_argument("--directory", type=Path, default=DEFAULT_PRODUCTS_DIR)
    update = commands.add_parser("status", help="Mettre à jour le statut d'une opportunité.")
    update.add_argument("opportunity_id")
    update.add_argument("status", choices=sorted(WORKFLOW_STATUSES))
    update.add_argument("--note", default=None)
    update.add_argument("--directory", type=Path, default=DEFAULT_PRODUCTS_DIR)
    args = parser.parse_args()
    if args.command == "evaluate":
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        report = evaluate_opportunity(data)
        print(save_opportunity(report, args.directory))
    elif args.command == "status":
        report = update_opportunity_status(args.directory, args.opportunity_id, args.status, args.note)
        print(json.dumps({"id": report["id"], "workflow_status": report["workflow_status"]}, ensure_ascii=False))
    else:
        print(json.dumps(list_opportunities(args.directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
