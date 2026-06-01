/* eslint-disable */
/**
 * app_version_watch.js — "Nová verze → Obnovit" prompt (Marti 1.6.2026).
 * ─────────────────────────────────────────────────────────────────────────────
 * Produkce: po každém nasazení mají lidi s otevřenou appkou starou verzi.
 * Tenhle watcher polluje /api/v1/erp/app-version (git HEAD sha). Když se verze
 * změní oproti té při načtení → spodní lišta "🔄 Nová verze — Obnovit".
 * Klik → location.reload() (network-first SW natáhne čerstvé).
 *
 * Sdílené — loadováno chatem (index.html) i ERP. Self-contained, bez závislostí.
 */
(function () {
  "use strict";

  var EP = "/api/v1/erp/app-version";
  var POLL_MS = 150000;  // 2.5 min
  var _loaded = null;
  var _shown = false;

  function _fetchVer(cb) {
    try {
      fetch(EP, { cache: "no-store", credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { cb(j && j.version ? j.version : null); })
        .catch(function () { cb(null); });
    } catch (e) { cb(null); }
  }

  function _showBanner() {
    if (_shown) return;
    _shown = true;
    var bar = document.createElement("div");
    bar.style.cssText =
      "position:fixed;left:0;right:0;bottom:0;z-index:100060;" +
      "background:#2a3a1f;border-top:2px solid #5a7a3a;color:#e8f4d8;" +
      "padding:12px 14px;display:flex;align-items:center;flex-wrap:wrap;gap:10px;" +
      "box-shadow:0 -4px 16px rgba(0,0,0,0.5);font-size:14px;";

    var t = document.createElement("div");
    t.style.cssText = "flex:1 1 auto;min-width:0;";
    t.textContent = "🔄 Nová verze STRATEGIE je k dispozici.";
    bar.appendChild(t);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "Obnovit";
    btn.style.cssText =
      "flex:0 0 auto;background:#3a7a3a;color:#fff;border:none;padding:10px 18px;" +
      "border-radius:6px;font-weight:700;font-size:15px;cursor:pointer;white-space:nowrap;";
    btn.addEventListener("click", function () {
      try { location.reload(); } catch (e) { location.href = location.href; }
    });
    bar.appendChild(btn);

    var x = document.createElement("button");
    x.type = "button";
    x.textContent = "×";
    x.style.cssText =
      "flex:0 0 auto;background:transparent;border:none;color:#bcd6a0;" +
      "font-size:24px;line-height:1;cursor:pointer;padding:4px 8px;";
    x.addEventListener("click", function () { try { bar.remove(); } catch (e) {} });
    bar.appendChild(x);

    document.body.appendChild(bar);
  }

  function _tick() {
    _fetchVer(function (v) {
      if (!v || v === "unknown") return;
      if (_loaded === null) { _loaded = v; return; }  // baseline při prvním načtení
      if (v !== _loaded) _showBanner();
    });
  }

  setTimeout(_tick, 3000);
  setInterval(_tick, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) _tick();
  });
})();
