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

    // DB-řízená vazba (Kristý 10.7.2026): registr se při loadu naseeduje z
    // fw.edit_form_binding přes GET /edit-form-binding/all. Statické záznamy
    // výše mají přednost (override). Tím jde jádro navázat na přehled za běhu
    // (import z Centrály zapíše vazbu) bez editace tohoto souboru.
    // Přídavné + tolerantní: když endpoint/tabulka chybí, registr zůstane
    // prázdný = chování jako dosud.
    var _EFB_SEEDED = false;
    function _seedEditFormRegistryFromDb() {
      if (_EFB_SEEDED) return Promise.resolve();
      _EFB_SEEDED = true;
      return fetch("/api/v1/erp/edit-form-binding/all", { credentials: "include" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          var b = d && d.bindings;
          if (!b || typeof b !== "object") return;
          Object.keys(b).forEach(function (gridCode) {
            // statický záznam (ruční override) NEpřepisujeme
            if (FW_EDIT_FORM_REGISTRY[gridCode] == null) {
              FW_EDIT_FORM_REGISTRY[gridCode] = b[gridCode];
            }
          });
        })
        .catch(function (e) {
          // best-effort; registr zůstane jak je (fallback = dnešní chování)
          try { console.warn("[ErpGridActions] edit-form-binding seed skip:", e); } catch (_e) {}
        });
    }
    // seed hned při načtení modulu (async, neblokuje)
    try { _seedEditFormRegistryFromDb(); } catch (_e) {}

    // ════════════════════════════════════════════════════════════════════
    // Helpers — internal
    // ════════════════════════════════════════════════════════════════════

    /** Najít editFormCoreId pro gridCode (registry lookup). */
    function _lookupEditFormCore(gridCode) {
      if (!gridCode) return null;
      return FW_EDIT_FORM_REGISTRY[gridCode] || null;
    }

    /** Open DesignFwForm (universal FW edit form, Marti's doctrine 17.5.). */
    function _openFwEditForm(gridCode, rowId, mode, onSaveCallback, extra) {
      // extra (Kristy 26.6.2026, CRM Akce routing):
      //   overrideCoreId — otevri konkretni edit jadro (misto registry lookup);
      //                    CRM Akce routuje podle typu akce / IDAkce zaznamu.
      //   injectValues   — hodnoty primichane do field_changes pri CREATE
      //                    (IDHlav firmy + IDAkce zvolene akce -> insert).
      extra = extra || {};
      // Phase 38.4 Krok 5.X+1 Fix I (27.5.2026, Marti's "double clik
      // vyrendrovalo sami duplicitne"): re-open guard. Without guard,
      // double-click on parent grid row WHILE edit form already open
      // creates SECOND DesignFwForm instance → 2nd shell appended to
      // document.body → 2 overlapping modals → visual confusion (Marti's
      // "duplicate sections in same area" actually 2 modals stacked).
      // Detection via dataset marker designFwFormRoot=1 (set v open()
      // line 1134). Re-open → no-op + warn.
      var coreId = (extra.overrideCoreId != null)
        ? extra.overrideCoreId : _lookupEditFormCore(gridCode);
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

      // Data-driven detail (Kristy 14.7.2026): pokud pro toto jadro existuje
      // definice ve fw.centrala_form_spec, otevri data-driven detail IN-PLACE
      // misto fw.* formulare. Gated + try/catch fallback (bez specu / pri chybe
      // pokracuje puvodni DesignFwForm).
      try {
        if (!extra.forceLegacy && global.ErpSpecForm && global.ErpSpecForm.hasCore(coreId)) {
          if (global.ErpSpecForm.tryOpen({ coreId: coreId, rowId: rowId, mode: mode, gridCode: gridCode })) {
            return Promise.resolve();
          }
        }
      } catch (_esfErr) {
        try { console.warn("[ErpGridActions] ErpSpecForm fallback:", _esfErr); } catch (e) {}
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
          // CRM Akce: seed IDHlav + IDAkce do field_changes pri CREATE.
          injectValues: extra.injectValues || null,
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

    // ════════════════════════════════════════════════════════════════
    // CRM Akce — picker typu akce + routing na edit jadro (Kristy 26.6.2026).
    // Grid 'grid_crm_akce' (sub-grid v karte zakaznika). 'Novy' otevre picker
    // typu akce; podle IDAkce se otevre prislusne edit jadro (default 82) se
    // seedem IDHlav (firma) + IDAkce. Edit existujiciho zaznamu routuje stejne
    // podle jeho IDAkce. Mapovani akce->jadro je config-driven (backend
    // /app/crm/akce-typy cte zivy cisselnik st.CRM_Kontakt_AkceCis).
    // ════════════════════════════════════════════════════════════════
    var CRM_AKCE_GRID_CODE = "grid_crm_akce";
    // Grid Kontaktni udaje (osoby) na karte 72 (Kristy 26.6.2026): Novy vytvori
    // kontakt = akce typu 17 (Ziskani kontaktu na osobu z firmy) pres jadro 81.
    // Jediny typ -> bez pickeru, IDAkce napevno 17 + IDHlav firmy.
    var CRM_OSOBY_GRID_CODE = "grid_crm_kontaktni_udaje";
    var CRM_OSOBY_CORE_ID = 81;
    var CRM_OSOBY_IDAKCE = 17;
    var _crmAkceTypesCache = null;

    function _crmAkceFetchTypes() {
      if (_crmAkceTypesCache) return Promise.resolve(_crmAkceTypesCache);
      return fetch("/api/v1/erp/app/crm/akce-typy", { credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && j.ok && Array.isArray(j.types)) { _crmAkceTypesCache = j; return j; }
          throw new Error((j && j.error) || "akce-typy fetch failed");
        });
    }

    function _crmAkceCoreFor(idAkce) {
      var def = (_crmAkceTypesCache && _crmAkceTypesCache.default_core) || 82;
      if (!_crmAkceTypesCache || idAkce == null) return def;
      var hit = _crmAkceTypesCache.types.filter(function (t) {
        return String(t.id) === String(idAkce);
      })[0];
      return (hit && hit.core_id != null) ? hit.core_id : def;
    }

    function _crmAkceRowIdAkce(rowData) {
      if (!rowData) return null;
      // MSSQL/MCP alias parity: IDakce / IDAkce / idakce.
      if (rowData.IDakce != null) return rowData.IDakce;
      if (rowData.IDAkce != null) return rowData.IDAkce;
      if (rowData.idakce != null) return rowData.idakce;
      return null;
    }

    /** Modal picker typu akce. Resolve(type) nebo resolve(null) pri zruseni. */
    function _crmAkcePickType() {
      return _crmAkceFetchTypes().then(function (j) {
        return new Promise(function (resolve) {
          var overlay = document.createElement("div");
          overlay.style.cssText =
            "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10002;" +
            "display:flex;align-items:center;justify-content:center;";
          var modal = document.createElement("div");
          modal.style.cssText =
            "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
            "min-width:360px;max-width:440px;max-height:80vh;color:#e8eef5;" +
            "font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;" +
            "display:flex;flex-direction:column;";
          var header = document.createElement("div");
          header.style.cssText =
            "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
            "font-weight:600;font-size:14px;display:flex;justify-content:space-between;align-items:center;";
          header.innerHTML = "<span>➕ Nová akce — vyber typ</span>";
          var closeBtn = document.createElement("button");
          closeBtn.type = "button"; closeBtn.textContent = "✕";
          closeBtn.style.cssText =
            "background:transparent;border:none;color:#8a96a4;font-size:18px;cursor:pointer;line-height:1;";
          header.appendChild(closeBtn);
          modal.appendChild(header);
          var list = document.createElement("div");
          list.style.cssText = "padding:8px;overflow-y:auto;display:flex;flex-direction:column;gap:4px;";
          function _close(val) {
            if (overlay.parentNode) document.body.removeChild(overlay);
            resolve(val);
          }
          (j.types || []).forEach(function (t) {
            var b = document.createElement("button");
            b.type = "button";
            b.textContent = t.nazev || ("Akce " + t.id);
            b.style.cssText =
              "text-align:left;padding:9px 12px;background:#0f141a;border:1px solid #2a3340;" +
              "color:#e8eef5;border-radius:4px;font-size:13px;cursor:pointer;";
            b.addEventListener("mouseenter", function () { b.style.background = "#1d2530"; });
            b.addEventListener("mouseleave", function () { b.style.background = "#0f141a"; });
            b.addEventListener("click", function () { _close(t); });
            list.appendChild(b);
          });
          modal.appendChild(list);
          closeBtn.addEventListener("click", function () { _close(null); });
          overlay.addEventListener("click", function (e) { if (e.target === overlay) _close(null); });
          overlay.appendChild(modal);
          document.body.appendChild(overlay);
        });
      }).catch(function (e) {
        alert("⚠ Načtení typů akcí selhalo: " + (e.message || e));
        return null;
      });
    }

    /** CRM Akce 'Novy' -> picker -> open edit jadro se seedem IDHlav+IDAkce. */
    function _crmAkceCreate(ctx) {
      if (ctx.refId == null) {
        alert("⚠ Nová akce: chybí ID firmy (otevři akci z karty zákazníka).");
        return Promise.reject(new Error("no_master_id"));
      }
      return _crmAkcePickType().then(function (type) {
        if (!type) return;  // zruseno
        return _openFwEditForm(
          CRM_AKCE_GRID_CODE, null, "create", ctx.refreshFn,
          {
            overrideCoreId: type.core_id,
            injectValues: { IDHlav: ctx.refId, IDAkce: type.id },
          }
        );
      });
    }

    /** CRM Akce 'Oprava' -> routuj na jadro podle IDAkce zaznamu. */
    function _crmAkceEdit(ctx, rowId) {
      return _crmAkceFetchTypes().then(function () {
        var idAkce = _crmAkceRowIdAkce(ctx.rowData);
        return _openFwEditForm(
          CRM_AKCE_GRID_CODE, rowId, "edit", ctx.refreshFn,
          { overrideCoreId: _crmAkceCoreFor(idAkce) }
        );
      });
    }

    /** Grid Kontaktni udaje 'Novy' -> jadro 81 se seedem IDHlav + IDAkce=17
     *  (bez pickeru — jediny typ akce). */
    function _crmOsobaCreate(ctx) {
      if (ctx.refId == null) {
        alert("⚠ Nový kontakt: chybí ID firmy (otevři z karty zákazníka).");
        return Promise.reject(new Error("no_master_id"));
      }
      return _openFwEditForm(
        CRM_OSOBY_GRID_CODE, null, "create", ctx.refreshFn,
        {
          overrideCoreId: CRM_OSOBY_CORE_ID,
          injectValues: { IDHlav: ctx.refId, IDAkce: CRM_OSOBY_IDAKCE },
        }
      );
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

    // ── Hromadne osloveni (Claude-24/Kristy 18.6.2026) ──────────────────
    // Maly toast (styly z erp_batch_action nejsou exportovane -> vlastni lehky).
    function _osloveniToast(variant, msg) {
      var c = ({ success: ["#1e501e", "#a3e4a3", "#4a8a4a"],
                 error:   ["#781e1e", "#ff8a8a", "#a04040"] })[variant]
              || ["#1e3a50", "#aac8ec", "#3a5a7a"];
      var t = document.createElement("div");
      t.style.cssText = "position:fixed;top:50px;right:8px;background:" + c[0] +
        ";color:" + c[1] + ";border:1px solid " + c[2] +
        ";padding:10px 16px;border-radius:8px;font-size:13px;font-weight:600;" +
        "z-index:100002;box-shadow:0 4px 16px rgba(0,0,0,.4);max-width:420px;" +
        "font-family:system-ui,-apple-system,sans-serif;";
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); },
                 variant === "error" ? 6000 : 3500);
    }

    function _oslEsc(s) {
      return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
    // Odznak podle druhu prijemce (osobni / info@ / bez e-mailu / odhlaseno).
    function _oslBadge(it) {
      if (it.opted_out) return "<span style='background:#5a1e1e;color:#ff9a9a;padding:1px 7px;border-radius:10px;font-size:11px'>odhlášeno</span>";
      if (it.kind === "osobni") return "<span style='background:#1e4a1e;color:#a3e4a3;padding:1px 7px;border-radius:10px;font-size:11px'>osobní</span>";
      if (it.kind === "info") return "<span style='background:#1e3a55;color:#9fc4ec;padding:1px 7px;border-radius:10px;font-size:11px'>info@</span>";
      return "<span style='background:#3a3a3a;color:#bbb;padding:1px 7px;border-radius:10px;font-size:11px'>bez e-mailu</span>";
    }

    function _fmtTs(iso) {
      if (!iso) return "";
      try {
        return new Date(iso).toLocaleString("cs-CZ", { day: "2-digit", month: "2-digit",
          year: "numeric", hour: "2-digit", minute: "2-digit" });
      } catch (e) { return String(iso); }
    }

    // Dialog „📊 Tracking" na přehledu Aktivity obchodníka (core 124): pro vybrané
    // řádky (akce) ukáže stav odeslání + otevření z tracking pixelu (crm_email_track).
    function _trackingDialog(rowsPayload) {
      return fetch("/api/v1/erp/crm/aktivity/tracking", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows: rowsPayload }),
      }).then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (j) {
          if (!j || !j.ok) { _osloveniToast("error", "✗ Tracking se nepodařilo načíst"); return; }
          var items = j.items || [];
          var opened = 0, mails = 0;
          var rowsHtml = items.map(function (it) {
            var stav;
            if (!it.is_email) {
              stav = "<span style='color:#c9a227'>není e-mail" +
                (it.typ ? " (" + _oslEsc(it.typ) + ")" : "") + "</span>";
            } else {
              mails++;
              if (it.opened_at) {
                opened++;
                stav = "<b style='color:#a3e4a3'>Otevřeno ✓</b> <span style='color:#8ab88a'>" +
                  _oslEsc(_fmtTs(it.opened_at)) + (it.opens > 1 ? " · " + it.opens + "×" : "") + "</span>";
              } else if (it.has_track || it.sent_at) {
                stav = "<span style='color:#9fc4ec'>Odesláno</span> <span style='color:#7f9fbf'>" +
                  _oslEsc(_fmtTs(it.sent_at)) + "</span> · <span style='color:#999'>zatím neotevřeno</span>";
              } else {
                stav = "<span style='color:#888'>bez trackingu (neodesláno přes systém)</span>";
              }
            }
            var kdo = _oslEsc((it && it.firma) || (it && it.email) || "(bez názvu)");
            var mail = (it && it.email) ? " <span style='color:#7a90a8'>· " + _oslEsc(it.email) + "</span>" : "";
            return "<div style='padding:8px 4px;border-bottom:1px solid #1c1c1c'>" +
              "<div style='font-weight:600;color:#dfe7ef'>" + kdo + mail + "</div>" +
              "<div style='margin-top:2px;font-size:12px'>" + stav + "</div></div>";
          }).join("");

          var bd = document.createElement("div");
          bd.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100001;" +
            "display:flex;align-items:center;justify-content:center;";
          var dlg = document.createElement("div");
          dlg.style.cssText = "background:#151515;border:1px solid #333;border-radius:12px;" +
            "width:min(560px,94vw);max-height:82vh;overflow:auto;padding:18px 20px;" +
            "font-family:system-ui,-apple-system,sans-serif;color:#dfe7ef;box-shadow:0 10px 40px rgba(0,0,0,.6);";
          var sum = mails ? ("Otevřeno <b style='color:#a3e4a3'>" + opened + "</b> z " + mails + " e-mailů")
                          : "Ve výběru není e-mailová akce";
          dlg.innerHTML = "<div style='font-weight:700;font-size:15px;margin-bottom:2px'>📊 Tracking otevření</div>" +
            "<div style='color:#9fb6cc;font-size:12px;margin-bottom:12px'>" + sum + "</div>" +
            (rowsHtml || "<div style='color:#9fb6cc;padding:8px'>Žádná data.</div>");
          var btn = document.createElement("button");
          btn.textContent = "Zavřít";
          btn.style.cssText = "margin-top:14px;background:#2a2a2a;color:#dfe7ef;border:1px solid #444;" +
            "border-radius:8px;padding:8px 18px;font-size:13px;cursor:pointer;";
          function close() {
            if (bd.parentNode) bd.parentNode.removeChild(bd);
            document.removeEventListener("keydown", onEsc);
          }
          function onEsc(e) { if (e.key === "Escape") close(); }
          btn.onclick = close;
          bd.onclick = function (e) { if (e.target === bd) close(); };
          document.addEventListener("keydown", onEsc);
          dlg.appendChild(btn);
          bd.appendChild(dlg); document.body.appendChild(bd);
        }).catch(function (e) {
          _osloveniToast("error", "✗ Síť: " + (e && e.message || e));
        });
    }

    // Dialog: nahled prijemcu (osobni/info@/zadny/odhlaseno) + vyber sablony +
    // zarazeni vybranych firem do fronty mod.crm_outreach.
    // NEPOSILA — odeslani je krok odesilaci rutiny (Marti-AI) za pravnim OK.
    function _osloveniDialog(idhlavList, refreshFn) {
      return new Promise(function (resolve) {
        var N = idhlavList.length, done = false;
        var bd = document.createElement("div");
        bd.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100001;" +
          "display:flex;align-items:center;justify-content:center;";
        var dlg = document.createElement("div");
        dlg.style.cssText = "background:#1a1a1a;border:2px solid #3a4a5a;border-radius:12px;" +
          "padding:22px 26px;max-width:560px;width:92%;color:#e0e0e0;" +
          "font-family:system-ui,-apple-system,sans-serif;box-shadow:0 12px 48px rgba(0,0,0,.6);";
        var h = document.createElement("div");
        h.style.cssText = "font-size:17px;font-weight:700;color:#aac8ec;margin-bottom:12px;";
        h.textContent = "✉️ Oslovit vybrané firmy (" + N + ")";
        var listBox = document.createElement("div");
        listBox.style.cssText = "max-height:240px;overflow:auto;margin-bottom:12px;border:1px solid #2a3a4a;" +
          "border-radius:8px;padding:8px 10px;background:#0d0d0d;font-size:13px;";
        listBox.innerHTML = "<div style='color:#9fb6cc;padding:6px'>Načítám náhled příjemců…</div>";
        var sumLine = document.createElement("div");
        sumLine.style.cssText = "font-size:12px;color:#9fb6cc;margin-bottom:12px;";
        var lab = document.createElement("label");
        lab.style.cssText = "display:block;margin-bottom:6px;color:#9fb6cc;font-size:13px;";
        lab.textContent = "Šablona e-mailu:";
        var sel = document.createElement("select");
        sel.style.cssText = "width:100%;padding:8px;border-radius:6px;background:#0d0d0d;" +
          "color:#e0e0e0;border:1px solid #3a4a5a;font-size:14px;";
        // Naplneni dropdownu sablonami z ciselniku (dbo.EC_KontaktMailSablonyCis).
        // Fallback 9/10 zustava, kdyby endpoint selhal (dialog je pak stale funkcni).
        function _oslFillSablony(list) {
          sel.innerHTML = "";
          list.forEach(function (o) {
            var op = document.createElement("option");
            op.value = o[0]; op.textContent = o[1];
            sel.appendChild(op);
          });
          // Výchozí = Automatický E-mail DE (ID 17), ať omylem neodejde jiná
          // šablona (Kristy 13.7.2026). Když 17 v seznamu není, nech první.
          if (list.some(function (o) { return String(o[0]) === "17"; })) {
            sel.value = "17";
          }
        }
        _oslFillSablony([["9", "OTEVÍRÁK – první oslovení"], ["10", "PŘIPOMÍNAČ – druhá vlna"]]);
        fetch("/api/v1/erp/crm/osloveni/sablony", { method: "GET", credentials: "include" })
          .then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (j) {
            if (j && j.ok && Array.isArray(j.sablony) && j.sablony.length) {
              _oslFillSablony(j.sablony.map(function (s) { return [String(s.id), s.nazev]; }));
            }
          }).catch(function () { /* ponech fallback 9/10 */ });
        var note = document.createElement("div");
        note.style.cssText = "font-size:12px;color:#8aa;margin-top:10px;";
        note.innerHTML = "<b>📤 Odeslat na ostro</b> = odešle z Pavlovy schránky na reálné firmy " +
          "(odhlášené a bez e-mailu se přeskočí), s trasováním otevření. &nbsp;·&nbsp; " +
          "<b>Zařadit do fronty</b> = nic se neodešle. &nbsp;·&nbsp; " +
          "<b>DEMO</b> = jen na tvoji adresu.";
        var row = document.createElement("div");
        row.style.cssText = "display:flex;gap:10px;justify-content:flex-end;margin-top:18px;";
        function mk(t, bg, fn) {
          var b = document.createElement("button"); b.type = "button"; b.textContent = t;
          b.style.cssText = "background:" + bg + ";color:#fff;border:0;padding:8px 18px;" +
            "border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;min-width:90px;";
          b.onclick = fn; return b;
        }
        function close(v) { if (done) return; done = true; if (bd.parentNode) bd.parentNode.removeChild(bd); resolve(v); }
        var btnOk = mk("Zařadit do fronty", "#2563eb", function () {
          btnOk.disabled = true; btnOk.textContent = "Zařazuji…";
          fetch("/api/v1/erp/crm/osloveni/enqueue", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idhlav_list: idhlavList, template_id: sel.value }),
          }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) { return { r: r, j: j }; });
          }).then(function (x) {
            if (x.r.ok && x.j.ok) {
              _osloveniToast("success", "✓ Zařazeno do fronty: " + x.j.queued +
                (x.j.skipped ? (" (přeskočeno " + x.j.skipped + ", už ve frontě)") : ""));
              if (typeof refreshFn === "function") { try { refreshFn(); } catch (e) {} }
              close(true);
            } else {
              _osloveniToast("error", "✗ " + ((x.j && x.j.error) || ("HTTP " + x.r.status)));
              btnOk.disabled = false; btnOk.textContent = "Zařadit do fronty";
            }
          }).catch(function (e) {
            _osloveniToast("error", "✗ Síť: " + (e && e.message || e));
            btnOk.disabled = false; btnOk.textContent = "Zařadit do fronty";
          });
        });
        // DEMO odeslani + tracking otevreni (Kristy 29.6.2026) — posila VZDY na
        // testovaci adresu (k.ksirova@eurosoft.com) z Marti-AI schranky.
        var firmaById = {};
        function _oslTrackCheck() {
          btnDemo.disabled = true; btnDemo.textContent = "Načítám…";
          fetch("/api/v1/erp/crm/osloveni/track-status", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idhlav_list: idhlavList }),
          }).then(function (r) { return r.json().catch(function () { return {}; }); })
            .then(function (j) {
              btnDemo.disabled = false; btnDemo.textContent = "🔄 Zkontrolovat otevření";
              if (!j || !j.ok) { _osloveniToast("error", "✗ Stav se nepodařilo načíst"); return; }
              var by = {}; (j.items || []).forEach(function (it) { by[it.firma_id] = it; });
              var opened = 0, html = "";
              idhlavList.forEach(function (fid) {
                var it = by[fid] || {};
                var stav = it.opened_at ? "<b style='color:#a3e4a3'>Otevřeno ✓</b>"
                  : (it.sent_at ? "<span style='color:#9fc4ec'>Odesláno</span>"
                  : "<span style='color:#888'>—</span>");
                if (it.opened_at) opened++;
                html += "<div style='display:flex;justify-content:space-between;gap:8px;" +
                  "padding:4px 2px;border-bottom:1px solid #1c1c1c'>" +
                  "<span style='overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:320px'>" +
                  _oslEsc(firmaById[fid] || ("#" + fid)) + "</span><span style='white-space:nowrap'>" +
                  stav + "</span></div>";
              });
              listBox.innerHTML = html || "<div style='padding:6px;color:#9fb6cc'>Žádná data.</div>";
              sumLine.innerHTML = "Otevřeno: <b style='color:#a3e4a3'>" + opened + "</b> z " + idhlavList.length;
            }).catch(function () { btnDemo.disabled = false; btnDemo.textContent = "🔄 Zkontrolovat otevření"; _osloveniToast("error", "✗ Síť"); });
        }
        var btnDemo = mk("📨 Odeslat teď (DEMO)", "#7c3aed", function () {
          btnDemo.disabled = true; btnDemo.textContent = "Odesílám…";
          fetch("/api/v1/erp/crm/osloveni/demo-send", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idhlav_list: idhlavList, template_id: sel.value }),
          }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) { return { r: r, j: j }; });
          }).then(function (x) {
            if (x.r.ok && x.j.ok) {
              _osloveniToast("success", "✓ Odesláno (DEMO): " + x.j.sent + " → " + x.j.recipient);
              note.innerHTML = "DEMO odesláno na <b>" + _oslEsc(x.j.recipient) + "</b> (z Marti-AI schránky). " +
                "Otevři e-maily ve schránce a pak klikni <b>🔄 Zkontrolovat otevření</b>.";
              btnDemo.textContent = "🔄 Zkontrolovat otevření";
              btnDemo.disabled = false;
              btnDemo.onclick = _oslTrackCheck;
            } else {
              _osloveniToast("error", "✗ " + ((x.j && x.j.error) || ("HTTP " + x.r.status)));
              btnDemo.disabled = false; btnDemo.textContent = "📨 Odeslat teď (DEMO)";
            }
          }).catch(function (e) {
            _osloveniToast("error", "✗ Síť: " + (e && e.message || e));
            btnDemo.disabled = false; btnDemo.textContent = "📨 Odeslat teď (DEMO)";
          });
        });
        // OSTRE odeslani z Pavlovy schranky na realne firmy (Claude-24/Kristy 7.7.2026).
        // Spousti clovek kliknutim + potvrzenim. Trasovani otevreni (pixel) je soucasti.
        var btnLive = mk("📤 Odeslat na ostro", "#dc2626", function () {
          if (!window.confirm("OSTRÉ odeslání z Pavlovy schránky na REÁLNÉ firmy (" + N + ").\n\n" +
              "Odhlášené a firmy bez e-mailu se automaticky přeskočí.\nOpravdu odeslat?")) return;
          btnLive.disabled = true; btnLive.textContent = "Odesílám…";
          fetch("/api/v1/erp/crm/osloveni/send", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idhlav_list: idhlavList, template_id: sel.value }),
          }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) { return { r: r, j: j }; });
          }).then(function (x) {
            if (x.r.ok && x.j.ok) {
              var extra = [];
              if (x.j.skipped_optout) extra.push("odhlášeno " + x.j.skipped_optout);
              if (x.j.skipped_noemail) extra.push("bez e-mailu " + x.j.skipped_noemail);
              if (x.j.truncated) extra.push("zbytek pošli dalším klikem");
              _osloveniToast("success", "✓ Odesláno na ostro: " + x.j.sent +
                (extra.length ? " (" + extra.join(", ") + ")" : ""));
              note.innerHTML = "Odesláno na ostro z <b>Pavlovy schránky</b> (" + x.j.sent + "). " +
                "Za chvíli klikni <b>🔄 Zkontrolovat otevření</b>.";
              btnLive.textContent = "🔄 Zkontrolovat otevření";
              btnLive.disabled = false;
              btnLive.onclick = _oslTrackCheck;
              if ((x.j.errors || []).length) {
                _osloveniToast("error", "Část se nepodařila: " + x.j.errors.slice(0, 2).join(" | "));
              }
            } else {
              _osloveniToast("error", "✗ " + ((x.j && x.j.error) || ("HTTP " + x.r.status)));
              btnLive.disabled = false; btnLive.textContent = "📤 Odeslat na ostro";
            }
          }).catch(function (e) {
            _osloveniToast("error", "✗ Síť: " + (e && e.message || e));
            btnLive.disabled = false; btnLive.textContent = "📤 Odeslat na ostro";
          });
        });
        var btnNo = mk("Zrušit", "#3a3a3a", function () { close(false); });
        row.appendChild(btnLive); row.appendChild(btnDemo); row.appendChild(btnOk); row.appendChild(btnNo);
        dlg.appendChild(h); dlg.appendChild(listBox); dlg.appendChild(sumLine);
        dlg.appendChild(lab); dlg.appendChild(sel); dlg.appendChild(note); dlg.appendChild(row);
        bd.appendChild(dlg); document.body.appendChild(bd);

        // Nacti nahled prijemcu
        fetch("/api/v1/erp/crm/osloveni/preview", {
          method: "POST", credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idhlav_list: idhlavList }),
        }).then(function (r) {
          return r.json().catch(function () { return {}; });
        }).then(function (j) {
          if (!j || !j.ok || !Array.isArray(j.items)) {
            listBox.innerHTML = "<div style='color:#ffb38a;padding:6px'>Náhled se nepodařilo načíst (" +
              _oslEsc((j && j.error) || "chyba") + "). Zařadit lze i tak.</div>";
            return;
          }
          var nOsob = 0, nInfo = 0, nNic = 0, nOdhl = 0, html = "";
          j.items.forEach(function (it) {
            firmaById[it.firma_id] = it.firma;
            if (it.opted_out) nOdhl++;
            else if (it.kind === "osobni") nOsob++;
            else if (it.kind === "info") nInfo++;
            else nNic++;
            html += "<div style='display:flex;justify-content:space-between;gap:8px;align-items:center;" +
              "padding:4px 2px;border-bottom:1px solid #1c1c1c'>" +
              "<span style='overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:300px'>" +
              _oslEsc(it.firma) + (it.recipient ? "<br><span style='color:#7d93a8;font-size:11px'>" +
              _oslEsc(it.recipient) + "</span>" : "") + "</span>" +
              "<span style='white-space:nowrap'>" + _oslBadge(it) +
              (it.osloven_kdy ? " <span style='color:#888;font-size:11px'>" + _oslEsc(it.osloven_kdy) + "</span>" : "") +
              "</span></div>";
          });
          listBox.innerHTML = html || "<div style='padding:6px;color:#9fb6cc'>Žádná data.</div>";
          sumLine.innerHTML = "Osobní: <b style='color:#a3e4a3'>" + nOsob + "</b> · info@: <b style='color:#9fc4ec'>" +
            nInfo + "</b> · bez e-mailu: <b style='color:#bbb'>" + nNic + "</b>" +
            (nOdhl ? " · odhlášeno: <b style='color:#ff9a9a'>" + nOdhl + "</b>" : "");
        }).catch(function (e) {
          listBox.innerHTML = "<div style='color:#ffb38a;padding:6px'>Náhled selhal: " +
            _oslEsc(e && e.message || e) + " — zařadit lze i tak.</div>";
        });
      });
    }

    // ════════════════════════════════════════════════════════════════════
    // ACTION REGISTRY — single truth source
    // ════════════════════════════════════════════════════════════════════
    /** Mail (Claude-23 3.7.2026): přesun e-mailu mezi Doručené (nove) a
     *  Zpracované (zpracovane). Náš stav, do Outlooku nezapisuje. */
    function _mailSetStav(ctx, stav) {
      var rowId = null;
      if (ctx.rowData) rowId = ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID;
      if (rowId == null) {
        alert("⚠ Nejprve vyber e-mail.");
        return Promise.reject(new Error("no_row_selected"));
      }
      return fetch("/api/v1/erp/app/mail/stav", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ id: rowId, stav: stav }),
      }).then(function (r) { return r.json(); }).then(function (j) {
        if (!j || !j.ok) { alert("Chyba: " + ((j && j.error) || "?")); return; }
        return _refreshGrid(ctx.gridCode, ctx.refreshFn);
      }).catch(function (e) { alert("Chyba: " + e); });
    }

    /** Escape HTML (detail e-mailu). */
    function _mailEsc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    /** Standardní detail e-mailu (Claude-23 3.7.2026): modal s hlavičkami +
     *  plným tělem + přílohami (odkazy ke stažení). */
    function _mailShowDetail(d) {
      var ov = document.createElement("div");
      ov.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.62);z-index:99999;" +
        "display:flex;align-items:center;justify-content:center;";
      var box = document.createElement("div");
      box.style.cssText = "position:relative;background:#121826;color:#e8edf6;max-width:920px;" +
        "width:92%;max-height:88vh;overflow:auto;border-radius:12px;border:1px solid #2a3547;" +
        "box-shadow:0 20px 60px rgba(0,0,0,.5);";
      var att = (d.prilohy || []).map(function (p) {
        return '<a href="' + p.url + '" target="_blank" rel="noopener" ' +
          'style="display:inline-block;color:#7cc4ff;text-decoration:none;background:#1a2233;' +
          'border:1px solid #2a3547;border-radius:8px;padding:5px 10px;margin:4px 8px 0 0;font-size:12.5px;">' +
          "📎 " + _mailEsc(p.name) + "</a>";
      }).join("");
      box.innerHTML =
        '<div style="padding:18px 22px;border-bottom:1px solid #2a3547;">' +
          '<div style="font-size:18px;font-weight:600;margin-bottom:10px;padding-right:90px;">' +
            _mailEsc(d.predmet || "(bez předmětu)") + "</div>" +
          '<div style="font-size:13px;color:#9fb0c8;line-height:1.8;">' +
            "<b>Od:</b> " + _mailEsc(((d.od_jmeno ? d.od_jmeno + " " : "") + "<" + (d.od_email || "") + ">")) + "<br>" +
            "<b>Komu:</b> " + _mailEsc(d.komu || "") +
            (d.kopie ? "<br><b>Kopie:</b> " + _mailEsc(d.kopie) : "") + "<br>" +
            "<b>Datum:</b> " + _mailEsc(d.datum || "") + "</div>" +
          (att ? '<div style="margin-top:8px;">' + att + "</div>" : "") +
        "</div>" +
        '<div id="_mailBody"></div>';
      var bodyWrap = box.querySelector("#_mailBody");
      if (d.telo_html) {
        // HTML e-mail v izolovaném sandbox iframe (bez skriptů) — bílé pozadí jako Outlook.
        var ifr = document.createElement("iframe");
        ifr.setAttribute("sandbox", "");
        ifr.setAttribute("referrerpolicy", "no-referrer");
        ifr.style.cssText = "width:100%;border:0;background:#fff;min-height:440px;display:block;";
        ifr.srcdoc = d.telo_html;
        bodyWrap.appendChild(ifr);
      } else {
        var pre = document.createElement("div");
        pre.style.cssText = "padding:22px;white-space:pre-wrap;word-break:break-word;" +
          "font-size:14px;line-height:1.65;";
        pre.textContent = d.telo_text || "(prázdné tělo)";
        bodyWrap.appendChild(pre);
      }
      var close = document.createElement("button");
      close.textContent = "✕ Zavřít";
      close.style.cssText = "position:absolute;top:16px;right:18px;background:#27313f;color:#cdd9ea;" +
        "border:0;border-radius:8px;padding:7px 13px;cursor:pointer;font-size:12.5px;";
      box.appendChild(close);
      ov.appendChild(box);
      function done() { try { document.body.removeChild(ov); } catch (e) {} document.removeEventListener("keydown", onEsc); }
      function onEsc(e) { if (e.key === "Escape") done(); }
      close.onclick = done;
      ov.onclick = function (e) { if (e.target === ov) done(); };
      document.addEventListener("keydown", onEsc);
      document.body.appendChild(ov);
    }

    function _mailOpenDetail(ctx) {
      var rowId = null;
      if (ctx.rowData) rowId = ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID;
      if (rowId == null) { alert("⚠ Nejprve vyber e-mail."); return Promise.reject(new Error("no_row")); }
      return fetch("/api/v1/erp/app/mail/detail/" + rowId, { credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d || !d.ok) { alert("Chyba: " + ((d && d.error) || "?")); return; }
          _mailShowDetail(d);
        }).catch(function (e) { alert("Chyba: " + e); });
    }

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
          // CRM Akce: picker typu akce -> routing + seed IDHlav/IDAkce.
          if (ctx.gridCode === CRM_AKCE_GRID_CODE) {
            return _crmAkceCreate(ctx);
          }
          // CRM Kontaktni udaje (osoby): jadro 81 + seed IDHlav + IDAkce=17.
          if (ctx.gridCode === CRM_OSOBY_GRID_CODE) {
            return _crmOsobaCreate(ctx);
          }
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
          // CRM Akce: routuj edit na jadro podle IDAkce zaznamu.
          if (ctx.gridCode === CRM_AKCE_GRID_CODE) {
            return _crmAkceEdit(ctx, rowId);
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
      // Mail: standardní detail e-mailu (Claude-23 3.7.2026). Modal s hlavičkami
      // + plným tělem + přílohami. Gate v page_render.js (mail_* přehledy).
      mail_otevrit: {
        key: "mail_otevrit",
        icon: "📧",
        label: "Otevřít e-mail",
        hint: "Zobrazit celý e-mail (od, komu, tělo, přílohy)",
        cssClass: "erp-action-edit",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) { return _mailOpenDetail(ctx); },
      },
      // Mail: uklidit / vrátit (Claude-23 3.7.2026). Gate v page_render.js
      // (jen mail_dorucene / mail_zpracovane přehledy). POST /app/mail/stav.
      mail_uklidit: {
        key: "mail_uklidit",
        icon: "✅",
        label: "Uklidit do Zpracovaných",
        hint: "Přesunout e-mail z Doručených do Zpracovaných",
        cssClass: "erp-action-refresh",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) { return _mailSetStav(ctx, "zpracovane"); },
      },
      mail_vratit: {
        key: "mail_vratit",
        icon: "↩️",
        label: "Vrátit do Doručených",
        hint: "Vrátit e-mail zpět do Doručených",
        cssClass: "erp-action-refresh",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) { return _mailSetStav(ctx, "nove"); },
      },
      // Hromadne osloveni firem (Claude-24/Kristy 18.6.2026): vyber firem v gridu
      // Kontakty -> zarazeni do fronty mod.crm_outreach. Gate v page_render.js
      // (jen crm_kontakty). Multi-row pres ctx.rowIds (getSelectedRows), fallback single.
      osloveni: {
        key: "osloveni",
        icon: "✉️",
        label: "Oslovit vybrané",
        hint: "Zařadit vybrané firmy do fronty hromadného oslovení (nabídka spolupráce)",
        cssClass: "erp-action-osloveni",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          var ids = (Array.isArray(ctx.rowIds) && ctx.rowIds.length > 0)
            ? ctx.rowIds.slice()
            : (ctx.rowData ? [ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID] : []);
          ids = ids.filter(function (x) { return x != null && x !== ""; });
          if (ids.length === 0) {
            alert("⚠ Oslovit: nejprve vyber firmy (lze i více — Ctrl/Shift + klik).");
            return Promise.reject(new Error("no_rows"));
          }
          return _osloveniDialog(ids, ctx.refreshFn);
        },
      },
      // Tracking otevření (Kristy 9.7.2026): na přehledu Aktivity obchodníka
      // (core 124) vyber e-mailové akce -> stav odeslání + otevření z pixelu.
      // Gate v page_render.js (jen crm_aktivity_obchodnik). Multi-row přes ctx.rowIds.
      tracking: {
        key: "tracking",
        icon: "📊",
        label: "Tracking otevření",
        hint: "Zobrazit stav odeslání a otevření u vybraných e-mailů",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          // Dataset 92 nemá ve výběru id -> nespoléhej na ctx.rowIds (bylo prázdné).
          // Vezmi vybrané řádky přímo z gridu a pošli e-mail/firmu/typ.
          var api = ctx.gridApi;
          var rows = (api && typeof api.getSelectedRows === "function")
            ? (api.getSelectedRows() || []) : [];
          if ((!rows || rows.length === 0) && ctx.rowData) rows = [ctx.rowData];
          if (!rows || rows.length === 0) {
            alert("⚠ Tracking: nejprve vyber řádek(y) (lze i více — Ctrl/Shift + klik).");
            return Promise.reject(new Error("no_rows"));
          }
          function _rget(r, needle) {
            if (!r) return "";
            for (var k in r) {
              if (String(k).toLowerCase().indexOf(needle) >= 0) return r[k];
            }
            return "";
          }
          var payload = rows.map(function (r) {
            return {
              email: _rget(r, "mail") || "",
              firma: _rget(r, "firma") || "",
              typ: _rget(r, "typ") || "",
            };
          });
          return _trackingDialog(payload);
        },
      },
      // Součet hodin (Claude-28/Jirka 10.7.2026, pro Dušana Havláta): na
      // přehledu Docházka — vše (core 183, vyroba.dusan_dochazka_vse) vyber
      // 1..N řádků (Ctrl/Shift + klik) → pravý klik „Σ Součet hodin" → sečte
      // sloupec 'hodin' vybraných záznamů a ukáže informativní okno s OK.
      // Gate v page_render.js (jen dochazka_vse). Čistě čtecí — nic nemění.
      soucet_hodin: {
        key: "soucet_hodin",
        icon: "Σ",
        label: "Součet hodin",
        hint: "Sečíst hodiny u vybraných záznamů (lze i více — Ctrl/Shift + klik)",
        cssClass: "erp-action-soucet-hodin",
        destructive: false,
        requiresRow: true,
        // Uživatelská akce → v context menu ÚPLNĚ DOLE (datagrid.js userItems),
        // ne mezi systémovými CRUD nahoře (Jirka 10.7.2026).
        userAction: true,
        handler: function (ctx) {
          // Preferuj skutečný výběr (multi); fallback = pravo-kliknutý řádek.
          var rows = [];
          try {
            if (ctx.gridApi && typeof ctx.gridApi.getSelectedRows === "function") {
              rows = ctx.gridApi.getSelectedRows() || [];
            }
          } catch (e) { rows = []; }
          if (rows.length === 0 && ctx.rowData) rows = [ctx.rowData];
          if (rows.length === 0) {
            alert("⚠ Součet hodin: nejprve vyber záznam(y) — lze i více (Ctrl/Shift + klik).");
            return Promise.reject(new Error("no_rows"));
          }
          var sum = 0, bezHodnoty = 0;
          rows.forEach(function (r) {
            var v = r ? r.hodin : null;
            var n = (v == null || v === "") ? NaN : Number(v);
            if (isNaN(n)) { bezHodnoty++; } else { sum += n; }
          });
          var fmt = sum.toLocaleString("cs-CZ",
            { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          // Informativní modal s OK (vzor _trackingDialog — overlay + Esc + klik mimo).
          var bd = document.createElement("div");
          bd.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100001;" +
            "display:flex;align-items:center;justify-content:center;";
          var dlg = document.createElement("div");
          dlg.style.cssText = "background:#151515;border:1px solid #333;border-radius:12px;" +
            "min-width:300px;max-width:420px;padding:20px 24px;text-align:center;" +
            "font-family:system-ui,-apple-system,sans-serif;color:#dfe7ef;box-shadow:0 10px 40px rgba(0,0,0,.6);";
          dlg.innerHTML =
            "<div style='font-weight:700;font-size:15px;margin-bottom:10px'>Σ Součet hodin</div>" +
            "<div style='color:#9fb6cc;font-size:13px;margin-bottom:6px'>Vybrané záznamy: <b style='color:#dfe7ef'>" +
              rows.length + "</b>" +
              (bezHodnoty ? " <span style='color:#c9a227'>(bez hodnoty: " + bezHodnoty + ")</span>" : "") +
            "</div>" +
            "<div style='font-size:24px;font-weight:700;color:#a3e4a3;margin:10px 0 4px'>" + fmt + " h</div>";
          var btn = document.createElement("button");
          btn.textContent = "OK";
          btn.style.cssText = "margin-top:14px;background:#2563eb;color:#fff;border:0;" +
            "border-radius:8px;padding:8px 34px;font-size:13px;font-weight:600;cursor:pointer;";
          function close() {
            if (bd.parentNode) bd.parentNode.removeChild(bd);
            document.removeEventListener("keydown", onEsc);
          }
          function onEsc(e) { if (e.key === "Escape" || e.key === "Enter") close(); }
          btn.onclick = close;
          bd.onclick = function (e) { if (e.target === bd) close(); };
          document.addEventListener("keydown", onEsc);
          dlg.appendChild(btn);
          bd.appendChild(dlg);
          document.body.appendChild(bd);
          try { btn.focus(); } catch (e) {}
          return Promise.resolve();
        },
      },
      // Kalkulace jádro (Claude-24/Kristy 9.7.2026): na přehledu Kalkulace a
      // nabídky (core 140, vp_kalkulace) otevře edit jádro „Kalkulace jádro"
      // (core 188 = @@COREIMPORT z Centrály form 271) pro vybraný řádek.
      // Gate + klávesová zkratka Alt+M v page_render.js (jen vp_kalkulace).
      kalkulace_jadro: {
        key: "kalkulace_jadro",
        icon: "🧮",
        label: "Položky kalkulace",
        hint: "Otevřít Položky kalkulace — staré jádro (Alt+M)",
        shortcut: "Alt+M",
        cssClass: "erp-action-kalkulace-jadro",
        destructive: false,
        requiresRow: true,
        handler: function (ctx) {
          var rid = null;
          if (ctx.rowData) {
            // MSSQL/MCP uppercase ID parity (28.5.2026 #3)
            rid = ctx.rowData.ID != null ? ctx.rowData.ID : ctx.rowData.id;
          }
          if (rid == null) {
            alert("⚠ Kalkulace jádro: nejprve vyber řádek kalkulace.");
            return Promise.reject(new Error("no_row"));
          }
          return _openFwEditForm(
            ctx.gridCode, rid, "edit", ctx.refreshFn,
            { overrideCoreId: 188, forceLegacy: true }  // 188 = staré jádro (Položky kalkulace → DesignFwForm, obchází ErpSpecForm)
          );
        },
      },
      // Složka dokumentů záznamu (Marti 18.6.2026) — systém adresářů (dir_config).
      // Otevře /files panel (list/upload/download) pro typ+ID řádku. Na CRM
      // Kontakty: type=kontakt, id=row.id. ACL+audit řeší backend.
      docfiles: {
        key: "docfiles",
        icon: "📁",
        label: "Dokumenty (složka)",
        hint: "Otevřít složku dokumentů tohoto záznamu — nahrát/stáhnout soubory",
        cssClass: "erp-action-docfiles",
        destructive: false,
        requiresRow: true,
        dirType: "kontakt",
        handler: function (ctx) {
          var rid = ctx.rowData ? (ctx.rowData.id != null ? ctx.rowData.id : ctx.rowData.ID) : null;
          if (rid == null) {
            alert("⚠ Dokumenty: nejprve vyber záznam v přehledu.");
            return Promise.reject(new Error("no_row_selected"));
          }
          var dtype = (ctx.dirType || "kontakt");
          var url = "/files?type=" + encodeURIComponent(dtype) + "&id=" + encodeURIComponent(rid) +
                    "&name=" + encodeURIComponent("Dokumenty — " + rid);
          window.open(url, "strategieFiles", "width=860,height=920");
          return Promise.resolve();
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

      // CRM Akce routing helpers (Kristy 26.6.2026) — pouziva i design_forms.js
      // embedded grid dblclick (edit routing podle IDAkce).
      crmAkceFetchTypes: _crmAkceFetchTypes,
      crmAkceCoreFor: _crmAkceCoreFor,
      crmAkceGridCode: CRM_AKCE_GRID_CODE,
    };

    console.log("[ErpGridActions] registered (v1.0.0) — actions:",
                Object.keys(ACTIONS).join(", "));
  });
})(window);
