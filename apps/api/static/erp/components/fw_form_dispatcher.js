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
      // Phase 38.4 Krok 14g Etapa F Step C (16.5.2026, Marti's "ID je svaty"):
      // DesignFwForm Step B accepts {coreId, rowId} (primary) OR {coreCode, rowId} (BC).
      // Auto-context: pass BOTH (Step B prefer coreId, fallback coreCode).
      const formArgs = {
        coreId: ctx.core_id || undefined,
        coreCode: ctx.core_code || undefined,
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
    // Open DesignFwForm s catch handler
    // ════════════════════════════════════════════════════════════════
    function _openForm(formArgs, cmiCode) {
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

      // Phase 38.4 Krok 14g Etapa F Step C: accept either coreId (primary) OR coreCode (BC)
      if (!formArgs.coreId && !formArgs.coreCode) {
        alert(
          "Custom item '" + (cmiCode || "?") +
          "': chybi coreId nebo coreCode.\n\n" +
          "Pridejte 'coreId' do action_params (preferred), napr:\n" +
          '{"coreId": "$core_id", "rowId": 1}\n\n' +
          "Nebo BC variant:\n" +
          '{"coreCode": "$core_code", "rowId": 1}\n\n' +
          "($core_id / $core_code resolvers picknou z DOM data-core-id / data-core-code)"
        );
        try {
          _logger.warn("fw_form_dispatcher.js",
            "coreId AND coreCode missing in action_params for cmi=" + cmiCode, {
              extra: { formArgs: formArgs },
            });
        } catch (e) {}
        return;
      }

      // Open FW form (data-driven render z fw.core + fw.comp_def)
      // Phase 38.4 Krok 14g Etapa F Step C: pass both coreId + coreCode.
      // Step B constructor: prefer coreId, fallback coreCode (warns BC).
      let modal;
      try {
        const ctorOpts = {
          rowId: formArgs.rowId || 1,
        };
        if (formArgs.coreId) ctorOpts.coreId = formArgs.coreId;
        if (formArgs.coreCode) ctorOpts.coreCode = formArgs.coreCode;
        modal = new global.DesignFwForm(ctorOpts);
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
      try {
        _logger.info("fw_form_dispatcher.js",
          "Dispatched FW form: " + formArgs.coreCode, {
            extra: {
              cmi_code: cmiCode,
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
      _openForm(formArgs, cmiSnap.code);
    };

  }); // _erpLoadModule end
})(window);
