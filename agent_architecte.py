"""Agent architecte : crée des profils JSON, jamais du code exécutable."""
import json
import os
import re
from pathlib import Path

from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent
PROFILE_DIR = ROOT / "agents_dynamiques"

def creer_nouvel_agent_autonome():
    if not any(os.getenv(key) for key in ("GROQ_API_KEY", "HF_API_KEY", "HF_TOKEN")):
        print("Architecte ignoré : aucune clé IA configurée.")
        return None
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(path.stem for path in PROFILE_DIR.glob("*.json"))
    prompt = f"""Propose un profil d’agent spécialisé utile pour un observatoire Tech, IA, gaming et cybersécurité.
Aucun code, script, commande ou accès à un compte. Analyse uniquement des sources publiques fournies.
Agents existants : {existing}
Réponds en JSON avec name, role, mission, instructions. name : minuscules et underscores."""
    try:
        raw, provider = generate_text([
            {"role": "system", "content": "Tu proposes des profils d’agents prudents, en JSON valide."},
            {"role": "user", "content": prompt},
        ], max_tokens=900, temperature=0.2, json_mode=True)
        raw = raw.strip()
        if not raw.startswith("{"):
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Réponse JSON absente")
            raw = raw[start:end + 1]
        data = json.loads(raw)
        name = re.sub(r"[^a-z0-9_]", "_", str(data.get("name", "")).lower()).strip("_")
        if not name or len(name) > 40 or name in existing:
            return None
        profile = {
            "name": name,
            "role": str(data.get("role", "Analyste"))[:120],
            "mission": str(data.get("mission", ""))[:500],
            "instructions": str(data.get("instructions", ""))[:1000],
            "provider": provider,
            "safety": "Sources fournies uniquement ; aucune publication autonome ; aucun code exécutable.",
        }
        if not profile["mission"] or not profile["instructions"]:
            return None
        path = PROFILE_DIR / f"{name}.json"
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Profil d’agent créé : {path}")
        return str(path)
    except Exception as exc:  # noqa: BLE001 — l'agent ne doit jamais interrompre le pipeline.
        print(f"Architecte : {type(exc).__name__}")
        return None

if __name__ == "__main__":
    creer_nouvel_agent_autonome()
