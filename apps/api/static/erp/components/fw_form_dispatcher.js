/* eslint-disable */
/**
 * Phase 38.4 Krok 14g-H+33 Etapa 2.2 v2 — FW Form Dispatcher (16.5.2026).
 *
 * Marti's vize z 15.5. večer: *„potrebuju ten muj mit fw, nikoli hardcoded,
 * tj, zacit jej stavet od nuly"* — dispatcher pro custom context menu items
 * (fw.context_menu_item registry) otevírá DesignFwForm (data-driven render
 * z fw.core + fw.comp_def) místo DesignSoudecekCoreForm (hardcoded JS class).
 *
 * **Etapa 2.2 v1 (commit 32ab57b, 15.5. večer):** inline JS v Python triple-
 * quoted HTML template → JS syntax error rendered line 5581:33 → revert
 * `git revert HEAD` na Etapu 2.1.
 *
 * **Etapa 2.2 v2 (16.5. — toto):** samostatný JS soubor s _erpLoadModule wrap
 * (mutual immunity), node --check validation pred deploy, integrated
 * _erpLogToDb pro dispatch event logging.
 *
 * Architektura:
 *   - $resolver pattern (z Etapy 2.1 preserved): `$menu_node_pk`,
 *     `$menu_node_code`, `$core_id`, `$core_code` v action_params
 *   - BC alias `form_core_code` → `coreCode` (Marti's existing test items)
 *   - Auto-context defaults: `{coreCode, rowId: 1}`
 *   - Validate coreCode required → alert s helpful message
 *   - Catch DesignFwForm.open() failures → alert + log do fw.diag_log
 *
 * Public API:
 *   window.dispatchFwFormFromContextMenu(cmiSnap, item, mnPk, mnCode)
 *     cmiSnap   — context menu item snapshot (z fw.context_menu_item row)
 *     item      — DOM element (.erp-tree-item nebo .ag-row, source pro ctx)
 *     mnPk      — menu_node primary key (z data-menu-node-pk)
 *     mnCode    — menu_node code (z data-id)
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

  _loader("fw_form_dispatcher.js", "v1.0.0", function () {

    // ════════════════════════════════════════════════════════════════
    // Build dispatch context z DOM item dataset
    // ════════════════════════════════════════════════════════════════
    function _buildContext(item, mnPk, mnCode) {
      // mnPk/mnCode pochazi z item.getAttribute("data-menu-node-pk")/"data-id"
      // (predane volajicim, drzi closure-safe i kdyby item zmenil node mezi
      // contextmenu open a klik na custom item)
      let coreId = null;
      let coreCode = null;
      try {
        const v = item ? item.getAttribute("data-core-id") : null;
        if (v) coreId = parseInt(v, 10);
        coreCode = item ? item.getAttribute("data-core-code") : null;
      } catch (e) {
        // item DOM gone — fail-safe, vrat partial ctx
      }
      return {
        menu_node_pk: mnPk ? parseInt(mnPk, 10) : null,
        menu_node_code: mnCode || null,
        core_id: coreId,
        core_code: coreCode || null,
      };
    }

    // ════════════════════════════════════════════════════════════════
    // Resolve action_params s $resolver pattern + BC alias
    // ════════════════════════════════════════════════════════════════
    function _resolveFormArgs(actionParams, ctx) {
      // Phase 38.4 Krok 14g Etapa F Krok 5.A cleanup pokracovani (16.5.2026
      // odpoledne, Marti's "zase dosazuje bludy"): DROP ctx.core_id fallback.
      // coreId MUSI byt EXPLICIT v action_params (z target_core_id FK
      // serializer slije target_core_id → action_params.coreId v backend).
      // Pokud action_params nema coreId → formArgs.coreId zustane undefined
      // → dispatcher otevre Kontejner picker (Krok 5.B) misto silent
      // fallback na DOM core_id (ktery vedl k otevirani random core formu).
      //
      // Marti's doctrine: "coreId = null nebo 0 misto silent dosazeni".
      const formArgs = {
        coreId: undefined,
        rowId: 1, // default — DesignFwForm requires non-null row
      };

      const ap = actionParams || {};
      for (const [key, val] of Object.entries(ap)) {
        // BC alias z Etapy 2: form_core_code → coreCode
        const targetKey = (key === "form_core_code") ? "coreCode" : key;

        if (typeof val === "string" && val.startsWith("$")) {
          // Dynamic resolver: $sourceField → ctx[sourceField]
          const sourceKey = val.substring(1);
          if (Object.prototype.hasOwnProperty.call(ctx, sourceKey)) {
            formArgs[targetKey] = ctx[sourceKey];
          } else {
            console.warn(
              "[fw_form_dispatcher] unknown source '" + val +
              "' v action_params['" + key + "'] — " +
              "dostupne: " + Object.keys(ctx).join(", ")
            );
            // Log warning to fw.diag_log
            try {
              _logger.warn("fw_form_dispatcher.js",
                "Unknown $source resolver: " + val, {
                  extra: { key: key, available_sources: Object.keys(ctx) },
                });
            } catch (e) {}
            formArgs[targetKey] = null;
          }
        } else {
          // Static value
          formArgs[targetKey] = val;
        }
      }
      return formArgs;
    }

    // ════════════════════════════════════════════════════════════════
    // Diag log (DESIGN mode only — console.info trace)
    // ════════════════════════════════════════════════════════════════
    function _diagLog(actionParams, ctx, formArgs) {
      if (global._erpDesignMode !== true) return;
      try {
        console.info(
          "[fw_form_dispatcher] action_params:", actionParams,
          "ctx:", ctx,
          "resolved formArgs:", formArgs
        );
      } catch (e) {}
    }

    // ════════════════════════════════════════════════════════════════
    // Open DesignFwForm — pure dispatch, no validation
    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g Etapa F Krok 5.A cleanup (16.5.2026): drop Step E.2
    // expectedCoreCode pre-validation block (~85 radku) + drop async wrapper.
    // Po Krok 3 (target_core_id FK na fw.core(id) ON DELETE RESTRICT) +
    // Krok 4 (drop expectedCoreCode z action_params) je validation redundantni:
    //   - FK constraint zaruci ze coreId pointuje na existing fw.core row
    //   - $resolver pro rowId je dynamic (current node's core_id), coreId
    //     je STATIC z target_core_id FK → mismatch nemuze nastat
    //   - Marti's "ID je svaty" doctrine: ID-based truth > code-based check
    function _openForm(formArgs, cmiCode, ctx, cmiId) {
      if (typeof global.DesignFwForm !== "function") {
        alert("DesignFwForm not loaded (design_forms.js missing or older verze).");
        try {
          _logger.error("fw_form_dispatcher.js",
            "DesignFwForm class not on window", {
              extra: { cmi_code: cmiCode },
            });
        } catch (e) {}
        return;
      }

      // Phase 38.4 Krok 14g Etapa F Krok 5.B (16.5.2026 odpoledne, Marti's
      // "nejdrive vybrat existing CORE kontejner, nebo vytvorit novy"):
      // Pokud coreId chybi (cmi.target_core_id=NULL + zadny coreId v
      // action_params), otevri Kontejner picker. Uzivatel bud:
      //   1) Vybere existing fw.core ze seznamu → recurse _openForm
      //   2) Klikne ➕ Nový → wizard pro INSERT noveho core (Krok 5.C,
      //      cekajici na konzultaci s Marti-AI)
      //
      // Marti's doctrine "coreId = null misto silent fallback na DOM ctx".
      if (!formArgs.coreId) {
        if (typeof global.ErpCatalogPicker !== "function") {
          alert("ErpCatalogPicker not loaded (catalog_picker.js missing).");
          try {
            _logger.error("fw_form_dispatcher.js",
              "ErpCatalogPicker class not on window — pro Krok 5.B picker", {
                extra: { cmi_code: cmiCode },
              });
          } catch (e) {}
          return;
        }
        try {
          _logger.info("fw_form_dispatcher.js",
            "Opening Kontejner picker (no coreId in action_params)", {
              extra: { cmi_code: cmiCode, formArgs: formArgs },
            });
        } catch (e) {}
        const _picker = new global.ErpCatalogPicker({
          title: "📋 Vybrat CORE kontejner pro '" + (cmiCode || "?") + "'",
          endpoint: "/api/v1/erp/design/fw-core/list",
          listKey: "cores",
          columns: [
            { headerName: "ID", field: "id", width: 70 },
            { headerName: "Code", field: "code", width: 240 },
            { headerName: "Label", field: "label", flex: 1 },
            { headerName: "Layout", field: "layout_type", width: 100 },
            { headerName: "Použito ×", field: "is_used_count", width: 100, type: "numericColumn" },
          ],
          idField: "id",
          labelField: "label",
          width: "1000px",
          enableNew: true,
          onSelect: function (row) {
            // Recurse s explicit coreId — projde guard above (coreId != undefined)
            _openForm(
              { coreId: row.id, rowId: formArgs.rowId || 1 },
              cmiCode, ctx, cmiId
            );
          },
          onNew: async function () {
            // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026, Marti's
            // "minimum parametru, pojmenovavat nic je k nicemu"): POST
            // create-minimal s origin tracking → recurse open form pro
            // novy drafted core.
            try {
              const _resp = await fetch(
                "/api/v1/erp/design/fw-core/create-minimal",
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({
                    origin_menu_node_id: (ctx && ctx.menu_node_pk) || null,
                    origin_cmi_id: cmiId || null,
                  }),
                }
              ).then(function (r) { return r.json(); });
              if (_resp && _resp.ok && _resp.core && _resp.core.id) {
                try {
                  _logger.info("fw_form_dispatcher.js",
                    "Created minimal fw.core draft id=" + _resp.core.id, {
                      extra: {
                        cmi_code: cmiCode,
                        cmi_id: cmiId,
                        origin_menu_node_id: (ctx && ctx.menu_node_pk) || null,
                        new_core_id: _resp.core.id,
                      },
                    });
                } catch (e) {}
                // Zavri picker pred recurse (DesignFwForm modal otevre se v overlay)
                try { _picker.close(); } catch (e) {}
                // Recurse — open Design form pro novy drafted core
                _openForm(
                  { coreId: _resp.core.id, rowId: 1 },
                  cmiCode, ctx, cmiId
                );
              } else {
                alert(
                  "Vytvoreni draftu selhalo: " +
                  ((_resp && _resp.error) || "unknown error")
                );
              }
            } catch (e) {
              alert("Vytvoreni draftu (network): " + (e.message || e));
            }
          },
        });
        _picker.open();
        return;
      }

      // Open FW form (data-driven render z fw.core + fw.comp_def)
      // Phase 38.4 Krok 14g Etapa F Step E.1: pass coreId only (drop coreCode BC).
      // Constructor requires coreId, open() lazy-resolves coreCode internally.
      let modal;
      try {
        modal = new global.DesignFwForm({
          coreId: formArgs.coreId,
          rowId: formArgs.rowId || 1,
        });
      } catch (e) {
        console.error("[fw_form_dispatcher] DesignFwForm constructor failed:", e);
        alert("Inicializace FW formu selhala: " + (e.message || e));
        try {
          _logger.error("fw_form_dispatcher.js",
            "DesignFwForm constructor threw: " + (e.message || String(e)), {
              stack: e.stack,
              exception_type: e.name,
              extra: { coreCode: formArgs.coreCode, rowId: formArgs.rowId },
            });
        } catch (logErr) {}
        return;
      }

      const _openPromise = modal.open();
      if (_openPromise && typeof _openPromise.catch === "function") {
        _openPromise.catch(function (e) {
          console.error("[fw_form_dispatcher] DesignFwForm.open failed:", e);
          alert(
            "Otevreni FW formu '" + formArgs.coreCode +
            "' selhalo:\n" + (e && e.message ? e.message : e) +
            "\n\nMozne priciny:\n" +
            "1. fw.core ma layout_type != 'form' (potreba ALTER nebo " +
            "scaffold form template)\n" +
            "2. Endpoint /api/v1/erp/fw-form/{code}/{rowId} vratil 404 " +
            "(form_core nenalezen)\n\n" +
            "Pouzij Design akci pro scaffold form template."
          );
          try {
            _logger.error("fw_form_dispatcher.js",
              "DesignFwForm.open rejected: " + (e && e.message ? e.message : String(e)), {
                stack: e && e.stack,
                exception_type: e && e.name,
                extra: { coreCode: formArgs.coreCode, rowId: formArgs.rowId },
              });
          } catch (logErr) {}
        });
      }

      // Success log (info level)
      // Phase 38.4 Krok 14g Etapa F Step C.1 (16.5.2026): label includes coreId
      // when coreCode unavailable (coreId-primary dispatch path). Pre-fix logged
      // "Dispatched FW form: undefined" pro coreId-only callers.
      try {
        const _coreLabel = formArgs.coreCode
          ? formArgs.coreCode
          : (formArgs.coreId ? ("id=" + formArgs.coreId) : "(unknown)");
        _logger.info("fw_form_dispatcher.js",
          "Dispatched FW form: " + _coreLabel, {
            extra: {
              cmi_code: cmiCode,
              coreId: formArgs.coreId,
              coreCode: formArgs.coreCode,
              rowId: formArgs.rowId,
            },
          });
      } catch (e) {}
    }

    // ════════════════════════════════════════════════════════════════
    // Public API
    // ════════════════════════════════════════════════════════════════
    /**
     * Main entry point — volaný z router.py inline contextmenu handler.
     *
     * @param {Object} cmiSnap   — Snapshot z fw.context_menu_item row
     *                              (closure-safe — menu se moze prebuilt)
     * @param {Element} item     — DOM element (.erp-tree-item / .ag-row)
     * @param {string} mnPk      — menu_node primary key (data-menu-node-pk)
     * @param {string} mnCode    — menu_node code (data-id)
     */
    global.dispatchFwFormFromContextMenu = function (cmiSnap, item, mnPk, mnCode) {
      if (!cmiSnap || typeof cmiSnap !== "object") {
        console.error("[fw_form_dispatcher] dispatch called with invalid cmiSnap:", cmiSnap);
        return;
      }

      const ctx = _buildContext(item, mnPk, mnCode);
      const formArgs = _resolveFormArgs(cmiSnap.action_params, ctx);
      _diagLog(cmiSnap.action_params, ctx, formArgs);
      // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026): pass ctx + cmiSnap.id
      // pro Kontejner picker onNew callback (origin tracking pri minimal INSERT
      // do fw.core — Marti's "rodicovstvi" doctrine).
      _openForm(formArgs, cmiSnap.code, ctx, cmiSnap.id);
    };

  }); // _erpLoadModule end
})(window);
