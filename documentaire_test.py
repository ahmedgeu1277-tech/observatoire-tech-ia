"""Compile quatre dossiers publiés en un documentaire de démonstration temporaire."""
import asyncio
import html
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from video_documentaire import generer_video

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
AUDIO_DIR = SITE / "audio"
ARTICLES_FILE = SITE / "articles.json"
MANIFEST = SITE / "documentaire-test.json"
PAGE = SITE / "documentaire-test.html"
SCRIPT = SITE / "documentaire-test.md"


def charger_dossiers():
    if not ARTICLES_FILE.is_file():
        raise RuntimeError("Le fichier des articles publiés est absent.")
    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    if not isinstance(articles, list):
        raise RuntimeError("Le fichier des articles n'est pas une liste.")

    selected = []
    seen = set()
    for article in sorted(articles, key=lambda item: str(item.get("date", "")), reverse=True):
        if not isinstance(article, dict):
            continue
        theme = str(article.get("theme") or article.get("title") or "").strip()
        title = str(article.get("title") or "").strip()
        summary = str(article.get("summary") or "").strip()
        verdict = str(article.get("verdict") or "").strip()
        tip = str(article.get("tip") or "").strip()
        sources = article.get("sources")
        if not theme or theme.casefold() in seen or not title or len(summary) < 40:
            continue
        if not isinstance(sources, list):
            continue
        secure_sources = [
            source for source in sources
            if isinstance(source, dict) and str(source.get("url", "")).startswith("https://")
        ]
        if not secure_sources:
            continue
        selected.append({
            "theme": theme,
            "title": title,
            "summary": summary,
            "verdict": verdict,
            "tip": tip,
            "sources": secure_sources[:3],
        })
        seen.add(theme.casefold())
        if len(selected) == 4:
            break
    if len(selected) != 4:
        raise RuntimeError("Il faut quatre dossiers distincts avec des sources HTTPS.")
    return selected


def generer_documentaire():
    dossiers = charger_dossiers()
    title = "Les actualités Tech & Gaming : quatre dossiers à vérifier"
    intro = (
        "Ce documentaire de démonstration compile quatre dossiers récents déjà publiés par "
        "l'Observatoire. Les résumés, verdicts et conseils sont repris sans ajouter de nouveaux faits. "
        "Les liens permettent de consulter les sources originales et les incertitudes restent signalées."
    )

    chapters = []
    for dossier in dossiers:
        source_names = ", ".join(
            str(source.get("publisher") or source.get("domain") or "source")
            for source in dossier["sources"]
        )
        body = (
            f"Résumé éditorial : {dossier['summary']} "
            f"Évaluation : {dossier['verdict']} "
            f"Conseil : {dossier['tip']} "
            f"Les références associées sont : {source_names}. "
            "Les éléments signalés comme incertains ne doivent pas être considérés comme confirmés. "
            "Pour approfondir, il faut ouvrir les sources originales et vérifier leur date et leur contexte."
        )
        chapters.append((dossier["title"], body, dossier["sources"]))

    script = "# " + title + "\n\n" + intro + "\n\n"
    for number, (heading, body, sources) in enumerate(chapters, 1):
        script += f"## Chapitre {number} — {heading}\n\n{body}\n\nSources :\n"
        for source in sources:
            publisher = str(source.get("publisher") or source.get("domain") or "Source")
            script += f"- {publisher} : {source['url']}\n"
        script += "\n"
    script += "\n---\nDocumentaire compilé automatiquement à partir des articles publiés.\n"
    if len(script) < 1200 or not verifier_conformite_legale(script, "DOCUMENTAIRE_TEST"):
        raise RuntimeError("Le contenu compilé est incomplet ou bloqué par le contrôle de sécurité.")

    now = datetime.now(UTC)
    expires = now + timedelta(hours=24)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_name = f"documentaire-test-{stamp}.mp3"
    audio_path = AUDIO_DIR / audio_name

    async def produire_audio():
        import edge_tts

        spoken = title + ". " + intro + " " + " ".join(
            heading + ". " + body for heading, body, _sources in chapters
        ) + " Fin du documentaire de démonstration."
        await asyncio.wait_for(
            edge_tts.Communicate(spoken[:24000], "fr-FR-HenriNeural").save(str(audio_path)),
            timeout=180,
        )

    asyncio.run(produire_audio())
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        raise RuntimeError("Le fichier audio n'a pas été créé correctement.")

    video_dir = SITE / "video"
    video_name = f"documentaire-test-{stamp}.mp4"
    video_path = video_dir / video_name
    slides = [("Introduction", title, intro)]
    slides.extend(
        (f"Dossier {number}", heading, dossier["summary"] + " " + dossier["verdict"])
        for number, (heading, _body, _sources), dossier
        in zip(range(1, len(chapters) + 1), chapters, dossiers)
    )
    generer_video(audio_path, slides, video_path)

    SCRIPT.write_text(script, encoding="utf-8")
    manifest = {
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "audio_file": audio_name,
        "video_file": video_name,
        "title": title,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sections = [
        f'<section><h2>Introduction</h2><p>{html.escape(intro)}</p></section>'
    ]
    for number, (heading, body, sources) in enumerate(chapters, 1):
        links = "".join(
            f'<li><a href="{html.escape(str(source["url"]), quote=True)}" rel="noopener noreferrer">'
            f'{html.escape(str(source.get("publisher") or source.get("domain") or "Source"))}</a></li>'
            for source in sources
        )
        sections.append(
            f'<section><h2>Chapitre {number} — {html.escape(heading)}</h2>'
            f'<p>{html.escape(body)}</p><h3>Sources</h3><ul>{links}</ul></section>'
        )

    page = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Documentaire audio de démonstration Tech & Gaming, compilé à partir des articles publiés.">
<title>Documentaire test — Usine Tech & Gaming</title>
<style>
body{margin:0;background:#0b1020;color:#eef3ff;font:17px/1.7 system-ui,Arial,sans-serif}
main{max-width:850px;margin:auto;padding:36px 20px}
header,section{background:#151e35;border:1px solid #2b3858;border-radius:18px;padding:24px;margin:18px 0}
h1{font-size:clamp(28px,5vw,44px);line-height:1.15}h2{color:#65ddff}
p,li{color:#cbd5eb}a{color:#65ddff}audio{width:100%;margin-top:12px}
small{color:#9eafd0}.tag{display:inline-block;background:#20304f;padding:5px 10px;border-radius:20px}
</style></head><body><main>
<header><span class="tag">TEST TEMPORAIRE · 24 H</span>
<h1>""" + html.escape(title) + """</h1>
<p>Documentaire compilé à partir des articles publiés. Consultez les sources originales.</p>
<video controls preload="metadata" playsinline style="width:100%;border-radius:12px;background:#101820" src="video/""" + html.escape(video_name, quote=True) + """"></video>
<audio controls preload="none" src="audio/""" + html.escape(audio_name, quote=True) + """"></audio>
<small>Vidéo MP4 avec narration originale. Expiration automatique prévue : """ + html.escape(expires.isoformat()) + """</small></header>
""" + "".join(sections) + """
</main></body></html>"""
    PAGE.write_text(page, encoding="utf-8")
    print(f"Documentaire compilé : {SCRIPT}")
    print(f"Audio créé : {audio_path}")
    print(f"Page publiée jusqu'au : {expires.isoformat()}")
    return str(PAGE)


if __name__ == "__main__":
    generer_documentaire()
