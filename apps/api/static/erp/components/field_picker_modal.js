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

      // Phase 38.4 Krok H+8.1 (26.5.2026, Marti's "hover = transient,
      // klik = persistent"):
      // Listen for 'erp:design-component-orchestrate' z DesignFwForm.
      // 3 akce:
      //   hover-in → add .erp-palette-row-hover (transient subtle bg)
      //   hover-out → remove .erp-palette-row-hover
      //   select → drop all .erp-palette-row-selected, add to current
      //            row, switch tab + scroll into view (persistent
      //            single-select pattern)
      this._reverseOrchestrationHandler = (ev) => {
        try {
          const detail = (ev && ev.detail) || {};
          const action = detail.action;
          const compDefId = detail.compDefId;
          if (!action) return;
          const body = this._shell && this._shell.body;
          if (!body) return;

          if (action === "hover-out") {
            // Drop hover class globally (cheap — typically 0-1 active rows)
            body.querySelectorAll(".erp-palette-row-hover").forEach(el => {
              el.classList.remove("erp-palette-row-hover");
            });
            return;
          }
          if (compDefId == null) return;

          if (action === "hover-in") {
            // Drop predchozi hover + apply na novy (single hover at a time)
            body.querySelectorAll(".erp-palette-row-hover").forEach(el => {
              el.classList.remove("erp-palette-row-hover");
            });
            const row = body.querySelector('[data-comp-def-id="' + compDefId + '"]');
            if (row) row.classList.add("erp-palette-row-hover");
            return;
          }

          if (action === "select") {
            // Persistent selection — switch na onform tab + scroll +
            // drop predchozi selected + apply na novy.
            if (this._activeTab !== "onform") {
              this._activeTab = "onform";
              try { this._render(); } catch (e) {}
            }
            requestAnimationFrame(() => {
              try {
                const _body = this._shell && this._shell.body;
                if (!_body) return;
                _body.querySelectorAll(".erp-palette-row-selected").forEach(el => {
                  el.classList.remove("erp-palette-row-selected");
                });
                const row = _body.querySelector('[data-comp-def-id="' + compDefId + '"]');
                if (!row) return;
                row.classList.add("erp-palette-row-selected");
                try {
                  row.scrollIntoView({ behavior: "smooth", block: "center" });
                } catch (e) {
                  try { row.scrollIntoView(); } catch (e2) {}
                }
              } catch (e) {
                console.error("[FieldPickerModal] select render failed:", e);
              }
            });
          }
        } catch (e) {
          console.error("[FieldPickerModal] reverse orchestration handler failed:", e);
        }
      };
      document.body.addEventListener(
        "erp:design-component-orchestrate",
        this._reverseOrchestrationHandler
      );
      // Cleanup pri zavreni palety — pri shell close odregistruj listener.
      const _originalClose = this._shell.close;
      this._shell.close = () => {
        try {
          document.body.removeEventListener(
            "erp:design-component-orchestrate",
            this._reverseOrchestrationHandler
          );
        } catch (e) {}
        try { _originalClose.call(this._shell); } catch (e) {}
      };

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
        // Krok 5-B Fix #13 (29.5.2026 vecer, Marti's "soft-deleted musi
        // byt v Nezarazeno pro obnoveni"): split podle is_orphan flag
        // z backend (Fix #12+ commit 685b885). Active -> "Jiz na forme",
        // orphans -> "Nezarazeno" bucket s _from_orphan=true marker.
        const _allContsBackend = ecData.existing_containers || [];
        this._existingContainers = _allContsBackend.filter(c => !c.is_orphan);
        const _orphanContsList = _allContsBackend.filter(c => c.is_orphan);
        // Krok 5-B Fix (28.5.2026 vecer pozde, Marti's "komponenty pod
        // panelama a tabsheetama na 'Jiz na forme' nejsou videt"):
        // backend ted vraci existing_fields = vsechny fields z hierarchy.
        // Krok 5-B Fix #13 (29.5.2026): split fields podle is_orphan.
        const _allFieldsBackend = ecData.existing_fields || [];
        this._existingFields = _allFieldsBackend.filter(f => !f.is_orphan);
        const _orphanFieldsList = _allFieldsBackend.filter(f => f.is_orphan);

        // Phase 38.4 Krok 14c+1: rozdeleni do dvou kolekci podle existing
        // Krok 5-B Fix #13: orphans pridat do _columnsAvailable jako
        // column-like shape s _from_orphan=true marker pro Nezarazeno tab.
        // Klik na orphan -> PATCH is_active=true (re-activate flow).
        const _unmatchedCols = this._columns.filter(
          c => c.existing_comp_def_id == null
        );
        const _orphansToBucket = [
          ..._orphanFieldsList.map(f => ({
            name: f.name,
            caption: f.caption || f.name,
            caption_default: f.caption || f.name,
            existing_comp_def_id: f.comp_def_id,
            existing_parent_comp_def_id: f.parent_comp_def_id,
            existing_sort_order: f.sort_order,
            existing_label: f.caption,
            suggested_type_id: f.type_id,
            suggested_type_code: f.type_code,
            type_code: f.type_code,
            is_active: f.is_active,
            _from_orphan: true,
            _orphan_reason: f.is_active === false ? "soft-deleted" : "parent soft-deleted",
          })),
          ..._orphanContsList.map(c => ({
            name: c.name,
            caption: c.caption || c.name,
            caption_default: c.caption || c.name,
            existing_comp_def_id: c.comp_def_id,
            existing_parent_comp_def_id: c.parent_comp_def_id,
            existing_sort_order: c.sort_order,
            existing_label: c.caption,
            suggested_type_id: c.type_id,
            suggested_type_code: c.type_code,
            type_code: c.type_code,
            is_active: c.is_active,
            _from_orphan: true,
            _is_container: true,
            _orphan_reason: c.is_active === false ? "soft-deleted" : "parent soft-deleted",
          })),
        ];
        this._columnsAvailable = [..._unmatchedCols, ..._orphansToBucket];
        // Krok 5-B Fix: extract IDs uz pouzitych ve _columnsOnForm pro
        // dedup s _existingFields (column-matched fields by se mohly
        // objevit oboje).
        const _matchedColumns = this._columns.filter(
          c => c.existing_comp_def_id != null
        );
        const _matchedIds = new Set(
          _matchedColumns.map(c => c.existing_comp_def_id)
        );
        // Map existing_fields → column-like shape (pro _renderOnFormRow
        // + _buildLinearizedTree kompatibilitu).
        const _fieldsAsColumns = this._existingFields
          .filter(f => !_matchedIds.has(f.comp_def_id))
          .map(f => ({
            name: f.name,
            caption: f.caption,
            caption_default: f.caption || f.name,
            existing_comp_def_id: f.comp_def_id,
            existing_parent_comp_def_id: f.parent_comp_def_id,
            existing_sort_order: f.sort_order,
            existing_label: f.caption,
            suggested_type_id: f.type_id,
            // Krok 5.Z (30.5.2026, Marti's "identifikace gridu na palete"):
            // render (_renderOnFormRow) cte col.existing_type_id pro type badge
            // + dropdown selected. Bez nej -> "type#undefined" + dropdown default
            // "Edit (id=2)". Mapuj f.type_id i sem (ne jen suggested_type_id).
            // Opravuje grid_modern (Grid (modern)) i vsechna ostatni hierarchy
            // pole (version, created_at, ...) co ukazovala type#undefined.
            existing_type_id: f.type_id,
            existing_region_slot: f.region_slot,
            type_code: f.type_code,
            type_label: f.type_label,
            // Marker: tento field neni z DB column whitelist, je z hierarchy.
            // (Krok 5-B Fix — pro budouci debug visibility.)
            _from_hierarchy: true,
          }));
        this._columnsOnForm = [..._matchedColumns, ..._fieldsAsColumns];
        // Krok H+5++++++ (26.5.2026 vecer, Marti's "prohod listy"):
        // Default tab = 'onform' (Již na formě). Marti tam dela vetsinu
        // prace (reorder + pinned + settings), "Schazi pridat" je sekundarni.
        this._activeTab = "onform";
        // Krok 5-B (29.5.2026 rano, Marti's "Mas dva systemy pro
        // zobrazeni prvku na Jiz na forme... nutne mit trigger ktery
        // to prepiname"): layout-only filter. Default false = show all
        // (containers + fields). True = skip fields, only containers.
        // Toggle button v _renderTabStrip header (visible jen on 'onform').
        if (this._layoutOnlyFilter == null) this._layoutOnlyFilter = false;

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
      // Krok H+5++++++ (26.5.2026 vecer, Marti's "prohod listy"): Jiz na
      // forme = PRVNI (Marti's primary workspace), Schazi pridat = druhy.
      // Krok 5.X (27.5.2026): nested grids jsou ted fw.comp_def rows
      // (kind='container') — automaticky v _existingContainers count.
      // H+13.4 _childCount + childComponents dropped.
      const tabs = [
        {
          key: "onform",
          // Phase 38.4 Krok H+5: count includes containers (panel/groupbox/
          // pagecontrol/tabsheet/nested_grid — all kind='container').
          label: "Již na formě",
          count: this._columnsOnForm.length + (this._existingContainers || []).length,
          accent: "#7ed4e8",
        },
        {
          key: "available",
          // Krok H+13.4.1 (27.5.2026, Marti): "Schází přidat" → "Nezařazeno"
          label: "Nezařazeno",
          count: this._columnsAvailable.length,
          accent: "#5dbf5d",
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
        // Krok 5-B (29.5.2026 rano, Marti's "Layout-only toggle"):
        // pro 'onform' tab pri aktivnim _layoutOnlyFilter ukaze JEN
        // pocet containers (skip fields), jinak total.
        let count = t.count;
        if (t.key === "onform" && this._layoutOnlyFilter) {
          count = (this._existingContainers || []).length;
        }
        const countStr = count != null ? " (" + count + ")" : "";
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

      // Krok 5-B (29.5.2026 rano, Marti's "trigger v Head Palete komponent"):
      // Layout-only toggle button na konci tab strip (margin-left:auto =
      // push-to-right). Visible jen pro 'onform' tab (kde dava smysl).
      // OFF = "🗂 Vše" (containers + fields, current behavior).
      // ON  = "📐 Jen layout" (containers only — panel/groupbox/tabsheet/
      // pagecontrol/nested_grid). Marti's primary workflow pri staveni
      // jadra: nejdriv layout, pak fields.
      if (this._activeTab === "onform") {
        const toggleBtn = document.createElement("button");
        toggleBtn.type = "button";
        const isLayoutOnly = this._layoutOnlyFilter === true;
        toggleBtn.textContent = isLayoutOnly ? "📐 Jen layout" : "🗂 Vše";
        toggleBtn.title = isLayoutOnly
          ? "Klik = zobrazit i fields (containers + pole)"
          : "Klik = zobrazit jen containers (panel/groupbox/tabsheet)";
        toggleBtn.style.cssText =
          "padding:6px 14px;background:" + (isLayoutOnly ? "#1a2028" : "transparent") +
          ";border:1px solid " + (isLayoutOnly ? "#a88cd4" : "#3a4754") +
          ";border-radius:3px;color:" + (isLayoutOnly ? "#a88cd4" : "#8a96a4") +
          ";cursor:pointer;font-size:12px;font-weight:" + (isLayoutOnly ? "600" : "400") +
          ";margin-left:auto;align-self:center;transition:color 0.15s, background 0.15s;";
        toggleBtn.addEventListener("click", () => {
          this._layoutOnlyFilter = !this._layoutOnlyFilter;
          this._render();
        });
        toggleBtn.addEventListener("mouseenter", () => {
          if (!isLayoutOnly) {
            toggleBtn.style.color = "#cfd6df";
            toggleBtn.style.background = "#1a2028";
          }
        });
        toggleBtn.addEventListener("mouseleave", () => {
          if (!isLayoutOnly) {
            toggleBtn.style.color = "#8a96a4";
            toggleBtn.style.background = "transparent";
          }
        });
        strip.appendChild(toggleBtn);
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
        // Krok 5-B (29.5.2026 rano, Marti's "Layout-only toggle"):
        // Hint reflects active filter — pokud Jen layout, ukaze container
        // count + tip jak vratit zpet.
        if (this._layoutOnlyFilter) {
          const cCount = (this._existingContainers || []).length;
          hint.innerHTML =
            "<b style=\"color:#a88cd4;\">📐 Jen layout</b> — " +
            "<b>" + cCount + "</b> containers (panel/groupbox/tabsheet) " +
            "na formě. Klik na \"🗂 Vše\" vpravo pro zobrazení fieldů.";
        } else {
          hint.innerHTML =
            "<b>" + this._columnsOnForm.length + "</b> polí už je na formě. " +
            "Klikni na ✕ vpravo pro odebrání (soft delete — komponenta zmizí " +
            "z formu, ale data v DB zůstanou).";
        }
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
        // Phase 38.4 Krok H+5+++++ (26.5.2026 vecer, Marti's "simulovat
        // strom"): depth-first tree traversal misto flat seznamu. Panely
        // first, jejich potomci indented pod nimi, dalsi panel, jeho
        // potomci, atd. Vizualne = strom; data = flat DOM s marginLeft.
        const containers = this._existingContainers || [];
        // Krok H+13.4 (27.5.2026): nested child grids (TELEFONY/EMAILY) —
        // memory-only z DesignFwForm._spec.children, ne v fw.comp_def DB.
        const childComps = (this.opts && Array.isArray(this.opts.childComponents))
          ? this.opts.childComponents : [];
        if (this._columnsOnForm.length === 0 && containers.length === 0 && childComps.length === 0) {
          const empty = document.createElement("div");
          empty.style.cssText = "padding:24px;text-align:center;color:#8a96a4;font-size:13px;";
          empty.innerHTML = "Form je zatím prázdný — žádné pole ani container.";
          content.appendChild(empty);
        } else {
          const tree = this._buildLinearizedTree();
          for (const node of tree) {
            let row;
            if (node.kind === "container") {
              row = this._renderOnFormContainerRow(node.item, node.depth);
            } else {
              row = this._renderOnFormRow(node.item, node.depth);
            }
            content.appendChild(row);
          }
          // Krok H+13.4: render child grids sekce na konci (separator
          // + per-child read-only row). Marti's "nejsou videt" — ted ano.
          if (childComps.length > 0) {
            const sep = document.createElement("div");
            sep.style.cssText =
              "margin-top:14px;padding:8px 12px;background:#0a0e13;" +
              "border-top:1px dashed #2a3340;border-bottom:1px solid #2a3340;" +
              "color:#7ed4e8;font-size:11px;font-weight:600;letter-spacing:0.5px;";
            sep.textContent = "🔗 NESTED GRIDY · " + childComps.length + " (memory-only)";
            content.appendChild(sep);
            for (const child of childComps) {
              const row = document.createElement("div");
              row.style.cssText =
                "display:grid;grid-template-columns:32px 1fr auto;gap:10px;" +
                "align-items:center;padding:8px 12px;border-bottom:1px solid #1a1f26;" +
                "color:#cfd6df;font-size:13px;";
              // Disabled-look placeholder pro ✕ (memory-only, ne mazatelné)
              const ph = document.createElement("div");
              ph.style.cssText = "color:#3a4754;font-size:11px;text-align:center;";
              ph.textContent = "—";
              ph.title = "Nested grid je memory-only — neexistuje v fw.comp_def, nelze odebrat tady";
              row.appendChild(ph);
              // Label
              const labelWrap = document.createElement("div");
              labelWrap.style.cssText = "display:flex;flex-direction:column;gap:2px;";
              const nameEl = document.createElement("div");
              nameEl.style.cssText = "color:#7a8696;font-size:10px;font-family:ui-monospace,Consolas,monospace;";
              nameEl.textContent = child.key || "(no key)";
              const labelEl = document.createElement("div");
              labelEl.style.cssText = "color:#cfd6df;font-size:13px;font-weight:500;";
              labelEl.textContent = child.label || child.key;
              labelWrap.appendChild(nameEl);
              labelWrap.appendChild(labelEl);
              row.appendChild(labelWrap);
              // Right info: row count + type badge
              const info = document.createElement("div");
              info.style.cssText =
                "display:flex;gap:8px;align-items:center;color:#7a8696;font-size:11px;";
              const typeBadge = document.createElement("span");
              typeBadge.style.cssText =
                "padding:2px 8px;background:rgba(126,212,232,0.10);" +
                "border:1px solid #2a3340;border-radius:3px;color:#7ed4e8;" +
                "font-size:10px;font-weight:500;";
              typeBadge.textContent = "nested_grid";
              info.appendChild(typeBadge);
              const rcEl = document.createElement("span");
              rcEl.textContent = (child.row_count || 0) + " řádků";
              info.appendChild(rcEl);
              row.appendChild(info);
              content.appendChild(row);
            }
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
    // ─────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok H+5+++ (26.5.2026 vecer, Marti's "sipky misto
    // drag-drop") + H+5++++ (Marti's "sipka pinned = trigger jako na
    // komponente, pinned-unpinned"): explicit ← ↑ ↓ tlacitka.
    //
    // Drag-drop UX je krehky (drop target ambiguity → "self-parent"
    // toasts pri omylu). Explicit buttons jsou spolehlive:
    //   ← pinned toggle (always_new_row) — mirror ⬅ button na rendrovane
    //     komponente v DesignFwForm. ON state = cyan accent visible.
    //   ↑ swap sort_order s prev sibling (PUT /comp-def/reorder)
    //   ↓ swap sort_order s next sibling (PUT /comp-def/reorder)
    //
    // Backend: PATCH /comp-def/update (layout.always_new_row) + PUT
    // /comp-def/reorder (sort_order multiples of 10).
    //
    // _moveOutdent zustava jako utility (dnes nepouzita) pro future
    // outdent feature pokud Marti rozhodne pridat 4. tlacitko.
    // ─────────────────────────────────────────────────────────────────

    // Build sibling list (fields + containers s same parent) sorted by sort_order.
    _getAllSiblings(parentId) {
      const result = [];
      for (const c of (this._columnsOnForm || [])) {
        if (c.existing_comp_def_id != null
            && c.existing_parent_comp_def_id === parentId) {
          result.push({
            id: c.existing_comp_def_id,
            sort: c.existing_sort_order || 0,
          });
        }
      }
      for (const cn of (this._existingContainers || [])) {
        if (cn.parent_comp_def_id === parentId) {
          result.push({
            id: cn.comp_def_id,
            sort: cn.sort_order || 0,
          });
        }
      }
      result.sort((a, b) => (a.sort || 0) - (b.sort || 0));
      return result;
    }

    // Lookup parent_comp_def_id pro dany comp_def_id (pro outdent grandparent).
    _findParentOf(compDefId) {
      for (const c of (this._columnsOnForm || [])) {
        if (c.existing_comp_def_id === compDefId) {
          return c.existing_parent_comp_def_id != null
            ? c.existing_parent_comp_def_id : null;
        }
      }
      for (const cn of (this._existingContainers || [])) {
        if (cn.comp_def_id === compDefId) {
          return cn.parent_comp_def_id != null
            ? cn.parent_comp_def_id : null;
        }
      }
      return null;
    }

    // ─────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok H+5+++++ (26.5.2026 vecer, Marti's "simulovat strom"):
    // Linearized tree — depth-first traversal vsech containers + fields.
    // Vrati flat array [{item, kind, sort, id, parentId, depth}].
    // Kind: 'container' | 'field'.
    //
    // Pouziti: render (depth = indent CSS marginLeft) + ↑/↓ navigation
    // (current index ±1 → cross-container move s prepocitanym
    // parent_comp_def_id + sort_order).
    // ─────────────────────────────────────────────────────────────────
    _buildLinearizedTree() {
      const formRoot = this.opts.parentCompDefId;
      const byParent = new Map();  // parentId → array of {item, kind, sort, id, parentId}

      // Index containers
      for (const cn of (this._existingContainers || [])) {
        const pid = cn.parent_comp_def_id;
        const arr = byParent.get(pid) || [];
        arr.push({
          item: cn,
          kind: "container",
          sort: cn.sort_order != null ? cn.sort_order : 999999,
          id: cn.comp_def_id,
          parentId: pid,
        });
        byParent.set(pid, arr);
      }
      // Index fields (jen ty na forme, ne dostupne)
      // Krok 5-B (29.5.2026 rano, Marti's "Layout-only toggle"): pokud
      // _layoutOnlyFilter aktivni, skip fields entirely → tree obsahuje
      // jen containers (panel/groupbox/tabsheet/pagecontrol/nested_grid).
      // Marti's workflow pri staveni jadra: 1. nastavit layout, 2. fields.
      if (!this._layoutOnlyFilter) {
        for (const c of (this._columnsOnForm || [])) {
          if (c.existing_comp_def_id == null) continue;
          const pid = c.existing_parent_comp_def_id;
          const arr = byParent.get(pid) || [];
          arr.push({
            item: c,
            kind: "field",
            sort: c.existing_sort_order != null ? c.existing_sort_order : 999999,
            id: c.existing_comp_def_id,
            parentId: pid,
          });
          byParent.set(pid, arr);
        }
      }

      // Sort kazdou sibling group by sort_order (tiebreaker = id pro stabilitu)
      for (const arr of byParent.values()) {
        arr.sort((a, b) => {
          if (a.sort !== b.sort) return a.sort - b.sort;
          return (a.id || 0) - (b.id || 0);
        });
      }

      // Depth-first walk z form root
      const result = [];
      const visited = new Set();
      const visit = (parentId, depth) => {
        const children = byParent.get(parentId) || [];
        for (const child of children) {
          if (visited.has(child.id)) continue;  // defense proti cycle
          visited.add(child.id);
          result.push({ ...child, depth: depth });
          if (child.kind === "container") {
            visit(child.id, depth + 1);
          }
        }
      };
      visit(formRoot, 0);

      // Orphans (parent neni form_root ani znamy container — defensive):
      // appendni na konec at depth=0. Marti tak vidi, ze tam jsou.
      for (const arr of byParent.values()) {
        for (const node of arr) {
          if (!visited.has(node.id)) {
            visited.add(node.id);
            result.push({ ...node, depth: 0 });
          }
        }
      }

      return result;
    }

    // ─────────────────────────────────────────────────────────────────
    // Linearized ↑/↓ navigation: cross-container moves.
    //
    // ↑ click: target = pozice IMMEDIATELY BEFORE linear_prev.
    //   new_parent = linear_prev.parentId
    //   new_sort_order = linear_prev.sort - 5 (po refresh renumber na 10)
    //
    // ↓ click: target = pozice IMMEDIATELY AFTER linear_next.
    //   new_parent = linear_next.parentId
    //   new_sort_order = linear_next.sort + 5
    //
    // Marti's intent ("simulovat strom" + "pohybovat se mezi
    // komponentama"): single ↑ click muze fyzicky presunout component
    // pres container boundary (napr. ven z panelu do nadrazene urovne,
    // nebo do sousedniho panelu jako jeho dite).
    // ─────────────────────────────────────────────────────────────────
    async _moveInLinearizedTree(compDefId, direction) {
      const tree = this._buildLinearizedTree();
      const myIdx = tree.findIndex((n) => n.id === compDefId);
      if (myIdx < 0) {
        console.warn("[FieldPickerModal] _moveInLinearizedTree: compDefId not in tree", compDefId);
        return;
      }
      const targetIdx = myIdx + direction;
      if (targetIdx < 0 || targetIdx >= tree.length) {
        // Out of bounds — should be disabled by canUp/canDown, defensive no-op
        return;
      }
      const myNode = tree[myIdx];
      const neighbor = tree[targetIdx];

      // Compute new parent + sort_order
      let newParentId;
      let newSortOrder;
      if (direction < 0) {
        // ↑ — insert BEFORE neighbor (becomes my "next")
        newParentId = neighbor.parentId;
        newSortOrder = (neighbor.sort != null ? neighbor.sort : 10) - 5;
      } else {
        // ↓ — insert AFTER neighbor (becomes my "prev")
        //
        // Phase 38.4 Krok H+11 (26.5.2026, Marti's "Description ↓ ma
        // zalezt do active panelu, ne sletet az dolu"):
        // Pokud neighbor je CONTAINER a NE moje stavajici parent, drill
        // INSIDE jako first child. Matches "depth-first next position"
        // — uzivatel ocekava postupne projizdeni stromu vcetne entry/exit
        // containeru, ne preskakovani celych podstromu.
        //
        // Edge case: neighbor je container ALE muj parent (= jsem prvni
        // sibling-after containeru s parent=container.parent) → drill
        // by vznikl cycle (sebe-rodicovstvi). Default sibling-after.
        //
        // Phase 38.4 Krok 5.X+1 Fix C (27.5.2026, Marti's "nemel by
        // skakat do pozice ditete k druhemu nested gridu"):
        // Nested_grid je HYBRID — backend kind='container' (kvuli children
        // data), ale UI semantika = field-like (data leaf, ne nadrazena
        // struktura panel/groupbox/pagecontrol/tabsheet). Drill INTO
        // nested_grid by udelal nested_grid parent jineho nested_gridu —
        // semanticky chyba (nested grids nejsou hierarchicke containers,
        // jsou to peer 1:N child views). Skip drill pro nested_grid —
        // fallback na default sibling-after.
        const nestedGridIds = new Set(
          (this._existingContainers || [])
            .filter((c) => c.type_code === "nested_grid")
            .map((c) => c.comp_def_id)
        );
        const neighborIsNestedGrid = nestedGridIds.has(neighbor.id);
        const selfIsNestedGrid = nestedGridIds.has(compDefId);
        const neighborIsContainer = (this._existingContainers || []).some(
          (c) => c.comp_def_id === neighbor.id
        );
        if (neighborIsContainer && neighbor.id !== myNode.parentId &&
            neighbor.id !== compDefId &&
            !neighborIsNestedGrid && !selfIsNestedGrid) {
          // Drill INTO container — become FIRST child
          newParentId = neighbor.id;
          // Find existing first child's sort, place before. Pokud container
          // je prazdny, default sort 10.
          let firstChildSort = null;
          for (const node of tree) {
            if (node.parentId === neighbor.id) {
              firstChildSort = node.sort;
              break;  // tree je sorted depth-first, first match = first child
            }
          }
          newSortOrder = (firstChildSort != null)
            ? Math.max(1, firstChildSort - 5)
            : 10;
        } else {
          // Default: insert as sibling-after neighbor
          newParentId = neighbor.parentId;
          newSortOrder = (neighbor.sort != null ? neighbor.sort : 10) + 5;
        }
      }

      // Cycle guard: ne nelze udelat sebe vlastnim potomkem (kdyz tahnu
      // panel A do A's child). Backend ma backstop, frontend ma cisty toast.
      // Walk: ancestors of newParentId nesmi obsahovat myNode.id.
      if (newParentId === compDefId) {
        _showToast("Nelze přesunout komponentu dovnitř sebe sama.",
                   "warning", 2500);
        return;
      }
      let ancestor = newParentId;
      const guardSet = new Set();
      while (ancestor != null && !guardSet.has(ancestor)) {
        guardSet.add(ancestor);
        if (ancestor === compDefId) {
          _showToast("Nelze přesunout komponentu dovnitř jejího potomka " +
                     "(vznikl by kruh).",
                     "warning", 2500);
          return;
        }
        ancestor = this._findParentOf(ancestor);
      }

      // Phase 38.4 Krok H+12 (26.5.2026, Marti's "sort_order musi byt
      // non-negative — co s tim? Prepocitat po desitkach?"):
      // Opakovane drill-in (Krok H+11) a ↑ poistuju sort o -5 kazdy krok,
      // takze sort eventualne padne na 0/negativni. Backend rejectne.
      // Fallback strategy: pokud newSortOrder < 1, switch na "renumber"
      // — 2-step transakce:
      //   1. PATCH parent_comp_def_id (sort = temp 999999, prepise se)
      //   2. PUT /reorder s prepocitanymi sort_order = (idx+1)*10 pro
      //      vsechny siblings v novem parentovi.
      // Tim se gap-based scheme zachova bez zaporneho rozsahu — Marti's
      // "prepocitat a znovu nastavit po desitkach" doctrine.
      const NEEDS_RENUMBER = (newSortOrder < 1);

      if (NEEDS_RENUMBER) {
        // Build new sibling list pro target parent
        const allInNewParent = this._getAllSiblings(newParentId)
          .filter((s) => s.id !== compDefId);
        // Compute insert position podle direction a wasDrill
        const wasDrill = (newParentId === neighbor.id);
        let insertIdx;
        if (wasDrill) {
          insertIdx = 0;  // drill = first child
        } else {
          const neighborIdx = allInNewParent.findIndex(
            (s) => s.id === neighbor.id
          );
          if (neighborIdx < 0) {
            // Defensive — neighbor zmizel z newSiblings list (shouldn't
            // happen since neighbor je v linearized tree). Fallback na
            // clamp = 1 + single PATCH.
            console.warn("[FieldPickerModal] renumber fallback: neighbor not in newSiblings");
            insertIdx = -1;
          } else {
            insertIdx = (direction < 0) ? neighborIdx : neighborIdx + 1;
          }
        }

        if (insertIdx >= 0) {
          // Build clean renumber payload
          const reordered = allInNewParent.slice();
          reordered.splice(insertIdx, 0, { id: compDefId, sort: 0 });
          const renumberPayload = reordered.map((s, i) => ({
            id: s.id,
            sort_order: (i + 1) * 10,
          }));
          try {
            // Step 1: PATCH parent_comp_def_id + temp sort (will be overwritten)
            const r1 = await fetch(
              "/api/v1/erp/design/comp-def/update/" + compDefId,
              {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  parent_comp_def_id: newParentId,
                  sort_order: 999999,  // temp — bude prepsano reorderem
                }),
              }
            );
            if (!r1.ok) {
              const eb = await r1.json().catch(() => ({}));
              throw new Error("PATCH HTTP " + r1.status + ": " +
                              (eb.error || r1.statusText));
            }
            // Step 2: PUT /reorder s clean renumber (multiples of 10)
            const r2 = await fetch(
              "/api/v1/erp/design/comp-def/reorder",
              {
                method: "PUT",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ field_orders: renumberPayload }),
              }
            );
            if (!r2.ok) {
              const eb = await r2.json().catch(() => ({}));
              throw new Error("REORDER HTTP " + r2.status + ": " +
                              (eb.error || r2.statusText));
            }
            const crossed = (myNode.parentId !== newParentId);
            _showToast(
              (direction < 0 ? "↑" : "↓") +
              (crossed ? " Přesunuto do jiného containeru" : " Posunuto") +
              " (přečíslováno)",
              "success", 1800
            );
            await this._refreshState();
            this._render();
            if (typeof this.opts.onComplete === "function") {
              try { this.opts.onComplete({ moved: 1, renumbered: 1 }); }
              catch (e) {}
            }
            return;
          } catch (e) {
            console.error("[FieldPickerModal] renumber move failed:", e);
            _showToast("Posun selhal: " + (e.message || e), "error", 3000);
            return;
          }
        }
        // Defensive fallback: clamp newSortOrder a fall through na default
        newSortOrder = 1;
      }

      // Default path: PATCH parent_comp_def_id + sort_order v jednom volani.
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + compDefId,
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              parent_comp_def_id: newParentId,
              sort_order: newSortOrder,
            }),
          }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (eb.error || r.statusText));
        }
        // Toast podle kontextu: same parent = simple swap, jiny parent = cross-container
        const crossed = (myNode.parentId !== newParentId);
        _showToast(
          (direction < 0 ? "↑" : "↓") + (crossed ? " Přesunuto do jiného containeru" : " Posunuto"),
          "success", 1500
        );
        await this._refreshState();
        this._render();
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ moved: 1 }); } catch (e) {}
        }
      } catch (e) {
        console.error("[FieldPickerModal] linearized move failed:", e);
        _showToast("Posun selhal: " + (e.message || e), "error", 3000);
      }
    }

    // Single arrow button factory (←, ↑, ↓).
    // Krok H+5++++ (26.5.2026): rozsireno o "active" state pro toggle buttons.
    _mkArrowBtn(label, enabled, tooltip, onClick, active) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.title = tooltip;
      btn.disabled = !enabled;
      // 3 stavy:
      //   active=true  → ON (cyan bg + accent border, Marti vidi stav)
      //   enabled=true → normal (transparent bg, cyan text, hover effect)
      //   enabled=false→ disabled (gray, opacity 0.5)
      btn.style.cssText =
        "width:30px;height:28px;border-radius:3px;font-size:14px;font-weight:600;line-height:1;" +
        (active
          ? "background:rgba(126,212,232,0.25);border:1px solid #7ed4e8;color:#bfe9f3;cursor:pointer;"
          : (enabled
            ? "background:#1f2530;border:1px solid #3a4754;color:#7ed4e8;cursor:pointer;"
            : "background:#0f1418;border:1px solid #1f2530;color:#3a4754;cursor:not-allowed;opacity:0.5;"));
      if (enabled) {
        if (!active) {
          btn.addEventListener("mouseenter", () => {
            btn.style.background = "#2a3340";
            btn.style.borderColor = "#7ed4e8";
          });
          btn.addEventListener("mouseleave", () => {
            btn.style.background = "#1f2530";
            btn.style.borderColor = "#3a4754";
          });
        }
        btn.addEventListener("click", onClick);
      }
      return btn;
    }

    // Build wrapper s 3 buttons (← ↑ ↓) pro dany comp_def_id.
    // Krok H+5++++ (26.5.2026, Marti's "sipka pinned = trigger"):
    //   ← = TOGGLE pinned (layout.always_new_row), mirror ⬅ na komponente.
    // Krok H+5+++++ (26.5.2026 vecer, Marti's "simulovat strom"):
    //   ↑/↓ = LINEARIZED tree navigation. Cross-container move = single
    //   click. Disabled jen na first/last v celem stromu (ne jen sibling).
    _makeMoveButtons(compDefId, parentId, sortOrder, layout, isContainer) {
      const wrap = document.createElement("div");
      wrap.style.cssText = "display:flex;gap:4px;align-items:center;justify-content:flex-start;";

      // Linearized tree pro canUp/canDown (cross-container aware)
      const tree = this._buildLinearizedTree();
      const myIdx = tree.findIndex((n) => n.id === compDefId);
      const canUp = myIdx > 0;
      const canDown = myIdx >= 0 && myIdx < tree.length - 1;

      // Pinned state z layout.always_new_row (boolean)
      const lay = (layout && typeof layout === "object") ? layout : {};
      const isPinned = !!lay.always_new_row;

      const self = this;

      // Phase 38.4 Krok H+9 (26.5.2026, Marti's "panel v panelu nemuzu
      // dostat ven... zkus tu sipku vlevo — u panelu pinned nikdy nebude"):
      // ← ma dvojí semantiku per role:
      //   - field (isContainer=false) → TOGGLE pinned (always_new_row)
      //   - container (isContainer=true) → OUTDENT (vyjet ven o uroven
      //     z parent containeru). Pro panely/groupboxů/pagecontrol/tabsheet
      //     ma vetsi smysl outdent nez pinned (panely neflowuji v gridu).
      if (isContainer === true) {
        // Container: ← = outdent (move to grandparent)
        // canOutdent = true pokud parent neni form root (grandparent existuje)
        const grandParentId = this._findParentOf(parentId);
        const canOutdent = grandParentId != null;
        wrap.appendChild(this._mkArrowBtn("←", canOutdent,
          canOutdent
            ? "Vyjmout o úroveň výš (přesunout mimo aktuální container)"
            : "Už je na nejvyšší úrovni",
          () => self._moveOutdent(compDefId, parentId)
        ));
      } else {
        // Field: ← = pinned toggle (existing behavior, mirror ⬅ na komponente)
        wrap.appendChild(this._mkArrowBtn("←", true,
          isPinned
            ? "Vždy na novém řádku — ZAP. Klikni pro vypnutí."
            : "Vždy na novém řádku — VYP. Klikni pro zapnutí.",
          () => self._togglePinned(compDefId, layout),
          isPinned  // active state visualization
        ));
      }

      // Phase 38.4 Krok H+10 (26.5.2026, Marti's "potrebuju dostat Core,
      // Refresh a Status do panelu — bez sipky doprava si neporadime"):
      // → indent — vnorit do predchoziho sibling containeru. Universalne
      // pro fields i containers (kazda komponenta muze byt vnorena pokud
      // ma predchoziho container souroda).
      // canIndent = je-li mezi predchozimi siblings nejaky container.
      const siblings = this._getAllSiblings(parentId);
      const myIdxInSiblings = siblings.findIndex((s) => s.id === compDefId);
      let hasPrecedingContainer = false;
      if (myIdxInSiblings > 0) {
        for (let i = myIdxInSiblings - 1; i >= 0; i--) {
          const sib = siblings[i];
          if ((this._existingContainers || []).some(c => c.comp_def_id === sib.id)) {
            hasPrecedingContainer = true;
            break;
          }
        }
      }
      wrap.appendChild(this._mkArrowBtn("→", hasPrecedingContainer,
        hasPrecedingContainer
          ? "Vnořit do předchozího containeru (panel/groupbox/tab)"
          : "Není kam vnořit (žádný container před touto komponentou)",
        () => self._moveIndent(compDefId, parentId)
      ));
      // ↑ (linearized up — cross-container OK)
      wrap.appendChild(this._mkArrowBtn("↑", canUp,
        canUp ? "Posunout výš ve stromu (i napříč containery)"
              : "Už je úplně nahoře",
        () => self._moveInLinearizedTree(compDefId, -1)));
      // ↓ (linearized down — cross-container OK)
      wrap.appendChild(this._mkArrowBtn("↓", canDown,
        canDown ? "Posunout níž ve stromu (i napříč containery)"
                : "Už je úplně dole",
        () => self._moveInLinearizedTree(compDefId, +1)));

      return wrap;
    }

    // Krok H+5++++ (26.5.2026): toggle layout.always_new_row. Mirror
    // _performFieldToggleAlwaysLeft v DesignFwForm — same PATCH endpoint,
    // same behavior. UX parita: ← v palete = ⬅ na komponente.
    async _togglePinned(compDefId, currentLayout) {
      const lay = (currentLayout && typeof currentLayout === "object")
        ? currentLayout : {};
      const wasOn = !!lay.always_new_row;
      const newLayout = Object.assign({}, lay, { always_new_row: !wasOn });
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + compDefId,
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ layout: newLayout }),
          }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (eb.error || r.statusText));
        }
        _showToast(
          !wasOn
            ? "← Pinned ZAP (vždy na novém řádku)"
            : "← Pinned VYP (default grid wrap)",
          "success", 1500
        );
        await this._refreshState();
        this._render();
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ pinnedToggled: 1 }); } catch (e) {}
        }
      } catch (e) {
        console.error("[FieldPickerModal] pinned toggle failed:", e);
        _showToast("Přepnutí pinned selhalo: " + (e.message || e), "error", 3000);
      }
    }

    // Move up/down: swap sort_order s adjacent sibling, PUT reorder vsech.
    async _moveUpDown(compDefId, parentId, direction) {
      const siblings = this._getAllSiblings(parentId);
      const myIdx = siblings.findIndex((s) => s.id === compDefId);
      if (myIdx < 0) return;
      const targetIdx = myIdx + direction;
      if (targetIdx < 0 || targetIdx >= siblings.length) return;

      // Swap positions
      const reordered = siblings.slice();
      const tmp = reordered[myIdx];
      reordered[myIdx] = reordered[targetIdx];
      reordered[targetIdx] = tmp;
      // Renumber multiples of 10
      const payload = reordered.map((s, i) => ({
        id: s.id,
        sort_order: (i + 1) * 10,
      }));

      try {
        const r = await fetch("/api/v1/erp/design/comp-def/reorder", {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ field_orders: payload }),
        });
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (eb.error || r.statusText));
        }
        _showToast(direction < 0 ? "↑ Posunuto výš" : "↓ Posunuto níž",
                   "success", 1500);
        await this._refreshState();
        this._render();
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ reordered: 1 }); } catch (e) {}
        }
      } catch (e) {
        console.error("[FieldPickerModal] move up/down failed:", e);
        _showToast("Posun selhal: " + (e.message || e), "error", 3000);
      }
    }

    // Phase 38.4 Krok H+10 (26.5.2026, Marti's "potrebuju dostat Core,
    // Refresh a Status do panelu — bez sipky doprava si neporadime"):
    // Indent — vnorit komponentu do PREDCHOZIHO sibling containeru.
    // Pattern: find siblings of compDefId, walk backward, najit prvni
    // container (panel/groupbox/pagecontrol/tabsheet), PATCH parent_comp_def_id.
    // Sort order zustava — Marti pak muze pres ↑/↓ uvnitr noveho parenta.
    async _moveIndent(compDefId, currentParentId) {
      const siblings = this._getAllSiblings(currentParentId);
      const myIdx = siblings.findIndex((s) => s.id === compDefId);
      if (myIdx <= 0) {
        _showToast("Není kam vnořit (žádná předchozí komponenta)", "info", 2000);
        return;
      }
      // Walk backward, najit prvni container mezi predchozimi siblings.
      // Container = jen ten je v _existingContainers list (panel/groupbox/
      // pagecontrol/tabsheet). Fields tam nejsou.
      let targetContainerId = null;
      for (let i = myIdx - 1; i >= 0; i--) {
        const sib = siblings[i];
        const isContainer = (this._existingContainers || []).some(
          (c) => c.comp_def_id === sib.id
        );
        if (isContainer) {
          targetContainerId = sib.id;
          break;
        }
      }
      if (targetContainerId == null) {
        _showToast("Není kam vnořit (žádný container před touto komponentou)",
                   "info", 2500);
        return;
      }
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + compDefId,
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ parent_comp_def_id: targetContainerId }),
          }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (eb.error || r.statusText));
        }
        _showToast("→ Vnořeno do containeru", "success", 1500);
        await this._refreshState();
        this._render();
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ indented: 1 }); } catch (e) {}
        }
      } catch (e) {
        console.error("[FieldPickerModal] indent failed:", e);
        _showToast("Vnoření selhalo: " + (e.message || e), "error", 3000);
      }
    }

    // Outdent: PATCH parent_comp_def_id = grandparent.
    async _moveOutdent(compDefId, currentParentId) {
      const grandParentId = this._findParentOf(currentParentId);
      if (grandParentId == null) {
        _showToast("Nelze posunout dál (už je na nejvyšší úrovni)",
                   "info", 2000);
        return;
      }
      try {
        const r = await fetch(
          "/api/v1/erp/design/comp-def/update/" + compDefId,
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ parent_comp_def_id: grandParentId }),
          }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error("HTTP " + r.status + ": " + (eb.error || r.statusText));
        }
        _showToast("← Vyjmuto o úroveň výš", "success", 1500);
        await this._refreshState();
        this._render();
        if (typeof this.opts.onComplete === "function") {
          try { this.opts.onComplete({ outdented: 1 }); } catch (e) {}
        }
      } catch (e) {
        console.error("[FieldPickerModal] outdent failed:", e);
        _showToast("Vyjmutí selhalo: " + (e.message || e), "error", 3000);
      }
    }

    _renderOnFormRow(col, depth) {
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "X jako prvni"):
      // Grid template column order: 32px (remove) | 200px | 1fr | 140px.
      // Symetrie s "Schazi pridat" tab kde checkbox je prvni (left).
      const row = document.createElement("div");
      // Krok H+8 (26.5.2026): tag row pro reverse orchestrace lookup.
      if (col.existing_comp_def_id != null) {
        row.dataset.compDefId = String(col.existing_comp_def_id);
      }
      // Krok H+5+++ (26.5.2026): pridana sloupec pro arrow buttons (110px)
      // mezi meta a typeSel — Marti's "do druhe tretiny vpravo".
      // Krok H+5+++++ (26.5.2026 vecer, Marti's "simulovat strom"):
      // marginLeft podle depth (20px na uroven) — vizualni hierarchie
      // ve flat DOM. Field = leaf, vetsinou depth >= 1 (uvnitr panelu).
      const _d = depth || 0;
      row.style.cssText =
        "display:grid;grid-template-columns:32px 200px 1fr 140px 170px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "background:rgba(126,212,232,0.04);" +
        (_d > 0 ? "margin-left:" + (_d * 20) + "px;" : "");

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
      // Krok 5.Z (30.5.2026, Marti's "identifikace gridu"): fallback na
      // col.type_label (backend existing_fields ho posila) pro typy mimo
      // _compTypesById — grid_modern (preview_html NULL, neni v addable
      // palette) -> "Grid (modern)" misto "type#101".
      meta.innerHTML =
        "<span style=\"background:#1f2530;padding:2px 6px;border-radius:3px;margin-right:6px;\">" +
        (col.existing_region_slot || "main") + "</span>" +
        (ct ? ct.label : (col.type_label || ("type#" + col.existing_type_id)));

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
      // Krok 5.Z (30.5.2026): pokud current type neni v _compTypes (grid_modern
      // a jine structural typy bez preview_html), inject synthetic selected
      // option, at dropdown ukaze spravny typ misto defaultu "Edit (id=2)".
      if (col.existing_type_id != null && !this._compTypesById[col.existing_type_id]) {
        const synthOpt = document.createElement("option");
        synthOpt.value = String(col.existing_type_id);
        synthOpt.textContent =
          (col.type_label || ("type#" + col.existing_type_id)) +
          " (id=" + col.existing_type_id + ")";
        synthOpt.selected = true;
        typeSel.insertBefore(synthOpt, typeSel.firstChild);
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

      // Krok H+5+++ (26.5.2026): move buttons (← ↑ ↓) mezi meta a typeSel.
      // Krok H+5++++: ← je teted pinned toggle (always_new_row) — predat
      // layout pro initial state.
      const moveBtns = this._makeMoveButtons(
        col.existing_comp_def_id,
        col.existing_parent_comp_def_id,
        col.existing_sort_order,
        col.existing_layout
      );
      // Krok H+13.2 (27.5.2026, Marti's "presun ikonku nastaveni do skupiny
      // k tem sipcickam, uplne napravo"): ⚙ append do moveBtns wrap jako
      // posledni button (po ↓). Visual grouping s ←→↑↓ arrows.
      moveBtns.appendChild(settingsBtn);

      // X jako prvni — symetrie s "Schazi pridat" checkbox left placement
      row.appendChild(removeBtn);
      row.appendChild(labelWrap);
      row.appendChild(meta);
      row.appendChild(typeSel);
      row.appendChild(moveBtns);

      // Phase 38.4 Krok H+7 (26.5.2026, Marti's "fajn orchestrovat klikem
      // na komponentu v druhem okne. Zvyraznit ji"): klik na radek →
      // highlight komponenty na formulari (flash outline). Skip pokud
      // klik byl na interactive element (button / select / input) —
      // tam ma click vlastni semantiku (delete / type change / settings).
      row.style.cursor = "pointer";
      row.title = "Klikni pro zvýraznění komponenty na formuláři";
      row.addEventListener("click", (ev) => {
        const tag = ev.target && ev.target.tagName;
        if (tag === "BUTTON" || tag === "SELECT" || tag === "INPUT" ||
            tag === "TEXTAREA" || tag === "OPTION") {
          return;  // necht native action chodi
        }
        if (typeof this.opts.onHighlightComponent === "function" &&
            col.existing_comp_def_id != null) {
          try { this.opts.onHighlightComponent(col.existing_comp_def_id); }
          catch (e) { console.error("[FieldPickerModal] onHighlightComponent failed:", e); }
        }
      });
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
      // Krok 5-B Fix #13 (29.5.2026, Marti's "soft-deleted v Nezarazeno"):
      // orphan rows = amber left border + tinted bg + reason badge.
      const isOrphan = col._from_orphan === true;
      const baseCss = "display:grid;grid-template-columns:24px 200px 1fr 160px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        "cursor:pointer;transition:background 0.1s;";
      row.style.cssText = isOrphan
        ? baseCss + "border-left:3px solid #d4b88a;background:rgba(212,184,138,0.05);"
        : baseCss;
      row.addEventListener("mouseenter", () => {
        row.style.background = isOrphan ? "rgba(212,184,138,0.12)" : "#141a20";
      });
      row.addEventListener("mouseleave", () => {
        if (this._selected.has(col.name)) {
          row.style.background = "#1a2530";
        } else {
          row.style.background = isOrphan ? "rgba(212,184,138,0.05)" : "transparent";
        }
      });

      // 1. Checkbox — Phase 38.4 Krok H+5 (26.5.2026, Marti's "orchestr"):
      // Instant POST single column na check. Klik = okamzite komponenta
      // na formu + live sync (onComplete reload).
      // Krok 5-B Fix #13 (29.5.2026): Orphan rows = PATCH is_active=true
      // (re-activate existing comp_def) misto POST (create new).
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.style.cssText = "width:16px;height:16px;cursor:pointer;";
      cb.addEventListener("change", async () => {
        if (!cb.checked) {
          // Uncheck — jen UI state reset (komponenta uz na formu pres prvni
          // check + POST). Pro delete uziva X button v "Jiz na forme" tab.
          row.style.background = isOrphan ? "rgba(212,184,138,0.05)" : "transparent";
          return;
        }
        // Check → instant POST (or PATCH for orphans = re-activate)
        cb.disabled = true;
        row.style.background = "#1a2530";

        // Krok 5-B Fix #13: orphan re-activate path
        if (isOrphan && col.existing_comp_def_id) {
          try {
            const targetParentId = this._resolveTargetParentId();
            const r = await fetch(
              "/api/v1/erp/design/comp_def/" + col.existing_comp_def_id,
              {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  field_changes: {
                    is_active: true,
                    parent_comp_def_id: targetParentId,
                  },
                }),
              }
            );
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.ok) {
              throw new Error(d.error || ("HTTP " + r.status));
            }
            _showToast("Obnoveno: " + (col.caption || col.name), "success", 1500);
            if (typeof this.opts.onComplete === "function") {
              this.opts.onComplete();
            }
            await this._refreshState();
            this._render();
          } catch (e) {
            _showToast("Obnoveni selhalo: " + (e.message || e), "error", 3000);
            cb.disabled = false;
            cb.checked = false;
            row.style.background = "rgba(212,184,138,0.05)";
          }
          return;
        }

        // Standard POST path
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
      labelCap.style.cssText = "font-size:13px;color:#e8eef5;display:flex;align-items:center;gap:6px;";
      const capText = document.createElement("span");
      capText.textContent = col.caption_default;
      labelCap.appendChild(capText);
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
      // Krok 5-B Fix #13 (29.5.2026 vecer, Marti's "pri presunu z
      // Nezarazeno se neaktualizuje Jiz na forme"): mirror load() handler
      // is_orphan split. Orphans (is_active=false) maji existing_comp_def_id
      // != null, takze prosly do _columnsOnForm bez tohoto fixu.
      const _allFieldsRefresh = d.existing_fields || [];
      const _allContainersRefresh = d.existing_containers || [];
      this._existingContainers = _allContainersRefresh.filter(c => !c.is_orphan);
      this._existingFields = _allFieldsRefresh.filter(f => !f.is_orphan);
      const _orphanFieldsRefresh = _allFieldsRefresh.filter(f => f.is_orphan);
      const _orphanContsRefresh = _allContainersRefresh.filter(c => c.is_orphan);

      const _unmatchedRefresh = this._columns.filter(c => c.existing_comp_def_id == null);
      const _matchedRefresh = this._columns.filter(c => c.existing_comp_def_id != null);
      const _matchedIdsRefresh = new Set(_matchedRefresh.map(c => c.existing_comp_def_id));
      const _fieldsAsColsRefresh = this._existingFields
        .filter(f => !_matchedIdsRefresh.has(f.comp_def_id))
        .map(f => ({
          name: f.name,
          caption: f.caption,
          caption_default: f.caption || f.name,
          existing_comp_def_id: f.comp_def_id,
          existing_parent_comp_def_id: f.parent_comp_def_id,
          existing_sort_order: f.sort_order,
          existing_label: f.caption,
          suggested_type_id: f.type_id,
          type_code: f.type_code,
          _from_hierarchy: true,
        }));
      this._columnsOnForm = [..._matchedRefresh, ..._fieldsAsColsRefresh];

      const _orphansToBucketRefresh = [
        ..._orphanFieldsRefresh.map(f => ({
          name: f.name,
          caption: f.caption || f.name,
          caption_default: f.caption || f.name,
          existing_comp_def_id: f.comp_def_id,
          existing_parent_comp_def_id: f.parent_comp_def_id,
          existing_sort_order: f.sort_order,
          existing_label: f.caption,
          suggested_type_id: f.type_id,
          suggested_type_code: f.type_code,
          type_code: f.type_code,
          is_active: f.is_active,
          _from_orphan: true,
          _orphan_reason: f.is_active === false ? "soft-deleted" : "parent soft-deleted",
        })),
        ..._orphanContsRefresh.map(c => ({
          name: c.name,
          caption: c.caption || c.name,
          caption_default: c.caption || c.name,
          existing_comp_def_id: c.comp_def_id,
          existing_parent_comp_def_id: c.parent_comp_def_id,
          existing_sort_order: c.sort_order,
          existing_label: c.caption,
          suggested_type_id: c.type_id,
          suggested_type_code: c.type_code,
          type_code: c.type_code,
          is_active: c.is_active,
          _from_orphan: true,
          _is_container: true,
          _orphan_reason: c.is_active === false ? "soft-deleted" : "parent soft-deleted",
        })),
      ];
      this._columnsAvailable = [..._unmatchedRefresh, ..._orphansToBucketRefresh];

      // Krok H+5++++ (26.5.2026 vecer, Marti's "prohod radky pri zmene poradi"):
      // Backend vrací columns v information_schema order (alphabetic). Pro
      // "Jiz na forme" tab chceme prikazne sort_order — jinak ↑/↓ swap se
      // v UI nezobrazi (DB se zmeni, ale rows zustanou alphabetic).
      const _sortBySO = (a, b) => {
        const aso = (a.existing_sort_order != null ? a.existing_sort_order : 999999);
        const bso = (b.existing_sort_order != null ? b.existing_sort_order : 999999);
        if (aso !== bso) return aso - bso;
        // Tiebreaker: alphabetic by name
        return (a.name || "").localeCompare(b.name || "");
      };
      this._columnsOnForm.sort(_sortBySO);
      this._existingContainers.sort((a, b) => {
        const aso = (a.sort_order != null ? a.sort_order : 999999);
        const bso = (b.sort_order != null ? b.sort_order : 999999);
        return aso - bso;
      });
    }

    // Phase 38.4 Krok H+5 (26.5.2026, Marti's "panel je komponenta"):
    // Container row v "Jiz na forme" tab. Symetrie s _renderOnFormRow
    // (column input), ale meta = type_label badge (panel/groupbox/...).
    // X click = instant DELETE (Marti's "orchestr") + live sync.
    _renderOnFormContainerRow(cont, depth) {
      const isActive = this._activeContainerCompDefId === cont.comp_def_id;
      const row = document.createElement("div");
      // Krok H+8 (26.5.2026): tag row pro reverse orchestrace lookup.
      if (cont.comp_def_id != null) {
        row.dataset.compDefId = String(cont.comp_def_id);
      }
      // Phase 38.4 Krok H+5 (26.5.2026, Marti's "radio button single-select"):
      // Grid: 32px (X) | 24px (radio) | 200px (caption) | 1fr (meta) | 140px (id) | 140px (arrows+settings).
      // Krok H+13.2 (27.5.2026): settings (⚙) moved INTO arrows group → 110→140 + drop separate 32px.
      // Krok H+5+++ (26.5.2026 vecer, Marti's "sipky"): pridana sloupec
      // pro move buttons (← ↑ ↓) mezi meta a id badge.
      // Krok H+5+++++ (26.5.2026 vecer, Marti's "simulovat strom"):
      // depth-based marginLeft (20px/uroven). Container = parent uzel,
      // depth zacina od 0 (root panel pod form root).
      // Aktivni container ma green tint background + bold label.
      const _d = depth || 0;
      row.style.cssText =
        "display:grid;grid-template-columns:32px 24px 200px 1fr 140px 140px;" +
        "align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #1a2028;" +
        (isActive
          ? "background:rgba(93,191,93,0.12);border-left:3px solid #5dbf5d;"
          : "background:rgba(168,140,212,0.06);") +
        (_d > 0 ? "margin-left:" + (_d * 20) + "px;" : "");

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

      // Krok 5.X+1 (27.5.2026, Marti's "nested grid neni kontejner,
      // nema mit radio button"): nested_grid je kind='container' v DB
      // (per pre-existing fw.comp_type), ale UI-behavior wise je field-like:
      // - Nehosti fields (žádný "active target" semantics)
      // - ← arrow = pinned toggle (ne outdent)
      // - ↑↓ = sibling-only (no drill-into / drill-from)
      // Detekce: cont.type_code === 'nested_grid'.
      const _isNestedGrid = (cont.type_code === "nested_grid");

      // Radio button — single-select active container (Marti's pattern).
      // Klik = activate this container (deactivate predchozi), nove
      // komponenty pak jdou jako deti tohoto containeru.
      // Krok 5.X+1: SKIP pro nested_grid → placeholder div pro consistent
      // grid template (24px column width preservation).
      const radioWrap = document.createElement("div");
      radioWrap.style.cssText =
        "display:flex;align-items:center;justify-content:center;" +
        (_isNestedGrid ? "" : "cursor:pointer;");
      if (_isNestedGrid) {
        // Placeholder — nothing rendered (nested_grid není active target)
      } else {
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
      }

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

      // Krok H+5+++ (26.5.2026): move buttons (← ↑ ↓) mezi meta a idBadge.
      // Krok H+9 (26.5.2026, Marti's "panel v panelu nemuzu ven"): isContainer=true
      // → ← znamena OUTDENT (move to grandparent), ne pinned toggle. Pro
      // panely/groupboxů/pagecontrol/tabsheet ma vetsi smysl outdent (panely
      // neflowuji v gridu, takze pinned je no-op).
      // Krok 5.X+1 (27.5.2026, Marti's "← jako pinned, ne outdent"):
      // Nested_grid je v containers_out kvuli kind='container', ale UI-wise
      // se chova jako field — pass isContainer=false → ← = pinned toggle
      // (nepouziva outdent na grandparent). Stejne, panely/groupboxy/etc.
      // zachovaji outdent behavior (isContainer=true).
      const moveBtns = this._makeMoveButtons(
        cont.comp_def_id,
        cont.parent_comp_def_id,
        cont.sort_order,
        cont.layout,
        !_isNestedGrid  // isContainer: false pro nested_grid (field-like ←)
      );
      // Krok H+13.2 (27.5.2026): ⚙ do skupiny arrows (uplne napravo).
      moveBtns.appendChild(settingsBtn);

      row.appendChild(removeBtn);
      row.appendChild(radioWrap);
      row.appendChild(labelWrap);
      row.appendChild(meta);
      row.appendChild(idBadge);
      row.appendChild(moveBtns);

      // Phase 38.4 Krok H+7 (26.5.2026, Marti's "orchestrovat klikem na
      // komponentu v druhem okne i komponentu"): symetrie s _renderOnFormRow.
      // Klik na radek containeru (panel/groupbox/pagecontrol/tabsheet) →
      // flash highlight na formulari. Skip pokud klik byl na interactive
      // element (button/radio/select) — tam ma click vlastni semantiku.
      row.style.cursor = "pointer";
      row.title = "Klikni pro zvýraznění komponenty na formuláři";
      row.addEventListener("click", (ev) => {
        const tag = ev.target && ev.target.tagName;
        if (tag === "BUTTON" || tag === "SELECT" || tag === "INPUT" ||
            tag === "TEXTAREA" || tag === "OPTION" || tag === "LABEL") {
          return;
        }
        if (typeof this.opts.onHighlightComponent === "function" &&
            cont.comp_def_id != null) {
          try { this.opts.onHighlightComponent(cont.comp_def_id); }
          catch (e) { console.error("[FieldPickerModal] onHighlightComponent failed:", e); }
        }
      });
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
