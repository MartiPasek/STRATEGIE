/**
 * STRATEGIE ERP — Minimal Service Worker.
 *
 * Phase B+9+++ (6.5.2026). Marti's spec: "A da se to udelat, aby ten Chrom
 * nebyl videt..." → PWA install vyžaduje:
 *   1. HTTPS ✓ (Let's Encrypt R10/R11 z Phase 25.3)
 *   2. manifest.json valid ✓ (Phase B+9+++ 1st pass)
 *   3. Icons 192 + 512 ✓
 *   4. Service Worker s fetch handlerem ✓ ← TENTO SOUBOR
 *
 * Bez SW Chrome nabídne jen "Přidat na plochu" (bookmark, URL bar zůstává).
 * S SW Chrome nabídne "Nainstalovat aplikaci" (standalone, bez chromu).
 *
 * Strategie: network-first passthrough (žádný cache) — STRATEGIE potřebuje
 * always-fresh data (CRM, dynamic API). Cache jen statické assets later
 * pokud bude potřeba offline mode.
 */

const SW_VERSION = "v2-network-first-2026-06-01";

// Install — claim immediately (žádný old SW retention)
self.addEventListener("install", (event) => {
  console.log("[SW] install", SW_VERSION);
  self.skipWaiting();
});

// Activate — claim all clients (immediate control after first install)
self.addEventListener("activate", (event) => {
  console.log("[SW] activate", SW_VERSION);
  event.waitUntil(self.clients.claim());
});

/**
 * Fetch — network-first pro app shell + JS/CSS (Marti 1.6.2026).
 * Po každém nasazení se natáhne ČERSTVÁ verze sama (cache: no-store obejde
 * HTTP cache) — konec "po deploy mazat cache / reinstall PWA". Ostatní
 * (API, obrázky, fonty) → browser default. Offline fallback na běžný fetch
 * (ERP stejně vyžaduje síť + live data).
 */
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const dest = req.destination;
  if (req.mode === "navigate" || dest === "document" ||
      dest === "script" || dest === "style") {
    event.respondWith(
      fetch(req.url, { cache: "no-store", credentials: "same-origin" })
        .catch(function () { return fetch(req); })
    );
  }
});
