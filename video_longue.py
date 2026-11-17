"""Documentaire hebdomadaire : cinq chapitres, script et pistes audio séparées."""
import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent


def extraire_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Réponse JSON absente.")
        raw = raw[start : end + 1]
    return json.loads(raw)


async def creer_documentaire_tech():
    memory = ROOT / "memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Documentaire ignoré : mémoire encore vide.")
        return None
    if not any(os.getenv(key) for key in ("GROQ_API_KEY", "HF_API_KEY", "HF_TOKEN")):
        print("Documentaire ignoré : aucune clé IA configurée.")
        return None

    notes = memory.read_text(encoding="utf-8")[-6000:]
    raw, provider = generate_text(
        [
            {
                "role": "system",
                "content": (
                    "Tu es un documentariste francophone prudent. "
                    "Tu écris uniquement à partir des notes fournies et réponds en JSON valide."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Rédige un documentaire Tech & IA complet avec un titre, une introduction et "
                    "exactement cinq chapitres distincts. Chaque chapitre doit contenir environ "
                    "100 à 130 mots. N'invente aucun fait, chiffre, date, citation ou source. "
                    "Distingue les faits des hypothèses et signale les informations manquantes. "
                    "Réponds en JSON avec les clés title, introduction et chapters. "
                    "chapters doit être une liste de cinq objets contenant title et text.\n"
                    "NOTES :\n" + notes
                ),
            },
        ],
        max_tokens=2600,
        temperature=0.2,
        json_mode=True,
    )
    data = extraire_json(raw)
    if not isinstance(data, dict):
        raise RuntimeError("Le documentaire renvoyé n'est pas un objet JSON.")

    title = str(data.get("title") or "Documentaire hebdomadaire Tech & IA")[:140]
    intro = str(data.get("introduction") or "").strip()[:2500]
    raw_chapters = data.get("chapters")
    if not isinstance(raw_chapters, list) or len(raw_chapters) != 5 or len(intro) < 80:
        raise RuntimeError("Le documentaire doit contenir une introduction et exactement cinq chapitres.")

    chapters = []
    for number, item in enumerate(raw_chapters, 1):
        if not isinstance(item, dict):
            raise RuntimeError(f"Chapitre {number} invalide.")
        heading = str(item.get("title") or f"Chapitre {number}")[:140]
        body = str(item.get("text") or "").strip()[:5000]
        if len(body.split()) < 45:
            raise RuntimeError(f"Chapitre {number} trop court ({len(body.split())} mots) : documentaire incomplet.")
        chapters.append((number, heading, body))

    parts = [
        "# " + title,
        "",
        intro,
        "",
        f"Documentaire assisté par {provider}. Vérifiez les sources originales.",
        "",
    ]
    for number, heading, body in chapters:
        parts.extend([f"## Chapitre {number} — {heading}", body, ""])
    script = "\n".join(parts)
    if not verifier_conformite_legale(script, "DOCUMENTAIRE"):
        raise RuntimeError("Documentaire bloqué par le contrôle de sécurité.")

    stamp = datetime.now(UTC).strftime("%Y%m%d")
    folder = ROOT / "archives"
    folder.mkdir(exist_ok=True)
    markdown = folder / f"documentaire_tech_{stamp}.md"
    markdown.write_text(script, encoding="utf-8")

    audio_folder = ROOT / "site" / "audio"
    audio_folder.mkdir(parents=True, exist_ok=True)
    async def produire_audio():
        import edge_tts

        created = 0
        for number, heading, body in chapters:
            spoken = (
                f"Chapitre {number}. {heading}. {body}. "
                "Ce chapitre a été préparé avec l’aide d’une intelligence artificielle."
            )
            audio_file = audio_folder / f"documentaire_tech_{stamp}_chapitre_{number}.mp3"
            try:
                await edge_tts.Communicate(spoken, "fr-FR-HenriNeural").save(str(audio_file))
                if not audio_file.exists() or audio_file.stat().st_size < 1000:
                    audio_file.unlink(missing_ok=True)
                    raise RuntimeError("fichier audio absent ou trop petit")
                created += 1
                print(f"Piste audio {number} créée.")
            except Exception as exc:  # noqa: BLE001 — une piste défaillante ne bloque pas les autres.
                print(f"Piste audio {number} indisponible ({type(exc).__name__}: {str(exc)[:120]}).")
            await asyncio.sleep(2)
        print(f"Pistes audio créées : {created}/5.")

    try:
        asyncio.run(produire_audio())
    except Exception as exc:  # noqa: BLE001 — le script écrit reste conservé.
        print(f"Synthèse audio indisponible ({type(exc).__name__}: {str(exc)[:120]}).")

    print(f"Documentaire écrit : {markdown}")
    return str(markdown)


if __name__ == "__main__":
    asyncio.run(creer_documentaire_tech())
