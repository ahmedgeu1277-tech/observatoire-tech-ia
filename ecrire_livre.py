"""Générateur manuel d'encyclopédie à partir des archives publiques."""
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = Path.home() / ".observatoire_tech_gaming" / "publications"


def generer_encyclopedie_annuelle():
    memory = ROOT / "memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Livre non créé : aucune mémoire disponible.")
        return None

    public_notes = memory.read_text(encoding="utf-8")[-24000:]
    result, provider = generate_text(
        [
            {"role": "system", "content": "Tu écris un guide documentaire en français, sans inventer de faits."},
            {"role": "user", "content": (
                "Rédige « Encyclopédie des outils et tendances Tech & IA ». "
                "Organise par thèmes. Distingue faits sourcés, hypothèses et conseils. "
                "N'invente aucune source, date, citation ou statistique. "
                "Indique les limites des notes disponibles.\nNOTES PUBLIQUES :\n" + public_notes
            )},
        ],
        max_tokens=6000,
        temperature=0.2,
    )
    content = result.strip()
    if len(content) < 1000 or not verifier_conformite_legale(content, "LIVRE_ANNUEL"):
        raise RuntimeError("Texte vide, trop court ou bloqué par le contrôle de sécurité.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "ENCYCLOPEDIE_TECH_IA.md"
    output.write_text(
        f"# Encyclopédie Tech & IA\n\nOuvrage assisté par {provider}. "
        "Vérifiez les sources originales.\n\n" + content,
        encoding="utf-8",
    )
    print("Livre créé dans le dossier privé de publications :", output)
    return str(output)


if __name__ == "__main__":
    generer_encyclopedie_annuelle()
