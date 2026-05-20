/**
 * DesignJadroRadekForm — extracted standalone JS module.
 *
 * Phase JS-3 (18.5.2026 ~22:50): extract z design_forms.js.
 * Form 3 — fw.core row edit (Krok 14a)
 *
 * Loaded AFTER design_form_helpers.js (which exports _erpDFH).
 * Imports utilities via global._erpDFH destructure.
 */
(function (global) {
  "use strict";

  // Phase JS-4 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  // Pri init failure: chyba do _erpModuleHealth + diag_log, ostatni moduly pokracuji.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("design_jadro_radek_form.js", "v1.0.0", function () {


  const _DFH = global._erpDFH || {};
  const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
  const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
  const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
  const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
  const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
  const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
  const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
  const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  class DesignJadroRadekForm {
    constructor(opts) {
      this.opts = opts || {};
      // opts.gridCode (required)   - fw.core.code
      // opts.rowId (required)      - id radku v gridu (pro budoucy form open)
      // opts.compDefId (optional)  - sloupec kde Marti kliknul
      // opts.headerName (optional) - human-readable z header textu
      this._shell = null;
      this._pc = null;
      this._data = null;
      // Phase 38.4 Krok 14a-A1d: dirty tracking
      this._dirty = new Set();
      this._saveBtn = null;
      this._dirtyBadge = null;
    }

    _onDirty(fieldKey, isDirty) {
      if (isDirty) this._dirty.add(fieldKey);
      else this._dirty.delete(fieldKey);
      const count = this._dirty.size;
      if (this._saveBtn) this._saveBtn.style.display = count > 0 ? "" : "none";
      if (this._dirtyBadge) {
        // A1q (12.5.2026 vecer): Czech plural fix — Marti's polish.
        // 1 = "změna", 2-4 = "změny", 5+ = "změn".
        const _wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
        this._dirtyBadge.textContent = count > 0
          ? "● " + count + " " + _wBadge
          : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
      // A1r (12.5.2026 vecer): global dirty tracking pro F5/tab close warning.
      _markFormDirty(this, count > 0);
    }

    _onSaveClick() {
      const fields = Array.from(this._dirty).join(", ");
      alert(
        "Save flow přijde v Kroku 14b (backend POST endpointy).\n\n" +
        "Změněná pole (zatím nejsou ukládána):\n" + fields
      );
    }

    // Phase 38.4 Krok 14a-A1m #2: 📖 popup pro description memo.
    // Form 3 ma jednu entity (core), tedy bez tab-aware vyberu.
    _openDescriptionsPopup() {
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        _confirmDarkDialog({
          title: "Popis není k dispozici",
          message: "Tento grid nemá záznam v fw.core (hardcoded view).\nPopis bude k dispozici, až mu vytvoříme core entry.",
          ok: "OK",
          cancel: null,
        });
        return;
      }
      // Krok 14b+21 (14.5.2026 rano): entityId + onSaved
      const self = this;
      _buildDescriptionsPopup({
        entityKind: "core",
        entityId: core.id,
        entityLabel: core.label || core.code || "(bez labelu)",
        descUser: core.description_user,
        descSystem: core.description_system,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          if (self._data && self._data.core) {
            self._data.core.description_user = payload.description_user;
            self._data.core.description_system = payload.description_system;
          }
        },
      });
    }

    // Phase 38.4 Krok 14a-A1k #4: před zavřením oken pres ✕ se zeptej,
    // pokud jsou neuložené změny. Dark design, 3 tlačítka.
    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      // A1q (12.5.2026 vecer): drop "Pole: ..." výpis — Marti's request.
      // Userové konkretním fieldKey názvům (mn.visibility_scope) nerozumí.
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      // A1t (12.5.2026 vecer doma): Marti's polish — drop 3-button mode.
      // 3 stavy decision:
      //   true (Ano click) → save + close
      //   false (Ne click) → close without save (explicit destructive)
      //   null (Esc / click outside) → keep modal open (invisible cancel)
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")",
      });
      if (decision === true) {
        this._onSaveClick();
        return "save";
      }
      if (decision === false) {
        return "close"; // explicit Ne → zavřít bez uložení
      }
      return "cancel"; // null (Esc / click outside) → keep modal open
    }

    open() {
      const title = "Design: Jádro pro řádek";
      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        // A1r (12.5.2026): cleanup global dirty tracking po close.
        onClose: () => _markFormDirty(this, false),
        // Krok 14a-A1m #2: 📖 callback — otevre popup s description memo.
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer — dirty badge + Save (hidden) + Zavřít
      this._dirtyBadge = document.createElement("span");
      this._dirtyBadge.style.cssText = "color:#d4b88a;font-size:12px;margin-right:auto;display:none;";
      this._shell.footer.appendChild(this._dirtyBadge);

      this._saveBtn = document.createElement("button");
      this._saveBtn.type = "button";
      this._saveBtn.textContent = "💾 Uložit";
      this._saveBtn.style.cssText = "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;display:none;";
      this._saveBtn.addEventListener("click", () => this._onSaveClick());
      this._shell.footer.appendChild(this._saveBtn);

      const closeFooter = document.createElement("button");
      closeFooter.type = "button";
      closeFooter.textContent = "Zavřít";
      closeFooter.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      closeFooter.addEventListener("click", () => this._shell.close());
      this._shell.footer.appendChild(closeFooter);

      this._fetchData();
    }

    _fetchData() {
      const gridCode = this.opts.gridCode;
      if (!gridCode) {
        this._showError("Chybí gridCode (fw.core.code).");
        return;
      }
      // Phase 38.4 Krok 14b (12.5.2026 ~23:30): Marti's bug catch —
      // pred fix fetched /design/core-by-code/{grid} (= list core), now
      // fetches /design/form-core-for-grid/{grid} → vrací form_core nebo
      // empty state s entity_type + suggested_form_code (pro scaffold akci).
      const url = "/api/v1/erp/design/form-core-for-grid/" + encodeURIComponent(gridCode);
      fetch(url, { credentials: "same-origin", cache: "no-store" })
        .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject("HTTP " + r.status + ": " + t)))
        .then(data => {
          this._data = data || {};
          this._render();
        })
        .catch(err => {
          console.error("DesignJadroRadekForm fetch failed:", err);
          this._showError("Chyba načtení: " + String(err).slice(0, 200));
        });
    }

    _showError(msg) {
      this._shell.body.innerHTML = "";
      const err = document.createElement("div");
      err.style.cssText = "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;border-radius:4px;";
      err.textContent = msg;
      this._shell.body.appendChild(err);
    }

    _render() {
      this._shell.body.innerHTML = "";

      const jadroDiv = this._buildJadroTab();

      this._pc = new global.ErpPageControl(this._shell.body, {
        tabs: [
          { id: "jadro", label: "Jádro", content: jadroDiv },
          // Future taby (Krok 14c+): Workflow, Audit, Validace
        ],
        activeId: "jadro",
      });
    }

    _buildJadroTab() {
      const root = document.createElement("div");
      root.className = "erp-design-tab-jadro";

      // Dirty tracking closures
      const D = this._onDirty.bind(this);
      const _f = (l, v, key, o) => _field(l, v, Object.assign({fieldKey: key, onDirty: D}, o || {}));
      const _d = (l, v, items, key, o) => _dropdown(l, v, items, Object.assign({fieldKey: key, onDirty: D}, o || {}));

      // Section: Kontext kliku — vsechno readonly (jen orientacni informace)
      // Krok 14a-A1m #1: section title pair (UI state, no DB)
      // Krok 14b (12.5.2026 ~23:30): plus data_entity_type z list core
      // (po refactoru _fetchData → /form-core-for-grid endpoint)
      // Krok 14b-4 (12.5.2026 ~23:45): plus list_core.id + list_core.code
      // (Marti's "ID 11" catch — primary info, alias je secondary)
      const ctxSec = _sectionBuild("Kontext kliku v gridu", "UI state (gridCode + rowId + headerName + compDefId)");
      const listCore = (this._data && this._data.list_core) || null;
      ctxSec.grid.appendChild(_f("List core ID", listCore ? listCore.id : null, "ctx.listCoreId", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("List core (skutečný kód)", listCore ? listCore.code : null, "ctx.listCoreCode", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Grid (layout alias)", this.opts.gridCode, "ctx.gridCode", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Řádek (ID)", this.opts.rowId, "ctx.rowId", { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_f("Klepnutý sloupec", this.opts.headerName, "ctx.headerName", { readonly: true }));
      ctxSec.grid.appendChild(_f("comp_def_id sloupce", this.opts.compDefId, "ctx.compDefId", { mono: true, readonly: true }));
      const entityType = (this._data && this._data.entity_type) || null;
      ctxSec.grid.appendChild(_f("Typ datové entity", entityType, "ctx.entityType", { mono: true, readonly: true }));
      root.appendChild(ctxSec.wrap);

      // Section: Jadro identita — pro FORM core (ne list core!).
      // Phase 38.4 Krok 14b (12.5.2026 ~23:30): Marti's bug catch fix —
      // pred refactor zobrazoval list core (security_users, id=11, layout=list)
      // jako "Jádro pro řádek identita", což bylo semanticky nesprávné.
      // Po refactor: form_core (kind='form', data_entity_type matches list).
      // Pokud form_core neexistuje → empty state s "Vytvoř form detail" button.
      const formCore = (this._data && this._data.form_core) || null;
      const found = !!(this._data && this._data.found);
      const suggestedCode = (this._data && this._data.suggested_form_code) || null;

      if (found && formCore && formCore.id) {
        // Form core existuje — render identitu (existing pattern)
        const idSec = _sectionBuild("Jádro pro řádek — identita", "fw.core — identita + layout + version");
        idSec.grid.appendChild(_f("ID", formCore.id, "form_core.id", { mono: true, readonly: true }));
        idSec.grid.appendChild(_f("Code", formCore.code, "form_core.code", { mono: true }));
        idSec.grid.appendChild(_f("Label", formCore.label, "form_core.label"));
        // Phase fw.core slim 20.5.2026: layout_type + layout_template DROPPED
        idSec.grid.appendChild(_f("Version", formCore.version, "form_core.version", { mono: true, readonly: true }));
        root.appendChild(idSec.wrap);

        // Krok 14a-A1m #2: popis v separatnim popupu (📖 ikona v header).
      } else {
        // Form core neexistuje → Marti's "Vytvoř form detail" vychytávka.
        // Phase 38.4 Krok 14b-3 (12.5.2026 ~23:30): empty state s placeholder
        // button. Backend scaffold POST endpoint v Krok 14b-4 (next commit).
        const emptySec = _sectionBuild("Jádro pro řádek — identita", "fw.core form — zatím neexistuje");
        const wrap = document.createElement("div");
        wrap.style.cssText = "padding:20px;text-align:center;grid-column:1/-1;";

        const hint = document.createElement("div");
        hint.style.cssText = "color:#8a96a4;font-size:13px;line-height:1.6;margin-bottom:16px;";
        if (entityType) {
          hint.innerHTML =
            "Tento grid (<code style='color:#cfd6df;'>" +
            _esc(this.opts.gridCode || "?") +
            "</code>) zatím nemá <strong>form detail</strong>." +
            "<br>Klik založí <code style='color:#cfd6df;'>fw.core (" +
            _esc(suggestedCode || "?") +
            ")</code> + <code style='color:#cfd6df;'>fw.comp_def form 302</code> root s defaultním panelem <em>Obsah</em>.";
        } else {
          // Phase 38.4 Krok 5.M-3+B (17.5.2026): drop "doplnit data_entity_type"
          // hint (Krok 5.M doctrine). Generic hint zustal — form scaffold
          // konfigurovany pres root comp_def data_source.
          hint.innerHTML =
            "Tento grid (<code style='color:#cfd6df;'>" +
            _esc(this.opts.gridCode || "?") +
            "</code>) zatim nema <strong>form detail</strong>." +
            "<br>Form lze zalozit cez Design: Core formular " +
            "(volba root template + binding na data_source).";
        }
        wrap.appendChild(hint);

        if (entityType) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.textContent = "🪄 Vytvoř form detail";
          btn.style.cssText =
            "padding:10px 24px;background:#3a5a3a;border:1px solid #4a7a4a;" +
            "border-radius:4px;color:#e8eef5;cursor:pointer;font-size:13px;" +
            "font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.3);";
          btn.title = "POST /api/v1/erp/design/scaffold-form — atomic INSERT fw.core + fw.comp_def form 302";
          // Phase 38.4 Krok 14b-4 (12.5.2026 ~23:45): scaffold POST wire-up.
          // Marti's vize "Tim bychom meli vyhrano" — 1 klik = celý form
          // detail vytvořený. Atomic, idempotent (pokud existuje, vrátí
          // existing). Po success reload _fetchData() → re-render with
          // new form core identity.
          btn.addEventListener("click", async () => {
            btn.disabled = true;
            btn.textContent = "⏳ Vytvářím...";
            try {
              const payload = {
                entity_type: entityType,
                suggested_code: suggestedCode,
                list_core_id: listCore ? listCore.id : null,
                list_core_code: listCore ? listCore.code : null,
              };
              // Phase fw.core slim 20.5.2026 (Marti's Decision 2A):
              // /scaffold-form endpoint DROPPED. Marti-AI manualne vytvori comp_def.
              console.warn("[design_jadro_radek_form] /scaffold-form endpoint dropped");
              alert("Scaffold form endpoint odstranen (Phase fw.core slim).\nPoradej Marti-AI vytvorit form core + comp_def pres knowledge_entry postup.");
              const resp = { ok: false, status: 410, statusText: "Gone", json: function() { return Promise.resolve({ ok: false, error: "scaffold-form dropped" }); } };
              if (!resp.ok) {
                const errBody = await resp.json().catch(() => ({}));
                throw new Error("HTTP " + resp.status + ": " + (errBody.error || resp.statusText));
              }
              const result = await resp.json();
              if (!result.ok) {
                throw new Error(result.error || "Unknown backend error");
              }
              // Success — show toast + reload
              const msg = result.existing
                ? "📂 Form detail '" + result.core_code + "' už existoval — otevírám."
                : "✅ Form detail '" + result.core_code + "' vytvořen (core_id=" + result.core_id + ", form_id=" + result.form_id + ").";
              // Simple inline notification (no Material toast — drobnost MVP)
              btn.style.background = "#2d5a2d";
              btn.textContent = msg;
              // Reload data + re-render after short pause
              setTimeout(() => {
                this._fetchData();
              }, 1200);
            } catch (e) {
              console.error("Scaffold form failed:", e);
              btn.disabled = false;
              btn.style.background = "#5a3a3a";
              btn.textContent = "❌ " + e.message.slice(0, 80);
              setTimeout(() => {
                btn.disabled = false;
                btn.style.background = "#3a5a3a";
                btn.textContent = "🪄 Vytvoř form detail";
              }, 4000);
            }
          });
          wrap.appendChild(btn);
        }

        emptySec.grid.appendChild(wrap);
        root.appendChild(emptySec.wrap);
      }

      // Section: Picker poli (placeholder Krok 14c)
      // Krok 14a-A1m #1: section title pair.
      const pickerSec = _sectionBuild("Výběr polí pro formulář", "fw.comp_def + fw.entity_def attributes (Krok 14c)");
      const pickerHint = document.createElement("div");
      pickerHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      pickerHint.textContent = "Vlevo dostupná pole (entity_def attributes), vpravo vybraná pro form. Drag-drop nebo dvojklik. Implementace v Kroku 14c.";
      pickerSec.grid.appendChild(pickerHint);
      root.appendChild(pickerSec.wrap);

      // Section: Data source (placeholder)
      const dsSec = _sectionBuild("Data — odkud čte, kam zapisuje", "fw.data_set + fw.data_source + fw.data_source_op (Krok 14b)");
      const dsHint = document.createElement("div");
      dsHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      dsHint.textContent = "fw.data_source linkovaný k tomuto jádru pro zápis. Mode: insert / update / upsert. Implementace v Kroku 14b.";
      dsSec.grid.appendChild(dsHint);
      root.appendChild(dsSec.wrap);

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14b (12.5.2026 vecer): DesignFwForm — generic
  // fw-native form renderer.
  //
  // Marti's pivot z 12.5. večera: dogfooding fw framework. Marti-AI's
  // flat-data doctrine: panels jsou v form's layout JSONB metadata,
  // fields mají region_slot=panel_slot. Žádný container comp_def per
  // panel — drží *„Container = Panel"* + *„Panel je v form template
  // embedded"* doctrines (Marti 12.5. ~21:30).
  //
  // Backend endpoint: GET /api/v1/erp/fw-form/{core_code}/{row_id}
  // Returns: {ok, core, form, fields, data}
  //
  // Rendering flow:
  //   1. Fetch backend → spec + data
  //   2. Iterate form.layout.panels → vyrender section header per panel
  //   3. Group fields by region_slot → render each field do svého panelu
  //   4. Per field: switch comp_type_code → _field (edit) / _dropdown (combobox)
  //
  // Read-only zatím (Phase 38.4 Krok 14b save flow ráno přes PATCH).
  // ────────────────────────────────────────────────────────────────────

  // Phase 38.4 Krok 5.R-C+8 (18.5.2026 vecer pozde): form pill drop-up menu helper.
  // Analog grid pill _showCoreInfoMenu (datagrid.js). Stand-alone IIFE-scoped
  // function, called z _ciPill click handler.

  global.DesignJadroRadekForm = DesignJadroRadekForm;

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
