<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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
</style>
</head>
<body>
<main>
<div class="toolbar">
<a href="./index.html" data-i18n="back">← Retour au média</a>
<label for="language" data-i18n="language">Langue</label>
<select id="language" aria-label="Language">
<option value="fr">Français</option><option value="en">English</option><option value="es">Español</option>
<option value="de">Deutsch</option><option value="pt">Português</option><option value="ar">العربية</option><option value="zh">中文</option>
</select>
</div>
<header>
<span data-i18n="archive">ARCHIVE CONSERVÉE 30 JOURS MINIMUM</span>
<h1>{{TITLE}}</h1>
<p data-i18n="description">Documentaire compilé à partir des articles publiés.</p>
<p data-i18n="contentNote">Le texte du documentaire et sa narration audio restent dans la langue d’origine des articles.</p>
<video id="documentary-video" controls preload="metadata" playsinline style="width:100%;border-radius:12px;background:#101820" src="video/{{VIDEO}}"><track id="subtitle-track" kind="subtitles" srclang="fr" label="Français" default></video>
<audio id="documentary-audio" controls preload="none" src="audio/{{AUDIO}}"></audio>
<small><span data-i18n="retention">Conservation prévue jusqu'au</span> : {{EXPIRY}}</small>
</header>
{{SECTIONS}}
<script id="translation-data" type="application/json">{{TRANSLATIONS_JSON}}</script>
</main>
<script>
(() => {
  const labels = {
    fr: {pageTitle:"Documentaire — Observatoire",back:"← Retour au média",language:"Langue",archive:"ARCHIVE CONSERVÉE 30 JOURS MINIMUM",description:"Documentaire compilé à partir des articles publiés.",contentNote:"Le texte du documentaire et sa narration audio restent dans la langue d’origine des articles.",intro:"Introduction",chapter:"Chapitre",sources:"Sources",retention:"Conservation prévue jusqu'au"},
    en: {pageTitle:"Documentary — Observatory",back:"← Back to the media site",language:"Language",archive:"ARCHIVE KEPT FOR AT LEAST 30 DAYS",description:"Documentary compiled from published articles.",contentNote:"The documentary text and audio narration remain in the articles' original language.",intro:"Introduction",chapter:"Chapter",sources:"Sources",retention:"Retention planned until"},
    es: {pageTitle:"Documental — Observatorio",back:"← Volver al medio",language:"Idioma",archive:"ARCHIVO CONSERVADO AL MENOS 30 DÍAS",description:"Documental recopilado a partir de artículos publicados.",contentNote:"El texto del documental y la narración de audio permanecen en el idioma original de los artículos.",intro:"Introducción",chapter:"Capítulo",sources:"Fuentes",retention:"Conservación prevista hasta"},
    de: {pageTitle:"Dokumentation — Observatorium",back:"← Zurück zum Medium",language:"Sprache",archive:"ARCHIV MINDESTENS 30 TAGE AUFBEWAHRT",description:"Dokumentation aus veröffentlichten Artikeln.",contentNote:"Der Dokumentationstext und die Audiowiedergabe bleiben in der Originalsprache der Artikel.",intro:"Einleitung",chapter:"Kapitel",sources:"Quellen",retention:"Aufbewahrung bis"},
    pt: {pageTitle:"Documentário — Observatório",back:"← Voltar ao portal",language:"Idioma",archive:"ARQUIVO CONSERVADO POR PELO MENOS 30 DIAS",description:"Documentário compilado a partir de artigos publicados.",contentNote:"O texto do documentário e a narração áudio permanecem no idioma original dos artigos.",intro:"Introdução",chapter:"Capítulo",sources:"Fontes",retention:"Conservação prevista até"},
    ar: {pageTitle:"فيلم وثائقي — المرصد",back:"العودة إلى الموقع ←",language:"اللغة",archive:"أرشيف محفوظ لمدة 30 يوماً على الأقل",description:"فيلم وثائقي جُمِع من المقالات المنشورة.",contentNote:"يبقى نص الفيلم الوثائقي والتعليق الصوتي بلغة المقالات الأصلية.",intro:"مقدمة",chapter:"الفصل",sources:"المصادر",retention:"الحفظ متوقع حتى"},
    zh: {pageTitle:"纪录片 — 观察站",back:"← 返回媒体主页",language:"语言",archive:"档案至少保留 30 天",description:"根据已发布文章汇编的纪录片。",contentNote:"纪录片文本和音频旁白保留文章的原始语言。",intro:"简介",chapter:"章节",sources:"来源",retention:"预计保留至"}
  };
  const selector = document.getElementById("language");
  function applyLanguage(language) {
    const lang = labels[language] ? language : "fr";
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.title = labels[lang].pageTitle;
    selector.setAttribute("aria-label", labels[lang].language);
    document.querySelectorAll("[data-i18n]").forEach(node => {
      const key = node.dataset.i18n;
      if (labels[lang][key]) node.textContent = labels[lang][key];
    });
    selector.value = lang;
    try { localStorage.setItem("observatoire-doc-language", lang); } catch (_) {}
  }
  const video = document.getElementById("documentary-video");
  const audio = document.getElementById("documentary-audio");
  const track = document.getElementById("subtitle-track");
  const translatedMedia = JSON.parse(document.getElementById("translation-data").textContent || "{}");
  const baseVideo = video.getAttribute("src");
  const baseAudio = audio.getAttribute("src");
  function applyContentLanguage(language) {
    const item = translatedMedia[language];
    if (!item) {
      video.src = baseVideo;
      audio.src = baseAudio;
      track.removeAttribute("src");
      track.default = false;
      return;
    }
    video.src = "video/" + item.video;
    audio.src = "audio/" + item.audio;
    track.src = "video/" + item.subtitles;
    track.srclang = language;
    track.label = item.name;
    track.default = true;
    const data = item.text;
    document.querySelector("header h1").textContent = data.title;
    const sections = [...document.querySelectorAll("main > section")];
    if (sections[0]) sections[0].querySelector("p").textContent = data.intro;
    sections.slice(1).forEach((section, index) => {
      const chapter = data.chapters[index];
      if (!chapter) return;
      section.querySelector("h2").textContent = chapter.title;
      section.querySelector("p").textContent =
        chapter.summary + " " + chapter.verdict + " " + chapter.tip;
    });
  }
  selector.addEventListener("change", () => {
    applyLanguage(selector.value);
    applyContentLanguage(selector.value);
  });
  let saved = "fr";
  try { saved = localStorage.getItem("observatoire-doc-language") || "fr"; } catch (_) {}
  applyLanguage(saved);
  applyContentLanguage(saved);
})();
</script>
</body>
</html>
