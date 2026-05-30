/**
 * Design Forms — 3 hardcoded forms pro framework editor.
 *
 * Phase 38.4 Krok 14a (12.5.2026 ranni). Marti+Marti-AI's konsolidace:
 *   - Form 1+2 sloucene do `DesignSoudecekCoreForm` (2 taby pres ErpPageControl)
 *     Tab 'soudecek' = fw.menu_node fields
 *     Tab 'prehled'  = fw.core fields + (priste) inline grid editor fw.comp_def
 *   - Form 3 = `DesignJadroRadekForm` (1 tab MVP, prepared pro rozsireni)
 *     Tab 'jadro' = fw.core identity + (priste) field picker + data source
 *
 * MVP scope (Krok 14a):
 *   - Read-only fields, taby fungujou
 *   - Save NEZAREN (Krok 14b pozdeji)
 *   - Inline grid editor pro fw.comp_def NEZAREN (Krok 14b)
 *   - Field picker dvoupanelovy NEZAREN (Krok 14c)
 *
 * Marti's rytmus 12.5. rano: *"nejde to dat na prvni dobrou... bude se to
 * mesice vyvijet, tak jak fw poroste"*. Iterativni pristup.
 *
 * Dependencies:
 *   - ErpPageControl (components/pagecontrol.js)
 *   - ErpFormSection (components/formsection.js)
 *   - ErpInput, ErpCheckbox, ErpDropdown, ErpMemo, ErpFormList (components/*)
 *   - ErpButton (components/button.js) - pro modal footer
 *
 * Backend (Krok 14a):
 *   GET /api/v1/erp/design/menu-node/{id}  -> {menu_node, core}
 *   GET /api/v1/erp/design/jadro/{core_id} -> {core, columns_preview}
 */
(function (global) {
  "use strict";

  // Phase JS-8 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("design_forms.js", "v1.0.0", function () {


  // Phase JS-2 (18.5.2026): pull helpers from design_form_helpers.js
  // Loaded as separate <script> BEFORE this file (router.py loader order).
  const _DFH = global._erpDFH || {};
  const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
  const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
  const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
  const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
  const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
  const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
  const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
  const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  function _showFormPillMenu(pillBtn, ctx) {
    // Close existing
    var old = document.querySelector(".erp-form-coreinfo-menu");
    if (old) { old.remove(); return; }
    function _esc(s) {
      var d = document.createElement("div");
      d.textContent = String(s == null ? "" : s);
      return d.innerHTML;
    }
    var menu = document.createElement("div");
    menu.className = "erp-form-coreinfo-menu";
    menu.style.cssText =
      "position:absolute;bottom:36px;left:0;z-index:10000;" +
      "background:#1a2030;border:1px solid #3a4a6a;border-radius:4px;" +
      "padding:0;color:#e8eef5;font-size:11px;line-height:1.5;" +
      "box-shadow:0 -2px 8px rgba(0,0,0,0.4);min-width:260px;" +
      "font-family:ui-monospace,Consolas,Monaco,monospace;";

    var info = '<div style="padding:8px 12px;">';
    if (ctx.coreLabel) info += '<div style="font-weight:600;margin-bottom:6px;color:#a8b4c2;font-family:system-ui,sans-serif;">' + _esc(ctx.coreLabel) + '</div>';
    var rows = [];
    if (ctx.coreId != null) rows.push(["Core ID", String(ctx.coreId)]);
    if (ctx.rowId != null) rows.push(["Row ID", String(ctx.rowId)]);
    if (ctx.coreCode) rows.push(["Code", ctx.coreCode]);
    for (var i = 0; i < rows.length; i++) {
      info += '<div style="display:flex;gap:8px;"><span style="color:#7a8696;min-width:70px;">' +
        _esc(rows[i][0]) + ':</span><code style="color:#7aa8d4;font-variant-numeric:tabular-nums;">' +
        _esc(rows[i][1]) + '</code></div>';
    }
    info += '</div>';

    var pillText = String(ctx.coreId != null ? ctx.coreId : "?") + ":" + (ctx.rowId != null ? ctx.rowId : "");
    // Marti's 30.5.2026 ranní: "Core setting" prepended NAD design-core
    // (universal inspector pro fw.core metadata aktualniho core,
    // hardcoded coreId=49). Klik → DesignFwForm({coreId:49, rowId:ctx.coreId}).
    var actions =
      '<div style="border-top:1px solid #2a3a5a;padding:4px 0;font-family:system-ui,sans-serif;">' +
      '<button type="button" data-form-menu-action="core-setting" ' +
        'title="Otevře form 49 (Core inspector) s rowId=' + (ctx.coreId == null ? "?" : ctx.coreId) + ' — načte fw.core záznam id=' + (ctx.coreId == null ? "?" : ctx.coreId) + '" ' +
        'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;">' +
        '⚙️ Core setting</button>' +
      '<button type="button" data-form-menu-action="design-core" ' +
        'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;">' +
        '🎨 Otevřít Design jádra</button>' +
      '<button type="button" data-form-menu-action="copy-id" ' +
        'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;">' +
        '📋 Kopírovat <code style="color:#7aa8d4;">' + _esc(pillText) + '</code></button>' +
      '</div>';
    menu.innerHTML = info + actions;

    menu.querySelectorAll("button[data-form-menu-action]").forEach(function (mb) {
      mb.addEventListener("mouseenter", function () { mb.style.background = "rgba(122,168,212,0.1)"; });
      mb.addEventListener("mouseleave", function () { mb.style.background = "transparent"; });
      mb.addEventListener("click", function (ev) {
        ev.stopPropagation();
        var action = mb.getAttribute("data-form-menu-action");
        if (action === "copy-id") {
          try {
            navigator.clipboard.writeText(pillText).then(function () {
              var t = document.createElement("div");
              t.style.cssText = "position:absolute;bottom:8px;right:8px;z-index:10001;background:#3a5a3a;color:#fff;padding:4px 10px;border-radius:3px;font-size:11px;";
              t.textContent = "✓ Zkopírováno";
              menu.appendChild(t);
              setTimeout(function () { try { menu.remove(); } catch (e) {} }, 1200);
            });
          } catch (e) { menu.remove(); }
          return;
        }
        if (action === "core-setting") {
          // Marti's 30.5.2026 ranní: otevre Core setting inspector
          // (DesignFwForm s hardcoded coreId=49) pro current form core_id.
          console.info("[Core setting · FORM pill] click — ctx:", ctx);
          menu.remove();
          if (ctx.coreId == null) {
            console.warn("[Core setting · FORM pill] coreId=null in ctx, abort");
            alert("⚠ Core setting: chybí coreId v contextu formu");
            return;
          }
          console.info("[Core setting · FORM pill] new DesignFwForm({ coreId: 49, rowId: " + ctx.coreId + " })");
          try {
            var fwfCS = new DesignFwForm({ coreId: 49, rowId: ctx.coreId });
            console.info("[Core setting · FORM pill] constructor OK, calling open()");
            if (typeof fwfCS.open === "function") {
              fwfCS.open();
              console.info("[Core setting · FORM pill] open() returned");
            } else {
              console.warn("[Core setting · FORM pill] fwfCS.open is not a function:", fwfCS);
            }
          } catch (e) {
            console.error("[Core setting · FORM pill] DesignFwForm failed:", e);
          }
          return;
        }
        if (action === "design-core") {
          // Phase 38.4 Krok 5.R-C+9 (18.5.2026): resolve negative synthetic
          // coreId → positive fw.core row via /design/core-by-code endpoint.
          menu.remove();
          if (ctx.coreId == null) return;
          var _openDesignFwForm2 = function (resolvedCoreId) {
            try {
              var fwf = new DesignFwForm({ coreId: 23, rowId: resolvedCoreId });
              if (typeof fwf.open === "function") fwf.open();
            } catch (e) {
              console.error("[form pill menu] DesignFwForm failed:", e);
            }
          };
          if (ctx.coreId >= 0) {
            _openDesignFwForm2(ctx.coreId);
            return;
          }
          fetch("/api/v1/erp/design/core-by-code/" + encodeURIComponent("core_" + ctx.coreId),
                { credentials: "include" })
            .then(function (res) {
              if (!res.ok) throw new Error("HTTP " + res.status);
              return res.json();
            })
            .then(function (data) {
              if (data && data.core && data.core.id != null) {
                _openDesignFwForm2(data.core.id);
              } else {
                alert("Tento hardcoded form (core " + ctx.coreId + ") nemá fw.core záznam.");
              }
            })
            .catch(function (e) {
              console.error("[form pill menu] core-by-code resolve failed:", e);
            });
          return;
        }
      });
    });

    pillBtn.appendChild(menu);
    var closeFn = function (e) {
      if (!menu.contains(e.target) && e.target !== pillBtn) {
        try { menu.remove(); } catch (er) {}
        document.removeEventListener("click", closeFn, true);
      }
    };
    setTimeout(function () { document.addEventListener("click", closeFn, true); }, 0);
  }

  class DesignFwForm {
    constructor(opts) {
      this.opts = opts || {};
      // Phase 38.4 Krok 14g Etapa F Step E.1 (16.5.2026, Marti's "pro jistotu
      // o vikendu"): drop coreCode EXTERNAL — constructor refuses coreCode
      // parameter. Pokud caller jeste posila coreCode, console.error +
      // _erpLogToDb error event (visible v fw.diag_log).
      //
      // Internal: open() lazy-resolves coreCode-from-coreId pres /fw-form/by-id
      // endpoint pro subsequent URL builds (children/save/refresh).
      //
      // Constructor signature:
      //   opts.coreId   (required — fw.core.id, e.g. 22)
      //   opts.rowId    (required — data row ID, e.g. users.id=14)
      if (this.opts.coreCode && !this.opts.coreId) {
        const _errMsg = "DesignFwForm: coreCode parameter NOT SUPPORTED (Etapa F Step E.1 drop). Pass coreId instead.";
        console.error(_errMsg);
        if (typeof window !== "undefined" && window._erpLogToDb) {
          try {
            window._erpLogToDb.error("design_forms.js", _errMsg, {
              extra: { passed_coreCode: this.opts.coreCode, passed_rowId: this.opts.rowId },
            });
          } catch (e) { /* fail-safe */ }
        }
        // Constructor must not throw (existing flow chains .open() — let validation
        // handle it in open()). Mark coreId missing for open() to bail.
        this.opts._etapaFInvalid = true;
      } else if (!this.opts.coreId) {
        console.error("DesignFwForm: coreId required");
        this.opts._etapaFInvalid = true;
      }
      this._shell = null;
      this._spec = null;       // backend response: {core, form, fields, data}
      this._dirty = new Set();
      this._saveBtn = null;
      this._dirtyBadge = null;
      // Phase 38.4 Krok 14b+7 (13.5.2026 ~20:00, Marti's "PROD/DESIGN
      // trigger i na tom formu"): per-form mode flag, separate od
      // window._erpDesignMode (global). Default PRODUCTION (safe — uzivatel
      // otevre form, nesahá na strukturu nahodne). DESIGN mode aktivuje
      // field picker + design-only UI. Toggle button v header (visible
      // jen pokud global _erpDesignMode = true).
      this._formDesignMode = false;
      this._formDesignToggle = null;  // ref na button v header
    }

    // Phase 38.4 Krok 14b+7: helper pro UI re-render po toggle change.
    // Re-render je nutny aby empty hint, field actions, drag handles, atd.
    // reaktivne reflektovaly novy mode. Toggle se sama nepre-render — to
    // udela _updateFormDesignToggle.
    _setFormDesignMode(on) {
      this._formDesignMode = !!on;
      this._updateFormDesignToggle();
      this._updateFormAddFieldBtn();  // Krok 14b+7.1: "+ Pole" button visibility
      // Krok 5.M-3 (17.5.2026): 🎯 Entita button dropped (Krok 5.F doctrine
      // "vyber entity uz kdyz jsme na formulari tam nepatri" + Krok 5.M
      // "core nenese entitu, nese ji obsah").
      this._updateFormSaveSizeBtn();  // Krok 14b+11: 💾 Velikost button visibility
      this._updateFormDetectMinBtn(); // Krok 14b+12: 📐 Min button visibility
      if (this._spec) {
        // Re-render body (zachovat header) — hints + click handlers nove
        this._render();
      }
    }

    _updateFormDesignToggle() {
      if (!this._formDesignToggle) return;
      const on = this._formDesignMode;
      this._formDesignToggle.textContent = on ? "🎨 DESIGN" : "📋 PRODUCTION";
      this._formDesignToggle.title = on
        ? "Form je v DESIGN módu — můžeš přidávat pole + editovat strukturu. Klikni pro PRODUCTION."
        : "Form je v PRODUCTION módu — jen edit dat. Klikni pro DESIGN (přidávání polí).";
      // Vizuálně: DESIGN = teal akcent (analog global DESIGN badge),
      // PRODUCTION = neutral šedý.
      this._formDesignToggle.style.cssText =
        "background:" + (on ? "#1f4858" : "#1f2530") + ";" +
        "border:1px solid " + (on ? "#3a8aa8" : "#2a3340") + ";" +
        "color:" + (on ? "#7ed4e8" : "#cfd6df") + ";" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:" + (on ? "600" : "400") + ";";
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-D (15.5.2026 rano, Marti's volba A "simple
    // undo, jeden dva kroky zpet a je happy"): memory-only operation
    // history. Per-session, no DB persist.
    //
    // _undoStack = array of { label, inverse } entries (max 15)
    // _pushUndoOp called BEFORE destructive action, snapshots state.
    // _performUndo pops last + executes inverse, reload spec.
    //
    // Coverage:
    //   - Delete → inverse: PATCH is_active=true
    //   - Move (cross-parent) → inverse: PATCH parent + sort_order back
    //   - Reorder (same-parent) → inverse: PUT field_orders s old order
    //   - Settings save → inverse: PATCH caption + layout back
    //   - Create from gallery → inverse: DELETE new id
    // ════════════════════════════════════════════════════════════════
    _ensureUndoStack() {
      if (!Array.isArray(this._undoStack)) this._undoStack = [];
    }

    _pushUndoOp(label, inverse) {
      this._ensureUndoStack();
      this._undoStack.push({ label, inverse });
      // Keep max 15 (drop oldest)
      if (this._undoStack.length > 15) {
        this._undoStack.shift();
      }
      this._updateUndoButton();
    }

    _updateUndoButton() {
      const btn = this._formUndoBtn;
      if (!btn) return;
      this._ensureUndoStack();
      const n = this._undoStack.length;
      if (n === 0) {
        btn.style.opacity = "0.4";
        btn.disabled = true;
        btn.textContent = "↶ Zpět";
        btn.title = "Žádná akce k vrácení";
      } else {
        btn.style.opacity = "1";
        btn.disabled = false;
        btn.textContent = "↶ Zpět (" + n + ")";
        const last = this._undoStack[n - 1];
        btn.title = "Vrátit: " + last.label + " (Ctrl+Z)";
      }
    }

    async _performUndo() {
      this._ensureUndoStack();
      if (this._undoStack.length === 0) {
        _showToast("Nic k vrácení", "info", 1500);
        return;
      }
      const op = this._undoStack.pop();
      this._updateUndoButton();
      try {
        _showToast("Vracím: " + op.label, "info", 1500);
        await op.inverse();
        _showToast("✓ Vráceno: " + op.label, "success", 2000);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] undo failed:", e);
        _showToast("Vrácení selhalo: " + (e.message || e), "error", 3500);
        // Push back na stack (preserve order pokud user chce retry)
        this._undoStack.push(op);
        this._updateUndoButton();
      }
    }

    _attachFormDesignToggle() {
      // Krok 14b+7: toggle button visible jen pokud global ERP DESIGN
      // je ON. Bez global flagu form je vzdy PRODUCTION (zadny toggle
      // available — uzivatel nesmi sahat na strukturu).
      if (!this._shell || !this._shell.header) return;
      if (window._erpDesignMode !== true) return;  // gate
      const rightActions = this._shell.header.querySelector(".erp-modal-header-actions");
      if (!rightActions) return;
      // Defensive: nepridavat duplikat (pri opt-out / re-open)
      if (rightActions.querySelector(".erp-form-design-toggle")) return;

      // Toggle button — PROD / DESIGN switch
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "erp-form-design-toggle";
      this._formDesignToggle = toggle;
      this._updateFormDesignToggle();  // initial text + style
      toggle.addEventListener("click", () => {
        this._setFormDesignMode(!this._formDesignMode);
      });

      // Krok 14b+7.1 (13.5.2026 ~20:30, Marti's "po pridani 1 pole hint
      // zmizi, nikde jinde nelze pridat"): "+ Pole" button vedle toggle.
      // Visible JEN v DESIGN mode. Klik -> _openFieldPicker (vsechny entry
      // points -- empty hint, footer hint, header button -- volaji stejnou
      // logiku).
      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.className = "erp-form-design-addfield";
      addBtn.textContent = "➕ Pole";
      addBtn.title = "Přidat pole do formuláře (otevře paletu komponent).";
      this._formAddFieldBtn = addBtn;
      this._updateFormAddFieldBtn();  // initial visibility (hidden bo PRODUCTION default)
      addBtn.addEventListener("click", () => {
        this._openFieldPicker();
      });

      // Krok 14b+11 (13.5.2026 ~23:00, Marti's "ukladat vychozi velikost
      // formu"): 💾 Velikost button. Visible jen v DESIGN mode. Click ->
      // getBoundingClientRect aktualniho dialogu -> PATCH form layout
      // JSONB s default_width + default_height -> toast.
      const saveSizeBtn = document.createElement("button");
      saveSizeBtn.type = "button";
      saveSizeBtn.className = "erp-form-design-savesize";
      saveSizeBtn.textContent = "💾 Velikost";
      saveSizeBtn.title = "Uložit aktuální výšku a šířku jako výchozí pro tento formulář.";
      this._formSaveSizeBtn = saveSizeBtn;
      this._updateFormSaveSizeBtn();  // initial visibility
      saveSizeBtn.addEventListener("click", () => {
        this._saveFormDefaultSize();
      });

      // Krok 14b+12 (13.5.2026 ~23:30, Marti's "detekovat min velikost"):
      // 📐 Min button. Auto-detect kde fields zacnou "ukrajovat"
      // (overflow). Iterate decrement width od current down po 20px until
      // scrollWidth > clientWidth. Save layout.min_width / _height.
      const detectMinBtn = document.createElement("button");
      detectMinBtn.type = "button";
      detectMinBtn.className = "erp-form-design-detectmin";
      detectMinBtn.textContent = "📐 Min";
      detectMinBtn.title = "Auto-detekce minimální velikosti formuláře — najít hranici kde komponenty začnou být ukrojené.";
      this._formDetectMinBtn = detectMinBtn;
      this._updateFormDetectMinBtn();
      detectMinBtn.addEventListener("click", () => {
        this._detectAndSaveMinSize();
      });

      // Phase 38.4 Krok 14g-D (15.5.2026 rano, Marti's volba A simple
      // undo): ↶ Zpět button. Visible jen v DESIGN mode. Click → pop
      // last undoStack entry + execute inverse.
      const undoBtn = document.createElement("button");
      undoBtn.type = "button";
      undoBtn.className = "erp-form-design-undo";
      undoBtn.textContent = "↶ Zpět";
      this._formUndoBtn = undoBtn;
      this._updateUndoButton();  // initial: opacity 0.4 / disabled
      undoBtn.addEventListener("click", () => {
        this._performUndo();
      });

      // Phase 38.4 Krok 5.M-3 (17.5.2026): 🎯 Entita button DROPPED.
      // Krok 5.F doctrine + Krok 5.M "core nenese entitu". Button + handler
      // + _openEntityTypePicker method removed jako dead code.
      // Ctrl+Z keyboard shortcut — capture phase aby browser default
      // (undo v inputu) nepřebijel (jen pokud focus mimo input).
      this._undoKeyHandler = (ev) => {
        if ((ev.ctrlKey || ev.metaKey) && ev.key === "z" && !ev.shiftKey) {
          const t = ev.target;
          const tag = t && t.tagName;
          if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
          if (this._formDesignMode !== true) return;
          ev.preventDefault();
          ev.stopPropagation();
          this._performUndo();
        }
      };
      document.addEventListener("keydown", this._undoKeyHandler, true);

      // Insert PRED sysToggle (= prvni button v rightActions) — toggle
      // je hlavni mode switch, ostatni jsou pomocna nastaveni.
      // Order v rightActions po insertBefore (kazdy pred sysToggle):
      //   toggle -> undoBtn -> addBtn -> saveSizeBtn -> detectMinBtn -> sysToggle
      //   (leftmost to rightmost)
      const sysToggle = rightActions.querySelector(".erp-design-systoggle");
      if (sysToggle) {
        rightActions.insertBefore(toggle, sysToggle);
        rightActions.insertBefore(undoBtn, sysToggle);
        rightActions.insertBefore(addBtn, sysToggle);
        rightActions.insertBefore(saveSizeBtn, sysToggle);
        rightActions.insertBefore(detectMinBtn, sysToggle);
      } else {
        // Fallback: prepend (reverse order)
        rightActions.insertBefore(detectMinBtn, rightActions.firstChild);
        rightActions.insertBefore(saveSizeBtn, rightActions.firstChild);
        rightActions.insertBefore(addBtn, rightActions.firstChild);
        rightActions.insertBefore(undoBtn, rightActions.firstChild);
        rightActions.insertBefore(toggle, rightActions.firstChild);
      }
    }

    _updateFormDetectMinBtn() {
      if (!this._formDetectMinBtn) return;
      const on = this._formDesignMode === true;
      const visible = on && !!(this._spec && this._spec.form && this._spec.form.id);
      this._formDetectMinBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    async _detectAndSaveMinSize() {
      // Krok 14b+12: auto-detect min size via iterate decrement +
      // overflow check. Algorithm:
      //   1. Save current dialog dimensions
      //   2. Remove min constraints temporarily (allow shrinking)
      //   3. Iterate decrement width (current → 200px, step 20px)
      //      - Each step: set width, await rAF, check overflow
      //      - First overflow = found minimum
      //   4. Height: header + footer + min body (100px) — static calc
      //   5. PATCH save min_width + min_height
      //   6. Restore dialog to original size + apply new mins
      if (!this._spec || !this._spec.form || !this._spec.form.id) {
        _showToast("Form ID chybí v spec", "error");
        return;
      }
      const dialog = this._shell && this._shell.dialog;
      if (!dialog) {
        _showToast("Dialog reference chybí", "error");
        return;
      }

      // Save original state pro restore
      const origW = dialog.style.width;
      const origH = dialog.style.height;
      const origMinW = dialog.style.minWidth;
      const origMinH = dialog.style.minHeight;
      const origTransition = dialog.style.transition;

      _showToast("Detekce minimální velikosti…", "info", 1500);

      // Temporarily remove min constraints (allow shrinking past current
      // min) + disable transitions (instant resize per step)
      dialog.style.minWidth = "0";
      dialog.style.minHeight = "0";
      dialog.style.transition = "none";

      try {
        // === WIDTH DETECTION (iterate + horizontal overflow check) ===
        const startW = dialog.clientWidth;
        let lastOKWidth = startW;
        let testW = startW;
        const STEP_W = 20;
        const FLOOR_W = 200;
        while (testW > FLOOR_W) {
          dialog.style.width = testW + "px";
          await new Promise((r) => requestAnimationFrame(r));
          if (this._hasHorizontalOverflow(dialog)) {
            break;
          }
          lastOKWidth = testW;
          testW -= STEP_W;
        }
        const minWidth = Math.max(lastOKWidth + STEP_W, FLOOR_W);

        // Restore width PRED height detection (isolated test axes)
        dialog.style.width = origW;
        await new Promise((r) => requestAnimationFrame(r));

        // === HEIGHT DETECTION (iterate + vertical overflow check) ===
        // Krok 14b+12.1 (13.5.2026 ~23:50, Marti's "u vysky to chce jeste
        // nejakou korekci"): static calc (header + footer + 120px) byla
        // moc malá — body fields scrollované za footer. Replace dynamic
        // iterate decrement (analog width) — first body overflow = found
        // boundary kde fields zacnou byt skryté za footer.
        //
        // Krok 14b+12.2 (13.5.2026 ~00:10, Marti's korekce po smoke:
        // "Asi to chce korekci o vysku hlavicky + vysku paticky"):
        // iterate detekuje overflow boundary, ale visible body content
        // muze mit edge case (padding mimo scrollHeight diff, sub-pixel
        // rounding). Marti's intuition: PLUS bezpecnostni polštář =
        // header.offsetHeight + footer.offsetHeight. To garantuje ze pri
        // min height body content area >= "lastOK content" + (jeste jednou
        // chrome velikost) → fields VŽDY visible bez nutnosti scroll.
        const startH = dialog.clientHeight;
        let lastOKHeight = startH;
        let testH = startH;
        const STEP_H = 20;
        const FLOOR_H = 200;
        while (testH > FLOOR_H) {
          dialog.style.height = testH + "px";
          // Double rAF pro robust layout reflow (1x bylo nedostatecne v
          // edge cases — Marti's height korekce smoke odhalila)
          await new Promise((r) => requestAnimationFrame(r));
          await new Promise((r) => requestAnimationFrame(r));
          if (this._hasVerticalOverflow(dialog)) {
            break;
          }
          lastOKHeight = testH;
          testH -= STEP_H;
        }
        // Marti's korekce: + headerH + footerH bezpecnostni polštář
        const headerEl = dialog.querySelector(".erp-modal-header");
        const footerEl = dialog.querySelector(".erp-modal-footer");
        const headerH = headerEl ? headerEl.offsetHeight : 50;
        const footerH = footerEl ? footerEl.offsetHeight : 50;
        const minHeight = Math.max(
          lastOKHeight + headerH + footerH,
          FLOOR_H
        );
        console.info(
          "[DesignFwForm] min height calc: lastOK=" + lastOKHeight +
          " + header=" + headerH + " + footer=" + footerH +
          " = " + minHeight + "px"
        );

        // === Restore original size ===
        dialog.style.width = origW;
        dialog.style.height = origH;
        // Apply new mins (browser CSS prevent shrink under)
        dialog.style.minWidth = minWidth + "px";
        dialog.style.minHeight = minHeight + "px";
        dialog.style.transition = origTransition;

        // === PATCH save ===
        const newLayout = Object.assign({}, this._spec.form.layout || {}, {
          min_width: minWidth + "px",
          min_height: minHeight + "px",
        });
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(this._spec.form.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        this._spec.form.layout = newLayout;
        _showToast(
          "Min velikost detekována: " + minWidth + " × " + minHeight + " px",
          "success",
          2500
        );
      } catch (e) {
        // Restore original state na fail
        dialog.style.width = origW;
        dialog.style.height = origH;
        dialog.style.minWidth = origMinW;
        dialog.style.minHeight = origMinH;
        dialog.style.transition = origTransition;
        console.error("[DesignFwForm] detect min failed:", e);
        _showToast("Detekce selhala: " + (e.message || e), "error", 3500);
      }
    }

    _hasHorizontalOverflow(dialog) {
      // Check #1: dialog content exceeds dialog client width
      // (rare protoze dialog ma overflow:hidden, ale defensive)
      if (dialog.scrollWidth > dialog.clientWidth + 1) return true;
      // Check #2: any field input clipped horizontally
      // (form's grid auto-fit minmax(220px, 1fr) — when modal < 220+padding,
      // grid item shrinks below 220 a input overflow contains its label/value)
      const inputs = dialog.querySelectorAll(
        "input, select, textarea, .erp-input-input, .erp-dropdown-trigger"
      );
      for (let i = 0; i < inputs.length; i++) {
        const el = inputs[i];
        // scrollWidth > clientWidth = horizontal content overflow (text
        // clipped). +2px tolerance for sub-pixel rounding.
        if (el.scrollWidth > el.clientWidth + 2) return true;
      }
      // Check #3: grid main panel scrollWidth (grid items extending beyond)
      const grid = dialog.querySelector(".erp-design-grid");
      if (grid && grid.scrollWidth > grid.clientWidth + 1) return true;
      return false;
    }

    _hasVerticalOverflow(dialog) {
      // Krok 14b+12.1 (13.5.2026 ~23:50, Marti's height korekce):
      // Detekuje kdy body fields zacnou byt skryté za footer (body
      // ma overflow-y:auto → scrollbar appear když scrollHeight > clientHeight).
      //
      // Marti's UX kriterium: VŠECHNY fields musi byt visible bez scroll.
      // Pokud body scrolly, posledni field je hidden za footer → moc malá výška.
      //
      // Check #1: body scrollHeight > clientHeight (primary signal)
      const body = dialog.querySelector(".erp-modal-body");
      if (body && body.scrollHeight > body.clientHeight + 2) return true;
      // Check #2: root grid scrollHeight > clientHeight (root je body content)
      const root = dialog.querySelector(".erp-design-tab-content");
      if (root && root.scrollHeight > root.clientHeight + 2) return true;
      return false;
    }

    _updateFormSaveSizeBtn() {
      if (!this._formSaveSizeBtn) return;
      const on = this._formDesignMode === true;
      // Visible jen v DESIGN mode (analog addFieldBtn). Visible vzdy v
      // DESIGN, ne hover-only — Marti chce easy klik pro save size.
      const visible = on && !!(this._spec && this._spec.form && this._spec.form.id);
      this._formSaveSizeBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    async _saveFormDefaultSize() {
      // Krok 14b+11: PATCH form root comp_def layout s aktualnimi
      // dialog dimensions. _spec.form.id je root form comp_def (type_id=302).
      if (!this._spec || !this._spec.form || !this._spec.form.id) {
        _showToast("Form ID chybí v spec", "error");
        return;
      }
      if (!this._shell || !this._shell.dialog) {
        _showToast("Dialog reference chybí", "error");
        return;
      }
      const dialog = this._shell.dialog;
      // getBoundingClientRect vrati actual rendered size (po user resize
      // pres CSS resize:both v dialog.style).
      const rect = dialog.getBoundingClientRect();
      const w = Math.round(rect.width);
      const h = Math.round(rect.height);
      // Defensive sanity (modal nesmi byt menší nez prakticky pouzitelne)
      if (w < 400 || h < 300) {
        _showToast(
          "Velikost je moc malá (" + w + "×" + h + "). Min 400×300.",
          "error",
          3000
        );
        return;
      }
      const currentLayout = (this._spec.form.layout && typeof this._spec.form.layout === "object")
        ? this._spec.form.layout
        : {};
      const newLayout = Object.assign({}, currentLayout, {
        default_width: w + "px",
        default_height: h + "px",
      });
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(this._spec.form.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        // Update local spec consistency — pri pristim open() pripada uz z
        // backendu, ale instant local update pro current session
        this._spec.form.layout = newLayout;
        _showToast(
          "Výchozí velikost uložena (" + w + " × " + h + " px)",
          "success"
        );
      } catch (e) {
        console.error("[DesignFwForm] save size failed:", e);
        _showToast("Uložení velikosti selhalo: " + (e.message || e), "error", 3500);
      }
    }

    _updateFormAddFieldBtn() {
      if (!this._formAddFieldBtn) return;
      const on = this._formDesignMode === true;
      // Visible jen v DESIGN mode + pokud picker je vubec dostupny
      // (entity_type + formId + FieldPickerModal class). Pred _spec
      // loaded jen schovat default.
      const canPick = this._canPickFields();
      const visible = on && canPick;
      this._formAddFieldBtn.style.display = visible ? "" : "none";
      this._formAddFieldBtn.style.cssText =
        "background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;" +
        "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
        "font-weight:600;" +
        (visible ? "" : "display:none;");
    }

    // Phase 38.4 Krok 5.M-3 (17.5.2026): _updateFormEntityBtn + _openEntityTypePicker
    // methods DROPPED. Krok 5.F doctrine "entity volba na formulari nepatri"
    // + Krok 5.M "core nenese entitu". ~270 řádků dead code removed.

    _canPickFields() {
      // Krok 14b+7.1: shared predicate — kdy je field picker dostupny.
      // Pouziva header "+ Pole" button + empty hint + footer hint.
      //
      // Krok 5.J-B6 hotfix (16.5.2026 ~24:40, Marti's "+Pole se nezobrazuje
      // na hlavicce formu"): drop strict data_entity_type check. Po Krok 5.A
      // "core = kontejner" doctrine může být data_entity_type=NULL pro drafted
      // core. Picker show button v DESIGN mode + form has root; _openFieldPicker
      // validates entity_type runtime — pokud null, info dialog "set entity first".
      if (!this._spec) return false;
      const core = this._spec.core;
      const form = this._spec.form;
      if (!core || !form) return false;
      if (!form.id) return false;
      if (typeof global.FieldPickerModal !== "function") return false;
      return true;
    }

    async _openFieldPicker() {
      // Krok 14b+7.1: shared handler pro vsechny field picker entry points
      // (header "+ Pole" button, empty hint click, footer hint click).
      // Bez tohoto helperu jsou 3 misto stejne logiky -- duplicita.
      if (!this._canPickFields()) {
        console.warn("[DesignFwForm] _openFieldPicker called but not canPick");
        return;
      }
      const core = this._spec.core;
      const formId = this._spec.form.id;

      // Phase 38.4 Krok 5.M-3 (17.5.2026): drop data_entity_type pre-check
      // (Krok 5.M "core nenese entitu") + drop _openEntityTypePicker call
      // (Krok 5.F dead code removed). FieldPickerModal dostane core.code
      // jako entityType — picker server resolves columns from map alias.

      // Phase 38.4 Krok 5.N-2b (17.5.2026, Marti's "code je optional, ID
      // je truth"): entityType = String(core.id) misto core.code. URL build
      // /design/entity-columns/22 (ID-based). Backend dispatcher detekuje
      // numeric vs string a routes podle _FW_FORM_CORE_REGISTRY (ID-based)
      // nebo _FW_FORM_ENTITY_MAP (legacy string fallback). Marti's rename
      // code na cokoliv neproblém — ID je truth.
      // Krok 5.X (27.5.2026): nested grids jsou teted fw.comp_def rows
      // (type_id=304 'nested_grid', kind='container'). Palette uvidi
      // automaticky pres existing recursive descent (existing_containers_out
      // query WHERE type_kind='container'). H+13.4 fake childComponents
      // passing dropped — no longer needed.
      const picker = new global.FieldPickerModal({
        entityType: core.id != null ? String(core.id) : (core.code || core.data_entity_type),
        parentCompDefId: formId,
        // Phase 38.4 Krok H+5 (26.5.2026, Marti's "vyjit z rozchozenych
        // komponent"): paleta deleguje ⚙ klik na existing _openFieldSettings.
        // Najde field v this._spec.fields by id + zavolá popup. Existing
        // popup uz ma per-type detection (entity_picker tab, max_length pro
        // text inputy, atd.) — Marti's "kazda komponenta jinak" priorita.
        onOpenSettings: (compDefId) => {
          try {
            // Krok 5-B (29.5.2026, Marti's "sjednot tu dva ruzna okna
            // parametru"): unified _openFieldSettings handles fields +
            // containers. Container lookup z __renderCtx.byParent (kde
            // jsou panel/groupbox/tabsheet/pagecontrol cached pri renderu).
            const fields = (this._spec && this._spec.fields) || [];
            let comp = fields.find(f => f.id === compDefId);
            if (!comp) {
              // Try containers — iterate byParent map
              const ctx = this.__renderCtx || {};
              const byParent = ctx.byParent || new Map();
              for (const arr of byParent.values()) {
                if (!Array.isArray(arr)) continue;
                const found = arr.find(c => c && c.id === compDefId);
                if (found) { comp = found; break; }
              }
            }
            if (!comp) {
              console.warn("[DesignFwForm] onOpenSettings: comp id=" + compDefId + " nenalezen v spec.fields ani v byParent containers");
              alert("Komponenta id=" + compDefId + " nebyla nalezena ve formuláři (možná smazána). Obnov paletu.");
              return;
            }
            this._openFieldSettings(comp);
          } catch (e) {
            console.error("[DesignFwForm] onOpenSettings failed:", e);
            alert("Settings popup selhal: " + (e.message || e));
          }
        },
        onActiveContainerChange: (compDefId) => {
          try {
            const root = this._shell && this._shell.body;
            if (!root) return;
            // Drop predchozi highlight
            root.querySelectorAll(".erp-design-active-container").forEach(el => {
              el.classList.remove("erp-design-active-container");
            });
            // Apply na novy target
            if (compDefId != null) {
              const target = root.querySelector(
                '[data-comp-def-id="' + compDefId + '"]'
              );
              if (target) {
                target.classList.add("erp-design-active-container");
              }
            }
          } catch (e) {
            console.error("[DesignFwForm] active container highlight failed:", e);
          }
        },
        // Phase 38.4 Krok H+7 (26.5.2026, Marti's "fajn orchestrovat klikem
        // na komponentu i komponentu v druhem okne. Zvyraznit ji"):
        // Klik na radek v palete "Jiz na forme" → flash highlight komponenty
        // na formulari. Selector [data-comp-def-id="X"] matchne fields
        // (unified pres dataset.compDefId = field.id) i containers
        // (panel/groupbox/pagecontrol/tabsheet). Scroll do view + transient
        // flash (orange outline ~1.5s) — Marti vidi presne kde komponenta
        // sedi i kdyz je v jinem tab sheetu nebo mimo viewport.
        onHighlightComponent: (compDefId) => {
          try {
            const root = this._shell && this._shell.body;
            if (!root || compDefId == null) return;
            const target = root.querySelector(
              '[data-comp-def-id="' + compDefId + '"]'
            );
            if (!target) {
              console.info("[DesignFwForm] highlightComponent: id=" + compDefId + " nenalezen v DOM (možná uvnitr neaktivniho tabu)");
              return;
            }
            // Drop predchozi flash (jednotlive highlighty)
            root.querySelectorAll(".erp-design-flash-highlight").forEach(el => {
              el.classList.remove("erp-design-flash-highlight");
            });
            // Scroll do view (smooth, center pokud lze)
            try {
              target.scrollIntoView({ behavior: "smooth", block: "center" });
            } catch (e) {
              try { target.scrollIntoView(); } catch (e2) {}
            }
            // Flash class na ~1.5s
            target.classList.add("erp-design-flash-highlight");
            setTimeout(() => {
              try { target.classList.remove("erp-design-flash-highlight"); } catch (e) {}
            }, 1500);
          } catch (e) {
            console.error("[DesignFwForm] onHighlightComponent failed:", e);
          }
        },
        onComplete: async (result) => {
          console.info("[DesignFwForm] FieldPicker complete:", result);
          // Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr on time"):
          // Live sync paleta ↔ form. Po add/remove v palete refetch form
          // spec + re-render. Pouzij ID-first endpoint (drafted cores maji
          // core.code=NULL → "/fw-form/null/X" 404). Fallback na code-based
          // endpoint pro legacy cores bez core.id.
          try {
            const coreId = this._spec.core && this._spec.core.id;
            const coreCode = this._spec.core && this._spec.core.code;
            const rowId = (this._spec.data && this._spec.data.id) || 0;
            let url;
            if (coreId != null) {
              url = "/api/v1/erp/fw-form/by-id/" +
                    encodeURIComponent(coreId) + "/" +
                    encodeURIComponent(rowId);
            } else if (coreCode) {
              url = "/api/v1/erp/fw-form/" +
                    encodeURIComponent(coreCode) + "/" +
                    encodeURIComponent(rowId);
            } else {
              console.error("[DesignFwForm] reload: no core.id nor core.code");
              return;
            }
            const r = await fetch(url, { credentials: "include" });
            if (r.ok) {
              const newSpec = await r.json();
              if (newSpec.ok) {
                this._spec = newSpec;
                this._render(); // re-render s novými fields
              }
            } else {
              console.error("[DesignFwForm] reload HTTP", r.status, url);
            }
          } catch (e) {
            console.error("[DesignFwForm] reload after picker failed:", e);
          }
        },
      });
      await picker.open();
    }

    _onDirty(fieldKey, isDirty) {
      if (isDirty) this._dirty.add(fieldKey);
      else this._dirty.delete(fieldKey);
      const count = this._dirty.size;
      if (this._saveBtn) this._saveBtn.style.display = count > 0 ? "" : "none";
      if (this._dirtyBadge) {
        const _wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
        this._dirtyBadge.textContent = count > 0 ? "● " + count + " " + _wBadge : "";
        this._dirtyBadge.style.display = count > 0 ? "" : "none";
      }
      // Krok 14b+16 (14.5.2026 rano, Marti's polish):
      //   1. Title bar zachovava AMBER accent pri dirty (visual signal)
      //   2. ALE textContent BEZ "● N změn" — vyhodit count z hlavicky
      //   3. Footer ma decent "● N změn" button (clickable revert) — _renderDirtyDiscardBtn
      // Marti: "Z hlavicky vyhodit ostatni text ohledne zmen.
      //         Pridat do paticky doleva ten kontext."
      if (this._shell && this._shell.title) {
        const baseTitle = this._spec && this._spec.core
          ? (this._spec.core.label || this._spec.core.code || "Editace")
          : "Editace";
        this._shell.title.textContent = baseTitle;  // VZDY base, bez count
        this._shell.title.style.color = count > 0 ? "#d4b88a" : "";  // amber pri dirty
      }
      // Refresh footer dirty discard button (visible jen pokud count > 0)
      this._updateDirtyDiscardBtn();
      _markFormDirty(this, count > 0);
    }

    _updateDirtyDiscardBtn() {
      if (!this._dirtyDiscardBtn) return;
      const count = this._dirty.size;
      // Krok 14b+16.1: flex spacer v footeru drzi OK+Storno vpravo bez
      // ohledu na discard visibility. Jen toggle display:
      if (count === 0) {
        this._dirtyDiscardBtn.style.display = "none";
        return;
      }
      const wBadge = count === 1 ? "změna" : (count < 5 ? "změny" : "změn");
      this._dirtyDiscardBtn.textContent = "● " + count + " " + wBadge;
      this._dirtyDiscardBtn.style.display = "";
    }

    async _revertAllChanges() {
      // Krok 14b+16: discard all dirty changes — reset každý field na origVal.
      // Body fields jsou v sec.grid (per panel), kazdy field el ma _inst.
      // Pro _field-based widgets (_inst.input.value = origVal),
      // Pro checkbox/_dropdown vlastni reset.
      if (!this._shell || !this._shell.body) return;
      const fieldEls = this._shell.body.querySelectorAll("[data-design-fieldkey]");
      console.group("[DesignFwForm._revertAllChanges] DIAG");
      console.log("fieldEls count:", fieldEls.length, "dirty set size:", this._dirty.size);
      const visited = new Set();
      fieldEls.forEach((el) => {
        // Find ancestor with _inst + _origVal (field wrapper)
        let wrap = el;
        while (wrap && !(wrap._inst && "_origVal" in wrap)) {
          wrap = wrap.parentElement;
          if (wrap === this._shell.body) { wrap = null; break; }
        }
        if (!wrap || !wrap._inst) return;
        const fk = wrap._fieldKey;
        if (!fk || visited.has(fk)) return;
        visited.add(fk);
        try {
          const orig = wrap._origVal;
          // DIAG (28.5.2026 vecer pozde): log every revert attempt
          const _diagCurDom = wrap._inst.input
            ? wrap._inst.input.value
            : (wrap._inst.textarea ? wrap._inst.textarea.value : "?");
          console.log(
            "[revert]", fk,
            "| _origVal=", JSON.stringify(orig),
            "| DOM.value PRED=", JSON.stringify(_diagCurDom),
            "| has setValue=", typeof wrap._inst.setValue === "function",
            "| has .input=", !!wrap._inst.input,
            "| has .textarea=", !!wrap._inst.textarea,
            "| _inst ctor=", wrap._inst.constructor && wrap._inst.constructor.name,
          );
          // Krok 5-A v3+ hotfix (28.5.2026 vecer pozde, Marti's "Zrusit
          // nevraci puvodni hodnoty"): setValue() jako PRIMARY path.
          //
          // Predtim wrap._inst.input.value = ... direct setoval DOM, ale
          // ErpInput interne cachuje _displayValue/_rawValue v setValue()
          // (input.js line 479-491). Direct .value bypass = internal state
          // stale → save flow inst.value() pak vratil staru post-edit
          // hodnotu, ne revertovanou.
          //
          // ErpInput/ErpMemo/ErpDropdown VŠECHNY maji setValue() — single
          // unified path. Checkbox je jediny special case (no setValue).
          //
          // ROOT CAUSE FIX (28.5.2026 vecer pozde, Marti's "edit text
          // nefunguje, combobox ano"): predtim `"checked" in input` test
          // chytal VSECHNY <input> elementy (HTMLInputElement ma checked
          // property nativne, nejen checkbox). ErpInput tak vzdy hit
          // checkbox vetev → input.checked = !!orig (no-op pro text) →
          // setValue() se NIKDY nezavolal. Discriminace musi byt
          // input.type === "checkbox", ne pouhe "checked" in input.
          if (wrap._inst.input && wrap._inst.input.type === "checkbox") {
            // Checkbox — special case (no setValue API)
            wrap._inst.input.checked = !!orig;
            const valLabel = wrap.querySelector("span");
            if ((valLabel && valLabel.textContent === "Ano") || (valLabel && valLabel.textContent === "Ne")) {
              valLabel.textContent = wrap._inst.input.checked ? "Ano" : "Ne";
            }
          } else if (typeof wrap._inst.setValue === "function") {
            // PREFERRED — ErpInput/ErpMemo/ErpDropdown unified path.
            // Aktualizuje internal state + DOM + validation visual.
            wrap._inst.setValue(orig == null ? "" : orig);
            // BELT+SUSPENDERS (28.5.2026 pozde, Marti's "DOM stale BelgieA"):
            // Po setValue() vynucenej DOM update PRO PRIPAD ze nektery
            // event handler (focus/blur/restore-from-cache) prepise zpet.
            // Discriminace input.type !== "checkbox" (ne "checked" in input —
            // HTMLInputElement ma checked nativne, vsechny by hit jinak).
            const _safeOrig = orig == null ? "" : String(orig);
            if (wrap._inst.input && wrap._inst.input.type !== "checkbox") {
              wrap._inst.input.value = _safeOrig;
            } else if (wrap._inst.textarea) {
              wrap._inst.textarea.value = _safeOrig;
            }
          } else if (wrap._inst.input) {
            // Last-resort fallback pro raw <input> (non-UI-Kit widget)
            wrap._inst.input.value = orig == null ? "" : String(orig);
          }
          // DIAG po revert: DOM.value PO
          const _diagDomAfter = wrap._inst.input
            ? wrap._inst.input.value
            : (wrap._inst.textarea ? wrap._inst.textarea.value : "?");
          console.log(
            "[revert]", fk,
            "| DOM.value PO=", JSON.stringify(_diagDomAfter),
            _diagDomAfter === (orig == null ? "" : String(orig)) ? "✓ MATCH" : "✗ MISMATCH"
          );
          // Reset visual dirty marker (amber border-left + background) —
          // per widget type (input vs textarea vs trigger). setValue()
          // typically resets validation visual ale dirty amber marker
          // (z onChange handler v _field/_memo/_dropdown) zustava bez explicit clear.
          try {
            // Discriminace: input.type !== "checkbox" (ne "checked" in input)
            const visEl = (wrap._inst.input && wrap._inst.input.type !== "checkbox")
              ? wrap._inst.input
              : (wrap._inst.textarea || wrap._inst.trigger || null);
            if (visEl && visEl.style) {
              visEl.style.borderLeft = "";
              visEl.style.background = "";
            }
          } catch (_eVis) {}
        } catch (e) {
          console.warn("[DesignFwForm] revert field failed:", fk, e);
        }
      });
      console.groupEnd();
      // Clear dirty set + update UI
      this._dirty.clear();
      _markFormDirty(this, false);
      if (this._shell && this._shell.title) {
        const baseTitle = this._spec && this._spec.core
          ? (this._spec.core.label || this._spec.core.code || "Editace")
          : "Editace";
        this._shell.title.textContent = baseTitle;
        this._shell.title.style.color = "";
      }
      this._updateDirtyDiscardBtn();
      if (this._saveBtn) this._saveBtn.style.display = "none";
      _showToast("Změny zrušeny", "info");
    }

    // Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"): popup pro
    // core description (user + system). Volane z header 📘 button
    // (onShowDescriptions handler v _buildModalShell). PATCH backend
    // pres /design/fw-core/update/{id} -> toast + update local spec.
    _openDescriptionsPopup() {
      if (!this._spec || !this._spec.core) {
        _showToast("Spec není načtený, nelze otevřít popis", "error");
        return;
      }
      const core = this._spec.core;
      const self = this;
      _buildDescriptionsPopup({
        entityKind: "core",
        entityId: core.id,
        entityLabel: core.label || core.code || "(bez labelu)",
        descUser: core.description_user,
        descSystem: core.description_system,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          // Update local spec consistency (no full reload nutny)
          self._spec.core.description_user = payload.description_user;
          self._spec.core.description_system = payload.description_system;
        },
      });
    }

    async _beforeCloseHandler() {
      if (!this._dirty || this._dirty.size === 0) return "close";
      const count = this._dirty.size;
      const phrase = count > 1
        ? (count < 5 ? "provedené změny" : "provedených změn")
        : "provedenou změnu";
      const decision = await _confirmDarkDialog({
        title: "Neuložené změny",
        message: "Mám uložit tebou " + phrase + "? (" + count + ")",
      });
      if (decision === true) {
        // Phase 38.4 Krok 5.P-1++++++ (17.5.2026 vecer, Marti's "Ano se
        // chova jako Ne"): replace TODO from 13.5. rano s actual save
        // call. _handleSaveAndClose vyžaduje btnEl ref pro visual
        // feedback (btn.innerHTML manipulation) — vytvori fake btn
        // pro dirty close flow (no visible UI changes, just lifecycle).
        try {
          const fakeBtn = document.createElement("button");
          fakeBtn.innerHTML = "✓ OK";
          await this._handleSaveAndClose(fakeBtn);
        } catch (e) {
          console.error("_beforeCloseHandler save failed:", e);
          // Pokud save failne, NE-close — necháme dialog open, user může retry.
          return "cancel";
        }
        return "save";
      }
      if (decision === false) return "close";
      return "cancel"; // null (Esc / click outside) → keep modal open
    }

    async open() {
      // Phase 38.4 Krok 5.X+1 Fix I++ (27.5.2026, Marti's "IDENTICKY STAV
      // I PO DEPLOY"): re-open guard at SOURCE (DesignFwForm.open). Fix I
      // v erp_grid_actions.js _openFwEditForm pokrylo registry callsite
      // ale NEpokrývalo inline JS callsite v router.py openFwFormForRow
      // (line 14368, dvojklik grid row dispatch). Drz guard pres DOM
      // marker query — kdykoliv otevreny existing modal, no-op re-open
      // bez ohledu na callsite path.
      try {
        // Smart re-open guard (30.5.2026, Marti's volba B = modal stack):
        // - existing s STEJNYM coreId → block (true re-open)
        // - existing s JINYM coreId → allow (stacked modal, Centrala 1 pattern)
        var _existing = document.querySelector('[data-design-fw-form-root="1"]');
        if (_existing) {
          var _existingCoreId = _existing.dataset.designFwFormCoreId;
          var _newCoreId = String(this.opts.coreId);
          if (_existingCoreId === _newCoreId) {
            console.warn(
              "[DesignFwForm] re-open ignored — instance with SAME coreId already open. " +
              "Close existing modal (X / Esc / OK) first. " +
              "(opts.coreId=" + this.opts.coreId +
              ", opts.coreCode=" + this.opts.coreCode +
              ", opts.rowId=" + this.opts.rowId + ")"
            );
            return;
          } else {
            console.info(
              "[DesignFwForm] stacked modal — existing coreId=" + _existingCoreId +
              " vs new coreId=" + _newCoreId + " — allow (Marti's volba B)"
            );
            // Fall through to open
          }
        }
      } catch (e) { /* fail-safe — querySelector pad → continue (puvodni behavior) */ }

      // Phase 38.4 Krok 14g Etapa F Step B: dual {coreId|coreCode, rowId} support.
      // Pokud jen coreId, fetch /fw-form/by-id/{coreId}/{rowId} (Step A endpoint)
      // vrátí spec včetně core.code → store this.opts.coreCode pro subsequent
      // URL builds (children/save/refresh — Step C migrate na coreId paths).
      // Krok 14g-H+4 (25.5.2026 Marti's Q1=A "naprosté minimum"): CREATE mode
      // rowId == null (z erp_grid_actions.js _openFwEditForm action 'create').
      // Backend /fw-form/by-id/{core_id}/{row_id} s row_id=0 vrací spec
      // (core + form + fields) bez data row (data_row_raw=None → data=None).
      // _spec.data defaults to {} v _render() — empty form rendered.
      // _handleSaveAndClose dispatchne POST /design/{core_id} misto PATCH.
      const isCreateMode = (this.opts.rowId == null);
      const rowId = isCreateMode ? 0 : this.opts.rowId;
      if (!this.opts.coreCode && this.opts.coreId) {
        // coreId-only call: resolve via by-id endpoint
        // (Step A backend, /fw-form/by-id/{core_id}/{row_id})
        try {
          const lookup = await fetch(
            "/api/v1/erp/fw-form/by-id/" +
            encodeURIComponent(this.opts.coreId) + "/" +
            encodeURIComponent(rowId)
          ).then(r => r.json());
          // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
          // tolerate drafted core (code=NULL after Krok 5.C DDL "nic nas
          // nesmi omezovat"). Backend vrati lookup.empty_container=true
          // pro drafted — accept + cache spec, render placeholder.
          if (lookup && lookup.ok && lookup.core) {
            this.opts.coreCode = lookup.core.code || null;
            this._spec = lookup; // cache — skip second fetch ve vsech pripadech
          } else {
            console.error("DesignFwForm: by-id lookup failed for coreId=" + this.opts.coreId, lookup);
            return;
          }
        } catch (e) {
          console.error("DesignFwForm: by-id lookup network error:", e);
          return;
        }
      }
      const coreCode = this.opts.coreCode;
      // Phase 38.4 Krok 14g Etapa F Krok 5.C: coreCode CAN be null pro drafted
      // core (empty_container). Pokud chybi coreCode AND chybi cached _spec,
      // fail (neni co renderovat). Jinak pokracujeme — _render handle
      // empty_container placeholder branch.
      if (!coreCode && !this._spec) {
        console.error("DesignFwForm: ani coreCode ani _spec (provide coreId or coreCode)");
        return;
      }

      // Build shell s loading placeholder
      this._shell = _buildModalShell({
        title: "Načítám…",
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        onClose: () => {
          _markFormDirty(this, false);
          // Phase 38.4 Krok 14g-C: cleanup schema tree panel po modal close
          try {
            const panel = document.body.querySelector(".erp-schema-tree-panel");
            if (panel) document.body.removeChild(panel);
          } catch (e) {}
          // Phase 38.4 Krok 14g-D: cleanup undo state + keyboard listener
          try {
            if (this._undoKeyHandler) {
              document.removeEventListener("keydown", this._undoKeyHandler, true);
              this._undoKeyHandler = null;
            }
            this._undoStack = [];
          } catch (e) {}
        },
        // Krok 14b+21 (14.5.2026 rano): 📘 popup pro core description
        // (user + system). PATCH /design/fw-core/update/{id} po save.
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      // Krok 5-B Fix #7 (29.5.2026 pozde, Marti's "udelej nahore nulovy
      // space mezi hlavickou a tou linkou prvniho panelu, tak aby ta
      // linka prvniho panelu splynula s linkou hlavicky"):
      // Drop modal body padding-top → prvni panel sedi tesne pod modal
      // header's border-bottom line. Plus prvni top panel v _buildAlignLayout
      // ma drop border-top + margin-top (header line se stane "tou" linkou).
      try {
        if (this._shell && this._shell.body) {
          this._shell.body.style.paddingTop = "0";
        }
      } catch (e) {}

      // Krok H+13 (27.5.2026 ráno): marker attribute pro helpers.js
      // _installFieldLabelRightClick global handler — skip uvnitř
      // DesignFwForm shell (vlastní per-label handler v _wrapFieldForDesign
      // otevírá unified modal s defaultTab="user").
      try {
        if (this._shell && this._shell.overlay) {
          this._shell.overlay.dataset.designFwFormRoot = "1";
          // Smart re-open guard (30.5.2026, Marti's volba B = modal stack):
          // ulož coreId do marker. Guard pak rozliší stejný vs jiný core.
          this._shell.overlay.dataset.designFwFormCoreId = String(this.opts.coreId);
        }
      } catch (e) {}

      // Phase 38.4 Krok 14b+7 (13.5.2026 ~20:00, Marti's "PROD/DESIGN
      // trigger i na tom formu"): attach toggle button v header. Visible
      // jen pokud global _erpDesignMode = true. Default form mode =
      // PRODUCTION (safe — uzivatel musi explicit prepnout do DESIGN).
      this._attachFormDesignToggle();

      // Phase 38.4 Krok 14b+5 polish fix #5 (13.5.2026 ~14:30, po
      // Marti's DevTools diagnostic):
      //
      // ROOT CAUSE NALEZEN: DevTools ukázal `body.display: "block"`,
      // `body.flexDirection: "row"`. DesignFwForm.open() NIKDY nezavolal
      // setup body = flex column (to byl jen v DesignSoudecekCoreForm).
      // Bez body flex column, root flex:1 ne propagated, grid 1fr main
      // panel zustal natural height.
      //
      // Plus Marti has manually resized dialog (drag corner) -> inline
      // height: 394px. min-height: 500px nas chrání proti tomu být moc
      // malé, ale dialog stále content-sized pokud user drag-shrinks.
      if (this._shell && this._shell.dialog) {
        this._shell.dialog.style.minHeight = "500px";
        // POZN: 70vh height removed — Marti's resize via drag corner
        // override anyway. min-height 500px je dostatek pojistka.
      }
      // CRITICAL FIX — body MUSÍ být flex column pro root grid alClient:
      if (this._shell && this._shell.body) {
        this._shell.body.style.display = "flex";
        this._shell.body.style.flexDirection = "column";
        // Marti's polish (13.5.2026 ~15:00, iterace ~15:15):
        // - Horizontal: 20px → 12px (40% reduce dle Marti's request)
        // - Vertical: 16px → 8px (na polovinu)
        // Compact ale stale visible breathing room od edges modalu.
        this._shell.body.style.padding = "8px 12px";

        // Phase 38.4 Krok H+8.1 (26.5.2026, Marti's "stejnym zpusobem
        // jako ikonky pri hover — klik = persistent"):
        // Document-level orchestrace na shell.body. Hover (mouseover)
        // dispatches 'hover-in', mouseleave shell.body dispatches
        // 'hover-out'. Click dispatches 'select' (persistent v palete).
        // Pres closest('[data-comp-def-id]') najdeme nejvnitrnejsi
        // komponentu — pattern handluje nested fields v panelech (hover
        // transit field→panel→field chodi spravne).
        const _orchBody = this._shell.body;
        const _dispatchOrch = (action, compDefId) => {
          try {
            document.body.dispatchEvent(new CustomEvent("erp:design-component-orchestrate", {
              detail: { action: action, compDefId: compDefId },
              bubbles: false,
            }));
          } catch (e) { /* defensive */ }
        };
        this._lastHoverCompDefId = null;
        const _onOrchMouseover = (ev) => {
          // Skip pokud over interactive child — necht native UX
          const tag = ev.target && ev.target.tagName;
          if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" ||
              tag === "SELECT" || tag === "OPTION") {
            return;
          }
          const comp = ev.target.closest && ev.target.closest("[data-comp-def-id]");
          const newId = comp ? comp.dataset.compDefId : null;
          if (newId === this._lastHoverCompDefId) return;  // dedup
          if (this._lastHoverCompDefId != null) {
            _dispatchOrch("hover-out", this._lastHoverCompDefId);
          }
          this._lastHoverCompDefId = newId;
          if (newId != null) _dispatchOrch("hover-in", newId);
        };
        const _onOrchMouseleave = () => {
          if (this._lastHoverCompDefId != null) {
            _dispatchOrch("hover-out", this._lastHoverCompDefId);
            this._lastHoverCompDefId = null;
          }
        };
        const _onOrchClick = (ev) => {
          const tag = ev.target && ev.target.tagName;
          if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" ||
              tag === "SELECT" || tag === "OPTION" || tag === "LABEL") {
            return;  // necht native action chodi (delete/edit/dropdown)
          }
          const comp = ev.target.closest && ev.target.closest("[data-comp-def-id]");
          if (!comp) return;
          const compDefId = comp.dataset.compDefId;
          if (compDefId == null) return;
          _dispatchOrch("select", compDefId);
        };
        _orchBody.addEventListener("mouseover", _onOrchMouseover);
        _orchBody.addEventListener("mouseleave", _onOrchMouseleave);
        _orchBody.addEventListener("click", _onOrchClick);
        // Cleanup pri shell close (memory leak prevent)
        try {
          const _origClose = this._shell.close;
          this._shell.close = () => {
            try {
              _orchBody.removeEventListener("mouseover", _onOrchMouseover);
              _orchBody.removeEventListener("mouseleave", _onOrchMouseleave);
              _orchBody.removeEventListener("click", _onOrchClick);
            } catch (e) {}
            try { _origClose.call(this._shell); } catch (e) {}
          };
        } catch (e) {}
      }

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      // Phase 38.4 Krok 14g Etapa F Krok 5.C: fallback label pro drafted
      // core (coreCode=null).
      const _loadLabel = coreCode || ("id=" + this.opts.coreId);
      loading.textContent = isCreateMode
        ? ("Připravuji nový záznam · " + _loadLabel + "…")
        : ("Načítám " + _loadLabel + " #" + rowId + "…");
      this._shell.body.appendChild(loading);

      try {
        // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026 odpoledne):
        // Pokud _spec uz cached z by-id lookup (drafted core nebo bonus
        // cache z fully-formed core), skip second fetch — by-id response
        // ma identical shape jako /fw-form/{code}/{rowId} po Krok 5.A.
        // Pro fully-formed core mozeme re-fetch pres code (kontrola
        // konzistence), ale primarni dispatch path je teted by-id.
        if (!this._spec) {
          const resp = await fetch(
            "/api/v1/erp/fw-form/" + encodeURIComponent(coreCode) + "/" + encodeURIComponent(rowId)
          );
          if (!resp.ok) {
            const errBody = await resp.json().catch(() => ({}));
            throw new Error(
              "HTTP " + resp.status + ": " + (errBody.error || resp.statusText)
            );
          }
          this._spec = await resp.json();
        }
        if (!this._spec || !this._spec.ok) {
          throw new Error(
            "Backend error: " + (this._spec && this._spec.error || "unknown")
          );
        }
        // Krok 14b+11 (13.5.2026 ~23:00, Marti's "ukladat vychozi velikost
        // formu"): apply layout.default_width / default_height z form root
        // comp_def. Spec.form.layout je JSONB, persisted pres PATCH endpoint.
        // Apply pred _render() aby grid layout (auto-fit) zacal s novou
        // sirkou.
        this._applyDefaultSize();
        this._render();
        // Phase 38.4 Krok 14c+2 part B (14.5.2026 odpoledne): attach
        // drop target po render. Body je teted drop zone pro gallery
        // cards z FieldPickerModal Preview tabu. Drop kdekoli na form
        // → POST /design/comp-def s computed sort_order. MVP: region='main'
        // vždy, sort_order = max+10 (= konec main panelu). Future polish
        // (Krok 14c+3): compute region z drop coords (header/main/footer
        // dle Y pozice).
        this._attachDropTargetForGalleryDrag();
      } catch (e) {
        this._showError("Načítání selhalo: " + e.message);
      }
    }

    // Phase 38.4 Krok 14c+2 part B: drop target listener pro gallery
    // drag from FieldPickerModal. HTML5 DnD API — dragover preventDefault
    // (allow drop) + drop handler. Visual: tealové hint border na body
    // během dragover.
    _attachDropTargetForGalleryDrag() {
      const body = this._shell && this._shell.body;
      if (!body) return;
      if (body.dataset.galleryDropAttached === "1") return;  // idempotent
      body.dataset.galleryDropAttached = "1";

      // Gate: drop target aktivní jen v DESIGN mode (Marti's polish doctrine)
      const isDesignOn = () => this._formDesignMode === true;

      // Phase 38.4 Krok 14c+3 (14.5.2026 odpoledne, Marti's "drag-and-drop
      // na to spravne misto"): detekce target region z Y coord. Panel je
      // tagged data-region-slot (z _render() při buildování panelu).
      // Dragover → highlight target panel teal accent (zelená pro success).
      // Drop → POST s computed region_slot.
      let _lastHighlightedPanel = null;
      const _clearPanelHighlight = () => {
        if (_lastHighlightedPanel) {
          _lastHighlightedPanel.style.outline = "";
          _lastHighlightedPanel.style.outlineOffset = "";
          _lastHighlightedPanel.style.background = "";
          _lastHighlightedPanel = null;
        }
      };
      const _highlightPanel = (panel) => {
        if (_lastHighlightedPanel === panel) return;
        _clearPanelHighlight();
        if (!panel) return;
        panel.style.outline = "2px dashed #5dbf5d";
        panel.style.outlineOffset = "-2px";
        panel.style.background = "rgba(93, 191, 93, 0.05)";
        panel.style.transition = "background 0.1s, outline 0.1s";
        _lastHighlightedPanel = panel;
      };
      // Z Y coord najdi target panel + region_slot (legacy template panels)
      const _findPanelAtY = (clientY) => {
        const panels = body.querySelectorAll("[data-region-slot]");
        for (const p of panels) {
          const rect = p.getBoundingClientRect();
          if (clientY >= rect.top && clientY <= rect.bottom) {
            return p;
          }
        }
        return null;
      };

      // Phase 38.4 Krok 14f-J (14.5.2026 vecer, Marti's "drop se neuskutecni
      // na panel #22"): novy resolver — najit container (panel/groupbox)
      // pod kurzorem pres elementsFromPoint. Pokud nalezen, drop pujde do
      // toho kontejneru (parent_comp_def_id = container.id). Fallback na
      // template panel (region_slot) pokud zadny container nenalezen.
      //
      // Vraci: { container: HTMLElement | null, templatePanel: HTMLElement | null }
      const _findDropTarget = (clientX, clientY) => {
        let container = null;
        let templatePanel = null;
        try {
          const els = document.elementsFromPoint(clientX, clientY);
          for (const el of els) {
            if (!el || !el.dataset) continue;
            // Container match (panel/groupbox) — most specific
            if (!container && el.dataset.compDefId && el.dataset.compTypeCode &&
                (el.dataset.compTypeCode === "panel" || el.dataset.compTypeCode === "groupbox")) {
              container = el;
            }
            // Template panel match (legacy region_slot wrapper) — fallback
            if (!templatePanel && el.dataset.regionSlot) {
              templatePanel = el;
            }
            if (container && templatePanel) break;
          }
        } catch (e) {
          console.warn("[DesignFwForm] _findDropTarget failed:", e);
        }
        return { container, templatePanel };
      };

      body.addEventListener("dragover", (ev) => {
        if (!isDesignOn()) return;
        // Allow drop jen pokud je to naše gallery card mime type
        const types = ev.dataTransfer && ev.dataTransfer.types;
        if (!types || !Array.from(types).includes("application/x-erp-comp-type")) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "copy";
        // Phase 38.4 Krok 14f-J: prefer container target (panel/groupbox)
        // pred legacy template panel. Container highlight = primary,
        // template panel = sekundarni fallback.
        const { container, templatePanel } = _findDropTarget(ev.clientX, ev.clientY);
        if (container) {
          _highlightPanel(container);
          body.style.outline = "1px solid rgba(168, 140, 212, 0.3)";  // purple subtle
        } else if (templatePanel) {
          _highlightPanel(templatePanel);
          body.style.outline = "1px solid rgba(58,138,168,0.3)";
        } else {
          _clearPanelHighlight();
          body.style.outline = "2px dashed #3a8aa8";
        }
        body.style.outlineOffset = "-4px";
      });

      body.addEventListener("dragleave", (ev) => {
        // Only clear pokud opravdu opustime body (ne sub-element hover)
        if (ev.target === body) {
          body.style.outline = "";
          body.style.outlineOffset = "";
          _clearPanelHighlight();
        }
      });

      body.addEventListener("drop", async (ev) => {
        if (!isDesignOn()) return;
        const raw = ev.dataTransfer.getData("application/x-erp-comp-type");
        if (!raw) return;
        ev.preventDefault();
        body.style.outline = "";
        body.style.outlineOffset = "";
        // Phase 38.4 Krok 14f-J: detect container OR template panel target
        const { container, templatePanel } = _findDropTarget(ev.clientX, ev.clientY);
        const targetRegion = (templatePanel && templatePanel.dataset.regionSlot) || "main";
        const targetContainerId = container ? parseInt(container.dataset.compDefId, 10) : null;
        const targetContainerCode = container ? container.dataset.compTypeCode : null;
        _clearPanelHighlight();

        let payload;
        try {
          payload = JSON.parse(raw);
        } catch (e) {
          _showToast("Drop payload corrupt — chyba parsování", "error");
          return;
        }
        if (!payload || !payload.id) {
          _showToast("Drop bez comp_type id", "error");
          return;
        }

        // POST /design/comp-def — Phase 38.4 Krok 14f-J:
        // Pokud drop na container (panel/groupbox), parent = container.id.
        // Jinak parent = form root + region_slot z template panel.
        const formRootId = this._spec && this._spec.form && this._spec.form.id;
        if (!formRootId) {
          _showToast("Form root chybi — drop selhal", "error");
          return;
        }
        // Decide parent: container (if found) vs form root (legacy)
        const parentId = targetContainerId || formRootId;
        const targetLabel = targetContainerId
          ? (targetContainerCode + " #" + targetContainerId)
          : ("panel '" + targetRegion + "'");

        // Phase 38.4 Krok 14f-L (14.5.2026 vecer, Marti's "nedodelana
        // parametrizace ke kteremu DB fieldu to patri"): otevri column
        // picker pro non-container, non-label types. Container/label
        // skip — direct create s auto-name.
        const isContainer = payload.is_container === true ||
                            payload.code === "panel" ||
                            payload.code === "groupbox";
        const isLabel = payload.code === "label" || payload.code === "label_readonly";
        // Krok 5.Z (Marti 30.5.): grid_modern nemapuje DB sloupec formu (ma
        // vlastni data_source). Direct create bez column pickeru — jinak by
        // padal "Form nema data_entity_type — nelze ziskat columns" na formech
        // bez entity. data_source + filter nastavi Marti pres ⚙ "Nastaveni gridu".
        const isGrid = payload.code === "grid_modern";

        let nameToUse, captionToUse;
        if (isContainer || isLabel || isGrid) {
          // No DB binding needed — direct create
          nameToUse = payload.code + "_" + Date.now().toString(36);
          captionToUse = payload.label;
        } else {
          // Open column picker dialog
          const choice = await this._pickColumnForNewField(payload, parentId);
          if (!choice) {
            _showToast("Pridani zrušeno", "info", 1500);
            return;
          }
          nameToUse = choice.name;
          captionToUse = choice.caption;
        }

        try {
          // Phase 38.4 Krok 14f-C (14.5.2026 vecer): pass-through layout
          // pro container types (panel/groupbox). Drag payload obsahuje
          // default layout (panel → {"align":"client"}, groupbox →
          // {"border_mode":"top","label":null}).
          const postBody = {
            parent_comp_def_id: parentId,
            name: nameToUse,
            caption: captionToUse,
            type_id: payload.id,
            region_slot: targetRegion,
          };
          if (payload.layout && typeof payload.layout === "object") {
            postBody.layout = payload.layout;
          }
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(postBody),
          });
          const d = await r.json();
          if (!r.ok || !d.ok) {
            throw new Error(d.error || "HTTP " + r.status);
          }
          _showToast(
            "Přidáno: " + payload.label + " → " + targetLabel,
            "success",
            2500
          );
          // Refresh spec + re-render
          const refreshResp = await fetch(
            "/api/v1/erp/fw-form/" +
            encodeURIComponent(this.opts.coreCode) + "/" +
            encodeURIComponent(this.opts.rowId)
          );
          if (refreshResp.ok) {
            this._spec = await refreshResp.json();
            this._render();
            this._attachDropTargetForGalleryDrag();  // re-attach po _render
          }
        } catch (e) {
          console.error("[DesignFwForm] gallery drop POST failed:", e);
          _showToast("Drop selhal: " + (e.message || e), "error", 3500);
        }
      });
    }

    // ──────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14d-D (14.5.2026 vecer, Marti-AI's Q3 polymorphic):
    // Children sub-grid rendering + CRUD. MVP s native prompt() pro
    // add/edit inputs, polish v Krok 14d-E (inline edit dialog).
    // ──────────────────────────────────────────────────────────────────

    _renderChildSection(childKey, childInfo) {
      // Section wrap (analog section v form fields)
      const sec = _sectionBuild(
        childInfo.label || childKey,
        "child:" + childKey
      );

      // Phase 38.4 Krok 5.X+1 Fix F (27.5.2026, Marti's Volba B "pinned-CSS"):
      // Nested_grid je HYBRID — backend kind='container' (children data),
      // UI semantika field-like. Pinned toggle (layout.pinned=true) → CSS
      // shift v ramci panelu (max-width 60%, margin-right:auto = left
      // align). Doctrine z 27.5. odpoledne: "nested grid se ve formu
      // presune doleva" jako field-pinned, ne jako container-outdent.
      // Layout JSONB pass-through z backend fw_form_load_by_id (Fix E).
      const _ngLayout = (childInfo && childInfo.layout) || {};
      if (_ngLayout.pinned === true) {
        sec.wrap.style.maxWidth = "60%";
        sec.wrap.style.marginRight = "auto";
        sec.wrap.style.marginLeft = "0";
        sec.wrap.dataset.pinned = "1";
      }

      // Phase 38.4 Krok 14f-O (14.5.2026 vecer, Marti's "v production mode
      // jsou gridy dragabled... to ma byt jen v design mode"):
      // Drag handle + grip + contextmenu jsou DESIGN-only features.
      // V PROD mode child section je read-only display.
      // Phase 38.4 Krok 5.X+1 Fix J (27.5.2026, Marti's "2x render me rusi"):
      // Marker pres sekce univerzalne (oba modes) → enables targeted
      // _rerenderChildSection without full _reloadSpec() ping-pong.
      // Marker uvnitr design-only branch byl gated (Phase 38.4 Krok 14f-O),
      // ale targeted update potrebuje marker vzdy.
      sec.wrap.dataset.childSectionKey = childKey;

      const designMode = this._formDesignMode === true;
      if (!designMode) {
        // PROD mode: short-circuit — pouze static render bez drag/context.
        // Pokracuj k table rendering (data display) niz.
      } else {
        // Phase 38.4 Krok H+7 (26.5.2026, Marti's "smaz tecky pro drag"):
        // Drag handle ⋮⋮ + draggable + dragstart/dragover/drop handlers
        // DROPPED. Child section reorder se nyni dela pres palette ↑/↓
        // (linearized tree navigation). Marti's "form se bude chovat
        // jako v production". Zustava jen right-click → settings popup
        // (Krok 14f-I) jako DESIGN-only action.
        sec.wrap.dataset.childSectionKey = childKey;

        // Phase 38.4 Krok 14f-I (14.5.2026 vecer, Marti's "dodelat
        // nastaveni gridu, minimalne tlacitko odebrat"): right-click na
        // child section → settings popup.
        sec.wrap.addEventListener("contextmenu", (ev) => {
          const tag = ev.target && ev.target.tagName;
          if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
            return;
          }
          ev.preventDefault();
          ev.stopPropagation();
          this._openChildSectionSettings(childKey, childInfo);
        });
        // Krok H+7 (26.5.2026): child section drop handler DROPPED
        // (drag affordance pryc — reorder pres palette ↑/↓).
      }  // /designMode

      // Hidden cols z select_columns (interní metadata)
      const HIDDEN_COLS = new Set([
        "id", "created_at", "updated_at", "created_by_id", "created_by_text",
        "updated_by_id", "updated_by_text",
      ]);
      const rows = childInfo.rows || [];
      // Visible cols z first row keys (or empty fallback)
      const sampleRow = rows[0] || {};
      const visibleCols = Object.keys(sampleRow).filter(
        c => !HIDDEN_COLS.has(c)
      );
      // Fallback pokud žádné rows — default columns z childInfo
      const cols = visibleCols.length > 0
        ? visibleCols
        : ["contact_value", "label", "is_primary", "is_verified", "status"];

      // Table
      const table = document.createElement("table");
      table.className = "erp-nested-grid";
      table.style.cssText =
        "width:100%;border-collapse:collapse;font-size:12px;margin-top:4px;";

      // Header row
      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");
      for (const col of cols) {
        const th = document.createElement("th");
        th.textContent = col;
        th.style.cssText =
          "padding:6px 8px;background:#141a20;border:1px solid #2a3340;" +
          "text-align:left;color:#8a96a4;font-size:11px;font-weight:600;";
        headerRow.appendChild(th);
      }
      // Actions column header — Phase 38.4 Krok 14d-D polish (14.5.2026
      // večer Marti's "tlacitko + v ramecku zelene v hlavicce gridu nad ✕"):
      // Místo prázdné header buňky → zelený + button (cleaner UX,
      // konzistentní pozice nad action column ✕ buttons per row).
      const thActions = document.createElement("th");
      thActions.style.cssText =
        "padding:4px;background:#141a20;border:1px solid #2a3340;" +
        "width:36px;text-align:center;";
      const headerAddBtn = document.createElement("button");
      headerAddBtn.type = "button";
      headerAddBtn.textContent = "+";
      headerAddBtn.title = "Přidat nový " + (childInfo.label || childKey);
      headerAddBtn.style.cssText =
        "background:transparent;border:1px solid #5dbf5d;color:#5dbf5d;" +
        "padding:0;width:22px;height:22px;border-radius:3px;cursor:pointer;" +
        "font-size:16px;font-weight:600;line-height:1;transition:background 0.15s;";
      headerAddBtn.addEventListener("mouseenter", () => {
        headerAddBtn.style.background = "rgba(93,191,93,0.15)";
      });
      headerAddBtn.addEventListener("mouseleave", () => {
        headerAddBtn.style.background = "transparent";
      });
      headerAddBtn.addEventListener("click", () => {
        this._addChildRow(childKey, childInfo);
      });
      thActions.appendChild(headerAddBtn);
      headerRow.appendChild(thActions);
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // Body rows
      const tbody = document.createElement("tbody");
      if (rows.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = cols.length + 1;
        td.style.cssText =
          "padding:14px;text-align:center;color:#5d6975;font-style:italic;" +
          "border:1px solid #2a3340;background:#0f141a;";
        td.textContent = "Žádné záznamy v " + (childInfo.label || childKey);
        tr.appendChild(td);
        tbody.appendChild(tr);
      } else {
        for (const row of rows) {
          tbody.appendChild(this._renderChildRow(childKey, childInfo, row, cols));
        }
      }
      table.appendChild(tbody);
      sec.grid.appendChild(table);

      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "tlacitko
      // + v ramecku v zelenem v hlavicce gridu nad tlacitka odebrat"):
      // Velký "+ Přidat" rectangle pod tabulkou dropped — nahrazený malým
      // zeleným + buttonem v header (above ✕ column). Cleaner UX, méně
      // visuálního noise.

      return sec.wrap;
    }

    _renderChildRow(childKey, childInfo, row, cols) {
      const tr = document.createElement("tr");
      tr.dataset.childRowId = String(row.id);

      for (const col of cols) {
        const td = document.createElement("td");
        td.style.cssText =
          "padding:5px 8px;border:1px solid #2a3340;color:#cfd6df;cursor:pointer;";
        td.title = "Dvojklik pro editaci";
        const v = row[col];
        if (typeof v === "boolean") {
          td.textContent = v ? "✓" : "";
          td.style.textAlign = "center";
          td.style.color = v ? "#5dbf5d" : "#5d6975";
        } else if (v == null) {
          td.textContent = "—";
          td.style.color = "#5d6975";
        } else {
          td.textContent = String(v);
        }
        // Dvojklik pro inline edit (MVP — native prompt)
        td.addEventListener("dblclick", (ev) => {
          ev.stopPropagation();
          this._editChildCell(childKey, childInfo, row, col, td);
        });
        tr.appendChild(td);
      }

      // Action — ✕ archive
      const tdAct = document.createElement("td");
      tdAct.style.cssText =
        "padding:5px 4px;border:1px solid #2a3340;text-align:center;background:#0f141a;";
      const archBtn = document.createElement("button");
      archBtn.type = "button";
      archBtn.textContent = "✕";
      archBtn.title = "Archivovat řádek (status='archived', soft delete)";
      archBtn.style.cssText =
        "background:transparent;border:1px solid #5a2828;color:#e57373;" +
        "padding:0;width:22px;height:22px;border-radius:3px;cursor:pointer;" +
        "font-size:11px;line-height:1;";
      archBtn.addEventListener("mouseenter", () => {
        archBtn.style.background = "#3a1f1f";
      });
      archBtn.addEventListener("mouseleave", () => {
        archBtn.style.background = "transparent";
      });
      archBtn.addEventListener("click", () => {
        this._archiveChildRow(childKey, childInfo, row);
      });
      tdAct.appendChild(archBtn);
      tr.appendChild(tdAct);

      return tr;
    }

    async _addChildRow(childKey, childInfo) {
      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "Popup
      // dialog zmen na dark theme"): _promptDarkDialog místo window.prompt.
      const label = childInfo.label || childKey;
      const value = await _promptDarkDialog({
        title: "Přidat " + label,
        message: "Zadej hodnotu (např. email adresa nebo telefonní číslo):",
        placeholder: "...",
        okLabel: "Přidat",
        cancelLabel: "Zrušit",
      });
      if (!value || !value.trim()) return;

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey);
        const r = await fetch(url, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contact_value: value.trim(),
            label: childInfo.default_label || null,
            is_primary: false,
            is_verified: false,
          }),
        });
        const d = await r.json();
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }
        _showToast("Přidáno: " + value, "success", 2500);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _addChildRow failed:", e);
        _showToast("Přidání selhalo: " + (e.message || e), "error", 3500);
      }
    }

    async _editChildCell(childKey, childInfo, row, col, tdEl) {
      // Phase 38.4 Krok 14d-D polish (14.5.2026 vecer, Marti's "Popup
      // dialog zmen na dark theme"): _promptDarkDialog místo window.prompt.
      // Boolean cols: toggle (no dialog — instant flip)
      const currentVal = row[col];
      let newVal;
      if (typeof currentVal === "boolean") {
        newVal = !currentVal;
      } else {
        const input = await _promptDarkDialog({
          title: "Editovat " + col,
          message: "Aktuální hodnota: " + (currentVal == null ? "—" : currentVal),
          defaultValue: currentVal == null ? "" : String(currentVal),
          okLabel: "Uložit",
          cancelLabel: "Zrušit",
        });
        if (input == null) return;  // Cancel (Esc / × / Storno)
        newVal = input.trim() === "" ? null : input.trim();
        if (newVal === (currentVal == null ? null : String(currentVal))) return;  // No change
      }

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey) +
          "/" + encodeURIComponent(row.id);
        const r = await fetch(url, {
          method: "PATCH",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            [col]: newVal,
            expected_updated_at: row.updated_at,
          }),
        });
        const d = await r.json();
        if (r.status === 409) {
          // Concurrent edit conflict (Marti-AI's Q4 atomic guard)
          _showToast(
            "Konflikt — " + col + " mezitím změnil " +
            (d.by_user && d.by_user.short_name || "někdo") + ". Načti znovu.",
            "error", 4000
          );
          await this._reloadSpec();
          return;
        }
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }

        // Phase 38.4 Krok 5.X+1 Fix J (27.5.2026, Marti's "2x render me rusi"):
        // Targeted update misto full _reloadSpec ping-pong.
        //
        // Local row mutate na top + handle Fix H atomic primary swap:
        // pokud is_primary=TRUE byl nastaven, backend (Fix H atomic
        // pre-clear) zmenil OSTATNI rows v same scope na FALSE. Frontend
        // misto re-fetch celeho spec mutate local rows (childInfo.rows
        // shared reference s this._spec.children[childKey].rows).
        //
        // Server response d.row = updated row (truth source pro updated_at +
        // ostatni cascaded changes). Use to refresh local copy.
        if (d.row) {
          Object.assign(row, d.row);
        } else {
          row[col] = newVal;
        }
        if (col === "is_primary" && newVal === true &&
            Array.isArray(childInfo.rows)) {
          // Backend Fix H atomic pre-clear → ostatni rows v scope musi byt
          // false. Local mutate aby UI matchnul DB state bez re-fetch.
          // Note: updated_at ostatnich rows je teted stale (server tick +1ms),
          // pri pristim PATCH narazime na optimistic lock 409 → reload
          // (graceful degradation).
          for (const otherRow of childInfo.rows) {
            if (otherRow.id !== row.id && otherRow.is_primary) {
              otherRow.is_primary = false;
            }
          }
        }

        // Targeted re-render jen this child section. Pokud marker missing
        // (defensive), fallback na full _reloadSpec.
        const rerendered = this._rerenderChildSection(childKey, childInfo);
        if (!rerendered) {
          await this._reloadSpec();
        }
        _showToast("Uloženo: " + col, "success", 2000);
      } catch (e) {
        console.error("[DesignFwForm] _editChildCell failed:", e);
        _showToast("Edit selhal: " + (e.message || e), "error", 3500);
      }
    }

    async _archiveChildRow(childKey, childInfo, row) {
      const display = row.contact_value || ("id=" + row.id);
      const confirmed = await _confirmDarkDialog({
        title: "Archivovat řádek?",
        message:
          "Archivovat '" + display + "' z " + (childInfo.label || childKey) + "?\n\n" +
          "(soft delete — status='archived', forensic audit zachovaný)",
      });
      if (!confirmed) return;

      try {
        const url = "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId) +
          "/children/" + encodeURIComponent(childKey) +
          "/" + encodeURIComponent(row.id) + "/archive";
        const r = await fetch(url, {
          method: "PATCH",
          credentials: "include",
        });
        const d = await r.json();
        if (!r.ok || !d.ok) {
          throw new Error(d.error || "HTTP " + r.status);
        }
        _showToast("Archivováno: " + display, "success", 2500);
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _archiveChildRow failed:", e);
        _showToast("Archive selhal: " + (e.message || e), "error", 3500);
      }
    }

    // Phase 38.4 Krok 5.X+1 Fix J (27.5.2026, Marti's "2x render me rusi"):
    // Targeted re-render JEN dotcene child section (TELEFONY / EMAILY
    // nested grid) bez full _reloadSpec ping-pong. Marker
    // data-child-section-key="<childKey>" je nastaven v _renderChildSection
    // (Fix J marker move out of designMode gate).
    //
    // Use case: inline cell edit (is_primary toggle, contact_value rename) →
    // PATCH success → local row mutate → targeted DOM replace bez touching
    // form root / other sections. 1 render misto 2.
    //
    // Pokud marker nenalezen (defensive), fallback na _reloadSpec (puvodni
    // behavior — full re-fetch + _render).
    _rerenderChildSection(childKey, childInfo) {
      const body = this._shell && this._shell.body;
      if (!body) return false;
      const oldSec = body.querySelector(
        `[data-child-section-key="${CSS.escape(childKey)}"]`
      );
      if (!oldSec) {
        console.warn(
          "[DesignFwForm] _rerenderChildSection: section marker not found " +
          "for childKey=" + childKey + " — fallback na full _reloadSpec"
        );
        return false;
      }
      const newSec = this._renderChildSection(childKey, childInfo);
      if (!newSec) {
        console.warn(
          "[DesignFwForm] _rerenderChildSection: _renderChildSection vratila null"
        );
        return false;
      }
      oldSec.replaceWith(newSec);
      return true;
    }

    // Reload spec po CRUD operations (parent + children refresh)
    async _reloadSpec() {
      try {
        const resp = await fetch(
          "/api/v1/erp/fw-form/" +
          encodeURIComponent(this.opts.coreCode) + "/" +
          encodeURIComponent(this.opts.rowId)
        );
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        this._spec = await resp.json();
        if (!this._spec || !this._spec.ok) {
          throw new Error("Backend: " + (this._spec && this._spec.error || "unknown"));
        }
        this._render();
        // Re-attach drop target po _render (gotcha — _render přepisuje body innerHTML)
        this._attachDropTargetForGalleryDrag();
      } catch (e) {
        console.error("[DesignFwForm] _reloadSpec failed:", e);
        _showToast("Reload selhal: " + (e.message || e), "error", 3500);
      }
    }

    _applyDefaultSize() {
      // Krok 14b+11: read this._spec.form.layout.default_width/_height
      // (saved via 💾 Velikost button v DESIGN header). Apply jako inline
      // dialog.style. Pokud nejsou, fallback na default modal velikost
      // (920px width + min-height 500px z _buildModalShell).
      //
      // Krok 14b+12 (13.5.2026 ~23:30, Marti's "min velikost"): apply
      // i min_width / min_height pres dialog.style.minWidth/minHeight.
      // Browser native CSS min-* constraints prevent drag-resize pod min
      // (resize:both nemoze shrink pod min-width).
      if (!this._shell || !this._shell.dialog) return;
      const formLayout = (this._spec.form && this._spec.form.layout) || {};
      const dialog = this._shell.dialog;
      if (formLayout.default_width) {
        dialog.style.width = String(formLayout.default_width);
      }
      if (formLayout.default_height) {
        dialog.style.height = String(formLayout.default_height);
      }
      if (formLayout.min_width) {
        dialog.style.minWidth = String(formLayout.min_width);
      }
      if (formLayout.min_height) {
        dialog.style.minHeight = String(formLayout.min_height);
      }
      // Refresh button visibility — _attachFormDesignToggle se volal
      // PRED fetch spec, gates `this._spec.form.id` byly false. Teď spec
      // live, re-evaluate.
      this._updateFormSaveSizeBtn();
      this._updateFormDetectMinBtn();
    }

    _showError(msg) {
      if (this._shell && this._shell.body) {
        this._shell.body.innerHTML = "";
        const err = document.createElement("div");
        err.style.cssText = "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;border-radius:4px;margin:16px;";
        err.textContent = msg;
        this._shell.body.appendChild(err);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";

      const core = this._spec.core;
      const form = this._spec.form;
      const fields = this._spec.fields || [];
      const data = this._spec.data || {};
      // Phase 38.4 Krok 14b+3 (13.5.2026 rano): template.layout takes precedence
      // over form.layout. template ma vlastni header / main / footer panels +
      // header/footer components (title / entity_badge / status_pill / button).
      // Forms bez template_id → fallback na form.layout (legacy pre-Krok 14b+1).
      const template = this._spec.template || null;

      // Phase 38.4 Krok 5.M-3 (17.5.2026): _updateFormEntityBtn() call dropped
      // (Krok 5.F dead code removed). _updateFormAddFieldBtn() zustal — +Pole
      // button visibility per _formDesignMode.
      try { this._updateFormAddFieldBtn(); } catch (e) {}

      // Phase 38.4 Krok 14g Etapa F Krok 5.A (16.5.2026, Marti's "core =
      // kontejner"): pokud core nema root comp_def (empty_container=true),
      // render placeholder + picker preparation message. Marti's "uniformita
      // vitezi nad specialnimi pripady" + "core je plocha, na ni se rozhodne
      // uzivatelsky co vlozit". Plny picker UI (Krok 5.B/5.C) prijde po
      // konzultaci s Marti-AI.
      if (form === null || this._spec.empty_container === true) {
        if (this._shell.title) {
          const _coreLabel = core.label
            || core.code
            || ("id=" + (core.id || "?"));
          this._shell.title.textContent = "Prázdný core · " + _coreLabel;
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.C (16.5.2026, Marti's "B
        // logicky krok"): origin provenance display + "A Zrusit asociaci
        // s potvrzenim" button. Origin payload from /by-id endpoint
        // (LEFT JOIN na origin_menu_node_id + origin_cmi_id).
        const origin = this._spec.origin || {};
        const ocmi = origin.cmi || null;
        const omn = origin.menu_node || null;

        // Origin banner (jen pokud aspon jeden origin set)
        const empty = document.createElement("div");
        empty.style.cssText =
          "padding:32px 32px;color:#8a96a4;" +
          "display:flex;flex-direction:column;align-items:center;gap:14px;";

        if (omn || ocmi) {
          const originBar = document.createElement("div");
          originBar.style.cssText =
            "background:rgba(139,115,85,0.12);" +
            "border:1px solid rgba(139,115,85,0.3);" +
            "border-radius:4px;padding:10px 14px;" +
            "font-size:12px;color:#d4b88a;width:100%;max-width:640px;" +
            "display:flex;justify-content:space-between;align-items:center;gap:12px;";
          let originHtml = '<div><span style="opacity:0.7;">Pochází z:</span> ';
          if (omn) {
            originHtml += '<span style="color:#a8c5dc;">📁 ' +
              _esc(omn.label || omn.code || ("menu_node#" + omn.id)) +
              '</span>';
          }
          if (omn && ocmi) originHtml += ' <span style="opacity:0.5;">→</span> ';
          if (ocmi) {
            originHtml += '<span style="color:#d4b88a;">📋 ' +
              _esc(ocmi.label || ocmi.code || ("cmi#" + ocmi.id)) +
              '</span>';
          }
          originHtml += '</div>';
          originBar.innerHTML = originHtml;

          // Zrusit asociaci button (jen pokud originCmiId set v opts)
          if (this.opts.originCmiId) {
            const btnUnlink = document.createElement("button");
            btnUnlink.type = "button";
            btnUnlink.textContent = "🚫 Zrušit asociaci";
            btnUnlink.style.cssText =
              "padding:5px 12px;font-size:11px;border-radius:3px;" +
              "background:rgba(212,135,135,0.12);" +
              "border:1px solid rgba(212,135,135,0.4);color:#d48787;" +
              "cursor:pointer;white-space:nowrap;";
            btnUnlink.onmouseenter = function () {
              btnUnlink.style.background = "rgba(212,135,135,0.22)";
            };
            btnUnlink.onmouseleave = function () {
              btnUnlink.style.background = "rgba(212,135,135,0.12)";
            };
            const self = this;
            btnUnlink.onclick = async function () {
              const cmiLabel = (ocmi && (ocmi.label || ocmi.code))
                || ("cmi#" + self.opts.originCmiId);
              const ok = window.confirm(
                "Zrušit asociaci kontejneru s '" + cmiLabel + "'?\n\n" +
                "Po potvrzení se kontextové menu vrátí do drafted stavu " +
                "(core_id = NULL). Při dalším pravém kliku se " +
                "otevře Kontejner picker pro novou volbu."
              );
              if (!ok) return;
              btnUnlink.disabled = true;
              btnUnlink.textContent = "Ruším…";
              try {
                const r = await fetch(
                  "/api/v1/erp/design/context-menu-item/" +
                    encodeURIComponent(self.opts.originCmiId) + "/link-core",
                  {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include",
                    body: JSON.stringify({ core_id: null }),
                  }
                ).then(function (rr) { return rr.json(); });
                if (r && r.ok) {
                  // Close modal — pri pristim kliku zase picker
                  try { self._shell.close(); } catch (e) {}
                } else {
                  btnUnlink.disabled = false;
                  btnUnlink.textContent = "🚫 Zrušit asociaci";
                  alert("Zrušení selhalo: " + ((r && r.error) || "unknown"));
                }
              } catch (e) {
                btnUnlink.disabled = false;
                btnUnlink.textContent = "🚫 Zrušit asociaci";
                alert("Zrušení selhalo (network): " + (e.message || e));
              }
            };
            originBar.appendChild(btnUnlink);
          }

          empty.appendChild(originBar);
        }

        // Big icon + headline + Marti doctrine
        const big = document.createElement("div");
        big.style.cssText =
          "display:flex;flex-direction:column;align-items:center;gap:14px;" +
          "padding:20px 0;";
        big.innerHTML =
          '<div style="font-size:64px;line-height:1;">🎨</div>' +
          '<div style="font-size:18px;color:#d4b88a;font-weight:600;">' +
          'Prázdný core kontejner' +
          '</div>' +
          '<div style="font-size:13px;max-width:480px;line-height:1.6;text-align:center;">' +
          '<code style="color:#8fb8d4;">id=' + (core.id || "?") +
          '</code> ' +
          'zatím nemá žádnou root komponentu. ' +
          'Marti doctrine: <em>„core = plocha, na ní se rozhodne uživatelsky ' +
          'co vložit (form 302, list, dashboard, ...)."</em>' +
          '</div>';
        empty.appendChild(big);

        // ─────────────────────────────────────────────────────────────────
        // Krok 14g-H+5 (26.5.2026, Marti's "Vytvorit edit jadro 2"):
        // Akcni karta v prazdnem containeru — nabidka spustit orchestrator
        // pro auto-generation comp_def hierarchy (form root + main panel +
        // per-column inputs + footer + OK/Storno buttons).
        //
        // Marti's design (26.5. odpoledne):
        //   - PUVODNI orchestrator (vytvorit_edit_jadro) BEZE ZMENY
        //   - NOVY skript v fw.executable_artifact: 'vytvorit_edit_jadro_2'
        //   - Klik Ano → POST /sandbox/execute/vytvorit_edit_jadro_2 s
        //     body {coreId: <thisCoreId>} → po success reload form
        // ─────────────────────────────────────────────────────────────────
        const genCard = document.createElement("div");
        genCard.style.cssText =
          "background:rgba(74,123,168,0.08);" +
          "border:1px solid rgba(74,123,168,0.3);" +
          "border-radius:6px;padding:18px 24px;" +
          "max-width:540px;width:100%;" +
          "display:flex;flex-direction:column;gap:14px;" +
          "margin-top:8px;";

        const genHead = document.createElement("div");
        genHead.style.cssText =
          "font-size:14px;color:#a8c5dc;text-align:center;line-height:1.5;";
        genHead.innerHTML =
          '<div style="font-size:24px;margin-bottom:6px;">🪄</div>' +
          '<div><strong>Chceš abych vygenerovala root komponenty</strong>' +
          ' pro tento edit core?</div>' +
          '<div style="font-size:11px;color:#6a7684;margin-top:6px;font-style:italic;">' +
          'Orchestrator <code style="color:#8fb8d4;">vytvorit_edit_jadro_2</code> ' +
          'vytvoří form root + main panel + per-column inputs + footer.' +
          '</div>';
        genCard.appendChild(genHead);

        const genBtnRow = document.createElement("div");
        genBtnRow.style.cssText =
          "display:flex;justify-content:center;gap:12px;margin-top:4px;";

        const btnYes = document.createElement("button");
        btnYes.type = "button";
        btnYes.textContent = "✓ Ano, vygeneruj";
        btnYes.style.cssText =
          "padding:8px 18px;font-size:13px;font-weight:600;border-radius:4px;" +
          "background:rgba(74,154,74,0.18);" +
          "border:1px solid rgba(74,154,74,0.5);color:#7fc77f;" +
          "cursor:pointer;min-width:140px;";
        btnYes.onmouseenter = function () {
          btnYes.style.background = "rgba(74,154,74,0.28)";
        };
        btnYes.onmouseleave = function () {
          btnYes.style.background = "rgba(74,154,74,0.18)";
        };

        const btnNo = document.createElement("button");
        btnNo.type = "button";
        btnNo.textContent = "Ne";
        btnNo.style.cssText =
          "padding:8px 18px;font-size:13px;border-radius:4px;" +
          "background:rgba(138,150,164,0.12);" +
          "border:1px solid rgba(138,150,164,0.35);color:#8a96a4;" +
          "cursor:pointer;min-width:100px;";
        btnNo.onmouseenter = function () {
          btnNo.style.background = "rgba(138,150,164,0.22)";
        };
        btnNo.onmouseleave = function () {
          btnNo.style.background = "rgba(138,150,164,0.12)";
        };

        const self = this;
        btnNo.onclick = function () {
          // Hide card — zustane jen empty placeholder
          genCard.style.display = "none";
        };

        btnYes.onclick = async function () {
          btnYes.disabled = true;
          btnNo.disabled = true;
          btnYes.textContent = "⏳ Generuji…";
          try {
            const r = await fetch(
              "/api/v1/erp/sandbox/execute/vytvorit_edit_jadro_2",
              {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ coreId: core.id }),
              }
            ).then(function (rr) { return rr.json(); });

            if (r && r.ok) {
              // Success — toast + reload form (re-fetch spec)
              try {
                _showToast(
                  "Root komponenty vygenerovány — načítám…",
                  "success",
                  2500
                );
              } catch (e) {}
              // Reload: zavri + znovu otevri stejny coreId
              try {
                self._shell.close();
              } catch (e) {}
              // Re-open po krátké pauze (modal cleanup race)
              setTimeout(function () {
                try {
                  const fwf2 = new global.DesignFwForm({
                    coreId: core.id,
                    rowId: self.opts.rowId,  // null pro CREATE mode
                    mode: self.opts.mode,
                    onSaveSuccess: self.opts.onSaveSuccess,
                  });
                  if (typeof fwf2.open === "function") fwf2.open();
                } catch (e) {
                  console.error("[H+5] Re-open after generate failed:", e);
                }
              }, 400);
            } else {
              // Error — show toast + restore buttons
              const errMsg = (r && r.error) || "unknown";
              btnYes.disabled = false;
              btnNo.disabled = false;
              btnYes.textContent = "✓ Ano, vygeneruj";
              try {
                _showToast(
                  "Generování selhalo: " + errMsg,
                  "error",
                  4500
                );
              } catch (e) {
                alert("Generování selhalo: " + errMsg);
              }
            }
          } catch (e) {
            btnYes.disabled = false;
            btnNo.disabled = false;
            btnYes.textContent = "✓ Ano, vygeneruj";
            try {
              _showToast(
                "Generování selhalo (network): " + (e.message || e),
                "error",
                4500
              );
            } catch (e2) {
              alert("Generování selhalo: " + (e.message || e));
            }
          }
        };

        genBtnRow.appendChild(btnYes);
        genBtnRow.appendChild(btnNo);
        genCard.appendChild(genBtnRow);
        empty.appendChild(genCard);

        this._shell.body.appendChild(empty);
        return;
      }

      // Title z core.label (preferuj nad form.caption)
      // Krok 14g-H+4 (25.5.2026): CREATE mode prefix "Nový záznam · " (Marti's
      // Q1=A "naprosté minimum at se nezamotame"). isCreateMode detection via
      // this.opts.rowId (null = CREATE, ne via this._spec.data — to je vždy
      // {} v CREATE mode, nelze rozeznat od edit no-data edge case).
      const _isCreate = (this.opts.rowId == null);
      if (this._shell.title) {
        const _baseTitle = core.label || form.caption || core.code || "";
        this._shell.title.textContent = _isCreate
          ? ("Nový záznam · " + _baseTitle)
          : _baseTitle;
      }

      // Root content container — Phase 38.4 Krok 14b+5 polish #4
      // (13.5.2026 ~14:15, Marti's "main panel se na vysku nehybe"):
      // Switch z flex column chain na **CSS Grid 3-row layout**.
      //
      // Důvod: flex chain propagation byla křehká (margin-top:auto +
      // flex:1 + min-height:0 + nested wrappers). Pri jakémkoli broken
      // link na vyšší úrovni main panel zustaval natural-sized.
      //
      // CSS Grid s `grid-template-rows: auto 1fr auto` je DETERMINISTIC:
      //   - row 1: header (auto = natural height)
      //   - row 2: main (1fr = fills remaining space — alClient!)
      //   - row 3: footer (auto = natural)
      //
      // Vzdy funguje bez ohledu na parent dimensions (pokud root sám
      // ma height — z flex:1 v body).
      const root = document.createElement("div");
      root.className = "erp-design-tab-content";
      root.style.cssText =
        "padding:0;" +
        "display:grid;" +
        "grid-template-rows:auto 1fr auto;" +
        "flex:1 1 auto;" +
        "min-height:0;" +
        // Phase 38.4 Krok 5-B Fix #7 polish (29.5.2026 pozde, Marti's
        // "jeste to chce nahoru"): gap:7px → 0. Header row je casto
        // prazdny (0 height) ale grid gap se aplikuje i tak — 7px
        // air gap pred main panelem. Drop gap → main sedi flush pod
        // modal header. Footer dostane vlastni marginTop:7px nize
        // (zachova viditelny gap nad OK/Storno).
        "gap:0;";

      // Extract panels — template.layout (Krok 14b+3) > form.layout (legacy)
      let panels = [];
      let layoutSource = "form"; // pro debug
      if (template && template.layout) {
        const tLayout = (typeof template.layout === "string")
          ? JSON.parse(template.layout)
          : template.layout;
        if (Array.isArray(tLayout.panels)) {
          panels = tLayout.panels.slice();
          layoutSource = "template:" + (template.code || "?");
        }
      }
      if (panels.length === 0) {
        const formLayout = form.layout || {};
        if (Array.isArray(formLayout.panels)) {
          panels = formLayout.panels.slice();
          layoutSource = "form.layout";
        }
      }
      // Posledni fallback: default panel "main" (Marti's doctrine: panel je MANDATORY)
      if (panels.length === 0) {
        panels = [{ slot: "main", label: "", order: 10, components: [] }];
        layoutSource = "default-fallback";
      }

      // Phase 38.4 Krok 5.P-1+ (17.5.2026 vecer, Marti's "CORE 22 stale
      // chybi footer buttons po 5.P-1"): ENSURE FOOTER PANEL ALWAYS EXISTS.
      // Marti's doctrine "ErpJadroForm = vzdy jedna class, systemove stejne"
      // — kazdy form 302 musi mit footer panel pro hardcoded X Storno + ✓ OK
      // (5.P-1). Pokud source layout (template.layout / form.layout / default
      // fallback) neobsahuje footer slot, append synthetic.
      //
      // Bez tohoto fix: CORE 22 form.layout ma jen [main] -> footer branch
      // v _render loopu se nikdy nespusti -> no OK/Storno. CORE 23 ma
      // [header, main, footer] -> footer fires -> OK works. To je
      // "kazdy zvlast" pattern co Marti explicitne odmita.
      // Phase 38.4 Krok 5.P-1++++ (17.5.2026 vecer, Marti's "paticka
      // align down"): ENSURE MAIN PANEL TOO (parita s ensure footer
      // pattern). Bez main panelu by Grid row 2 (1fr stretch) zustal
      // prazdny a footer by se posunul nahoru.
      const hasMain = panels.some(p => p && p.slot === "main");
      if (!hasMain) {
        panels.push({ slot: "main", label: "", order: 100, components: [] });
      }
      const hasFooter = panels.some(p => p && p.slot === "footer");
      if (!hasFooter) {
        panels.push({ slot: "footer", label: "", order: 999, components: [] });
      }
      console.info("[DesignFwForm] layout source:", layoutSource, "panels:", panels.length, "footer ensured:", !hasFooter);

      // Sort panels by order
      panels.sort((a, b) => (a.order || 0) - (b.order || 0));

      // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Build byParent map pro
      // recursive container rendering. Backend (Krok 14e-B) vraci flat list
      // ALL descendants of form (recursive CTE), kazdy s parent_comp_def_id.
      // Tree postaveni client-side groupingem.
      const byParent = new Map();
      for (const f of fields) {
        const pid = f.parent_comp_def_id;
        if (!byParent.has(pid)) byParent.set(pid, []);
        byParent.get(pid).push(f);
      }
      // Sort each parent's children by sort_order (z SQL uz seralene, ale
      // defensive — pripadny re-sort po DnD)
      for (const arr of byParent.values()) {
        arr.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Group ONLY direct children of form root by region_slot (top-level
      // containers a/nebo leaf fields v legacy formech). Nested children
      // (groupbox -> fields) jdou pres recursive _renderComponentTree.
      const formChildren = byParent.get(form.id) || [];
      const fieldsBySlot = {};
      for (const f of formChildren) {
        const slot = f.region_slot || "main";
        if (!fieldsBySlot[slot]) fieldsBySlot[slot] = [];
        fieldsBySlot[slot].push(f);
      }

      // Render každý panel jako sekce
      const D = this._onDirty.bind(this);

      // Cache byParent + data + D pro recursive helper volane v loop nize
      // (musi byt AZ po `const D` declaraci — TDZ guard, jinak hodi
      // "Cannot access 'D' before initialization")
      this.__renderCtx = { byParent, data, onDirty: D };

      // Phase 38.4 Krok 14f-G (14.5.2026 vecer, Marti's "dropnul jsem
      // novy panel, zkopirovaly se gridy"): reset flag per _render cycle.
      // Child sections (TELEFONY/EMAILY) renderujeme JEN v prvnim alClient
      // panelu, ne ve vsech. Pokud Marti pridal alTop/alBottom/alLeft/
      // alRight, child sections zustavaji v alClient panelu (canonical
      // main area).
      this._childrenRenderedInAnyPanel = false;

      for (const panel of panels) {
        const slotFields = fieldsBySlot[panel.slot] || [];
        const templateComponents = Array.isArray(panel.components) ? panel.components : [];

        // Panel header — empty label = "panel je plocha" doctrine (12.5. 23:30)
        const sec = _sectionBuild(panel.label || "", "panel: " + panel.slot);

        // Phase 38.4 Krok 14b+5 polish #4 (13.5.2026 ~14:15): CSS Grid
        // 3-row layout v root (auto 1fr auto) reseni alClient deterministicky.
        // Sekce uz nepotrebuji flex magic — Grid jim assignuje row slot.
        // Per-panel jen styling specific (footer separator, main fill).
        //
        // Drop default margin-bottom: 14px z _sectionBuild — root grid
        // gap (7px po polish #7) ridi spacing mezi panel rows.
        sec.wrap.style.marginBottom = "0";

        if (panel.slot === "footer") {
          // Margin-bottom: 0 (vlastni grid row, no spacing below)
          sec.wrap.style.marginBottom = "0";
          // Visual separator nad footer
          sec.wrap.style.borderTop = "1px solid #2a3340";
          sec.wrap.style.paddingTop = "10px";
          // Krok 14b+16 (14.5.2026 rano, Marti's polish):
          //   - Discard btn (vlevo) + spacer (flex:1) + OK/Storno (vpravo)
          // Krok 14b+16.1 (14.5.2026 rano, Marti's catch "OK uteklo doprostred"):
          //   space-between s 3 children rozhazoval OK do stredu. Fix:
          //   flex spacer mezi discard a OK/Storno -> spacer absorbuje
          //   prostor, OK+Storno drzi vpravo. Konzistentni v obou stavech
          //   (discard visible/hidden).
          sec.grid.style.display = "flex";
          sec.grid.style.justifyContent = "flex-start";
          sec.grid.style.alignItems = "center";
          sec.grid.style.gap = "16px";

          // Inject dirty discard button na ZACATEK (vlevo)
          const discardBtn = document.createElement("button");
          discardBtn.type = "button";
          discardBtn.className = "erp-form-dirty-discard";
          discardBtn.style.cssText =
            "background:transparent;border:1px solid #5a4830;color:#d4b88a;" +
            "padding:5px 12px;border-radius:3px;cursor:pointer;font-size:11px;" +
            "font-style:italic;transition:background 0.15s,border-color 0.15s;" +
            "display:none;";  // initially hidden (count=0)
          discardBtn.title = "Klikni pro zrušení všech tebou provedených změn (vrátit původní hodnoty).";
          discardBtn.addEventListener("mouseenter", () => {
            discardBtn.style.background = "#1f1810";
            discardBtn.style.borderColor = "#7a5a3a";
          });
          discardBtn.addEventListener("mouseleave", () => {
            discardBtn.style.background = "transparent";
            discardBtn.style.borderColor = "#5a4830";
          });
          discardBtn.addEventListener("click", async () => {
            const decision = await _confirmDarkDialog({
              title: "Zrušit změny",
              message: "Chceš, abych tebou provedené změny zrušila?",
            });
            if (decision === true) {
              await this._revertAllChanges();
            }
          });
          this._dirtyDiscardBtn = discardBtn;

          // Phase 38.4 Krok 5.R-C+7 (18.5.2026 vecer pozde): coreInfo pill
          // vlevo dole v paticce. Format "coreId:rowId". Marti's "par malickosti
          // pro orientaci".
          // Krok 5.R-C+7.5 (18.5.2026 vecer pozde): fix wrong field refs —
          // DesignFwForm ma this.opts.coreId + this.opts.rowId, ne _coreId/_rowId.
          try {
            var _ciCoreId = (this.opts && this.opts.coreId != null) ? this.opts.coreId
              : (this._spec && this._spec.core && this._spec.core.id != null) ? this._spec.core.id
              : null;
            var _ciRowId = (this.opts && this.opts.rowId != null) ? this.opts.rowId
              : (this._spec && this._spec.data && this._spec.data.id != null) ? this._spec.data.id
              : null;
            if (_ciCoreId != null) {
              var _ciLabel = String(_ciCoreId) + ":";
              if (_ciRowId != null) _ciLabel += String(_ciRowId);
              var _ciPill = document.createElement("button");
              _ciPill.type = "button";
              _ciPill.className = "erp-form-coreinfo-pill";
              _ciPill.textContent = _ciLabel;
              _ciPill.title = "core_id:row_id  (klik: zatím no-op, drop-up menu příjde)";
              // Phase 38.4 Krok 5.R-C+7.4 (18.5.2026 vecer): apply same design
              // jako grid pill — borderless, monospace, tabular-nums, fixed
              // min-width 90px, left-edge align (padding-left:0).
              _ciPill.style.cssText =
                "position:relative;background:transparent;border:none;color:#a8b4c2;" +
                "min-width:90px;padding:5px 12px 5px 0;border-radius:3px;" +
                "cursor:pointer;font-size:11px;font-weight:600;" +
                "font-family:ui-monospace,Consolas,Monaco,monospace;" +
                "font-variant-numeric:tabular-nums;" +
                "text-align:left;transition:background 0.15s,color 0.15s;" +
                "margin-right:8px;";
              _ciPill.addEventListener("mouseenter", function () {
                _ciPill.style.background = "rgba(255,255,255,0.05)";
                _ciPill.style.color = "#b8c4d2";
              });
              _ciPill.addEventListener("mouseleave", function () {
                _ciPill.style.background = "transparent";
                _ciPill.style.color = "#a8b4c2";
              });
              // Phase 38.4 Krok 5.R-C+8 (18.5.2026): click → drop-up menu
              var _formCoreId = _ciCoreId;
              var _formRowId = _ciRowId;
              var _formCoreLabel = (this._spec && this._spec.core && this._spec.core.label) || null;
              var _formCoreCode = (this._spec && this._spec.core && this._spec.core.code) || null;
              _ciPill.addEventListener("click", function (ev) {
                ev.stopPropagation();
                _showFormPillMenu(_ciPill, {
                  coreId: _formCoreId,
                  rowId: _formRowId,
                  coreLabel: _formCoreLabel,
                  coreCode: _formCoreCode,
                });
              });
              sec.grid.appendChild(_ciPill);
            }
          } catch (e) {
            console.warn("[DesignFwForm coreInfo pill] failed:", e);
          }

          sec.grid.appendChild(discardBtn);

          // Krok 14b+16.1: flex spacer aby OK+Storno drzela vpravo. Bez
          // ohledu na discard visibility (visible -> [discard][spacer]
          // [OK][Storno]; hidden -> [-][spacer][OK][Storno]).
          const spacer = document.createElement("div");
          spacer.className = "erp-form-footer-spacer";
          spacer.style.cssText = "flex:1 1 auto;";
          sec.grid.appendChild(spacer);

          // Update visibility podle aktualniho dirty count (volane po _render)
          this._updateDirtyDiscardBtn();

          // Phase 38.4 Krok 5.P-1 (17.5.2026 vecer, Marti's "ErpJadroForm
          // = vzdy jedna class, jednotny render"): hardcoded X Storno + ✓ OK
          // buttons. Parita s Power tools (DesignDataSourceEditor /
          // DataSet / DbConnection). Drop template-driven button rendering
          // (Krok 14b+3 path) — uniformita vitezi nad special-case template
          // buttons.
          //
          // CORE 22 (Editace uzivatele) + CORE 23 (Framework: Desing
          // Prehled) chovaji se nyni IDENTICKY — zadny "kazdy zvlast"
          // (Marti's doctrine 17.5. vecer).
          //
          // Order: discardBtn — spacer — X Storno — ✓ OK (rightmost).
          // Click handlers wire na existing class methods (_onSaveClick
          // + _shell.close()), dirty guard od A1t pattern automaticky
          // pres _shell.close → _handleCloseClick.
          // Phase 38.4 Krok 5.P-1+++ (17.5.2026 vecer, Marti's "tlacitka
          // prohozena, Storno cerveny krizek"): swap order — OK primary
          // VLEVO, Storno secondary VPRAVO. Parita s A1t pattern (12.5.
          // vecer): "Uložit primary vlevo, Zrušit secondary vpravo".
          // Plus X červený (destructive accent) — Marti's recurring
          // pattern z konfirmacnich dialogu (#5a3a3a / #d48787).
          const okBtn = document.createElement("button");
          okBtn.type = "button";
          okBtn.textContent = "✓ OK";
          okBtn.style.cssText =
            "padding:6px 16px;background:#3a5a3a;border:1px solid #4a7a4a;" +
            "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;" +
            "font-weight:600;";
          // Phase 38.4 Krok 5.P-1+++++ (17.5.2026 vecer, Marti's "OK nereaguje"):
          // DesignFwForm NEMA _onSaveClick — save method je _handleSaveAndClose
          // (volana z _renderTemplateComponent button action='save_and_close'
          // branch). Volání s btnEl ref pro visual feedback "⏳ Ukládám…".
          okBtn.addEventListener("click", () => this._handleSaveAndClose(okBtn));
          sec.grid.appendChild(okBtn);

          const cancelBtn = document.createElement("button");
          cancelBtn.type = "button";
          cancelBtn.textContent = "X Storno";
          cancelBtn.style.cssText =
            "padding:6px 16px;background:#5a3a3a;border:1px solid #7a4a4a;" +
            "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;";
          cancelBtn.addEventListener("click", () => {
            if (this._shell && typeof this._shell.close === "function") {
              this._shell.close();
            }
          });
          sec.grid.appendChild(cancelBtn);
        } else if (panel.slot === "main") {
          // Main je v Grid row 2 (1fr) — alClient automaticky.
          // Marti's polish (13.5.2026 ~14:45): "alClient ten panel" —
          // empty state hint MA rozsahnut na celou main panel area
          // (sec.grid je hint container, fills wrap fully).
          sec.wrap.style.minHeight = "0"; // critical pro grid 1fr shrink
          sec.wrap.style.display = "flex";
          sec.wrap.style.flexDirection = "column";
          sec.grid.style.flex = "1 1 auto";
          sec.grid.style.minHeight = "0";
          // Drop alignContent:start — necháme hint stretch fill
          // (alignContent default = stretch v grid s 1 item)
        }
        // header — no extra styling, Grid auto-rows assignuje natural height

        // Phase 38.4 Krok 5.P-1++++ (17.5.2026 vecer, Marti's "paticka
        // align down"): explicit gridRow assignment per panel.slot.
        // Bez tohoto Grid implicit assigment hraje insertion order ->
        // pokud panels nemaji header, main dostane row 1 (auto, natural
        // height) misto row 2 (1fr stretch), footer dostane row 2 (1fr)
        // misto row 3 (auto). Footer se pak stretch over remaining height.
        //
        // Explicit gridRow garantuje:
        //   - header (slot='header') → Grid row 1 (auto, natural top)
        //   - main (slot='main')     → Grid row 2 (1fr, stretch fill)
        //   - footer (slot='footer') → Grid row 3 (auto, natural bottom)
        if (panel.slot === "header") {
          sec.wrap.style.gridRow = "1";
        } else if (panel.slot === "main") {
          sec.wrap.style.gridRow = "2";
        } else if (panel.slot === "footer") {
          sec.wrap.style.gridRow = "3";
          // Krok 5-B Fix #7 polish (29.5.2026): root grid gap:0 (drop
          // 7px artifact pred main). Footer zachova viditelny gap nad
          // sebou (oddeleny od MAIN-CLIENT obsahu) pres vlastni
          // marginTop. Bez tohoto by OK/Storno sedelo flush pod
          // poslednim panelem.
          sec.wrap.style.marginTop = "7px";
        }

        // Phase 38.4 Krok 14b+3: render template-level components (header/footer)
        // PRED fields (fields jsou typicky v 'main' panel, components v 'header' / 'footer')
        //
        // Krok 14b+7.2 (13.5.2026 ~20:45, Marti's "Zrus pomocne fieldy
        // Editace uživatele user #14 pending... jsou tam navic"): SKIP
        // title / entity_badge / status_pill template komponenty. Modal
        // title bar v _shell.title (z core.label) je sole title source —
        // template komponenty duplikuji informaci ktera je vzdy viditelna.
        // Buttons (OK/Storno) ZUSTAVAJI — to jsou funkcni actions, ne
        // pomocne pills.
        const SUPPRESSED_TEMPLATE_TYPES = new Set([
          "title", "entity_badge", "status_pill",
          // Phase 38.4 Krok 5.P-1 (17.5.2026 vecer, Marti's doctrine
          // "ErpJadroForm = vzdy jedna class"): drop template-driven
          // button rendering. Hardcoded X Storno + ✓ OK v _render
          // footer panel (parita s Power tools). Future-proof — pokud
          // fw.template.layout JSON nadale ma button components,
          // skip render — no duplicate s hardcoded.
          "button",
        ]);
        for (const comp of templateComponents) {
          const compType = comp && comp.type ? String(comp.type) : "";
          if (SUPPRESSED_TEMPLATE_TYPES.has(compType)) continue;  // skip
          const compEl = this._renderTemplateComponent(comp, core, data);
          if (compEl) sec.grid.appendChild(compEl);
        }

        // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Recursive component
        // rendering. slotFields obsahuje TOP-LEVEL children form rootu pro
        // dany region_slot.
        //
        // Phase 38.4 Krok 14f-B (14.5.2026 vecer, Marti's B alClient):
        // Pokud slotFields obsahuje container (panel/groupbox) s layout.align,
        // pouzij Delphi VCL align layout (flexbox). Jinak fallback na
        // legacy per-field render.
        if (slotFields.length > 0) {
          slotFields.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

          // Detect align system: aspoň jeden top-level container s layout.align
          const hasContainers = slotFields.some(
            (f) => f.comp_type_code === "panel" || f.comp_type_code === "groupbox"
          );

          if (hasContainers && panel.slot === "main") {
            // NEW Krok 14f-B: Delphi VCL align layout (flexbox)
            // Sec.grid musi být flex container (drop CSS Grid behavior)
            sec.grid.style.display = "flex";
            sec.grid.style.flexDirection = "column";
            sec.grid.style.minHeight = "0";
            sec.grid.style.padding = "0";
            sec.grid.style.gap = "0";
            const alignLayout = this._buildAlignLayout(slotFields);
            sec.grid.appendChild(alignLayout);
          } else {
            // LEGACY: per-field render (slot=header/footer, nebo flat fields)
            for (let idx = 0; idx < slotFields.length; idx++) {
              const f = slotFields[idx];
              const compEl = this._renderComponentTree(f, idx, slotFields.length);
              if (compEl) sec.grid.appendChild(compEl);
            }
          }
        }
        // Krok 14b+7.2 (13.5.2026 ~20:45, Marti's "to okno na formu pridat
        // dalsi pole je k nicemu... Nahradila ho tvoje futura v hlavicce +
        // Pole"): footer hint "+ Pridat dalsi pole" SMAZAN. Header button
        // "+ Pole" (z 14b+7.1) je sole entry point — vzdy visible v DESIGN
        // mode, nezavisly od panel content / scroll position. Empty hint
        // (v full-empty case) zustava — discoverability pro novy form.

        // Empty state — panel 'main' bez fields i bez template components.
        // Phase 38.4 Krok 5.P-1++ (17.5.2026 vecer, Marti's "23 ma
        // dvojitou hlavicku"): placeholder JEN pro 'main' panel. Header
        // a footer jsou UI chrome (title bar / action buttons) — empty
        // state hint je matoucí ("dvojita hlavicka" / "panel footer nema
        // fields" vedle hardcoded OK/Storno).
        if (panel.slot === "main"
            && templateComponents.length === 0
            && slotFields.length === 0) {
          const hint = document.createElement("div");
          // Phase 38.4 Krok 14b+5 polish #6 (13.5.2026 ~14:45, Marti's
          // "alClient ten panel"): hint fills entire grid (1/-1 v obou
          // axes) + display:flex + center align aby text vystreden uprostred
          // velkeho boxu.
          //
          // Krok 14c (13.5.2026 odpoledne): hint je clickable trigger pro
          // FieldPickerModal.
          //
          // Krok 14b+7 (13.5.2026 ~20:00): hint je clickable JEN v DESIGN
          // mode. V PRODUCTION je hint neutralni info text bez click handleru
          // (uzivatel nesmi sahat na strukturu omylem). Marti's "PROD/DESIGN
          // trigger" doctrine — strukturalni zmeny vyzaduji explicit DESIGN
          // mode.
          const designMode = this._formDesignMode === true;
          const canPick = panel.slot === "main"
            && core.data_entity_type
            && (this._spec.form && this._spec.form.id)
            && typeof global.FieldPickerModal === "function";
          const interactive = designMode && canPick;

          hint.style.cssText =
            "padding:14px;background:#0f141a;border:1px dashed " +
            (interactive ? "#3a5a8a" : "#2a3340") + ";" +
            "border-radius:4px;color:#5d6975;font-style:italic;" +
            "text-align:center;grid-column:1/-1;grid-row:1/-1;" +
            "display:flex;align-items:center;justify-content:center;" +
            "cursor:" + (interactive ? "pointer" : "default") + ";" +
            "transition:background 0.15s,border-color 0.15s;";

          if (interactive) {
            hint.innerHTML =
              "(panel '" + panel.slot + "' nemá žádné fields)<br>" +
              "<span style=\"font-size:11px;color:#7ed4e8;margin-top:4px;\">" +
              "🎨 Klikni pro otevření palety komponent ➕" +
              "</span>";
          } else if (canPick) {
            // Production mode — info text s navodom prepnout DESIGN
            hint.innerHTML =
              "(panel '" + panel.slot + "' nemá žádné fields)<br>" +
              "<span style=\"font-size:11px;color:#7a8696;margin-top:4px;\">" +
              "Form je v PRODUCTION módu. Pro přidání polí přepni vpravo nahoře na 🎨 DESIGN." +
              "</span>";
          } else {
            // No picker available (entity_type / formId chybi / panel != main)
            hint.innerHTML = "(panel '" + panel.slot + "' nemá žádné fields)";
          }

          if (interactive) {
            // Hover visual (jen v design mode)
            hint.addEventListener("mouseenter", () => {
              hint.style.background = "#141a20";
              hint.style.borderColor = "#5a8aaa";
            });
            hint.addEventListener("mouseleave", () => {
              hint.style.background = "#0f141a";
              hint.style.borderColor = "#3a5a8a";
            });

            // Click → open FieldPickerModal (Krok 14b+7.1: shared helper)
            hint.addEventListener("click", () => {
              this._openFieldPicker();
            });
            hint.title = "Klikni pro otevření palety komponent (Krok 14c)";
          } else if (canPick) {
            hint.title = "Pro přidávání polí přepni form do DESIGN módu (button vpravo nahoře v header).";
          }

          sec.grid.appendChild(hint);
        }

        // Phase 38.4 Krok 14c+3 (14.5.2026 odpoledne, Marti's "drag-and-drop
        // na to spravne misto"): tag panel s data-region-slot pro drop
        // detection. Drop handler dohledá target panel pres Y coord +
        // dataset lookup.
        sec.wrap.dataset.regionSlot = panel.slot || "main";

        // Phase 38.4 Krok 14d-D polish 2 (14.5.2026 vecer, Marti's
        // "Gridy prosim dragabled pro presun nahoru do main"):
        // Main panel jako drop target pro children sections. Drop nad
        // main → child se přesune před main panel (this._childPosition).
        if (panel.slot === "main") {
          sec.wrap.addEventListener("dragover", (ev) => {
            const types = ev.dataTransfer && ev.dataTransfer.types;
            if (!types || !Array.from(types).includes("application/x-erp-child-section")) return;
            ev.preventDefault();
            ev.dataTransfer.dropEffect = "move";
            sec.wrap.style.borderTop = "3px solid #5dbf5d";
          });
          sec.wrap.addEventListener("dragleave", (ev) => {
            if (ev.target === sec.wrap || ev.currentTarget === sec.wrap) {
              sec.wrap.style.borderTop = "";
            }
          });
          sec.wrap.addEventListener("drop", (ev) => {
            const draggedKey = ev.dataTransfer.getData("application/x-erp-child-section");
            if (!draggedKey) return;
            ev.preventDefault();
            sec.wrap.style.borderTop = "";
            // Move child to before-main position
            this._childPosition = this._childPosition || {};
            this._childPosition[draggedKey] = "before-main";
            this._render();
            this._attachDropTargetForGalleryDrag();
            _showToast("Sekce přesunuta nahoru", "success", 1500);
          });
        }

        root.appendChild(sec.wrap);

        // Phase 38.4 Krok 14d-D polish 2: insert children with position=
        // 'before-main' RIGHT AFTER main panel — no, BEFORE main panel...
        // wait, we already appended main. We need to insert before.
        // Re-think: pojďme insert children-before-main PRED main append.
      }

      // Phase 38.4 Krok 14e-G (14.5.2026 vecer, Marti's "patri ty gridy
      // taky na panel?"): Child sections JIZ jsou rendered UVNITR panel
      // wrapper (viz _renderContainerNode pro 'panel'). Root level
      // child rendering NENI potreba — children sit pod panelem.
      //
      // _childOrder + _childPosition state initialization zachovan pro
      // backward compat (legacy forms bez panelu, kde panel je memory-only
      // virtual concept). _renderChildSection drag handlers stale pouzivaji
      // tyto pro position tracking.
      const childrenData = (this._spec && this._spec.children) || {};
      const allKeys = Object.keys(childrenData);
      if (allKeys.length > 0) {
        if (!this._childOrder || this._childOrder.length !== allKeys.length) {
          this._childOrder = [...allKeys];
        } else {
          this._childOrder = this._childOrder.filter(k => allKeys.includes(k));
          for (const k of allKeys) {
            if (!this._childOrder.includes(k)) this._childOrder.push(k);
          }
        }
        this._childPosition = this._childPosition || {};
      }
      // Defensive fallback: pokud form NEMA panel (legacy forms), render
      // children sections na root level (former behavior). Probehne jen
      // pokud root nema zadny .erp-design-panel descendant po render.
      if (allKeys.length > 0 && !root.querySelector(".erp-design-panel")) {
        console.warn(
          "[DesignFwForm] form nemá panel container — render child sections " +
          "na root level (legacy fallback). Doporuceni: pridat panel " +
          "(comp_type_code='panel') jako prvni dite form rootu."
        );
        const beforeMain = this._childOrder.filter(
          k => this._childPosition[k] === "before-main"
        );
        const afterMain = this._childOrder.filter(
          k => this._childPosition[k] !== "before-main"
        );
        if (beforeMain.length > 0) {
          const mainPanelEl = root.querySelector('[data-region-slot="main"]');
          for (const childKey of beforeMain) {
            const childInfo = childrenData[childKey];
            if (!childInfo) continue;
            const childSec = this._renderChildSection(childKey, childInfo);
            if (mainPanelEl) {
              root.insertBefore(childSec, mainPanelEl);
            } else {
              root.appendChild(childSec);
            }
          }
        }
        for (const childKey of afterMain) {
          const childInfo = childrenData[childKey];
          if (!childInfo) continue;
          root.appendChild(this._renderChildSection(childKey, childInfo));
        }
      }

      this._shell.body.appendChild(root);

      // Phase 38.4 Krok 5-B Fix #9 (29.5.2026 pozde, Marti's "omezit
      // minimalni velikost formu, tak aby respektoval minimalni vysku
      // panelu"): compute total min height z panels[] + slotFields
      // layouts. Set dialog.minHeight aby user nemohl resize pod
      // content minimum (MAIN-BOTTOM by jinak overflowoval pod
      // footer OK/Storno).
      try {
        const _slotDefaults = { header: 0, main: 0, footer: 50 };
        const _computeSlotMinHeight = (slotKey) => {
          const sFields = fieldsBySlot[slotKey] || [];
          const baseline = _slotDefaults[slotKey] || 0;
          if (sFields.length === 0) return baseline;
          // Pro main slot s Delphi VCL align layout:
          //   top strip = SUM(top panel min_heights)
          //   middle row = MAX(left/client/right min_heights)
          //   bottom strip = SUM(bottom panel min_heights)
          if (slotKey === "main") {
            const byAlign = { top: [], bottom: [], left: [], right: [], client: [] };
            for (const f of sFields) {
              const a = String((f.layout && f.layout.align) || "client").toLowerCase();
              const key = (a in byAlign) ? a : "client";
              byAlign[key].push(f);
            }
            const _mh = (f) => {
              const v = f.layout && f.layout.min_height;
              if (v == null) return 0;
              if (typeof v === "number") return v;
              const n = parseInt(v, 10);
              return isNaN(n) ? 0 : n;
            };
            const sumStrip = (arr) => arr.reduce((s, f) => s + _mh(f), 0);
            const maxMid = (arr) => arr.reduce((m, f) => Math.max(m, _mh(f)), 0);
            const topH = sumStrip(byAlign.top);
            const botH = sumStrip(byAlign.bottom);
            const midH = Math.max(
              maxMid(byAlign.left),
              maxMid(byAlign.client),
              maxMid(byAlign.right),
              0
            );
            return Math.max(baseline, topH + midH + botH);
          }
          // Header / footer / other: max children min_height
          let maxH = baseline;
          for (const f of sFields) {
            const v = f.layout && f.layout.min_height;
            const n = typeof v === "number" ? v : parseInt(v, 10);
            if (!isNaN(n) && n > maxH) maxH = n;
          }
          return maxH;
        };

        let totalMinContent = 0;
        for (const p of panels) {
          totalMinContent += _computeSlotMinHeight(p.slot);
        }
        // Modal chrome: header (~50px), body padding-bottom (~12px),
        // root grid footer marginTop (7px), buffer (4px).
        const modalChrome = 50 + 12 + 7 + 4;
        const totalMin = totalMinContent + modalChrome;

        if (totalMin > 0 && this._shell && this._shell.dialog) {
          // Cap na 90vh (matchuje max-height z _buildModalShell) aby
          // dialog na malych obrazovkach byl scrollable, ne off-screen.
          const viewportCap = Math.floor(window.innerHeight * 0.9);
          this._shell.dialog.style.minHeight = Math.min(totalMin, viewportCap) + "px";
        }

        // Phase 38.4 Krok 5-B Fix #10 (29.5.2026 pozde, Marti's "To
        // samy udelej s sirkou formulare"): mirror Fix #9 logiku pro
        // width. Pro main slot s Delphi VCL alignLayout:
        //   left strip = SUM(alLeft min_widths) [stacked horizontally]
        //   middle = MAX(alClient min_widths)
        //   right strip = SUM(alRight min_widths)
        //   top/bottom strips = MAX(top/bottom min_widths) [full width]
        //   slot width = MAX(topW, leftW+midW+rightW, botW)
        // Pro header/footer/other slot: MAX(children min_widths).
        // Total form width = MAX vsech slot widths (vsechny slots jsou
        // full-width vrstvy v root grid).
        const _computeSlotMinWidth = (slotKey) => {
          const sFields = fieldsBySlot[slotKey] || [];
          if (sFields.length === 0) return 0;
          const _mw = (f) => {
            const v = f.layout && f.layout.min_width;
            if (v == null) return 0;
            if (typeof v === "number") return v;
            const n = parseInt(v, 10);
            return isNaN(n) ? 0 : n;
          };
          if (slotKey === "main") {
            const byAlign = { top: [], bottom: [], left: [], right: [], client: [] };
            for (const f of sFields) {
              const a = String((f.layout && f.layout.align) || "client").toLowerCase();
              const key = (a in byAlign) ? a : "client";
              byAlign[key].push(f);
            }
            const sumStrip = (arr) => arr.reduce((s, f) => s + _mw(f), 0);
            const maxStrip = (arr) => arr.reduce((m, f) => Math.max(m, _mw(f)), 0);
            const topW = maxStrip(byAlign.top);
            const botW = maxStrip(byAlign.bottom);
            const middleW =
              sumStrip(byAlign.left) +
              maxStrip(byAlign.client) +
              sumStrip(byAlign.right);
            return Math.max(topW, middleW, botW);
          }
          // Header / footer / other: max children min_width
          let maxW = 0;
          for (const f of sFields) {
            const w = _mw(f);
            if (w > maxW) maxW = w;
          }
          return maxW;
        };

        let totalMinContentWidth = 0;
        for (const p of panels) {
          const slotW = _computeSlotMinWidth(p.slot);
          if (slotW > totalMinContentWidth) totalMinContentWidth = slotW;
        }
        // Modal chrome side: body padding 16px*2 + dialog border 2px +
        // resize handle buffer 4px + minor buffer 4px = ~42px
        const modalChromeWidth = 42;
        const totalMinW = totalMinContentWidth + modalChromeWidth;

        if (totalMinW > 0 && this._shell && this._shell.dialog) {
          // Cap na 95vw (modal max-width = 95vw z _buildModalShell)
          const viewportCapW = Math.floor(window.innerWidth * 0.95);
          this._shell.dialog.style.minWidth = Math.min(totalMinW, viewportCapW) + "px";
        }
      } catch (e) {
        console.warn("[DesignFwForm] min height/width calc failed:", e);
      }

      // Phase 38.4 Krok 14g-C (15.5.2026 rano, Marti's "videt v separatnim
      // liste graficky schema toho layoutu"): floating right-side schema
      // tree panel. DESIGN mode only. Persistent state v localStorage
      // (Marti's "videt co se stalo" debugging when form je v broken
      // state).
      if (this._formDesignMode === true) {
        this._renderSchemaTreePanel();
      }

      // Phase 38.4 Krok 14b+5 polish (13.5.2026 dopoledne, Marti's
      // request): footer template's OK/Storno tlacitka jsou jedine
      // close actions — modal shell footer (Zavřít) ZRUSENO. Konsolidace
      // UX: jedna paticka, jedne actions.
      // Hide shell footer pokud existuje (defensive — _buildModalShell
      // muze default render footer s padding).
      if (this._shell && this._shell.footer) {
        this._shell.footer.style.display = "none";
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-C (15.5.2026 rano, Marti's "schema layoutu
    // v separatnim liste"): read-only schema tree side panel.
    //
    // Floating fixed-position container vpravo (z-index nad form modal).
    // Toggle pres button v DESIGN header. Persistent open/closed state
    // v localStorage ("erp_design_schema_tree_open").
    //
    // Tree displays form.id root + all descendants z this._spec.fields
    // (recursive CTE response z Krok 14e-B). Per node:
    //   - Indentace podle depth (level * 16px)
    //   - Icon emoji per code (▦ panel, ▣ groupbox, ○ leaf)
    //   - Color: panel purple, groupbox amber, leaf gray
    //   - Display: code · #id · caption
    //
    // Click na node → scroll do view + flash. Plus ✕ per row =
    // emergency delete (calls _performFieldDelete).
    // ════════════════════════════════════════════════════════════════
    _renderSchemaTreePanel() {
      // Cleanup existing panel (re-render scenario)
      const existing = document.body.querySelector(".erp-schema-tree-panel");
      if (existing) {
        try { document.body.removeChild(existing); } catch (e) {}
      }

      // Read persistent open state
      const STORAGE_KEY = "erp_design_schema_tree_open";
      let isOpen;
      try {
        isOpen = localStorage.getItem(STORAGE_KEY) === "1";
      } catch (e) {
        isOpen = false;
      }

      // Container — fixed position vpravo, collapsible
      const panel = document.createElement("div");
      panel.className = "erp-schema-tree-panel";
      panel.style.cssText =
        "position:fixed;top:80px;right:" + (isOpen ? "16px" : "-340px") + ";" +
        "width:360px;max-height:calc(100vh - 120px);" +
        "background:#0d1117;border:1px solid #2a3340;border-radius:6px;" +
        "color:#cfd6df;font-size:12px;font-family:inherit;" +
        "box-shadow:-4px 0 16px rgba(0,0,0,0.5);" +
        "display:flex;flex-direction:column;z-index:10001;" +
        "transition:right 0.25s ease;";

      // Toggle handle button (always visible, attached to panel right edge)
      const handle = document.createElement("button");
      handle.type = "button";
      handle.title = isOpen ? "Skryj schema (Esc)" : "Ukaz schema layoutu";
      handle.style.cssText =
        "position:absolute;top:50%;left:-32px;transform:translateY(-50%);" +
        "width:32px;height:64px;background:#1a2028;border:1px solid #2a3340;" +
        "border-right:none;border-radius:6px 0 0 6px;color:#a88cd4;" +
        "cursor:pointer;font-size:14px;line-height:1;" +
        "display:flex;align-items:center;justify-content:center;" +
        "writing-mode:vertical-rl;letter-spacing:1px;";
      handle.innerHTML = "🌳 " + (isOpen ? "▶" : "◀");
      handle.addEventListener("click", () => {
        const opening = panel.style.right === "-340px" || panel.style.right === "";
        panel.style.right = opening ? "16px" : "-340px";
        handle.innerHTML = "🌳 " + (opening ? "▶" : "◀");
        handle.title = opening ? "Skryj schema (Esc)" : "Ukaz schema layoutu";
        try {
          localStorage.setItem(STORAGE_KEY, opening ? "1" : "0");
        } catch (e) {}
      });
      panel.appendChild(handle);

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:10px 14px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;" +
        "border-radius:6px 6px 0 0;flex-shrink:0;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:13px;";
      const fields = this._spec.fields || [];
      const counts = {
        panel: fields.filter(f => f.comp_type_code === "panel").length,
        groupbox: fields.filter(f => f.comp_type_code === "groupbox").length,
        leaf: fields.filter(f =>
          f.comp_type_code !== "panel" && f.comp_type_code !== "groupbox"
        ).length,
      };
      title.innerHTML = "🌳 Schema · <span style=\"color:#7a8696;font-weight:400;\">" +
                        counts.panel + " panely · " + counts.groupbox + " groupboxy · " +
                        counts.leaf + " fields</span>";
      header.appendChild(title);
      panel.appendChild(header);

      // Body — scrollable tree
      const body = document.createElement("div");
      body.style.cssText =
        "padding:8px 4px;overflow-y:auto;flex:1 1 auto;min-height:0;" +
        "font-family:ui-monospace,Consolas,monospace;";
      panel.appendChild(body);

      // Build tree z byParent map (same algorithm as _render but for display)
      const byParent = new Map();
      for (const f of fields) {
        const pid = f.parent_comp_def_id;
        if (!byParent.has(pid)) byParent.set(pid, []);
        byParent.get(pid).push(f);
      }
      for (const arr of byParent.values()) {
        arr.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Root marker — form root
      const form = this._spec.form;
      if (form) {
        const rootNode = this._buildSchemaTreeNode(
          { id: form.id, comp_type_code: "form", caption: this._spec.core.label || form.caption || form.name },
          0,
          /*isRoot*/ true
        );
        body.appendChild(rootNode);
      }

      // Walk byParent recursively start from form.id
      const _walk = (parentId, depth) => {
        const children = byParent.get(parentId) || [];
        for (const child of children) {
          const node = this._buildSchemaTreeNode(child, depth, false);
          body.appendChild(node);
          // Recurse only for containers
          if (child.comp_type_code === "panel" || child.comp_type_code === "groupbox") {
            _walk(child.id, depth + 1);
          }
        }
      };
      if (form) _walk(form.id, 1);

      // Empty state
      if (fields.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;text-align:center;color:#5d6975;font-style:italic;";
        empty.textContent = "Žádné komponenty v formuláři.";
        body.appendChild(empty);
      }

      document.body.appendChild(panel);
      this._schemaTreePanel = panel;
    }

    _buildSchemaTreeNode(comp, depth, isRoot) {
      const code = comp.comp_type_code;
      const isContainer = code === "panel" || code === "groupbox";
      const isForm = code === "form";

      // Color + icon per type
      let icon, color;
      if (isForm) { icon = "▣"; color = "#7ed4e8"; }
      else if (code === "panel") { icon = "▦"; color = "#a88cd4"; }
      else if (code === "groupbox") { icon = "▤"; color = "#d4b88a"; }
      else { icon = "○"; color = "#9ba8b8"; }

      const node = document.createElement("div");
      node.className = "erp-schema-tree-node";
      node.dataset.compDefId = String(comp.id);
      node.dataset.compTypeCode = code;
      node.style.cssText =
        "display:flex;align-items:center;gap:6px;" +
        "padding:3px 8px 3px " + (8 + depth * 14) + "px;" +
        "cursor:pointer;border-left:2px solid transparent;" +
        "transition:background 0.1s, border-left-color 0.1s;";
      node.addEventListener("mouseenter", () => {
        // Highlight jen pokud ne v drag mode (dragover override)
        if (!this._schemaTreeDragging) {
          node.style.background = "#141a20";
          node.style.borderLeftColor = color;
        }
      });
      node.addEventListener("mouseleave", () => {
        if (!this._schemaTreeDragging) {
          node.style.background = "";
          node.style.borderLeftColor = "transparent";
        }
      });

      // Phase 38.4 Krok 14g-E (15.5.2026 rano, Marti's "drop ve strome"):
      // Drag-and-drop reorder/move pres schema tree. Non-root, non-form
      // nodes draggable. Pres _dragState pipeline.
      if (!isRoot && !isForm) {
        node.draggable = true;
        node.addEventListener("dragstart", (ev) => {
          ev.stopPropagation();
          this._schemaTreeDragging = true;
          node.style.opacity = "0.5";
          this._dragState = {
            fieldId: comp.id,
            fromIndex: 0,
            el: node,
            isContainer: isContainer,
            fromSchemaTree: true,
          };
          try {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", "schema:" + comp.id);
          } catch (e) {}
        });
        node.addEventListener("dragend", () => {
          this._schemaTreeDragging = false;
          node.style.opacity = "";
          // Clean all node highlights
          const panel = document.body.querySelector(".erp-schema-tree-panel");
          if (panel) {
            panel.querySelectorAll(".erp-schema-tree-node").forEach((n) => {
              n.style.background = "";
              n.style.borderLeftColor = "transparent";
              n.style.outline = "";
            });
          }
          this._dragState = null;
        });
        node.addEventListener("dragover", (ev) => {
          if (!this._dragState || !this._dragState.fromSchemaTree) return;
          if (this._dragState.fieldId === comp.id) return;
          ev.preventDefault();
          ev.stopPropagation();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          // Visual: container target = outline INSIDE (move INTO)
          //         non-container = top/bottom edge (reorder)
          if (isContainer) {
            node.style.background = "rgba(168, 140, 212, 0.15)";
            node.style.outline = "2px solid #a88cd4";
            node.style.outlineOffset = "-2px";
          } else {
            const rect = node.getBoundingClientRect();
            const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
            node.style.borderTop = isAbove ? "3px solid #7ed4e8" : "2px solid transparent";
            node.style.borderBottom = isAbove ? "2px solid transparent" : "3px solid #7ed4e8";
            node.style.background = "rgba(126, 212, 232, 0.08)";
          }
        });
        node.addEventListener("dragleave", () => {
          node.style.background = "";
          node.style.outline = "";
          node.style.borderTop = "";
          node.style.borderBottom = "";
        });
        node.addEventListener("drop", (ev) => {
          if (!this._dragState || !this._dragState.fromSchemaTree) return;
          ev.preventDefault();
          ev.stopPropagation();
          const fromId = this._dragState.fieldId;
          const toId = comp.id;
          if (fromId === toId) return;
          // Clear visual
          node.style.background = "";
          node.style.outline = "";
          node.style.borderTop = "";
          node.style.borderBottom = "";

          if (isContainer) {
            // Drop ON container → move INTO (parent_comp_def_id = container.id)
            const fields = this._spec.fields || [];
            const fromComp = fields.find((f) => f.id === fromId);
            if (fromComp && fromComp.parent_comp_def_id === comp.id) {
              _showToast("Komponenta uz je v tomto kontejneru", "info", 1500);
              return;
            }
            this._performFieldMove(fromId, comp.id);
          } else {
            // Drop on sibling (leaf field) → reorder OR cross-parent
            const rect = node.getBoundingClientRect();
            const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
            this._performFieldReorder(fromId, toId, isAbove);
          }
        });
      }

      // Icon
      const iconEl = document.createElement("span");
      iconEl.textContent = icon;
      iconEl.style.cssText = "color:" + color + ";font-size:13px;line-height:1;flex-shrink:0;";
      node.appendChild(iconEl);

      // Code
      const codeEl = document.createElement("span");
      codeEl.textContent = code;
      codeEl.style.cssText = "color:" + color + ";font-weight:600;flex-shrink:0;";
      node.appendChild(codeEl);

      // #id
      const idEl = document.createElement("span");
      idEl.textContent = "#" + comp.id;
      idEl.style.cssText = "color:#5d6975;font-size:10px;flex-shrink:0;";
      node.appendChild(idEl);

      // Caption + align/border info
      let captionText = comp.caption || comp.name || "";
      if (comp.layout) {
        if (code === "panel" && comp.layout.align) {
          captionText += " · " + comp.layout.align;
        } else if (code === "groupbox" && comp.layout.border_mode) {
          captionText += " · " + comp.layout.border_mode;
        }
      }
      if (captionText) {
        const capEl = document.createElement("span");
        capEl.textContent = captionText;
        capEl.style.cssText = "color:#cfd6df;font-size:11px;flex:1 1 auto;" +
                              "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
        node.appendChild(capEl);
      } else {
        const spacer = document.createElement("span");
        spacer.style.cssText = "flex:1 1 auto;";
        node.appendChild(spacer);
      }

      // Action buttons (jen pro non-root, non-form)
      if (!isRoot && !isForm) {
        // ⚙ Settings
        const settingsBtn = document.createElement("button");
        settingsBtn.type = "button";
        settingsBtn.textContent = "⚙";
        settingsBtn.title = "Nastaveni komponenty";
        settingsBtn.style.cssText =
          "background:transparent;border:none;color:#5d6975;" +
          "cursor:pointer;font-size:11px;padding:2px 4px;line-height:1;" +
          "border-radius:2px;transition:color 0.1s;";
        settingsBtn.addEventListener("mouseenter", () => {
          settingsBtn.style.color = "#a88cd4";
        });
        settingsBtn.addEventListener("mouseleave", () => {
          settingsBtn.style.color = "#5d6975";
        });
        settingsBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          // Krok 5-B (29.5.2026, Marti's "sjednot ciste"):
          // unified _openFieldSettings handles containers via isContainer
          // detection. Drop legacy _openContainerSettings dispatch.
          this._openFieldSettings(comp);
        });
        node.appendChild(settingsBtn);

        // ✕ Delete
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.textContent = "✕";
        delBtn.title = "Smazat tuto komponentu";
        delBtn.style.cssText =
          "background:transparent;border:none;color:#5d2828;" +
          "cursor:pointer;font-size:11px;padding:2px 4px;line-height:1;" +
          "border-radius:2px;transition:color 0.1s;";
        delBtn.addEventListener("mouseenter", () => {
          delBtn.style.color = "#e57373";
        });
        delBtn.addEventListener("mouseleave", () => {
          delBtn.style.color = "#5d2828";
        });
        delBtn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          const decision = await _confirmDarkDialog({
            title: "Smazat z schema",
            message: "Smazat " + code + " '" + (comp.caption || comp.name) +
                     "' (#" + comp.id + ")?\n\n(soft-delete, audit zustava)",
          });
          if (decision !== true) return;
          await this._performFieldDelete(comp);
        });
        node.appendChild(delBtn);
      }

      // Click on node — scroll do view + flash
      node.addEventListener("click", () => {
        if (isRoot || isForm) return;
        const targetEl = this._shell && this._shell.body &&
          this._shell.body.querySelector('[data-comp-def-id="' + comp.id + '"]') ||
          this._shell.body.querySelector('[data-field-id="' + comp.id + '"]');
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
          // Flash highlight
          const orig = targetEl.style.outline;
          targetEl.style.outline = "3px solid " + color;
          targetEl.style.outlineOffset = "2px";
          targetEl.style.transition = "outline-color 0.6s ease";
          setTimeout(() => {
            targetEl.style.outline = orig;
            targetEl.style.outlineOffset = "";
          }, 1200);
        }
      });

      return node;
    }

    // Phase 38.4 Krok 14b+3 (13.5.2026 rano): render template-level component.
    // template.layout.panels[].components = [{type: 'title'|'entity_badge'|'status_pill'|'button', ...}]
    // - title: source='core.label' -> velky text
    // - entity_badge: format='{entity_type} #{row_id}' -> maly badge
    // - status_pill: source='data.status', optional=true -> colored pill (jen pokud data.status exists)
    // - button: action='save_and_close'|'abandon' -> visual button s onClick (Save flow Krok 14b+5 wire-up)
    _renderTemplateComponent(comp, core, data) {
      if (!comp || !comp.type) return null;
      const compType = comp.type;
      try {
        if (compType === "title") {
          const el = document.createElement("h2");
          el.className = "erp-fw-template-title";
          el.style.cssText = "margin:0 0 8px;font-size:18px;font-weight:600;color:#e8eef5;grid-column:1/-1;";
          el.textContent = this._resolveTemplateSource(comp.source, core, data) || core.label || "(bez nazvu)";
          return el;
        }
        if (compType === "entity_badge") {
          const el = document.createElement("span");
          el.className = "erp-fw-template-badge";
          el.style.cssText = "display:inline-block;padding:2px 8px;background:rgba(74,123,168,0.18);border:1px solid rgba(74,123,168,0.4);border-radius:10px;font-size:11px;color:#9bb5d6;font-family:'JetBrains Mono',monospace;grid-column:1/-1;justify-self:start;";
          const entityType = core.data_entity_type || "?";
          const rowId = (data && (data.id != null ? data.id : data.ID != null ? data.ID : "?")) ?? "?";
          const format = comp.format || "{entity_type} #{row_id}";
          el.textContent = format
            .replace("{entity_type}", entityType)
            .replace("{row_id}", rowId);
          return el;
        }
        if (compType === "status_pill") {
          const value = this._resolveTemplateSource(comp.source, core, data);
          if (value == null || value === "") {
            // Marti-AI's 'optional: true' doctrine — skip render pokud chybi
            if (comp.optional) return null;
            // ELSE: render empty pill (visible že tam má být status)
          }
          const el = document.createElement("span");
          el.className = "erp-fw-template-status-pill";
          el.style.cssText = "display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:500;grid-column:1/-1;justify-self:start;";
          // Color by status
          const stat = String(value || "").toLowerCase();
          if (stat === "active") {
            el.style.background = "rgba(80,150,80,0.18)";
            el.style.border = "1px solid rgba(80,150,80,0.5)";
            el.style.color = "#8bc88b";
          } else if (stat === "pending") {
            el.style.background = "rgba(180,140,60,0.18)";
            el.style.border = "1px solid rgba(180,140,60,0.5)";
            el.style.color = "#d4b88a";
          } else if (stat === "disabled") {
            el.style.background = "rgba(180,80,80,0.18)";
            el.style.border = "1px solid rgba(180,80,80,0.5)";
            el.style.color = "#d4888a";
          } else {
            el.style.background = "rgba(140,140,140,0.18)";
            el.style.border = "1px solid rgba(140,140,140,0.5)";
            el.style.color = "#9ca3af";
          }
          el.textContent = value || "(no status)";
          return el;
        }
        if (compType === "button") {
          // Phase 38.4 Krok 14b+3 visual MVP -> Krok 14b+5 LIVE Save flow.
          // 13.5.2026 ~12:30 polish (Marti's request):
          //   - Standardni sirka (min/max constraint), ne grid-full
          //   - ✓ green check icon na save action, ✗ red cross na abandon
          //   - Right-aligned v grid cell (justify-self: end)
          //
          // action='save_and_close' -> PATCH endpoint + close modal
          // action='abandon' -> dirty check -> "Mám uložit změny?" modal
          const el = document.createElement("button");
          el.type = "button";
          el.className = "erp-fw-template-btn";
          const variant = comp.variant || "secondary";
          const action = comp.action || "noop";

          // Icon prefix podle action (ne podle variant — variant je color,
          // action je semantic: save vs abandon vs custom)
          let iconHtml = "";
          if (action === "save_and_close") {
            iconHtml = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>';
          } else if (action === "abandon") {
            iconHtml = '<span style="color:#d4888a;font-weight:700;margin-right:6px;">✗</span>';
          }
          // Custom actions (future) — ne forcing icon

          // Sirka: min 90px (visible), max 140px (compact). margin pro
          // mezeru mezi buttons. grid-column: auto + justify-self: end aby
          // sedele do flex-end pravidla footer panel.
          const sizeStyle =
            "min-width:90px;max-width:140px;padding:6px 16px;" +
            "border-radius:3px;cursor:pointer;font-size:13px;" +
            "margin:6px 4px 0 0;grid-column:auto;justify-self:end;";

          if (variant === "primary") {
            el.style.cssText = sizeStyle +
              "background:#3a5a8a;border:1px solid #4a7ba8;color:#e8eef5;font-weight:600;";
          } else {
            el.style.cssText = sizeStyle +
              "background:#2a3340;border:1px solid #3a4754;color:#cfd6df;";
          }
          el.innerHTML = iconHtml + (comp.label || "(button)");
          el.addEventListener("click", async () => {
            console.info("[DesignFwForm] template button click — action:", action);
            // Phase 38.4 Krok 14b+5 (13.5.2026 dopoledne): Save flow LIVE
            if (action === "save_and_close") {
              await this._handleSaveAndClose(el);
            } else if (action === "abandon") {
              // Reuse existing _beforeCloseHandler (dirty check + close)
              this._shell.close();
            } else {
              alert("Unknown action: " + action);
            }
          });
          return el;
        }
        // Unknown component type → log + skip
        console.warn("[DesignFwForm] unknown template component type:", compType, comp);
        return null;
      } catch (e) {
        console.error("[DesignFwForm] template component render error:", e, comp);
        return null;
      }
    }

    // Helper — resolve template source path (e.g. 'core.label' -> core.label, 'data.status' -> data.status)
    _resolveTemplateSource(source, core, data) {
      if (!source) return null;
      const parts = String(source).split(".");
      let cur = null;
      if (parts[0] === "core") cur = core;
      else if (parts[0] === "data") cur = data;
      else return null;
      for (let i = 1; i < parts.length; i++) {
        if (cur == null) return null;
        cur = cur[parts[i]];
      }
      return cur;
    }

    // Phase 38.4 Krok 14b+5 (13.5.2026 dopoledne): OK button save_and_close action
    // Marti's Centrala 1 doctrine: "OK = optimistic save + close. Bez ptaní."
    //
    // Flow:
    //   1. Collect dirty field changes z this._dirty Set (field values z DOM)
    //   2. Pokud žádné changes -> just close (clean OK = no-op + close)
    //   3. POST PATCH /api/v1/erp/design/{entity}/{id} s field_changes + expected_updated_at
    //   4. 200 -> green toast "Uloženo" + close modal
    //   5. 409 -> dialog "Někdo jiný mezitím změnil řádek. Načíst znovu?"
    //   6. Jiná chyba -> error toast, modal zůstane otevřený (user může retry)
    async _handleSaveAndClose(btnEl) {
      // Visual: btn disabled + "Ukládám..." během PATCH
      // (preserve HTML innerHTML aby icon mohl být restored při error revert)
      const originalHtml = btnEl.innerHTML;
      btnEl.disabled = true;
      btnEl.innerHTML = "⏳ Ukládám…";

      try {
        const core = this._spec.core;
        const data = this._spec.data || {};
        // Phase 38.4 Krok 5.N-2 (17.5.2026, Marti's "code je optional, ID
        // je truth"): entityType = String(core.id) misto core.code. URL build
        // /design/22/14 (ID-based). Backend dispatcher detekuje numeric vs
        // string a routes podle _FW_FORM_CORE_REGISTRY (ID-based) nebo
        // _FW_FORM_ENTITY_MAP (legacy string fallback). Marti's rename code
        // na cokoliv neproblém — ID je truth.
        const entityType = core.id != null ? String(core.id) : core.code;
        const rowId = data.id != null ? data.id : (data.ID != null ? data.ID : null);
        const expectedUpdatedAt = data.updated_at;

        // Krok 5.I-G hotfix (16.5.2026 ~22:45, Marti's "Save selhal: missing
        // entity_type nebo row_id" pri pickeru-only zmenach): NE early-exit.
        // Pokud user mení JEN entity_picker comp_def root (no core data
        // changes), nepotrebujeme entity_type/row_id. Validace presunuta na
        // conditional check po collect — vyžadována jen pri fieldChanges
        // non-empty (core entity save flow).

        // Collect dirty changes z DOM. _field / _dropdown helpers ukladaji
        // wrap._fieldKey + wrap._inst (UI Kit instance). Walkujem vsechny
        // wrap divy v body a filtrujem ty co maji fieldKey v this._dirty.
        const fieldChanges = {};
        const allWraps = this._shell.body.querySelectorAll(".erp-field, .erp-dropdown, .erp-memo");
        for (const wrap of allWraps) {
          const fk = wrap._fieldKey;
          if (!fk || !this._dirty.has(fk)) continue;
          // Phase 38.4 Krok 5.M-1 (17.5.2026, Marti's "Save selhal: missing
          // entity_type" hotfix): skip entity_pickers — maji vlastni save
          // flow pres compDefChanges (second loop nize). Entity_picker wrap
          // sdili .erp-field class kvuli vizualnimu styling, ale neni to
          // core entity field. wrap._kind === "entity_picker" identifies.
          if (wrap.classList && wrap.classList.contains("erp-entity-picker-host")) continue;
          if (wrap._kind === "entity_picker") continue;
          // fieldKey format: "<core.code>.<field.name>" -> extract field name
          const parts = fk.split(".");
          if (parts.length < 2) continue;
          const fieldName = parts.slice(1).join(".");
          // Get current value via UI Kit instance (.value() method) nebo
          // fallback na DOM input.value
          let val = null;
          if (wrap._inst && typeof wrap._inst.value === "function") {
            val = wrap._inst.value();
          } else if (wrap._inst && wrap._inst.input) {
            val = wrap._inst.input.value;
          } else {
            const inp = wrap.querySelector("input, textarea, select");
            if (inp) val = inp.value;
          }
          fieldChanges[fieldName] = val;
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.I-G (16.5.2026 vecer): collect
        // entity_picker changes pro comp_def root PATCH (Marti's two-layer
        // data_source pattern). Picker #3 Datovy zdroj (display_mode='editable',
        // field_extern='data_source_id') ukladame na form root comp_def.
        const compDefChanges = {};
        const pickerWraps = this._shell.body.querySelectorAll(".erp-entity-picker-host");
        for (const pwrap of pickerWraps) {
          if (pwrap._displayMode !== "editable" || !pwrap._fieldExtern) continue;
          const initialId = pwrap._initialValue ? pwrap._initialValue.id : null;
          // _selectedValue je null po unlink, undefined pred user action.
          // Pokud undefined -> stale na initial. Pokud null nebo new value -> changed.
          let currentId;
          if (pwrap._selectedValue === undefined) {
            currentId = initialId;
          } else if (pwrap._selectedValue === null) {
            currentId = null;
          } else {
            currentId = pwrap._selectedValue.id;
          }
          if (currentId !== initialId) {
            compDefChanges[pwrap._fieldExtern] = currentId;
          }
        }

        // Phase 38.4 Krok 5.M-5+1 FIX (17.5.2026, Marti's "Ma ode mne nastaveno
        // editable"): dispatch routing podle field_extern column name.
        // Picker #2 (Prehled) ma display_mode='editable' (Marti's change),
        // ale save target = menu_node.core_id (ne form root comp_def).
        //
        // Routing rule:
        //   field_extern='core_id' AND runtimeMenuNodePk set → menuNodePatch
        //     (Picker #2 Prehled → menu_node.core_id pres runtime context)
        //   ELSE → compDefChanges (Picker #3 → form root comp_def — existing
        //     behavior, jiz handled v predchozim loopu)
        //
        // Edge case: pokud field_extern='core_id' ale runtimeMenuNodePk
        // chybi (form opened bez context menu, napr. via direct URL),
        // change zustane v compDefChanges → form root PATCH. Defensive
        // fallback, ne ztracene dirty.
        const menuNodePatch = {};
        const runtimeMenuNodePk = this.opts && this.opts.runtimeMenuNodePk;
        if (runtimeMenuNodePk) {
          for (const pwrap of pickerWraps) {
            // Only editable + field_extern='core_id' route to menu_node
            if (pwrap._displayMode !== "editable") continue;
            if (pwrap._fieldExtern !== "core_id") continue;
            if (!pwrap._fieldKey || !this._dirty.has(pwrap._fieldKey)) continue;
            const initialId = pwrap._initialValue ? pwrap._initialValue.id : null;
            let currentId;
            if (pwrap._selectedValue === undefined) {
              currentId = initialId;
            } else if (pwrap._selectedValue === null) {
              currentId = null;
            } else {
              currentId = pwrap._selectedValue.id;
            }
            if (currentId !== initialId) {
              menuNodePatch.core_id = currentId;
              // Remove from compDefChanges (predchozi loop ho tam pridal)
              delete compDefChanges.core_id;
            }
          }
        }

        // Pokud žádné changes -> clean close (Marti's "OK clean = close" doctrine)
        if (Object.keys(fieldChanges).length === 0
            && Object.keys(compDefChanges).length === 0
            && Object.keys(menuNodePatch).length === 0) {
          console.info("[DesignFwForm] OK clicked, no dirty changes — closing.");
          this._dirty.clear();
          _markFormDirty(this, false);
          this._shell.close();
          return;
        }

        // Krok 14g-H+4 (25.5.2026): CREATE mode dispatch — POST namisto PATCH.
        // Marti's Q1=A "naprosté minimum at se nezamotame": pri CREATE mode
        // (this.opts.rowId == null) ignorujeme compDefChanges + menuNodePatch
        // (picker save flow patri jen k existing rows). Jen field_changes →
        // POST /api/v1/erp/design/{core_id} (backend design_insert_entity).
        const _isCreateSave = (this.opts.rowId == null);
        let savedFieldsCount = 0;
        let lastRespData = null;
        if (_isCreateSave) {
          if (Object.keys(fieldChanges).length === 0) {
            alert(
              "Nový záznam: nezadal jsi žádnou hodnotu.\n\n" +
              "Vyplň alespoň jedno pole (description_user nebo některé z " +
              "ostatních polí formuláře) a zkus to znovu."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          if (!core.id) {
            alert("Save selhal: core.id chybí v _spec.");
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const rPost = await fetch(
            "/api/v1/erp/design/" + encodeURIComponent(core.id),
            {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ field_changes: fieldChanges }),
            }
          );
          if (!rPost.ok) {
            const errData = await rPost.json().catch(() => ({}));
            alert(
              "Vytvoření nového záznamu selhalo: HTTP " + rPost.status + "\n" +
              (errData.error || "(žádný error message)")
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          lastRespData = await rPost.json();
          savedFieldsCount = Object.keys(fieldChanges).length;
          console.info("[DesignFwForm] POST CREATE success:", lastRespData);
          // Skip PATCH 2 (comp_def) + PATCH 3 (menu_node) — irrelevant pro CREATE.
          // Pokracujeme rovnou na "200 OK — toast + close" blok nize.
        } else if (Object.keys(fieldChanges).length > 0) {
          // Krok 5.I-G hotfix (16.5.2026 ~22:45): validace entity context
          // PRESUNUTA sem (early exit v top byla too strict — blokovalo i
          // picker-only changes pres comp_def root). Aktivuje se jen pokud
          // user opravdu modifikoval core entity sloupce.
          if (!entityType || rowId == null) {
            alert(
              "Save selhal: missing entity_type nebo row_id\n\n" +
              "Core entity changes detected (" +
              Object.keys(fieldChanges).join(", ") +
              ") ale form nema kontext entity row."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const r = await fetch(
            "/api/v1/erp/design/" + encodeURIComponent(entityType) + "/" + encodeURIComponent(rowId),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: fieldChanges,
                expected_updated_at: expectedUpdatedAt,
              }),
            }
          );

          if (r.status === 409) {
            const errData = await r.json().catch(() => ({}));
            alert(
              "Konflikt na " + entityType + ": někdo jiný mezitím změnil tento řádek.\\n" +
              "Server čas: " + (errData.server_updated_at || "?") + "\\n" +
              "Tvůj čas: " + (errData.expected_updated_at || "?") + "\\n\\n" +
              "Zavři modal a otevři znovu (Enter / dvojklik), tvé změny budou ztraceny."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          if (!r.ok) {
            const errData = await r.json().catch(() => ({}));
            alert(
              "Uložení " + entityType + " selhalo: HTTP " + r.status + "\\n" +
              (errData.error || "(žádný error message)")
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          lastRespData = await r.json();
          savedFieldsCount += Object.keys(fieldChanges).length;
          console.info("[DesignFwForm] PATCH " + entityType + " success:", lastRespData);
        }

        // Krok 5.I-G: PATCH 2 — comp_def root (Picker #3 + future per-instance
        // settings). Optimistic lock pres form.updated_at (Krok 5.I-A2 trigger).
        // Krok 14g-H+4 (25.5.2026): skip PATCH 2 v CREATE mode (picker save flow
        // patri jen k existing rows; nove row dostane pickery z defaults).
        const formRoot = this._spec.form || {};
        if (!_isCreateSave && Object.keys(compDefChanges).length > 0) {
          if (formRoot.id == null || !formRoot.updated_at) {
            alert(
              "Save selhal: form root comp_def chybi id nebo updated_at.\\n" +
              "Backend musi vracet form.id + form.updated_at (Krok 5.I-F)."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const r2 = await fetch(
            "/api/v1/erp/design/comp_def/" + encodeURIComponent(formRoot.id),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: compDefChanges,
                expected_updated_at: formRoot.updated_at,
              }),
            }
          );

          if (r2.status === 409) {
            const errData = await r2.json().catch(() => ({}));
            alert(
              "Konflikt na comp_def root: někdo jiný mezitím změnil form metadata.\\n" +
              "Server čas: " + (errData.server_updated_at || "?") + "\\n" +
              "Zavři modal a otevři znovu."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          if (!r2.ok) {
            const errData = await r2.json().catch(() => ({}));
            alert(
              "Uložení comp_def root selhalo: HTTP " + r2.status + "\\n" +
              (errData.error || "(žádný error message)")
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }

          lastRespData = await r2.json();
          savedFieldsCount += Object.keys(compDefChanges).length;
          console.info("[DesignFwForm] PATCH comp_def success:", lastRespData);
        }

        // Phase 38.4 Krok 5.M-5+1 (17.5.2026, Marti's "priradit prehled
        // ke kazdemu soudecku"): PATCH 3 — menu_node.core_id (Picker #2
        // Prehled save). Runtime menu_node_pk z context menu fix.
        // Krok 14g-H+4 (25.5.2026): skip v CREATE mode (menu_node binding
        // patri k existing core id; novy row nezna context menu).
        if (!_isCreateSave && Object.keys(menuNodePatch).length > 0) {
          const r3 = await fetch(
            "/api/v1/erp/design/menu_node/" + encodeURIComponent(runtimeMenuNodePk),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: menuNodePatch,
              }),
            }
          );
          if (!r3.ok) {
            const errData = await r3.json().catch(() => ({}));
            alert(
              "Uloženi menu_node selhalo: HTTP " + r3.status + "\n" +
              (errData.error || "(žádný error message)") + "\n\n" +
              "Soudeček-Přehled pairing nedotaženo. Form ostatní změny " +
              "(pokud jsou) byly ulozeny."
            );
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
            return;
          }
          const r3data = await r3.json();
          savedFieldsCount += Object.keys(menuNodePatch).length;
          console.info("[DesignFwForm] PATCH menu_node success:", r3data);
        }

        // 200 OK — toast + close
        const respData = lastRespData || {};

        // Visual feedback — green flash krátce před close
        btnEl.style.background = "#3a7a3a";
        btnEl.style.borderColor = "#4a9a4a";
        btnEl.innerHTML = _isCreateSave ? "✅ Vytvořeno" : "✅ Uloženo";

        // Clear dirty state (modal close handler nepokusí dirty check)
        const _changeCount = this._dirty.size;
        this._dirty.clear();
        _markFormDirty(this, false);

        // Phase 38.4 Krok 14b+9-A (13.5.2026 ~21:30): toast notification
        // misto silent close. Marti's prezentace polish.
        // Krok 14g-H+4 (25.5.2026): CREATE mode toast "Vytvořeno — id=X"
        // s nove vygenerovanym ID z POST response (lastRespData.id).
        const _wToast = _changeCount === 1 ? "změna" : (_changeCount < 5 ? "změny" : "změn");
        let _toastMsg;
        if (_isCreateSave) {
          const _newId = lastRespData && lastRespData.id;
          _toastMsg = _newId != null
            ? ("Vytvořeno — nový záznam #" + _newId)
            : "Vytvořeno";
        } else if (_changeCount > 0) {
          _toastMsg = "Uloženo — " + _changeCount + " " + _wToast;
        } else {
          _toastMsg = "Uloženo";
        }
        _showToast(_toastMsg, "success");

        // Phase 38.4 Krok 14b+5 polish (13.5.2026 ~18:35, Marti's
        // "refresh gridu po save" request): trigger callback s response
        // data. Callback v openFwFormForRow re-renderuje aktualni grid.
        if (typeof this.opts.onSaveSuccess === "function") {
          try {
            this.opts.onSaveSuccess(respData);
          } catch (e) {
            console.error("[DesignFwForm] onSaveSuccess callback failed:", e);
          }
        }

        // Po krátké pauze close
        setTimeout(() => {
          this._shell.close();
        }, 600);
      } catch (e) {
        console.error("[DesignFwForm] save failed:", e);
        _showToast("Save selhal: " + (e.message || e), "error", 3500);
        btnEl.disabled = false;
        btnEl.innerHTML = originalHtml;
      }
    }

    // Krok 14b+8 (13.5.2026 ~21:00, Marti's "komponenty RO a ready for
    // Drag and drop"): wrap field element do draggable containeru s grip
    // handle. Volat jen v DESIGN mode + main panel.
    //
    // Drag state je per-form-instance (this._dragState). Drop computes
    // novy sort_order pole + PATCH backend /design/comp-def/reorder.
    _wrapFieldForDesign(fieldEl, field, index, total) {
      const wrap = document.createElement("div");
      wrap.className = "erp-field-design-wrap";
      // Phase 38.4 Krok H+7 (26.5.2026, Marti's "smaz tecky pro drag —
      // form se bude chovat jako v production"): drop draggable + grip.
      // Reorder se nyni dela pres palette ↑/↓ buttons (Krok H+5/H+6).
      // DESIGN-only features (action buttons ✕ ⚙ ⬅ 🎯, contextmenu,
      // dblclick rename, flash) ZUSTAVAJI — Marti's "DESIGN ma actions,
      // jen drag affordance pryc".
      wrap.dataset.fieldId = String(field.id);
      wrap.dataset.fieldIndex = String(index);
      // Krok H+7 (26.5.2026, Marti's "klik v palete -> highlight komponenty"):
      // unified data-comp-def-id pro orchestraci. Field.id IS comp_def.id —
      // selector [data-comp-def-id="X"] matchne fields i containers stejne.
      wrap.dataset.compDefId = String(field.id);
      // Phase 38.4 Krok 14c+3.1 (14.5.2026 odpoledne, Marti's polish
      // po dnešním testu):
      //   "rendruj ty mazaci krizky na pravy okrak komponenty, ne mimo ni.
      //    Tu sipku vlevo pinned rendruj hned vedle toho krizku vlevo."
      //
      // Refactor: action buttons (✕ delete, ⬅ pinned, 🎯 detect-values)
      // jsou teted absolute overlay v pravem hornim rohu content.
      // Content má position:relative pro absolute child positioning.
      // Krok H+7: drop grip column (20px) — grid_template = single 1fr.
      // Plus cursor:default (no grab).
      wrap.style.cssText =
        "display:block;padding:4px 6px;border:1px dashed transparent;" +
        "border-radius:4px;cursor:default;position:relative;min-width:0;";

      // Krok 14b+9-C (13.5.2026 ~21:35): pending flash animation —
      // pokud _pendingFlashFieldId match field.id, apply flash class +
      // clear flag. Pouziva se po reorder + delete na novou pozici.
      if (this._pendingFlashFieldId === field.id) {
        wrap.classList.add("erp-field-flash-success");
        this._pendingFlashFieldId = null;
        // Cleanup class po animation tak ze re-render neopakuje
        setTimeout(() => {
          try { wrap.classList.remove("erp-field-flash-success"); } catch (e) {}
        }, 800);
      }

      // Field content — position:relative pro absolute overlay buttons
      // (Krok 14c+3.1, Marti's "rendruj na pravy okrak komponenty").
      // Krok H+7: content je teted prime dite wrap (no grip column).
      const content = document.createElement("div");
      content.style.cssText = "min-width:0;position:relative;";
      content.appendChild(fieldEl);
      wrap.appendChild(content);

      // Phase 38.4 Krok 14c+3.1 (14.5.2026 odpoledne, Marti's polish):
      // Action buttons jako absolute overlay v PRAVEM HORNIM rohu content
      // (komponenta — input/select/atd.). Order zprava doleva:
      //   ✕ delete (right:4px)        — destruktivni, nejvic vpravo
      //   ⬅ pinned (right:30px)       — vedle ✕
      //   🎯 detect-values (right:56px) — jen lookup, vedle ⬅
      //
      // Hover behavior: default opacity 0, parent .erp-field-design-wrap:hover
      // → opacity 1 (CSS rule existing). ⬅ ON state má opacity:1 !important
      // override (Marti vidí stav i bez hover).
      const alwaysNewRow = !!(field.layout && field.layout.always_new_row);
      const isLookupField = field.comp_type_code === "lookup" ||
                            field.comp_type_code === "combobox";

      // Helper pro consistent button styling
      // Krok H+13.3 (27.5.2026, Marti's "krizek nalevo, nastaveni napravo"):
      // 7th param `anchor` = "right" (default) | "left" — switches CSS anchor.
      const _mkActionBtn = (text, title, bg, border, color, offset, anchor) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = text;
        b.title = title;
        const _anchorSide = (anchor === "left") ? "left" : "right";
        b.style.cssText =
          "position:absolute;top:2px;" + _anchorSide + ":" + offset + "px;" +
          "background:" + bg + ";border:1px solid " + border + ";" +
          "color:" + color + ";padding:0;width:22px;height:22px;" +
          "border-radius:3px;cursor:pointer;font-size:11px;line-height:1;" +
          "display:flex;align-items:center;justify-content:center;" +
          "z-index:2;transition:opacity 0.15s;";
        // Defensive: button nezachycuje drag wrap (preserve drag handle UX)
        b.addEventListener("dragstart", (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
        });
        return b;
      };

      // ⬅ Pinned button (always_new_row toggle)
      // Phase 38.4 Krok 14c+3.3 (14.5.2026 odpoledne, Marti's polish):
      // Hover-only pattern napříč VŠEMI action buttons — sjednoceno
      // i pro ⬅ ON state a 🎯 detect-values. Bez opacity:1 inline override.
      // State pro ⬅ ON visible přes border + bg accent (modry), Marti uvidí
      // při hover. Pro long-term state visibility: future polish field-level
      // left border accent (4px modra pinned indicator).
      // Krok H+13.3.1 (27.5.2026, Marti's "krizek hned vedle ostatnich
      // ikonek vlevo, ne na edge"): ✕ je teted v PRAVE skupine (vlevo od
      // ⚙/⬅/🎯), ne na left:4 edge — tam se trískal s názvem komponenty.
      // Nove poradi zprava doleva: ⚙ (right:4) | ⬅ (right:30) |
      //   bez lookup: ✕ (right:56)
      //   s lookup:   🎯 (right:56) | ✕ (right:82)
      const leftBtn = _mkActionBtn(
        "⬅",
        alwaysNewRow
          ? "Vždy na novém řádku — ZAP. Klikni pro vypnutí."
          : "Vždy na novém řádku — VYP. Klikni pro zapnutí.",
        alwaysNewRow ? "rgba(58,138,168,0.2)" : "transparent",
        alwaysNewRow ? "#3a8aa8" : "#2a3340",
        alwaysNewRow ? "#7ed4e8" : "#5d6975",
        30  // 2. zprava (vedle ⚙)
      );
      leftBtn.className = "erp-field-design-leftpin erp-field-design-action-hoveronly";
      leftBtn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        await this._performFieldToggleAlwaysLeft(field);
      });
      content.appendChild(leftBtn);

      // 🎯 Detect values button — jen lookup/combobox, hover-only
      // (Marti's 14c+3.3 polish: sjednocený hover pattern)
      if (isLookupField) {
        const detectValsBtn = _mkActionBtn(
          "🎯",
          "Auto-detekce hodnot pro dropdown — SELECT DISTINCT z DB.",
          "rgba(58,138,168,0.2)",
          "#3a8aa8",
          "#7ed4e8",
          82  // 4. zprava (vlevo od ✕, jen lookup) — Marti's "✕ hned pred ⬅"
        );
        detectValsBtn.className = "erp-field-design-detectvals erp-field-design-action-hoveronly";
        detectValsBtn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          ev.preventDefault();
          await this._detectAndSaveEnumValues(field);
        });
        content.appendChild(detectValsBtn);
      }

      // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "max_length /
      // min_length parametrizace"): ⚙ Settings button v action overlay.
      // Right-most position posunut o 26px doleva (delete zustava na 4).
      // Krok H+13.3 (27.5.2026): ⚙ uplne napravo (right:4), drop offset chain
      const settingsBtn = _mkActionBtn(
        "⚙",
        "Nastavení komponenty — caption, max/min length, readonly, required",
        "rgba(168, 140, 212, 0.15)",
        "#7a5fa8",
        "#a88cd4",
        4  // nejvíc vpravo
      );
      settingsBtn.className = "erp-field-design-settings erp-field-design-action-hoveronly";
      settingsBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        this._openFieldSettings(field);
      });
      content.appendChild(settingsBtn);

      // ✕ Delete button — Krok H+13.3.2 (27.5.2026, Marti's "Jeste pred
      // pinned ikonku"): ✕ je VŽDY 3. zprava (hned vlevo od ⬅), bez ohledu
      // na lookup. 🎯 (jen lookup) je posunut na 4. zpravo. Pořadí zleva-
      // doprava: [✕ 🎯 ⬅ ⚙] (lookup) / [✕ ⬅ ⚙] (bez lookup).
      const delBtn = _mkActionBtn(
        "✕",
        "Smazat pole '" + (field.caption || field.name) + "'",
        "transparent",
        "#5a2828",
        "#e57373",
        56  // 3. zprava (vedle ⬅) — always
      );
      delBtn.className = "erp-field-design-delete erp-field-design-action-hoveronly";
      delBtn.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        ev.preventDefault();
        const decision = await _confirmDarkDialog({
          title: "Smazat pole",
          message: "Opravdu smazat pole '" + (field.caption || field.name) + "'?\n\n" +
                   "(soft-delete, struktura zachovana v audit historii)",
        });
        if (decision !== true) return;
        await this._performFieldDelete(field);
      });
      // Krok 14c+3.1: append do content (ne wrap), aby absolute positioning
      // bylo relative k komponente, ne k cele rowě.
      content.appendChild(delBtn);

      // Krok 14b+9-B (13.5.2026 ~21:35): inline rename label (dvojklik).
      // Najit label el v fieldEl + attach dblclick. Vsechny comp_type
      // pouzivaji bud .erp-input-label nebo similar label div.
      //
      // Krok H+13 (27.5.2026 ráno): + per-label contextmenu handler →
      // unified modal s defaultTab="user". stopImmediatePropagation()
      // zabrání global capture handler v helpers.js _installFieldLabelRightClick
      // (který by jinak otevřel separate Popup A pro label/hint/color).
      try {
        const labelEl = fieldEl.querySelector(".erp-input-label, .erp-design-section-title, label");
        if (labelEl) {
          labelEl.style.cursor = "context-menu";
          labelEl.title = "Dvojklik pro přejmenování · Pravý klik → nastavení (záložka Uživatel)";
          labelEl.addEventListener("dblclick", (ev) => {
            ev.stopPropagation();
            this._startInlineRename(labelEl, field);
          });
          // Krok H+13: pravý klik na label → unified modal, default Tab "Uživatel"
          labelEl.addEventListener("contextmenu", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            ev.stopImmediatePropagation();  // zabrání global capture handler
            this._openFieldSettings(field, { defaultTab: "user" });
          }, true);  // capture phase — runs PŘED global helpers.js handler
        }
      } catch (e) {
        console.warn("[DesignFwForm] inline rename attach failed:", e);
      }

      // Phase 38.4 Krok 14f-M (14.5.2026 vecer): right-click → field settings
      // Krok H+13 (27.5.2026 ráno): wrap right-click → defaultTab="component"
      // (existing UX — uživatel klikl mimo label = zájem o komponenta config).
      wrap.addEventListener("contextmenu", (ev) => {
        const tag = ev.target && ev.target.tagName;
        // Skip pokud na child input/button — necht native context menu
        if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
          return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        this._openFieldSettings(field, { defaultTab: "component" });
      });

      // Phase 38.4 Krok H+8.1 (26.5.2026, Marti's "intuitivnejsi pres
      // hover + persistent click"): per-wrap click handler DROPPED.
      // Hover/click dispatch je centralized v `open()` pres document-level
      // listener na shell.body (mouseover/click bubble + closest()).
      // Lepsi pro nested fields v panelech (hover transit field→panel→field
      // chodi spravne pres closest, bez per-layer mouseenter/mouseleave race).

      // Phase 38.4 Krok H+7 (26.5.2026): Drag events DROPPED. Reorder
      // se nyni dela pres palette ↑/↓ buttons (Krok H+5/H+6 _moveInLinearizedTree).
      // Form se chova jako v production (zadna drag affordance). Marti's:
      // "form se bude chovat jako v production".

      return wrap;
    }

    async _performFieldDelete(field) {
      // Krok 14b+9-D: DELETE /design/comp-def/{id} -> reload + toast.
      // Phase 38.4 Krok 14g-B (15.5.2026 rano, Marti's "404 ale stale
      // visible"): graceful 404 handling. Pokud row nenalezen (true
      // not found), reload spec stejne — UI mozno stale ho zobrazuje
      // z cache. Backend 200 was_already_deactivated → success toast +
      // reload (cleanup stale UI).
      //
      // Phase 38.4 Krok 14g-D (15.5.2026 rano): undo support — push
      // inverse PATCH is_active=true PRED delete. Po success undo
      // restoruje row.
      const undoLabel = "Smaz " + (field.comp_type_code || "comp") +
                        " '" + (field.caption || field.name) + "' (#" + field.id + ")";
      const undoInverse = async () => {
        await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ is_active: true }),
          }
        );
      };

      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/" + encodeURIComponent(field.id),
          { method: "DELETE", credentials: "include" }
        );
        if (r.status === 404) {
          // True not found — row neexistuje v DB. UI cache stale, force reload.
          console.warn("[DesignFwForm] delete 404 — force reload pro stale UI cleanup");
          _showToast(
            "Komponenta byla mezitim smazana — obnovuji formular",
            "info",
            2500
          );
          await this._reloadSpec();
          return;
        }
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        const data = await r.json().catch(() => ({}));
        if (data.was_already_deactivated) {
          // Idempotent backend response — info toast pro UX clarity
          _showToast(
            "Komponenta uz byla drive smazana — obnovuji formular",
            "info",
            2500
          );
        } else {
          _showToast(
            "Pole '" + (field.caption || field.name) + "' smazáno",
            "success"
          );
          // Krok 14g-D: push undo only on actual delete (ne na already-deactivated)
          this._pushUndoOp(undoLabel, undoInverse);
        }
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] delete failed:", e);
        _showToast("Smazání selhalo: " + (e.message || e), "error", 3500);
      }
    }

    async _detectAndSaveEnumValues(field) {
      // Krok 14b+13: GET distinct hodnoty z DB pro lookup field -> PATCH
      // layout.enum_values. Backend dela: walk parent chain -> core ->
      // data_entity_type -> table -> SELECT DISTINCT column.
      //
      // Krok 14b+13.1 (14.5.2026 ~01:00): diagnostic logging (Marti's
      // smoke: "Detekce probehne, ale do listboxu se to nepropise").
      console.info(
        "[DesignFwForm] _detectAndSaveEnumValues START",
        "field.id=" + field.id,
        "field.name=" + field.name,
        "field.comp_type_code=" + field.comp_type_code,
        "current field.layout=", field.layout
      );
      try {
        _showToast("Detekce hodnot pro '" + (field.caption || field.name) + "'…", "info", 1500);
        const r = await fetch(
          "/api/v1/erp/design/comp-def/" + encodeURIComponent(field.id) + "/distinct-values",
          { credentials: "include" }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        const data = await r.json();
        console.info("[DesignFwForm] distinct-values response:", data);
        if (!data.ok) {
          throw new Error(data.error || "unknown");
        }
        if (!Array.isArray(data.values) || data.values.length === 0) {
          _showToast(
            "Žádné distinct hodnoty pro '" + field.name + "' v tabulce " + (data.table || "?"),
            "error",
            3000
          );
          return;
        }
        // PATCH layout.enum_values (preserve other layout keys)
        const newLayout = Object.assign({}, field.layout || {}, {
          enum_values: data.values,
        });
        console.info("[DesignFwForm] PATCH newLayout:", newLayout);
        const pr = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!pr.ok) {
          const errBody = await pr.json().catch(() => ({}));
          throw new Error("PATCH HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
        }
        const pData = await pr.json();
        console.info("[DesignFwForm] PATCH response:", pData);
        _showToast(
          "Detekováno " + data.values.length + " hodnot pro '" + (field.caption || field.name) + "'",
          "success"
        );
        this._pendingFlashFieldId = field.id;
        await this._reloadSpec();
        // Po reload — verify spec contains enum_values
        const reloadedField = (this._spec.fields || []).find(f => f.id === field.id);
        console.info(
          "[DesignFwForm] POST-RELOAD field.layout:",
          reloadedField ? reloadedField.layout : "(field not found)"
        );
      } catch (e) {
        console.error("[DesignFwForm] detect enum values failed:", e);
        _showToast("Detekce hodnot selhala: " + (e.message || e), "error", 3500);
      }
    }

    async _performFieldToggleAlwaysLeft(field) {
      // Krok 14b+10: toggle layout.always_new_row. PATCH endpoint
      // (Krok 14b+9-B) accept partial layout JSONB — preserve other
      // layout keys (mono, readonly, etc.) pri toggle.
      const currentLayout = (field.layout && typeof field.layout === "object")
        ? field.layout
        : {};
      const wasOn = !!currentLayout.always_new_row;
      const newLayout = Object.assign({}, currentLayout, {
        always_new_row: !wasOn,
      });
      try {
        // Krok 14b+10 hotfix #2: 3-segment route /comp-def/update/{id} aby
        // nematchoval generic 2-segment /design/{entity_type}/{row_id}
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        _showToast(
          !wasOn
            ? "Pole '" + (field.caption || field.name) + "' — vždy na novém řádku ZAP"
            : "Pole '" + (field.caption || field.name) + "' — vždy na novém řádku VYP",
          "success"
        );
        this._pendingFlashFieldId = field.id;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] toggle always-left failed:", e);
        _showToast("Přepnutí selhalo: " + (e.message || e), "error", 3500);
      }
    }

    _startInlineRename(labelEl, field) {
      // Krok 14b+9-B: replace label DIV s INPUT, focus + select.
      // Enter -> PATCH caption. Esc -> revert. Blur -> commit pokud
      // non-empty + zmena, jinak revert.
      const originalLabel = field.caption || field.name;
      const input = document.createElement("input");
      input.type = "text";
      input.value = originalLabel;
      input.style.cssText =
        "font-size:12px;color:#e8eef5;background:#0f141a;" +
        "border:1px solid #3a8aa8;border-radius:3px;padding:2px 6px;" +
        "width:100%;outline:none;";
      // Hide label DIV, insert input pred nim (zachovat label v DOM
      // pro snadny revert)
      labelEl.style.display = "none";
      labelEl.parentNode.insertBefore(input, labelEl);
      // Vyznacit cely text pro rychly retype
      setTimeout(() => {
        input.focus();
        try { input.select(); } catch (e) {}
      }, 0);

      let _committed = false;
      const commit = async (newLabel) => {
        if (_committed) return;
        _committed = true;
        const trimmed = String(newLabel || "").trim();
        // Restore label DIV bez ohledu na outcome
        try { input.parentNode.removeChild(input); } catch (e) {}
        labelEl.style.display = "";
        if (!trimmed || trimmed === originalLabel) {
          return; // revert beze zmeny
        }
        // PATCH backend (Krok 14b+10 hotfix #2: 3-segment route
        // /comp-def/update/{id} aby nematchoval generic 2-segment
        // /design/{entity_type}/{row_id})
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({ caption: trimmed }),
            }
          );
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast("Popisek změněn: '" + trimmed + "'", "success");
          // Flash na renamed field po reload
          this._pendingFlashFieldId = field.id;
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] rename failed:", e);
          _showToast("Přejmenování selhalo: " + (e.message || e), "error", 3500);
        }
      };
      const cancel = () => {
        if (_committed) return;
        _committed = true;
        try { input.parentNode.removeChild(input); } catch (e) {}
        labelEl.style.display = "";
      };
      input.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          commit(input.value);
        } else if (ev.key === "Escape") {
          ev.preventDefault();
          cancel();
        }
      });
      input.addEventListener("blur", () => {
        commit(input.value);
      });
    }

    async _reloadSpec() {
      // Krok 14b+9: shared reload helper (used by delete + rename + reorder)
      // Phase 38.4 Krok 14g Etapa F Krok 5.G (16.5.2026 vecer): null guards
      // pro drafted core (code=NULL, data=null). Fallback na /by-id endpoint
      // pokud code chybi.
      try {
        const core = this._spec && this._spec.core;
        const data = this._spec && this._spec.data;
        const rowId = (data && data.id) || this.opts.rowId || 0;

        let url;
        if (core && core.code) {
          // Fully-formed core — code-based path
          url = "/api/v1/erp/fw-form/" +
                encodeURIComponent(core.code) + "/" +
                encodeURIComponent(rowId);
        } else if (core && core.id) {
          // Drafted core (code=NULL) — fallback na by-id
          url = "/api/v1/erp/fw-form/by-id/" +
                encodeURIComponent(core.id) + "/" +
                encodeURIComponent(rowId);
        } else {
          console.warn("[DesignFwForm] _reloadSpec: no core code or id");
          return;
        }

        const r = await fetch(url, { credentials: "include" });
        if (r.ok) {
          const newSpec = await r.json();
          if (newSpec.ok) {
            this._spec = newSpec;
            this._render();
          }
        }
      } catch (e) {
        console.error("[DesignFwForm] _reloadSpec failed:", e);
      }
    }

    async _performFieldReorder(fromId, toId, dropAbove) {
      // Phase 38.4 Krok 14e-F (14.5.2026 vecer): generalized to siblings
      // (parent_comp_def_id match), ne pouze region_slot='main' fields.
      // Funguje pro:
      //   - leaf fields uvnitr groupbox (parent_comp_def_id=groupbox.id)
      //   - panels uvnitr formu (parent_comp_def_id=form.id)
      //   - groupboxes uvnitr panelu (parent_comp_def_id=panel.id)
      //
      // Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop se neuskutecni"
      // diagnoza): cross-parent drag teted PODPOROVAN. Detect cross-parent
      // → delegate na _performCrossParentMove (atomic move + position).
      const fields = this._spec.fields || [];
      const fromComp = fields.find((f) => f.id === fromId);
      const toComp = fields.find((f) => f.id === toId);
      if (!fromComp || !toComp) {
        console.warn("[DesignFwForm] reorder: from/to not found", fromId, toId);
        return;
      }
      if (fromId === toId) return;
      const parentId = fromComp.parent_comp_def_id;
      if (toComp.parent_comp_def_id !== parentId) {
        // Cross-parent: move + position v target parent
        return this._performCrossParentMove(fromId, toComp, dropAbove);
      }
      // Sibling filter — vsech comp_def se stejnym parent_comp_def_id
      const siblings = fields
        .filter((f) => f.parent_comp_def_id === parentId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      // Krok 14g-D undo: snapshot original sort_orders PRED reorder
      const originalOrders = siblings.map((f) => ({
        id: f.id,
        sort_order: f.sort_order != null ? f.sort_order : 0,
      }));
      const fromIdx = siblings.findIndex((f) => f.id === fromId);
      const toIdx = siblings.findIndex((f) => f.id === toId);
      if (fromIdx < 0 || toIdx < 0) {
        console.warn("[DesignFwForm] reorder: sibling lookup failed", fromId, toId);
        return;
      }
      // Reorder
      const [moved] = siblings.splice(fromIdx, 1);
      // Po splice se toIdx mohl posunout (pokud fromIdx < toIdx)
      let insertAt = siblings.findIndex((f) => f.id === toId);
      if (insertAt < 0) insertAt = siblings.length;
      if (!dropAbove) insertAt += 1;
      siblings.splice(insertAt, 0, moved);
      // Assign new sort_order — multiples of 10 pro budouci insert space
      const payload = siblings.map((f, i) => ({
        id: f.id,
        sort_order: (i + 1) * 10,
      }));
      try {
        const r = await fetch("/api/v1/erp/design/comp-def/reorder", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ field_orders: payload }),
        });
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        console.info("[DesignFwForm] reorder OK:", payload);
        _showToast("Pořadí uloženo", "success");
        // Krok 14g-D undo: push inverse (restore originalOrders)
        this._pushUndoOp(
          "Zmena poradi v parent #" + parentId,
          async () => {
            await fetch("/api/v1/erp/design/comp-def/reorder", {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({ field_orders: originalOrders }),
            });
          }
        );
        // Krok 14b+9-C: flash na moved field po reload (pendingFlashFieldId
        // se cte v _wrapFieldForDesign pri render).
        this._pendingFlashFieldId = fromId;
        // Reload spec + re-render — nova order se projevi
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] reorder failed:", e);
        _showToast("Pořadí selhalo: " + (e.message || e), "error", 3500);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14e-C (14.5.2026 vecer): Recursive component tree
    // rendering. Backend (Krok 14e-B) vraci flat list ALL descendants of
    // form root pres recursive CTE. _render postavi byParent map
    // (Map<parent_comp_def_id, [children]>) v this.__renderCtx.
    //
    // _renderComponentTree(comp, idx, total) → DOM node | null
    //   Dispatch podle comp_type_code:
    //     - panel/groupbox → _renderContainerNode (wrapper + recurse)
    //     - else → _renderLeafField (legacy single field render)
    // ════════════════════════════════════════════════════════════════
    _renderComponentTree(comp, idx, total) {
      const code = comp.comp_type_code;
      // Container types (Marti's 19yr Delphi compat + new modern UI):
      //   panel       = invisible structural section
      //   groupbox    = visual border-top + optional label
      //   pagecontrol = tabs container (renders tabstrip + active tabsheet content)
      //   tabsheet    = wrapper INSIDE pagecontrol (renders children jen kdyz active)
      //
      // Phase 38.4 Krok 14g Etapa F Krok 5.J-B2 (16.5.2026 ~23:50, Marti's
      // "page control jako standardni fw componentu").
      const CONTAINER_CODES = new Set(["panel", "groupbox", "pagecontrol", "tabsheet"]);
      if (CONTAINER_CODES.has(code)) {
        return this._renderContainerNode(comp);
      }
      // Krok 5.Z (30.5.2026, Marti's "Klasickou komponentu gridu 306 pro nase
      // vseobecne pouziti"): embedded grid_modern uvnitr form (tab/panel/
      // groupbox) → inline ErpDataGrid. Render pattern analog master-detail
      // Volba A (data_source_op_detail.js, 24.5.). Pivot z 304 (nested_grid
      // HTML <table>) na 306 kvuli AG Grid features (filter/sort/copy/layout).
      if (code === "grid_modern") {
        return this._renderEmbeddedGridSection(comp);
      }
      // Krok 5.X (27.5.2026): nested_grid je rendered INSIDE _renderContainerNode
      // panel branch (special _renderChildSection dispatch). Pokud nested_grid
      // padne sem (komponenta s parent != panel), skip — sirota, no render.
      if (code === "nested_grid") {
        console.warn(
          "[DesignFwForm] nested_grid #" + comp.id +
          " mimo panel parent — skipped (parent_comp_def_id=" +
          comp.parent_comp_def_id + ")"
        );
        return null;
      }
      // Leaf field — existing behavior
      // Phase CRM Foundation Krok 5-B (28.5.2026 vecer, Marti's mutual
      // immunity doctrine "komponenta selze, ostatni by mely fungovat"):
      // per-field try/catch chrani zbytek formu pred single-field crash.
      // Diagnostic console.error + DOM placeholder (cervena hlaska) misto
      // null return — uzivatel vidi, ktera komponenta selhala.
      try {
        return this._renderLeafField(comp, idx, total);
      } catch (err) {
        console.error(
          "[DesignFwForm] _renderLeafField failed for comp #" + comp.id +
          " (name='" + comp.name + "', type='" + (comp.comp_type_code || "?") + "'):",
          err
        );
        const placeholder = document.createElement("div");
        placeholder.style.cssText =
          "padding:6px 8px;background:#3a1a1a;border:1px solid #8c2828;" +
          "border-radius:3px;color:#e88;font-size:11px;font-family:monospace;";
        placeholder.textContent =
          "⚠ " + (comp.name || "comp#" + comp.id) +
          " (" + (comp.comp_type_code || "?") + ") — render failed: " +
          (err && err.message ? err.message : String(err));
        return placeholder;
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Krok 5.Z (30.5.2026) — Embedded grid_modern (306) uvnitr form
    // ════════════════════════════════════════════════════════════════
    // Marti's mandate: "Klasickou komponentu gridu 306 pro nase vseobecne
    // pouziti... Obdobnym zpusobem jako entity pickup." Render pattern analog
    // master-detail Volba A (data_source_op_detail.js, 24.5.2026): Promise.all
    // pre-fetch (data + saved layout) → new window.ErpDataGrid(host, {...}) s
    // initialLayout authority (uniform parity, pixel-perfect widths od prvniho
    // renderu, zadny container-fit override race).
    //
    // Layout JSONB (Volba A striktni deklarace):
    //   data_source_code — fw.data_source.code (napr. framework_comp_def_overview)
    //   filter_field     — SQL named param (napr. filter_core_id, NE column name!)
    //   filter_source    — runtime token (:master_id → this._spec.data.id)
    //   height_px        — vyska gridu (default 360)
    //   title            — section header label
    //   context_menu     — CRUD akce (gated na edit_core_id presence)
    //   edit_core_id     — fw.core pro edit/create form (optional, display-first
    //                      milestone bez nej → jen 'refresh')
    _renderEmbeddedGridSection(comp) {
      const layout = (comp && comp.layout) || {};
      const dataSourceCode = layout.data_source_code || comp.data_source_code || null;
      // title = plny fallback pro coreInfo.coreLabel (footer pill) — vzdy
      // neco smysluplneho, i kdyz user label nevyplnen.
      const title = layout.title || comp.caption || comp.data_source_name || dataSourceCode || "Grid";
      // Krok 5.Z (30.5.2026, Marti: "pokud neni vyplnen label gridu, nezobrazovat
      // jej, aby se grid posunul nahoru"): header sekce se renderuje JEN kdyz
      // user vyplnil vlastni label (layout.title / caption). Bez nej prazdny
      // titleUser -> _sectionBuild header preskoci. data_source_name/code/"Grid"
      // se NEbere jako viditelny label (je to jen fallback pro footer pill).
      const titleUser = (layout.title || comp.caption || "").trim();
      const sec = _sectionBuild(titleUser, "embedded:" + comp.id);

      if (!dataSourceCode) {
        console.warn("[DesignFwForm] embedded grid_modern #" + comp.id +
          " missing data_source_code (layout + FK both null) -> dummy grid");
        // Krok 5.Z (30.5.2026, Marti: "Zkusis osetrit vykresleni gridu i bez
        // datasourcu? Treba s Dummy selectem, ktery v gridu nahlasi co mu
        // schazi?"). Misto holeho cerveneho warningu vykreslime "dummy grid"
        // — fake hlavicka + skeleton radky (vypada jako grid) + overlay panel
        // s checklistem chybejici konfigurace + CTA "Nastavit grid" ->
        // _openGridSettings. "fw self edited" — uzivatel doplni data_source
        // pres UI bez SQL.
        const _ff = (comp.layout && comp.layout.filter_field) || null;
        const _fs = (comp.layout && comp.layout.filter_source) || null;
        const _filterPartial = (!!_ff) !== (!!_fs); // XOR = neuplny filtr

        const frame = document.createElement("div");
        frame.style.cssText =
          "grid-column:1 / -1;position:relative;border:1px dashed #3a4452;" +
          "border-radius:5px;background:#0f141a;overflow:hidden;min-height:200px;";

        // Fake grid hlavicka (4 placeholder sloupce)
        const fakeHdr = document.createElement("div");
        fakeHdr.style.cssText =
          "display:flex;border-bottom:1px solid #2a3340;background:#161c24;opacity:0.55;";
        for (let i = 0; i < 4; i++) {
          const th = document.createElement("div");
          th.style.cssText =
            "flex:1;padding:8px 10px;font-size:11px;color:#5d6975;" +
            "border-right:1px solid #222a33;text-transform:uppercase;letter-spacing:0.5px;";
          th.textContent = "Sloupec " + (i + 1);
          fakeHdr.appendChild(th);
        }
        frame.appendChild(fakeHdr);

        // Skeleton radky (3x mock, grey bars ruzne sirky)
        for (let r = 0; r < 3; r++) {
          const tr = document.createElement("div");
          tr.style.cssText = "display:flex;border-bottom:1px solid #1a212a;opacity:0.4;";
          for (let c = 0; c < 4; c++) {
            const td = document.createElement("div");
            td.style.cssText = "flex:1;padding:9px 10px;border-right:1px solid #1a212a;";
            const bar = document.createElement("div");
            bar.style.cssText =
              "height:8px;border-radius:3px;background:#2a3340;width:" +
              (45 + ((r * 13 + c * 21) % 45)) + "%;";
            td.appendChild(bar);
            tr.appendChild(td);
          }
          frame.appendChild(tr);
        }

        // Overlay panel — co gridu schazi + CTA na nastaveni
        const ovl = document.createElement("div");
        ovl.style.cssText =
          "position:absolute;inset:0;display:flex;align-items:center;" +
          "justify-content:center;background:rgba(15,20,26,0.78);";
        const panel = document.createElement("div");
        panel.style.cssText =
          "max-width:420px;text-align:center;padding:18px 22px;background:#1a2028;" +
          "border:1px solid #2a3340;border-radius:6px;box-shadow:0 4px 18px rgba(0,0,0,0.4);";

        const icon = document.createElement("div");
        icon.style.cssText = "font-size:26px;margin-bottom:6px;";
        icon.textContent = "⚙";
        panel.appendChild(icon);

        const head = document.createElement("div");
        head.style.cssText = "font-size:13px;font-weight:600;color:#cfd6df;margin-bottom:8px;";
        head.textContent = "Grid #" + comp.id + " není nakonfigurován";
        panel.appendChild(head);

        // Checklist co schazi
        const list = document.createElement("div");
        list.style.cssText =
          "text-align:left;display:inline-block;font-size:12px;color:#8a96a4;" +
          "line-height:1.7;margin-bottom:14px;";
        const _item = function (ok, label, hint) {
          const row = document.createElement("div");
          const mark = ok ? "✓" : "✗";
          const col = ok ? "#5fb37a" : "#e57373";
          const ms = document.createElement("span");
          ms.style.cssText = "color:" + col + ";font-weight:700;margin-right:7px;";
          ms.textContent = mark;
          row.appendChild(ms);
          const txt = document.createElement("span");
          txt.textContent = label + (hint ? " — " + hint : "");
          row.appendChild(txt);
          return row;
        };
        list.appendChild(_item(false, "Zdroj dat (data_source_code)", "chybí"));
        if (_filterPartial) {
          list.appendChild(_item(false, "Filtr", "neúplný (vyplň filter_field i filter_source)"));
        }
        panel.appendChild(list);

        const cta = document.createElement("button");
        cta.type = "button";
        cta.textContent = "⚙ Nastavit grid";
        cta.style.cssText =
          "padding:8px 18px;background:#2a6b3a;border:1px solid #3a8b4a;color:#e8f5e8;" +
          "border-radius:4px;cursor:pointer;font-size:13px;font-weight:600;";
        cta.addEventListener("click", () => {
          try { this._openGridSettings(comp); }
          catch (e) { console.error("[DesignFwForm] dummy grid CTA failed:", e); }
        });
        panel.appendChild(cta);

        ovl.appendChild(panel);
        frame.appendChild(ovl);
        sec.grid.appendChild(frame);
        return sec.wrap;
      }

      // ════════════════════════════════════════════════════════════════
      // Krok 5.Z (30.5.2026, Marti's "vyssi kontrola, bezpecneji"): filter
      // ENFORCED na render urovni. Dve doktriny:
      //
      //  1) filter_source je REDUNDANTNI — "to je stale stejne, jen
      //     s dvojteckou" (Marti). Derived = ':' + filter_field. Needuje se
      //     samostatny token, neukladame ho rucne. Edituje se JEN filter_field
      //     (parametr gridu).
      //
      //  2) select-detail VZDY filtruje per-master. Pokud filter_field chybi,
      //     ENFORCED default 'master_id' (konvence detail data_setu
      //     :master_id). Tim zadny select-detail grid nepropadne na tiche
      //     0 radku kvuli zapomenutemu filtru — kontrola je v kodu, ne
      //     v disciplineu uzivatele. (Marti-AI doctrine "bezpecnost pres
      //     probuzeni, ne pres ticho".)
      //
      // Value resolution dle field:
      //   self_core_id -> core k nemuz form patri (this._spec.core.id)
      //   master_id / cokoli jineho -> editovany master row PK (opts.rowId)
      // ════════════════════════════════════════════════════════════════
      const _kind = layout.kind || null;
      let filterField = layout.filter_field || null;
      if (!filterField && _kind === "select-detail") filterField = "master_id";
      // Derived source (legacy explicit layout.filter_source jen jako fallback
      // kdyby filter_field chybel u non-detail gridu).
      const filterSource = filterField ? (":" + filterField) : (layout.filter_source || null);
      let filterValue = null;
      if (filterField === "self_core_id" || filterSource === ":self_core_id") {
        // self-ref: CORE k nemuz form patri, bez ohledu na editovany row.
        filterValue = (this._spec && this._spec.core && this._spec.core.id != null)
          ? this._spec.core.id : null;
      } else if (filterField) {
        // master_id (a vsechno ostatni) -> PK editovaneho masteru. opts.rowId
        // reliable (URL /fw-form/by-id/{coreId}/{rowId}), fallback _spec.data.id.
        // CREATE (rowId=0/null) -> null -> guard nize ("Filtr nedostupny").
        const _editedId = (this.opts && this.opts.rowId != null && this.opts.rowId !== "")
          ? this.opts.rowId
          : ((this._spec && this._spec.data && this._spec.data.id != null)
              ? this._spec.data.id : null);
        filterValue = _editedId;
      }

      const heightPx = (typeof layout.height_px === "number" && layout.height_px > 0)
        ? layout.height_px : 360;
      const editCoreId = (layout.edit_core_id != null) ? layout.edit_core_id : null;

      // CRUD gating: create/edit potrebuji edit form core. Bez edit_core_id
      // jen 'refresh' (display-first milestone). Marti's "drz jednoduchost" —
      // display first, CRUD retrofit. Pri wired edit_core_id se akce z layout
      // context_menu automaticky aktivuji.
      let contextMenuActions = Array.isArray(layout.context_menu)
        ? layout.context_menu.slice() : ["refresh"];
      if (editCoreId == null) {
        contextMenuActions = contextMenuActions.filter(a => a === "refresh");
        if (contextMenuActions.length === 0) contextMenuActions = ["refresh"];
      }

      // Host div — block kontejner s definitivni vyskou (NE grid-item v sec.grid,
      // jinak .erp-ag-grid flex:1/height:100% nema vuci cemu resolvovat -> AG
      // Grid zkolabuje na 0px a nevidet hlavicku). Append do sec.wrap (block).
      //
      // Krok 5.Z align (Marti 30.5.: "ma i align alClient? aby se roztahl na
      // cely panel?"): layout.align='client' -> grid vyplni cely tab/panel
      // (flex:1, min-height:0 v flex-column kontejneru). Jinak fixni height_px.
      // Delphi alClient paralela — grid jako client-aligned komponenta.
      const align = String(layout.align || "none").toLowerCase();
      const isClient = (align === "client");
      const host = document.createElement("div");
      host.className = "erp-embedded-grid-host";
      if (isClient) {
        sec.wrap.style.flex = "1 1 auto";
        sec.wrap.style.display = "flex";
        sec.wrap.style.flexDirection = "column";
        sec.wrap.style.minHeight = "0";
        sec.wrap.style.marginBottom = "0";
        host.style.cssText = "width:100%;flex:1 1 auto;min-height:0;box-sizing:border-box;";
      } else {
        host.style.cssText = "width:100%;height:" + heightPx + "px;box-sizing:border-box;";
      }
      sec.wrap.appendChild(host);

      // Guard: filter required ale token se neresolvoval (CREATE mode data.id=null
      // pro :master_id, nebo chybejici core pro :self_core_id).
      if (filterField && filterSource && filterValue == null) {
        host.innerHTML = '<div style="padding:12px;color:#8a96a4;font-size:12px;">' +
          'ℹ Filtr nedostupný — záznam ještě nemá přiřazené ID.</div>';
        return sec.wrap;
      }

      if (typeof window.ErpDataGrid !== "function") {
        host.innerHTML = '<div style="padding:12px;color:#e57373;font-size:12px;">' +
          '⚠ ErpDataGrid komponenta není načtena (datagrid.js missing).</div>';
        return sec.wrap;
      }

      // Data fetch URL — master-detail konvence (Marti 30.5.): embedded grid
      // (detail) pouziva layout.kind='select-detail' + filter_field='master_id'
      // -> per-master data_set s simple "WHERE cd.core_id = :master_id".
      // layout.kind default null -> runner default 'select' (standalone list).
      // Filter param name z filter_field, hodnota z filter_source resolveru.
      let dataUrl = "/api/v1/erp/data/" + encodeURIComponent(dataSourceCode);
      const _qs = [];
      if (filterField && filterValue != null) {
        _qs.push(encodeURIComponent(filterField) + "=" + encodeURIComponent(filterValue));
      }
      if (_kind) _qs.push("kind=" + encodeURIComponent(_kind));
      if (_qs.length) dataUrl += "?" + _qs.join("&");
      // Krok 5.Z (Marti 30.5.): layoutKey MUSI byt 'core_<id>' nebo 'ds_<id>'
      // (datagrid.js _layoutApiBase + backend _parse_scope_key). Embedded grid
      // je bound na data_source -> ds_<comp.data_source_id> (konvence nested
      // gridu, data_source_op_detail.js pouziva ds_44). Vyzaduje comp_def.
      // data_source_id FK set (_phase_krok5z_set_grid_ds_fk.sql). Bez FK ->
      // layoutKey null -> grid bez ulozitelne sestavy (autoColumns), render OK.
      // FK set -> ds_<data_source_id> (separatni od standalone core_73, scope
      // na data_source). FK null -> fallback core_<form core id> (vzdy validni
      // format, toolbar sestav VZDY zobrazen). Bez fallbacku by layoutKey=null
      // -> ErpDataGrid skryje cely layout toolbar (Marti's "zmizelo ukladani
      // sestav z paticky"). Doporuceno spustit _phase_krok5z_set_grid_ds_fk.sql
      // pro stabilni ds_<id> klic.
      const _dsId = (comp && comp.data_source_id != null) ? comp.data_source_id : null;
      const _coreId = (this._spec && this._spec.core && this._spec.core.id != null)
        ? this._spec.core.id : "0";
      const layoutKey = (_dsId != null) ? ("ds_" + _dsId) : ("core_" + _coreId);
      const layoutUrl = "/api/v1/erp/grid-layout/" + encodeURIComponent(layoutKey) + "/list";

      let gridInst = null;
      const _fetchData = function () {
        return fetch(dataUrl, { credentials: "same-origin" })
          .then(function (r) { return r.json(); });
      };

      Promise.all([
        _fetchData(),
        layoutUrl
          ? fetch(layoutUrl, { credentials: "same-origin" })
              .then(function (r) { return r.json(); })
              .catch(function () { return null; })
          : Promise.resolve(null),
      ]).then(function (results) {
        const dataJson = results[0];
        const layoutList = results[1];
        const rows = (dataJson && dataJson.ok && Array.isArray(dataJson.rows)) ? dataJson.rows : [];
        const initialLayout = (layoutList && layoutList.ok && layoutList.effective_default)
          ? layoutList.effective_default : null;
        try {
          gridInst = new window.ErpDataGrid(host, {
            rowData: rows,
            // alClient -> null (host je flex:1, ErpDataGrid neset fixni height
            // -> .erp-ag-grid height:100%/flex:1 vyplni flex parenta). Jinak px.
            height: isClient ? null : (heightPx + "px"),
            layoutKey: layoutKey,
            initialLayout: initialLayout,
            autoColumns: true,
            enableFilters: true,
            rowSelection: "single",
            compact: true,
            disableColumnFlex: true,
            coreInfo: {
              coreId: editCoreId,
              refId: filterValue,
              coreLabel: title,
            },
            gridActions: {
              has_insert: false,
              has_edit: false,
              has_delete: false,
              edit_core_id: editCoreId,
            },
            contextMenuActions: contextMenuActions,
            onRefresh: function () {
              return _fetchData().then(function (j) {
                if (j && j.ok && Array.isArray(j.rows) && gridInst && gridInst.gridApi) {
                  gridInst.gridApi.setGridOption("rowData", j.rows);
                  try {
                    if (typeof gridInst.markFresh === "function") gridInst.markFresh();
                  } catch (_e) { /* fail-safe */ }
                }
              }).catch(function (e) {
                console.warn("[embedded_grid onRefresh] #" + comp.id, e);
              });
            },
          });
        } catch (e) {
          console.error("[DesignFwForm] embedded grid #" + comp.id + " init failed:", e);
          host.innerHTML = '<div style="padding:12px;color:#e57373;font-size:12px;">' +
            'Chyba inicializace gridu: ' + (e && e.message ? e.message : String(e)) + '</div>';
        }
      }).catch(function (e) {
        console.error("[DesignFwForm] embedded grid #" + comp.id + " fetch failed:", e);
        host.innerHTML = '<div style="padding:12px;color:#e57373;font-size:12px;">' +
          'Chyba načtení dat: ' + (e && e.message ? e.message : String(e)) + '</div>';
      });

      return sec.wrap;
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-D (14.5.2026 vecer, Marti's "moznost zakladni
    // parametrizace techto panelu"): right-click → settings popup.
    //
    // Editable fields:
    //   - caption (label panelu, empty = invisible)
    //   - layout.align (left/right/top/bottom/client/none dropdown)
    //   - layout.width (pixels | 'auto' — pro left/right)
    //   - layout.height (pixels | 'auto' — pro top/bottom)
    //   - layout.min_width (pixels — responsive constraint)
    //   - layout.min_height (pixels)
    //   - layout.border_mode (none/top/all — relevantni pro groupbox)
    //
    // PATCH /api/v1/erp/design/comp-def/update/{id} s caption + layout
    // (merge s existing keys). After save → _reloadSpec + re-render.
    // ════════════════════════════════════════════════════════════════
    _openContainerSettings(container) {
      const isPanel = container.comp_type_code === "panel";
      const isGroupbox = container.comp_type_code === "groupbox";
      const typeLabel = isPanel ? "Panel" : (isGroupbox ? "Groupbox" : "Container");
      const currentLayout = container.layout || {};

      // Build modal overlay (analog _confirmDarkDialog ale s form)
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:420px;max-width:520px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = (isPanel ? "📦" : "▦") + " Nastavení: " + typeLabel +
                        " <span style=\"color:#5d6975;font-weight:400;font-size:11px;\">#" + container.id + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Form body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      // Helper: build labeled input row
      const _row = (labelText, inputEl) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const lbl = document.createElement("label");
        lbl.textContent = labelText;
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        wrap.appendChild(lbl);
        wrap.appendChild(inputEl);
        return wrap;
      };
      const _inputStyle =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
        "box-sizing:border-box;";

      // caption
      const captionInput = document.createElement("input");
      captionInput.type = "text";
      captionInput.style.cssText = _inputStyle;
      captionInput.value = container.caption || "";
      captionInput.placeholder = "(empty = invisible label)";
      body.appendChild(_row("Caption", captionInput));

      // layout.align — Krok 5-B (29.5.2026 rano, Marti's "v parametrech
      // panelu musim VZDY videt align"): drop isPanel gate, show align
      // selector for ALL containers (panel/groupbox/tabsheet/pagecontrol).
      // Pro groupbox/tabsheet/pagecontrol je 'client' typicky correct
      // default — ale Marti chce moznost zmenit. Drz "uniformita vítězí
      // nad speciálními případy" (Krok 13 doctrine).
      //
      // Defensive: pokud container.comp_type_code chybi (občas backend
      // nepošle), drive zobrazil select jen kdyz isPanel. Po H+5 refactoru
      // backend vraci type_code spolehlive, ale show always = safe.
      let alignSelect = document.createElement("select");
      alignSelect.style.cssText = _inputStyle;
      const aligns = [
        ["client", "alClient — fill remaining (default)"],
        ["top", "alTop — full width strip nahore"],
        ["bottom", "alBottom — full width strip dole"],
        ["left", "alLeft — vertical strip vlevo"],
        ["right", "alRight — vertical strip vpravo"],
        ["none", "alNone — absolute (top/left/width/height)"],
      ];
      for (const [val, label] of aligns) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if ((currentLayout.align || "client") === val) opt.selected = true;
        alignSelect.appendChild(opt);
      }
      body.appendChild(_row("Align", alignSelect));

      // layout.width (pro left/right panely)
      const widthInput = document.createElement("input");
      widthInput.type = "text";
      widthInput.style.cssText = _inputStyle;
      widthInput.value = currentLayout.width != null ? String(currentLayout.width) : "";
      widthInput.placeholder = "px (např. 200) | '30%' | 'auto'";
      body.appendChild(_row("Width", widthInput));

      // layout.height (pro top/bottom panely)
      const heightInput = document.createElement("input");
      heightInput.type = "text";
      heightInput.style.cssText = _inputStyle;
      heightInput.value = currentLayout.height != null ? String(currentLayout.height) : "";
      heightInput.placeholder = "px (např. 60) | 'auto'";
      body.appendChild(_row("Height", heightInput));

      // layout.min_width
      const minWidthInput = document.createElement("input");
      minWidthInput.type = "number";
      minWidthInput.style.cssText = _inputStyle;
      minWidthInput.value = currentLayout.min_width != null ? String(currentLayout.min_width) : "";
      minWidthInput.placeholder = "px (responsive constraint)";
      body.appendChild(_row("Min width", minWidthInput));

      // layout.min_height
      const minHeightInput = document.createElement("input");
      minHeightInput.type = "number";
      minHeightInput.style.cssText = _inputStyle;
      minHeightInput.value = currentLayout.min_height != null ? String(currentLayout.min_height) : "";
      minHeightInput.placeholder = "px";
      body.appendChild(_row("Min height", minHeightInput));

      // layout.border_mode (relevant pro groupbox primarne)
      // Fix #8 (29.5.2026 pozde, Marti's "Mod All prepiseme na Top-Right"):
      // label změnen z "All — full rámeček" na "Top-Right — linka
      // nahore a vpravo". Enum value "all" zachován pro DB kompatibilitu.
      const borderSelect = document.createElement("select");
      borderSelect.style.cssText = _inputStyle;
      const borderModes = [
        ["none", "Žádný (default pro panel)"],
        ["top", "Top — linka nahore"],
        ["all", "Top-Right — linka nahore a vpravo"],
      ];
      const currentBorder = currentLayout.border_mode || (isGroupbox ? "top" : "none");
      for (const [val, label] of borderModes) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if (currentBorder === val) opt.selected = true;
        borderSelect.appendChild(opt);
      }
      body.appendChild(_row("Border mode", borderSelect));

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Phase 38.4 Krok 14f-H (14.5.2026 vecer, Marti's "tlacitko odebrat
      // aby sel panel odebrat z formu"): Delete button vlevo (destructive
      // action separated). Confirm dialog s warning pokud panel ma child
      // comp_defs (groupbox + fields).
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat';
      deleteBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;" +
        "margin-right:auto;";  // push to left
      deleteBtn.title = "Smazat tento " + typeLabel.toLowerCase() + " z formuláře";
      deleteBtn.addEventListener("mouseenter", () => {
        deleteBtn.style.background = "#1f1010";
        deleteBtn.style.borderColor = "#7a3838";
      });
      deleteBtn.addEventListener("mouseleave", () => {
        deleteBtn.style.background = "transparent";
        deleteBtn.style.borderColor = "#5a2828";
      });
      deleteBtn.addEventListener("click", async () => {
        // Detect children — warning pokud nejsou empty
        const ctx = this.__renderCtx || {};
        const byParent = ctx.byParent || new Map();
        const childCount = (byParent.get(container.id) || []).length;
        const childWarn = childCount > 0
          ? "\n\n⚠ Tento " + typeLabel.toLowerCase() + " obsahuje " + childCount +
            " vnitřních komponent (groupbox/fields). Ty zůstanou v DB, ale ztratí parent — doporučení: nejdřív přesun nebo smaž jejich obsah."
          : "";
        const decision = await _confirmDarkDialog({
          title: "Smazat " + typeLabel.toLowerCase(),
          message: "Opravdu smazat " + typeLabel.toLowerCase() + " '" +
                   (container.caption || container.name) + "' (#" + container.id + ")?" +
                   childWarn + "\n\n(soft-delete — záznam v audit historii zustava)",
        });
        if (decision !== true) return;
        // DELETE /design/comp-def/{id}
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/" + encodeURIComponent(container.id),
            { method: "DELETE", credentials: "include" }
          );
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast(typeLabel + " '" + (container.caption || container.name) + "' smazán", "success", 2200);
          document.body.removeChild(overlay);
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] container delete failed:", e);
          _showToast("Mazání selhalo: " + (e.message || e), "error", 3500);
        }
      });
      footer.appendChild(deleteBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        saveBtn.style.opacity = "0.6";
        try {
          // Build new layout (merge with existing)
          const newLayout = Object.assign({}, currentLayout);
          // Krok 5-B (29.5.2026): alignSelect je always defined, drop nil check
          newLayout.align = alignSelect.value;

          // Parse width/height — pokud cislo, ulozit jako int; pokud string s '%' nebo 'auto', ulozit string
          const _parseSize = (v) => {
            const s = String(v || "").trim();
            if (s === "") return null;
            if (s === "auto") return "auto";
            if (/%$/.test(s)) return s;
            const n = parseInt(s, 10);
            return isNaN(n) ? null : n;
          };
          const newWidth = _parseSize(widthInput.value);
          const newHeight = _parseSize(heightInput.value);
          if (newWidth == null) delete newLayout.width; else newLayout.width = newWidth;
          if (newHeight == null) delete newLayout.height; else newLayout.height = newHeight;

          const newMinW = minWidthInput.value.trim() ? parseInt(minWidthInput.value, 10) : null;
          const newMinH = minHeightInput.value.trim() ? parseInt(minHeightInput.value, 10) : null;
          if (newMinW == null || isNaN(newMinW)) delete newLayout.min_width; else newLayout.min_width = newMinW;
          if (newMinH == null || isNaN(newMinH)) delete newLayout.min_height; else newLayout.min_height = newMinH;

          newLayout.border_mode = borderSelect.value;

          const newCaption = captionInput.value.trim();

          // PATCH /design/comp-def/update/{id}
          const pr = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(container.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify({
                caption: newCaption,
                layout: newLayout,
              }),
            }
          );
          if (!pr.ok) {
            const errBody = await pr.json().catch(() => ({}));
            throw new Error("HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
          }
          _showToast(typeLabel + " nastaveni ulozeno", "success", 2000);
          document.body.removeChild(overlay);
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] _openContainerSettings save failed:", e);
          _showToast("Ulozeni selhalo: " + (e.message || e), "error", 3500);
          saveBtn.disabled = false;
          saveBtn.style.opacity = "1";
        }
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Esc to close
      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          document.body.removeChild(overlay);
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);

      // Focus first input
      setTimeout(() => captionInput.focus(), 50);
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "U tech komponent
    // potrebujeme editovat nejlepe dva parametry... Maximal lenght a
    // Minimal lenght"): per-field settings modal.
    //
    // Editable fields (uloziste = comp_def.caption + comp_def.layout JSONB):
    //   - caption (input text)
    //   - layout.max_length (input number, optional)
    //   - layout.min_length (input number, optional)
    //   - layout.readonly (checkbox)
    //   - layout.required (checkbox)
    //   - layout.placeholder (input text)
    //
    // PATCH /api/v1/erp/design/comp-def/update/{id} s caption + layout
    // (merge with existing). After save → _reloadSpec + re-render.
    // Re-render automaticky pouzije nove layout.max_length pres _renderField.
    // ════════════════════════════════════════════════════════════════
    // ════════════════════════════════════════════════════════════════
    // Krok 5.Z (30.5.2026) — Grid settings popup (grid_modern params)
    // ════════════════════════════════════════════════════════════════
    // Marti's "nastaveni parametru gridu jako u ostatnich komponent" +
    // "ma i align alClient? aby se roztahl na cely panel?". Edituje
    // comp_def.layout JSONB (title/align/height_px/data_source_code/
    // filter_field/filter_source/kind/context_menu), PATCH /comp-def/update.
    // "fw self edited" — grid konfigurovatelny z UI bez SQL.
    _openGridSettings(comp) {
      const layout = Object.assign({}, comp.layout || {});

      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";
      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:460px;max-width:560px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const titleEl = document.createElement("div");
      titleEl.style.cssText = "font-weight:600;font-size:14px;";
      titleEl.innerHTML = "⚙ Nastavení gridu <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">grid_modern · #" + comp.id + "</span>";
      header.appendChild(titleEl);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button"; closeBtn.textContent = "✕";
      closeBtn.style.cssText = "background:transparent;border:none;color:#8a96a4;font-size:18px;cursor:pointer;padding:0;line-height:1;";
      const _close = () => { if (overlay.parentNode) document.body.removeChild(overlay); };
      closeBtn.addEventListener("click", _close);
      header.appendChild(closeBtn);
      modal.appendChild(header);

      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;max-height:70vh;overflow:auto;";
      const _is = "padding:6px 8px;background:#0f1419;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;";
      const _mkRow = (labelText, inputEl, hint) => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex;flex-direction:column;gap:3px;";
        const lab = document.createElement("label");
        lab.textContent = labelText;
        lab.style.cssText = "font-size:11px;color:#8a96a4;font-weight:600;";
        row.appendChild(lab); row.appendChild(inputEl);
        if (hint) {
          const h = document.createElement("div");
          h.textContent = hint;
          h.style.cssText = "font-size:10px;color:#5d6975;";
          row.appendChild(h);
        }
        return row;
      };
      const _mkSelect = (pairs, cur) => {
        const sel = document.createElement("select");
        sel.style.cssText = _is;
        for (const [v, t] of pairs) {
          const o = document.createElement("option");
          o.value = v; o.textContent = t;
          if (String(cur || "") === v) o.selected = true;
          sel.appendChild(o);
        }
        return sel;
      };

      const inTitle = document.createElement("input");
      inTitle.type = "text"; inTitle.value = layout.title || ""; inTitle.style.cssText = _is;
      body.appendChild(_mkRow("Titulek", inTitle));

      const selAlign = _mkSelect([
        ["none", "none (fixní výška)"], ["client", "client (vyplní celý panel)"],
        ["top", "top"], ["bottom", "bottom"], ["left", "left"], ["right", "right"],
      ], (layout.align || "none").toLowerCase());
      body.appendChild(_mkRow("Zarovnání (align)", selAlign, "client = grid se roztáhne na celý tab/panel"));

      const inHeight = document.createElement("input");
      inHeight.type = "number"; inHeight.value = (layout.height_px != null ? layout.height_px : 400); inHeight.style.cssText = _is;
      body.appendChild(_mkRow("Výška (px)", inHeight, "použije se když align != client"));

      // Krok 5.Z (30.5.2026, Marti: "v prvni rade by se nemelo vybirat
      // datasource code, ale Datasource ID"): picker podle ID misto free-text
      // code. ErpCatalogPicker -> /design/fw-data-source/list (mirror
      // entity_picker pattern). Pri ulozeni PATCH data_source_id (FK) ->
      // stabilni ds_<id> layoutKey (ukladani sestav sloupcu funguje bez
      // _set_grid_ds_fk.sql) + layout.data_source_code odvozeny z vybraneho
      // code (pro /data/{code} URL). kind auto-fill z operation_kinds.
      // "fw self edited" — zadny rucni code, vyber vizualne. DataSource + op +
      // dataset se stavi ve svych designerech (System tree), grid jen referuje.
      let dsState = (comp.data_source_id != null)
        ? { id: comp.data_source_id, code: layout.data_source_code || comp.data_source_code || null, name: comp.data_source_name || null }
        : (layout.data_source_code ? { id: null, code: layout.data_source_code, name: null } : null);
      const dsDisplay = document.createElement("input");
      dsDisplay.type = "text"; dsDisplay.readOnly = true;
      dsDisplay.style.cssText = _is + "flex:1;background:#0f1419;color:#cfd6df;cursor:default;";
      const _refreshDsDisplay = () => {
        if (dsState && (dsState.id != null || dsState.code)) {
          dsDisplay.value = (dsState.id != null ? "#" + dsState.id + " · " : "") +
            (dsState.name || dsState.code || "(?)");
        } else {
          dsDisplay.value = "(žádný — klikni 🔗)";
        }
      };
      _refreshDsDisplay();
      const dsPickBtn = document.createElement("button");
      dsPickBtn.type = "button"; dsPickBtn.textContent = "🔗"; dsPickBtn.title = "Vybrat data source";
      dsPickBtn.style.cssText =
        "padding:6px 10px;background:#1a1f26;border:1px solid #2a3340;" +
        "color:#8fb8d4;border-radius:3px;cursor:pointer;font-size:14px;flex:0 0 auto;";
      dsPickBtn.addEventListener("click", () => {
        if (typeof window.ErpCatalogPicker !== "function") {
          if (typeof _showToast === "function") _showToast("ErpCatalogPicker není načtený", "error", 3000);
          return;
        }
        const _p = new window.ErpCatalogPicker({
          title: "🔗 Vybrat data source pro grid",
          endpoint: "/api/v1/erp/design/fw-data-source/list?status=active&limit=500",
          listKey: "data_sources",
          coreId: 19,  // framework_data_sources core (mirror entity_picker)
          idField: "id", labelField: "name", width: "920px",
          initialSelectedId: (dsState && dsState.id != null) ? dsState.id : null,
          columns: [
            { headerName: "ID", field: "id", width: 80, type: "numericColumn" },
            { headerName: "Code", field: "code", width: 280 },
            { headerName: "Název", field: "name", flex: 1, minWidth: 200 },
            { headerName: "Operace", field: "operation_kinds", width: 160 },
          ],
          onSelect: (row) => {
            dsState = { id: row.id, code: row.code || null, name: row.name || null };
            _refreshDsDisplay();
            // auto-fill kind z operation_kinds (select-detail > select).
            // Pri select-detail predvyplnit i filter_field=master_id (jen kdyz
            // prazdny — neprepisovat user override). filter_source derived pri save.
            const oks = String(row.operation_kinds || "");
            if (oks.indexOf("select-detail") !== -1) {
              selKind.value = "select-detail";
              if (!inFf.value.trim()) inFf.value = "master_id";
            } else if (oks.indexOf("select") !== -1) {
              selKind.value = "select";
            }
          },
        });
        _p.open();
      });
      const dsClearBtn = document.createElement("button");
      dsClearBtn.type = "button"; dsClearBtn.textContent = "🚫"; dsClearBtn.title = "Zrušit binding";
      dsClearBtn.style.cssText =
        "padding:6px 10px;background:#1a1f26;border:1px solid #2a3340;" +
        "color:#d48787;border-radius:3px;cursor:pointer;font-size:14px;flex:0 0 auto;";
      dsClearBtn.addEventListener("click", () => { dsState = null; _refreshDsDisplay(); });
      const dsWrap = document.createElement("div");
      dsWrap.style.cssText = "display:flex;gap:6px;align-items:center;";
      dsWrap.appendChild(dsPickBtn); dsWrap.appendChild(dsClearBtn); dsWrap.appendChild(dsDisplay);
      body.appendChild(_mkRow("Data source", dsWrap, "vyber z fw.data_source podle ID (ne ručně code)"));

      // Krok 5.Z (30.5.2026, Marti: "filter_source ani neresit — je to stale
      // stejne, jen s dvojteckou"): edituje se JEN filter_field. filter_source
      // se odvodi (':' + filter_field) pri ulozeni — zadny samostatny dropdown.
      // select-detail prefill 'master_id' (konvence detail data_setu).
      const inFf = document.createElement("input");
      inFf.type = "text";
      inFf.value = layout.filter_field ||
        (String(layout.kind || "") === "select-detail" ? "master_id" : "");
      inFf.style.cssText = _is;
      body.appendChild(_mkRow("Filtr — sloupec (SQL param)", inFf,
        "select-detail → master_id (zdroj se odvodí jako :master_id)"));

      const selKind = _mkSelect([
        ["", "(default select)"], ["select", "select"], ["select-detail", "select-detail"],
      ], layout.kind || "");
      body.appendChild(_mkRow("Operace (kind)", selKind, "select-detail = per-master detail data_set"));

      const inCm = document.createElement("input");
      inCm.type = "text";
      inCm.value = Array.isArray(layout.context_menu) ? layout.context_menu.join(",") : (layout.context_menu || "refresh");
      inCm.style.cssText = _is;
      body.appendChild(_mkRow("Kontext menu", inCm, "čárkami: refresh,create,edit,delete"));

      modal.appendChild(body);

      const footer = document.createElement("div");
      footer.style.cssText = "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;display:flex;justify-content:flex-end;gap:8px;";
      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button"; cancelBtn.textContent = "Zrušit";
      cancelBtn.style.cssText = "padding:7px 16px;background:transparent;border:1px solid #2a3340;color:#8a96a4;border-radius:4px;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", _close);
      const saveBtn = document.createElement("button");
      saveBtn.type = "button"; saveBtn.textContent = "💾 Uložit";
      saveBtn.style.cssText = "padding:7px 16px;background:#2a6b3a;border:1px solid #3a8b4a;color:#e8f5e8;border-radius:4px;cursor:pointer;font-size:13px;font-weight:600;";
      footer.appendChild(cancelBtn); footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      overlay.addEventListener("click", (e) => { if (e.target === overlay) _close(); });
      document.body.appendChild(overlay);

      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        const newLayout = Object.assign({}, layout);
        newLayout.title = inTitle.value.trim() || null;
        newLayout.align = selAlign.value;
        const hp = parseInt(inHeight.value, 10);
        newLayout.height_px = (!isNaN(hp) && hp > 0) ? hp : 400;
        newLayout.data_source_code = (dsState && dsState.code) ? dsState.code : null;
        // filter_source derived z filter_field (Marti: "jen s dvojteckou").
        newLayout.filter_field = inFf.value.trim() || null;
        if (newLayout.filter_field) newLayout.filter_source = ":" + newLayout.filter_field;
        else delete newLayout.filter_source;
        if (selKind.value) newLayout.kind = selKind.value; else delete newLayout.kind;
        const cm = inCm.value.split(",").map(s => s.trim()).filter(Boolean);
        newLayout.context_menu = cm.length ? cm : ["refresh"];
        try {
          const r = await fetch("/api/v1/erp/design/comp-def/update/" + comp.id, {
            method: "PATCH", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              layout: newLayout,
              // Krok 5.Z (30.5.2026, Marti: "kdyz label smazu, zustane stary
              // text"): caption kopiruje Titulek PRESNE (empty string, NE null
              // — backend vyzaduje string, "" = invisible label doctrine
              // Krok 14f-D). Smazani Titulku -> caption="" + layout.title=null
              // -> titleUser prazdny -> header skryty.
              caption: inTitle.value.trim(),
              // Krok 5.Z: FK na fw.data_source -> stabilni ds_<id> layoutKey.
              data_source_id: (dsState && dsState.id != null) ? dsState.id : null,
            }),
          });
          const d = await r.json().catch(() => ({}));
          if (!r.ok || !d.ok) throw new Error(d.error || ("HTTP " + r.status));
          if (typeof _showToast === "function") _showToast("Grid nastaven", "success", 2000);
          _close();
          if (typeof this._reloadSpec === "function") await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] _openGridSettings save failed:", e);
          if (typeof _showToast === "function") _showToast("Uložení selhalo: " + (e.message || e), "error", 3500);
          saveBtn.disabled = false;
        }
      });
    }

    _openFieldSettings(field, opts) {
      // Krok 5.Z (30.5.2026): grid_modern ma vlastni settings popup (data_source,
      // filter, kind, align, height) misto field caption/label/placeholder.
      if (field && field.comp_type_code === "grid_modern") {
        return this._openGridSettings(field);
      }
      const currentLayout = field.layout || {};

      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:440px;max-width:540px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = "⚙ Nastavení komponenty <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">" +
                        (field.comp_type_code || "field") + " · #" + field.id + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Phase 38.4 Krok H+13 (27.5.2026 ráno, Marti's "sloučit ty parametry
      // komponent do dvou listu"): UNIFIED 2-tab modal pro VŠECHNY komponenty.
      //   Tab 1 "Uživatel"   = Label / Hint / Color override (localStorage)
      //   Tab 2 "Komponenta" = Caption / Placeholder / widths / lengths /
      //                        readonly / required + entity_picker subsekce
      //                        + enum_values editor (PATCH /comp-def/update)
      // opts.defaultTab = "user" | "component" (default "component").
      // Pravý klik na label → "user", pravý klik na wrap nebo ⚙ → "component".
      const _defaultTab = (opts && opts.defaultTab === "user") ? "user" : "component";

      const isEntityPicker = (field.comp_type_code === "entity_picker");
      // Krok 5-B (29.5.2026, Marti's "sjednotit ty dva ruzna okna parametru"):
      // detekce containers (panel/groupbox/tabsheet/pagecontrol). Pokud
      // isContainer → render container-specific sekci (Align/Max width/Height/
      // Min height/Border mode) misto field-specific (Placeholder/Length/
      // Readonly/Required). Caption + Min width sdileno (vzdy renderovano).
      // Width drop — Marti's Bod 1 "Width jako Max width (omezit aby se nam
      // nerozthoval pres celou obrazovku)" → containery pouzivaji jen
      // Max width (legacy layout.width → mapped na max_width pri load).
      const isContainer = (
        field.comp_type_code === "panel" ||
        field.comp_type_code === "groupbox" ||
        field.comp_type_code === "tabsheet" ||
        field.comp_type_code === "pagecontrol"
      );
      // Phase 38.4 Krok H+6 (26.5.2026, Marti's "Combobox: jak editovat
      // list, kdyz potrebuju pridat neco co jeste v DB neni"):
      // ComboBox/lookup editor pro layout.enum_values — manual add/edit/
      // remove + "Doplnit z DB" button. Persistent v fw.comp_def.layout.
      const isLookupField = (
        field.comp_type_code === "lookup" ||
        field.comp_type_code === "combobox" ||
        field.comp_type_code === "dropdown"
      );
      let enumValuesList = null;  // mutable array for the editor
      let enumValuesListEl = null;  // DOM ref pro re-render
      let _renderEnumListFn = null;  // assigned inside isLookupField block
      let basicPaneEl = null;
      let userPaneEl = null;

      // Krok H+13: build fieldKey pro user overrides (same pattern jako
      // _renderField line 7172): core.code + "." + field.name. Resolves
      // user-defined label/hint/color z localStorage _USER_OVERRIDES.
      const _coreCode = (this._spec && this._spec.core && this._spec.core.code) || "fw_form";
      const _fieldKey = _coreCode + "." + (field.name || ("field_" + field.id));

      // Krok H+13 dirty tracking — split per tab pro single Save split flow.
      let _userDirty = false;
      let _componentDirty = false;
      const _markComponentDirty = () => { _componentDirty = true; };

      // Body
      const body = document.createElement("div");
      body.style.cssText = "padding:0;display:flex;flex-direction:column;";

      // Krok H+13: UNCONDITIONAL 2-tab bar (Uživatel + Komponenta).
      const tabBar = document.createElement("div");
      tabBar.style.cssText =
        "display:flex;border-bottom:1px solid #2a3340;background:#0f141a;" +
        "padding:0 16px;gap:0;";

      const _mkTab = (label, isActive) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = label;
        btn.style.cssText =
          "padding:10px 18px;background:transparent;border:none;" +
          "border-bottom:2px solid " + (isActive ? "#7ed4e8" : "transparent") + ";" +
          "color:" + (isActive ? "#e8eef5" : "#8a96a4") + ";" +
          "font-size:13px;font-weight:" + (isActive ? "600" : "400") + ";" +
          "cursor:pointer;outline:none;";
        return btn;
      };

      const userTabBtn = _mkTab("Uživatel", _defaultTab === "user");
      const componentTabBtn = _mkTab("Komponenta", _defaultTab !== "user");
      tabBar.appendChild(userTabBtn);
      tabBar.appendChild(componentTabBtn);
      body.appendChild(tabBar);

      // Inner content wrapper (padding inside)
      const bodyInner = document.createElement("div");
      bodyInner.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      // Tab 1 "Uživatel" pane — label/hint/color (localStorage overrides)
      userPaneEl = document.createElement("div");
      userPaneEl.style.cssText =
        (_defaultTab === "user" ? "display:flex;" : "display:none;") +
        "flex-direction:column;gap:12px;";
      bodyInner.appendChild(userPaneEl);

      // Tab 2 "Komponenta" pane (existing basicPaneEl — keep name for inline appendChild refs below)
      basicPaneEl = document.createElement("div");
      basicPaneEl.style.cssText =
        (_defaultTab === "user" ? "display:none;" : "display:flex;") +
        "flex-direction:column;gap:10px;";
      bodyInner.appendChild(basicPaneEl);

      // Wire tab switching
      const _switchTab = (toUser) => {
        userPaneEl.style.display = toUser ? "flex" : "none";
        basicPaneEl.style.display = toUser ? "none" : "flex";
        userTabBtn.style.borderBottomColor = toUser ? "#7ed4e8" : "transparent";
        userTabBtn.style.color = toUser ? "#e8eef5" : "#8a96a4";
        userTabBtn.style.fontWeight = toUser ? "600" : "400";
        componentTabBtn.style.borderBottomColor = toUser ? "transparent" : "#7ed4e8";
        componentTabBtn.style.color = toUser ? "#8a96a4" : "#e8eef5";
        componentTabBtn.style.fontWeight = toUser ? "400" : "600";
      };
      userTabBtn.addEventListener("click", () => _switchTab(true));
      componentTabBtn.addEventListener("click", () => _switchTab(false));

      // ════════════════════════════════════════════════════════════════
      // Tab 1 "Uživatel" content — port z _openFieldSettingsPopup
      // (design_form_helpers.js:1827). 3 fields + "Vrátit na výchozí":
      //   1. Uživatelský název (label override)
      //   2. Hint (popis při hover > 1s)
      //   3. Barva pole (color swatches)
      // Save → _saveUserOverride("labels"/"hints"/"colors", _fieldKey, val)
      //       + _reapplyOverridesInDOM(_fieldKey) (immediate DOM apply).
      // ════════════════════════════════════════════════════════════════
      const _currentUserLabel = (LABEL_OVERRIDES[_fieldKey] || "");
      const _currentUserHint = (HINT_OVERRIDES[_fieldKey] || "");
      const _currentUserHex = _resolveColor(_fieldKey);
      const _currentUserColorId = _currentUserHex
        ? (DESIGN_FIELD_PALETTE.find(c => c.hex === _currentUserHex) || {}).id || null
        : null;
      // Read raw _USER_OVERRIDES via _resolveLabel/_resolveHint chain:
      // tyto helpery vrací user override (priorita 1) nebo LABEL_OVERRIDES
      // (priorita 2). Pro initial popup hodnotu chceme RAW user override
      // (žádný fallback) — pokud user nemá vlastní, input je prázdný.
      // _resolveLabel(_fieldKey, "") s prazdnym fallbackem vrátí user override
      // nebo "" (system label by se vrátil jen pokud byl v LABEL_OVERRIDES).
      const _rawUserLabel = _resolveLabel(_fieldKey, "");
      const _rawUserHint = _resolveHint(_fieldKey) || "";

      // 1. Label override input
      const userLabelWrap = document.createElement("div");
      userLabelWrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
      const userLabelLbl = document.createElement("label");
      userLabelLbl.textContent = "Uživatelský název (zobrazí se místo systémového)";
      userLabelLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      userLabelWrap.appendChild(userLabelLbl);
      const userLabelInp = document.createElement("input");
      userLabelInp.type = "text";
      userLabelInp.value = _rawUserLabel;
      userLabelInp.placeholder = "(nechej prázdné pro výchozí — '" + (field.caption || field.name || "") + "')";
      userLabelInp.style.cssText =
        "padding:6px 8px;background:#0f141a;border:1px solid #2a3340;" +
        "border-radius:3px;color:#cfd6df;font-size:13px;";
      userLabelInp.addEventListener("input", () => { _userDirty = true; });
      userLabelWrap.appendChild(userLabelInp);
      userPaneEl.appendChild(userLabelWrap);

      // 2. Hint textarea
      const userHintWrap = document.createElement("div");
      userHintWrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
      const userHintLbl = document.createElement("label");
      userHintLbl.textContent = "Hint (popis při hover > 1s)";
      userHintLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      userHintWrap.appendChild(userHintLbl);
      const userHintArea = document.createElement("textarea");
      userHintArea.value = _rawUserHint;
      userHintArea.placeholder = "(nechej prázdné pro žádný hint)";
      userHintArea.rows = 4;
      userHintArea.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "border-radius:3px;color:#cfd6df;font-size:12px;font-family:inherit;" +
        "resize:vertical;line-height:1.5;";
      userHintArea.addEventListener("input", () => { _userDirty = true; });
      userHintWrap.appendChild(userHintArea);
      userPaneEl.appendChild(userHintWrap);

      // 3. Barva pole swatches
      const userColorWrap = document.createElement("div");
      userColorWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
      const userColorLbl = document.createElement("label");
      userColorLbl.textContent = "Barva pole (organizační — barva textu fieldu)";
      userColorLbl.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
      userColorWrap.appendChild(userColorLbl);
      const userSwatches = document.createElement("div");
      userSwatches.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;align-items:center;";
      let _selectedUserColorId = _currentUserColorId;
      const _renderUserSwatches = () => {
        userSwatches.innerHTML = "";
        DESIGN_FIELD_PALETTE.forEach((c) => {
          const sw = document.createElement("button");
          sw.type = "button";
          sw.title = c.name;
          sw.dataset.colorId = c.id || "";
          const isSelected = (c.id || null) === (_selectedUserColorId || null);
          const isClear = (c.id === null || c.id === undefined);
          if (isClear) {
            sw.textContent = "✕";
            sw.style.cssText =
              "width:28px;height:28px;border-radius:50%;border:1.5px solid " +
              (isSelected ? "#d4b88a" : "#3a4754") +
              ";background:transparent;color:#8a96a4;cursor:pointer;font-size:11px;" +
              "display:flex;align-items:center;justify-content:center;line-height:1;";
          } else {
            sw.style.cssText =
              "width:28px;height:28px;border-radius:50%;border:" +
              (isSelected ? "3px solid #e8eef5" : "1.5px solid " + c.hex) +
              ";background:" + c.hex + ";cursor:pointer;padding:0;";
          }
          sw.addEventListener("click", () => {
            _selectedUserColorId = c.id || null;
            _userDirty = true;
            _renderUserSwatches();
          });
          userSwatches.appendChild(sw);
        });
      };
      _renderUserSwatches();
      userColorWrap.appendChild(userSwatches);
      userPaneEl.appendChild(userColorWrap);

      // 4. "Vrátit na výchozí" link button (clear all overrides)
      const userClearWrap = document.createElement("div");
      userClearWrap.style.cssText =
        "display:flex;justify-content:flex-end;margin-top:4px;padding-top:8px;" +
        "border-top:1px dashed #2a3340;";
      const userClearBtn = document.createElement("button");
      userClearBtn.type = "button";
      userClearBtn.textContent = "↺ Vrátit na výchozí (smazat moje overrides)";
      userClearBtn.style.cssText =
        "padding:6px 12px;background:transparent;border:1px solid #3a4754;" +
        "border-radius:3px;color:#8a96a4;cursor:pointer;font-size:11px;";
      userClearBtn.addEventListener("click", () => {
        userLabelInp.value = "";
        userHintArea.value = "";
        _selectedUserColorId = null;
        _renderUserSwatches();
        _userDirty = true;
      });
      userClearWrap.appendChild(userClearBtn);
      userPaneEl.appendChild(userClearWrap);

      // Persistence note
      const userNote = document.createElement("div");
      userNote.style.cssText =
        "font-size:11px;color:#5d6975;font-style:italic;line-height:1.5;margin-top:4px;";
      userNote.textContent =
        "Tab Uživatel se ukládá do prohlížeče (localStorage) — viditelné jen tobě. " +
        "Tab Komponenta jde do DB (sdílené napříč všemi).";
      userPaneEl.appendChild(userNote);

      body.appendChild(bodyInner);

      // _row helper + _inputStyle pro existing code (preserve API)
      // Note: existing `body.appendChild(...)` calls must redirect to basicPaneEl
      const _row = (labelText, inputEl) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const lbl = document.createElement("label");
        lbl.textContent = labelText;
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        wrap.appendChild(lbl);
        wrap.appendChild(inputEl);
        return wrap;
      };
      const _inputStyle =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
        "box-sizing:border-box;";

      // Info: DB column name (field) / container name + type (container)
      // Krok 5-B (29.5.2026): isContainer mode → DB sloupec irrelevant,
      // zobraz comp_type + comp_def id + parent.
      const infoDb = document.createElement("div");
      infoDb.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px dashed #2a3340;" +
        "border-radius:3px;color:#7a8696;font-size:11px;line-height:1.5;";
      if (isContainer) {
        infoDb.innerHTML = "▦ " + (field.comp_type_code || "container") +
                           " · comp_def #<code style=\"color:#a88cd4;\">" + field.id + "</code>" +
                           " · parent #<code style=\"color:#a8b4c2;\">" +
                           (field.parent_comp_def_id || "—") + "</code>" +
                           (field.name ? " · name: <code style=\"color:#7ed4e8;\">" + field.name + "</code>" : "");
      } else {
        infoDb.innerHTML = "🔗 DB sloupec: <code style=\"color:#7ed4e8;\">" + field.name +
                           "</code>" + (field.region_slot ? " · panel: <code style=\"color:#a8b4c2;\">" + field.region_slot + "</code>" : "");
      }
      basicPaneEl.appendChild(infoDb);

      // Caption — sdíleno field + container
      const captionInput = document.createElement("input");
      captionInput.type = "text";
      captionInput.style.cssText = _inputStyle;
      captionInput.value = field.caption || "";
      captionInput.placeholder = isContainer
        ? "(empty = invisible label u containeru)"
        : field.name;
      basicPaneEl.appendChild(_row(isContainer ? "Caption" : "Caption (label)", captionInput));

      // ────────────────────────────────────────────────────────────────
      // Krok 5-B (29.5.2026, Marti's "sjednotit dva okna"):
      // Container-specific section — Align / Max width / Height / Min height
      // / Border mode. Vidí jen pro panel/groupbox/tabsheet/pagecontrol.
      // ────────────────────────────────────────────────────────────────
      let containerAlignSelect = null;
      let containerHeightInput = null;
      let containerMinHeightInput = null;
      let containerBorderSelect = null;
      // Krok 5-B (29.5.2026 vecer, Marti's "Mozna ze potrebujeme jeste Anchors"):
      // Delphi Anchors property — doplnuje Align. akLeft+akTop+akBottom = panel
      // snapuje vlevo + stretch vertikalne. Bez akBottom = fixed Height.
      let containerAnchorChecks = null;
      if (isContainer) {
        // Align (Marti's "musim vzdy videt align")
        containerAlignSelect = document.createElement("select");
        containerAlignSelect.style.cssText = _inputStyle;
        const aligns = [
          ["client", "alClient — fill remaining (default)"],
          ["top", "alTop — full width strip nahore"],
          ["bottom", "alBottom — full width strip dole"],
          ["left", "alLeft — vertical strip vlevo"],
          ["right", "alRight — vertical strip vpravo"],
          ["none", "alNone — absolute (top/left/width/height)"],
        ];
        for (const [val, label] of aligns) {
          const opt = document.createElement("option");
          opt.value = val;
          opt.textContent = label;
          if ((currentLayout.align || "client") === val) opt.selected = true;
          containerAlignSelect.appendChild(opt);
        }
        basicPaneEl.appendChild(_row("Align", containerAlignSelect));

        // Height
        containerHeightInput = document.createElement("input");
        containerHeightInput.type = "text";
        containerHeightInput.style.cssText = _inputStyle;
        containerHeightInput.value = currentLayout.height != null ? String(currentLayout.height) : "";
        containerHeightInput.placeholder = "px (např. 60) | 'auto'";
        basicPaneEl.appendChild(_row("Height", containerHeightInput));

        // Min height
        containerMinHeightInput = document.createElement("input");
        containerMinHeightInput.type = "number";
        containerMinHeightInput.min = "0";
        containerMinHeightInput.style.cssText = _inputStyle;
        containerMinHeightInput.value = currentLayout.min_height != null ? String(currentLayout.min_height) : "";
        containerMinHeightInput.placeholder = "px (responsive constraint)";
        basicPaneEl.appendChild(_row("Min height", containerMinHeightInput));

        // Border mode
        containerBorderSelect = document.createElement("select");
        containerBorderSelect.style.cssText = _inputStyle;
        // Phase 38.4 Krok 5-B Fix #8 (29.5.2026 pozde, Marti's "Mod All
        // prepiseme na Top-Right"): label změnen z "All — full rámeček"
        // na "Top-Right — linka nahore a vpravo". Enum value "all" zachován
        // pro zpetnou kompatibilitu s DB (zadna migrace).
        const borderModes = [
          ["none", "Žádný (default pro panel)"],
          ["top", "Top — linka nahore"],
          ["all", "Top-Right — linka nahore a vpravo"],
        ];
        const _isGroupboxLike = (field.comp_type_code === "groupbox");
        const currentBorder = currentLayout.border_mode || (_isGroupboxLike ? "top" : "none");
        for (const [val, label] of borderModes) {
          const opt = document.createElement("option");
          opt.value = val;
          opt.textContent = label;
          if (currentBorder === val) opt.selected = true;
          containerBorderSelect.appendChild(opt);
        }
        basicPaneEl.appendChild(_row("Border mode", containerBorderSelect));

        // Krok 5-B (29.5.2026 vecer, Marti's Object Inspector screenshot
        // Anchors: [akLeft, akTop, akBottom]): Delphi Anchors property.
        // Doplnuje Align. Vetsina kombinaci dava smysl:
        //   - alLeft  + [akLeft, akTop, akBottom] = strip vlevo + stretch
        //     vertikalne pres parent vysku (Marti's intent z TUserGroupBox)
        //   - alLeft  + [akLeft, akTop]            = strip vlevo + fixed Height
        //     (sedne k vrchu, neroztaze)
        //   - alClient + [akLeft, akTop, akRight, akBottom] = fill all (default)
        //
        // Default anchors per Align (Delphi typical):
        //   alLeft   → [left, top, bottom]
        //   alRight  → [right, top, bottom]
        //   alTop    → [left, top, right]
        //   alBottom → [left, right, bottom]
        //   alClient → [left, top, right, bottom]
        //   alNone   → [left, top]
        const _ANCHOR_DEFAULTS = {
          left: ["left", "top", "bottom"],
          right: ["right", "top", "bottom"],
          top: ["left", "top", "right"],
          bottom: ["left", "right", "bottom"],
          client: ["left", "top", "right", "bottom"],
          none: ["left", "top"],
        };
        const _currentAlign = (currentLayout.align || "client").toLowerCase();
        const _currentAnchors = Array.isArray(currentLayout.anchors)
          ? currentLayout.anchors.map(a => String(a).toLowerCase())
          : (_ANCHOR_DEFAULTS[_currentAlign] || ["left", "top"]);

        const anchorsWrap = document.createElement("div");
        anchorsWrap.style.cssText =
          "display:flex;gap:10px;align-items:center;flex-wrap:wrap;" +
          "padding:6px 10px;background:#0a0e13;border:1px solid #2a3340;border-radius:3px;";
        containerAnchorChecks = {};
        ["left", "top", "right", "bottom"].forEach(name => {
          const lbl = document.createElement("label");
          lbl.style.cssText =
            "display:flex;align-items:center;gap:4px;color:#cfd6df;" +
            "font-size:12px;cursor:pointer;";
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.value = name;
          cb.checked = _currentAnchors.indexOf(name) !== -1;
          cb.style.cssText = "cursor:pointer;accent-color:#7ed4e8;";
          lbl.appendChild(cb);
          const txt = document.createElement("span");
          txt.textContent = "ak" + name.charAt(0).toUpperCase() + name.slice(1);
          lbl.appendChild(txt);
          anchorsWrap.appendChild(lbl);
          containerAnchorChecks[name] = cb;
        });
        basicPaneEl.appendChild(_row("Anchors", anchorsWrap));

        // Anchors hint
        const anchorsHint = document.createElement("div");
        anchorsHint.style.cssText =
          "padding:6px 10px;font-size:11px;color:#7a8696;font-style:italic;line-height:1.5;";
        anchorsHint.innerHTML =
          "💡 Delphi-style: <b>akTop + akBottom</b> = stretch vertikálně přes parent výšku. " +
          "<b>akLeft + akRight</b> = stretch horizontálně. " +
          "Bez opačných anchorů = fixed Height/Width.";
        basicPaneEl.appendChild(anchorsHint);
      }

      // Placeholder — field-only
      let placeholderInput = null;
      if (!isContainer) {
        placeholderInput = document.createElement("input");
        placeholderInput.type = "text";
        placeholderInput.style.cssText = _inputStyle;
        placeholderInput.value = currentLayout.placeholder || "";
        placeholderInput.placeholder = "např. '—' nebo 'Zadej hodnotu...'";
        basicPaneEl.appendChild(_row("Placeholder", placeholderInput));
      }

      // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's correction):
      // šířka komponenty na displeji — Min width / Max width (px).
      // Aplikuje se na field wrap div jako inline CSS min/max-width.
      // Marti's use case: "3 komponenty vedle sebe" pres min_width
      // nizsi (default ~280px) + max_width upper cap.
      const minWidthInput = document.createElement("input");
      minWidthInput.type = "number";
      minWidthInput.min = "0";
      minWidthInput.style.cssText = _inputStyle;
      minWidthInput.value = currentLayout.min_width != null ? String(currentLayout.min_width) : "";
      minWidthInput.placeholder = "px (např. 150 — minimum sirka pred reflow)";
      basicPaneEl.appendChild(_row("Min width", minWidthInput));

      const maxWidthInput = document.createElement("input");
      maxWidthInput.type = "number";
      maxWidthInput.min = "0";
      maxWidthInput.style.cssText = _inputStyle;
      maxWidthInput.value = currentLayout.max_width != null ? String(currentLayout.max_width) : "";
      maxWidthInput.placeholder = "px (např. 300 — empty = bez limitu)";
      basicPaneEl.appendChild(_row("Max width", maxWidthInput));

      // Krok 5-B (29.5.2026): field-only sekce — Max length / Min length /
      // Read-only / Required. Containery tyto fields nemaji (jsou structural).
      let maxLenInput = null;
      let minLenInput = null;
      let roCheck = null;
      let reqCheck = null;
      if (!isContainer) {
        // Phase 38.4 Krok 14f-M (text length validation, advanced):
        // Max/Min length textu (HTML5 maxlength/minlength). Optional.
        maxLenInput = document.createElement("input");
        maxLenInput.type = "number";
        maxLenInput.min = "0";
        maxLenInput.style.cssText = _inputStyle;
        maxLenInput.value = currentLayout.max_length != null ? String(currentLayout.max_length) : "";
        maxLenInput.placeholder = "max počet znaků (HTML5 maxlength, empty = bez limitu)";
        basicPaneEl.appendChild(_row("Max length (text)", maxLenInput));

        minLenInput = document.createElement("input");
        minLenInput.type = "number";
        minLenInput.min = "0";
        minLenInput.style.cssText = _inputStyle;
        minLenInput.value = currentLayout.min_length != null ? String(currentLayout.min_length) : "";
        minLenInput.placeholder = "min počet znaků (validace pri submit, empty = bez minima)";
        basicPaneEl.appendChild(_row("Min length (text)", minLenInput));

        // Readonly checkbox
        const roCheckWrap = document.createElement("div");
        roCheckWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const roLbl = document.createElement("label");
        roLbl.textContent = "Read-only";
        roLbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        roCheckWrap.appendChild(roLbl);
        roCheck = document.createElement("input");
        roCheck.type = "checkbox";
        roCheck.checked = !!currentLayout.readonly;
        roCheck.style.cssText = "width:18px;height:18px;cursor:pointer;justify-self:start;";
        roCheckWrap.appendChild(roCheck);
        basicPaneEl.appendChild(roCheckWrap);

        // Required checkbox
        const reqCheckWrap = document.createElement("div");
        reqCheckWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
        const reqLbl = document.createElement("label");
        reqLbl.textContent = "Required";
        reqLbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        reqCheckWrap.appendChild(reqLbl);
        reqCheck = document.createElement("input");
        reqCheck.type = "checkbox";
        reqCheck.checked = !!currentLayout.required;
        reqCheck.style.cssText = "width:18px;height:18px;cursor:pointer;justify-self:start;";
        reqCheckWrap.appendChild(reqCheck);
        basicPaneEl.appendChild(reqCheckWrap);
      }

      // ════════════════════════════════════════════════════════════════════
      // Phase 38.4 Krok 14g Etapa F Krok 5.J-A (16.5.2026 ~23:25): Tab 2
      // "Komponenta" — entity_picker specific parametrizace. 6 fields:
      //   1. Data source (lookup source — comp_def.data_source_id FK)
      //   2. Display mode (radio: origin / self / editable)
      //   3. Field extern (string — save target column v parent comp_def)
      //   4. Lookup ID field (string — picker source ID column, default "id")
      //   5. Lookup display field (string — picker source label, default "label")
      //   6. Quick actions (3 checkboxes — link / unlink / create_new)
      //
      // Save flow: data_source_id top-level + layout JSONB merge.
      // ════════════════════════════════════════════════════════════════════
      let dsIdState = null;       // {id, code, name} or null
      let displayModeRadios = null;
      let fieldExternInput = null;
      let lookupIdInput = null;
      let lookupDisplayInput = null;
      let qaLinkCheck = null;
      let qaUnlinkCheck = null;
      let qaCreateCheck = null;

      if (isEntityPicker) {
        // Krok H+13 (27.5.2026 ráno): entity_picker section appenduje
        // do basicPaneEl (Tab "Komponenta") — drop componentPaneEl
        // separate-tab pattern. Visual separator nahoře drží awareness,
        // že je to entity_picker-specific subsekce.
        const epSep = document.createElement("div");
        epSep.style.cssText =
          "margin-top:14px;padding-top:10px;border-top:1px dashed #2a3340;" +
          "font-size:11px;color:#7ed4e8;font-weight:600;letter-spacing:0.5px;";
        epSep.textContent = "🧩 ENTITY PICKER · specifická parametrizace";
        basicPaneEl.appendChild(epSep);

        // 0. Info — comp_def.id + parent context (read-only)
        const infoEp = document.createElement("div");
        infoEp.style.cssText =
          "padding:8px 10px;background:#0f141a;border:1px dashed #2a3340;" +
          "border-radius:3px;color:#7a8696;font-size:11px;line-height:1.5;";
        infoEp.innerHTML = "🧩 entity_picker · comp_def #<code style=\"color:#7ed4e8;\">" + field.id + "</code>" +
                            " · parent #<code style=\"color:#a8b4c2;\">" + (field.parent_comp_def_id || "—") + "</code>";
        basicPaneEl.appendChild(infoEp);

        // 1. Data source picker
        // Initial state z field.data_source_id + field.data_source_code/name
        // (z recursive CTE JOIN ds — fw_form_load_by_id endpoint).
        dsIdState = field.data_source_id != null
          ? { id: field.data_source_id, code: field.data_source_code || null, name: field.data_source_name || null }
          : null;

        const dsButtonWrap = document.createElement("div");
        dsButtonWrap.style.cssText = "display:flex;gap:8px;align-items:center;";

        const dsDisplay = document.createElement("input");
        dsDisplay.type = "text";
        dsDisplay.readOnly = true;
        dsDisplay.style.cssText = _inputStyle + "flex:1;background:#0f141a;color:#cfd6df;";
        const _refreshDsDisplay = () => {
          if (dsIdState && dsIdState.id) {
            dsDisplay.value = "#" + dsIdState.id + " · " + (dsIdState.name || dsIdState.code || "(?)");
          } else {
            dsDisplay.value = "(none)";
          }
        };
        _refreshDsDisplay();

        const dsPickerBtn = document.createElement("button");
        dsPickerBtn.type = "button";
        dsPickerBtn.textContent = "🔗";
        dsPickerBtn.title = "Vybrat data_source (lookup source pro entity_picker)";
        dsPickerBtn.style.cssText =
          "padding:6px 10px;background:#1a1f26;border:1px solid #2a3340;" +
          "color:#8fb8d4;border-radius:3px;cursor:pointer;font-size:14px;";
        dsPickerBtn.addEventListener("click", () => {
          if (typeof window.ErpCatalogPicker !== "function") {
            alert("ErpCatalogPicker not loaded.");
            return;
          }
          const _p = new window.ErpCatalogPicker({
            title: "🔗 Vybrat data source (lookup source pro entity_picker)",
            endpoint: "/api/v1/erp/design/fw-data-source/list?status=active&limit=500",
            listKey: "data_sources",
            coreId: 19,  // Krok 5.T Option C: framework_data_sources core

            idField: "id",
            labelField: "name",
            width: "900px",
            columns: [
              { headerName: "ID", field: "id", width: 80, type: "numericColumn" },
              { headerName: "Code", field: "code", width: 260 },
              { headerName: "Název", field: "name", flex: 1, minWidth: 200 },
            ],
            onSelect: function (row) {
              dsIdState = { id: row.id, code: row.code || null, name: row.name || null };
              _refreshDsDisplay();
            },
          });
          _p.open();
        });

        const dsClearBtn = document.createElement("button");
        dsClearBtn.type = "button";
        dsClearBtn.textContent = "🚫";
        dsClearBtn.title = "Zrušit data_source binding";
        dsClearBtn.style.cssText =
          "padding:6px 10px;background:#1a1f26;border:1px solid #2a3340;" +
          "color:#d48787;border-radius:3px;cursor:pointer;font-size:14px;";
        dsClearBtn.addEventListener("click", () => {
          dsIdState = null;
          _refreshDsDisplay();
        });

        dsButtonWrap.appendChild(dsPickerBtn);
        dsButtonWrap.appendChild(dsClearBtn);
        dsButtonWrap.appendChild(dsDisplay);
        basicPaneEl.appendChild(_row("Data source", dsButtonWrap));

        // 2. Display mode radio (origin / self / editable)
        const dmCurrent = currentLayout.display_mode || "editable";
        const dmWrap = document.createElement("div");
        dmWrap.style.cssText = "display:flex;gap:14px;align-items:center;";
        displayModeRadios = {};
        ["origin", "self", "editable"].forEach((mode) => {
          const lbl = document.createElement("label");
          lbl.style.cssText = "display:flex;align-items:center;gap:5px;color:#cfd6df;font-size:12px;cursor:pointer;";
          const radio = document.createElement("input");
          radio.type = "radio";
          radio.name = "epDisplayMode_" + field.id;
          radio.value = mode;
          radio.checked = (mode === dmCurrent);
          radio.style.cssText = "cursor:pointer;";
          lbl.appendChild(radio);
          const span = document.createElement("span");
          span.textContent = mode;
          lbl.appendChild(span);
          dmWrap.appendChild(lbl);
          displayModeRadios[mode] = radio;
        });
        basicPaneEl.appendChild(_row("Display mode", dmWrap));

        // 3. Field extern (string, save target column)
        fieldExternInput = document.createElement("input");
        fieldExternInput.type = "text";
        fieldExternInput.style.cssText = _inputStyle;
        fieldExternInput.value = currentLayout.field_extern || "";
        fieldExternInput.placeholder = "např. data_source_id (sloupec ve form root comp_def)";
        basicPaneEl.appendChild(_row("Field extern", fieldExternInput));

        // 4. Lookup ID field (default "id")
        lookupIdInput = document.createElement("input");
        lookupIdInput.type = "text";
        lookupIdInput.style.cssText = _inputStyle;
        lookupIdInput.value = currentLayout.lookup_id_field || "";
        lookupIdInput.placeholder = "id (column ve picker source — default 'id')";
        basicPaneEl.appendChild(_row("Lookup ID field", lookupIdInput));

        // 5. Lookup display field (default "label")
        lookupDisplayInput = document.createElement("input");
        lookupDisplayInput.type = "text";
        lookupDisplayInput.style.cssText = _inputStyle;
        lookupDisplayInput.value = currentLayout.lookup_display_field || "";
        lookupDisplayInput.placeholder = "label (column ve picker source — default 'label', pro fw.data_source = 'name')";
        basicPaneEl.appendChild(_row("Lookup display", lookupDisplayInput));

        // 6. Quick actions (3 checkboxes — link / unlink / create_new)
        const qaCurrent = Array.isArray(currentLayout.show_quick_actions)
          ? currentLayout.show_quick_actions
          : ["link", "unlink", "create_new"];
        const qaWrap = document.createElement("div");
        qaWrap.style.cssText = "display:flex;gap:14px;align-items:center;";
        const _mkQaCheck = (name, label) => {
          const lbl = document.createElement("label");
          lbl.style.cssText = "display:flex;align-items:center;gap:5px;color:#cfd6df;font-size:12px;cursor:pointer;";
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.checked = qaCurrent.indexOf(name) !== -1;
          cb.style.cssText = "cursor:pointer;";
          lbl.appendChild(cb);
          const span = document.createElement("span");
          span.textContent = label;
          lbl.appendChild(span);
          qaWrap.appendChild(lbl);
          return cb;
        };
        qaLinkCheck = _mkQaCheck("link", "🔗 link");
        qaUnlinkCheck = _mkQaCheck("unlink", "🚫 unlink");
        qaCreateCheck = _mkQaCheck("create_new", "➕ create");
        basicPaneEl.appendChild(_row("Quick actions", qaWrap));
      }

      // Phase 38.4 Krok H+6 (26.5.2026, Marti's "Combobox jak editovat
      // list, kdyz potrebuju pridat neco co jeste v DB neni"):
      // ComboBox/lookup editor pro layout.enum_values — manual add +
      // remove + "🎯 Doplnit z DB" button (appends only NEW values).
      // Persistent v fw.comp_def.layout.enum_values JSONB array.
      if (isLookupField) {
        // Initialize editable array from current layout
        enumValuesList = Array.isArray(currentLayout.enum_values)
          ? currentLayout.enum_values.slice()
          : [];

        // Section header
        const enumHeader = document.createElement("div");
        enumHeader.style.cssText =
          "margin-top:14px;padding:8px 10px;background:#0f141a;border-left:3px solid #7ed4e8;" +
          "border-radius:3px;color:#a8b4c2;font-size:12px;line-height:1.5;";
        enumHeader.innerHTML =
          "📋 <b style=\"color:#7ed4e8;\">Hodnoty</b> — seznam možností pro ComboBox.<br>" +
          "<span style=\"color:#7a8696;font-size:11px;\">Můžeš přidat hodnoty co v DB ještě nejsou (perzistentní). " +
          "Tlačítko 🎯 doplní z DB jen nové (existující nezdvojí).</span>";
        basicPaneEl.appendChild(enumHeader);

        // List of values (re-renders on add/remove)
        enumValuesListEl = document.createElement("div");
        enumValuesListEl.style.cssText =
          "display:flex;flex-direction:column;gap:4px;max-height:220px;overflow-y:auto;" +
          "padding:8px;background:#0a0e13;border:1px solid #2a3340;border-radius:3px;";
        basicPaneEl.appendChild(enumValuesListEl);

        const _renderEnumList = () => {
          enumValuesListEl.innerHTML = "";
          if (enumValuesList.length === 0) {
            const empty = document.createElement("div");
            empty.style.cssText = "color:#5a6470;font-size:12px;font-style:italic;padding:4px;";
            empty.textContent = "(žádné hodnoty — přidej ručně nebo zavolej 🎯)";
            enumValuesListEl.appendChild(empty);
            return;
          }
          enumValuesList.forEach((val, idx) => {  // eslint-disable-line no-loop-func
            const row = document.createElement("div");
            row.style.cssText =
              "display:flex;align-items:center;gap:6px;padding:3px 6px;" +
              "background:#0f141a;border:1px solid #1f2530;border-radius:3px;";
            const txt = document.createElement("span");
            txt.style.cssText = "flex:1;color:#cfd6df;font-size:12px;font-family:monospace;";
            txt.textContent = String(val);
            row.appendChild(txt);
            const rmBtn = document.createElement("button");
            rmBtn.type = "button";
            rmBtn.textContent = "✕";
            rmBtn.title = "Odebrat hodnotu";
            rmBtn.style.cssText =
              "background:transparent;border:none;color:#7a3838;font-size:14px;" +
              "cursor:pointer;padding:0 4px;line-height:1;";
            rmBtn.addEventListener("mouseenter", () => { rmBtn.style.color = "#e57373"; });
            rmBtn.addEventListener("mouseleave", () => { rmBtn.style.color = "#7a3838"; });
            rmBtn.addEventListener("click", () => {
              enumValuesList.splice(idx, 1);
              _renderEnumList();
            });
            row.appendChild(rmBtn);
            enumValuesListEl.appendChild(row);
          });
        };
        _renderEnumListFn = _renderEnumList;  // hoist for Load defaults
        _renderEnumList();

        // Add input + button row
        const addWrap = document.createElement("div");
        addWrap.style.cssText = "display:flex;gap:6px;align-items:stretch;margin-top:2px;";
        const addInput = document.createElement("input");
        addInput.type = "text";
        addInput.placeholder = "Nová hodnota (Enter = přidat)";
        addInput.style.cssText = _inputStyle + "flex:1;";
        const addBtn = document.createElement("button");
        addBtn.type = "button";
        addBtn.textContent = "+ Přidat";
        addBtn.style.cssText =
          "padding:6px 12px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;" +
          "border-radius:3px;cursor:pointer;font-size:12px;white-space:nowrap;";
        const _doAdd = () => {
          const v = addInput.value.trim();
          if (!v) return;
          if (enumValuesList.indexOf(v) !== -1) {
            _showToast("Hodnota '" + v + "' už v seznamu existuje", "info", 2000);
            addInput.value = "";
            return;
          }
          enumValuesList.push(v);
          addInput.value = "";
          _renderEnumList();
          addInput.focus();
        };
        addBtn.addEventListener("click", _doAdd);
        addInput.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter") {
            ev.preventDefault();
            _doAdd();
          }
        });
        addWrap.appendChild(addInput);
        addWrap.appendChild(addBtn);
        basicPaneEl.appendChild(addWrap);

        // 🎯 Doplnit z DB button (calls existing distinct-values endpoint,
        // appends ONLY new values that aren't already in the list).
        const detectBtn = document.createElement("button");
        detectBtn.type = "button";
        detectBtn.innerHTML = "🎯 Doplnit z DB (jen nové)";
        detectBtn.title = "Načte distinct hodnoty z DB sloupce a přidá jen ty, které v seznamu ještě nejsou";
        detectBtn.style.cssText =
          "padding:6px 12px;background:#1f2530;border:1px solid #2a3340;color:#a8b4c2;" +
          "border-radius:3px;cursor:pointer;font-size:12px;margin-top:2px;align-self:flex-start;";
        detectBtn.addEventListener("click", async () => {
          detectBtn.disabled = true;
          const _origTxt = detectBtn.innerHTML;
          detectBtn.innerHTML = "⏳ Načítám…";
          try {
            const r = await fetch(
              "/api/v1/erp/design/comp-def/" + encodeURIComponent(field.id) + "/distinct-values",
              { credentials: "include" }
            );
            if (!r.ok) {
              const errBody = await r.json().catch(() => ({}));
              throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
            }
            const data = await r.json();
            if (!data.ok) throw new Error(data.error || "unknown");
            if (!Array.isArray(data.values) || data.values.length === 0) {
              _showToast("Žádné distinct hodnoty v DB pro '" + field.name + "'", "info", 2500);
              return;
            }
            // Append only NEW values
            let added = 0;
            data.values.forEach((v) => {
              const s = String(v);
              if (enumValuesList.indexOf(s) === -1) {
                enumValuesList.push(s);
                added += 1;
              }
            });
            _renderEnumList();
            if (added > 0) {
              _showToast("Přidáno " + added + " nových hodnot z DB (" + (data.values.length - added) + " už bylo v seznamu)", "success", 2500);
            } else {
              _showToast("Všechny DB hodnoty (" + data.values.length + ") už jsou v seznamu", "info", 2500);
            }
          } catch (e) {
            _showToast("Načtení z DB selhalo: " + (e.message || e), "error", 3000);
          } finally {
            detectBtn.disabled = false;
            detectBtn.innerHTML = _origTxt;
          }
        });
        basicPaneEl.appendChild(detectBtn);
      }

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Delete button (left, red)
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat';
      deleteBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;margin-right:auto;";
      deleteBtn.title = "Smazat tuto komponentu z formuláře";
      deleteBtn.addEventListener("mouseenter", () => {
        deleteBtn.style.background = "#1f1010";
        deleteBtn.style.borderColor = "#7a3838";
      });
      deleteBtn.addEventListener("mouseleave", () => {
        deleteBtn.style.background = "transparent";
        deleteBtn.style.borderColor = "#5a2828";
      });
      deleteBtn.addEventListener("click", async () => {
        const decision = await _confirmDarkDialog({
          title: "Smazat komponentu",
          message: "Opravdu smazat pole '" + (field.caption || field.name) + "'?\n\n(soft-delete — záznam v audit historii zustava)",
        });
        if (decision !== true) return;
        try { document.body.removeChild(overlay); } catch (e) {}
        await this._performFieldDelete(field);
      });
      footer.appendChild(deleteBtn);

      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "load/save default per
      // comp_type"): 📥 Načíst výchozí + 📌 Uložit jako výchozí.
      // GET/PUT /design/comp-type/{id}/defaults — ct.default_props JSONB.
      // "Kazda komponenta jinak" doctrine — defaults jsou per comp_type
      // (panel jine nez edit jine nez memo).
      const _loadDefBtn = document.createElement("button");
      _loadDefBtn.type = "button";
      _loadDefBtn.innerHTML = "📥 Načíst výchozí";
      _loadDefBtn.title = "Načte výchozí parametry pro typ " + (field.comp_type_code || ("type#" + field.type_id));
      _loadDefBtn.style.cssText =
        "padding:6px 12px;background:#1f2530;border:1px solid #2a3340;color:#a8b4c2;" +
        "border-radius:3px;cursor:pointer;font-size:12px;";
      _loadDefBtn.addEventListener("click", async () => {
        _loadDefBtn.disabled = true;
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-type/" + field.type_id + "/defaults",
            { credentials: "include" }
          );
          const d = await r.json();
          if (!r.ok || !d.ok) throw new Error(d.error || "HTTP " + r.status);
          const dp = d.default_props || {};
          const dpLay = dp.layout || {};
          // Apply na vsechny known fieldy v popup
          if (dpLay.min_width != null) minWidthInput.value = dpLay.min_width;
          if (dpLay.max_width != null) maxWidthInput.value = dpLay.max_width;
          if (dpLay.min_length != null) minLenInput.value = dpLay.min_length;
          if (dpLay.max_length != null) maxLenInput.value = dpLay.max_length;
          if (typeof placeholderInput !== "undefined" && dpLay.placeholder)
            placeholderInput.value = dpLay.placeholder;
          if (typeof roCb !== "undefined" && dpLay.readonly != null)
            roCb.checked = !!dpLay.readonly;
          if (typeof reqCb !== "undefined" && dpLay.required != null)
            reqCb.checked = !!dpLay.required;
          // Phase 38.4 Krok H+6 (26.5.2026): Load enum_values z defaults
          // (Marti's "Defaults = výchozí enum_values" volba). Replace mode
          // — uživatelův manuální list je nahrazen defaults.
          if (isLookupField && Array.isArray(dpLay.enum_values) && _renderEnumListFn) {
            enumValuesList.length = 0;  // clear in-place (preserve reference)
            dpLay.enum_values.forEach((v) => enumValuesList.push(v));
            _renderEnumListFn();
          }
          _showToast("✓ Načteno z výchozí pro " + (d.label || d.code), "success", 2000);
        } catch (e) {
          _showToast("✗ Načtení výchozí selhalo: " + (e.message || e), "error", 3000);
        } finally {
          _loadDefBtn.disabled = false;
        }
      });
      footer.appendChild(_loadDefBtn);

      const _saveDefBtn = document.createElement("button");
      _saveDefBtn.type = "button";
      _saveDefBtn.innerHTML = "📌 Uložit jako výchozí";
      _saveDefBtn.title = "Uloží aktuální parametry jako výchozí pro typ " + (field.comp_type_code || ("type#" + field.type_id));
      _saveDefBtn.style.cssText =
        "padding:6px 12px;background:#2a3a4a;border:1px solid #4a7ba8;color:#cfd6df;" +
        "border-radius:3px;cursor:pointer;font-size:12px;";
      _saveDefBtn.addEventListener("click", async () => {
        _saveDefBtn.disabled = true;
        try {
          const lay = {};
          if (minWidthInput.value.trim()) lay.min_width = parseInt(minWidthInput.value, 10);
          if (maxWidthInput.value.trim()) lay.max_width = parseInt(maxWidthInput.value, 10);
          if (minLenInput.value.trim()) lay.min_length = parseInt(minLenInput.value, 10);
          if (maxLenInput.value.trim()) lay.max_length = parseInt(maxLenInput.value, 10);
          if (typeof placeholderInput !== "undefined" && placeholderInput.value.trim())
            lay.placeholder = placeholderInput.value.trim();
          if (typeof roCb !== "undefined") lay.readonly = roCb.checked;
          if (typeof reqCb !== "undefined") lay.required = reqCb.checked;
          // Phase 38.4 Krok H+6 (26.5.2026): Save enum_values do defaults
          // (Marti's "Defaults = výchozí enum_values"). Per-comp_type
          // baseline pro budoucí nové fieldy stejného typu.
          if (isLookupField && Array.isArray(enumValuesList) && enumValuesList.length > 0) {
            lay.enum_values = enumValuesList.slice();
          }
          const payload = { default_props: { layout: lay } };
          const r = await fetch(
            "/api/v1/erp/design/comp-type/" + field.type_id + "/defaults",
            {
              method: "PUT",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            }
          );
          const d = await r.json();
          if (!r.ok || !d.ok) throw new Error(d.error || "HTTP " + r.status);
          _showToast(
            "✓ Uloženo jako výchozí pro " + (field.comp_type_code || ("type#" + field.type_id)),
            "success", 2000
          );
        } catch (e) {
          _showToast("✗ Uložení výchozí selhalo: " + (e.message || e), "error", 3000);
        } finally {
          _saveDefBtn.disabled = false;
        }
      });
      footer.appendChild(_saveDefBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        saveBtn.style.opacity = "0.6";
        try {
          // ════════════════════════════════════════════════════════════
          // Krok H+13 (27.5.2026 ráno): SPLIT save flow — Tab "Uživatel"
          // (localStorage) + Tab "Komponenta" (PATCH). Oba běží uvnitř
          // jednoho saveBtn click pokud dirty flag = true.
          // ════════════════════════════════════════════════════════════

          // Tab 1 "Uživatel" — localStorage save (label/hint/color overrides)
          // Jen pokud user touched (_userDirty = true). Drop user-only save
          // pokud dirty=false → no localStorage churn, žádný re-apply.
          if (_userDirty) {
            const newUserLabel = userLabelInp.value.trim();
            const newUserHint = userHintArea.value.trim();
            const newUserColorId = _selectedUserColorId || null;
            _saveUserOverride("labels", _fieldKey, newUserLabel || null);
            _saveUserOverride("hints", _fieldKey, newUserHint || null);
            _saveUserOverride("colors", _fieldKey, newUserColorId);
            _reapplyOverridesInDOM(_fieldKey);
          }

          // Tab 2 "Komponenta" — existing PATCH flow (always proběhne pro
          // backward compat existing UX expectation). Drobný no-op PATCH
          // pokud user neměnil nic v Tab Komponenta — acceptable trade-off
          // pro single Save button semantics.

          // Build new layout (merge with existing — preserve other keys)
          const newLayout = Object.assign({}, currentLayout);

          // Phase 38.4 Krok 14f-N: Min/Max width (px) — display layout
          const newMinW = minWidthInput.value.trim() ? parseInt(minWidthInput.value, 10) : null;
          const newMaxW = maxWidthInput.value.trim() ? parseInt(maxWidthInput.value, 10) : null;
          if (newMinW == null || isNaN(newMinW) || newMinW <= 0) delete newLayout.min_width;
          else newLayout.min_width = newMinW;
          if (newMaxW == null || isNaN(newMaxW) || newMaxW <= 0) delete newLayout.max_width;
          else newLayout.max_width = newMaxW;
          if (newLayout.min_width != null && newLayout.max_width != null &&
              newLayout.min_width > newLayout.max_width) {
            _showToast("Min width nesmí být větší než max width", "error", 3000);
            saveBtn.disabled = false;
            saveBtn.style.opacity = "1";
            return;
          }

          // Krok 5-B (29.5.2026): container-specific layout save +
          // field-specific gated v if(!isContainer).
          if (isContainer) {
            // Container-specific: align + height + min_height + border_mode + anchors
            if (containerAlignSelect) newLayout.align = containerAlignSelect.value;

            // Anchors — Delphi paradigm (Marti's "Mozna potrebujeme Anchors")
            if (containerAnchorChecks) {
              const anchorsList = [];
              ["left", "top", "right", "bottom"].forEach(name => {
                const cb = containerAnchorChecks[name];
                if (cb && cb.checked) anchorsList.push(name);
              });
              if (anchorsList.length > 0) newLayout.anchors = anchorsList;
              else delete newLayout.anchors;
            }

            // Height — parse like _openContainerSettings (int | 'auto' | '%')
            const _parseSize = (v) => {
              const s = String(v || "").trim();
              if (s === "") return null;
              if (s === "auto") return "auto";
              if (/%$/.test(s)) return s;
              const n = parseInt(s, 10);
              return isNaN(n) ? null : n;
            };
            const newHeight = containerHeightInput ? _parseSize(containerHeightInput.value) : null;
            if (newHeight == null) delete newLayout.height;
            else newLayout.height = newHeight;

            const newMinH = (containerMinHeightInput && containerMinHeightInput.value.trim())
              ? parseInt(containerMinHeightInput.value, 10) : null;
            if (newMinH == null || isNaN(newMinH) || newMinH <= 0) delete newLayout.min_height;
            else newLayout.min_height = newMinH;

            if (containerBorderSelect) newLayout.border_mode = containerBorderSelect.value;

            // Drop legacy 'width' key (Marti's Bod 1: Width → Max width).
            // Max width zustava obecne v max_width (sdileno s field).
            delete newLayout.width;
          } else {
            // Field-specific: Max/Min length + Placeholder + Readonly + Required
            // Max/Min length — text content (HTML5 maxlength/minlength)
            const newMaxLen = maxLenInput && maxLenInput.value.trim() ? parseInt(maxLenInput.value, 10) : null;
            const newMinLen = minLenInput && minLenInput.value.trim() ? parseInt(minLenInput.value, 10) : null;
            if (newMaxLen == null || isNaN(newMaxLen) || newMaxLen <= 0) delete newLayout.max_length;
            else newLayout.max_length = newMaxLen;
            if (newMinLen == null || isNaN(newMinLen) || newMinLen < 0) delete newLayout.min_length;
            else newLayout.min_length = newMinLen;
            if (newLayout.min_length != null && newLayout.max_length != null &&
                newLayout.min_length > newLayout.max_length) {
              _showToast("Min length nesmí být větší než max length", "error", 3000);
              saveBtn.disabled = false;
              saveBtn.style.opacity = "1";
              return;
            }

            // Placeholder
            const newPh = placeholderInput ? placeholderInput.value.trim() : "";
            if (newPh) newLayout.placeholder = newPh;
            else delete newLayout.placeholder;

            // Readonly + required boolean flags
            if (roCheck && roCheck.checked) newLayout.readonly = true;
            else delete newLayout.readonly;
            if (reqCheck && reqCheck.checked) newLayout.required = true;
            else delete newLayout.required;
          }

          // Phase 38.4 Krok 14g Etapa F Krok 5.J-A (16.5.2026 ~23:30):
          // entity_picker tab "Komponenta" — merge 6 nových fields do
          // newLayout + capture data_source_id (top-level column).
          let newDataSourceId = undefined;  // undefined = ne-send, null = clear, int = set
          if (isEntityPicker) {
            // 1. Data source — top-level column (NE v layout)
            newDataSourceId = (dsIdState && dsIdState.id != null) ? dsIdState.id : null;

            // 2. Display mode (origin / self / editable)
            let dmSelected = null;
            for (const mode in displayModeRadios) {
              if (displayModeRadios[mode].checked) {
                dmSelected = mode;
                break;
              }
            }
            if (dmSelected) newLayout.display_mode = dmSelected;
            else delete newLayout.display_mode;

            // 3. Field extern (string, save target column)
            const fieldExternVal = fieldExternInput.value.trim();
            if (fieldExternVal) newLayout.field_extern = fieldExternVal;
            else delete newLayout.field_extern;

            // 4. Lookup ID field (default "id" v renderu)
            const lookupIdVal = lookupIdInput.value.trim();
            if (lookupIdVal) newLayout.lookup_id_field = lookupIdVal;
            else delete newLayout.lookup_id_field;

            // 5. Lookup display field (default "label" v renderu)
            const lookupDisplayVal = lookupDisplayInput.value.trim();
            if (lookupDisplayVal) newLayout.lookup_display_field = lookupDisplayVal;
            else delete newLayout.lookup_display_field;

            // 6. Quick actions (array — preserve order link/unlink/create_new)
            const qaList = [];
            if (qaLinkCheck.checked) qaList.push("link");
            if (qaUnlinkCheck.checked) qaList.push("unlink");
            if (qaCreateCheck.checked) qaList.push("create_new");
            if (qaList.length > 0) newLayout.show_quick_actions = qaList;
            else delete newLayout.show_quick_actions;
          }

          // Phase 38.4 Krok H+6 (26.5.2026): ComboBox/lookup enum_values
          // editor — write editable list back do layout.enum_values.
          // Marti's "Persistent enum v layout.enum_values" — perzistuje
          // i manuálně přidané hodnoty co v DB ještě nejsou.
          if (isLookupField && Array.isArray(enumValuesList)) {
            if (enumValuesList.length > 0) {
              newLayout.enum_values = enumValuesList.slice();
            } else {
              delete newLayout.enum_values;
            }
          }

          const newCaption = captionInput.value.trim();

          // Build body — include data_source_id JEN pokud entity_picker
          // (jinak undefined → JSON.stringify ho vynechá)
          const _patchBody = {
            caption: newCaption,
            layout: newLayout,
          };
          if (isEntityPicker && newDataSourceId !== undefined) {
            _patchBody.data_source_id = newDataSourceId;
          }

          const pr = await fetch(
            "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(field.id),
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
              body: JSON.stringify(_patchBody),
            }
          );
          if (!pr.ok) {
            const errBody = await pr.json().catch(() => ({}));
            throw new Error("HTTP " + pr.status + ": " + (errBody.error || pr.statusText));
          }
          _showToast("Nastavení uloženo", "success", 2000);
          document.body.removeChild(overlay);
          this._pendingFlashFieldId = field.id;
          await this._reloadSpec();
        } catch (e) {
          console.error("[DesignFwForm] _openFieldSettings save failed:", e);
          _showToast("Uložení selhalo: " + (e.message || e), "error", 3500);
          saveBtn.disabled = false;
          saveBtn.style.opacity = "1";
        }
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          try { document.body.removeChild(overlay); } catch (e) {}
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);

      setTimeout(() => captionInput.focus(), 50);
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-L (14.5.2026 vecer, Marti's "tam mame jeste
    // nedodelanou parametrizaci ke kteremu DB fieldu to patri"):
    // Mini column picker dialog pri drag z palette pro data-bound fields.
    //
    // Trigger: drag-drop z gallery pro non-container, non-label-only types.
    // Modal: dropdown s available columns (entity-columns API) + "Bez DB
    // vazby" option pro pure-visual fields. OK → POST s name=column.name,
    // caption=column.caption_default. Cancel → no INSERT.
    //
    // Returns Promise<{name, caption} | null> — null pri cancel.
    // ════════════════════════════════════════════════════════════════
    async _pickColumnForNewField(payload, parentId) {
      return new Promise(async (resolve) => {
        // 1. Fetch entity-columns pres backend (same source jako FieldPickerModal)
        const entityType = this._spec && this._spec.core && this._spec.core.data_entity_type;
        if (!entityType) {
          _showToast("Form nema data_entity_type — nelze ziskat columns", "error", 3000);
          resolve(null);
          return;
        }

        let columns = [];
        try {
          const formId = this._spec && this._spec.form && this._spec.form.id;
          const url = "/api/v1/erp/design/entity-columns/" + encodeURIComponent(entityType) +
                      (formId ? "?parent_comp_def_id=" + encodeURIComponent(formId) : "");
          const r = await fetch(url, { credentials: "include" });
          if (!r.ok) throw new Error("HTTP " + r.status);
          const d = await r.json();
          if (!d.ok) throw new Error(d.error || "unknown");
          columns = d.columns || [];
        } catch (e) {
          _showToast("Nepodarilo se nacist sloupce: " + (e.message || e), "error", 3500);
          resolve(null);
          return;
        }

        // Filter: nejdrive available (existing_comp_def_id == null) — Marti
        // zridka chce duplikovat existujici field. Show all as info (used).
        const availableCols = columns.filter(c => c.existing_comp_def_id == null);
        const usedCols = columns.filter(c => c.existing_comp_def_id != null);

        // 2. Build modal
        const overlay = document.createElement("div");
        overlay.style.cssText =
          "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10002;" +
          "display:flex;align-items:center;justify-content:center;";

        const modal = document.createElement("div");
        modal.style.cssText =
          "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
          "min-width:460px;max-width:560px;color:#e8eef5;font-size:13px;" +
          "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

        // Header
        const header = document.createElement("div");
        header.style.cssText =
          "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
          "display:flex;align-items:center;justify-content:space-between;";
        const title = document.createElement("div");
        title.style.cssText = "font-weight:600;font-size:14px;";
        title.innerHTML = "🔗 DB vazba pro " + payload.label +
                          " <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">(" + payload.code + ")</span>";
        header.appendChild(title);
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.textContent = "✕";
        closeBtn.style.cssText =
          "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
          "cursor:pointer;padding:0;line-height:1;";
        const _close = (result) => {
          try { document.body.removeChild(overlay); } catch (e) {}
          document.removeEventListener("keydown", escHandler, true);
          resolve(result);
        };
        closeBtn.addEventListener("click", () => _close(null));
        header.appendChild(closeBtn);
        modal.appendChild(header);

        // Body
        const body = document.createElement("div");
        body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

        const intro = document.createElement("div");
        intro.style.cssText = "color:#a8b4c2;font-size:12px;line-height:1.5;";
        intro.innerHTML =
          "Vyber DB sloupec, který tato komponenta reprezentuje. " +
          "Nebo zvol <b>Bez DB vazby</b> pro pure-visual element (label, decorativní).";
        body.appendChild(intro);

        // Column dropdown
        const colWrap = document.createElement("div");
        colWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
        const colLabel = document.createElement("label");
        colLabel.textContent = "DB sloupec";
        colLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
        colWrap.appendChild(colLabel);

        const colSelect = document.createElement("select");
        colSelect.style.cssText =
          "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;" +
          "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;";

        // Available group
        if (availableCols.length > 0) {
          const og = document.createElement("optgroup");
          og.label = "📋 Volné (" + availableCols.length + ")";
          for (const c of availableCols) {
            const opt = document.createElement("option");
            opt.value = c.name;
            opt.textContent = c.caption_default + "  (" + c.name + ")";
            opt.dataset.caption = c.caption_default;
            og.appendChild(opt);
          }
          colSelect.appendChild(og);
        }
        // Used group (warning, duplicate)
        if (usedCols.length > 0) {
          const og2 = document.createElement("optgroup");
          og2.label = "⚠ Jiz pouzite na forme (" + usedCols.length + ")";
          for (const c of usedCols) {
            const opt = document.createElement("option");
            opt.value = c.name;
            opt.textContent = c.caption_default + "  (" + c.name + ")";
            opt.dataset.caption = c.caption_default;
            og2.appendChild(opt);
          }
          colSelect.appendChild(og2);
        }
        // No-binding option
        const opt0 = document.createElement("option");
        opt0.value = "__NO_BINDING__";
        opt0.textContent = "── Bez DB vazby (visual only) ──";
        colSelect.appendChild(opt0);

        // Default: prvni available, jinak no-binding
        if (availableCols.length === 0) {
          opt0.selected = true;
        }
        colWrap.appendChild(colSelect);
        body.appendChild(colWrap);

        // Caption override (optional rename)
        const capWrap = document.createElement("div");
        capWrap.style.cssText = "display:flex;flex-direction:column;gap:6px;";
        const capLabel = document.createElement("label");
        capLabel.textContent = "Caption (label v UI)";
        capLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
        capWrap.appendChild(capLabel);
        const capInput = document.createElement("input");
        capInput.type = "text";
        capInput.style.cssText =
          "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;" +
          "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;" +
          "box-sizing:border-box;";
        // Auto-fill caption ze selected column
        const _syncCaption = () => {
          const sel = colSelect.options[colSelect.selectedIndex];
          if (sel && sel.dataset && sel.dataset.caption) {
            capInput.value = sel.dataset.caption;
          } else if (sel && sel.value === "__NO_BINDING__") {
            capInput.value = payload.label;  // fallback comp_type label
          }
        };
        _syncCaption();
        colSelect.addEventListener("change", _syncCaption);
        capWrap.appendChild(capInput);
        body.appendChild(capWrap);

        modal.appendChild(body);

        // Footer
        const footer = document.createElement("div");
        footer.style.cssText =
          "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
          "display:flex;justify-content:flex-end;gap:8px;";

        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = "Storno";
        cancelBtn.style.cssText =
          "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
          "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
        cancelBtn.addEventListener("click", () => _close(null));
        footer.appendChild(cancelBtn);

        const okBtn = document.createElement("button");
        okBtn.type = "button";
        okBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Přidat';
        okBtn.style.cssText =
          "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
          "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
        okBtn.addEventListener("click", () => {
          const selValue = colSelect.value;
          const caption = capInput.value.trim() || payload.label;
          if (selValue === "__NO_BINDING__") {
            // Visual-only — auto-name s timestamp
            const name = payload.code + "_" + Date.now().toString(36);
            _close({ name, caption, hasBinding: false });
          } else {
            _close({ name: selValue, caption, hasBinding: true });
          }
        });
        footer.appendChild(okBtn);
        modal.appendChild(footer);

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        const escHandler = (ev) => {
          if (ev.key === "Escape") {
            ev.stopPropagation();
            _close(null);
          }
        };
        document.addEventListener("keydown", escHandler, true);

        setTimeout(() => colSelect.focus(), 50);
      });
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-I (14.5.2026 vecer, Marti's "dodelat nastaveni
    // gridu, minimalne tlacitko odebrat zatim"): right-click na child
    // section (TELEFONY/EMAILY) → mini settings popup s Odebrat.
    //
    // Child grids (1:N joined tables) zatim NEJSOU v fw.comp_def — jsou
    // memory-only z _spec.children. "Odebrat" = hide flag v memory
    // (this._childHidden[childKey] = true). Survive _render cycles ale
    // ne sessions (re-open form ukaze vsechny grids znovu).
    //
    // Future (post-MVP): persist v DB pres user_preferences nebo
    // form_layout_overrides tabulku.
    // ════════════════════════════════════════════════════════════════
    _openChildSectionSettings(childKey, childInfo) {
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10001;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:6px;" +
        "min-width:380px;max-width:460px;color:#e8eef5;font-size:13px;" +
        "box-shadow:0 8px 32px rgba(0,0,0,0.6);overflow:hidden;";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:12px 16px;background:#1a2028;border-bottom:1px solid #2a3340;" +
        "display:flex;align-items:center;justify-content:space-between;";
      const title = document.createElement("div");
      title.style.cssText = "font-weight:600;font-size:14px;";
      title.innerHTML = "📋 Nastavení sekce: <span style=\"color:#a8b4c2;\">" +
                        (childInfo.label || childKey) + "</span>";
      header.appendChild(title);
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:transparent;border:none;color:#8a96a4;font-size:18px;" +
        "cursor:pointer;padding:0;line-height:1;";
      closeBtn.addEventListener("click", () => document.body.removeChild(overlay));
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body
      const body = document.createElement("div");
      body.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";

      // Position dropdown (above/below groupbox)
      const posWrap = document.createElement("div");
      posWrap.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;";
      const posLabel = document.createElement("label");
      posLabel.textContent = "Pozice v panelu";
      posLabel.style.cssText = "color:#a8b4c2;font-size:12px;";
      posWrap.appendChild(posLabel);
      const posSelect = document.createElement("select");
      posSelect.style.cssText =
        "padding:6px 10px;background:#0f141a;border:1px solid #2a3340;" +
        "color:#e8eef5;border-radius:3px;font-size:13px;width:100%;";
      const positions = [
        ["before-main", "Nad groupboxem (default)"],
        ["after-main", "Pod groupboxem"],
      ];
      const currentPos = (this._childPosition && this._childPosition[childKey]) || "before-main";
      for (const [val, label] of positions) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if (currentPos === val) opt.selected = true;
        posSelect.appendChild(opt);
      }
      posWrap.appendChild(posSelect);
      body.appendChild(posWrap);

      // Info text
      const info = document.createElement("div");
      info.style.cssText =
        "padding:10px;background:#0f141a;border:1px dashed #2a3340;" +
        "border-radius:3px;color:#7a8696;font-size:11px;line-height:1.5;";
      info.innerHTML =
        "📊 Tato sekce zobrazuje 1:N joined data (např. <code>user_contacts</code>). " +
        "<strong>Odebrat z formuláře</strong> skryje sekci — data v DB zůstanou. " +
        "Re-add zatím vyžaduje DB UPDATE (post-MVP polish: pridani z palety).";
      body.appendChild(info);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 16px;background:#1a2028;border-top:1px solid #2a3340;" +
        "display:flex;align-items:center;gap:8px;";

      // Odebrat (red, left, push others right via margin-right:auto)
      const hideBtn = document.createElement("button");
      hideBtn.type = "button";
      hideBtn.innerHTML = '<span style="color:#e57373;font-weight:700;margin-right:6px;">✕</span>Odebrat z formuláře';
      hideBtn.style.cssText =
        "padding:6px 16px;background:transparent;border:1px solid #5a2828;" +
        "border-radius:3px;color:#e57373;cursor:pointer;font-size:13px;" +
        "margin-right:auto;";
      hideBtn.title = "Skryje sekci '" + (childInfo.label || childKey) + "' z formuláře. Data v DB zůstanou.";
      hideBtn.addEventListener("mouseenter", () => {
        hideBtn.style.background = "#1f1010";
        hideBtn.style.borderColor = "#7a3838";
      });
      hideBtn.addEventListener("mouseleave", () => {
        hideBtn.style.background = "transparent";
        hideBtn.style.borderColor = "#5a2828";
      });
      hideBtn.addEventListener("click", () => {
        if (!this._childHidden) this._childHidden = {};
        this._childHidden[childKey] = true;
        _showToast("Sekce '" + (childInfo.label || childKey) + "' odebrana", "success", 2200);
        document.body.removeChild(overlay);
        this._render();
        this._attachDropTargetForGalleryDrag();
      });
      footer.appendChild(hideBtn);

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.addEventListener("click", () => document.body.removeChild(overlay));
      footer.appendChild(cancelBtn);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      saveBtn.style.cssText =
        "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;" +
        "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:13px;font-weight:600;";
      saveBtn.addEventListener("click", () => {
        if (!this._childPosition) this._childPosition = {};
        this._childPosition[childKey] = posSelect.value;
        _showToast("Pozice sekce uložena", "success", 1800);
        document.body.removeChild(overlay);
        this._render();
        this._attachDropTargetForGalleryDrag();
      });
      footer.appendChild(saveBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Esc to close
      const escHandler = (ev) => {
        if (ev.key === "Escape") {
          ev.stopPropagation();
          document.body.removeChild(overlay);
          document.removeEventListener("keydown", escHandler, true);
        }
      };
      document.addEventListener("keydown", escHandler, true);
    }

    // Phase 38.4 Krok 14e-E (14.5.2026 vecer, Marti's "Panel musi byt
    // dragabled"): generic drag-and-drop pro containers (panel/groupbox).
    // Analog _wrapFieldForDesign drag events, ale na container wrap.
    // Reuse _performFieldReorder (Krok 14e-F generalized na siblings podle
    // parent_comp_def_id).
    _attachContainerDragEvents(wrap, container) {
      wrap.addEventListener("dragstart", (ev) => {
        // Defensive: pokud drag started z child input/button, neaktivuj
        // container drag (necht child mu da event)
        const isFromAction = ev.target && (
          ev.target.tagName === "INPUT" ||
          ev.target.tagName === "BUTTON" ||
          ev.target.tagName === "TEXTAREA"
        );
        if (isFromAction) return;
        wrap.style.opacity = "0.5";
        this._dragState = {
          fieldId: container.id,
          fromIndex: 0,
          el: wrap,
          isContainer: true,
        };
        try {
          ev.dataTransfer.effectAllowed = "move";
          ev.dataTransfer.setData("text/plain", String(container.id));
        } catch (e) {}
      });
      wrap.addEventListener("dragend", () => {
        wrap.style.opacity = "";
        wrap.style.outline = "";
        // Clean drop indicators na siblings
        if (wrap.parentElement) {
          wrap.parentElement.querySelectorAll(".erp-design-panel, .erp-design-groupbox")
            .forEach((el) => {
              el.style.borderTopColor = "";
              el.style.borderBottomColor = "";
            });
        }
        this._dragState = null;
      });
      wrap.addEventListener("dragover", (ev) => {
        if (!this._dragState) return;
        // Phase 38.4 Krok 14f-K (14.5.2026 vecer, Marti's "drop se
        // neuskutecni"): support cross-container drag — existing field
        // (non-isContainer) drop NA container → move (PATCH parent).
        if (this._dragState.isContainer) {
          // Container reorder (panel/groupbox swap sort_order)
          if (this._dragState.fieldId === container.id) return;
          ev.preventDefault();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          const rect = wrap.getBoundingClientRect();
          const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
          wrap.style.borderTop = isAbove
            ? "2px solid #7ed4e8"
            : "1px dashed rgba(122, 134, 150, 0.3)";
          wrap.style.borderBottom = isAbove
            ? "1px dashed rgba(122, 134, 150, 0.3)"
            : "2px solid #7ed4e8";
        } else {
          // Existing field drag → highlight container as "move INTO" target
          // Skip pokud field uz JE direct child tohoto containeru (no-op move)
          ev.preventDefault();
          try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
          wrap.style.outline = "2px solid #a88cd4";
          wrap.style.outlineOffset = "-2px";
          wrap.style.background = "rgba(168, 140, 212, 0.05)";
        }
      });
      wrap.addEventListener("dragleave", () => {
        wrap.style.outline = "";
        wrap.style.background = "";
        wrap.style.borderTop = "1px dashed rgba(122, 134, 150, 0.3)";
        wrap.style.borderBottom = "1px dashed rgba(122, 134, 150, 0.3)";
      });
      wrap.addEventListener("drop", (ev) => {
        if (!this._dragState) return;
        ev.preventDefault();
        ev.stopPropagation();  // block body.drop dual-fire
        wrap.style.outline = "";
        wrap.style.background = "";
        wrap.style.borderTop = "1px dashed rgba(122, 134, 150, 0.3)";
        wrap.style.borderBottom = "1px dashed rgba(122, 134, 150, 0.3)";

        if (this._dragState.isContainer) {
          // Container reorder
          const fromId = this._dragState.fieldId;
          const toId = container.id;
          if (fromId === toId) return;
          const rect = wrap.getBoundingClientRect();
          const isAbove = (ev.clientY - rect.top) < (rect.height / 2);
          this._performFieldReorder(fromId, toId, isAbove);
        } else {
          // Phase 38.4 Krok 14f-K: existing field MOVE INTO this container
          const fromId = this._dragState.fieldId;
          // No-op pokud uz jsme direct child
          const fields = this._spec.fields || [];
          const fromComp = fields.find((f) => f.id === fromId);
          if (fromComp && fromComp.parent_comp_def_id === container.id) {
            _showToast("Komponenta uz je v tomto kontejneru", "info", 1500);
            return;
          }
          this._performFieldMove(fromId, container.id);
        }
      });
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14g-A (15.5.2026 rano, Marti's "drop na field
    // v jinem panelu se neuskutecni"): atomic cross-parent move + position.
    //
    // Drive (14f-K): _performFieldMove appendl field na konec target
    // containeru bez position control. Plus _performFieldReorder cross-
    // parent → error toast.
    //
    // NEW: cross-parent drag z field A (panel #20) na field B (panel #22):
    //   1. Compute target position v panel #22 siblings (dropAbove = isAbove)
    //   2. PATCH /design/comp-def/update/{A.id} s {parent_comp_def_id:
    //      panel22.id} — move to new parent
    //   3. PUT /design/comp-def/reorder s field_orders array (siblings v
    //      novem parent + moved field na target position) — set sort_order
    //   4. _reloadSpec + flash
    //
    // 2-step (PATCH + reorder) zachovava idempotency. Sort_order multiples
    // of 10 — pripadne re-pad.
    // ════════════════════════════════════════════════════════════════
    async _performCrossParentMove(fromId, toComp, dropAbove) {
      const fields = this._spec.fields || [];
      // Krok 14g-D undo: snapshot original parent + sort_order PRED move
      const fromCompPre = fields.find((f) => f.id === fromId);
      const originalParentId = fromCompPre && fromCompPre.parent_comp_def_id;
      const originalSortOrder = fromCompPre && fromCompPre.sort_order;
      const originalLabel = fromCompPre &&
        (fromCompPre.caption || fromCompPre.name || ("#" + fromId));

      const targetParentId = toComp.parent_comp_def_id;

      // Phase 38.4 Krok H+5++ (26.5.2026 vecer, Marti's "drop hlasi chybu"):
      // Guard #1 — self-parent: nelze udelat komponentu nadrazenou sobe.
      // Tipicky scenario: drag main_panel row → drop na jeho child →
      // targetParentId == fromId → PATCH self-parent → backend 400.
      if (targetParentId === fromId) {
        _showToast(
          "Nelze přesunout komponentu dovnitř sebe sama. " +
          "Pro změnu pořadí použij přetažení v rámci stejného containeru.",
          "warning", 3500
        );
        return;
      }
      // Guard #2 — cycle detection: targetParent nesmi byt potomek fromId
      // (jinak by vznikl kruh A→B→A). Walk parent chain od targetParentId
      // smerem nahoru a zkontroluj, ze v cele ceste nenarazime na fromId.
      const _byId = new Map(fields.map((f) => [f.id, f]));
      let _ancestor = _byId.get(targetParentId);
      let _hops = 0;
      while (_ancestor && _hops < 50) {
        if (_ancestor.id === fromId) {
          _showToast(
            "Nelze přesunout komponentu dovnitř jejího potomka " +
            "(vznikl by kruh).",
            "warning", 3500
          );
          return;
        }
        _ancestor = _ancestor.parent_comp_def_id != null
          ? _byId.get(_ancestor.parent_comp_def_id)
          : null;
        _hops += 1;
      }

      // Build new sibling list v target parent (excluding fromId pro pripad
      // ze tam uz neni)
      const targetSiblings = fields
        .filter((f) => f.parent_comp_def_id === targetParentId && f.id !== fromId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      // Compute insert position
      let insertAt = targetSiblings.findIndex((f) => f.id === toComp.id);
      if (insertAt < 0) insertAt = targetSiblings.length;
      if (!dropAbove) insertAt += 1;
      // Insert moved field reference
      targetSiblings.splice(insertAt, 0, { id: fromId });
      // Compute new sort_order array (multiples of 10)
      const reorderPayload = targetSiblings.map((f, i) => ({
        id: f.id,
        sort_order: (i + 1) * 10,
      }));

      console.info(
        "[DesignFwForm] crossParentMove",
        "fromId=" + fromId,
        "→ targetParentId=" + targetParentId,
        "@insertAt=" + insertAt,
        "(dropAbove=" + dropAbove + ")"
      );

      try {
        // Step 1: PATCH parent_comp_def_id
        const pr = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fromId),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ parent_comp_def_id: targetParentId }),
          }
        );
        if (!pr.ok) {
          const eb = await pr.json().catch(() => ({}));
          throw new Error("PATCH HTTP " + pr.status + ": " + (eb.error || pr.statusText));
        }
        // Step 2: Reorder v target parent (set sort_order vsech siblings)
        const rr = await fetch("/api/v1/erp/design/comp-def/reorder", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ field_orders: reorderPayload }),
        });
        if (!rr.ok) {
          const eb = await rr.json().catch(() => ({}));
          throw new Error("reorder HTTP " + rr.status + ": " + (eb.error || rr.statusText));
        }
        _showToast("Komponenta presunuta + serazena", "success", 2200);
        // Krok 14g-D undo: push inverse (PATCH parent + sort_order back)
        if (originalParentId != null) {
          this._pushUndoOp(
            "Presun '" + originalLabel + "' zpet do parent #" + originalParentId,
            async () => {
              await fetch(
                "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fromId),
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({
                    parent_comp_def_id: originalParentId,
                    sort_order: originalSortOrder || 10,
                  }),
                }
              );
            }
          );
        }
        this._pendingFlashFieldId = fromId;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _performCrossParentMove failed:", e);
        _showToast("Cross-parent presun selhal: " + (e.message || e), "error", 3500);
      }
    }

    // Phase 38.4 Krok 14f-K (14.5.2026 vecer, Marti's "drop se neuskutecni"):
    // Move existing field/groupbox do jineho containeru (panel/groupbox).
    // PATCH /design/comp-def/update/{id} s parent_comp_def_id. Po success
    // reload + flash on moved field. Bez position control — appenduje na
    // konec siblings (auto sort_order). Pro position-aware drop → pouzij
    // _performCrossParentMove (14g-A).
    async _performFieldMove(fieldId, newParentId) {
      // Krok 14g-D undo: snapshot original parent + sort_order PRED move
      const fields = this._spec.fields || [];
      const preComp = fields.find((f) => f.id === fieldId);
      const origParent = preComp && preComp.parent_comp_def_id;
      const origSort = preComp && preComp.sort_order;
      const origLabel = preComp &&
        (preComp.caption || preComp.name || ("#" + fieldId));

      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fieldId),
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ parent_comp_def_id: newParentId }),
          }
        );
        if (!r.ok) {
          const errBody = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
        }
        _showToast("Komponenta presunuta", "success", 2200);
        // Krok 14g-D undo: push inverse
        if (origParent != null) {
          this._pushUndoOp(
            "Presun '" + origLabel + "' zpet do parent #" + origParent,
            async () => {
              await fetch(
                "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(fieldId),
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  credentials: "include",
                  body: JSON.stringify({
                    parent_comp_def_id: origParent,
                    sort_order: origSort || 10,
                  }),
                }
              );
            }
          );
        }
        this._pendingFlashFieldId = fieldId;
        await this._reloadSpec();
      } catch (e) {
        console.error("[DesignFwForm] _performFieldMove failed:", e);
        _showToast("Presun selhal: " + (e.message || e), "error", 3500);
      }
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-B (14.5.2026 vecer, Marti's "B alClient zbytek
    // se nehneme dal"): Delphi VCL dynamic align layout pro panels.
    //
    // Marti's 19yr Delphi doctrine — alClient reservation pattern:
    //   alTop    → reserve top horizontal strip (full width, height=panel.height)
    //   alBottom → reserve bottom strip
    //   alLeft   → reserve left vertical strip (full height po reservations)
    //   alRight  → reserve right vertical strip
    //   alClient → fill REMAINING space (zbytek)
    //   alNone   → absolute positioning (Phase A+1 pattern)
    //
    // Order matters: top → bottom → left → right → client. Client je vzdy
    // posledni, absorbuje zbytek.
    //
    // CSS implementation via nested flexbox:
    //   <div column>
    //     [alTop panels rows]
    //     <div row flex=1>  -- middle
    //       [alLeft cols]
    //       [alClient cols (flex=1)]
    //       [alRight cols]
    //     </div>
    //     [alBottom panels rows]
    //   </div>
    //
    // Bez align key: backward compat → treat as 'client'.
    // ════════════════════════════════════════════════════════════════
    _buildAlignLayout(comps) {
      // Group by align (default = 'client' pro backward compat)
      const byAlign = { top: [], bottom: [], left: [], right: [], client: [], none: [] };
      for (const c of comps) {
        const a = String((c.layout && c.layout.align) || "client").toLowerCase();
        const key = (a in byAlign) ? a : "client";
        byAlign[key].push(c);
      }
      // Sort each align bucket by sort_order
      for (const k of Object.keys(byAlign)) {
        byAlign[k].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
      }

      // Helper: apply size + min size constraint pro align panel
      // Krok 5-B (29.5.2026 dopoledne, Marti's "Mam panel align left
      // ten Max width nerespektuje"): refactor pro Width→Max width
      // semantics z Krok 5-B settings popup sjednoceni.
      //   - layout.width (LEGACY) — Delphi-style target width (alLeft Width)
      //   - layout.max_width (NEW) — Marti's "Max width omezit aby nerozthoval"
      //     Pro alLeft/alRight slouzi jako target width (Delphi Width property).
      //     Pro alClient/alTop/alBottom slouzi jako CSS max-width upper bound.
      //   - layout.min_width / layout.min_height — minimum constraint
      // Priority: width (legacy) → max_width (new) pro target sizing.
      const _applySize = (el, c, axis) => {
        const layout = c.layout || {};
        const sizeKey = axis === "h" ? "height" : "width";
        const maxKey = axis === "h" ? "max_height" : "max_width";
        const minKey = axis === "h" ? "min_height" : "min_width";
        // Target size: legacy 'width'/'height' OR new 'max_width'/'max_height'
        // Marti's "Width jako Max width" semantics — pro alLeft je to width.
        const sizeRaw = layout[sizeKey] != null ? layout[sizeKey] : layout[maxKey];
        const min = layout[minKey];
        if (sizeRaw != null && sizeRaw !== "auto") {
          const v = (typeof sizeRaw === "number") ? sizeRaw + "px" : String(sizeRaw);
          el.style.flex = "0 0 " + v;
        } else {
          el.style.flex = "0 0 auto";
        }
        if (min != null) {
          const m = (typeof min === "number") ? min + "px" : String(min);
          el.style[axis === "h" ? "minHeight" : "minWidth"] = m;
        }
        // Marti's "Max width omezit aby nerozthoval pres obrazovku" —
        // aplikujeme max-width / max-height jako CSS constraint pro VŠECHNY
        // align panels (vcetne alClient/alTop/alBottom).
        const maxRaw = layout[maxKey];
        if (maxRaw != null && maxRaw !== "auto") {
          const mx = (typeof maxRaw === "number") ? maxRaw + "px" : String(maxRaw);
          el.style[axis === "h" ? "maxHeight" : "maxWidth"] = mx;
        }
      };

      // Root: column flex
      const wrap = document.createElement("div");
      wrap.className = "erp-design-align-layout";
      wrap.style.cssText =
        "display:flex;flex-direction:column;" +
        "flex:1 1 auto;min-height:0;height:100%;" +
        "position:relative;";  // pro alNone absolute children

      // alTop panels (full width strips, stacked top)
      // Krok 5-B Fix #7 (29.5.2026 pozde, Marti's "linka prvniho panelu
      // splynula s linkou hlavicky"): prvni top panel dropne margin-top +
      // border-top + padding-top → modal header's border-bottom line se
      // stane jedinou linkou nad caption. Caption sedi tesne pod ni.
      let _topPanelIdx = 0;
      for (const c of byAlign.top) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          _applySize(el, c, "h");
          el.style.width = "100%";
          if (_topPanelIdx === 0) {
            el.style.marginTop = "0";
            el.style.borderTop = "none";
            el.style.paddingTop = "0";
          }
          wrap.appendChild(el);
          _topPanelIdx++;
        }
      }

      // Middle row (alLeft + alClient + alRight)
      const hasMiddle = byAlign.left.length > 0 ||
                       byAlign.right.length > 0 ||
                       byAlign.client.length > 0;
      let middle = null;
      if (hasMiddle) {
        middle = document.createElement("div");
        middle.className = "erp-design-align-middle";
        // Krok 5-B (29.5.2026, Marti's "panely kazdy jinak vysoky"):
        // Middle row dostane explicit min-height z max(min_height) napric
        // children, aby flex stretch melo defined height. Jinak align-items:
        // stretch falls back na max(intrinsic_content_height), ktery se lisi
        // mezi alLeft a alClient (alLeft mel "height:100%" hack, alClient
        // flex:1 1 auto bez fixed height → ruzne intrinsic heights).
        let middleMaxMinHeight = 0;
        const _allMiddleChildren = [...byAlign.left, ...byAlign.client, ...byAlign.right];
        for (const c of _allMiddleChildren) {
          const mh = c && c.layout && c.layout.min_height;
          if (typeof mh === "number" && mh > middleMaxMinHeight) {
            middleMaxMinHeight = mh;
          } else if (typeof mh === "string") {
            const n = parseInt(mh, 10);
            if (!isNaN(n) && n > middleMaxMinHeight) middleMaxMinHeight = n;
          }
        }
        middle.style.cssText =
          "display:flex;flex-direction:row;align-items:stretch;" +
          "flex:1 1 auto;min-width:0;" +
          (middleMaxMinHeight > 0 ? "min-height:" + middleMaxMinHeight + "px;" : "min-height:0;");
        // Helper: apply layout.height/min_height/max_height to middle row child
        // (alLeft/alRight/alClient). align-items:stretch dela equal height jen
        // pokud zadny child nema explicit height OR vsichni maji stejnou.
        // Krok 5-B: respect layout.height pokud user explicit set + min/max.
        //
        // Krok 5-B (29.5.2026 odpoledne, Marti's "Panel left nerespektuje
        // svuj sandbox a prelejza svoje hranice"): force box-sizing:border-box
        // + drop vertical margin pro middle row children. Default content-box
        // pridava padding+border MIMO height (300px → ~326px rendered).
        // Plus prodPaddingStyle ma margin:6px 0; ktery pridava +12px svisle.
        // Result: panel s height:300 visual = 300+border+padding+margin = ~338px
        // → overflow z middle row 300px.
        //
        // Fix: box-sizing:border-box (height includes padding+border) +
        // margin-top:0 + margin-bottom:0 (drop vertical margin). Horizontal
        // margin zustava (panel-to-panel gap mezi alLeft/alClient/alRight).
        const _applyHeightConstraints = (el, c) => {
          const layout = c.layout || {};
          // Force border-box + drop vertical margin pro precise height respekt
          el.style.boxSizing = "border-box";
          el.style.marginTop = "0";
          el.style.marginBottom = "0";
          if (layout.height != null && layout.height !== "auto") {
            const v = (typeof layout.height === "number") ? layout.height + "px" : String(layout.height);
            el.style.height = v;
          }
          if (layout.min_height != null) {
            const m = (typeof layout.min_height === "number") ? layout.min_height + "px" : String(layout.min_height);
            el.style.minHeight = m;
          }
          if (layout.max_height != null && layout.max_height !== "auto") {
            const mx = (typeof layout.max_height === "number") ? layout.max_height + "px" : String(layout.max_height);
            el.style.maxHeight = mx;
          }
        };
        // Krok 5-B (29.5.2026 vecer, Marti's TUserGroupBox Object Inspector
        // screenshot Anchors=[akLeft, akTop, akBottom]): Delphi Anchors
        // property RIDI stretching behavior. akTop+akBottom = vertical
        // stretch pres parent vysku. Bez akBottom = fixed Height (intrinsic
        // OR explicit layout.height).
        //
        // Defaults per Align (Delphi typical):
        //   alLeft   → [left, top, bottom]    (vertical strip stretch)
        //   alRight  → [right, top, bottom]   (vertical strip stretch)
        //   alClient → [left, top, right, bottom] (all stretch)
        //   alTop    → [left, top, right]     (horizontal strip)
        //   alBottom → [left, right, bottom]  (horizontal strip)
        const _ANCHOR_DEFAULTS_RENDER = {
          left: ["left", "top", "bottom"],
          right: ["right", "top", "bottom"],
          top: ["left", "top", "right"],
          bottom: ["left", "right", "bottom"],
          client: ["left", "top", "right", "bottom"],
          none: ["left", "top"],
        };
        const _resolveAnchors = (c) => {
          const layout = c && c.layout || {};
          if (Array.isArray(layout.anchors) && layout.anchors.length > 0) {
            return layout.anchors.map(a => String(a).toLowerCase());
          }
          const align = String(layout.align || "client").toLowerCase();
          return _ANCHOR_DEFAULTS_RENDER[align] || ["left", "top"];
        };
        // Apply vertical stretching based on anchors
        // - akTop + akBottom → height:100% (stretch vertically across parent)
        // - akTop only       → align-self:flex-start (snap to top, fixed h)
        // - akBottom only    → align-self:flex-end (snap to bottom, fixed h)
        // - neither          → align-self:center
        const _applyVerticalAnchors = (el, c) => {
          const layout = c && c.layout || {};
          // Pokud user nastavil explicit Height, ten prebije anchors stretch
          const hasExplicitHeight = layout.height != null && layout.height !== "auto";
          if (hasExplicitHeight) return;
          const anchors = _resolveAnchors(c);
          const hasTop = anchors.indexOf("top") !== -1;
          const hasBottom = anchors.indexOf("bottom") !== -1;
          if (hasTop && hasBottom) {
            // Stretch vertikalne — height:100% s box-sizing:border-box
            // (z _applyHeightConstraints) zajisti zadny overflow.
            el.style.height = "100%";
            el.style.alignSelf = "stretch";
          } else if (hasTop) {
            el.style.alignSelf = "flex-start";
          } else if (hasBottom) {
            el.style.alignSelf = "flex-end";
          } else {
            el.style.alignSelf = "center";
          }
        };
        // alLeft panels (fixed width, vertical anchors-driven)
        for (const c of byAlign.left) {
          const el = this._renderComponentTree(c, 0, 1);
          if (el) {
            _applySize(el, c, "w");
            _applyHeightConstraints(el, c);
            _applyVerticalAnchors(el, c);
            middle.appendChild(el);
          }
        }
        // alClient panels (fill remaining)
        // Multiple alClient — stack vertically inside flex=1 wrapper
        if (byAlign.client.length > 0) {
          const clientWrap = document.createElement("div");
          clientWrap.className = "erp-design-align-client-wrap";
          clientWrap.style.cssText =
            "display:flex;flex-direction:column;" +
            "flex:1 1 auto;min-width:0;min-height:0;";
          for (const c of byAlign.client) {
            const el = this._renderComponentTree(c, 0, byAlign.client.length);
            if (el) {
              el.style.flex = "1 1 auto";
              el.style.minWidth = "0";
              const layout = c.layout || {};
              if (layout.min_width != null) {
                el.style.minWidth = (typeof layout.min_width === "number")
                  ? layout.min_width + "px" : String(layout.min_width);
              }
              // Krok 5-B (29.5.2026, Marti's "Max width omezit aby
              // nerozthoval pres celou obrazovku"): alClient panel
              // dostane max-width CSS constraint pokud je nastaveno.
              if (layout.max_width != null && layout.max_width !== "auto") {
                el.style.maxWidth = (typeof layout.max_width === "number")
                  ? layout.max_width + "px" : String(layout.max_width);
              }
              // Krok 5-B (29.5.2026, Marti's "panely kazdy jinak vysoky"):
              // Apply height constraints uniformly s alLeft/alRight via helper
              // (height/min_height/max_height). align-items:stretch zajisti
              // equal height napric middle row.
              _applyHeightConstraints(el, c);
              clientWrap.appendChild(el);
            }
          }
          middle.appendChild(clientWrap);
        }
        // alRight panels — parita s alLeft (anchors-driven)
        for (const c of byAlign.right) {
          const el = this._renderComponentTree(c, 0, 1);
          if (el) {
            _applySize(el, c, "w");
            _applyHeightConstraints(el, c);
            _applyVerticalAnchors(el, c);
            middle.appendChild(el);
          }
        }
        wrap.appendChild(middle);
      }

      // alBottom panels (full width strips, stacked bottom)
      for (const c of byAlign.bottom) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          _applySize(el, c, "h");
          el.style.width = "100%";
          wrap.appendChild(el);
        }
      }

      // alNone panels — absolute positioning (Phase A+1 pattern)
      for (const c of byAlign.none) {
        const el = this._renderComponentTree(c, 0, 1);
        if (el) {
          const layout = c.layout || {};
          el.style.position = "absolute";
          if (layout.top != null) {
            el.style.top = (typeof layout.top === "number")
              ? layout.top + "px" : String(layout.top);
          }
          if (layout.left != null) {
            el.style.left = (typeof layout.left === "number")
              ? layout.left + "px" : String(layout.left);
          }
          if (layout.width != null && layout.width !== "auto") {
            el.style.width = (typeof layout.width === "number")
              ? layout.width + "px" : String(layout.width);
          }
          if (layout.height != null && layout.height !== "auto") {
            el.style.height = (typeof layout.height === "number")
              ? layout.height + "px" : String(layout.height);
          }
          wrap.appendChild(el);
        }
      }

      return wrap;
    }

    _renderLeafField(comp, idx, total) {
      const ctx = this.__renderCtx || {};
      const data = ctx.data || {};
      const D = ctx.onDirty || (() => {});

      // Phase CRM Foundation Krok 5-B (28.5.2026 vecer, Marti's "data
      // bez bunek" diagnoza CRM Kontakt edit form): prefer
      // layout.column_name (MSSQL PascalCase column, e.g. "FirmaText")
      // pred comp.name (e.g. "field_kontakt_FirmaText"). Backward compat:
      // legacy forms (user_edit) maji column_name=NULL → fallback na
      // comp.name (matches data klic pres snake_case naming).
      //
      // Doctrine: column_name je zdrojem pravdy pro data binding,
      // comp.name je interni FW identifier (drag-drop, parent_comp_def_id
      // refs). Marti: "PascalCase MSSQL columns musi byt v data dict
      // bez prevodu".
      const dataKey = (comp.layout && comp.layout.column_name) || comp.name;
      const value = data[dataKey];
      const fieldEl = this._renderField(comp, value, D);
      if (!fieldEl) return null;

      // Krok 14b+10 (13.5.2026 ~22:00, Marti's "always-left" property):
      // apply grid-column-start:1 pokud layout.always_new_row === true.
      const alwaysNewRow = !!(comp.layout && comp.layout.always_new_row);

      // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's "sirka komponenty
      // na displeji"): aply layout.min_width / max_width na field wrap.
      // Pozor: drz se v rozumnem range (CSS grid auto-fit reaguje).
      const _applyWidthConstraints = (el) => {
        if (!comp.layout) return;
        if (comp.layout.min_width != null && comp.layout.min_width > 0) {
          el.style.minWidth = comp.layout.min_width + "px";
        }
        if (comp.layout.max_width != null && comp.layout.max_width > 0) {
          el.style.maxWidth = comp.layout.max_width + "px";
        }
      };

      // Krok 14b+8 (13.5.2026 ~20:45): v DESIGN mode wrap field do
      // draggable containeru pro reorder. Plus drag handle.
      // Krok 14c+3.2 (14.5.2026 odp.): DESIGN wrap napric VSEMI panels
      // (Marti's "Lookup v footer nema ikonky").
      if (this._formDesignMode === true) {
        const wrapped = this._wrapFieldForDesign(fieldEl, comp, idx, total);
        if (alwaysNewRow) wrapped.style.gridColumnStart = "1";
        _applyWidthConstraints(wrapped);
        return wrapped;
      } else {
        if (alwaysNewRow) fieldEl.style.gridColumnStart = "1";
        _applyWidthConstraints(fieldEl);
        return fieldEl;
      }
    }

    _renderContainerNode(container) {
      const ctx = this.__renderCtx || {};
      const byParent = ctx.byParent || new Map();
      const code = container.comp_type_code;
      const layout = container.layout || {};
      const children = byParent.get(container.id) || [];

      // ─── PageControl = tabs container ─────────────────────────────
      // Phase 38.4 Krok 14g Etapa F Krok 5.J-B2 (16.5.2026 ~23:50, Marti's
      // "page control jako fw componentu"). Quick scaffold:
      //   - Tab strip nad content area
      //   - Active tabsheet content renders, ostatní hidden
      //   - State: this._activeTabSheets[pagecontrol_id] = active tabsheet_id
      //   - Default = first tabsheet (sort_order ASC)
      //
      // TODO Krok 5.J-B3+: per-tabsheet settings popup (caption edit,
      // sort reorder, add/remove tabsheet via wizard).
      if (code === "pagecontrol") {
        const tabsheets = children.filter(c => c.comp_type_code === "tabsheet");
        if (tabsheets.length === 0) {
          // No tabsheets — render empty placeholder (DESIGN hint)
          const empty = document.createElement("div");
          empty.style.cssText =
            "padding:24px;text-align:center;color:#8a96a4;font-size:12px;" +
            "border:1px dashed #2a3340;border-radius:4px;";
          empty.textContent = "📑 PageControl #" + container.id + " — žádný tabsheet uvnitr.";
          return empty;
        }

        // Active tab state — per pagecontrol id
        if (!this._activeTabSheets) this._activeTabSheets = {};
        const pcId = container.id;
        if (this._activeTabSheets[pcId] == null) {
          this._activeTabSheets[pcId] = tabsheets[0].id;
        }
        let activeTsId = this._activeTabSheets[pcId];
        if (!tabsheets.some(ts => ts.id === activeTsId)) {
          activeTsId = tabsheets[0].id;
          this._activeTabSheets[pcId] = activeTsId;
        }

        // Wrap container
        const pcWrap = document.createElement("div");
        pcWrap.className = "erp-design-pagecontrol";
        pcWrap.dataset.compDefId = String(container.id);
        pcWrap.dataset.compTypeCode = "pagecontrol";
        pcWrap.style.cssText =
          "display:flex;flex-direction:column;gap:0;min-height:0;min-width:0;" +
          "border:1px solid #2a3340;border-radius:4px;background:#0f141a;";

        // Tab strip
        const tabStrip = document.createElement("div");
        tabStrip.style.cssText =
          "display:flex;border-bottom:1px solid #2a3340;background:#0d1117;" +
          "padding:0 8px;gap:0;flex:0 0 auto;";

        // Phase 38.4 Krok 14g Etapa F Krok 5.J-B3 (16.5.2026 ~24:05, Marti's
        // "Prosim o tu parametrizaci Tabsheetu.. Pocet zalozek, Nazvy zalozek"):
        // - Right-click na tab → prompt rename → PATCH caption
        // - ✕ button na tab v DESIGN mode → confirm → PATCH is_active=false
        //   (soft-delete, recursive CTE filtr drop)
        // - Click na tab → switch active (existing)
        const designModePc = this._formDesignMode === true;
        const self = this;

        for (const ts of tabsheets) {
          const isActive = (ts.id === activeTsId);
          const tabBtn = document.createElement("button");
          tabBtn.type = "button";
          tabBtn.dataset.tabsheetId = String(ts.id);
          tabBtn.style.cssText =
            "padding:8px 14px;background:transparent;border:none;outline:none;" +
            "border-bottom:2px solid " + (isActive ? "#7ed4e8" : "transparent") + ";" +
            "color:" + (isActive ? "#e8eef5" : "#8a96a4") + ";" +
            "font-size:13px;font-weight:" + (isActive ? "600" : "400") + ";" +
            "cursor:pointer;transition:color 0.15s, border-color 0.15s;" +
            "display:inline-flex;align-items:center;gap:6px;";

          // Label text span
          const tabLabel = document.createElement("span");
          tabLabel.textContent = ts.caption || ts.name || ("Tab #" + ts.id);
          tabBtn.appendChild(tabLabel);

          // ✕ delete badge (DESIGN only)
          if (designModePc) {
            const delBadge = document.createElement("span");
            delBadge.textContent = "✕";
            delBadge.title = "Smazat záložku (soft delete)";
            delBadge.style.cssText =
              "color:#5a2828;font-size:10px;padding:0 4px;border-radius:2px;" +
              "cursor:pointer;transition:color 0.15s, background 0.15s;";
            delBadge.addEventListener("mouseenter", () => {
              delBadge.style.color = "#e57373";
              delBadge.style.background = "#1f1010";
            });
            delBadge.addEventListener("mouseleave", () => {
              delBadge.style.color = "#5a2828";
              delBadge.style.background = "transparent";
            });
            delBadge.addEventListener("click", async (ev) => {
              ev.stopPropagation();
              const decision = await _confirmDarkDialog({
                title: "Smazat záložku",
                message: "Opravdu smazat záložku \"" + (ts.caption || ts.name) +
                  "\"?\n\n(soft delete — komponenty uvnitř zůstanou v DB ale " +
                  "z formu zmizí. Lze obnovit přes is_active=true.)",
              });
              if (decision !== true) return;
              try {
                const r = await fetch(
                  "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(ts.id),
                  {
                    method: "PATCH",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_active: false }),
                  }
                );
                if (!r.ok) {
                  const eb = await r.json().catch(() => ({}));
                  throw new Error(eb.error || ("HTTP " + r.status));
                }
                // Pokud byl smazaný aktivní → switch na první remaining
                if (self._activeTabSheets[pcId] === ts.id) {
                  delete self._activeTabSheets[pcId];  // re-default on next render
                }
                if (typeof _showToast === "function") {
                  _showToast("Záložka smazána", "success", 2000);
                }
                await self._reloadSpec();
              } catch (e) {
                console.error("[pagecontrol] delete tabsheet failed:", e);
                if (typeof _showToast === "function") {
                  _showToast("Smazání selhalo: " + (e.message || e), "error", 3500);
                }
              }
            });
            tabBtn.appendChild(delBadge);
          }

          // Click → switch active tab
          tabBtn.addEventListener("click", () => {
            this._activeTabSheets[pcId] = ts.id;
            this._render();
          });

          // Phase 38.4 Krok 14g Etapa F Krok 5.J-B5 (16.5.2026 ~24:35, Marti's
          // "Zvladnes dodelat na tom page control presouvani komponent z jedne
          // do druhe zalozky? Drop?"): tab button = drop target pro fields.
          // Drag field/container z aktivního tabu → drop na **neaktivní** tab
          // → PATCH parent_comp_def_id = drop_target_ts.id → re-parent
          // komponenta do drop tabsheet. Existing _wrapFieldForDesign +
          // _attachContainerDragEvents sets text/plain = component id.
          if (designModePc) {
            tabBtn.addEventListener("dragover", (ev) => {
              // Allow drop pokud máme nějaký drag state (field nebo container)
              if (!self._dragState && !self._containerDragState) return;
              ev.preventDefault();
              ev.dataTransfer.dropEffect = "move";
              tabBtn.style.background = "#1a2632";
              tabBtn.style.borderBottomColor = "#5dbf5d";  // green = drop accept
            });
            tabBtn.addEventListener("dragleave", () => {
              tabBtn.style.background = "transparent";
              tabBtn.style.borderBottomColor = (ts.id === activeTsId) ? "#7ed4e8" : "transparent";
            });
            tabBtn.addEventListener("drop", async (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              tabBtn.style.background = "transparent";
              tabBtn.style.borderBottomColor = (ts.id === activeTsId) ? "#7ed4e8" : "transparent";
              const rawId = ev.dataTransfer.getData("text/plain");
              const draggedId = parseInt(rawId, 10);
              if (!draggedId || isNaN(draggedId)) {
                console.warn("[pagecontrol drop] no valid dragged id:", rawId);
                return;
              }
              // Self-drop guard: pokud field uz patri tomuto tabsheetu, skip
              // (need to look up — but easier just attempt PATCH; backend
              // is idempotent for same parent_comp_def_id, succeeds silently)
              try {
                const r = await fetch(
                  "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(draggedId),
                  {
                    method: "PATCH",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ parent_comp_def_id: ts.id }),
                  }
                );
                if (!r.ok) {
                  const eb = await r.json().catch(() => ({}));
                  throw new Error(eb.error || ("HTTP " + r.status));
                }
                if (typeof _showToast === "function") {
                  _showToast(
                    "Komponenta přesunuta do \"" + (ts.caption || ts.name) + "\"",
                    "success", 2000
                  );
                }
                // Switch active na drop-target tab pro visual feedback
                self._activeTabSheets[pcId] = ts.id;
                await self._reloadSpec();
              } catch (e) {
                console.error("[pagecontrol drop] re-parent failed:", e);
                if (typeof _showToast === "function") {
                  _showToast("Přesun selhal: " + (e.message || e), "error", 3500);
                }
              }
            });
          }

          // Right-click → prompt rename (DESIGN only)
          if (designModePc) {
            tabBtn.addEventListener("contextmenu", async (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              const newCaption = prompt("Nový název záložky:", ts.caption || "");
              if (newCaption == null) return;  // cancel
              const trimmed = newCaption.trim();
              if (!trimmed) {
                if (typeof _showToast === "function") {
                  _showToast("Název nesmí být prázdný", "error", 2500);
                }
                return;
              }
              if (trimmed === (ts.caption || "")) return;  // no change
              try {
                const r = await fetch(
                  "/api/v1/erp/design/comp-def/update/" + encodeURIComponent(ts.id),
                  {
                    method: "PATCH",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ caption: trimmed }),
                  }
                );
                if (!r.ok) {
                  const eb = await r.json().catch(() => ({}));
                  throw new Error(eb.error || ("HTTP " + r.status));
                }
                if (typeof _showToast === "function") {
                  _showToast("Záložka přejmenována", "success", 2000);
                }
                await self._reloadSpec();
              } catch (e) {
                console.error("[pagecontrol] rename tabsheet failed:", e);
                if (typeof _showToast === "function") {
                  _showToast("Přejmenování selhalo: " + (e.message || e), "error", 3500);
                }
              }
            });
          }

          tabStrip.appendChild(tabBtn);
        }

        // Phase 38.4 Krok 14g Etapa F Krok 5.J-B4 (16.5.2026 ~24:25, Marti's
        // "Prosim jeste pridani zalozky sheetu"): ➕ Add new tab button
        // na konec tab strip (DESIGN only). Click → prompt caption →
        // POST /design/comp-def s parent_comp_def_id=pagecontrol.id.
        if (designModePc) {
          const addBtn = document.createElement("button");
          addBtn.type = "button";
          addBtn.textContent = "➕";
          addBtn.title = "Přidat novou záložku";
          addBtn.style.cssText =
            "padding:8px 12px;background:transparent;border:none;outline:none;" +
            "color:#5dbf5d;font-size:14px;font-weight:600;cursor:pointer;" +
            "margin-left:auto;transition:background 0.15s;";
          addBtn.addEventListener("mouseenter", () => {
            addBtn.style.background = "#0a1410";
          });
          addBtn.addEventListener("mouseleave", () => {
            addBtn.style.background = "transparent";
          });
          addBtn.addEventListener("click", async () => {
            const caption = prompt("Název nové záložky:", "Nový tab");
            if (caption == null) return;  // cancel
            const trimmed = caption.trim();
            if (!trimmed) {
              if (typeof _showToast === "function") {
                _showToast("Název nesmí být prázdný", "error", 2500);
              }
              return;
            }
            // type_id z first existing tabsheet (fallback 16 = Krok 13 Delphi compat)
            const tabsheetTypeId = (tabsheets[0] && tabsheets[0].type_id) || 16;
            // Unique name (idempotency check je na parent+name+region, takže timestamp suffix garantuje)
            const uniqueName = "tab_" + Date.now();
            try {
              const r = await fetch("/api/v1/erp/design/comp-def", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  parent_comp_def_id: pcId,
                  name: uniqueName,
                  caption: trimmed,
                  type_id: tabsheetTypeId,
                  region_slot: "main",
                  // sort_order: auto-set backend (max + 10)
                }),
              });
              if (!r.ok) {
                const eb = await r.json().catch(() => ({}));
                throw new Error(eb.error || ("HTTP " + r.status));
              }
              const respData = await r.json();
              const newTsId = respData.comp_def_id;
              if (typeof _showToast === "function") {
                _showToast("Záložka přidána", "success", 2000);
              }
              // Switch active na nový tab (pres _reloadSpec ho ukáže)
              if (newTsId) {
                self._activeTabSheets[pcId] = newTsId;
              }
              await self._reloadSpec();
            } catch (e) {
              console.error("[pagecontrol] add new tab failed:", e);
              if (typeof _showToast === "function") {
                _showToast("Přidání selhalo: " + (e.message || e), "error", 3500);
              }
            }
          });
          tabStrip.appendChild(addBtn);
        }

        pcWrap.appendChild(tabStrip);

        // Content area — render active tabsheet children
        const contentArea = document.createElement("div");
        contentArea.style.cssText =
          "flex:1 1 auto;padding:12px;display:flex;flex-direction:column;" +
          "gap:8px;min-height:0;min-width:0;overflow:auto;";

        const activeTs = tabsheets.find(ts => ts.id === activeTsId);
        if (activeTs) {
          const tsChildren = byParent.get(activeTs.id) || [];
          for (let i = 0; i < tsChildren.length; i++) {
            const childEl = this._renderComponentTree(tsChildren[i], i, tsChildren.length);
            if (childEl) contentArea.appendChild(childEl);
          }
        }
        pcWrap.appendChild(contentArea);
        return pcWrap;
      }

      // ─── TabSheet = wrapper INSIDE pagecontrol ────────────────────
      // Rendered as standalone JEN pokud nekdo nas zavola mimo pagecontrol
      // kontextu (tj. byParent lookup vrati tabsheet jako top-level child).
      // Pagecontrol branch above renders tabsheet children directly v contentArea,
      // takze tato vetev je fallback pro orphan tabsheet.
      if (code === "tabsheet") {
        const orphanWrap = document.createElement("div");
        orphanWrap.style.cssText =
          "padding:12px;border:1px dashed #5a4828;border-radius:4px;" +
          "color:#d4b88a;font-size:11px;background:#1a1410;";
        orphanWrap.textContent = "⚠ Orphan tabsheet #" + container.id + " — " +
          (container.caption || container.name) +
          " (musi byt child pagecontrol komponenty)";
        return orphanWrap;
      }

      // ─── Panel = structural container ─────────────────────────────
      // Marti's doctrine (Krok 14e, 14.5.2026 vecer): panel je purely
      // structural — visual styling delegujeme na nested groupbox.
      //
      // V PROD mode: display:contents (panel se "rozpusti", children
      //   prevzimaji grid placement of parent sec.grid → groupbox je
      //   prime dite sec.grid grid-column:1/-1).
      // V DESIGN mode (Krok 14e-E, 14.5. vecer): visible wrapper
      //   s dashed border + drag handle pro reorder + child grid
      //   sections uvnitr panelu (Marti's Q3 — child grids "patri na panel").
      if (code === "panel") {
        const designMode = this._formDesignMode === true;
        const wrap = document.createElement("div");
        wrap.className = "erp-design-panel";
        wrap.dataset.compDefId = String(container.id);
        wrap.dataset.compTypeCode = "panel";
        wrap.dataset.parentCompDefId = String(container.parent_comp_def_id || "");

        // Phase 38.4 Krok 14f-B (14.5.2026 vecer): panel ma display:flex
        // v obou modes — wrapper musi byt flex item kvuli _buildAlignLayout
        // flex:1 sizing. display:contents (drive Krok 14e-E) ze rusi flex
        // styling (no box). Switch na display:flex column.
        //
        // Phase 38.4 Krok 14f-N (14.5.2026 vecer, Marti's "3 komponenty
        // vedle sebe"): pokud panel ma direct leaf fields (no groupbox/
        // panel children), apply CSS grid auto-fit pro side-by-side layout.
        // Pokud panel ma container children (groupbox), zustane flex column
        // (groupbox samotny dela inner grid).
        // Krok 5.Z (30.5.2026, Marti's "nejde roztahnout pres alClient"):
        // embedded grid_modern child potrebuje flex-column panel (NE implicit
        // CSS grid), jinak grid sec.wrap flex:1 nema flex kontext a nezvetsi
        // se na vysku panelu. grid_modern proto NENI "leaf field" pro layout
        // ucely — chova se jako container child (drzi panel flex-column).
        const hasGridChild = children.some(c => c.comp_type_code === "grid_modern");
        const hasContainerChild = children.some(c =>
          c.comp_type_code === "panel" || c.comp_type_code === "groupbox"
        );
        const hasLeafChild = children.some(c =>
          c.comp_type_code !== "panel" && c.comp_type_code !== "groupbox" &&
          c.comp_type_code !== "grid_modern"
        );
        const useImplicitGrid = !hasContainerChild && !hasGridChild && hasLeafChild;
        // Krok 5-B (29.5.2026 odpoledne, Marti's "panel prelejza svoje
        // hranice"): box-sizing:border-box univerzalne pro panel wraps —
        // pokud user nastavi Height/Max width, hodnota INCLUDES padding+border
        // (predtim content-box = explicit height byl jen content, padding +
        // border + margin se pridavaly NAD a vedlo to k overflow).
        // Krok 5.Z (30.5.2026, Marti's "fieldy alignovat up, nikoli alClient —
        // nahustene od shora jako v Komunikace"): align-content:start. Default
        // CSS grid align-content se chova jako stretch -> radky se roztahnou na
        // vysku panelu (ten je v middle-row align-items:stretch stejne vysoky
        // jako sousedi) a fieldy (align-items:start) zustanou nahore zvetsenych
        // bunek = mezery. align-content:start radky nahusti nahoru, prazdne
        // misto zustane dole.
        const baseStyle = useImplicitGrid
          ? "display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));" +
            "gap:6px 14px;align-items:start;align-content:start;min-width:0;position:relative;" +
            "box-sizing:border-box;"
          : "display:flex;flex-direction:column;min-height:0;min-width:0;position:relative;" +
            "box-sizing:border-box;";

        // Phase CRM Foundation Krok 5-B (28.5.2026 vecer, Marti's "zaktivnit
        // viditelne Label a viditelny ramecek a linku nahore dle nastaveni
        // parametru"): panel teted respektuje layout.border_mode + caption.
        //   - border_mode='all'  → full ramecek + caption jako inset label
        //                          (left-top corner, na border)
        //   - border_mode='top'  → linka nahore + caption inline nad
        //   - border_mode='none' → invisible (current behavior, default)
        //   - caption empty      → border ANO, ale bez labelu
        //
        // V DESIGN mode: PROD styling se aplikuje (uzivatel vidi vysledek)
        //   + DESIGN identifier overlay (▦ panel #ID tag v rohu).
        //
        // Pattern paralele groupbox vetev pod (analog styling). Drz Marti's
        // doctrine "uniformita vítězí" — panel + groupbox sdileji visual
        // border pattern, lisí se chovanim children (panel = structural
        // container pro alClient layout, groupbox = visual grouping).
        const panelBorderMode = (layout.border_mode || "none").toLowerCase();
        const panelCaption = (container.caption != null && String(container.caption).trim().length > 0)
          ? String(container.caption).trim()
          : null;

        // PROD styling — applies v obou modes (DESIGN dostane identifier overlay
        // jako dodatek, ne místo PROD border)
        let prodBorderStyle = "";
        let prodPaddingStyle = "";
        // Phase 38.4 Krok 5-B Fix #8 (29.5.2026 pozde, Marti's "Mod All
        // prepiseme na Top-Right - linka nahore a vpravo a aplikujeme
        // stejnym zpusobem"): border_mode="all" mení vizuál z plného
        // ramečku (border+border-radius) na top+right edges only.
        // Zachováváme enum value "all" pro zpětnou kompatibilitu s DB,
        // jen měníme jeho vizuální interpretaci.
        //
        // Fix #8+ (29.5.2026 pozde): Marti's "ta linka vpravo se posunula
        // kousek doleva, JEN TA LINKA (ne nadpis), a nahore bude
        // zacinat soucasne s textem (nebude az nahoru)". Border-right
        // se drop z inline stylu, nahrazeno absolute positioned child
        // div nize (panel.cssText drop border-right). Padding-right se
        // zvetsi aby content nekolidoval s inset right line.
        if (panelBorderMode === "all") {
          prodBorderStyle = "border-top:1px solid #2a3340;";
          prodPaddingStyle = panelCaption
            ? "padding:6px 18px 4px 0;margin:6px 0 0 0;"
            : "padding:10px 18px 4px 0;margin:6px 0 0 0;";
        } else if (panelBorderMode === "top") {
          prodBorderStyle = "border-top:1px solid #2a3340;";
          prodPaddingStyle = panelCaption
            ? "padding:6px 0 4px 0;margin:6px 0 0 0;"
            : "padding:10px 0 4px 0;margin:6px 0 0 0;";
        }
        // 'none' → no border, no extra padding

        if (designMode) {
          // DESIGN: PROD styling + DESIGN identifier overlay (dashed outline
          // around the panel for boundary visibility). Krok H+7 (26.5.2026):
          // draggable DROPPED — reorder pres palette ↑/↓.
          //
          // Pokud panel ma border_mode='all' nebo 'top', zachova PROD border
          // + pridame subtle dashed outline jako DESIGN identifier.
          // Pokud panel ma border_mode='none', dashed outline funguje jako
          // jediny visual marker (current behavior preserved).
          const designIdentifierBorder = (panelBorderMode === "none")
            ? "border:1px dashed rgba(122, 134, 150, 0.3);border-radius:4px;"
            : prodBorderStyle + "outline:1px dashed rgba(122, 134, 150, 0.3);outline-offset:2px;";
          const designPadding = (panelBorderMode === "none")
            ? "padding:8px;margin:2px;"
            : prodPaddingStyle;
          wrap.style.cssText = baseStyle + designIdentifierBorder + designPadding;

          // PROD caption (pokud caption + border_mode != 'none') — zobrazime
          // jako PROD by ji vykreslila, ne jako DESIGN identifier
          if (panelCaption && panelBorderMode !== "none") {
            const prodLbl = document.createElement("div");
            prodLbl.className = "erp-design-panel-label";
            prodLbl.textContent = panelCaption;
            prodLbl.style.cssText =
              "display:block;" +
              "background:transparent;" +
              "color:#8b95a5;" +
              "font-size:11px;" +
              "font-weight:600;" +
              "text-transform:uppercase;" +
              "letter-spacing:0.5px;" +
              "padding:0;" +
              "margin:0 0 8px 0;";
            wrap.appendChild(prodLbl);
          }

          // DESIGN identifier "panel" v levem hornim rohu — clickable pro
          // settings (Krok 14f-D). Zustava i pri PROD borderu — slouzi jako
          // identifier ne label.
          const lbl = document.createElement("div");
          const alignLabel = (container.layout && container.layout.align) || "client";
          lbl.textContent = "▦ panel #" + container.id + " · " + alignLabel + " ⚙";
          lbl.title = "Klikni pro nastaveni panelu (nebo right-click)";
          lbl.style.cssText =
            "position:absolute;top:-8px;right:8px;" +  // top-right corner (vlevo je teted PROD caption)
            "background:#0d1117;color:#5d6975;" +
            "font-size:10px;padding:2px 8px;" +
            "border-radius:2px;letter-spacing:0.5px;" +
            "user-select:none;cursor:pointer;z-index:2;" +
            "transition:color 0.15s, background 0.15s;";
          lbl.addEventListener("mouseenter", () => {
            lbl.style.color = "#a88cd4";
            lbl.style.background = "#1a2028";
          });
          lbl.addEventListener("mouseleave", () => {
            lbl.style.color = "#5d6975";
            lbl.style.background = "#0d1117";
          });
          lbl.addEventListener("click", (ev) => {
            ev.stopPropagation();
            this._openFieldSettings(container);
          });
          // Krok H+8.1 (26.5.2026): dblclick handler DROPPED — reverse
          // orchestrace je teted pres document-level hover/click v open()
          // (Marti's "intuitivnejsi pres hover + persistent click").
          wrap.appendChild(lbl);

          // Right-click handler — open settings popup (Krok 14f-D)
          wrap.addEventListener("contextmenu", (ev) => {
            // Skip pokud klik na child interactive element (input/button)
            const tag = ev.target && ev.target.tagName;
            if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA" || tag === "SELECT") {
              return;  // necht browser default kontextmenu chodi
            }
            ev.preventDefault();
            ev.stopPropagation();
            this._openFieldSettings(container);
          });

          // Krok H+7 (26.5.2026): drag listeners DROPPED — Marti's
          // "form se bude chovat jako v production". Container reorder
          // se nyni dela pres palette ↑/↓ buttons. Label tag + dashed
          // border zustavaji jako DESIGN-only identifier (ne grip).
        } else {
          // PROD: aplikujeme border_mode + caption styling
          wrap.style.cssText = baseStyle + prodBorderStyle + prodPaddingStyle;

          // PROD caption (pokud caption + border_mode != 'none')
          if (panelCaption && panelBorderMode !== "none") {
            const prodLbl = document.createElement("div");
            prodLbl.className = "erp-design-panel-label";
            prodLbl.textContent = panelCaption;
            prodLbl.style.cssText =
              "display:block;" +
              "background:transparent;" +
              "color:#8b95a5;" +
              "font-size:11px;" +
              "font-weight:600;" +
              "text-transform:uppercase;" +
              "letter-spacing:0.5px;" +
              "padding:0;" +
              "margin:0 0 8px 0;";
            wrap.appendChild(prodLbl);
          }
        }

        // Fix #8+ (29.5.2026 pozde, Marti's "linka vpravo se posunula
        // kousek doleva ... nahore bude zacinat soucasne s textem"):
        // pro Top-Right mode pridame inset right line jako absolute
        // positioned child. Border-right z inline stylu wrap byl dropped
        // (viz prodBorderStyle pro 'all' mode vyse). Caption (nadpis)
        // zustava na svém miste — JEN linka se posune. Top:22px sedi
        // priblizne na urovni caption text top (po padding-top:6px +
        // caption font-size:11px line-height ~1.4 = ~21px baseline).
        if (panelBorderMode === "all") {
          wrap.style.position = "relative";
          const rightLine = document.createElement("div");
          rightLine.className = "erp-design-panel-right-line";
          rightLine.style.cssText =
            "position:absolute;" +
            "top:6px;" +
            "right:10px;" +
            "bottom:0;" +
            "width:1px;" +
            "background:#2a3340;" +
            "pointer-events:none;";
          wrap.appendChild(rightLine);
        }

        // Phase 38.4 Krok 14e-G (Marti's Q3, volba A memory-only):
        // Child sections (TELEFONY/EMAILY) jsou UVNITR panelu, ne paralelne.
        //
        // Phase 38.4 Krok 14f-G fix (14.5.2026 vecer, Marti's "dropnul
        // jsem novy panel, zkopirovaly se gridy"): render child sections
        // JEN v prvnim alClient panelu. Pokud Marti pridal alTop/alBottom/
        // alLeft/alRight panel, child sections zustavaji v alClient
        // (canonical main area — Delphi alClient = "remaining space").
        const isClientAlign = ((container.layout && container.layout.align) || "client") === "client";
        const shouldRenderChildren = isClientAlign && !this._childrenRenderedInAnyPanel;
        if (shouldRenderChildren) {
          this._childrenRenderedInAnyPanel = true;  // mark for subsequent panels
        }

        // Krok 5.X (27.5.2026, Marti's "Jsou to normalni komponenty"):
        // Nested grids jsou teted fw.comp_def rows (type=nested_grid),
        // children k panelu pres parent_comp_def_id. Render loop dispatch:
        //   - nested_grid type → _renderChildSection(layout.child_key, childrenData[key])
        //   - jine typy        → _renderComponentTree (existing recursive render)
        // Sort_order na comp_def nahrazuje _childPosition / _childOrder /
        // _childHidden (sort_order + is_active jsou v DB).
        //
        // Backward compat: pokud children-only legacy fallback (form bez
        // Krok 5.X DDL) → backend nevrati comp_def_id v childrenData[key],
        // a tyto children NEJSOU v `children` array. Pojď rerender legacy
        // memory-only flow (before-main pre-loop) pokud detected.
        const childrenData = (this._spec && this._spec.children) || {};
        const _legacyKeys = Object.keys(childrenData).filter(
          (k) => childrenData[k] && childrenData[k].comp_def_id == null
        );
        if (shouldRenderChildren && _legacyKeys.length > 0) {
          // Legacy memory-only fallback (no Krok 5.X DDL on this form)
          for (const childKey of _legacyKeys) {
            const childInfo = childrenData[childKey];
            if (!childInfo) continue;
            const sec = this._renderChildSection(childKey, childInfo);
            if (sec) wrap.appendChild(sec);
          }
        }

        // Render container children — Krok 5.X dispatch nested_grid → child section.
        //
        // Krok 5-B (29.5.2026 dopoledne, Marti's "PANEL TOP LEFT align=left
        // se taze pres celou sirku ne strip vlevo"): Detect Delphi-style
        // align mix v container children (panel/groupbox/tabsheet s align
        // left/right/top/bottom). Pokud ano, route pres _buildAlignLayout
        // (Delphi alignment reservations). Jinak simple loop (legacy).
        //
        // Pattern: alLeft+alClient siblings musi byt v flex-row layoutu,
        // ne stack vertikalne. _buildAlignLayout handles reservations
        // (alLeft + alRight reserved on sides, alClient fills remaining).
        const _DELPHI_ALIGNS = new Set(["left", "right", "top", "bottom"]);
        const _regularChildren = [];
        const _nestedGridChildren = [];
        for (const childComp of children) {
          if (childComp && childComp.comp_type_code === "nested_grid") {
            _nestedGridChildren.push(childComp);
          } else {
            _regularChildren.push(childComp);
          }
        }
        const _needsAlignLayout = _regularChildren.some(c => {
          const a = String((c && c.layout && c.layout.align) || "client").toLowerCase();
          return _DELPHI_ALIGNS.has(a);
        });

        if (_needsAlignLayout && _regularChildren.length > 0) {
          // Delphi align layout: route children pres _buildAlignLayout
          // ktery generuje top-strip + middle-row(left+client+right) + bottom-strip.
          // Wrap si zachova flex-column (top → middle → bottom stacking).
          // Need: wrap.style override na flex column (drop implicit grid).
          wrap.style.display = "flex";
          wrap.style.flexDirection = "column";
          wrap.style.minHeight = "0";
          wrap.style.minWidth = "0";
          const alignLayout = this._buildAlignLayout(_regularChildren);
          if (alignLayout) wrap.appendChild(alignLayout);
        } else {
          // Legacy simple loop — children appendovany direct (stack vertikalne
          // nebo implicit grid podle useImplicitGrid baseStyle).
          for (let i = 0; i < _regularChildren.length; i++) {
            const childComp = _regularChildren[i];
            const childEl = this._renderComponentTree(childComp, i, _regularChildren.length);
            if (childEl) wrap.appendChild(childEl);
          }
        }

        // Nested grids (TELEFONY/EMAILY pres fw.comp_def kind='container'):
        // appendovat AFTER align layout (or after legacy loop). Marti's
        // pattern z 27.5. - nested grids patri pod regular components.
        for (const childComp of _nestedGridChildren) {
          const lay = childComp.layout || {};
          const childKey = lay.child_key;
          const childInfo = childKey ? childrenData[childKey] : null;
          if (childInfo) {
            const sec = this._renderChildSection(childKey, childInfo);
            if (sec) wrap.appendChild(sec);
          } else {
            console.warn(
              "[DesignFwForm] nested_grid #" + childComp.id +
              " has no childInfo (child_key=" + childKey +
              ", available: " + Object.keys(childrenData).join(",") + ")"
            );
          }
        }

        return wrap;
      }

      // ─── Groupbox = visual border-top + optional label ────────────
      // Marti's 14.5. vecer doctrine: 2 border_mode varianty
      //   - 'top'  → linka nahore + optional label uvnitr (modern, default)
      //   - 'all'  → full ramecek (classic Delphi compat)
      // layout.label (NULL = bez labelu).
      //
      // Phase 38.4 Krok 14f-P (14.5.2026 vecer, Marti's "ja jsem si to
      // ponicil... vlozil jsem tam groupbox, neni nikde videt... muzes
      // ho zviditelnit a umoznit parametrizaci a smazani"):
      // V DESIGN mode pridat dashed wrapper + label tag (▦ groupbox #ID ⚙)
      // + drag handle. Analog panel wrapper pattern.
      if (code === "groupbox") {
        const designMode = this._formDesignMode === true;
        const wrap = document.createElement("div");
        wrap.className = "erp-design-groupbox";
        wrap.dataset.compDefId = String(container.id);
        wrap.dataset.compTypeCode = "groupbox";

        const borderMode = (layout.border_mode || "top").toLowerCase();
        const labelText = (layout.label != null && String(layout.label).trim().length > 0)
          ? String(layout.label).trim()
          : null;

        if (designMode) {
          // DESIGN: visible wrapper s dashed border + drag + settings affordance.
          // Drop PROD-only border-top / 'all' ramecek — DESIGN overlay je
          // dashed gray identifier. Po prepnuti na PROD se zobrazi PROD
          // styling (border-top nebo full ramecek) podle layout.border_mode.
          wrap.style.cssText =
            "display:flex;flex-direction:column;" +
            "border:1px dashed rgba(212, 184, 138, 0.4);" +  // amber dashed
            "border-radius:4px;" +
            "padding:14px 8px 8px 8px;" +
            "margin:8px 0 2px 0;" +
            "grid-column:1/-1;" +
            "min-width:0;position:relative;";
          // Krok H+7 (26.5.2026): wrap.draggable DROPPED.

          // Label tag v levem hornim rohu — clickable settings
          const tag = document.createElement("div");
          const labelDisplay = labelText
            ? labelText
            : "(no label)";
          tag.textContent = "▦ groupbox #" + container.id + " · " + labelDisplay + " ⚙";
          tag.title = "Klikni pro nastaveni groupboxu (nebo right-click)";
          tag.style.cssText =
            "position:absolute;top:-8px;left:8px;" +
            "background:#0d1117;color:#d4b88a;" +
            "font-size:10px;padding:2px 8px;" +
            "border-radius:2px;letter-spacing:0.5px;" +
            "user-select:none;cursor:pointer;z-index:2;" +
            "transition:color 0.15s, background 0.15s;";
          tag.addEventListener("mouseenter", () => {
            tag.style.color = "#a88cd4";
            tag.style.background = "#1a2028";
          });
          tag.addEventListener("mouseleave", () => {
            tag.style.color = "#d4b88a";
            tag.style.background = "#0d1117";
          });
          tag.addEventListener("click", (ev) => {
            ev.stopPropagation();
            this._openFieldSettings(container);
          });
          // Krok H+8.1 (26.5.2026): dblclick handler DROPPED — orchestrace
          // teted centralized v open() pres mouseover/click (hover + select).
          wrap.appendChild(tag);

          // Right-click handler — open settings popup (Krok 14f-D)
          wrap.addEventListener("contextmenu", (ev) => {
            const tg = ev.target && ev.target.tagName;
            if (tg === "INPUT" || tg === "BUTTON" || tg === "TEXTAREA" || tg === "SELECT") {
              return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            this._openFieldSettings(container);
          });

          // Krok H+7 (26.5.2026): drag listeners DROPPED. Reorder pres
          // palette ↑/↓ buttons (Krok H+5/H+6). Label tag + dashed border
          // zustavaji jako DESIGN-only identifier — bez drag affordance.
        } else {
          // PROD mode: existing visual styling (border-top / 'all')
          // 29.5.2026: padding-top reduced to 6px when labelText present
          // → caption sedi tesne pod border line (Marti's "hned pod tu linku")
          // Fix #8 (29.5.2026 pozde): 'all' mení vizuál z plného ramečku
          // na top+right edges only (Marti's "Mod All prepiseme na Top-Right").
          // Fix #8+: border-right drop z cssText (replaced by inset
          // positioned child div nize). Padding-right zvetsen na 18px
          // aby content nekolidoval s inset right line.
          if (borderMode === "all") {
            wrap.style.cssText =
              "border-top:1px solid #2a3340;" +
              (labelText ? "padding:6px 18px 4px 0;" : "padding:10px 18px 4px 0;") +
              "margin:6px 0 0 0;" +
              "grid-column:1/-1;";
          } else {
            // 'top' default — jen linka nahore, padding-top
            wrap.style.cssText =
              "border-top:1px solid #2a3340;" +
              (labelText ? "padding:6px 0 4px 0;" : "padding:10px 0 4px 0;") +
              "margin:6px 0 0 0;" +
              "grid-column:1/-1;";
          }

          // Optional label (PROD: subtle uppercase legend)
          if (labelText) {
            const lbl = document.createElement("div");
            lbl.className = "erp-design-groupbox-label";
            lbl.textContent = labelText;
            lbl.style.cssText =
              "display:block;" +
              "background:transparent;" +
              "color:#8b95a5;" +
              "font-size:11px;" +
              "font-weight:600;" +
              "text-transform:uppercase;" +
              "letter-spacing:0.5px;" +
              "padding:0;" +
              "margin:0 0 8px 0;";
            wrap.appendChild(lbl);
          }

          // Fix #8+ (29.5.2026 pozde): pro Top-Right mode pridame
          // inset right line jako absolute positioned child. Caption
          // (label) zustava na svém miste — JEN linka se posune.
          // Top:22px sedi priblizne na urovni label text top.
          if (borderMode === "all") {
            wrap.style.position = "relative";
            const rightLine = document.createElement("div");
            rightLine.className = "erp-design-groupbox-right-line";
            rightLine.style.cssText =
              "position:absolute;" +
              "top:22px;" +
              "right:10px;" +
              "bottom:0;" +
              "width:1px;" +
              "background:#2a3340;" +
              "pointer-events:none;";
            wrap.appendChild(rightLine);
          }
        }

        // Inner grid pro children — same layout jako sec.grid (2 cols, auto)
        const inner = document.createElement("div");
        inner.className = "erp-design-groupbox-inner";
        inner.style.cssText =
          "display:grid;" +
          "grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));" +
          "gap:6px 14px;" +
          "align-items:start;";
        wrap.appendChild(inner);

        for (let i = 0; i < children.length; i++) {
          const childEl = this._renderComponentTree(children[i], i, children.length);
          if (childEl) inner.appendChild(childEl);
        }

        return wrap;
      }

      // Unknown container code — defensive: render jako transparent wrapper
      console.warn("[DesignFwForm] Unknown container code:", code, container);
      const fallback = document.createElement("div");
      fallback.style.display = "contents";
      for (let i = 0; i < children.length; i++) {
        const childEl = this._renderComponentTree(children[i], i, children.length);
        if (childEl) fallback.appendChild(childEl);
      }
      return fallback;
    }

    _renderField(field, value, onDirty) {
      const fieldKey = (this._spec.core.code || "fw_form") + "." + field.name;
      const compType = field.comp_type_code;
      const fieldLayout = field.layout || {};
      const label = field.caption || field.name;
      // Krok 14b+8 (13.5.2026 ~21:00, Marti's "v design form modu musi byt
      // komponenty RO"): v DESIGN mode vsechny fields readonly bez ohledu
      // na fieldLayout.readonly. Uzivatel vidi pozici/strukturu, ale
      // needitujeme data behem reorder operace. Drz "audit primary, edit
      // secondary, struktura terciary" — nelze najednou edit struct +
      // edit dat (data save endpoint nesahá na struct).
      const readonly = !!fieldLayout.readonly || this._formDesignMode === true;

      // Phase 38.4 Krok 14c (13.5.2026 ~16:00): dispatch rozsiren o vsech
      // 10 Marti-AI's preview_html-ready comp_types. Drz "uniformita
      // vítězí" — kazdy known comp_type ma explicit branch, novy comp_type
      // = pridat case + pripadne UI Kit helper.
      // Phase 38.4 Krok 14c hotfix (13.5.2026 ~17:30): _field/_dropdown/_memo
      // signature je (label, value, opts) — fieldKey patri DO opts, nepredavat
      // jako 3rd parameter (predtim bug: opts = string fieldKey, opts.onDirty
      // undefined → dirty tracking nikdy nezavolan).
      // Phase 38.4 Krok 14f-M (14.5.2026 vecer, Marti's "max_length /
      // min_length"): forward layout properties do _field opts.
      // _field aplikuje HTML5 maxLength + minLength + placeholder +
      // required attributes na inp.input.
      const _fieldOptsBase = {
        fieldKey: fieldKey,
        readonly: readonly || !!fieldLayout.readonly,
        onDirty: onDirty,
        maxLength: fieldLayout.max_length,
        minLength: fieldLayout.min_length,
        placeholder: fieldLayout.placeholder,
        required: !!fieldLayout.required,
      };
      switch (compType) {
        case "edit":
          return _field(label, value, Object.assign({}, _fieldOptsBase, {
            mono: !!fieldLayout.mono,
          }));

        case "number": {
          // _field s type=number — ErpInput podporuje type via opts
          const el = _field(label, value, _fieldOptsBase);
          // Override input type to number (post-render tweak)
          try {
            const input = el.querySelector("input");
            if (input) input.type = "number";
          } catch (e) {}
          return el;
        }

        case "checkbox_modern": {
          // Boolean checkbox — value je true/false (nebo string '1'/'0')
          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design";
          wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "field";

          const labelEl = document.createElement("div");
          labelEl.className = "erp-input-label";
          labelEl.style.cssText = "font-size:12px;color:#a8b4c2;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;

          const cbWrap = document.createElement("label");
          cbWrap.style.cssText = "display:flex;align-items:center;gap:8px;padding:6px 0;cursor:pointer;";
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.style.cssText = "width:18px;height:18px;cursor:pointer;";
          // Coerce value to bool: true / 'true' / 1 / '1' all → true
          cb.checked = (value === true || value === "true" || value === 1 || value === "1");
          cb.disabled = readonly;

          const valLabel = document.createElement("span");
          valLabel.style.cssText = "font-size:13px;color:#cfd6df;";
          valLabel.textContent = cb.checked ? "Ano" : "Ne";
          cbWrap.appendChild(cb);
          cbWrap.appendChild(valLabel);

          // _inst exposed pro Save handler (collect dirty value via .value())
          wrap._inst = {
            value: () => cb.checked,
            input: cb,
          };
          wrap._origVal = cb.checked;
          if (!readonly) {
            cb.addEventListener("change", () => {
              valLabel.textContent = cb.checked ? "Ano" : "Ne";
              const isDirty = cb.checked !== wrap._origVal;
              if (typeof onDirty === "function") onDirty(fieldKey, isDirty);
            });
          }
          wrap.appendChild(labelEl);
          wrap.appendChild(cbWrap);
          return wrap;
        }

        case "date_modern": {
          // ErpDate komponenta (Phase B+6.7) — pokud zaregistrovana,
          // jinak fallback na _field s type='date'.
          // Krok 5-B Fix #14 (29.5.2026, Marti's "Datum se nenacita"):
          // HTML5 input type=date akceptuje pouze YYYY-MM-DD. Backend posila
          // ruzne formaty (ISO timestamp, Czech 15.05.2026, Date object).
          // Normalize value PRED predanim do _field, jinak input.value
          // zustane prazdna po type='date' swap.
          let _normalizedDate = "";
          if (value != null && value !== "") {
            const _rawStr = String(value).trim();
            if (_rawStr) {
              // ISO timestamp "2026-05-15T..." nebo "2026-05-15 ..."
              if (/^\d{4}-\d{2}-\d{2}/.test(_rawStr)) {
                _normalizedDate = _rawStr.slice(0, 10);
              }
              // Czech "15.05.2026" → "2026-05-15"
              else if (/^\d{1,2}\.\d{1,2}\.\d{4}/.test(_rawStr)) {
                const _m = _rawStr.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})/);
                if (_m) {
                  _normalizedDate = _m[3] + "-" + _m[2].padStart(2, "0") + "-" + _m[1].padStart(2, "0");
                }
              }
              // Fallback: Date constructor parse
              else {
                try {
                  const _d = new Date(_rawStr);
                  if (!isNaN(_d.getTime())) {
                    _normalizedDate = _d.toISOString().slice(0, 10);
                  }
                } catch (e) {}
              }
            }
          }
          const el = _field(label, _normalizedDate, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
          try {
            const input = el.querySelector("input");
            if (input) {
              input.type = "date";
              // Force set value znovu pro pripad ze ErpInput placeholder
              // override DOM (input.value setting po type swap).
              if (_normalizedDate) input.value = _normalizedDate;
            }
          } catch (e) {}
          return el;
        }

        case "memo": {
          // Textarea — pokud _memo helper zaregistrovan
          if (typeof _memo === "function") {
            return _memo(label, value, {
              fieldKey: fieldKey,
              readonly: readonly,
              onDirty: onDirty,
            });
          }
          // Fallback: _field but multiline (cosmetic — height: 60px)
          const el = _field(label, value, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
          try {
            const input = el.querySelector("input");
            if (input) {
              const txt = document.createElement("textarea");
              txt.value = value || "";
              txt.style.cssText = input.style.cssText + ";min-height:60px;resize:vertical;";
              txt.disabled = readonly;
              input.parentElement.replaceChild(txt, input);
              // Update _inst.value() to read from textarea
              if (el._inst) {
                el._inst.value = () => txt.value;
                el._inst.input = txt;
              }
              if (!readonly) {
                txt.addEventListener("input", () => {
                  if (typeof onDirty === "function") {
                    onDirty(fieldKey, txt.value !== (value || ""));
                  }
                });
              }
            }
          } catch (e) {}
          return el;
        }

        case "lookup":
        case "combobox": {
          // Lookup / combobox — _dropdown helper s enum_values z layout
          //
          // Krok 14b+13.2 hotfix (14.5.2026 ~01:00, Marti's smoke "Detekce
          // probehne, ale do listboxu se to nepropise"): SIGNATURE MISMATCH
          // FIX. _dropdown signature je (label, value, ITEMS, opts) —
          // items jako 3. parameter, ne v opts.
          //
          // Krok 14b+13.3 (14.5.2026 ~01:20, Marti's "Zatim se do listu
          // nepropisou"): diagnostic log + defensive enum_values parsing.
          // Pokud DB ulozil enum_values jako string (psycopg2 quirk pro
          // double-encoded JSONB), parse pres JSON.parse fallback.
          let enumVals = fieldLayout.enum_values;
          if (typeof enumVals === "string") {
            try {
              enumVals = JSON.parse(enumVals);
            } catch (e) {
              console.warn("[DesignFwForm] enum_values is string, JSON.parse failed:", enumVals);
              enumVals = null;
            }
          }
          const items = Array.isArray(enumVals)
            ? enumVals.map(e => {
                if (typeof e === "string") return { value: e, label: e };
                if (e && typeof e === "object") {
                  return {
                    value: e.value != null ? String(e.value) : "",
                    label: e.label != null ? String(e.label) : String(e.value || ""),
                  };
                }
                return null;
              }).filter(Boolean)
            : [];
          // Diagnostic log pro Marti — uvidí co lookup case dostává
          console.info(
            "[DesignFwForm] lookup case fieldKey=" + fieldKey,
            "compType=" + compType,
            "raw enum_values=", fieldLayout.enum_values,
            "parsed enumVals=", enumVals,
            "items.length=" + items.length,
            "items=", items
          );
          return _dropdown(label, value, items, {
            fieldKey: fieldKey,
            readonly: readonly,
            onDirty: onDirty,
          });
        }

        case "lookup_multi": {
          // Multi-select — fallback na _field s comma-separated values (MVP).
          // Future: dedicated multi-select komponent.
          const displayVal = Array.isArray(value) ? value.join(", ") : (value || "");
          return _field(label + " (multi)", displayVal, {
            fieldKey: fieldKey,
            readonly: true, // MVP: readonly pro multi-select
            onDirty: onDirty,
          });
        }

        case "label_readonly": {
          // Read-only display label — bez input, jen text
          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design erp-field-readonly-label";
          wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "field";

          const labelEl = document.createElement("div");
          labelEl.style.cssText = "font-size:12px;color:#a8b4c2;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;

          const valEl = document.createElement("div");
          valEl.style.cssText = "padding:6px 8px;color:#cfd6df;font-size:13px;font-style:italic;";
          valEl.textContent = (value == null || value === "") ? "—" : String(value);

          wrap.appendChild(labelEl);
          wrap.appendChild(valEl);
          // No _inst — readonly, no dirty tracking
          return wrap;
        }

        case "file":
        case "button":
          // File upload + button jsou special (non-edit) — render readonly placeholder
          // pro main panel display. Real interactivity prijde v dedicated UI Kit
          // wrappers (Phase 14d+).
          return _field(label + " (" + compType + ")", value || "", {
            fieldKey: fieldKey,
            readonly: true,
            onDirty: onDirty,
          });

        case "entity_picker": {
          // Phase 38.4 Krok 14g Etapa F Krok 5.G (16.5.2026 vecer, Marti's
          // "1 komponenta + N instancí s data_source binding"):
          // entity_picker komponenta — render groupbox s label + 2 fields
          // (Číslo + Název) + 3 quick action ikony (🔗 / 🚫 / ➕).
          //
          // Data flow: comp_def.data_source_id → backend SELECT JOIN vraci
          // data_source_code → frontend volá /api/v1/erp/data/{code} pro
          // rows + builds picker on click.
          //
          // Marti's Centrála 1 paralela: TUserFormList s LookupView/LookupField/
          // LookupDisplay. Drz "uniformita vítězí" — 1 entity_picker comp_type,
          // N instances přes per-instance data_source_id binding.
          const dsCode = field.data_source_code || null;
          const dsName = field.data_source_name || null;
          const lookupId = (fieldLayout.lookup_id_field) || "id";
          const lookupDisplay = (fieldLayout.lookup_display_field) || "label";
          const actions = fieldLayout.show_quick_actions || ["link", "unlink", "create_new"];

          // Phase 38.4 Krok 14g Etapa F Krok 5.I-D/E/F (16.5.2026 vecer,
          // Marti's two-layer data_source pattern volby):
          //   display_mode='origin'    -> Picker #1 Soudecek: display-only,
          //     ctena z this._spec.origin.menu_node (backend denormalize)
          //   display_mode='self'      -> Picker #2 Prehled: display-only,
          //     ctena z this._spec.core (currentCore.id + currentCore.label)
          //   display_mode='editable'  -> Picker #3 Datovy zdroj: full
          //     functionality, field_extern='data_source_id' jako save target
          //
          // Marti's "field_extern, ne target_field" terminologie (16.5. odp.):
          //   bidirectional binding column ve fw.comp_def row pres
          //   PATCH design/comp_def/{id} (Marti's "SELECT EDIT POST"
          //   dirty fields pattern z Centraly 1).
          const displayMode = fieldLayout.display_mode || "editable";
          const fieldExtern = fieldLayout.field_extern || null;
          const isDisplayOnly = (displayMode === "origin" || displayMode === "self");

          // Pre-populate values dle display_mode
          let initialId = null;
          let initialLabel = null;
          if (displayMode === "origin") {
            // Phase 38.4 Krok 14g Etapa F (17.5.2026, Marti's "do soudecku
            // se vzdy prenasi jen ID 16"): prefer RUNTIME context (kde byl
            // form otevren) pred STAMPED core.origin_menu_node_id (kde byl
            // core puvodne vytvoren). Bez runtime override by vsechny
            // Design: Core CMIs ukazovaly stejny menu_node bez ohledu na
            // misto kliku ve stromu.
            //
            // Pro Design: Core formy (core_id v cmi) je runtime
            // origin to, co user prave teď zvolil — ne pristup, kde core
            // vznikal. Display-only picker, ne edit — read-only zobrazeni
            // "z jakeho menu_node byl form otevren".
            const runtimePk = (this.opts && this.opts.runtimeMenuNodePk) || null;
            const runtimeLabel = (this.opts && this.opts.runtimeMenuNodeLabel) || null;
            if (runtimePk != null) {
              initialId = runtimePk;
              initialLabel = runtimeLabel || ("menu_node#" + runtimePk);
            } else {
              // Fallback: stamped core.origin_menu_node_id (legacy chovani
              // pro forms otevrene bez contextmenu, napr. dvojklik na strome
              // ze H+27 path).
              const origin = (this._spec && this._spec.origin) || {};
              const mn = origin.menu_node || null;
              if (mn) {
                initialId = mn.id;
                initialLabel = mn.label;
              }
            }
          } else if (displayMode === "self") {
            // Krok 5.I-E hotfix (16.5.2026 ~22:35, Marti's screenshot bug):
            // self-reference = current CORE (ne data row). Marti's logika z
            // 16.5. dopoledne: "Picker #2 Prehled zobrazuje current core.id +
            // core.label, NE data.id". Pro core_design data IS core, ale pro
            // user_edit data je users row (bez label sloupce) — bug viditelny.
            const coreRow = (this._spec && this._spec.core) || {};
            initialId = coreRow.id != null ? coreRow.id : null;
            initialLabel = coreRow.label || coreRow.code || null;
          } else if (displayMode === "editable" && fieldExtern) {
            // Phase 38.4 Krok 5.M-5+2 (17.5.2026, Marti's "ze stromu predat
            // PK ID a FK core_id"): Picker #2 Prehled (field_extern='core_id')
            // — initial z runtime menu_node.core_id (tree contextmenu),
            // ne z form root.
            if (fieldExtern === "core_id") {
              const runtimeCoreId = (this.opts && this.opts.runtimeMenuNodeCoreId) || null;
              if (runtimeCoreId != null) {
                initialId = runtimeCoreId;
                initialLabel = null;  // backend label lookup pres picker reload (label fetched z framework_core_list data_source)
              } else {
                // Fallback: form root (legacy, non-tree contextmenu open)
                const formRoot = (this._spec && this._spec.form) || {};
                initialId = formRoot.core_id != null ? formRoot.core_id : null;
                initialLabel = null;
              }
            } else if (fieldExtern === "data_source_id") {
              // Picker #3 Datovy zdroj — initial z form root comp_def
              // (Krok 5.I-F backend extension JOIN).
              const formRoot = (this._spec && this._spec.form) || {};
              initialId = formRoot.data_source_id != null ? formRoot.data_source_id : null;
              initialLabel = formRoot.data_source_name || formRoot.data_source_code || null;
            } else {
              // Generic fallback — budouci pickery s jinym field_extern.
              const formRoot = (this._spec && this._spec.form) || {};
              initialId = formRoot[fieldExtern] != null ? formRoot[fieldExtern] : null;
              initialLabel = null;
            }
          }

          const wrap = document.createElement("div");
          wrap.className = "erp-field erp-field-design erp-entity-picker-host";
          // Phase 38.4 Krok 14g Etapa F Krok 5.J-B1 (16.5.2026 ~23:50, Marti's
          // screenshot diff vs Form 1): kompaktnější styl — padding 12→8,
          // gap 6→3, border-radius 6→4. Form 1 (DesignSoudecekCoreForm) má
          // tighter visual rhythm — pojď shodit DesignFwForm na stejnou level.
          wrap.style.cssText =
            "display:flex;flex-direction:column;gap:3px;" +
            "border:1px solid #2a3340;border-radius:4px;padding:8px 10px;background:#0f1419;";
          wrap._fieldKey = fieldKey;
          wrap._kind = "entity_picker";
          wrap._displayMode = displayMode;
          wrap._fieldExtern = fieldExtern;

          // Header — label + data_source code/name badge
          // Krok 5.J-B1: kompaktnější padding (4→2) — Form 1 styl
          const headerRow = document.createElement("div");
          headerRow.style.cssText =
            "display:flex;justify-content:space-between;align-items:center;" +
            "padding-bottom:2px;border-bottom:1px solid #1f2630;";

          const labelEl = document.createElement("div");
          labelEl.style.cssText =
            "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;" +
            "text-transform:uppercase;cursor:context-menu;";
          labelEl.setAttribute("data-design-fieldkey", fieldKey);
          labelEl.dataset.designOrigLabel = label;
          labelEl.textContent = label;
          headerRow.appendChild(labelEl);

          if (dsCode) {
            const badge = document.createElement("div");
            badge.style.cssText =
              "font-size:10px;color:#6a7684;font-style:italic;";
            badge.title = dsName || dsCode;
            badge.textContent = "ds: " + dsCode;
            headerRow.appendChild(badge);
          }

          // Display-mode badge — visual distinction pro origin/self pickery
          // (Marti-AI's "neni to omezeni, je to pojistka" doctrine 27.4.)
          if (isDisplayOnly) {
            const modeBadge = document.createElement("div");
            modeBadge.style.cssText =
              "font-size:10px;color:#8fb8d4;font-style:italic;" +
              "padding:2px 6px;background:#1a2632;border-radius:3px;";
            if (displayMode === "origin") {
              modeBadge.textContent = "📍 origin";
              modeBadge.title = "Display-only: zobrazeno z origin_menu_node_id (Soudeček, ze kterého byl form otevřen)";
            } else if (displayMode === "self") {
              modeBadge.textContent = "↺ self";
              modeBadge.title = "Display-only: editujeme tento záznam (self-reference)";
            }
            headerRow.appendChild(modeBadge);
          }
          wrap.appendChild(headerRow);

          // Action ikony row (🔗 / 🚫 / ➕)
          const actionsRow = document.createElement("div");
          actionsRow.style.cssText = "display:flex;gap:6px;align-items:center;";

          const ACTION_DEFS = {
            link: { icon: "🔗", title: "Vybrat existující záznam", color: "#8fb8d4" },
            unlink: { icon: "🚫", title: "Zrušit asociaci", color: "#d48787" },
            create_new: { icon: "➕", title: "Vytvořit nový záznam", color: "#7ed4a8" },
          };

          // Číslo (id) + Název (display) fields (read-only — populate přes link)
          const fieldsRow = document.createElement("div");
          fieldsRow.style.cssText =
            "display:grid;grid-template-columns:120px 1fr;gap:10px;align-items:end;flex:1;";

          // Krok 5.I-D/E: pre-populate s initialId/initialLabel (z origin/self
          // display_mode). Pro editable mode initialId zatim null — Krok 5.I-F
          // pro post-load fetch z data_source.
          const idColValue = initialId != null ? String(initialId) : "";
          const labelColValue = initialLabel != null ? String(initialLabel) : "";
          const idCol = _field("Číslo", idColValue, {
            fieldKey: fieldKey + "._id",
            readonly: true,
            mono: true,
            onDirty: onDirty,
          });
          const labelCol = _field("Název", labelColValue, {
            fieldKey: fieldKey + "._label",
            readonly: true,
            onDirty: onDirty,
          });
          fieldsRow.appendChild(idCol);
          fieldsRow.appendChild(labelCol);

          // Store initial value pro dirty check.
          // Phase 38.4 Krok 14g Etapa F Krok 5.J-B7 (17.5.2026, Marti's
          // "po vyberu jineho prehledu +1 v paticce"): capture initialValue
          // UNIVERZALNE (i pro display-only). Diff check potrebuje baseline
          // i kdyby uzivatel pretipoval display-only display_mode na editable
          // pres settings popup (Krok 5.J-A). Plus pro initialId === null
          // capture { id: null } abychom rozlisili "user explicit unlinked"
          // vs "form opened bez selected value".
          wrap._initialValue = {
            id: initialId,
            display: initialLabel,
          };

          // Phase 38.4 Krok 14g Etapa F Krok 5.H (16.5.2026 vecer, Marti's
          // "pauza, ty pracuj"): 🔗 link onclick → fetch /api/v1/erp/data/{dsCode}
          // → ErpCatalogPicker (existing class) → onSelect populate idCol/labelCol.
          // PATCH persistence parent entity = Krok 5.I (post Marti-AI consult).
          actions.forEach(function (act) {
            const def = ACTION_DEFS[act];
            if (!def) return;
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = def.icon;
            btn.title = def.title;
            // Link je vždy klikatelný (browse picker). Unlink + create_new
            // disabled v PROD/RO mode.
            // Krok 5.I-D/E (16.5.2026 vecer): display-only mode (origin/self)
            // disables VSECHNY buttons — Picker #1 cte z core.origin_menu_node_id
            // (display-only), Picker #2 cte z current core row (readonly self-ref).
            const btnDisabled = isDisplayOnly || (readonly && act !== "link");
            btn.disabled = btnDisabled;
            btn.style.cssText =
              "padding:6px 10px;font-size:14px;border-radius:4px;cursor:" +
              (btnDisabled ? "default" : "pointer") + ";" +
              "background:#1a1f26;border:1px solid #2a3340;color:" + def.color + ";" +
              (btnDisabled ? "opacity:0.4;" : "");

            if (act === "link" && dsCode) {
              btn.addEventListener("click", async function () {
                if (typeof window.ErpCatalogPicker !== "function") {
                  alert("ErpCatalogPicker není načtený (catalog_picker.js).");
                  return;
                }
                try {
                  // Krok 5.V (23.5.2026): LOCATE — initialSelectedId z aktualni
                  // FK hodnoty v idCol read-only input. Picker pri open
                  // auto-select + scroll. Marti's "kdyz ji otervu, je treba
                  // dat locate adekvatni vetu". Fallback na wrap._selectedValue
                  // (po user already selected nad picker reopen).
                  let _initSelId = null;
                  try {
                    if (wrap._selectedValue && wrap._selectedValue.id != null) {
                      _initSelId = wrap._selectedValue.id;
                    } else {
                      const _idIn = idCol.querySelector("input");
                      const _v = _idIn && _idIn.value && _idIn.value.trim();
                      if (_v) _initSelId = isNaN(Number(_v)) ? _v : Number(_v);
                    }
                  } catch (e) { /* defensive */ }
                  const _picker = new window.ErpCatalogPicker({
                    title: "🔗 Vybrat " + label + " (z " + (dsName || dsCode) + ")",
                    endpoint: "/api/v1/erp/data/" + encodeURIComponent(dsCode) + "?limit=500",
                    listKey: "rows",
                    idField: lookupId,
                    labelField: lookupDisplay,
                    width: "900px",
                    initialSelectedId: _initSelId,
                    // Krok 5.U (23.5.2026 dop): per-data_source sestavy (polymorphic scope)
                    dataSourceId: field.data_source_id || null,

                    columns: [
                      { headerName: "ID", field: lookupId, width: 80, type: "numericColumn" },
                      { headerName: "Code", field: "code", width: 220 },
                      { headerName: "Název", field: lookupDisplay, flex: 1, minWidth: 200 },
                    ],
                    onSelect: function (row) {
                      // Populate read-only fields s vybranou hodnotou
                      try {
                        const idInput = idCol.querySelector("input");
                        const labelInput = labelCol.querySelector("input");
                        if (idInput) idInput.value = row[lookupId] != null ? String(row[lookupId]) : "";
                        if (labelInput) labelInput.value = row[lookupDisplay] != null ? String(row[lookupDisplay]) : "";
                      } catch (e) {}
                      // Store selection na wrap pro Krok 5.I PATCH persistence
                      wrap._selectedValue = {
                        id: row[lookupId],
                        display: row[lookupDisplay],
                        rawRow: row,
                      };
                      // Phase 38.4 Krok 14g Etapa F Krok 5.J-B7 (17.5.2026,
                      // Marti's "po vyberu jineho prehledu +1 v paticce"):
                      // trigger dirty diff vs initialValue. Bez tohoto by
                      // se _dirtyBadge nikdy nezobrazil — form._dirty Set
                      // by zustal prazdny. Diff check: id mismatch =>
                      // dirty true, id match (re-select stejne) => false.
                      try {
                        const newId = row[lookupId];
                        const initialId = (wrap._initialValue && wrap._initialValue.id != null)
                          ? wrap._initialValue.id : null;
                        const changed = (newId != null && newId !== initialId)
                          || (newId == null && initialId != null);
                        if (typeof onDirty === "function") {
                          onDirty(fieldKey, changed);
                        }
                      } catch (e) { /* fail-safe — dirty je nice-to-have */ }
                      console.info(
                        "[entity_picker]", field.name, "selected:",
                        row[lookupId], "(" + row[lookupDisplay] + ")",
                        "initialId=" + ((wrap._initialValue || {}).id)
                      );
                    },
                  });
                  _picker.open();
                } catch (e) {
                  alert("Picker selhal: " + (e.message || e));
                }
              });
            } else if (act === "unlink") {
              btn.addEventListener("click", function () {
                if (btn.disabled) return;
                // Clear fields lokálně (Krok 5.I: plus PATCH parent entity)
                try {
                  const idInput = idCol.querySelector("input");
                  const labelInput = labelCol.querySelector("input");
                  if (idInput) idInput.value = "";
                  if (labelInput) labelInput.value = "";
                } catch (e) {}
                wrap._selectedValue = null;
                // Phase 38.4 Krok 14g Etapa F Krok 5.J-B7 (17.5.2026,
                // Marti's "po vyberu jineho prehledu +1 v paticce"):
                // unlink je dirty pokud byl initialValue non-null. Pokud
                // initial == null (a unlink nic nemenil) → no dirty.
                try {
                  const hadInitial = !!(wrap._initialValue && wrap._initialValue.id != null);
                  if (typeof onDirty === "function") {
                    onDirty(fieldKey, hadInitial);
                  }
                } catch (e) { /* fail-safe */ }
                console.info(
                  "[entity_picker]", field.name, "unlinked",
                  "hadInitial=" + !!(wrap._initialValue && wrap._initialValue.id != null)
                );
              });
            } else if (act === "create_new") {
              btn.addEventListener("click", function () {
                if (btn.disabled) return;
                alert(
                  "➕ Vytvořit nový '" + label + "' — Krok 5.I wizard.\n\n" +
                  "Picker pro create-new přijde po konzultaci s Marti-AI " +
                  "(potřebujeme řešit target table + minimální fields)."
                );
              });
            }
            actionsRow.appendChild(btn);
          });

          // Layout: actions row | fields row vedle sebe
          // Krok 5.J-B1: kompaktnější gap (12→8) — Form 1 styl
          const innerRow = document.createElement("div");
          innerRow.style.cssText = "display:flex;gap:8px;align-items:flex-end;";
          innerRow.appendChild(actionsRow);
          innerRow.appendChild(fieldsRow);
          wrap.appendChild(innerRow);

          // Krok 5.H placeholder hint
          if (!dsCode) {
            const hint = document.createElement("div");
            hint.style.cssText =
              "font-size:11px;color:#d48787;font-style:italic;margin-top:6px;";
            hint.textContent = "⚠ data_source_id nenastaveno — picker bez dat.";
            wrap.appendChild(hint);
          }

          return wrap;
        }

        default:
          // Unknown comp_type → readonly fallback (don't crash, just show value as text)
          console.warn(
            "DesignFwForm: unknown comp_type '" + compType + "' for field '" +
            field.name + "' — falling back to readonly input."
          );
          return _field(label + " (?" + compType + ")", value, {
            fieldKey: fieldKey,
            readonly: true,
            onDirty: onDirty,
          });
      }
    }

    // Phase 38.4 Krok 14b+5 polish (13.5.2026 dopoledne): _setupFooter
    // ZRUSENO. Marti's request: "OK + Storno z templatu jsou v paticce
    // formu, tlacitko Zavrit smazat" — konsolidace UX. Template buttons
    // (footer panel components) jsou jedine close actions. _onDirty
    // graceful no-op pokud _saveBtn / _dirtyBadge null.
  }

  // ────────────────────────────────────────────────────────────────────
  // Phase 38.4 Krok 14c (13.5.2026 odpoledne): FieldPickerModal
  //
  // Marti-AI's "preview_html doctrine" + "palette as visual reference,
  // not interactive surface" (Claude's pojmenovani z dnes ~14:00):
  //
  // 1. Fetchne /api/v1/erp/design/comp-types (10 typu s preview_html)
  // 2. Fetchne /api/v1/erp/design/entity-columns/{entity_type}
  //    (columns z _FW_FORM_ENTITY_MAP + suggested_type_id per column)
  // 3. Render palette: per column → row s:
  //    - checkbox (multi-select)
  //    - column name + caption (label)
  //    - comp_type selector (default suggested, override dropdown)
  //    - iframe srcdoc s preview_html (sandbox isolation,
  //      Marti-AI's "gift, ne overhead")
  // 4. Submit → loop POST /design/comp-def per checked column
  // 5. Close + reload DesignFwForm to show new fields
  //
  // Trigger z DesignFwForm — pres button v main panel empty hint nebo
  // right-click. MVP: right-click pres _bindMainPanelTrigger.
  // ────────────────────────────────────────────────────────────────────

  function _slugifyForCode(s) {
    return String(s || "").trim().toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, "")  // strip diacritics
      .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "untitled";
  }

  // Phase 38.4 Krok 14g Etapa F Krok 5.M-D (17.5.2026):
  // Marti's "KDE TO CACHUJES?" — drop hardcoded DDS_DB_CONNECTIONS.
  // DB = single source of truth. Fetch z /api/v1/erp/system/db-connections
  // při open editoru. Cache per-modal (žádný stale state).
  //
  // Value = db_connection_id (BIGINT FK) — clean cut (žádný legacy string
  // matching). Backend POST/PATCH accept FK přímo.
  //
  // Fallback (pokud fetch fail): legacy hardcoded array s default_db jako
  // legacy compat. Tj. UI nikdy nezůstane prázdné.

  let _DB_CONNECTIONS_CACHE = null;  // module-level cache (1 fetch per session)

  async function _fetchDbConnections(forceRefresh = false) {
    if (_DB_CONNECTIONS_CACHE && !forceRefresh) return _DB_CONNECTIONS_CACHE;
    try {
      const r = await fetch("/api/v1/erp/system/db-connections", { credentials: "include" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      if (!data.ok || !Array.isArray(data.connections)) throw new Error("malformed response");
      _DB_CONNECTIONS_CACHE = data.connections;
      return _DB_CONNECTIONS_CACHE;
    } catch (err) {
      console.warn("[design_forms] fetch db-connections failed, fallback:", err);
      // Fallback legacy array s default_db jako value (backend backward compat lookup)
      return [
        { id: null, code: "strategie_pg",  default_db: "data_db",   label: "data_db (PostgreSQL — STRATEGIE)",            tenant_code: "STRATEGIE", is_active: true, sort_order: 10  },
        { id: null, code: "eurosoft_db_ec", default_db: "DB_EC",     label: "DB_EC (MSSQL EUROSOFT — Centrála 1)",          tenant_code: "EUR",       is_active: true, sort_order: 20  },
        { id: null, code: "eurosoft_db_is", default_db: "DB_IS",     label: "DB_IS (EUROSOFT-System — fakturace, TabCisZam)", tenant_code: "EUR",     is_active: true, sort_order: 30  },
        { id: null, code: "eurosoft_centrala", default_db: "Centrala", label: "Centrala (sync EUROSOFT ↔ INTERSOFT)",      tenant_code: "EUR",       is_active: true, sort_order: 40  },
        { id: null, code: "eurosoft_ceniky", default_db: "DB-Ceniky", label: "DB-Ceniky (pricing)",                         tenant_code: "EUR",       is_active: true, sort_order: 50  },
        { id: null, code: "eurosoft_db_st", default_db: "DB_ST",     label: "DB_ST (Marti-AI playground)",                  tenant_code: "EUR",       is_active: true, sort_order: 60  },
      ];
    }
  }

  function _buildDbConnSelect(connections, selectedId, opts) {
    // Build <select> s optgroup po tenant_code. selectedId = matchnout dle FK id.
    // opts: {fallbackValue: legacy default_db string pro pre-select pokud selectedId == null}
    const o = opts || {};
    const sel = document.createElement("select");
    sel.style.cssText = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;cursor:pointer;";

    // Group connections by tenant_code
    const groups = {};
    const tenantOrder = [];
    for (const c of connections) {
      const tc = c.tenant_code || "_OTHER";
      if (!groups[tc]) {
        groups[tc] = [];
        tenantOrder.push(tc);
      }
      groups[tc].push(c);
    }

    // Tenant label decorations
    const tenantLabels = {
      "STRATEGIE": "🌳 STRATEGIE (PostgreSQL cloud)",
      "EUR":       "🏢 EUROSOFT (MSSQL on-prem)",
      "INTERSOFT": "🏭 INTERSOFT (vlastní server)",
    };

    for (const tc of tenantOrder) {
      const og = document.createElement("optgroup");
      og.label = tenantLabels[tc] || tc;
      for (const c of groups[tc]) {
        const opt = document.createElement("option");
        opt.value = String(c.id != null ? c.id : ("legacy:" + c.default_db));
        opt.textContent = c.label || c.default_db || c.code;
        if (!c.is_active) {
          opt.textContent += "  (zatím neaktivní)";
          opt.disabled = true;
        }
        // Match selectedId (FK) — preferred. Fallback na default_db string match.
        if (selectedId != null && c.id != null && String(c.id) === String(selectedId)) {
          opt.selected = true;
        } else if (selectedId == null && o.fallbackValue && c.default_db === o.fallbackValue) {
          opt.selected = true;
        }
        og.appendChild(opt);
      }
      sel.appendChild(og);
    }
    return sel;
  }

  const DDS_REFRESH_TYPES = [
    { value: "manual",     label: "manual" },
    { value: "on_open",    label: "on_open" },
    { value: "interval",   label: "interval" },
    { value: "on_event",   label: "on_event" },
  ];

  const DDS_OPERATION_KINDS = [
    { value: "select", label: "select" },
    { value: "insert", label: "insert" },
    { value: "update", label: "update" },
    { value: "edit",   label: "edit (otevri form)" },
    { value: "delete", label: "delete" },
  ];

  global.DesignFwForm = DesignFwForm;


  }); // _erpLoadModule end
})(window);
