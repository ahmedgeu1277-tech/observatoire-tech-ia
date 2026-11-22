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
<video controls preload="metadata" playsinline style="width:100%;border-radius:12px;background:#101820" src="video/{{VIDEO}}"></video>
<audio controls preload="none" src="audio/{{AUDIO}}"></audio>
<small><span data-i18n="retention">Conservation prévue jusqu'au</span> : {{EXPIRY}}</small>
</header>
{{SECTIONS}}
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
</script>
</body>
</html>
