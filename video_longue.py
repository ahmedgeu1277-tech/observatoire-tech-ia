"""Documentaire hebdomadaire : cinq chapitres, script et pistes audio séparées."""
import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent

async def creer_documentaire_tech():
    memory = ROOT / "memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Documentaire ignoré : mémoire encore vide.")
        return None
    if not any(os.getenv(key) for key in ("GROQ_API_KEY", "HF_API_KEY", "HF_TOKEN")):
        print("Documentaire ignoré : aucune clé IA configurée.")
        return None
    notes = memory.read_text(encoding="utf-8")[-7000:]
    plan_text, provider = generate_text([
        {"role": "system", "content": "Tu construis un plan de documentaire factuel en français."},
        {"role": "user", "content": f"Propose exactement cinq titres de chapitres distincts pour un documentaire Tech & IA fondé uniquement sur ces notes. Un titre par ligne. Signale les limites des informations.\n{notes}"},
    ], max_tokens=500, temperature=0.2)
    titles = [line.strip(" -•0123456789.\t") for line in plan_text.splitlines() if line.strip()][:5]
    if len(titles) != 5:
        raise RuntimeError("Le plan du documentaire ne contient pas cinq chapitres.")
    parts = ["# Documentaire hebdomadaire Tech & IA", "", f"Script assisté par IA ({provider}). Vérifier les sources originales.", ""]
    chapters = []
    for number, title in enumerate(titles, 1):
        body, chapter_provider = generate_text([
            {"role": "system", "content": "Tu rédiges en français, distingues faits et incertitudes, et n’inventes aucune source ni aucun chiffre."},
            {"role": "user", "content": f"Rédige un chapitre documentaire de 400 à 450 mots sur « {title} ». Appuie-toi uniquement sur les notes ci-dessous. Si elles ne permettent pas cette longueur, sois plus court et dis ce qui manque. Ne prétends pas avoir vérifié des faits.\nNOTES :\n{notes}"},
        ], max_tokens=850, temperature=0.2)
        body = body.strip()
        if len(body.split()) < 180:
            raise RuntimeError(f"Chapitre {number} trop court : documentaire incomplet.")
        chapters.append((number, title, body, chapter_provider))
        parts.extend([f"## Chapitre {number} — {title}", body, ""])
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
    try:
        import edge_tts
        for number, title, body, chapter_provider in chapters:
            spoken = f"Chapitre {number}. {title}. {body}. Ce chapitre a été préparé avec l’aide d’une intelligence artificielle."
            audio_file = audio_folder / f"documentaire_tech_{stamp}_chapitre_{number}.mp3"
            await edge_tts.Communicate(spoken, "fr-FR-HenriNeural").save(str(audio_file))
        print("Cinq pistes audio de chapitres créées.")
    except Exception as exc:  # noqa: BLE001 — l'audio est facultatif, le script reste conservé.
        print(f"Audio documentaire incomplet ({type(exc).__name__}); le script écrit est conservé.")
    print(f"Documentaire écrit : {markdown}")
    return str(markdown)

if __name__ == "__main__":
    asyncio.run(creer_documentaire_tech())
