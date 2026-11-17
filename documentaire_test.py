"""Crée un documentaire audio de démonstration et le publie sur GitHub Pages pour 24 h."""
import asyncio
import html
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from groq import Groq

from agent_gardien import verifier_conformite_legale

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
AUDIO_DIR = SITE / "audio"
MANIFEST = SITE / "documentaire-test.json"
PAGE = SITE / "documentaire-test.html"
SCRIPT = SITE / "documentaire-test.md"
MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"


def lire_notes():
    path = ROOT / "memoire_tech.txt"
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        raise RuntimeError("La mémoire est vide : lance d'abord une collecte d'actualités.")
    return path.read_text(encoding="utf-8")[-18000:]


def demander(client, messages, max_tokens=1200):
    result = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.25,
        reasoning_effort="low",
        max_completion_tokens=max_tokens,
    )
    return (result.choices[0].message.content or "").strip()


def generer_documentaire():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("Secret GROQ_API_KEY absent.")
    notes = lire_notes()
    client = Groq(api_key=key, timeout=60, max_retries=2)

    plan = demander(client, [
        {"role": "system", "content": "Tu es un journaliste documentaire francophone prudent."},
        {"role": "user", "content": (
            "Prépare un documentaire court intitulé « Les technologies qui changent notre quotidien » "
            "avec une introduction et exactement 4 chapitres. Base-toi uniquement sur les notes ci-dessous. "
            "N'invente aucun fait, date, chiffre ou citation. Signale ce qui reste incertain. "
            "Réponds en JSON avec les clés title, introduction et chapters. chapters doit être une liste "
            "de 4 objets contenant title et text.\nNOTES :\n" + notes
        )}
    ], 2200)

    plan = plan.strip()
    if plan.startswith("```"):
        plan = plan.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(plan)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Le modèle n'a pas renvoyé le JSON attendu.") from exc
    chapters = data.get("chapters")
    if not isinstance(chapters, list) or len(chapters) != 4:
        raise RuntimeError("Le documentaire doit contenir exactement quatre chapitres.")
    title = str(data.get("title") or "Les technologies qui changent notre quotidien")[:140]
    intro = str(data.get("introduction") or "")[:2500]
    clean_chapters = []
    for item in chapters:
        if not isinstance(item, dict):
            continue
        heading = str(item.get("title") or "Chapitre")[:140]
        body = str(item.get("text") or "")[:5000]
        if body.strip():
            clean_chapters.append((heading, body))
    if len(clean_chapters) != 4 or len(intro) < 80:
        raise RuntimeError("Le contenu généré est incomplet.")
    script = "# " + title + "\n\n" + intro + "\n\n"
    for number, (heading, body) in enumerate(clean_chapters, 1):
        script += f"## Chapitre {number} — {heading}\n\n{body}\n\n"
    script += "\n---\nDocumentaire de démonstration assisté par IA. Les informations sont issues des notes archivées ; consulte les sources d'origine pour les vérifier.\n"
    if len(script) < 1200 or not verifier_conformite_legale(script, "DOCUMENTAIRE_TEST"):
        raise RuntimeError("Le contrôle de publication a bloqué le documentaire.")

    now = datetime.now(UTC)
    expires = now + timedelta(hours=24)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_name = f"documentaire-test-{stamp}.mp3"
    audio_path = AUDIO_DIR / audio_name

    async def produire_audio():
        import edge_tts
        spoken = title + ". " + intro + " " + " ".join(
            heading + ". " + body for heading, body in clean_chapters
        ) + " Fin du documentaire de démonstration."
        await edge_tts.Communicate(spoken[:24000], "fr-FR-HenriNeural").save(str(audio_path))

    asyncio.run(produire_audio())
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        raise RuntimeError("Le fichier audio n'a pas été créé correctement.")

    SCRIPT.write_text(script, encoding="utf-8")
    manifest = {
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "audio_file": audio_name,
        "title": title
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sections = [f'<section><h2>Introduction</h2><p>{html.escape(intro).replace(chr(10), "<br>")}</p></section>']
    for i, (heading, body) in enumerate(clean_chapters, 1):
        sections.append(
            f'<section><h2>Chapitre {i} — {html.escape(heading)}</h2>'
            f'<p>{html.escape(body).replace(chr(10), "<br>")}</p></section>'
        )
    page = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Documentaire audio de démonstration Tech & Gaming.">
<title>Documentaire test — Usine Tech & Gaming</title>
<style>
body{margin:0;background:#0b1020;color:#eef3ff;font:17px/1.7 system-ui,Arial,sans-serif}
main{max-width:850px;margin:auto;padding:36px 20px}
header,section{background:#151e35;border:1px solid #2b3858;border-radius:18px;padding:24px;margin:18px 0}
h1{font-size:clamp(28px,5vw,44px);line-height:1.15}h2{color:#65ddff}
p{color:#cbd5eb}audio{width:100%;margin-top:12px}
small{color:#9eafd0}.tag{display:inline-block;background:#1c3850;padding:5px 10px;border-radius:20px}
</style></head><body><main><header><span class="tag">Documentaire de test · assisté par IA</span>
<h1>""" + html.escape(title) + """</h1>
<p>Écoute le documentaire audio puis lis son script. Cette publication temporaire sera retirée automatiquement après 24 heures.</p>
<audio controls preload="metadata" src="./audio/""" + html.escape(audio_name) + """"></audio>
<p><small>Créé le """ + now.strftime("%d/%m/%Y à %H:%M UTC") + """ · Expire le """ + expires.strftime("%d/%m/%Y à %H:%M UTC") + """</small></p></header>
""" + "".join(sections) + """<section><p><strong>Transparence :</strong> texte et narration générés avec une IA à partir des notes archivées. Vérifie les informations auprès des sources originales.</p></section>
</main></body></html>"""
    PAGE.write_text(page, encoding="utf-8")
    print("Documentaire publié dans site/documentaire-test.html")
    print("Audio :", audio_path)
    print("Expiration :", expires.isoformat())


if __name__ == "__main__":
    generer_documentaire()
