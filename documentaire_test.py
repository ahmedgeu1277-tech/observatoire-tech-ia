"""Compile quatre dossiers publiés en un documentaire de démonstration archivé 30 jours."""
import asyncio
import html
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from video_documentaire import generer_video
from traduire_documentaire import generer_variantes_multilingues

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
AUDIO_DIR = SITE / "audio"
VIDEO_DIR = SITE / "video"
ARCHIVE_DIR = SITE / "archives"
ARTICLES_FILE = SITE / "articles.json"
MANIFEST = SITE / "documentaire-test.json"
PAGE = SITE / "documentaire-test.html"
SCRIPT = SITE / "documentaire-test.md"
TEMPLATE = ROOT / "templates" / "documentaire.html.tpl"


def charger_dossiers():
    if not ARTICLES_FILE.is_file():
        raise RuntimeError("Le fichier des articles publiés est absent.")
    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    if not isinstance(articles, list):
        raise RuntimeError("Le fichier des articles n'est pas une liste.")
    selected, seen = [], set()
    for article in sorted(articles, key=lambda item: str(item.get("date", "")), reverse=True):
        if not isinstance(article, dict):
            continue
        theme = str(article.get("theme") or article.get("title") or "").strip()
        title = str(article.get("title") or "").strip()
        summary = str(article.get("summary") or "").strip()
        verdict = str(article.get("verdict") or "").strip()
        tip = str(article.get("tip") or "").strip()
        sources = article.get("sources")
        if not theme or theme.casefold() in seen or not title or len(summary) < 40 or not isinstance(sources, list):
            continue
        secure_sources = [s for s in sources if isinstance(s, dict) and str(s.get("url", "")).startswith("https://")]
        if not secure_sources:
            continue
        selected.append({"theme": theme, "title": title, "summary": summary, "verdict": verdict, "tip": tip, "sources": secure_sources[:3]})
        seen.add(theme.casefold())
        if len(selected) == 4:
            break
    if len(selected) != 4:
        raise RuntimeError("Il faut quatre dossiers distincts avec des sources HTTPS.")
    return selected


def generer_documentaire():
    dossiers = charger_dossiers()
    title = "Les actualités Tech & Gaming : quatre dossiers à vérifier"
    intro = ("Ce documentaire compile quatre dossiers récents déjà publiés par l'Observatoire. "
             "Les résumés, verdicts et conseils sont repris sans ajouter de nouveaux faits. "
             "Les liens permettent de consulter les sources originales et les incertitudes restent signalées.")
    chapters = []
    for dossier in dossiers:
        source_names = ", ".join(str(s.get("publisher") or s.get("domain") or "source") for s in dossier["sources"])
        body = (f"Résumé éditorial : {dossier['summary']} Évaluation : {dossier['verdict']} "
                f"Conseil : {dossier['tip']} Les références associées sont : {source_names}. "
                "Les éléments incertains ne doivent pas être considérés comme confirmés. "
                "Pour approfondir, ouvrir les sources originales et vérifier leur date et leur contexte.")
        chapters.append((dossier["title"], body, dossier["sources"]))
    script = "# " + title + "\n\n" + intro + "\n\n"
    for number, (heading, body, sources) in enumerate(chapters, 1):
        script += f"## Chapitre {number} — {heading}\n\n{body}\n\nSources :\n"
        for source in sources:
            script += f"- {source.get('publisher') or source.get('domain') or 'Source'} : {source['url']}\n"
        script += "\n"
    script += "\n---\nDocumentaire compilé automatiquement à partir des articles publiés.\n"
    if len(script) < 1200 or not verifier_conformite_legale(script, "DOCUMENTAIRE_TEST"):
        raise RuntimeError("Le contenu compilé est incomplet ou bloqué par le contrôle de sécurité.")
    now = datetime.now(UTC)
    expires = now + timedelta(days=30)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    audio_name = f"documentaire-test-{stamp}.mp3"
    audio_path = AUDIO_DIR / audio_name

    async def produire_audio():
        import edge_tts
        spoken = title + ". " + intro + " " + " ".join(h + ". " + b for h, b, _ in chapters) + " Fin du documentaire."
        await asyncio.wait_for(edge_tts.Communicate(spoken[:24000], "fr-FR-RemyMultilingualNeural", rate="-5%", pitch="+0Hz", volume="+0%").save(str(audio_path)), timeout=180)

    asyncio.run(produire_audio())
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        raise RuntimeError("Le fichier audio n'a pas été créé correctement.")
    video_name = f"documentaire-test-{stamp}.mp4"
    video_path = VIDEO_DIR / video_name
    slides = [("Introduction", title, intro)]
    slides.extend((f"Dossier {n}", heading, dossier["summary"] + " " + dossier["verdict"])
                  for n, (heading, _body, _sources), dossier in zip(range(1, 5), chapters, dossiers))
    generer_video(audio_path, slides, video_path)
    # Les sources ne sont jamais envoyées au traducteur : seuls titre, résumé,
    # verdict et conseil sont traduits. En cas de quota indisponible, le français reste publié.
    translated_dossiers = [
        {"title": d["title"], "summary": d["summary"], "verdict": d["verdict"], "tip": d["tip"]}
        for d in dossiers
    ]
    translations = generer_variantes_multilingues(
        title, intro, translated_dossiers, AUDIO_DIR, VIDEO_DIR, stamp
    )
    SCRIPT.write_text(script, encoding="utf-8")
    archive_script = ARCHIVE_DIR / f"documentaire-test-{stamp}.md"
    shutil.copy2(SCRIPT, archive_script)
    manifest = {"created_at": now.isoformat(), "expires_at": expires.isoformat(),
                "audio_file": audio_name, "video_file": video_name,
                "archive_file": archive_script.name, "title": title,
                "retention_days": 30, "translations": translations}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        '<section><h2 data-i18n="intro">Introduction</h2><p>'
        + html.escape(intro) + '</p></section>'
    ]
    for number, (heading, body, sources) in enumerate(chapters, 1):
        links = "".join(
            f'<li><a href="{html.escape(str(source["url"]), quote=True)}" '
            f'rel="noopener noreferrer">{html.escape(str(source.get("publisher") or source.get("domain") or "Source"))}</a></li>'
            for source in sources
        )
        sections.append(
            f'<section><h2><span data-i18n="chapter">Chapitre</span> {number} — '
            f'{html.escape(heading)}</h2><p>{html.escape(body)}</p>'
            f'<h3 class="sources-heading" data-i18n="sources">Sources</h3><ul>{links}</ul></section>'
        )
    template = TEMPLATE.read_text(encoding="utf-8")
    page = (
        template
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{VIDEO}}", html.escape(video_name, quote=True))
        .replace("{{AUDIO}}", html.escape(audio_name, quote=True))
        .replace("{{EXPIRY}}", html.escape(expires.isoformat()))
        .replace("{{SECTIONS}}", "".join(sections))
        .replace("{{TRANSLATIONS_JSON}}", json.dumps(translations, ensure_ascii=False).replace("<", "\\u003c"))
    )
    PAGE.write_text(page, encoding="utf-8")
    print(f"Documentaire généré ; médias et copie écrite conservés jusqu'au {expires.isoformat()}.")
    return str(PAGE)


if __name__ == "__main__":
    generer_documentaire()
