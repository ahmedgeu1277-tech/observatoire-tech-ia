#!/usr/bin/env node
/**
 * Parcours synthétiques du site : navigation, affichage mobile et contrôles accessibles.
 * Aucun compte, cookie utilisateur ou secret n'est utilisé.
 */
const { chromium } = require("playwright");

const BASE = process.env.SITE_BASE_URL || "http://127.0.0.1:4173";
const PAGES = ["/site/index.html", "/site/documentaire-test.html"];
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

  const layout = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
    title: document.title,
  }));
  if (layout.document > layout.viewport + 1 || layout.body > layout.viewport + 1) {
    fail(route + " : débordement horizontal à " + viewport.width + "px (" +
      layout.document + "px de contenu).");
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
