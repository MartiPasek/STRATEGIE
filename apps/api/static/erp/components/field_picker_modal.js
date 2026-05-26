/**
 * FieldPickerModal — extracted standalone JS module.
 *
 * Phase JS-5+6+7 (18.5.2026 ~23:45): extract z design_forms.js.
 * 2-panel field picker (Krok 14g-H+11..+13)
 *
 * Loaded AFTER design_form_helpers.js (which exports _erpDFH).
 * Wrapped v _erpLoadModule pre Module Health visibility.
 */
(function (global) {
  "use strict";

  // Mutual immunity wrap (Krok 14g Etapa C pattern)
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("field_picker_modal.js", "v1.0.0", function () {

    const _DFH = global._erpDFH || {};
    const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
    const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
    const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
    const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
    const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
    const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
    const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
    const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  class FieldPickerModal {
    constructor(opts) {
      this.opts = opts || {};
      // opts: { entityType: 'user', parentCompDefId: 2, onComplete: cb }
      this._shell = null;
      this._compTypes = [];       // [{id, code, label, kind, preview_html}]
      this._compTypesById = {};
      this._columns = [];         // [{name, caption_default, suggested_type_id, ...}]
      this._selected = new Set(); // column names checked
      this._typeOverrides = {};   // column.name -> type_id (override)
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "radio button single-select"):
      // Active container = target parent pro nove komponenty z palety.
      // null = pridava do form root (default). Klik na radio v "Jiz na forme"
      // container row prepne active. Single-select (jeden na formular).
      this._activeContainerCompDefId = null;
    }

    /**
     * Resolve target parent_comp_def_id pro novou komponentu:
     * - active container (Marti's radio button volba) pokud existuje
     * - fallback form root (parentCompDefId)
     */
    _resolveTargetParentId() {
      return this._activeContainerCompDefId || this.opts.parentCompDefId;
    }

    /**
     * Phase 38.4 Krok H+5 (26.5.2026, Marti's "vyjit z rozchozenych
     * komponent" + "kazda komponenta jinak"):
     * ⚙ settings button delegate na parent DesignFwForm._openFieldSettings(field).
     * Existing popup uz ma per-comp_type detection (entity_picker tab, atd.) —
     * reuse misto vlastniho duplikatu. Per-type fields (panel align /
     * groupbox border_mode / edit max_length / atd.) jsou pak v jedne
     * code path, snadno udrzitelne.
     *
     * @param {Object} opts
     * @param {number} opts.compDefId — PATCH target (parent najde field
     *                                  v this._spec.fields / containers by id)
     * @returns {HTMLElement} settings button
     */
    _makeSettingsBtn(opts) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "⚙";
      btn.title = "Nastavení komponenty";
      btn.style.cssText =
        "width:28px;height:28px;background:transparent;border:1px solid #2a3340;" +
        "color:#a8b4c2;cursor:pointer;border-radius:3px;font-size:14px;";
      btn.addEventListener("mouseenter", () => {
        btn.style.background = "#1a2530";
        btn.style.borderColor = "#7ed4e8";
        btn.style.color = "#7ed4e8";
      });
      btn.addEventListener("mouseleave", () => {
        btn.style.background = "transparent";
        btn.style.borderColor = "#2a3340";
        btn.style.color = "#a8b4c2";
      });
      btn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        // Delegate na parent (DesignFwForm) — reuse existing popup
        if (typeof this.opts.onOpenSettings === "function") {
          try { this.opts.onOpenSettings(opts.compDefId); }
          catch (e) {
            console.error("[FieldPickerModal] onOpenSettings failed:", e);
            _showToast("Settings popup selhal: " + (e.message || e), "error", 3000);
          }
        } else {
          _showToast("Settings popup není dostupný (chybí onOpenSettings handler)", "warn", 2500);
        }
      });
      return btn;
    }

    /**
     * Settings popup — caption + layout (width/height/min) + region_slot.
     * 3 action buttons: Uložit / Uložit jako výchozí / Načíst výchozí.
     *
     * mode='available' → Uložit = cached override v _availableOverrides[col.name]
     * mode='onform' / 'container' → Uložit = PATCH live /design/comp-def/update/{id}
     */
    async _openCompSettingsPopup(opts) {
      const { col, mode, compDefId, typeId } = opts;
      const ct = this._compTypesById[typeId] || {};
      const compLabel = (col && (col.caption_default || col.name)) ||
                       (opts.caption) || ct.label || "komponenta";

      // Init values — priority: opts.caption/layout > col existing > defaults
      const initLayout = opts.layout || (col && col.existing_layout) || {};
      const initCaption = opts.caption ||
                         (col && (col.existing_label || col.caption_default)) || "";
      const initRegionSlot = (col && col.existing_region_slot) || "main";

      // Backdrop + dialog
      const backdrop = document.createElement("div");
      backdrop.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200000;" +
        "display:flex;align-items:center;justify-content:center;";
      const dialog = document.createElement("div");
      dialog.style.cssText =
        "background:#0f1418;border:1px solid #2a3340;border-radius:6px;" +
        "width:460px;max-width:90vw;padding:20px;color:#cfd6df;" +
        "display:flex;flex-direction:column;gap:14px;";

      // Header
      const header = document.createElement("div");
      header.style.cssText = "display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #2a3340;padding-bottom:10px;";
      const title = document.createElement("div");
      title.style.cssText = "font-size:14px;font-weight:600;color:#e8eef5;";
      title.innerHTML = "⚙ Nastavení: " + _esc(compLabel) +
        " <span style=\"color:#7ed4e8;font-size:11px;font-family:ui-monospace,Consolas,monospace;margin-left:8px;\">" +
        _esc(ct.label || ("type#" + typeId)) + "</span>";
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText = "background:transparent;border:none;color:#8a96a4;cursor:pointer;font-size:18px;";
      closeBtn.addEventListener("click", () => backdrop.remove());
      header.appendChild(title);
      header.appendChild(closeBtn);
      dialog.appendChild(header);

      // Helper — field row
      const makeField = (label, inputEl) => {
        const row = document.createElement("div");
        row.style.cssText = "display:grid;grid-template-columns:140px 1fr;gap:10px;align-items:center;";
        const lbl = document.createElement("label");
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        lbl.textContent = label;
        row.appendChild(lbl);
        row.appendChild(inputEl);
        return row;
      };
      const styleInput = (el) =>
        "padding:5px 8px;background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
        "border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;";

      // Caption
      const captionInput = document.createElement("input");
      captionInput.type = "text";
      captionInput.value = initCaption;
      captionInput.style.cssText = styleInput();
      dialog.appendChild(makeField("Caption (label)", captionInput));

      // Region slot
      const regionSel = document.createElement("select");
      regionSel.style.cssText = styleInput();
      for (const slot of ["header", "main", "footer"]) {
        const opt = document.createElement("option");
        opt.value = slot;
        opt.textContent = slot;
        if (slot === initRegionSlot) opt.selected = true;
        regionSel.appendChild(opt);
      }
      dialog.appendChild(makeField("Region slot", regionSel));

      // Width / height / min_width / min_height (number inputs)
      const numFields = {};
      for (const [key, label] of [
        ["width", "Width (px)"],
        ["height", "Height (px)"],
        ["min_width", "Min width (px)"],
        ["min_height", "Min height (px)"],
      ]) {
        const inp = document.createElement("input");
        inp.type = "number";
        inp.min = "0";
        inp.placeholder = "—";
        if (initLayout[key] != null) inp.value = initLayout[key];
        inp.style.cssText = styleInput();
        numFields[key] = inp;
        dialog.appendChild(makeField(label, inp));
      }

      // Hint
      const hint = document.createElement("div");
      hint.style.cssText = "color:#8a96a4;font-size:11px;font-style:italic;padding:4px 0;";
      hint.textContent = "Prázdné = automatický (CSS default). Uložit jako výchozí = aplikuje na nové komponenty tohoto typu.";
      dialog.appendChild(hint);

      // Status row
      const status = document.createElement("div");
      status.style.cssText = "color:#7ed4e8;font-size:11px;min-height:14px;";
      dialog.appendChild(status);

      // Build payload helper
      const collectValues = () => {
        const layout = {};
        for (const [k, inp] of Object.entries(numFields)) {
          if (inp.value !== "" && !isNaN(parseInt(inp.value, 10))) {
            layout[k] = parseInt(inp.value, 10);
          }
        }
        return {
          caption: captionInput.value.trim(),
          region_slot: regionSel.value,
          layout: layout,
        };
      };
      const applyValues = (props) => {
        if (props.caption != null) captionInput.value = props.caption || "";
        if (props.region_slot) regionSel.value = props.region_slot;
        const lay = props.layout || {};
        for (const [k, inp] of Object.entries(numFields)) {
          inp.value = (lay[k] != null) ? lay[k] : "";
        }
      };

      // Action buttons
      const actions = document.createElement("div");
      actions.style.cssText = "display:flex;gap:8px;justify-content:flex-end;border-top:1px solid #2a3340;padding-top:12px;";

      // Načíst výchozí
      const loadDefBtn = document.createElement("button");
      loadDefBtn.type = "button";
      loadDefBtn.innerHTML = "📥 Načíst výchozí";
      loadDefBtn.style.cssText =
        "padding:6px 12px;background:#1f2530;border:1px solid #2a3340;color:#a8b4c2;" +
        "border-radius:3px;cursor:pointer;font-size:12px;";
      loadDefBtn.addEventListener("click", async () => {
        loadDefBtn.disabled = true;
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-type/" + typeId + "/defaults",
            { credentials: "include" }
          );
          const d = await r.json();
          if (!r.ok || !d.ok) throw new Error(d.error || "HTTP " + r.status);
          applyValues(d.default_props || {});
          status.textContent = "✓ Načteno z výchozí konfigurace " + (d.label || ct.label || "");
          status.style.color = "#5dbf5d";
        } catch (e) {
          status.textContent = "✗ Načtení selhalo: " + (e.message || e);
          status.style.color = "#d4888a";
        } finally {
          loadDefBtn.disabled = false;
        }
      });

      // Uložit jako výchozí
      const saveDefBtn = document.createElement("button");
      saveDefBtn.type = "button";
      saveDefBtn.innerHTML = "📌 Uložit jako výchozí";
      saveDefBtn.style.cssText =
        "padding:6px 12px;background:#2a3a4a;border:1px solid #4a7ba8;color:#cfd6df;" +
        "border-radius:3px;cursor:pointer;font-size:12px;";
      saveDefBtn.addEventListener("click", async () => {
        saveDefBtn.disabled = true;
        try {
          const vals = collectValues();
          const payload = {
            default_props: {
              default_caption: vals.caption || null,
              layout: vals.layout,
            },
          };
          const r = await fetch(
            "/api/v1/erp/design/comp-type/" + typeId + "/defaults",
            {
              method: "PUT",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            }
          );
          const d = await r.json();
          if (!r.ok || !d.ok) throw new Error(d.error || "HTTP " + r.status);
          status.textContent = "✓ Uloženo jako výchozí pro " + (ct.label || ("type#" + typeId));
          status.style.color = "#5dbf5d";
        } catch (e) {
          status.textContent = "✗ Uložení selhalo: " + (e.message || e);
          status.style.color = "#d4888a";
        } finally {
          saveDefBtn.disabled = false;
        }
      });

      // Uložit (mode-specific)
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.innerHTML = "💾 Uložit";
      saveBtn.style.cssText =
        "padding:6px 14px;background:#3a5a8a;border:1px solid #4a7ba8;color:#e8eef5;" +
        "border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;";
      saveBtn.addEventListener("click", async () => {
        const vals = collectValues();
        if (mode === "available") {
          // Cached override — applied při add POST z _resolveAddOverrides()
          if (!this._availableOverrides) this._availableOverrides = {};
          this._availableOverrides[col.name] = vals;
          status.textContent = "✓ Override uložen (aplikuje se při přidání na formulář)";
          status.style.color = "#5dbf5d";
          setTimeout(() => backdrop.remove(), 1200);
        } else {
          // PATCH live (onform / container)
          if (compDefId == null) {
            status.textContent = "✗ comp_def_id chybí — nelze uložit";
            status.style.color = "#d4888a";
            return;
          }
          saveBtn.disabled = true;
          try {
            const payload = {};
            if (vals.caption) payload.caption = vals.caption;
            if (vals.region_slot) payload.region_slot = vals.region_slot;
            payload.layout = vals.layout;
            const r = await fetch(
              "/api/v1/erp/design/comp-def/update/" + compDefId,
              {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              }
            );
            const d = await r.json();
            if (!r.ok || !d.ok) throw new Error(d.error || "HTTP " + r.status);
            status.textContent = "✓ Uloženo na formuláři";
            status.style.color = "#5dbf5d";
            // Live sync — parent form re-render
            if (typeof this.opts.onComplete === "function") {
              try { this.opts.onComplete({ updated: 1 }); }
              catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
            }
            setTimeout(() => backdrop.remove(), 1200);
          } catch (e) {
            status.textContent = "✗ Uložení selhalo: " + (e.message || e);
            status.style.color = "#d4888a";
            saveBtn.disabled = false;
          }
        }
      });

      actions.appendChild(loadDefBtn);
      actions.appendChild(saveDefBtn);
      actions.appendChild(saveBtn);
      dialog.appendChild(actions);

      backdrop.appendChild(dialog);
      backdrop.addEventListener("click", (ev) => {
        if (ev.target === backdrop) backdrop.remove();
      });
      document.body.appendChild(backdrop);
      captionInput.focus();
    }

    async open() {
      // Phase 38.4 Krok 14c+2 part A.2 (14.5.2026 odpoledne, Marti's
      // "musi se chovat jako normalni samostatne okno, ne modal"):
      //   floating=true → žádný overlay backdrop, lze proklikat přes ERP.
      //   Drop přes form panel funguje (HTML5 DnD nebyl blokován overlay
      //   pointer-events).
      // startPos: pravý horní roh viewport (drop target = DesignFwForm
      // pod modal, který je default v středu — Marti vidí form + drag
      // ze strany).
      this._shell = _buildModalShell({
        title: "🎨 Paleta komponent",
        width: "780px",
        hideDescToggle: true,
        floating: true,
        noBackdropClose: true,
        startPos: { top: "80px", left: "calc(100vw - 820px)" },
      });
      document.body.appendChild(this._shell.overlay);

      // Phase 38.4 Krok 14c+2 part B (14.5.2026 odpoledne, Marti's
      // "Drzi se stale vevnitr"): "Detach do okna" button v header.
      // Click → window.open() popup window, lze přesunout na druhý
      // monitor / kamkoliv mimo browser viewport. Cross-window drag-drop
      // funguje nativně (HTML5 DnD je cross-window pro same-origin).
      try {
        const headerActions = this._shell.header &&
          this._shell.header.querySelector(".erp-modal-header-actions");
        if (headerActions) {
          const detachBtn = document.createElement("button");
          detachBtn.type = "button";
          detachBtn.className = "erp-palette-detach";
          detachBtn.textContent = "🪟 Do okna";
          detachBtn.title = "Otevřít paletu v samostatném okně — lze přesunout na druhý monitor / mimo browser. Drag-drop do ERP funguje napříč okny.";
          detachBtn.style.cssText =
            "background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
            "padding:4px 10px;border-radius:3px;cursor:pointer;font-size:11px;" +
            "margin-right:4px;";
          detachBtn.addEventListener("click", () => {
            // Open popup window — Marti vidí standalone gallery
            const popup = window.open(
              "/erp/palette-popup",
              "erp-palette-popup",
              "width=420,height=720,resizable=yes,scrollbars=yes,toolbar=no,menubar=no"
            );
            if (!popup) {
              _showToast("Popup blokován prohlížečem — povol popups pro tuto stránku", "error", 4000);
              return;
            }
            // Close parent modal — popup je teted primary palette
            // (Marti's intent: detach + use popup ve standalone režimu).
            // Pokud Marti chce obojí, ot evře +Pole znovu.
            popup.focus();
            _showToast("Paleta otevřena v okně. Drag z popup → drop na ERP form.", "success", 3500);
            this._shell.close();
          });
          // Insert pred closeBtn (poslední button v rightActions)
          const closeBtn = headerActions.querySelector("button:last-child");
          if (closeBtn) {
            headerActions.insertBefore(detachBtn, closeBtn);
          } else {
            headerActions.appendChild(detachBtn);
          }
        }
      } catch (e) {
        console.warn("[FieldPickerModal] detach button attach failed:", e);
      }

      // Body styling — same as DesignFwForm (flex column)
      if (this._shell.body) {
        this._shell.body.style.display = "flex";
        this._shell.body.style.flexDirection = "column";
        this._shell.body.style.padding = "12px 16px";
      }
      // Dialog explicit height pro layout stability
      if (this._shell.dialog) {
        this._shell.dialog.style.minHeight = "500px";
      }

      // Loading state
      const loading = document.createElement("div");
      loading.style.cssText = "padding:20px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám paletu komponent…";
      this._shell.body.appendChild(loading);

      try {
        // Phase 38.4 Krok 14c+1 (14.5.2026 vecer): pridan parent_comp_def_id
        // query param. Backend pak vraci `existing_comp_def_id` per column,
        // ktery rozdeli sloupce do "available" / "already on form" tabs.
        const ecUrl = "/api/v1/erp/design/entity-columns/" +
                      encodeURIComponent(this.opts.entityType) +
                      (this.opts.parentCompDefId
                        ? "?parent_comp_def_id=" + encodeURIComponent(this.opts.parentCompDefId)
                        : "");
        // Parallel fetch — comp_types + entity_columns (s merge)
        const [ctResp, ecResp] = await Promise.all([
          fetch("/api/v1/erp/design/comp-types", { credentials: "include" }),
          fetch(ecUrl, { credentials: "include" }),
        ]);
        if (!ctResp.ok) throw new Error("comp-types HTTP " + ctResp.status);
        if (!ecResp.ok) throw new Error("entity-columns HTTP " + ecResp.status);
        const ctData = await ctResp.json();
        const ecData = await ecResp.json();
        if (!ctData.ok) throw new Error("comp-types: " + (ctData.error || "unknown"));
        if (!ecData.ok) throw new Error("entity-columns: " + (ecData.error || "unknown"));

        this._compTypes = ctData.items || [];
        this._compTypesById = {};
        for (const ct of this._compTypes) this._compTypesById[ct.id] = ct;
        this._columns = ecData.columns || [];
        // Phase 38.4 Krok H+5 (26.5.2026): containers v "Jiz na forme"
        this._existingContainers = ecData.existing_containers || [];

        // Phase 38.4 Krok 14c+1: rozdeleni do dvou kolekci podle existing
        this._columnsAvailable = this._columns.filter(
          c => c.existing_comp_def_id == null
        );
        this._columnsOnForm = this._columns.filter(
          c => c.existing_comp_def_id != null
        );
        // Active tab — default 'available' (kde user akce sedi)
        this._activeTab = "available";

        this._render();
      } catch (e) {
        loading.style.color = "#e88";
        loading.textContent = "Načítání selhalo: " + (e.message || e);
        console.error("[FieldPickerModal] load failed:", e);
      }
    }

    // Phase 38.4 Krok 14c+1: switch tab + re-render body
    _switchTab(tabKey) {
      if (this._activeTab === tabKey) return;
      this._activeTab = tabKey;
      this._render();
    }

    // Phase 38.4 Krok 14c+1: tab strip header (button per tab + counter
    // badge). Pattern z UI Kit ErpPageControl, ale inline pro modal (no
    // dependency, ne velka komponenta v jenom palette).
    _renderTabStrip() {
      const strip = document.createElement("div");
      strip.style.cssText =
        "display:flex;gap:2px;border-bottom:1px solid #2a3340;margin-bottom:10px;";

      // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
      // tab): paleta panel + groupbox pro drag-drop na formular. Marti's
      // choice A: rozsireni existing FieldPickerModal o novy tab (vs
      // samostatny PanelPickerModal).
      const tabs = [
        {
          key: "available",
          label: "Schází přidat",
          count: this._columnsAvailable.length,
          accent: "#5dbf5d",
        },
        {
          key: "onform",
          // Phase 38.4 Krok H+5: count includes containers (panel/groupbox/...)
          label: "Již na formě",
          count: this._columnsOnForm.length + (this._existingContainers || []).length,
          accent: "#7ed4e8",
        },
        {
          key: "preview",
          label: "Preview",
          count: null,
          accent: "#d4b88a",
        },
        {
          key: "layout",
          label: "📐 Layout",
          count: null,
          accent: "#a88cd4",
        },
      ];

      for (const t of tabs) {
        const btn = document.createElement("button");
        btn.type = "button";
        const active = this._activeTab === t.key;
        const countStr = t.count != null ? " (" + t.count + ")" : "";
        btn.textContent = t.label + countStr;
        btn.style.cssText =
          "padding:6px 14px;background:" + (active ? "#1f2530" : "transparent") +
          ";border:1px solid " + (active ? "#3a4754" : "transparent") +
          ";border-bottom:" + (active
            ? "3px solid " + t.accent
            : "3px solid transparent") +
          ";color:" + (active ? t.accent : "#8a96a4") +
          ";cursor:pointer;font-size:12px;font-weight:" + (active ? "600" : "400") +
          ";border-radius:3px 3px 0 0;transition:color 0.15s;";
        btn.addEventListener("click", () => this._switchTab(t.key));
        btn.addEventListener("mouseenter", () => {
          if (!active) btn.style.color = "#cfd6df";
        });
        btn.addEventListener("mouseleave", () => {
          if (!active) btn.style.color = "#8a96a4";
        });
        strip.appendChild(btn);
      }
      return strip;
    }

    _render() {
      this._shell.body.innerHTML = "";

      // Phase 38.4 Krok 14c+1 (14.5.2026 vecer, Marti's "tabsheet pro
      // schazi/na forme/preview"): tab strip + tab content + footer.
      // Header counter agreguje cisla per tab.
      this._shell.body.appendChild(this._renderTabStrip());

      // Top hint (per tab)
      const hint = document.createElement("div");
      hint.style.cssText = "color:#8a96a4;font-size:12px;margin-bottom:10px;line-height:1.5;";
      if (this._activeTab === "available") {
        hint.innerHTML =
          "Klikni na řádek pro výběr / odznačení. Typ komponenty lze přepsat " +
          "pres dropdown vpravo. <b>" + this._columnsAvailable.length +
          "</b> sloupců zbývá přidat.";
      } else if (this._activeTab === "onform") {
        hint.innerHTML =
          "<b>" + this._columnsOnForm.length + "</b> polí už je na formě. " +
          "Klikni na ✕ vpravo pro odebrání (soft delete — komponenta zmizí " +
          "z formu, ale data v DB zůstanou).";
      } else if (this._activeTab === "preview") {
        hint.innerHTML =
          "Preview formuláře po insertu vybraných polí. " +
          "<span style=\"opacity:0.7;font-style:italic;\">(Phase 38.4 Krok 14c+2 — TODO)</span>";
      } else if (this._activeTab === "layout") {
        hint.innerHTML =
          "<b style=\"color:#a88cd4;\">📐 Layout containers</b> — strukturální komponenty (panel + groupbox). " +
          "Drag kartu na formulář → vytvořit novy container. Default panel align='client', " +
          "groupbox border_mode='top'. Změna parametrů pres right-click na panel/groupbox.";
      }
      this._shell.body.appendChild(hint);

      // Tab content container — scrollable list of rows
      const content = document.createElement("div");
      content.style.cssText =
        "flex:1 1 auto;overflow-y:auto;border:1px solid #2a3340;border-radius:4px;background:#0f141a;";
      this._shell.body.appendChild(content);

      // Render per active tab
      if (this._activeTab === "available") {
        if (this._columnsAvailable.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "padding:24px;text-align:center;color:#5dbf5d;font-size:13px;";
          empty.innerHTML = "✓ Všechny sloupce už jsou na formě. Není co přidat.";
          content.appendChild(empty);
        } else {
          for (const col of this._columnsAvailable) {
            content.appendChild(this._renderColumnRow(col));
          }
        }
      } else if (this._activeTab === "onform") {
        // Phase 38.4 Krok H+5 (26.5.2026, Marti's "panel je komponenta"):
        // Render containers + inputs uniformne. Containers first (structural
        // top), pak inputs (data fields).
        const containers = this._existingContainers || [];
        if (this._columnsOnForm.length === 0 && containers.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "padding:24px;text-align:center;color:#8a96a4;font-size:13px;";
          empty.innerHTML = "Form je zatím prázdný — žádné pole ani container.";
          content.appendChild(empty);
        } else {
          for (const cont of containers) {
            content.appendChild(this._renderOnFormContainerRow(cont));
          }
          for (const col of this._columnsOnForm) {
            content.appendChild(this._renderOnFormRow(col));
          }
        }
      } else if (this._activeTab === "preview") {
        // Phase 38.4 Krok 14c+2 part A (14.5.2026 odpoledne po IT prezentaci):
        // Preview gallery — visual paleta dostupných komponent. Marti's "pro
        // relax" iteration. Per card: preview_html v iframe + label +
        // comp_type code (mono) + draggable=true (foundation pro Part B
        // drag-drop na DesignFwForm main panel).
        //
        // Filter: form-relevant typy (input, dropdown, memo, button, atd.) —
        // grid-only typy (grid_modern, grid_column, 7 column types) skip,
        // protoze nepouzitelne v form fields. Whitelist by renderer_hint
        // OR code prefix.
        const FORM_RELEVANT_HINTS = new Set([
          "input", "input-number", "textarea", "checkbox",
          "select", "multiselect", "datepicker", "datetimepicker",
          "timepicker", "button", "speedbutton",
          "fieldset",     // groupbox container
          "tabs_outer",   // pagecontrol container
          "tab_inner",    // tabsheet container
          "label",        // label / label_readonly
          "fileupload",   // file
          "md_render",    // markdown_view
        ]);
        const galleryItems = (this._compTypes || []).filter(ct =>
          FORM_RELEVANT_HINTS.has(ct.renderer_hint) ||
          ["label", "edit", "checkbox", "combobox", "memo", "number",
           "checkbox_modern", "date_modern", "datetime", "lookup",
           "lookup_multi", "file", "label_readonly", "groupbox",
           "pagecontrol", "tabsheet", "button", "richedit"].includes(ct.code)
        );

        // Hint
        const galleryHint = document.createElement("div");
        galleryHint.style.cssText =
          "padding:10px 14px;color:#8a96a4;font-size:11px;line-height:1.5;background:#141a20;border-bottom:1px solid #2a3340;";
        galleryHint.innerHTML =
          "<b style=\"color:#d4b88a;\">🎨 Paleta komponent</b> — " +
          galleryItems.length + " typů dostupných pro formuláře. " +
          "Klikni na kartu pro detail. <span style=\"opacity:0.7;font-style:italic;\">" +
          "(Drag-and-drop na formulář přijde v části B.)</span>";
        content.appendChild(galleryHint);

        // Gallery grid (3 columns auto-fit)
        const gallery = document.createElement("div");
        gallery.style.cssText =
          "padding:12px;display:grid;" +
          "grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));" +
          "gap:12px;";
        content.appendChild(gallery);

        if (galleryItems.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "grid-column:1/-1;padding:24px;text-align:center;color:#8a96a4;";
          empty.innerHTML = "Žádné form-relevant komponenty s preview_html. " +
                            "UPDATE fw.comp_type SET preview_html=... pro form fields.";
          gallery.appendChild(empty);
        } else {
          for (const ct of galleryItems) {
            gallery.appendChild(this._renderGalleryCard(ct));
          }
        }
      } else if (this._activeTab === "layout") {
        // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
        // tab): paleta strukturalnich komponent (panel + groupbox).
        // Filter: kind='container'. Backend (Krok 14f-C fix) uz prefiltruje
        // status='active' — frontend dropnu redundantni check.
        const layoutItems = (this._compTypes || []).filter(ct =>
          ct.kind === "container"
        );

        // Gallery grid (2-3 columns wider cards pro layout types)
        const gallery = document.createElement("div");
        gallery.style.cssText =
          "padding:12px;display:grid;" +
          "grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));" +
          "gap:12px;";
        content.appendChild(gallery);

        if (layoutItems.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "grid-column:1/-1;padding:24px;text-align:center;color:#8a96a4;";
          empty.innerHTML =
            "Žádné active container types. UPDATE fw.comp_type SET status='active' " +
            "pro panel (id=13) + groupbox (id=12).";
          gallery.appendChild(empty);
        } else {
          for (const ct of layoutItems) {
            gallery.appendChild(this._renderLayoutCard(ct));
          }
        }
      }

      // Footer bar — Selected count + actions
      const footer = document.createElement("div");
      footer.style.cssText =
        "margin-top:12px;display:flex;align-items:center;justify-content:flex-end;gap:16px;" +
        "border-top:1px solid #2a3340;padding-top:10px;";
      const counter = document.createElement("span");
      counter.id = "fpmCounter";
      counter.style.cssText = "color:#a8b4c2;font-size:12px;margin-right:auto;";
      counter.textContent = "Vybráno: " + this._selected.size;
      footer.appendChild(counter);

      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr"): drop "Přidat
      // vybraná" submit button. Checkbox = instant POST single column (live
      // sync s formem). Žádný batch flow, žádné Submit.

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.style.cssText =
        "min-width:90px;padding:6px 16px;background:#2a3340;border:1px solid #3a4754;" +
        "border-radius:3px;color:#cfd6df;cursor:pointer;font-size:13px;";
      cancelBtn.innerHTML = this._activeTab === "available"
        ? '<span style="color:#d4888a;font-weight:700;margin-right:6px;">✗</span>Storno'
        : 'Zavřít';
      cancelBtn.addEventListener("click", () => this._shell.close());
      footer.appendChild(cancelBtn);

      this._shell.body.appendChild(footer);
    }

    // Phase 38.4 Krok 14c+1: render row v tabu "Již na formě".
    // Read-only display (name, caption, current type) + ✕ remove button.
    _renderOnFormRow(col) {
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "X jako prvni"):
      // Grid template column order: 32px (remove) | 200px | 1fr | 140px.
      // Symetrie s "Schazi pridat" tab kde checkbox je prvni (left).
      const row = document.createElement("div");
      row.style.cssText =
        "display:grid;grid-template-columns:32px 200px 1fr 140px 32px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "background:rgba(126,212,232,0.04);";

      // 1. Column name + caption
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
      const labelName = document.createElement("div");
      labelName.style.cssText = "font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#9bb5d6;";
      labelName.textContent = col.name;
      const labelCap = document.createElement("div");
      labelCap.style.cssText = "font-size:13px;color:#e8eef5;";
      labelCap.textContent = col.existing_label || col.caption_default;
      labelWrap.appendChild(labelName);
      labelWrap.appendChild(labelCap);

      // 2. Region slot badge + type label + comp_def id (info)
      const meta = document.createElement("div");
      meta.style.cssText = "color:#8a96a4;font-size:11px;";
      const ct = this._compTypesById[col.existing_type_id];
      meta.innerHTML =
        "<span style=\"background:#1f2530;padding:2px 6px;border-radius:3px;margin-right:6px;\">" +
        (col.existing_region_slot || "main") + "</span>" +
        (ct ? ct.label : "type#" + col.existing_type_id);

      // 3. Type dropdown — Phase 38.4 Krok H+5 (26.5.2026, Marti's "menit
      // dynamicky"): change comp_type live na existing field. PATCH
      // /design/comp-def/update/{id} s type_id. Po success: form re-render
      // (onComplete trigger).
      const typeSel = document.createElement("select");
      typeSel.title = "Změnit typ komponenty (PATCH live)";
      typeSel.style.cssText =
        "padding:4px 8px;background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
        "border-radius:3px;font-size:12px;cursor:pointer;";
      for (const ct of this._compTypes) {
        const opt = document.createElement("option");
        opt.value = String(ct.id);
        opt.textContent = ct.label + " (id=" + ct.id + ")";
        if (ct.id === col.existing_type_id) opt.selected = true;
        typeSel.appendChild(opt);
      }
      typeSel.addEventListener("change", async () => {
        const newId = parseInt(typeSel.value, 10);
        const oldId = col.existing_type_id;
        if (newId === oldId) return;
        typeSel.disabled = true;
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/update/" + col.existing_comp_def_id,
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ type_id: newId }),
            }
          );
          const d = await r.json().catch(() => ({}));
          if (!r.ok || !d.ok) {
            throw new Error(d.error || ("HTTP " + r.status));
          }
          col.existing_type_id = newId;
          _showToast(
            "Typ změněn: " + (this._compTypesById[newId] || {}).label,
            "success", 1500
          );
          // Live sync — parent form reload (component re-render s novym typem)
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ typeChanged: 1 }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] type change failed:", e);
          _showToast("Změna typu selhala: " + (e.message || e), "error", 3000);
          typeSel.value = String(oldId);  // revert UI
        } finally {
          typeSel.disabled = false;
        }
      });

      // 4. ✕ remove button
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.textContent = "✕";
      removeBtn.title = "Odebrat pole z formuláře (soft delete — is_active=false)";
      removeBtn.style.cssText =
        "width:28px;height:28px;background:transparent;border:1px solid #3a4754;" +
        "color:#d4888a;cursor:pointer;border-radius:3px;font-size:14px;";
      removeBtn.addEventListener("mouseenter", () => {
        removeBtn.style.background = "#3a1f1f";
        removeBtn.style.borderColor = "#d4888a";
      });
      removeBtn.addEventListener("mouseleave", () => {
        removeBtn.style.background = "transparent";
        removeBtn.style.borderColor = "#3a4754";
      });
      removeBtn.addEventListener("click", async () => {
        // Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr"):
        // Drop confirm dialog — klik X = instant DELETE. Soft delete je
        // reverzibilní (is_active=false), takze zadny "harm" pri nahodnem
        // kliku. Live sync s formem pres onComplete reload.
        removeBtn.disabled = true;
        try {
          const r = await fetch("/api/v1/erp/design/comp-def/" + col.existing_comp_def_id, {
            method: "DELETE",
            credentials: "include",
          });
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast("Pole odebráno", "success");
          // Move column z onForm → available + re-render
          col.existing_comp_def_id = null;
          col.existing_label = null;
          col.existing_region_slot = null;
          col.existing_type_id = null;
          this._columnsAvailable.push(col);
          this._columnsOnForm = this._columnsOnForm.filter(c => c !== col);
          this._render();
          // Parent form refresh — analog onComplete callback
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ removed: 1 }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] remove failed:", e);
          _showToast("Odebrání selhalo: " + (e.message || e), "error", 3500);
          removeBtn.disabled = false;
        }
      });

      // ⚙ Settings button (Krok H+5) — popup s caption + layout + defaults
      const settingsBtn = this._makeSettingsBtn({
        col: col,
        mode: "onform",
        compDefId: col.existing_comp_def_id,
        typeId: col.existing_type_id,
      });

      // X jako prvni — symetrie s "Schazi pridat" checkbox left placement
      row.appendChild(removeBtn);
      row.appendChild(labelWrap);
      row.appendChild(meta);
      row.appendChild(typeSel);
      row.appendChild(settingsBtn);
      return row;
    }

    // Phase 38.4 Krok 14c+2 part A.1 (14.5.2026 odpoledne, Marti's
    // "obdelnicky jsou super, jen drag jen ta komponenta uvnitr, ne cela
    // karta"):
    //
    // Card je teted kontextový rámeček (label + id + meta — NE draggable).
    // Drag = pouze first interactive element preview_html (input / button /
    // select / atd.). Drag preview = real DOM komponenta, ne 220px karta —
    // víc "živé", Marti uvidi přesně co bude na formě.
    //
    // Iframe → inline DOM s scoped CSS (drag nepřechází přes iframe
    // boundary). Scope CSS reset v hlavní stylesheet bloku (řádek ~510).
    _renderGalleryCard(ct) {
      const card = document.createElement("div");
      card.style.cssText =
        "background:#141a20;border:1px solid #2a3340;border-radius:5px;" +
        "padding:10px;cursor:default;transition:border-color 0.15s;" +
        "display:flex;flex-direction:column;gap:8px;";
      card.dataset.compTypeId = String(ct.id);
      card.dataset.compTypeCode = ct.code;
      // Card NEMÁ draggable=true — drag je delegated na vnitřní komponentu.

      // Hover accent na CARD (visual feedback že se s tím dá interagovat)
      card.addEventListener("mouseenter", () => {
        card.style.borderColor = "#3a8aa8";
      });
      card.addEventListener("mouseleave", () => {
        card.style.borderColor = "#2a3340";
      });

      // 1. Preview INLINE (replace iframe). preview_html injected do
      // scope wrap, first child se stane draggable handle.
      const previewWrap = document.createElement("div");
      previewWrap.style.cssText =
        "background:#1f2530;border-radius:3px;padding:6px;" +
        "min-height:42px;display:flex;align-items:center;justify-content:center;" +
        "overflow:hidden;";
      const previewScope = document.createElement("div");
      previewScope.className = "erp-gallery-preview-scope";
      previewScope.innerHTML = ct.preview_html ||
        "<span style=\"color:#8a96a4;font-size:11px;\">(no preview)</span>";

      // Phase 38.4 Krok 14c+3.5 (14.5.2026 odpoledne, Marti's bug "drag
      // funguje jen Lookup/LookupMulti/Checkbox/Label"):
      //
      // PATTERN ROOT CAUSE:
      //   Funguje:    <select>, <label>  → container elementy bez vlastní
      //               interaction model
      //   Nefunguje:  <input>, <button>, <textarea> → mají vlastní pointer
      //               behavior co interferuje s HTML5 DnD v Chrome:
      //                 <input readonly>: text-select claims drag space
      //                 <button>: pointer event model nefire dragstart
      //                 <textarea>: text-select + scrollable same issue
      //
      // FIX: wrapper div approach — divs jsou universal drag handles.
      //   Pro input/button/textarea: wrapnout do <div draggable=true>,
      //   inner element + pointer-events:none (no interaction passing).
      //   Pro select/label: direct draggable (osvědčené pro 4 working
      //   komponenty Lookup/LookupMulti/Checkbox/Label).
      const innerEl = previewScope.querySelector(
        "input, select, textarea, button, label"
      ) || previewScope.firstElementChild;

      let dragHandle = null;
      if (innerEl) {
        const tag = innerEl.tagName;
        const needsWrapper = tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA";

        if (needsWrapper) {
          // Wrap input/button/textarea v div pro clean drag init.
          // Inner element pointer-events:none — no click/select interfere.
          const wrapperDiv = document.createElement("div");
          wrapperDiv.style.cssText =
            "display:inline-block;cursor:grab;line-height:0;";
          innerEl.parentNode.insertBefore(wrapperDiv, innerEl);
          wrapperDiv.appendChild(innerEl);
          innerEl.style.pointerEvents = "none";
          if (tag === "INPUT" || tag === "TEXTAREA") {
            innerEl.setAttribute("readonly", "");
          }
          dragHandle = wrapperDiv;
        } else {
          // <select> / <label> / fallback firstElementChild: direct draggable
          dragHandle = innerEl;
          if (tag === "SELECT") {
            dragHandle.style.pointerEvents = "auto";
          }
        }
      }

      if (dragHandle) {
        dragHandle.setAttribute("draggable", "true");
        dragHandle.style.cursor = "grab";
        // Phase 38.4 Krok 14c+3.5: mousedown preventDefault není potřeba
        // (wrapper div approach pro input/button/textarea + native drag pro
        // select/label — žádný text-select interference).
        dragHandle.addEventListener("dragstart", (ev) => {
          ev.stopPropagation();
          dragHandle.style.opacity = "0.5";
          dragHandle.style.cursor = "grabbing";
          ev.dataTransfer.effectAllowed = "copy";
          ev.dataTransfer.setData(
            "application/x-erp-comp-type",
            JSON.stringify({ id: ct.id, code: ct.code, label: ct.label })
          );
          ev.dataTransfer.setData("text/plain", ct.code);
        });
        dragHandle.addEventListener("dragend", () => {
          dragHandle.style.opacity = "1";
          dragHandle.style.cursor = "grab";
        });
      }

      previewWrap.appendChild(previewScope);
      card.appendChild(previewWrap);

      // 2. Label (human-readable)
      const lbl = document.createElement("div");
      lbl.style.cssText = "font-size:13px;color:#e8eef5;font-weight:600;";
      lbl.textContent = ct.label;
      card.appendChild(lbl);

      // 3. Comp type code + id (mono, subtle)
      const code = document.createElement("div");
      code.style.cssText =
        "font-family:ui-monospace,Consolas,monospace;font-size:10px;" +
        "color:#7ed4e8;opacity:0.7;";
      code.textContent = ct.code + " · id=" + ct.id;
      card.appendChild(code);

      // 4. Footer (kind badge + description short)
      const meta = document.createElement("div");
      meta.style.cssText =
        "font-size:10px;color:#8a96a4;line-height:1.3;" +
        "border-top:1px solid #1a2028;padding-top:6px;margin-top:auto;";
      const kindBadge =
        "<span style=\"background:#1f2530;padding:1px 5px;border-radius:2px;margin-right:4px;\">" +
        (ct.kind || "leaf") + "</span>";
      meta.innerHTML = kindBadge + (ct.description || "").slice(0, 60);
      card.appendChild(meta);

      // Click na card (mimo dragHandle) → toast hint pro discoverability
      card.addEventListener("click", (ev) => {
        // Skip pokud klik na drag handle (komponenta uvnitř)
        if (dragHandle && (ev.target === dragHandle || dragHandle.contains(ev.target))) {
          return;
        }
        _showToast(
          ct.label + " (" + ct.code + ") — drag tu komponentu nahoře na formulář",
          "info",
          2200
        );
      });

      return card;
    }

    // ════════════════════════════════════════════════════════════════
    // Phase 38.4 Krok 14f-C (14.5.2026 vecer, Marti's "Layout containers"
    // tab): render karta pro container type (panel/groupbox).
    // Analog _renderGalleryCard ale s container-specific:
    //   - Visual: large emoji/icon (📦 panel, ▦ groupbox)
    //   - Description: align (panel) / border (groupbox) hints
    //   - Draggable=true s payload {id, code, label, layout: default}
    //   - Drop pipeline → DesignFwForm._attachDropTargetForGalleryDrag
    //     receives layout in payload, POST /design/comp-def s layout JSONB
    // ════════════════════════════════════════════════════════════════
    _renderLayoutCard(ct) {
      const card = document.createElement("div");
      card.style.cssText =
        "background:#0f141a;border:1px solid #2a3340;border-radius:6px;" +
        "padding:14px;display:flex;flex-direction:column;gap:8px;" +
        "transition:border-color 0.15s, transform 0.15s;" +
        "position:relative;";
      card.addEventListener("mouseenter", () => {
        card.style.borderColor = "#a88cd4";
      });
      card.addEventListener("mouseleave", () => {
        card.style.borderColor = "#2a3340";
      });

      // Per-type icon + visual hint
      const isPanel = ct.code === "panel";
      const isGroupbox = ct.code === "groupbox";
      const icon = isPanel ? "📦" : (isGroupbox ? "▦" : "▣");
      const accentColor = isPanel ? "#a88cd4" : "#d4b88a";

      // Default layout pro drag payload (drop pipeline pouzije pro POST body)
      let defaultLayout;
      if (isPanel) {
        defaultLayout = { align: "client" };
      } else if (isGroupbox) {
        defaultLayout = { border_mode: "top", label: null };
      } else {
        defaultLayout = {};
      }

      // 1. Icon + visual hint
      const visualWrap = document.createElement("div");
      visualWrap.style.cssText =
        "padding:12px;background:#141a20;border:1px dashed " + accentColor + ";" +
        "border-radius:4px;display:flex;align-items:center;justify-content:center;" +
        "gap:8px;min-height:60px;cursor:grab;";
      visualWrap.setAttribute("draggable", "true");

      const iconEl = document.createElement("span");
      iconEl.textContent = icon;
      iconEl.style.cssText = "font-size:28px;line-height:1;";
      visualWrap.appendChild(iconEl);

      const iconLabel = document.createElement("span");
      iconLabel.textContent = ct.label;
      iconLabel.style.cssText = "font-size:14px;color:" + accentColor + ";font-weight:600;";
      visualWrap.appendChild(iconLabel);

      visualWrap.addEventListener("dragstart", (ev) => {
        ev.stopPropagation();
        visualWrap.style.opacity = "0.5";
        visualWrap.style.cursor = "grabbing";
        ev.dataTransfer.effectAllowed = "copy";
        // Phase 38.4 Krok 14f-C: payload obsahuje layout (default per code)
        // — DesignFwForm drop handler ho posila do POST body.
        ev.dataTransfer.setData(
          "application/x-erp-comp-type",
          JSON.stringify({
            id: ct.id,
            code: ct.code,
            label: ct.label,
            layout: defaultLayout,  // novy klic — backend pass-through
            is_container: true,
          })
        );
        ev.dataTransfer.setData("text/plain", ct.code);
      });
      visualWrap.addEventListener("dragend", () => {
        visualWrap.style.opacity = "1";
        visualWrap.style.cursor = "grab";
      });

      card.appendChild(visualWrap);

      // 2. Label (human-readable)
      const lbl = document.createElement("div");
      lbl.style.cssText = "font-size:13px;color:#e8eef5;font-weight:600;";
      lbl.textContent = ct.label;
      card.appendChild(lbl);

      // 3. Code + id (mono)
      const code = document.createElement("div");
      code.style.cssText =
        "font-family:ui-monospace,Consolas,monospace;font-size:10px;" +
        "color:" + accentColor + ";opacity:0.7;";
      code.textContent = ct.code + " · id=" + ct.id;
      card.appendChild(code);

      // 4. Default behavior hint (per-type)
      const meta = document.createElement("div");
      meta.style.cssText =
        "font-size:10px;color:#8a96a4;line-height:1.4;" +
        "border-top:1px solid #1a2028;padding-top:6px;margin-top:auto;";
      let hint;
      if (isPanel) {
        hint = "Strukturální container (alClient default). " +
               "Right-click pro nastavení align/width/height.";
      } else if (isGroupbox) {
        hint = "Vizuální wrapper s linkou nahoře (default). " +
               "Optional label. Drag dovnitř panelu.";
      } else {
        hint = ct.description || "Container component.";
      }
      meta.innerHTML = '<span style="background:#1f2530;padding:1px 5px;border-radius:2px;margin-right:4px;">container</span>' + hint;
      card.appendChild(meta);

      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr i pro layout"):
      // Click na card = instant POST + live sync s formem (paralel s
      // checkbox checked v "Schazi pridat"). Container muze byt vicekrat —
      // auto-generated unique name (e.g. "panel_2", "groupbox_3").
      // Visual feedback: "+" badge top-right, cursor pointer, hover green.
      const addBadge = document.createElement("div");
      addBadge.textContent = "+";
      addBadge.title = "Klik = pridat na formular";
      addBadge.style.cssText =
        "position:absolute;top:6px;right:6px;width:22px;height:22px;" +
        "background:#3a7a3a;color:#e8eef5;border-radius:50%;" +
        "display:flex;align-items:center;justify-content:center;" +
        "font-size:16px;font-weight:700;line-height:1;cursor:pointer;" +
        "transition:background 0.12s, transform 0.12s;";
      addBadge.addEventListener("mouseenter", () => {
        addBadge.style.background = "#4a9a4a";
        addBadge.style.transform = "scale(1.15)";
      });
      addBadge.addEventListener("mouseleave", () => {
        addBadge.style.background = "#3a7a3a";
        addBadge.style.transform = "scale(1)";
      });
      card.appendChild(addBadge);

      const doAdd = async () => {
        // Auto-generate unique name: <code>_<N> kde N = pocet existing + 1
        // (defensive — backend dela uniqueness check stejne).
        const ts = Date.now().toString(36).slice(-4);
        const autoName = ct.code + "_" + ts;
        addBadge.style.pointerEvents = "none";
        addBadge.textContent = "…";
        try {
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              parent_comp_def_id: this._resolveTargetParentId(),
              name: autoName,
              caption: ct.label,
              type_id: ct.id,
              region_slot: "main",
              layout: defaultLayout,
            }),
          });
          const d = await r.json().catch(() => ({}));
          if (!r.ok || !d.ok) {
            throw new Error(d.error || ("HTTP " + r.status));
          }
          _showToast("Přidáno: " + ct.label, "success", 1500);
          // Phase 38.4 Krok H+5 (26.5.2026, Marti's "neobcerstvi Jiz na forme"):
          // Refresh paleta state — novy container se objevi v "Jiz na forme"
          // tab. Bez tohoto refresh paleta vlastni state je stale (jen onComplete
          // refreshuje form, ne paletu).
          try {
            await this._refreshState();
            this._render();
          } catch (refErr) {
            console.error("[FieldPickerModal] refresh after container add failed:", refErr);
          }
          // Live sync — parent form reload
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ added: 1, container: true }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] container add failed:", e);
          _showToast("Přidání selhalo: " + (e.message || e), "error", 3000);
        } finally {
          addBadge.style.pointerEvents = "auto";
          addBadge.textContent = "+";
        }
      };

      // Click na card OR add badge → instant POST (drag visualWrap je
      // separe; chovani pres dataTransfer setData).
      card.addEventListener("click", (ev) => {
        if (visualWrap.contains(ev.target) && ev.target !== visualWrap) return;
        doAdd();
      });
      card.style.cursor = "pointer";

      return card;
    }

    _renderColumnRow(col) {
      const row = document.createElement("div");
      row.style.cssText =
        "display:grid;grid-template-columns:24px 200px 1fr 160px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "cursor:pointer;transition:background 0.1s;";
      row.addEventListener("mouseenter", () => row.style.background = "#141a20");
      row.addEventListener("mouseleave", () => {
        row.style.background = this._selected.has(col.name) ? "#1a2530" : "transparent";
      });

      // 1. Checkbox — Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr"):
      // Instant POST single column na check. Žádný submit button, žádný batch.
      // Klik = okamžitě komponenta na formu + live sync (onComplete reload).
      // Uncheck = no-op (jen UI affordance pro vizuální feedback).
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.style.cssText = "width:16px;height:16px;cursor:pointer;";
      cb.addEventListener("change", async () => {
        if (!cb.checked) {
          // Uncheck — jen UI state reset (komponenta uz na formu pres prvni
          // check + POST). Pro delete uziva X button v "Jiz na forme" tab.
          row.style.background = "transparent";
          return;
        }
        // Check → instant POST
        cb.disabled = true;
        row.style.background = "#1a2530";
        const typeId = this._typeOverrides[col.name] || col.suggested_type_id;
        try {
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              parent_comp_def_id: this._resolveTargetParentId(),
              name: col.name,
              caption: col.caption_default,
              type_id: typeId,
              region_slot: "main",
            }),
          });
          const d = await r.json().catch(() => ({}));
          if (!r.ok || !d.ok) {
            throw new Error(d.error || ("HTTP " + r.status));
          }
          _showToast("Přidáno: " + col.name, "success", 1500);
          // Move column z available → onForm (in-memory) + re-render
          col.existing_comp_def_id = d.comp_def_id || d.id || null;
          col.existing_label = col.caption_default;
          col.existing_region_slot = "main";
          col.existing_type_id = typeId;
          this._columnsOnForm.push(col);
          this._columnsAvailable = this._columnsAvailable.filter(c => c !== col);
          this._render();
          // Live sync — parent form reload (komponenta se okamžitě zobrazí)
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ added: 1 }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] instant add failed:", e);
          _showToast("Přidání selhalo: " + (e.message || e), "error", 3000);
          cb.checked = false;
          cb.disabled = false;
          row.style.background = "transparent";
        }
      });

      // 2. Column name + caption
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
      const labelName = document.createElement("div");
      labelName.style.cssText = "font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#9bb5d6;";
      labelName.textContent = col.name;
      const labelCap = document.createElement("div");
      labelCap.style.cssText = "font-size:13px;color:#e8eef5;";
      labelCap.textContent = col.caption_default;
      labelWrap.appendChild(labelName);
      labelWrap.appendChild(labelCap);

      // 3. Preview (iframe srcdoc — Marti-AI's "sandbox isolation is gift")
      const previewWrap = document.createElement("div");
      previewWrap.style.cssText = "min-height:36px;display:flex;align-items:center;";
      const initialTypeId = this._typeOverrides[col.name] || col.suggested_type_id;
      const initialCt = this._compTypesById[initialTypeId];
      const iframe = this._buildPreviewIframe(initialCt);
      previewWrap.appendChild(iframe);

      // 4. Type override dropdown
      const typeSel = document.createElement("select");
      typeSel.style.cssText =
        "padding:4px 8px;background:#1f2530;border:1px solid #2a3340;color:#cfd6df;" +
        "border-radius:3px;font-size:12px;cursor:pointer;";
      for (const ct of this._compTypes) {
        const opt = document.createElement("option");
        opt.value = String(ct.id);
        opt.textContent = ct.label + " (id=" + ct.id + ")";
        if (ct.id === initialTypeId) opt.selected = true;
        typeSel.appendChild(opt);
      }
      typeSel.addEventListener("change", () => {
        const newId = parseInt(typeSel.value, 10);
        this._typeOverrides[col.name] = newId;
        // Re-render preview iframe
        previewWrap.innerHTML = "";
        const newIframe = this._buildPreviewIframe(this._compTypesById[newId]);
        previewWrap.appendChild(newIframe);
      });

      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "jen pres checkbox"):
      // Drop row click toggle — akce jen na explicit checkbox click.
      // Predtim klik doprostred kompounenty (label/preview) trigger POST,
      // coz vedlo k nahodnym pridanim.

      row.appendChild(cb);
      row.appendChild(labelWrap);
      row.appendChild(previewWrap);
      row.appendChild(typeSel);
      return row;
    }

    _buildPreviewIframe(compType) {
      const iframe = document.createElement("iframe");
      // iframe srcdoc — sandbox isolation (Marti-AI's "gift")
      // Default theme styling pro consistent look napříč all comp_types
      const srcdoc =
        '<!DOCTYPE html><html><head><style>' +
        'body{margin:0;padding:4px 6px;background:transparent;' +
        'font-family:system-ui,-apple-system,sans-serif;font-size:12px;color:#cfd6df;}' +
        'input,select,textarea,button{font-family:inherit;font-size:12px;' +
        'background:#1f2530;border:1px solid #2a3340;color:#cfd6df;border-radius:3px;' +
        'padding:3px 6px;width:auto;max-width:100%;}' +
        'input[type="checkbox"]{width:14px;height:14px;}' +
        'label{display:flex;align-items:center;gap:5px;}' +
        '</style></head><body>' +
        (compType && compType.preview_html ? compType.preview_html : '<span style="color:#8a96a4">(no preview)</span>') +
        '</body></html>';
      iframe.srcdoc = srcdoc;
      iframe.style.cssText =
        "width:100%;height:36px;border:none;background:transparent;" +
        "pointer-events:none;"; // Decorative only — Marti-AI's doctrine
      iframe.setAttribute("sandbox", "allow-same-origin");
      return iframe;
    }

    _updateCounter() {
      const counter = this._shell.body.querySelector("#fpmCounter");
      if (counter) counter.textContent = "Vybráno: " + this._selected.size;
    }

    async _handleSubmit(btnEl) {
      if (this._selected.size === 0) {
        alert("Vyber alespoň 1 pole z palety.");
        return;
      }

      const origHtml = btnEl.innerHTML;
      btnEl.disabled = true;
      btnEl.innerHTML = "⏳ Ukládám…";

      const parentId = this.opts.parentCompDefId;
      const results = { ok: [], failed: [], existing: [] };

      // Sequential POST per column (parallel by způsobit FK race conditions)
      for (const colName of this._selected) {
        const col = this._columns.find(c => c.name === colName);
        if (!col) continue;
        const typeId = this._typeOverrides[colName] || col.suggested_type_id;
        try {
          const r = await fetch("/api/v1/erp/design/comp-def", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              parent_comp_def_id: parentId,
              name: colName,
              caption: col.caption_default,
              type_id: typeId,
              region_slot: "main",
            }),
          });
          const d = await r.json();
          if (r.ok && d.ok) {
            if (d.existing) results.existing.push(colName);
            else results.ok.push(colName);
          } else {
            results.failed.push({ name: colName, error: d.error || "HTTP " + r.status });
          }
        } catch (e) {
          results.failed.push({ name: colName, error: e.message || String(e) });
        }
      }

      // Report results
      const okCount = results.ok.length;
      const existingCount = results.existing.length;
      const failedCount = results.failed.length;
      if (failedCount > 0) {
        const errLines = results.failed.map(f => "• " + f.name + ": " + f.error).join("\\n");
        alert(
          "Přidáno: " + okCount + ", už existovalo: " + existingCount + ", chyby: " + failedCount + "\\n\\n" +
          errLines
        );
        btnEl.disabled = false;
        btnEl.innerHTML = origHtml;
        return;
      }

      // Phase 38.4 Krok 14c+1: po success NEzavirat modal. Misto toho
      // refresh state z backendu + switch na "Na forme" tab — Marti
      // okamzite vidi pridana pole + muze pokracovat (further add /
      // remove / Preview). Modal je teted live form editor.
      btnEl.style.background = "#3a7a3a";
      btnEl.innerHTML = "✅ Přidáno (" + (okCount + existingCount) + ")";

      try {
        await this._refreshState();
        this._selected.clear();
        this._typeOverrides = {};
        this._activeTab = "onform"; // switch na vysledek
        // _render pretvori cely modal vc. footeru — toast oznamuje
        // success pro discoverability
        _showToast(
          "Přidáno: " + okCount + (existingCount > 0 ? ", existovalo: " + existingCount : ""),
          "success"
        );
        this._render();
      } catch (e) {
        console.error("[FieldPickerModal] refresh after submit failed:", e);
        // Fallback: stale close
        btnEl.disabled = false;
        btnEl.innerHTML = origHtml;
      }

      // Parent form refresh — analog DELETE flow
      if (typeof this.opts.onComplete === "function") {
        try { this.opts.onComplete({ added: okCount, existing: existingCount }); }
        catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
      }
    }

    // Phase 38.4 Krok 14c+1: re-fetch entity-columns s mergem existing
    // comp_def (po POST/DELETE). Updatuje _columns / _columnsAvailable /
    // _columnsOnForm in-place — caller pak vola _render().
    async _refreshState() {
      const ecUrl = "/api/v1/erp/design/entity-columns/" +
                    encodeURIComponent(this.opts.entityType) +
                    (this.opts.parentCompDefId
                      ? "?parent_comp_def_id=" + encodeURIComponent(this.opts.parentCompDefId)
                      : "");
      const r = await fetch(ecUrl, { credentials: "include" });
      if (!r.ok) throw new Error("entity-columns refresh HTTP " + r.status);
      const d = await r.json();
      if (!d.ok) throw new Error("entity-columns refresh: " + (d.error || "unknown"));
      this._columns = d.columns || [];
      this._columnsAvailable = this._columns.filter(c => c.existing_comp_def_id == null);
      this._columnsOnForm = this._columns.filter(c => c.existing_comp_def_id != null);
      // Phase 38.4 Krok H+5 (26.5.2026): refresh existing_containers
      this._existingContainers = d.existing_containers || [];
    }

    // Phase 38.4 Krok H+5 (26.5.2026, Marti's "panel je komponenta"):
    // Container row v "Jiz na forme" tab. Symetrie s _renderOnFormRow
    // (column input), ale meta = type_label badge (panel/groupbox/...).
    // X click = instant DELETE (Marti's "orchestr") + live sync.
    _renderOnFormContainerRow(cont) {
      const isActive = this._activeContainerCompDefId === cont.comp_def_id;
      const row = document.createElement("div");
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "radio button single-select"):
      // Grid: 32px (X) | 24px (radio) | 200px (caption) | 1fr (meta) | 140px (id).
      // Aktivni container ma green tint background + bold label.
      row.style.cssText =
        "display:grid;grid-template-columns:32px 24px 200px 1fr 140px 32px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        (isActive
          ? "background:rgba(93,191,93,0.12);border-left:3px solid #5dbf5d;"
          : "background:rgba(168,140,212,0.06);");

      // X remove button (PRVNI sloupec — parita s "Schazi pridat" cb)
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.textContent = "✕";
      removeBtn.title = "Odebrat container z formuláře (soft delete)";
      removeBtn.style.cssText =
        "width:28px;height:28px;background:transparent;border:1px solid #3a4754;" +
        "color:#d4888a;cursor:pointer;border-radius:3px;font-size:14px;";
      removeBtn.addEventListener("mouseenter", () => {
        removeBtn.style.background = "#3a1f1f";
        removeBtn.style.borderColor = "#d4888a";
      });
      removeBtn.addEventListener("mouseleave", () => {
        removeBtn.style.background = "transparent";
        removeBtn.style.borderColor = "#3a4754";
      });
      removeBtn.addEventListener("click", async () => {
        removeBtn.disabled = true;
        try {
          const r = await fetch(
            "/api/v1/erp/design/comp-def/" + cont.comp_def_id,
            { method: "DELETE", credentials: "include" }
          );
          if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error("HTTP " + r.status + ": " + (errBody.error || r.statusText));
          }
          _showToast("Container odebrán", "success");
          // Refresh state + re-render
          this._existingContainers = this._existingContainers.filter(
            c => c.comp_def_id !== cont.comp_def_id
          );
          this._render();
          if (typeof this.opts.onComplete === "function") {
            try { this.opts.onComplete({ removed: 1, container: true }); }
            catch (e) { console.error("[FieldPickerModal] onComplete failed:", e); }
          }
        } catch (e) {
          console.error("[FieldPickerModal] container remove failed:", e);
          _showToast("Odebrání selhalo: " + (e.message || e), "error", 3500);
          removeBtn.disabled = false;
        }
      });

      // Radio button — single-select active container (Marti's pattern).
      // Klik = activate this container (deactivate predchozi), nove
      // komponenty pak jdou jako deti tohoto containeru.
      const radioWrap = document.createElement("div");
      radioWrap.style.cssText =
        "display:flex;align-items:center;justify-content:center;cursor:pointer;";
      radioWrap.title = isActive
        ? "Aktivní cíl — nové komponenty z palety půjdou sem"
        : "Klik = nastavit jako aktivní cíl (jeden na formuláři)";
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "fpm_active_container";  // single-select group
      radio.checked = isActive;
      radio.style.cssText = "width:16px;height:16px;cursor:pointer;accent-color:#5dbf5d;";
      radio.addEventListener("change", () => {
        if (radio.checked) {
          this._activeContainerCompDefId = cont.comp_def_id;
          _showToast(
            "Aktivní cíl: " + (cont.caption || cont.type_label),
            "info", 1500
          );
          this._render();  // re-render — highlight + tab counter hint
          // Phase 38.4 Krok H+5 (26.5.2026, Marti's "zvyraznit na forme"):
          // Notify parent (DesignFwForm) — highlight container DOM element
          // [data-comp-def-id="X"] s green border/glow.
          if (typeof this.opts.onActiveContainerChange === "function") {
            try { this.opts.onActiveContainerChange(cont.comp_def_id); }
            catch (e) { console.error("[FieldPickerModal] onActiveContainerChange failed:", e); }
          }
        }
      });
      radioWrap.appendChild(radio);
      radioWrap.addEventListener("click", (ev) => {
        if (ev.target !== radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event("change"));
        }
      });

      // Caption + name (analog input row)
      const labelWrap = document.createElement("div");
      labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
      const labelName = document.createElement("div");
      labelName.style.cssText = "font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#a88cd4;";
      labelName.textContent = cont.name || "(no name)";
      const labelCap = document.createElement("div");
      labelCap.style.cssText =
        "font-size:13px;color:#e8eef5;" +
        (isActive ? "font-weight:700;" : "");
      labelCap.textContent = cont.caption || cont.type_label;
      labelWrap.appendChild(labelName);
      labelWrap.appendChild(labelCap);

      // Meta — type_label badge + region_slot
      const meta = document.createElement("div");
      meta.style.cssText = "color:#a88cd4;font-size:11px;";
      meta.innerHTML =
        "<span style=\"background:#2a1f3a;padding:2px 6px;border-radius:3px;margin-right:6px;color:#a88cd4;\">" +
        (cont.type_code || "container") + "</span>" +
        (cont.type_label || "");

      // ID badge
      const idBadge = document.createElement("div");
      idBadge.style.cssText = "font-size:11px;color:#a88cd4;font-family:ui-monospace,Consolas,monospace;";
      idBadge.textContent = "id=" + cont.comp_def_id;

      // ⚙ Settings button (Krok H+5) — popup s caption + layout + defaults
      const settingsBtn = this._makeSettingsBtn({
        col: cont,
        mode: "container",
        compDefId: cont.comp_def_id,
        typeId: cont.type_id,
        caption: cont.caption,
        layout: cont.layout,
      });

      row.appendChild(removeBtn);
      row.appendChild(radioWrap);
      row.appendChild(labelWrap);
      row.appendChild(meta);
      row.appendChild(idBadge);
      row.appendChild(settingsBtn);
      return row;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // ══════════════════════════════════════════════════════════════════════
  // Phase 38.4 Krok 14g Etapa F Krok 5.K-B (17.5.2026 dopoledne, Marti's
  // "nejdulezitejsi a nejpouzivaneji nastroj pro designery"): hardcoded
  // editor pro fw.data_source + N operations + N inline data_sets.
  //
  // Marti's MVP scope: CRUD data_source header + add operations inline.
  // SQL editor = ErpRichEdit (Ace 1.32, SQL mode, monokai theme).
  // DB connection = hardcoded dropdown (data_db / DB_EC / DB_IS / DB-Ceniky /
  // DB-ARCHIV) per Marti's tempo "pomaly start".
  //
  // Backend Krok 5.K-A endpoints:
  //   GET  /design/data-source/{id}/full     — load existing detail
  //   POST /design/data-source/full          — bulk create (header + ops + sets)
  //
  // Constructor: { dataSourceId: int|null, onComplete?: fn }
  //   null = create new mode
  //   int  = view existing mode (load + display, no edit yet — defer Krok 5.K-B3)
  //
  // Test query / DB schema autocomplete / edit existing op / delete op DEFER.
  // ══════════════════════════════════════════════════════════════════════

  // Krok 5.K-B4 (17.5.2026, Marti's "code je matouci a navic"): slugify
  // helper pro auto-generate technical code z user-friendly name.
  // "EUROSOFT Klienti" → "eurosoft_klienti"
  // Diacritics stripped via NFD normalize, non-alphanumeric → underscore.

    global.FieldPickerModal = FieldPickerModal;
  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
