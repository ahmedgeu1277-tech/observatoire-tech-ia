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
    await page.waitForFunction(() => {
      const status = document.querySelector("#status");
      return status && status.textContent !== "Chargement…";
    }, { timeout: 10000 }).catch(() => fail("Accueil : les actualités ne terminent pas leur chargement."));
    if (await page.locator("#articles > .article").count() < 1) {
      fail("Accueil : aucune carte d'actualité n'est affichée.");
    }
    const sourceLabels = page.locator('#articles [data-article-label="sources"]');
    if (await sourceLabels.count() < 1) {
      fail("Accueil : libellé de source introuvable pour vérifier les traductions.");
    } else {
      await page.selectOption("#language", "de");
      const germanSources = await sourceLabels.first().textContent();
      if (germanSources !== "Quellen") fail("Accueil : le libellé dynamique des sources n'est pas traduit en allemand.");
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

  if (route === "/site/ville-demo.html") {
    const districts = page.locator("[data-district]");
    if (await districts.count() !== 4) fail("Ville démo : les quatre quartiers ne sont pas présents.");
    await page.locator('[data-district="mobilite"]').click();
    const selected = await page.locator('[data-district="mobilite"]').getAttribute("aria-pressed");
    if (selected !== "true") fail("Ville démo : la sélection d'un quartier ne fonctionne pas.");
    const detail = await page.locator("#district-detail").textContent();
    if (!detail.includes("Mobilité")) fail("Ville démo : le panneau de détail ne suit pas le quartier sélectionné.");
    for (const id of ["energy", "mobility", "air", "projects"]) {
      if (!(await page.locator("#" + id).count())) fail("Ville démo : indicateur absent " + id + ".");
    }
    await page.selectOption("#language", "en");
    if ((await page.locator("h1").textContent()) !== "Experimental city") {
      fail("Ville démo : le titre anglais n'est pas appliqué.");
    }
    await page.selectOption("#language", "es");
    if ((await page.locator("#map-title").textContent()) !== "Mapa de distritos") {
      fail("Ville démo : le titre espagnol de la carte n'est pas appliqué.");
    }
    await page.selectOption("#language", "de");
    if ((await page.locator("#metrics-title").textContent()) !== "Demo-Kennzahlen") {
      fail("Ville démo : le titre allemand des indicateurs n'est pas appliqué.");
    }
    await page.selectOption("#language", "pt");
    if ((await page.locator("#map-title").textContent()) !== "Mapa dos bairros") {
      fail("Ville démo : le titre portugais de la carte n'est pas appliqué.");
    }
    await page.selectOption("#language", "ar");
    const arabicCity = await page.evaluate(() => ({
      direction: document.documentElement.dir,
      title: document.querySelector("h1")?.textContent,
    }));
    if (arabicCity.direction !== "rtl" || arabicCity.title !== "مدينة تجريبية") {
      fail("Ville démo : traduction arabe ou direction RTL incorrecte.");
    }
    await page.selectOption("#language", "zh");
    if ((await page.locator("h1").textContent()) !== "实验城市") {
      fail("Ville démo : le titre chinois n'est pas appliqué.");
    }
    await page.selectOption("#language", "fr");
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
