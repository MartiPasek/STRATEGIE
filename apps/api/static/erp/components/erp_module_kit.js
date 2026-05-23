/**
 * Phase 38.4 Krok 14g Etapa B (16.5.2026) — Frontend Module Kit
 *
 * Marti's doctrine 16.5.:
 *   "kdyz neco v nejakem selze, hodi to uzivateli plnohodnotnou
 *    diagnostiku a zbytek bezi dale" — mutual immunity
 *
 * Provides global helpers loaded PRED vsemi ostatnimi ERP modules:
 *
 *   window._erpModuleHealth — register / markLoaded / markError / snapshot / stats
 *   window._erpLogToDb(level, moduleId, message, opts) — async, fail-safe
 *   window._erpLogToDb.info|warn|error|fatal — shortcuts
 *   window._erpLogToDb.drain() — manual drain trigger
 *   window._erpLoadModule(id, version, fn) — IIFE wrapper, catches init errors
 *
 *   Global handlers: window.error + unhandledrejection auto-log do fw.diag_log
 *   LocalStorage queue (Layer 2): erp_diag_log_queue, max 100, drop-oldest
 *   Periodic drain: every 30s
 *   Diagnostic UI banner: top-right pill (🟢/🟡/🔴 N/M mod · K err · Q q)
 *
 * Architecture: 3-layer fallback FE side:
 *   Layer 1: POST /api/v1/erp/diag-log/event (direct)
 *   Layer 2: localStorage queue (capacity 100, drop-oldest)
 *   Layer 3: console.error stderr (last resort, never crashes app)
 *
 * Backend has its own 3-layer fallback (DB → file → memory). Combined
 * FE+BE = 6-layer defense in depth.
 */

"use strict";

(function () {
  // ════════════════════════════════════════════════════════════════════
  // Module Health Register
  // ════════════════════════════════════════════════════════════════════
  const MODULES = {};

  function _isoNow() { return new Date().toISOString(); }

  const moduleHealth = {
    register(id, version) {
      if (!id) return;
      MODULES[id] = MODULES[id] || {};
      if (version) MODULES[id].version = version;
      MODULES[id].registeredAt = MODULES[id].registeredAt || _isoNow();
      MODULES[id].status = MODULES[id].status || "registered";
    },
    markLoaded(id, version) {
      if (!id) return;
      MODULES[id] = MODULES[id] || {};
      if (version) MODULES[id].version = version;
      MODULES[id].loadedAt = _isoNow();
      MODULES[id].status = "loaded";
      MODULES[id].lastError = null;
      _scheduleBannerUpdate();
    },
    markError(id, error) {
      if (!id) return;
      MODULES[id] = MODULES[id] || {};
      MODULES[id].status = "error";
      MODULES[id].lastError = {
        message: error?.message || String(error || "unknown"),
        stack: error?.stack || null,
        name: error?.name || null,
        when: _isoNow(),
      };
      _scheduleBannerUpdate();
    },
    snapshot() {
      try { return JSON.parse(JSON.stringify(MODULES)); }
      catch (e) { return {}; }
    },
    stats() {
      const total = Object.keys(MODULES).length;
      let loaded = 0, errors = 0, registered = 0;
      for (const m of Object.values(MODULES)) {
        if (m.status === "loaded") loaded++;
        else if (m.status === "error") errors++;
        else registered++;
      }
      return { total, loaded, errors, registered };
    },
  };

  window._erpModuleHealth = moduleHealth;

  // ════════════════════════════════════════════════════════════════════
  // LocalStorage Queue (Layer 2 fallback)
  // ════════════════════════════════════════════════════════════════════
  const QUEUE_KEY = "erp_diag_log_queue";
  const QUEUE_MAX = 100;

  function _queueGet() {
    try {
      const raw = localStorage.getItem(QUEUE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }

  function _queueSet(arr) {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(arr));
    } catch (e) {
      // localStorage full or disabled — last resort console
      try { console.error("[erp_module_kit] localStorage write failed:", e); } catch (_) {}
    }
  }

  function _queuePush(event) {
    const q = _queueGet();
    q.push(event);
    while (q.length > QUEUE_MAX) q.shift();
    _queueSet(q);
  }

  async function _drainQueue() {
    const q = _queueGet();
    if (q.length === 0) return { drained: 0, remaining: 0 };

    let drained = 0;
    const remaining = [];
    let dbDead = false;

    for (const event of q) {
      if (dbDead) {
        remaining.push(event);
        continue;
      }
      try {
        const r = await fetch("/api/v1/erp/diag-log/event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(event),
        });
        if (r.ok) {
          drained++;
        } else {
          remaining.push(event);
          dbDead = true;
        }
      } catch (e) {
        remaining.push(event);
        dbDead = true;
      }
    }

    _queueSet(remaining);
    _scheduleBannerUpdate();
    return { drained, remaining: remaining.length };
  }

  // ════════════════════════════════════════════════════════════════════
  // Element selector helper (stable-ish CSS path)
  // ════════════════════════════════════════════════════════════════════
  function _erpSelector(el) {
    if (!el || el.nodeType !== 1) return null;
    if (el.id) return "#" + el.id;
    const parts = [];
    let cur = el;
    let depth = 0;
    while (cur && cur.nodeType === 1 && depth < 5) {
      let part = (cur.tagName || "").toLowerCase();
      if (typeof cur.className === "string" && cur.className.trim()) {
        const classes = cur.className.split(/\s+/).filter(Boolean).slice(0, 2);
        if (classes.length) part += "." + classes.join(".");
      }
      parts.unshift(part);
      cur = cur.parentElement;
      depth++;
    }
    return parts.join(" > ");
  }

  // ════════════════════════════════════════════════════════════════════
  // _erpLogToDb — main logging API
  // ════════════════════════════════════════════════════════════════════
  async function _logToDbImpl(level, moduleId, message, opts) {
    opts = opts || {};
    const event = {
      level: level || "info",
      source: opts.source || "js",
      module_id: moduleId || "unknown",
      module_version: opts.version || (MODULES[moduleId] && MODULES[moduleId].version) || null,
      message: String(message == null ? "(no message)" : message),
      stack: opts.stack || (opts.error && opts.error.stack) || null,
      page_url: opts.page_url || (typeof location !== "undefined" ? location.href : null),
      user_agent: opts.user_agent || (typeof navigator !== "undefined" ? navigator.userAgent : null),
      viewport: opts.viewport ||
        (typeof window !== "undefined"
          ? `${window.innerWidth || 0}x${window.innerHeight || 0}`
          : null),
      element_selector: opts.element ? _erpSelector(opts.element) : (opts.element_selector || null),
      file_name: opts.file_name || opts.file || null,
      line_number: opts.line_number != null ? opts.line_number : (opts.line != null ? opts.line : null),
      column_number: opts.column_number != null ? opts.column_number : (opts.col != null ? opts.col : null),
      exception_type: opts.exception_type || (opts.error && opts.error.name) || null,
      extra: opts.extra || null,
      dom_state: opts.dom_state || null,
      design_mode: typeof window !== "undefined" && window._erpDesignMode === true,
      // Fix J Vrstva 5 (20.5. vecer): grid/form attribution z window context.
      // JS rows (info/warn/error) dostanou core_id + comp_def_id → fw.diag_log
      // → filter "vsechny errory pro core 22" v master gridu instant.
      core_id: opts.core_id != null
        ? opts.core_id
        : (typeof window !== "undefined" ? (window._erpActiveCoreId || null) : null),
      comp_def_id: opts.comp_def_id != null
        ? opts.comp_def_id
        : (typeof window !== "undefined" ? (window._erpActiveCompDefId || null) : null),
      ...((opts.overrides && typeof opts.overrides === "object") ? opts.overrides : {}),
    };

    // Layer 1: direct POST
    try {
      const r = await fetch("/api/v1/erp/diag-log/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event),
      });
      if (r.ok) {
        // Opportunistic drain (next tick, non-blocking)
        setTimeout(() => { _drainQueue().catch(() => {}); }, 0);
        try { return await r.json(); } catch (_) { return { ok: true }; }
      }
      // Backend rejected (4xx/5xx) — queue
      _queuePush(event);
      _scheduleBannerUpdate();
      return null;
    } catch (e) {
      // Network down or fetch threw — queue
      _queuePush(event);
      _scheduleBannerUpdate();
      return null;
    }
  }

  window._erpLogToDb = _logToDbImpl;
  window._erpLogToDb.info  = (mod, msg, opts) => _logToDbImpl("info",  mod, msg, opts);
  window._erpLogToDb.warn  = (mod, msg, opts) => _logToDbImpl("warn",  mod, msg, opts);
  window._erpLogToDb.error = (mod, msg, opts) => _logToDbImpl("error", mod, msg, opts);
  window._erpLogToDb.fatal = (mod, msg, opts) => _logToDbImpl("fatal", mod, msg, opts);
  window._erpLogToDb.drain = _drainQueue;
  window._erpLogToDb.queueSize = () => _queueGet().length;

  // ════════════════════════════════════════════════════════════════════
  // Fix L (21.5. rano) — global window.fetch wrapper pro Fix J header injection
  // ════════════════════════════════════════════════════════════════════
  // Marti's catch 21.5.: core_id NULL u Python error rows i po Fix K deploy.
  // Root cause: Fix J Vrstva 5 přidal X-Erp-Core-Id header jen do _apiCall()
  // v router.py inline JS. Ostatní fetch sites (page_render.js, datagrid.js)
  // volají raw fetch bez headeru → middleware contextvar=None → row.core_id=NULL.
  //
  // Fix: jednou zaregistrovat wrapper, který intercept VŠECHNY fetch calls
  // na /api/v1/erp/* a inject X-Erp-Core-Id + X-Erp-Comp-Def-Id z window state.
  // Same-origin scope (žádný cross-origin leak).
  //
  // Idempotent guard: pokud window.fetch už wrapped (re-load souboru), skip.
  if (!window._erpFetchWrappedV1) {
    window._erpFetchWrappedV1 = true;
    const _origFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
      try {
        const url = typeof input === "string"
          ? input
          : (input && input.url) || "";
        // Only inject pro ERP API calls (same-origin)
        if (url && url.indexOf("/api/v1/erp/") !== -1) {
          init = init || {};
          // Normalize headers do plain object (může být Headers instance)
          if (init.headers instanceof Headers) {
            const _h = {};
            init.headers.forEach((v, k) => { _h[k] = v; });
            init.headers = _h;
          } else if (!init.headers) {
            init.headers = {};
          }
          // Inject jen pokud caller nedal vlastní hodnotu
          const _coreId = window._erpActiveCoreId;
          if (_coreId !== undefined && _coreId !== null
              && init.headers["X-Erp-Core-Id"] === undefined) {
            init.headers["X-Erp-Core-Id"] = String(_coreId);
          }
          const _compDefId = window._erpActiveCompDefId;
          if (_compDefId !== undefined && _compDefId !== null
              && init.headers["X-Erp-Comp-Def-Id"] === undefined) {
            init.headers["X-Erp-Comp-Def-Id"] = String(_compDefId);
          }
        }
      } catch (_e) { /* never crash fetch */ }
      return _origFetch.call(this, input, init);
    };
  }

  // ════════════════════════════════════════════════════════════════════
  // _erpLoadModule — IIFE wrapper s mutual immunity
  // ════════════════════════════════════════════════════════════════════
  // Pattern:
  //   window._erpLoadModule('entity_picker.js', 'v1.0.0', function() {
  //     window.ErpEntityPicker = class { ... };
  //   });
  // Pri throw v fn: zaznamena se do health register + DB, ostatni moduly
  // se nacitaji dal. Doctrine: "zbytek bezi dale".
  window._erpLoadModule = function (id, version, fn) {
    if (!id || typeof fn !== "function") {
      console.error("[erp_module_kit] _erpLoadModule called with invalid args:", id, fn);
      return;
    }
    moduleHealth.register(id, version);
    try {
      fn();
      moduleHealth.markLoaded(id, version);
    } catch (e) {
      moduleHealth.markError(id, e);
      try {
        _logToDbImpl("error", id, "Module init failed: " + (e.message || String(e)), {
          stack: e.stack,
          exception_type: e.name,
          version: version,
          extra: { phase: "module_init" },
        });
      } catch (logErr) {
        try { console.error("[erp_module_kit] log on module init failed:", logErr); } catch (_) {}
      }
      try { console.error(`[erp_module_kit] Module '${id}' init failed:`, e); } catch (_) {}
      // No re-throw — mutual immunity. Subsequent modules continue.
    }
  };

  // ════════════════════════════════════════════════════════════════════
  // Global error handlers
  // ════════════════════════════════════════════════════════════════════
  window.addEventListener("error", function (e) {
    try {
      _logToDbImpl("error", "window.onerror",
        e.message || "Uncaught error", {
          stack: e.error && e.error.stack,
          exception_type: e.error && e.error.name,
          file_name: e.filename,
          line_number: e.lineno,
          column_number: e.colno,
          element: e.target,
        });
    } catch (ex) {
      try { console.error("[erp_module_kit] error handler failed:", ex); } catch (_) {}
    }
  });

  window.addEventListener("unhandledrejection", function (e) {
    try {
      const reason = e.reason;
      const msg = reason && reason.message ? reason.message : String(reason);
      _logToDbImpl("error", "unhandledrejection", msg, {
        stack: reason && reason.stack,
        exception_type: reason && reason.name,
      });
    } catch (ex) {
      try { console.error("[erp_module_kit] rejection handler failed:", ex); } catch (_) {}
    }
  });

  // ════════════════════════════════════════════════════════════════════
  // Diagnostic UI Banner (top-right pill)
  // ════════════════════════════════════════════════════════════════════
  let _banner = null;
  let _bannerTimer = null;

  function _scheduleBannerUpdate() {
    if (_bannerTimer) return;
    _bannerTimer = setTimeout(() => {
      _bannerTimer = null;
      _updateBanner();
    }, 150);
  }

  function _ensureBanner() {
    if (_banner) return _banner;
    if (!document.body) return null;
    _banner = document.createElement("div");
    _banner.id = "erpDiagBanner";
    // Marti's 24.5. drobnost: pod DEV badge (router.py erp-design-badge top:9px).
    // DEV badge je ~22px vysoký + 9px top => 31px. Posun na top:38px = ~7px gap.
    // right:16px zarovnání s DEV badge edge.
    _banner.style.cssText = [
      "position:fixed", "top:38px", "right:16px",
      "background:rgba(20,30,40,0.85)", "color:#cfd6dc",
      "padding:4px 10px", "border-radius:12px",
      "font-size:11px", "font-family:monospace",
      "cursor:pointer", "z-index:99999",
      "backdrop-filter:blur(4px)",
      "border:1px solid rgba(255,255,255,0.1)",
      "user-select:none", "transition:opacity 0.2s",
      "opacity:0.7"
    ].join(";");
    _banner.addEventListener("mouseenter", () => { _banner.style.opacity = "1"; });
    _banner.addEventListener("mouseleave", () => { _banner.style.opacity = "0.7"; });
    _banner.addEventListener("click", _showHealthModal);
    document.body.appendChild(_banner);
    return _banner;
  }

  function _updateBanner() {
    if (!document.body) {
      setTimeout(_updateBanner, 200);
      return;
    }
    const b = _ensureBanner();
    if (!b) return;
    const s = moduleHealth.stats();
    const queued = _queueGet().length;
    const icon = s.errors > 0 ? "🔴" : (queued > 0 ? "🟡" : "🟢");
    let txt = `${icon} ${s.loaded}/${s.total} mod`;
    if (s.errors > 0) txt += ` · ${s.errors} err`;
    if (queued > 0) txt += ` · ${queued} q`;
    b.textContent = txt;
    b.title =
      `${s.loaded} z ${s.total} modulu nacteno\n` +
      `${s.errors} chyb\n` +
      `${queued} eventu v offline fronte\n\n` +
      `Kliknout pro detail`;
  }

  function _showHealthModal() {
    const snap = moduleHealth.snapshot();
    const queued = _queueGet();
    const ids = Object.keys(snap).sort();
    let rowsHtml = "";
    for (const id of ids) {
      const m = snap[id];
      const sc = m.status === "error" ? "#e88" : (m.status === "loaded" ? "#8e8" : "#bbb");
      const errMsg = m.lastError && m.lastError.message
        ? String(m.lastError.message).slice(0, 80).replace(/[<>&]/g, c => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]))
        : "—";
      rowsHtml +=
        `<tr><td style="padding:4px;">${id}</td>` +
        `<td style="padding:4px;color:${sc};">${m.status}</td>` +
        `<td style="padding:4px;color:#999;">${m.version || "—"}</td>` +
        `<td style="padding:4px;color:#e88;">${errMsg}</td></tr>`;
    }
    const html = `
      <div style="font-family:monospace;font-size:12px;max-width:720px;width:80%;background:#1a242e;color:#cfd6dc;padding:14px;border-radius:8px;max-height:80vh;overflow:auto;">
        <div style="font-size:14px;margin-bottom:10px;border-bottom:1px solid #2a3540;padding-bottom:6px;">📊 ERP Module Health</div>
        <table style="width:100%;border-collapse:collapse;">
          <tr style="border-bottom:1px solid #2a3540;">
            <th style="text-align:left;padding:4px;">Module</th>
            <th style="text-align:left;padding:4px;">Status</th>
            <th style="text-align:left;padding:4px;">Version</th>
            <th style="text-align:left;padding:4px;">Last error</th>
          </tr>
          ${rowsHtml || '<tr><td colspan="4" style="padding:8px;color:#777;">(zatim zadne moduly registrovane)</td></tr>'}
        </table>
        <div style="margin-top:12px;font-size:11px;color:#aaa;">📤 Offline fronta: <b>${queued.length}</b> eventu (cap 100)</div>
        <div style="margin-top:12px;display:flex;gap:8px;">
          <button id="erpDiagFlush" style="background:#234;color:#cfd6dc;border:1px solid #345;padding:6px 12px;border-radius:4px;cursor:pointer;">🔄 Flush fronty</button>
          <button id="erpDiagClose" style="background:#234;color:#cfd6dc;border:1px solid #345;padding:6px 12px;border-radius:4px;cursor:pointer;">Zavrit</button>
        </div>
      </div>
    `;

    let modal = document.getElementById("erpDiagModal");
    if (modal) modal.remove();
    modal = document.createElement("div");
    modal.id = "erpDiagModal";
    modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:999999;display:flex;align-items:flex-start;justify-content:center;padding-top:60px;";
    modal.innerHTML = html;
    document.body.appendChild(modal);

    modal.querySelector("#erpDiagFlush") && modal.querySelector("#erpDiagFlush").addEventListener("click", async () => {
      const r = await _drainQueue();
      _scheduleBannerUpdate();
      alert(`Flush: ${r.drained} odeslano, ${r.remaining} zustava ve fronte.`);
      modal.remove();
    });
    modal.querySelector("#erpDiagClose") && modal.querySelector("#erpDiagClose").addEventListener("click", () => modal.remove());
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });
    // ESC close
    document.addEventListener("keydown", function escHandler(ev) {
      if (ev.key === "Escape") {
        modal.remove();
        document.removeEventListener("keydown", escHandler);
      }
    });
  }

  // ════════════════════════════════════════════════════════════════════
  // Periodic drain + initial setup
  // ════════════════════════════════════════════════════════════════════
  if (typeof setInterval === "function") {
    setInterval(() => {
      if (_queueGet().length > 0) {
        _drainQueue().catch(() => {});
      } else {
        _scheduleBannerUpdate();
      }
    }, 30000);
  }

  function _init() {
    _updateBanner();
    _drainQueue().catch(() => {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _init);
  } else {
    setTimeout(_init, 50);
  }

  // Self register (sanity)
  moduleHealth.register("erp_module_kit.js", "v1.0.0");
  moduleHealth.markLoaded("erp_module_kit.js", "v1.0.0");
})();
