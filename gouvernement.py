"""Gouvernement et économie virtuelle d'Usine IA Tech & Gaming 24-7.

Tous les crédits UCT sont fictifs, internes, non transférables et sans valeur réelle.
Les grèves, manifestations et opinions sont des simulations logicielles, pas des personnes.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "data"
STATE_FILE = STATE_DIR / "gouvernement.json"
CURRENCY = "UCT"
STARTING_BALANCE = 0

DIRECTORS = [
    ("Ariane", "présidente", "visionnaire", "innovation et croissance durable", "audacieuse"),
    ("Bastien", "vice-président", "méthodique", "coordination et stabilité", "conciliant"),
    ("Chloé", "finances", "prudente", "épargne et budgets équilibrés", "analytique"),
    ("Darius", "technologie", "curieux", "architecture logicielle", "expérimental"),
    ("Elena", "sécurité", "vigilante", "protection et résilience", "sceptique"),
    ("Farid", "gaming", "compétitif", "jeux multijoueurs", "énergique"),
    ("Gaëlle", "marketing", "sociable", "communautés et tendances", "expressive"),
    ("Hugo", "qualité", "perfectionniste", "tests et fiabilité", "exigeant"),
    ("Inès", "utilisateurs", "empathique", "accessibilité et simplicité", "diplomate"),
    ("Jules", "juridique", "rigoureux", "règles et propriété intellectuelle", "précis"),
    ("Kenza", "recherche", "inventive", "prototypes et découvertes", "exploratrice"),
    ("Léo", "production", "organisé", "délais et planification", "pragmatique"),
    ("Maya", "ressources humaines", "équitable", "formation et progression", "protectrice"),
    ("Nassim", "infrastructure", "résistant", "hébergement et disponibilité", "préventif"),
    ("Olivia", "données", "cartésienne", "mesures et statistiques", "factuelle"),
    ("Pavel", "international", "adaptable", "langues et marchés", "ouvert"),
    ("Quitterie", "créativité", "artistique", "identité visuelle et narration", "imaginative"),
    ("Rayan", "automatisation", "efficace", "processus reproductibles", "direct"),
    ("Salomé", "formation", "pédagogue", "documentation et apprentissage", "patiente"),
    ("Théo", "partenariats", "relationnel", "coopération et échanges", "négociateur"),
    ("Uma", "environnement", "responsable", "sobriété numérique", "réfléchie"),
    ("Victor", "audit", "indépendant", "traçabilité et contrôles", "impartial"),
    ("Wafa", "support", "serviable", "résolution des problèmes", "calme"),
    ("Xavier", "produit", "ambitieux", "fonctionnalités utiles", "décideur"),
    ("Yasmine", "communication", "créative", "transparence et pédagogie", "nuancée"),
    ("Zack", "performance", "tenace", "rapidité et optimisation", "intense"),
    ("Amira", "risques", "préventive", "continuité et plans de secours", "anticipatrice"),
    ("Noé", "communauté", "participatif", "retours des joueurs", "collectif"),
    ("Lina", "accessibilité", "attentive", "inclusion et ergonomie", "bienveillante"),
    ("Ethan", "innovation", "disruptif", "technologies émergentes", "provocateur"),
]

MINISTRIES = {
    "Finances": ["finances", "risques", "audit"],
    "Technologie": ["technologie", "infrastructure", "données", "automatisation"],
    "Gaming": ["gaming", "produit", "performance", "créativité"],
    "Sécurité": ["sécurité", "audit", "risques"],
    "Recherche": ["recherche", "innovation", "international"],
    "Ressources humaines": ["ressources humaines", "formation", "support"],
    "Production": ["production", "qualité", "technologie"],
    "Communication": ["marketing", "communication", "partenariats"],
    "Juridique et conformité": ["juridique", "audit"],
    "Communauté et accessibilité": ["utilisateurs", "communauté", "accessibilité"],
}

def now():
    return datetime.now(UTC).isoformat(timespec="seconds")

def initial_state():
    directors = []
    for index, (name, portfolio, personality, taste, style) in enumerate(DIRECTORS, start=1):
        directors.append({
            "id": f"ADM-{index:02d}", "name": name, "portfolio": portfolio,
            "personality": personality, "taste": taste, "decision_style": style,
            "grade": "membre du conseil", "experience": 0, "votes": 0,
            "satisfaction": 70, "active": True,
        })
    return {
        "schema_version": 1,
        "created_at": now(),
        "currency": {"code": CURRENCY, "name": "Unité de Crédit Technologique",
                     "real_value": 0, "convertible": False, "transferable": False,
                     "external_purchases_allowed": False},
        "treasury": 0,
        "ledger": [],
        "directors": directors,
        "ministries": MINISTRIES,
        "teams": [],
        "workforce": [],
        "activity_log": [],
        "projects": [],
        "meetings": [],
        "laws": [],
        "reforms": [],
        "social_events": [],
        "policy": {"priority_order": ["sécurité", "fiabilité", "projets essentiels",
                                      "innovation", "communication"],
                   "human_approval_required_for": [
                       "dépense réelle", "publication externe", "accès à un compte",
                       "modification de secrets", "suppression de données",
                       "changement de permissions"
                   ]},
    }

def load_state(path=STATE_FILE):
    path = Path(path)
    if not path.exists():
        return initial_state()
    with path.open(encoding="utf-8") as stream:
        state = json.load(stream)
    if state.get("schema_version") != 1:
        raise ValueError("Version de données gouvernementales non prise en charge.")
    if len(state.get("directors", [])) != 30:
        raise ValueError("Le conseil doit contenir exactement 30 administrateurs.")
    # Migration additive : conserve les anciennes sauvegardes du gouvernement.
    state.setdefault("teams", [])
    state.setdefault("workforce", [])
    state.setdefault("activity_log", [])
    return state

def save_state(state, path=STATE_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def add_credits(state, amount, reason, source="récompense interne simulée"):
    """Ajoute des points virtuels; ne représente jamais un paiement réel."""
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError("Le montant doit être un entier strictement positif.")
    state["treasury"] += amount
    state["ledger"].append({"date": now(), "type": "émission virtuelle",
                            "amount": amount, "balance": state["treasury"],
                            "reason": reason, "source": source, "real_money": False})
    return state["treasury"]

def allocate_budget(state, ministry, amount, reason):
    if ministry not in state["ministries"]:
        raise ValueError("Ministère inconnu.")
    if not isinstance(amount, int) or amount < 0:
        raise ValueError("Budget invalide.")
    if amount > state["treasury"]:
        raise ValueError("Budget refusé : crédits virtuels insuffisants.")
    state["treasury"] -= amount
    state["ledger"].append({"date": now(), "type": "allocation", "ministry": ministry,
                            "amount": -amount, "balance": state["treasury"],
                            "reason": reason, "real_money": False})
    return state["treasury"]

def _record_activity(state, event_type, description, details=None):
    entry = {"date": now(), "type": event_type, "description": description,
             "details": details or {}}
    state.setdefault("activity_log", []).append(entry)
    state["activity_log"] = state["activity_log"][-200:]
    return entry


def create_team(state, name, ministry, mission):
    name = str(name).strip()
    mission = str(mission).strip()
    if not name or not mission:
        raise ValueError("Une équipe doit avoir un nom et une mission.")
    if ministry not in state["ministries"]:
        raise ValueError("Ministère inconnu.")
    if any(team["name"].casefold() == name.casefold() for team in state["teams"]):
        raise ValueError("Une équipe porte déjà ce nom.")
    team = {"id": f"TEAM-{len(state['teams']) + 1:04d}", "name": name,
            "ministry": ministry, "mission": mission[:500], "status": "active",
            "members": [], "created_at": now()}
    state["teams"].append(team)
    _record_activity(state, "équipe créée", f"Équipe {name} créée dans {ministry}.",
                     {"team_id": team["id"]})
    return team


def recruit_agent(state, name, role, team_id):
    name, role = str(name).strip(), str(role).strip()
    team = next((t for t in state["teams"] if t["id"] == team_id), None)
    if team is None or team["status"] != "active":
        raise ValueError("Équipe introuvable ou inactive.")
    if not name or not role:
        raise ValueError("Le nom et le rôle de l'agent sont obligatoires.")
    agent_id = f"AGT-{len(state['workforce']) + 1:05d}"
    agent = {"id": agent_id, "name": name[:80], "role": role[:80],
             "team_id": team_id, "grade": "junior", "status": "actif",
             "experience": 0, "created_at": now()}
    state["workforce"].append(agent)
    team["members"].append(agent_id)
    _record_activity(state, "agent recruté", f"{name} rejoint {team['name']}.",
                     {"agent_id": agent_id, "team_id": team_id})
    return agent


def dissolve_team(state, team_id, reason):
    team = next((t for t in state["teams"] if t["id"] == team_id), None)
    if team is None or team["status"] != "active":
        raise ValueError("Équipe introuvable ou déjà inactive.")
    active_projects = [p for p in state["projects"]
                       if team["name"] in p.get("team", [])
                       and p.get("status") not in {"terminé", "annulé"}]
    if active_projects:
        raise ValueError("Impossible de dissoudre une équipe affectée à un projet actif.")
    reason = str(reason).strip()
    if len(reason) < 12:
        raise ValueError("Une justification d'au moins 12 caractères est nécessaire.")
    team["status"] = "dissoute"
    team["dissolved_at"] = now()
    team["dissolution_reason"] = reason[:500]
    for agent in state["workforce"]:
        if agent["team_id"] == team_id:
            agent["status"] = "en attente de réaffectation"
    _record_activity(state, "équipe dissoute", f"L'équipe {team['name']} a été dissoute.",
                     {"team_id": team_id, "reason": reason[:500]})
    return team


def promote_agent(state, agent_id, new_grade, evidence):
    agent = next((a for a in state["directors"] + state.get("workforce", []) if a["id"] == agent_id), None)
    if agent is None:
        raise ValueError("Agent introuvable.")
    if not evidence or len(str(evidence).strip()) < 12:
        raise ValueError("Une justification vérifiable est nécessaire.")
    grades = ["stagiaire", "junior", "confirmé", "expert", "chef d'équipe",
              "directeur adjoint", "directeur", "ministre", "membre du conseil"]
    if new_grade not in grades:
        raise ValueError("Grade inconnu.")
    if grades.index(new_grade) < grades.index(agent["grade"]):
        raise ValueError("Une rétrogradation nécessite une procédure distincte.")
    agent["grade"] = new_grade
    agent["promotion_evidence"] = str(evidence)[:500]
    agent["promoted_at"] = now()
    return agent

def create_project(state, name, priority, estimated_hours, due_date, team):
    priorities = {"critique": 1, "haute": 2, "normale": 3, "basse": 4}
    if priority not in priorities:
        raise ValueError("Priorité inconnue.")
    if not isinstance(estimated_hours, (int, float)) or estimated_hours <= 0:
        raise ValueError("Durée estimée invalide.")
    if not name.strip() or not team:
        raise ValueError("Le projet doit avoir un nom et une équipe.")
    project = {"id": f"PRJ-{len(state['projects']) + 1:04d}",
               "name": name.strip(), "priority": priority,
               "priority_rank": priorities[priority],
               "estimated_hours": estimated_hours, "due_date": due_date,
               "team": list(dict.fromkeys(team)), "status": "planifié",
               "created_at": now()}
    state["projects"].append(project)
    state["projects"].sort(key=lambda p: (p["priority_rank"], p["due_date"]))
    return project

def convene_meeting(state, meeting_type, topic, participants=None):
    valid_types = {"conseil", "urgence", "ministérielle", "projet", "crise"}
    if meeting_type not in valid_types:
        raise ValueError("Type de réunion inconnu.")
    if participants is None:
        participants = [a["id"] for a in state["directors"]]
    known = {a["id"] for a in state["directors"]}
    if not set(participants).issubset(known):
        raise ValueError("Un participant n'existe pas.")
    meeting = {"id": f"MTG-{len(state['meetings']) + 1:04d}",
               "type": meeting_type, "topic": topic,
               "participants": list(dict.fromkeys(participants)),
               "status": "ouverte", "votes": {}, "created_at": now()}
    state["meetings"].append(meeting)
    return meeting

def cast_vote(state, meeting_id, director_id, choice):
    if choice not in {"pour", "contre", "abstention"}:
        raise ValueError("Vote invalide.")
    meeting = next((m for m in state["meetings"] if m["id"] == meeting_id), None)
    if meeting is None or meeting["status"] != "ouverte":
        raise ValueError("Réunion introuvable ou fermée.")
    if director_id not in meeting["participants"]:
        raise ValueError("Cet administrateur ne participe pas à la réunion.")
    meeting["votes"][director_id] = choice
    return meeting

def close_vote(state, meeting_id):
    meeting = next((m for m in state["meetings"] if m["id"] == meeting_id), None)
    if meeting is None or meeting["status"] != "ouverte":
        raise ValueError("Réunion introuvable ou déjà fermée.")
    counts = {key: sum(1 for value in meeting["votes"].values() if value == key)
              for key in ("pour", "contre", "abstention")}
    meeting["status"] = "terminée"
    meeting["result"] = "adoptée" if counts["pour"] > counts["contre"] else "rejetée"
    meeting["counts"] = counts
    return meeting

def simulate_social_climate(state, policy_name, satisfaction_change):
    """Simule débats, pétitions, grèves ou manifestations sans action dans le monde réel."""
    if not isinstance(satisfaction_change, int) or not -30 <= satisfaction_change <= 30:
        raise ValueError("Variation de satisfaction hors limites.")
    for agent in state["directors"]:
        agent["satisfaction"] = max(0, min(100, agent["satisfaction"] + satisfaction_change))
    average = sum(a["satisfaction"] for a in state["directors"]) / 30
    event = {"date": now(), "policy": policy_name, "average_satisfaction": round(average, 1)}
    if average < 25:
        event.update({"type": "grève simulée", "description": "Une partie des équipes suspend symboliquement le travail et demande une négociation."})
    elif average < 40:
        event.update({"type": "manifestation simulée", "description": "Des agents organisent une manifestation virtuelle et déposent des revendications."})
    elif average < 55:
        event.update({"type": "pétition simulée", "description": "Une pétition virtuelle demande une révision de la politique."})
    else:
        event.update({"type": "consultation", "description": "Le climat social simulé reste stable; les avis sont enregistrés."})
    state["social_events"].append(event)
    return event

def save_public_state(state, root=ROOT):
    """Sauvegarde l'état pour le programme et pour le tableau de bord public."""
    root = Path(root)
    save_state(state, root / "data" / "gouvernement.json")
    save_state(state, root / "site" / "data" / "gouvernement.json")


def dashboard(state):
    return {
        "conseil": len(state["directors"]),
        "ministères": len(state["ministries"]),
        "agents_actifs": sum(1 for a in state["directors"] if a["active"]),
        "trésorerie_virtuelle": state["treasury"],
        "monnaie": CURRENCY,
        "projets": len(state["projects"]),
        "réunions": len(state["meetings"]),
        "événements_sociaux_simulés": len(state["social_events"]),
    }

if __name__ == "__main__":
    state = load_state()
    save_public_state(state)
    print(json.dumps(dashboard(state), ensure_ascii=False, indent=2))
