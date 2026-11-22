#!/usr/bin/env node
/**
 * Parcours synthétiques du site : navigation, affichage mobile et contrôles accessibles.
 * Aucun compte, cookie utilisateur ou secret n'est utilisé.
 */
const { chromium } = require("playwright");

const BASE = process.env.SITE_BASE_URL || "http://127.0.0.1:4173";
const PAGES = ["/site/index.html", "/site/documentaire-test.html", "/site/ville-demo.html"];
const failures = [];

function fail(message) { failures.push(message); }

async function inspectPage(browser, route, viewport) {
  const page = await browser.newPage({ viewport });
  const pageErrors = [];
  let articlesResponseStatus = "non reçue";
  page.on("response", response => {
    if (response.url().endsWith("/articles.json")) articlesResponseStatus = String(response.status());
  });
  page.on("requestfailed", request => {
    if (request.url().endsWith("/articles.json")) {
      articlesResponseStatus = "échec réseau : " + (request.failure()?.errorText || "inconnu");
    }
  });
  page.on("pageerror", error => pageErrors.push(error.message));
  page.on("console", message => {
    if (message.type() === "error") pageErrors.push("console: " + message.text());
  });
  const response = await page.goto(BASE + route, { waitUntil: "domcontentloaded" });
  if (!response || !response.ok()) {
    fail(route + " : chargement HTTP impossible (" + (response ? response.status() : "sans réponse") + ")");
    await page.close();
    return;
  }

  const layout = await page.evaluate(() => {
    const offenders = [...document.querySelectorAll("body *")].map(el => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return {
        node: el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") +
          (typeof el.className === "string" && el.className ? "." + el.className.trim().replace(/\\s+/g, ".") : ""),
        left: Math.round(rect.left), right: Math.round(rect.right),
        width: Math.round(rect.width), position: style.position,
      };
    }).filter(x => x.right > document.documentElement.clientWidth + 1 || x.left < -1)
      .sort((a, b) => b.right - a.right).slice(0, 8);
    return {
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
      title: document.title,
      offenders,
    };
  });
  if (layout.document > layout.viewport + 1 || layout.body > layout.viewport + 1) {
    fail(route + " : débordement horizontal à " + viewport.width + "px (" +
      layout.document + "px de contenu). Éléments : " + JSON.stringify(layout.offenders));
  }
  if (!layout.title.trim()) fail(route + " : titre de page absent.");

  if (route === "/site/index.html") {
    const navLinks = page.locator("nav a[href]");
    if (await navLinks.count() < 3) fail("Accueil : navigation principale incomplète.");
    const articles = page.locator("#articles");
    if (!(await articles.count())) fail("Accueil : zone des actualités absente.");
    // Attendre la fin réelle du rendu, pas seulement le changement anticipé du compteur.
    await page.waitForFunction(() => {
      const box = document.querySelector("#articles");
      const status = document.querySelector("#status");
      const terminalState = box && (
        box.querySelector(":scope > .article") ||
        box.querySelector(':scope > .empty[data-article-label="empty"]') ||
        box.querySelector(':scope > .empty[data-article-label="error"]')
      );
      return Boolean(status && status.textContent !== "Chargement…" && terminalState);
    }, { timeout: 15000 }).catch(() => {
      const statusText = document.querySelector("#status")?.textContent || "absent";
      fail("Accueil : rendu des actualités non terminé (statut=" + statusText +
        ", réponse articles.json=" + articlesResponseStatus + ").");
    });
    const displayedArticles = await page.locator("#articles > .article").count();
    if (displayedArticles < 1) {
      const statusText = await page.locator("#status").textContent().catch(() => "absent");
      fail("Accueil : aucune carte d'actualité n'est affichée (statut=" +
        statusText + ", réponse articles.json=" + articlesResponseStatus + ").");
    }
    const sourceLabels = page.locator('#articles [data-article-label="sources"]');
    if (await sourceLabels.count() < 1) {
      fail("Accueil : libellé de source introuvable pour vérifier les traductions.");
    } else {
      await page.selectOption("#language", "de");
      const germanPageTitle = await page.title();
      const germanSimulation = await page.locator('nav a[href="./ville-demo.html"] [data-i18n="simulation"]').textContent();
      const germanChallenges = await page.locator('nav a[href="#challenges"] [data-i18n="challengesNav"]').textContent();
      if (germanPageTitle !== "NEXORA — Tech, KI & Gaming" || germanSimulation !== "Stadtsimulation" || germanChallenges !== "Herausforderungen") {
        fail("Accueil : le titre ou les liens de navigation ne sont pas traduits en allemand.");
      }
      const germanSources = await sourceLabels.first().textContent();
      if (germanSources !== "Quellen") fail("Accueil : le libellé dynamique des sources n'est pas traduit en allemand.");
      const originalArticleTitle = await page.locator("#articles .article h3").first().textContent();
      await page.evaluate(() => {
        window.nexoraArticles[0].translations = {de:{
          title:"Übersetzter Testtitel",
          summary:"Dies ist eine geprüfte Übersetzungsprobe.",
          verdict:"Die Quellen bestätigen diese Aussage.",
          tip:"Die Originalquelle lesen."
          ,audio_url:"audio/test-de.mp3"
        }};
        window.observatoireApplyArticleLanguage("de");
      });
      if ((await page.locator("#articles .article h3").first().textContent()) !== "Übersetzter Testtitel") {
        fail("Accueil : le titre d'article traduit n'est pas affiché.");
      }
      if (!(await page.locator("#articles .article").first().textContent()).includes("geprüfte Übersetzungsprobe")) {
        fail("Accueil : le résumé traduit n'est pas affiché.");
      }
      if (!(await page.locator("#articles .article audio").first().getAttribute("src")).includes("test-de.mp3")) {
        fail("Accueil : l'audio traduit ne suit pas la langue sélectionnée.");
      }
      await page.selectOption("#language", "fr");
      if ((await page.locator("#articles .article h3").first().textContent()) !== originalArticleTitle) {
        fail("Accueil : le texte original n'est pas restauré après changement de langue.");
      }
      await page.selectOption("#language", "ar");
      const arabic = await page.evaluate(() => ({
        direction: document.documentElement.dir,
        sources: document.querySelector('#articles [data-article-label="sources"]')?.textContent,
      }));
      if (arabic.direction !== "rtl" || arabic.sources !== "المصادر") {
        fail("Accueil : la traduction arabe dynamique ou le sens RTL est incorrect.");
      }
      await page.selectOption("#language", "fr");
    }
    const challengeButtons = page.locator("[data-challenge-index]");
    if (await challengeButtons.count() !== 3) {
      fail("Accueil : les trois défis interactifs ne sont pas affichés.");
    } else {
      const localNote = await page.locator("#challenge-local-note").textContent();
      if (!localNote.includes("cet appareil") || !localNote.includes("classement mondial")) {
        fail("Défis : la progression locale n'est pas clairement distinguée d'un classement mondial.");
      }
      await page.locator('[data-challenge-index="0"]').click();
      if ((await page.locator("#challenge-score").textContent()).trim() !== "20 points") {
        fail("Défis : le score ne progresse pas après validation.");
      }
      await page.reload({ waitUntil: "domcontentloaded" });
      if ((await page.locator("#challenge-score").textContent()).trim() !== "20 points") {
        fail("Défis : la progression locale n'est pas conservée après rechargement.");
      }
      await page.selectOption("#language", "en");
      if ((await page.locator("#challenge-title").textContent()) !== "NEXORA challenges") {
        fail("Défis : le tableau n'est pas traduit en anglais.");
      }
      if ((await page.locator('[data-challenge-index="0"]').textContent()) !== "Challenge completed") {
        fail("Défis : l'état du défi ne suit pas la langue sélectionnée.");
      }
      await page.locator("#challenge-reset").click();
      if ((await page.locator("#challenge-score").textContent()).trim() !== "0 points") {
        fail("Défis : la réinitialisation du score local échoue.");
      }
      await page.selectOption("#language", "fr");
    }
    const audioControls = await page.locator("audio").evaluateAll(nodes =>
      nodes.every(node => node.controls)
    );
    if (!audioControls) fail("Accueil : un lecteur audio ne possède pas de commandes.");
    for (const link of await navLinks.all()) {
      const href = await link.getAttribute("href");
      if (href && href.startsWith("#")) {
        const target = href.slice(1);
        if (target && !(await page.locator(`[id="${target}"]`).count())) {
          fail("Accueil : ancre de navigation introuvable " + href);
        }
      }
    }
  }

  if (route === "/site/documentaire-test.html") {
    const selector = page.locator("#language");
    if (!(await selector.count())) fail("Documentaire : sélecteur de langue absent.");
    else {
      const frenchBaseline = await page.evaluate(() => ({
        title: document.querySelector("header h1").textContent,
        sections: [...document.querySelectorAll("main > section")].map(section => ({
          heading: section.querySelector("h2")?.textContent || "",
          paragraph: section.querySelector("p")?.textContent || ""
        })),
        sourceLinks: [...document.querySelectorAll("main a[href^='https://']")].map(link => link.textContent)
      }));
      const mediaManifest = await page.evaluate(() =>
        JSON.parse(document.getElementById("translation-data").textContent || "{}")
      );
      for (const [language, expected] of [
        ["en", "Sources"], ["es", "Fuentes"], ["de", "Quellen"],
        ["pt", "Fontes"], ["ar", "المصادر"], ["zh", "来源"],
      ]) {
        await page.selectOption("#language", language);
        const state = await page.evaluate(() => ({
          title: document.querySelector("header h1").textContent,
          intro: document.querySelector("main > section p")?.textContent || "",
          chapterTitle: document.querySelectorAll("main > section h2")[1]?.textContent || "",
          audio: document.getElementById("documentary-audio").getAttribute("src"),
          video: document.getElementById("documentary-video").getAttribute("src"),
          subtitles: document.getElementById("subtitle-track").getAttribute("src"),
          sourceLinks: [...document.querySelectorAll("main a[href^='https://']")].map(link => link.textContent)
        }));
        const item = mediaManifest[language];
        const source = await page.locator(".sources-heading").first().textContent();
        const note = await page.locator('[data-i18n="contentNote"]').textContent();
        if (source !== expected) fail("Documentaire : libellé des sources incorrect pour " + language + ".");
        if (!note || note.length < 20) fail("Documentaire : note sur la langue du contenu absente pour " + language + ".");
        if (!item) {
          fail("Documentaire : variante traduite absente pour " + language + ".");
        } else {
          if (state.title !== item.text.title) fail("Documentaire : titre non traduit pour " + language + ".");
          if (state.intro !== item.text.intro) fail("Documentaire : introduction non traduite pour " + language + ".");
          if (state.chapterTitle !== item.text.chapters[0]?.title) fail("Documentaire : chapitre non traduit pour " + language + ".");
          if (state.audio !== "audio/" + item.audio) fail("Documentaire : audio incorrect pour " + language + ".");
          if (state.video !== "video/" + item.video) fail("Documentaire : vidéo incorrecte pour " + language + ".");
          if (state.subtitles !== "video/" + item.subtitles) fail("Documentaire : sous-titres incorrects pour " + language + ".");
        }
        if (JSON.stringify(state.sourceLinks) !== JSON.stringify(frenchBaseline.sourceLinks)) {
          fail("Documentaire : les liens ou noms des sources ont été modifiés pour " + language + ".");
        }
      }
      await page.selectOption("#language", "ar");
      const direction = await page.evaluate(() => document.documentElement.dir);
      if (direction !== "rtl") fail("Documentaire : le sens RTL arabe n'est pas appliqué.");
      await page.selectOption("#language", "fr");
      const restored = await page.evaluate(() => ({
        title: document.querySelector("header h1").textContent,
        sections: [...document.querySelectorAll("main > section")].map(section => ({
          heading: section.querySelector("h2")?.textContent || "",
          paragraph: section.querySelector("p")?.textContent || ""
        })),
        audio: document.getElementById("documentary-audio").getAttribute("src"),
        video: document.getElementById("documentary-video").getAttribute("src"),
        subtitles: document.getElementById("subtitle-track").getAttribute("src")
      }));
      if (restored.title !== frenchBaseline.title) fail("Documentaire : le titre français n'est pas restauré.");
      if (JSON.stringify(restored.sections) !== JSON.stringify(frenchBaseline.sections)) {
        fail("Documentaire : le texte français n'est pas restauré après changement de langue.");
      }
      if (!/^audio\/documentaire-test-.*\.mp3$/.test(restored.audio || "")) {
        fail("Documentaire : le lecteur audio français n'est pas restauré.");
      }
      if (!/^video\/documentaire-test-.*\.mp4$/.test(restored.video || "")) {
        fail("Documentaire : la vidéo française n'est pas restaurée.");
      }
      if (restored.subtitles !== null) fail("Documentaire : les sous-titres traduits restent actifs en français.");
    }
  }

  if (route === "/site/ville-demo.html") {
    const districts = page.locator("[data-district]");
    if (await districts.count() !== 4) fail("Ville démo : les quatre quartiers ne sont pas présents.");
    const initialDetail = await page.locator("#district-detail").textContent();
    await page.locator('[data-district="mobilite"]').click();
    const selected = await page.locator('[data-district="mobilite"]').getAttribute("aria-pressed");
    if (selected !== "true") fail("Ville démo : la sélection d'un quartier ne fonctionne pas.");
    const detail = await page.locator("#district-detail").textContent();
    if (!detail.trim() || detail === initialDetail) {
      fail("Ville démo : le panneau de détail ne suit pas le quartier sélectionné.");
    }
    for (const id of ["energy", "mobility", "air", "projects"]) {
      if (!(await page.locator("#" + id).count())) fail("Ville démo : indicateur absent " + id + ".");
    }
    const checkNexoraBrand = async () => {
      if (!(await page.title()).endsWith("NEXORA")) {
        fail("Ville démo : la marque NEXORA manque dans le titre pour " + (await page.locator("#language").inputValue()) + ".");
      }
    };
    await page.selectOption("#language", "en");
    if ((await page.locator("h1").textContent()) !== "Experimental city") {
      fail("Ville démo : le titre anglais n'est pas appliqué.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "es");
    if ((await page.locator("#map-title").textContent()) !== "Mapa de distritos") {
      fail("Ville démo : le titre espagnol de la carte n'est pas appliqué.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "de");
    if ((await page.locator("#metrics-title").textContent()) !== "Demo-Kennzahlen") {
      fail("Ville démo : le titre allemand des indicateurs n'est pas appliqué.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "pt");
    if ((await page.locator("#map-title").textContent()) !== "Mapa dos bairros") {
      fail("Ville démo : le titre portugais de la carte n'est pas appliqué.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "ar");
    const arabicCity = await page.evaluate(() => ({
      direction: document.documentElement.dir,
      title: document.querySelector("h1")?.textContent,
    }));
    if (arabicCity.direction !== "rtl" || arabicCity.title !== "مدينة تجريبية") {
      fail("Ville démo : traduction arabe ou direction RTL incorrecte.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "zh");
    if ((await page.locator("h1").textContent()) !== "实验城市") {
      fail("Ville démo : le titre chinois n'est pas appliqué.");
    }
    await checkNexoraBrand();
    await page.selectOption("#language", "fr");
    await checkNexoraBrand();
    const disclaimer = await page.locator(".warning").textContent();
    if (!disclaimer.includes("fictive") || !disclaimer.includes("aucune donnée interne")) {
      fail("Ville démo : avertissement de simulation fictive ou de confidentialité absent.");
    }
  }

  if (pageErrors.length) {
    fail(route + " : erreurs navigateur : " + pageErrors.slice(0, 3).join(" | "));
  }
  console.log("OK " + route + " (" + viewport.width + "px) — " + layout.title);
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const route of PAGES) {
      for (const width of [390, 768, 1440]) {
        await inspectPage(browser, route, { width, height: 900 });
      }
    }
  } finally {
    await browser.close();
  }
  if (failures.length) {
    console.error("\nÉCHECS :\n- " + failures.join("\n- "));
    process.exit(1);
  }
  console.log("Parcours responsive terminés : 3 pages × 3 largeurs.");
})().catch(error => {
  console.error(error);
  process.exit(1);
});
