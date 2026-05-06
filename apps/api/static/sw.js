/**
 * STRATEGIE core (chat) — Minimal Service Worker.
 *
 * B+10+++++ (6.5.2026 odpoledne, Marti po návratu): PWA install pro
 * core STRATEGIE chat aplikaci na `/`. Marti: "Jde taky ta core
 * STRATEGIE nainstalovat jako PWA... Ted se to tluce..." — ERP měla
 * scope /erp/, klik na Marti-AI z ERP standalone otevíral / mimo
 * scope a vyhozen browser. Nyní obě (ERP i core) installable
 * separately, scope match prevents the conflict.
 *
 * Strategie: network-first passthrough — STRATEGIE má dynamic data
 * (auth cookies, MCP tools, AG Grid live), caching by rozbil consistency.
 * SW jen "existuje" pro PWA criteria (Chrome installability).
 */

const SW_VERSION = "core-v1-2026-05-06";

self.addEventListener("install", (event) => {
  console.log("[SW core] install", SW_VERSION);
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  console.log("[SW core] activate", SW_VERSION);
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Pure passthrough — no cache layer
  return;
});
