/* eslint-disable */
/**
 * Phase 38.4 Krok 14g — Etapa D+1 (16.5.2026 dop.) — ERP Grid Dispatcher.
 *
 * Marti's request: *„rozdelit na dalsi JS a zalogovat"* — extrahuje
 * dispatch logiku (mode → URL → rows) z inline router.py HTML template
 * do samostatného modulu s _erpLogToDb event logging pres každý krok.
 *
 * Architecture (3-tier dispatch, replicates router.py inline pattern):
 *   1. /api/v1/erp/hw/{code} — hw_registry primary (A3 LIVE or delegate_url)
 *   2. /api/v1/erp/system/security|framework|audit-overview — legacy fallback
 *   3. Throws Error if all fail (caller renders error message)
 *
 * Each step logs to fw.diag_log via _erpLogToDb:
 *   - info: "Dispatching mode=X, code=Y"
 *   - info: "hw_registry response: rows=N OR delegate_url=Z"
 *   - warn: "hw_registry 404 / parse error → falling to legacy"
 *   - error: "legacy fetch failed with HTTP S"
 *
 * Public API:
 *   window.dispatchGridData(mode) → Promise<rows[]>
 *     mode: string like "security_users", "framework_menu_nodes", "diag_log_master"
 *     Resolves with array of row dicts (může být prázdné).
 *     Rejects s Error pri všech 3 selhání (legacy + hw + parse).
 */

"use strict";

(function (global) {
  "use strict";

  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  const _logger = (typeof global !== "undefined" && global._erpLogToDb)
    ? global._erpLogToDb
    : { info: () => {}, warn: () => {}, error: () => {} };

  _loader("erp_grid_dispatcher.js", "v1.0.0", function () {

    const MODULE_ID = "erp_grid_dispatcher.js";

    // ════════════════════════════════════════════════════════════
    // mode → hw_registry code mapping
    // ════════════════════════════════════════════════════════════
    //   Audit modes (audited/all/stats) → "audit_<mode>"
    //   security_* / framework_* → as-is
    //   diag_log_master / others → as-is
    function _modeToHwCode(mode) {
      if (mode === "audited" || mode === "all" || mode === "stats") {
        return "audit_" + mode;
      }
      // security_*, framework_*, diag_log_master, etc. → as-is
      return mode;
    }

    // ════════════════════════════════════════════════════════════
    // Layer 1: hw_registry dispatch (primary)
    // ════════════════════════════════════════════════════════════
    async function _tryHwRegistry(mode, code) {
      try {
        const r = await fetch("/api/v1/erp/hw/" + encodeURIComponent(code),
          { credentials: "include", cache: "no-store" });
        if (!r.ok) {
          // 404 expected pro modes bez hw_registry entry — fall through
          _logger.info(MODULE_ID,
            "hw_registry " + r.status + " for code=" + code + " — fall through to legacy", {
              extra: { mode, hw_code: code, http_status: r.status },
            });
          return null;
        }
        const d = await r.json();
        if (!d || !d.ok) {
          _logger.warn(MODULE_ID,
            "hw_registry response not ok for code=" + code, {
              extra: { mode, hw_code: code, response: d },
            });
          return null;
        }

        // A3 primary — rows direct v response
        if (Array.isArray(d.rows)) {
          _logger.info(MODULE_ID,
            "hw_registry A3 primary returned " + d.rows.length + " rows for code=" + code, {
              extra: { mode, hw_code: code, row_count: d.rows.length },
            });
          return d.rows;
        }

        // hw_off / hw_audit / hw_compare — follow delegate_url
        if (d.delegate_url) {
          _logger.info(MODULE_ID,
            "hw_registry delegate_url for code=" + code + ": " + d.delegate_url, {
              extra: { mode, hw_code: code, delegate_url: d.delegate_url },
            });
          const rd = await fetch(d.delegate_url,
            { credentials: "include", cache: "no-store" });
          if (!rd.ok) {
            _logger.error(MODULE_ID,
              "delegate_url fetch failed " + rd.status + " for " + d.delegate_url, {
                extra: { mode, hw_code: code, delegate_url: d.delegate_url, http_status: rd.status },
              });
            return null;
          }
          const dd = await rd.json();
          // Pres response_hint: extract rows. Common keys: rows, events, conversations
          // Backend nemá JSONPath resolver v JS, jen tryneme známé keys.
          const rows = dd.rows || dd.events || dd.conversations || [];
          _logger.info(MODULE_ID,
            "delegate_url returned " + rows.length + " rows from " + d.delegate_url, {
              extra: { mode, hw_code: code, delegate_url: d.delegate_url, row_count: rows.length },
            });
          return rows;
        }

        _logger.warn(MODULE_ID,
          "hw_registry response has neither rows nor delegate_url for code=" + code, {
            extra: { mode, hw_code: code, response_keys: Object.keys(d) },
          });
        return null;
      } catch (e) {
        _logger.error(MODULE_ID,
          "hw_registry network error for code=" + code + ": " + (e.message || String(e)), {
            stack: e.stack,
            exception_type: e.name,
            extra: { mode, hw_code: code },
          });
        return null;
      }
    }

    // ════════════════════════════════════════════════════════════
    // Layer 2: Legacy hardcoded dispatch (fallback)
    // ════════════════════════════════════════════════════════════
    function _legacyUrl(mode) {
      if (mode.indexOf("security_") === 0) {
        return "/api/v1/erp/system/security?mode=" + encodeURIComponent(mode.substring(9));
      } else if (mode.indexOf("framework_") === 0) {
        return "/api/v1/erp/system/framework?mode=" + encodeURIComponent(mode.substring(10));
      } else {
        return "/api/v1/erp/system/audit-overview?mode=" + encodeURIComponent(mode);
      }
    }

    async function _tryLegacy(mode) {
      const url = _legacyUrl(mode);
      _logger.info(MODULE_ID,
        "Legacy fallback dispatch: " + url, {
          extra: { mode, legacy_url: url },
        });
      try {
        const res = await fetch(url, { credentials: "include", cache: "no-store" });
        if (!res.ok) {
          const errMsg = "HTTP " + res.status + " from " + url;
          _logger.error(MODULE_ID,
            "Legacy dispatch failed: " + errMsg, {
              extra: { mode, legacy_url: url, http_status: res.status },
            });
          throw new Error(errMsg);
        }
        const data = await res.json();
        const rows = data.rows || data.conversations || data.events || [];
        _logger.info(MODULE_ID,
          "Legacy dispatch returned " + rows.length + " rows from " + url, {
            extra: { mode, legacy_url: url, row_count: rows.length },
          });
        return rows;
      } catch (e) {
        if (!(e instanceof Error) || !e.message.startsWith("HTTP ")) {
          // Network / parse error (already logged HTTP above if got response)
          _logger.error(MODULE_ID,
            "Legacy dispatch network/parse error: " + (e.message || String(e)), {
              stack: e.stack,
              exception_type: e.name,
              extra: { mode, legacy_url: url },
            });
        }
        throw e;  // propagate to caller
      }
    }

    // ════════════════════════════════════════════════════════════
    // Public API: dispatchGridData(mode) → Promise<rows[]>
    // ════════════════════════════════════════════════════════════
    global.dispatchGridData = async function (mode) {
      if (!mode || typeof mode !== "string") {
        const err = new Error("dispatchGridData: invalid mode (must be non-empty string)");
        _logger.error(MODULE_ID, err.message, { extra: { mode: mode } });
        throw err;
      }

      // Fix J Vrstva 5 (20.5. vecer): reset comp_def_id pri grid open
      // (grid context nema komponentu — comp_def je relevant jen pro form
      // fields). core_id nastavuje dispatchPageRender PRED tim, tady jen clear.
      try {
        global._erpActiveCompDefId = null;
      } catch (_e) { /* never crash dispatcher */ }

      const hwCode = _modeToHwCode(mode);
      _logger.info(MODULE_ID,
        "dispatchGridData start: mode=" + mode + ", hw_code=" + hwCode, {
          extra: { mode, hw_code: hwCode },
        });

      // Layer 1: try hw_registry
      const hwRows = await _tryHwRegistry(mode, hwCode);
      if (hwRows !== null) {
        return hwRows;
      }

      // Layer 2: legacy fallback
      return await _tryLegacy(mode);
    };

    // Expose helpers pro testing
    global.dispatchGridData._modeToHwCode = _modeToHwCode;
    global.dispatchGridData._legacyUrl = _legacyUrl;

  }); // _erpLoadModule end
})(window);
