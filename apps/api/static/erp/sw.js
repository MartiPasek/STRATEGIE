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

const SW_VERSION = "v1-2026-05-06";

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
 * Fetch — pure passthrough.
 * STRATEGIE má dynamic data (auth cookies, MCP tools, AG Grid live updates)
 * — caching by jen rozbil consistency. SW jen "existuje" pro PWA criteria,
 * fetch handler nedělá žádnou cache.
 *
 * Pokud jednou budeme chtít offline mode (read-only přehledy), tady přidat
 * cache-first strategy pro /static/* a network-first pro /api/*.
 */
self.addEventListener("fetch", (event) => {
  // Pass-through — Chrome to detekuje jako "fetch handler exists" a oznámí
  // site jako installable. event.respondWith volat netřeba (browser default
  // handles fetch normálně).
  return;
});
