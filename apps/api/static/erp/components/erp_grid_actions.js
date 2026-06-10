/* eslint-disable */
/**
 * erp_grid_actions.js — Universal CRUD action registry (Marti's 24.5.2026 vecer).
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * JEDEN truth source pro Nový/Oprava/Smazat/Obnovit napříč 3 vrstvy:
 *   1. AG Grid context menu (pravý klik na row)
 *   2. Grid header toolbar (Krok 5.Y location)
 *   3. Workspace mainscreen toolbar (Krok 5.S Fáze 6 location)
 *
 * Marti's doctrine: "zobrazovat stejne a stejne funkce k nim" — labels +
 * icons + handlers definované jen tady; konzumenti pull-them dle akce.
 *
 * Drží Marti's "fw self edited" doctrine (11.5.) — gridCode → editFormCoreId
 * mapping přes FW_EDIT_FORM_REGISTRY (per-entity edit form je fw.core row,
 * žádný hardcoded editor class per entita).
 *
 * Public API:
 *   window.ErpGridActions.get(actionKey) → ActionDef | null
 *   window.ErpGridActions.list(actionKeys) → ActionDef[] (in order)
 *   window.ErpGridActions.dispatch(actionKey, ctx) → Promise<void>
 *   window.ErpGridActions.registerEditForm(gridCode, coreId) — runtime override
 *
 * Action handler signature:
 *   handler(ctx = { gridCode, rowData?, gridApi?, refreshFn? }) → Promise<void>
 *
 * Drží Krok 5.O doctrine (jednotná class) — Nový/Oprava volají DesignFwForm
 * jako jediný entry point, ne power-tool editory.
 *
 * Wrapped v _erpLoadModule pattern (Module Health visibility).
 */
"use strict";

(function (global) {
  "use strict";

  var _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "]", e); } };

  _loader("erp_grid_actions.js", "v1.0.0", function () {

    // ════════════════════════════════════════════════════════════════════
    // FW_EDIT_FORM_REGISTRY — gridCode → editFormCoreId mapping.
    // Per-entity edit form = fw.core row, lookup přes /fw-core/{id}/page-spec.
    // Etapa D dnes seed pro framework_data_sources, ostatní postupně.
    // ════════════════════════════════════════════════════════════════════
    var FW_EDIT_FORM_REGISTRY = {
      // gridCode → coreId of edit form fw.core row
      // (Etapa D seed dnes: "system_new.framework_data_sources": <coreId>)
    };

    // ════════════════════════════════════════════════════════════════════
    // Helpers — internal
    // ════════════════════════════════════════════════════════════════════

    /** Najít editFormCoreId pro gridCode (registry lookup). */
    function _lookupEditFormCore(gridCode) {
      if (!gridCode) return null;
      return FW_EDIT_FORM_REGISTRY[gridCode] || null;
    }

    /** Open DesignFwForm (universal FW edit form, Marti's doctrine 17.5.). */
    function _openFwEditForm(gridCode, rowId, mode, onSaveCallback) {
      // Phase 38.4 Krok 5.X+1 Fix I (27.5.2026, Marti's "double clik
      // vyrendrovalo sami duplicitne"): re-open guard. Without guard,
      // double-click on parent grid row WHILE edit form already open
      // creates SECOND DesignFwForm instance → 2nd shell appended to
      // document.body → 2 overlapping modals → visual confusion (Marti's
      // "duplicate sections in same area" actually 2 modals stacked).
      // Detection via dataset marker designFwFormRoot=1 (set v open()
      // line 1134). Re-open → no-op + warn.
      var coreId = _lookupEditFormCore(gridCode);
      if (!coreId) {
        alert(
          "⚠ Edit form není nakonfigurován pro grid '" + gridCode + "'.\n\n" +
          "Pro povolení Nový/Oprava akcí musí být v fw.core seed-nut " +
          "edit form pro tuto entitu a registrován v " +
          "FW_EDIT_FORM_REGISTRY (erp_grid_actions.js).\n\n" +
          "Marti's doctrine: 'fw self edited' — žádný hardcoded editor."
        );
        return Promise.reject(new Error("no_edit_form_registered"));
      }
      // Smart re-open guard (31.5.2026, parita s DesignFwForm.open ř.~1346,
      // Marti's volba B = modal stack): blokuj JEN existing se STEJNYM coreId
      // (true double-click re-open). JINY coreId → allow (stacked modal — edit
      // form z nested gridu otevreny nad parent formem). Puvodni blanket guard
      // blokoval JAKYKOLIV otevreny form → nested grid CRUD "nereagoval na C/U".
      var _existingSame = document.querySelector(
        '[data-design-fw-form-root="1"][data-design-fw-form-core-id="' + coreId + '"]'
      );
      if (_existingSame) {
        console.warn(
          "[ErpGridActions] edit form coreId=" + coreId + " already open — ignore " +
          "re-open (gridCode=" + gridCode + ", rowId=" + rowId + "). Close it first."
        );
        return Promise.resolve();
      }
      if (typeof global.DesignFwForm !== "function") {
        alert("⚠ DesignFwForm komponenta není načtena.");
        return Promise.reject(new Error("designfwform_missing"));
      }
      try {
        var fwf = new global.DesignFwForm({
          coreId: coreId,
          rowId: rowId,
          mode: mode || (rowId ? "edit" : "create"),
          // Etapa F Krok 1+ (24.5.2026 vecer pozde, Marti's directive
          // "po editaci vety pres fw DesignFwGrid se pak da take refresh"):
          // FIX parameter name — DesignFwForm cte this.opts.onSaveSuccess
          // (design_forms.js:3419), ne onSave. Predtim silent drop.
          // Now: po PATCH success -> opts.onSaveSuccess(respData) -> onSaveCallback
          // -> ctx.refreshFn (z _wireCrudToolbar dispatch) -> smooth refresh
          // s locate restore (Krok 1 pattern).
          onSaveSuccess: function (respData) {
            if (typeof onSaveCallback === "function") {
              try { onSaveCallback(respData); } catch (e) {
                console.warn("[ErpGridActions] onSaveSuccess callback failed:", e);
              }
            }
          },
        });
        if (typeof fwf.open === "function") fwf.open();
        return Promise.resolve();
      } catch (e) {
        console.error("[ErpGridActions] DesignFwForm open failed:", e);
        alert("⚠ Otevření edit formuláře selhalo: " + (e.message || e));
        return Promise.reject(e);
      }
    }

    /** Hard delete via erp_batch_action (Marti's Q3=a hard delete).
     * Etapa F Fix 2 multi-row (24.5.2026 vecer Marti's catch "vcera jsme
     * rozchodili mazani vice vet"): preferred ctx.rowIds (array z getSelectedRows),
     * fallback ctx.rowData.id (single row backward compat).
     * ctx must include coreId (= page-spec core_id, used as source table
     * resolver in backend design_delete_entity handler).
     */
    function _hardDeleteRow(ctx) {
      var coreId = ctx.coreId;
      var refreshFn = ctx.refreshFn;
      // Etapa F Fix 2 multi-row — preferred rowIds array, fallback single rowData
      var rowIds = (Array.isArray(ctx.rowIds) && ctx.rowIds.length > 0)
        ? ctx.rowIds
        : (ctx.rowData && ctx.rowData.id != null ? [ctx.rowData.id] : []);
      if (rowIds.length === 0) {
        alert("⚠ Smazat: nejprve vyber řádek.");
        return Promise.reject(new Error("no_row_id"));
      }
      if (coreId == null) {
        alert("⚠ Smazat: chybí coreId v ctx (page_render.js musí passet).");
        return Promise.reject(new Error("no_core_id"));
      }
      if (typeof global._erpBatchRowAction !== "function") {
        alert("⚠ erp_batch_action.js není načten.");
        return Promise.reject(new Error("batch_action_missing"));
      }
      // Reuse Krok 5.X Mód 1 cyklicky per-row (sequential loop) + existing DELETE
      // endpoint /api/v1/erp/design/{core_id}/{row_id} (router.py:3585, Krok 5.W).
      // Marti's doctrine "stejne funkce" — same endpoint jako Krok 5.S Fáze 6
      // workspace toolbar Smazat, just routed přes registry. Multi-row drz
      // Marti's Centrala 1 19yr Mod 1 doctrine (cyklicky per-row, ne batch SQL).
      return global._erpBatchRowAction({
        rowIds: rowIds,
        opLabel: "Smazat",
        opVerb: "smazat",
        destructive: true,
        actionFn: function (rowId) {
          var url = "/api/v1/erp/design/" +
                    encodeURIComponent(coreId) + "/" +
                    encodeURIComponent(rowId);
          return fetch(url, {
            method: "DELETE",
            credentials: "include",
          }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (json) {
              if (r.ok && json && json.ok) return { ok: true };
              var errMsg = (json && json.error) || ("HTTP " + r.status);
              return { ok: false, error: errMsg };
            });
          }).catch(function (e) {
            return { ok: false, error: "network: " + (e && e.message || e) };
          });
        },
        refreshFn: refreshFn,
      });
    }

    /** Refresh grid via passed refreshFn (page_render.js zaregistruje). */
    function _refreshGrid(gridCode, refreshFn) {
      if (typeof refreshFn === "function") {
        try { refreshFn(); return Promise.resolve(); }
        catch (e) {
          console.error("[ErpGridActions] refresh failed:", e);
          return Promise.reject(e);
        }
      }
      console.warn("[ErpGridActions] refresh: no refreshFn provided pro", gridCode);
      return Promise.reject(new Error("no_refresh_fn"));
    }

    // ════════════════════════════════════════════════════════════════════
    // ACTION REGISTRY — single truth source
    // ════════════════════════════════════════════════════════════════════
    var ACTIONS = {
      // Marti's 30.5.2026 ranní doctrine: "Core setting" — universal
      // inspector pro fw.core metadata aktualniho core. Hardcoded
      // coreId=49 (existujici "Editace: Zeme" inspector core).
      // Klik: otevre DesignFwForm s coreId=49, rowId=current core_id.
      "core-setting": {
        key: "core-setting",
        icon: "⚙️",
        label: "Core setting",
        hint: "Inspector metadat aktuálního jádra (fw.core)",
        cssClass: "erp-action-core-setting",
        destructive: false,
        requiresRow: false,
        handler: function (ctx) {
          if (ctx.coreId == null) {
            alert("⚠ Core setting: chybí coreId v contextu (grid " +
                  (ctx.gridCode || "?") + ")");
            return Promise.reject(new Error("no_core_id"));
          }
          console.info("[Core setting · grid row context] open form 49 with rowId=" + ctx.coreId, ctx);
          try {
            var fwfCS = new DesignFwForm({ coreId: 49, rowId: ctx.coreId });
            if (typeof fwfCS.open === "function") fwfCS.open();
            return Promise.resolve();
          } catch (e) {
            console.error("[Core setting · grid row context] DesignFwForm failed:", e);
            return Promise.reject(e);
          }
        },
      },
      create: {
        key: "create",
        icon: "➕",
        label: "Nový",
        hint: "Vytvořit nový záznam (Insert)",
        cssClass: "erp-action-create",
        destructive: false,
        requiresRow: false,  // grid header / context menu i bez selected row
        handler: function (ctx) {
          return _openFwEditForm(
            ctx.gridCode, null, "create", ctx.refreshFn
          );
        },
      },
      edit: {
        key: "edit",
        icon: "✏️",
        label: "Oprava",
        hint: "Editovat vybraný záznam (Update)",
        cssClass: "erp-action-edit",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          // MSSQL/MCP data (Centrála 1) ma 'ID' uppercase, PG ma 'id' lowercase.
          // Tired-Marti UX (28.5.2026 #3): accept oboje (mirror cellFocused
          // listener v datagrid.js). Marti's catch — MSSQL gridy z MCP
          // connection vraci row keys v case-as-aliased (Centrala 1 SELECT
          // SELECT TOP (:limit) KA.ID, ...).
          var rowId = null;
          if (ctx.rowData) {
            rowId = ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID;
          }
          if (rowId == null) {
            alert("⚠ Oprava: nejprve vyber řádek.");
            return Promise.reject(new Error("no_row_selected"));
          }
          return _openFwEditForm(
            ctx.gridCode, rowId, "edit", ctx.refreshFn
          );
        },
      },
      delete: {
        key: "delete",
        icon: "🗑",
        label: "Smazat",
        hint: "Trvale smazat vybraný záznam (DELETE)",
        cssClass: "erp-action-delete",
        destructive: true,
        requiresRow: true,
        handler: function (ctx) {
          // MSSQL/MCP uppercase ID parity (viz edit handler vyse).
          var rowIdDel = null;
          if (ctx.rowData) {
            rowIdDel = ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID;
          }
          if (rowIdDel == null) {
            alert("⚠ Smazat: nejprve vyber řádek.");
            return Promise.reject(new Error("no_row_selected"));
          }
          return _hardDeleteRow(ctx);
        },
      },
      refresh: {
        key: "refresh",
        icon: "🔄",
        label: "Obnovit",
        hint: "Načíst grid znovu (Refresh)",
        cssClass: "erp-action-refresh",
        destructive: false,
        requiresRow: false,
        handler: function (ctx) {
          return _refreshGrid(ctx.gridCode, ctx.refreshFn);
        },
      },
      // Personální dokumenty na klik (Marti 10.6.2026). Jen na Finance lidí
      // gridu (page_render gate hr_finance_lidi). Řádek = engagement → id.
      // Malý chooser → /api/v1/erp/employee-doc?engagement_id=&typ=.
      doc: {
        key: "doc",
        icon: "📄",
        label: "Dokumenty",
        hint: "Vygenerovat personální dokument (smlouva / výměr / popis / DPP)",
        cssClass: "erp-action-doc",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          var rid = ctx.rowData ? (ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID) : null;
          if (rid == null) {
            alert("⚠ Dokumenty: nejprve vyber zaměstnance v přehledu.");
            return Promise.reject(new Error("no_row_selected"));
          }
          var ex = document.getElementById("erpDocChooser");
          if (ex) ex.remove();
          var box = document.createElement("div");
          box.id = "erpDocChooser";
          box.style.cssText = "position:fixed;z-index:99999;right:24px;bottom:24px;background:#fff;border:1px solid #1F4E78;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.25);padding:14px 16px;font-family:Verdana,Arial,sans-serif;min-width:240px;";
          var h = document.createElement("div");
          h.textContent = "📄 Generovat dokument";
          h.style.cssText = "font-weight:bold;color:#1F4E78;margin-bottom:8px;";
          box.appendChild(h);
          [["smlouva", "Pracovní smlouva"], ["vymer", "Mzdový výměr"],
           ["popis", "Popis pracovního místa"], ["dpp", "Dohoda o provedení práce (DPP)"]
          ].forEach(function (t) {
            var b = document.createElement("button");
            b.textContent = t[1];
            b.style.cssText = "display:block;width:100%;text-align:left;margin:4px 0;padding:7px 10px;border:1px solid #ccc;border-radius:6px;background:#f5f8fb;cursor:pointer;font-family:inherit;font-size:13px;";
            b.onclick = function () {
              window.open("/api/v1/erp/employee-doc?engagement_id=" + encodeURIComponent(rid) + "&typ=" + t[0], "_blank");
            };
            box.appendChild(b);
          });
          var c = document.createElement("button");
          c.textContent = "Zavřít";
          c.style.cssText = "margin-top:6px;padding:5px 10px;border:none;background:transparent;color:#888;cursor:pointer;";
          c.onclick = function () { box.remove(); };
          box.appendChild(c);
          document.body.appendChild(box);
          return Promise.resolve();
        },
      },
      // Graf pipeline (Marti 3.6.2026 — prezentace IT šéfům): vizualizace
      // pipeline jako naskládané akční karty (ErpActionCard). Jen na pipeline
      // gridu (page_render gate). Ref = pipeline code (fallback id).
      graph: {
        key: "graph",
        icon: "📊",
        label: "Graf pipeline",
        hint: "Vizuální přehled kroků pipeline (akční karty pod sebe)",
        cssClass: "erp-action-graph",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          var ref = null;
          if (ctx.rowData) {
            ref = ctx.rowData.code || ctx.rowData.id || ctx.rowData.ID || null;
          }
          if (ref == null) {
            alert("⚠ Graf: nejprve vyber pipeline.");
            return Promise.reject(new Error("no_pipeline_ref"));
          }
          if (typeof global.openPipelineGraph !== "function") {
            alert("⚠ Graf komponenta (action_card.js) není načtena.");
            return Promise.reject(new Error("graph_component_missing"));
          }
          global.openPipelineGraph(ref);
          return Promise.resolve();
        },
      },
    };

    // ════════════════════════════════════════════════════════════════════
    // Public API
    // ════════════════════════════════════════════════════════════════════
    global.ErpGridActions = {
      /** Get single action def by key (returns null if unknown). */
      get: function (key) { return ACTIONS[key] || null; },

      /** Get array of action defs for given keys (preserves order, skips unknowns). */
      list: function (keys) {
        if (!Array.isArray(keys)) return [];
        return keys
          .map(function (k) { return ACTIONS[k]; })
          .filter(function (a) { return !!a; });
      },

      /** Dispatch action by key with ctx={gridCode, rowData?, refreshFn?}. */
      dispatch: function (key, ctx) {
        var action = ACTIONS[key];
        if (!action) {
          console.warn("[ErpGridActions] unknown action key:", key);
          return Promise.reject(new Error("unknown_action: " + key));
        }
        ctx = ctx || {};
        return action.handler(ctx);
      },

      /** Register edit form coreId pro gridCode (runtime override / seed). */
      registerEditForm: function (gridCode, coreId) {
        if (!gridCode || coreId == null) {
          console.warn("[ErpGridActions] registerEditForm: invalid args",
                       gridCode, coreId);
          return;
        }
        FW_EDIT_FORM_REGISTRY[gridCode] = coreId;
        console.info("[ErpGridActions] registered edit form: " +
                     gridCode + " → coreId=" + coreId);
      },

      /** Read-only view of registry (pro debug). */
      _registry: FW_EDIT_FORM_REGISTRY,
    };

    console.log("[ErpGridActions] registered (v1.0.0) — actions:",
                Object.keys(ACTIONS).join(", "));
  });
})(window);
