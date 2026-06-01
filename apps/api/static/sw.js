/**
 * STRATEGIE Chat — Minimal Service Worker.
 *
 * Phase 38.5+ (10.5.2026 ráno). Marti's PWA Builder report:
 * "Make your app faster and more reliable by adding a service worker."
 *
 * PWA install kritéria:
 *   1. HTTPS ✓ (Let's Encrypt R10/R11 z Phase 25.3)
 *   2. manifest.json valid ✓
 *   3. Icons 192 + 512 ✓
 *   4. Service Worker s fetch handlerem ✓ ← TENTO SOUBOR
 *   5. launch_handler.client_mode='focus-existing' (Chrome 102+) ✓
 *
 * Bez SW Chrome nabídne jen "Přidat na plochu" (bookmark + chrome bar).
 * S SW Chrome nabídne "Nainstalovat aplikaci" (real PWA, standalone bez chromu).
 *
 * Strategie: network-first passthrough (žádný cache) — STRATEGIE chat má
 * always-fresh data (Marti-AI's konverzace, RAG memory, tool responses).
 *
 * Identický s /static/erp/sw.js, jen jiný scope ('/' vs '/erp/').
 */

const SW_VERSION = "chat-v2-network-first-2026-06-01";

self.addEventListener("install", (event) => {
  console.log("[SW chat] install", SW_VERSION);
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  console.log("[SW chat] activate", SW_VERSION);
  event.waitUntil(self.clients.claim());
});

// Network-first pro app shell (navigace) + JS/CSS — po každém nasazení se
// natáhne ČERSTVÁ verze sama (cache: no-store obejde HTTP cache prohlížeče).
// Marti 1.6.2026: konec "po deploy musím mazat cache / odinstalovat PWA".
// Ostatní (API, obrázky, fonty) → browser default. Offline fallback na
// běžný fetch (chat stejně vyžaduje síť).
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
