"use strict";
const CACHE_NAME = "nexora-public-v1";
const CORE_URLS = ["./", "./index.html", "./methode.html", "./ville-demo.html", "./offline.html", "./manifest.webmanifest", "./icon.svg", "./articles.json"];

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.allSettled(CORE_URLS.map(async path => {
      const response = await fetch(path, {cache: "reload"});
      if (response.ok) await cache.put(path, response);
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith("nexora-public-") && name !== CACHE_NAME)
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  // Les requêtes Range (lecture audio/vidéo) renvoient souvent HTTP 206 ; Cache API ne peut pas les stocker.
  if (request.headers.has("range")) {
    event.respondWith(fetch(request));
    return;
  }
  const url = new URL(request.url);
  // Ne pas mettre en cache les médias lourds : préserver le stockage des téléphones et tablettes.
  if (/\\.(?:mp3|mp4|webm|m4a|ogg|wav)$/i.test(url.pathname)) return;
  if (url.pathname.includes("/.laboratoire_prive/")) return;

  if (request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(request, response.clone());
        }
        return response;
      } catch (_) {
        const cached = await caches.match(request);
        if (cached) return cached;
        return (await caches.match("./offline.html")) || new Response(
          "NEXORA est hors ligne. Ouvre une page déjà consultée lorsque la connexion revient.",
          {status: 503, headers: {"Content-Type": "text/plain; charset=utf-8"}}
        );
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cached = await caches.match(request);
    if (cached) {
      event.waitUntil(fetch(request).then(async response => {
        if (response.ok) (await caches.open(CACHE_NAME)).put(request, response.clone());
      }).catch(() => {}));
      return cached;
    }
    try {
      const response = await fetch(request);
      if (response.ok) (await caches.open(CACHE_NAME)).put(request, response.clone());
      return response;
    } catch (_) {
      return new Response("", {status: 504, statusText: "Offline"});
    }
  })());
});
