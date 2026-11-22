"""Compile quatre dossiers publiés en un documentaire de démonstration archivé 30 jours."""
import asyncio
import html
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from video_documentaire import generer_video

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
AUDIO_DIR = SITE / "audio"
VIDEO_DIR = SITE / "video"
ARCHIVE_DIR = SITE / "archives"
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
    SCRIPT.write_text(script, encoding="utf-8")
    archive_script = ARCHIVE_DIR / f"documentaire-test-{stamp}.md"
    shutil.copy2(SCRIPT, archive_script)
    manifest = {"created_at": now.isoformat(), "expires_at": expires.isoformat(),
                "audio_file": audio_name, "video_file": video_name,
                "archive_file": archive_script.name, "title": title,
                "retention_days": 30}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        f'<section><h2 data-i18n="intro">Introduction</h2><p>{html.escape(intro)}</p></section>'
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
    page = (  # nosec B608 - modèle HTML/CSS statique, aucune requête SQL construite.
        """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Documentaire Tech & Gaming compilé à partir des articles publiés.">
<title>Documentaire — Observatoire</title>
<style>
*{box-sizing:border-box;min-width:0}
html,body{width:100%;max-width:100%;overflow-x:hidden}
body{margin:0;background:#0b1020;color:#eef3ff;font:17px/1.7 system-ui,Arial,sans-serif}
main{width:100%;max-width:850px;margin:auto;padding:24px 20px 36px}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
select{font:inherit;font-size:13px;padding:8px;border-radius:8px}
video{display:block;width:100%;max-width:100%;height:auto}
h1,h2,p,li{overflow-wrap:anywhere}
header,section{background:#151e35;border:1px solid #2b3858;border-radius:18px;padding:24px;margin:18px 0}
h1{font-size:clamp(28px,5vw,44px);line-height:1.15}
h2{color:#65ddff}
p,li{color:#cbd5eb}
a{color:#65ddff}
audio{width:100%;margin-top:12px}
small{color:#9eafd0}
</style></head><body><main>
<div class="toolbar"><a href="./index.html" data-i18n="back">← Retour au média</a>
<label for="language" data-i18n="language">Langue</label>
<select id="language" aria-label="Language">
<option value="fr">Français</option><option value="en">English</option><option value="es">Español</option>
<option value="de">Deutsch</option><option value="pt">Português</option><option value="ar">العربية</option><option value="zh">中文</option>
</select></div>
<header>
<span data-i18n="archive">ARCHIVE CONSERVÉE 30 JOURS MINIMUM</span>
<h1>""" + html.escape(title) + """</h1>
<p data-i18n="description">Documentaire compilé à partir des articles publiés.</p>
<video controls preload="metadata" playsinline style="width:100%;border-radius:12px;background:#101820" src="video/""" + html.escape(video_name, quote=True) + """"></video>
<audio controls preload="none" src="audio/""" + html.escape(audio_name, quote=True) + """"></audio>
<small><span data-i18n="retention">Conservation prévue jusqu'au</span> : """ + html.escape(expires.isoformat()) + """</small>
</header>""" + "".join(sections) + """
</main>
<script>
(() => {
  const labels = {
    fr: {back:"← Retour au média",language:"Langue",archive:"ARCHIVE CONSERVÉE 30 JOURS MINIMUM",description:"Documentaire compilé à partir des articles publiés.",intro:"Introduction",chapter:"Chapitre",sources:"Sources",retention:"Conservation prévue jusqu'au"},
    en: {back:"← Back to the media site",language:"Language",archive:"ARCHIVE KEPT FOR AT LEAST 30 DAYS",description:"Documentary compiled from published articles.",intro:"Introduction",chapter:"Chapter",sources:"Sources",retention:"Retention planned until"},
    es: {back:"← Volver al medio",language:"Idioma",archive:"ARCHIVO CONSERVADO AL MENOS 30 DÍAS",description:"Documental recopilado a partir de artículos publicados.",intro:"Introducción",chapter:"Capítulo",sources:"Fuentes",retention:"Conservación prevista hasta"},
    de: {back:"← Zurück zum Medium",language:"Sprache",archive:"ARCHIV MINDESTENS 30 TAGE AUFBEWAHRT",description:"Dokumentation aus veröffentlichten Artikeln.",intro:"Einleitung",chapter:"Kapitel",sources:"Quellen",retention:"Aufbewahrung bis"},
    pt: {back:"← Voltar ao portal",language:"Idioma",archive:"ARQUIVO CONSERVADO POR PELO MENOS 30 DIAS",description:"Documentário compilado a partir de artigos publicados.",intro:"Introdução",chapter:"Capítulo",sources:"Fontes",retention:"Conservação prevista até"},
    ar: {back:"العودة إلى الموقع ←",language:"اللغة",archive:"أرشيف محفوظ لمدة 30 يوماً على الأقل",description:"فيلم وثائقي جُمِع من المقالات المنشورة.",intro:"مقدمة",chapter:"الفصل",sources:"المصادر",retention:"الحفظ متوقع حتى"},
    zh: {back:"← 返回媒体主页",language:"语言",archive:"档案至少保留 30 天",description:"根据已发布文章汇编的纪录片。",intro:"简介",chapter:"章节",sources:"来源",retention:"预计保留至"}
  };
  const selector = document.getElementById("language");
  function applyLanguage(language) {
    const lang = labels[language] ? language : "fr";
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach(node => {
      const key = node.dataset.i18n;
      if (labels[lang][key]) node.textContent = labels[lang][key];
    });
    selector.value = lang;
    try { localStorage.setItem("observatoire-doc-language", lang); } catch (_) {}
  }
  selector.addEventListener("change", () => applyLanguage(selector.value));
  let saved = "fr";
  try { saved = localStorage.getItem("observatoire-doc-language") || "fr"; } catch (_) {}
  applyLanguage(saved);
})();
</script></body></html>
        """)
    PAGE.write_text(page, encoding="utf-8")
    print(f"Documentaire généré ; médias et copie écrite conservés jusqu'au {expires.isoformat()}.")
    return str(PAGE)


if __name__ == "__main__":
    generer_documentaire()
