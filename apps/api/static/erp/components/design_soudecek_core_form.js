/**
 * DesignSoudecekCoreForm — extracted standalone JS module.
 *
 * Phase JS-5+6+7 (18.5.2026 ~23:45): extract z design_forms.js.
 * Form 1+2 — fw.menu_node + fw.core editor (Phase 38.4 Krok 14a)
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

  _loader("design_soudecek_core_form.js", "v1.0.0", function () {

    const _DFH = global._erpDFH || {};
    const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
    const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
    const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
    const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
    const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
    const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
    const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
    const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  class DesignSoudecekCoreForm {
    constructor(opts) {
      this.opts = opts || {};
      // opts.menuNodeId (preferred) | opts.menuNodeCode | opts.coreId
      // opts.initialTab = 'prehled' (default po Krok 14g-H+31 step 8) | 'soudecek'
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

    async _onSaveClick() {
      // Phase 38.4 Krok 14g-H+18 (15.5.2026 ~14:49, Marti's "Nejde mi
      // ulozit nastaveni soudecku v HC formu"): reuse Form 3 PATCH pattern
      // pres generic /design/{entity}/{id} endpoint. Form 1 ma 2 entity
      // (menu_node + core), takze split dirty fields by prefix.
      if (this._dirty.size === 0) {
        this._shell.close();
        return;
      }

      const mn = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;

      // Collect dirty changes z DOM. Wraps drzi _fieldKey (mn.label, core.code)
      // + _inst (UI Kit instance pro .value() read).
      const mnChanges = {};
      const coreChanges = {};
      const allWraps = this._shell.body.querySelectorAll(".erp-field, .erp-dropdown, .erp-memo");
      for (const wrap of allWraps) {
        const fk = wrap._fieldKey;
        if (!fk || !this._dirty.has(fk)) continue;
        const parts = fk.split(".");
        if (parts.length < 2) continue;
        const prefix = parts[0];  // "mn" | "core"
        const fieldName = parts.slice(1).join(".");
        let val = null;
        if (wrap._inst && typeof wrap._inst.value === "function") {
          val = wrap._inst.value();
        } else if (wrap._inst && wrap._inst.input) {
          val = wrap._inst.input.value;
        } else {
          const inp = wrap.querySelector("input, textarea, select");
          if (inp) val = inp.value;
        }
        if (prefix === "mn") mnChanges[fieldName] = val;
        else if (prefix === "core") coreChanges[fieldName] = val;
      }

      // Save menu_node + core sekvenčně (oba entity = oba PATCH calls)
      const errors = [];
      let savedCount = 0;

      const _doPatch = async (entityType, rowId, changes, expectedUpdatedAt) => {
        if (!Object.keys(changes).length) return;
        if (rowId == null) {
          errors.push(entityType + ": missing row id");
          return;
        }
        try {
          const r = await fetch(
            "/api/v1/erp/design/" + encodeURIComponent(entityType) + "/" + encodeURIComponent(rowId),
            {
              method: "PATCH",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                field_changes: changes,
                expected_updated_at: expectedUpdatedAt,
              }),
            }
          );
          if (r.status === 409) {
            errors.push(entityType + ": konflikt (někdo jiný editoval)");
            return;
          }
          if (!r.ok) {
            const errData = await r.json().catch(() => ({}));
            errors.push(entityType + ": " + (errData.error || ("HTTP " + r.status)));
            return;
          }
          savedCount += Object.keys(changes).length;
        } catch (e) {
          errors.push(entityType + ": " + (e.message || e));
        }
      };

      if (mn && Object.keys(mnChanges).length) {
        await _doPatch("menu_node", mn.id, mnChanges, mn.updated_at);
      }
      if (core && Object.keys(coreChanges).length) {
        await _doPatch("core", core.id, coreChanges, core.updated_at);
      }

      if (errors.length) {
        alert("Uložení selhalo:\n" + errors.join("\n"));
        return;
      }

      // Success — toast + close
      this._dirty.clear();
      _markFormDirty(this, false);
      const _wToast = savedCount === 1 ? "změna" : (savedCount < 5 ? "změny" : "změn");
      if (typeof _showToast === "function") {
        _showToast("Uloženo — " + savedCount + " " + _wToast, "success");
      }
      this._shell.close();
      // Refresh tree + grid (drag-drop H+9/H+15 pattern)
      try {
        if (typeof window.reloadErpTree === "function") {
          await window.reloadErpTree();
        }
        if (window._sysHelpers
            && typeof window._sysHelpers.renderSystemGrid === "function"
            && window._sysCurrentMode === "menu_nodes") {
          await window._sysHelpers.renderSystemGrid("menu_nodes", window._sysCurrentLabel || "");
        }
      } catch (eRefresh) {
        console.warn("[DesignSoudecekCoreForm] post-save refresh failed:", eRefresh);
      }
    }

    /**
     * Phase 38.4 Krok 14g-H+22 (15.5.2026 ~17:30): core picker pres novou
     * ErpCatalogPicker komponentu (Centrála 1 parita). Reusable napriС
     * vsechny FK reference scenarios.
     */
    async _openCorePickerModal() {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Picker chyba: chybi menu_node ID.");
        return;
      }
      if (typeof window.ErpCatalogPicker !== "function") {
        alert("ErpCatalogPicker not loaded (catalog_picker.js missing).");
        return;
      }

      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Použit v ' + v + ' soudečku(ů)" style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };

      const self = this;
      // Krok 5.V (23.5.2026): LOCATE — initialSelectedId z aktualne
      // asociovaneho core (menu_node.core_id). Picker pri open auto-select
      // + scroll na adekvatni vetu.
      const coreInitId = (menuNode && menuNode.core_id) || null;
      const picker = new window.ErpCatalogPicker({
        title: "🔗 Vybrat existing core přehled",
        endpoint: "/api/v1/erp/design/fw-core/list",
        listKey: "cores",
        coreId: 30,  // Krok 5.T Option C: CORE Jádro (framework_core_list mainscreen)
        initialSelectedId: coreInitId,

        labelField: "label",
        columns: [
          { headerName: "Code", field: "code", width: 220, filter: "agTextColumnFilter", sortable: true },
          { headerName: "Label", field: "label", flex: 1, minWidth: 200, filter: "agTextColumnFilter", sortable: true },
          // Phase fw.core slim 20.5.2026: layout_type column DROPPED
          { headerName: "v", field: "version", width: 60, type: "numericColumn", sortable: true },
          { headerName: "Použit ×", field: "is_used_count", width: 110, type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
        ],
        onSelect: (row) => {
          this._associateCoreWithMenuNode(row.id, row.label, null);
        },
        // Phase 38.4 Krok 14g-H+23 (15.5.2026 ~18:00, Marti's "tlacitko +"):
        // Day 2 first task — enable CRUD ➕ Nový. Edit / Delete stay disabled.
        enableNew: true,
        enableEdit: false,
        enableDelete: false,
        onNew: () => self._openCoreCreateForm(picker),
      });
      picker.open();
    }

    /**
     * Phase 38.4 Krok 14g-H+23 (15.5.2026 ~18:00, Marti's "tlacitko +
     * bez nej se systemove nepohneme"): mini form modal pro CREATE
     * fw.core. Po success refresh picker grid + auto-associate s
     * current menu_node.
     */
    _openCoreCreateForm(picker) {
      // Mini overlay
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10020;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "width:480px;max-width:95vw;background:#1a1f26;border:1px solid #2a3340;" +
        "border-radius:6px;display:flex;flex-direction:column;color:#cfd6df;" +
        "font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.5);";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:14px 18px;border-bottom:1px solid #2a3340;display:flex;" +
        "align-items:center;justify-content:space-between;";
      header.innerHTML = '<div style="font-size:14px;font-weight:600;color:#e8eef5;">' +
        '➕ Vytvořit nový core přehled</div>';
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:none;border:none;color:#7a8696;font-size:18px;cursor:pointer;padding:0 4px;";
      closeBtn.onclick = () => overlay.remove();
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body — form fields
      const body = document.createElement("div");
      body.style.cssText = "padding:18px;display:flex;flex-direction:column;gap:14px;";

      const _mkField = (label, hint, isRequired) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
        const lbl = document.createElement("label");
        lbl.style.cssText = "color:#a8b4c2;font-size:11px;font-weight:500;";
        lbl.innerHTML = label + (isRequired ? ' <span style="color:#d4a8a8;">*</span>' : '');
        wrap.appendChild(lbl);
        if (hint) {
          const h = document.createElement("div");
          h.style.cssText = "color:#7a8696;font-size:10px;font-style:italic;";
          h.textContent = hint;
          wrap.appendChild(h);
        }
        return wrap;
      };

      // code
      const codeWrap = _mkField("Code", "Lowercase snake_case (a-z, 0-9, _). Unikátní v fw.core. Např. 'users_grid', 'audit_dashboard'.", true);
      const codeInput = document.createElement("input");
      codeInput.type = "text";
      codeInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;font-family:monospace;outline:none;";
      codeInput.placeholder = "users_grid";
      codeWrap.appendChild(codeInput);
      body.appendChild(codeWrap);

      // label
      const labelWrap = _mkField("Label", "Human-readable jméno (UI label). Např. 'Uživatelé', 'Audit dashboard'.", true);
      const labelInput = document.createElement("input");
      labelInput.type = "text";
      labelInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      labelInput.placeholder = "Uživatelé";
      labelWrap.appendChild(labelInput);
      body.appendChild(labelWrap);

      // layout_type (dropdown)
      const layoutWrap = _mkField("Layout type", "Jak se přehled zobrazuje. 'list' = AG Grid table. 'form' = single-row editor. Default 'list'.", false);
      const layoutSelect = document.createElement("select");
      layoutSelect.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      ["list", "form", "dashboard", "kanban"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        layoutSelect.appendChild(opt);
      });
      layoutWrap.appendChild(layoutSelect);
      body.appendChild(layoutWrap);

      // Phase 38.4 Krok 5.M-3+B (17.5.2026): "Data entity (table)" input
      // field DROPPED. Krok 5.M doctrine "core nenese entitu". Wizard
      // creates drafted core, entity je odvozena z form root data_source.

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 18px;border-top:1px solid #2a3340;display:flex;" +
        "gap:10px;justify-content:flex-end;align-items:center;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:8px 18px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;" +
        "border-radius:4px;cursor:pointer;font-size:12px;";
      cancelBtn.onclick = () => overlay.remove();
      footer.appendChild(cancelBtn);

      const createBtn = document.createElement("button");
      createBtn.type = "button";
      createBtn.textContent = "➕ Vytvořit";
      createBtn.style.cssText =
        "padding:8px 18px;background:#2a4760;border:1px solid #4a7ba8;color:#a8c4dc;" +
        "border-radius:4px;cursor:pointer;font-size:12px;font-weight:500;";
      createBtn.onclick = async () => {
        const code = codeInput.value.trim();
        const label = labelInput.value.trim();
        const layoutType = layoutSelect.value;
        // Phase 38.4 Krok 5.M-3+B (17.5.2026): dataEntity DROPPED, entity
        // is determined by form root data_source (Krok 5.M doctrine).

        if (!code) { alert("Code je povinný."); codeInput.focus(); return; }
        if (!/^[a-z][a-z0-9_]*$/.test(code)) {
          alert("Code musí být lowercase snake_case (a-z, 0-9, _), začínat písmenem.");
          codeInput.focus();
          return;
        }
        if (!label) { alert("Label je povinný."); labelInput.focus(); return; }

        createBtn.disabled = true;
        createBtn.textContent = "⏳ Vytvářím…";
        try {
          const r = await fetch("/api/v1/erp/design/fw-core", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: code,
              label: label,
              // Phase fw.core slim 20.5.2026: layout_type + data_entity_type DROPPED
            }),
          });
          const data = await r.json().catch(() => ({}));
          if (!r.ok || !data.ok) {
            alert("Vytvoření selhalo: " + (data.error || ("HTTP " + r.status)));
            createBtn.disabled = false;
            createBtn.textContent = "➕ Vytvořit";
            return;
          }
          // Success — toast + close create modal
          if (typeof _showToast === "function") {
            _showToast("Core '" + label + "' vytvořen", "success");
          }
          overlay.remove();
          // Refresh picker grid (new row visible)
          if (picker && typeof picker.refresh === "function") {
            await picker.refresh();
          }
        } catch (e) {
          alert("Vytvoření selhalo: " + (e.message || e));
          createBtn.disabled = false;
          createBtn.textContent = "➕ Vytvořit";
        }
      };
      footer.appendChild(createBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      setTimeout(() => codeInput.focus(), 50);
    }

    async _associateCoreWithMenuNode(coreId, coreLabel, overlay) {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Asociace chyba: chybi menu_node ID.");
        return;
      }
      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { core_id: coreId },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Asociace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Core " + coreLabel + " asociovan", "success");
        }
        if (overlay) overlay.remove();
        // Reload spec — re-render Prehled tab s new core data
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        // Otevri popup znovu (refresh data)
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode.id,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[CorePicker] re-open failed:", e);
          }
        }, 150);
        // Tree + grid refresh (H+9/H+15 pattern)
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[CorePicker] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Asociace selhala: " + (e.message || e));
      }
    }

    /**
     * Phase 38.4 Krok 14g-H+21 (15.5.2026 ~17:00, Marti's "musi byt tlacitko
     * zrusit"): unassociate core přehled od menu_node. PATCH core_id = NULL.
     * Po success → re-open popup s tab='prehled' = empty state placeholder.
     */
    async _unassociateCore() {
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      if (!menuNode || !menuNode.id) {
        alert("Chybi menu_node ID.");
        return;
      }
      const ok = confirm(
        "Zrušit asociaci core přehledu '" + (core && core.label || "?") + "' " +
        "od soudečku '" + (menuNode.label || "?") + "'?\n\n" +
        "menu_node.core_id bude NULL. Core sám zůstane v fw.core (může být " +
        "znovu vybrán nebo asociovaný s jiným soudečkem)."
      );
      if (!ok) return;
      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { core_id: null },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Zrušení selhalo: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Asociace zrušena", "success");
        }
        // Re-open popup s tab='prehled' → empty state placeholder
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode.id,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[Unassociate] re-open failed:", e);
          }
        }, 150);
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[Unassociate] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Zrušení selhalo: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+30 Etapa 3/4/5 (15.5.2026 vecer, Marti's B
    // varianta dotahnout do finale): data_source picker + unassociate.
    //
    // Etapa 3 stub: alert placeholders → real impl v Etape 4 (picker pres
    // ErpCatalogPicker) + Etape 5 (backend PATCH associate). Etapa 6
    // (➕ Novy data_source button) prijde po picker funkcnim.
    // ────────────────────────────────────────────────────────────────────
    async _openDataSourcePickerModal() {
      // Phase 38.4 Krok 14g-H+30 Etapa 4 (15.5.2026 vecer, Marti's
      // "B varianta dotahnout do finale"): real picker via
      // ErpCatalogPicker (reuse z H+22). On-select zatim placeholder —
      // Etapa 5 (associate backend) prijde dal.
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        alert("Picker chyba: chybi core (asociuj nejdriv core v 1. radku).");
        return;
      }
      if (typeof window.ErpCatalogPicker !== "function") {
        alert("ErpCatalogPicker not loaded (catalog_picker.js missing).");
        return;
      }

      // Renderer pro Used by N cores (analog _openCorePickerModal)
      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Pouzit v ' + v + ' core(s) pres code" ' +
                 'style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };

      // Renderer pro operation_kinds (compact list)
      const opsRenderer = function (params) {
        const v = params && params.value;
        if (!v) return '<span style="color:#5a6573;">—</span>';
        return '<span style="color:#a8b4c2;font-size:11px;">' + v + '</span>';
      };

      const self = this;
      const coreCode = core.code || "";
      // Krok 5.V (23.5.2026): LOCATE — initialSelectedId z aktualne
      // asociovaneho data_source. Picker pri open auto-select + scroll
      // na adekvatni vetu. Marti's "kdyz ji otervu, je treba dat locate".
      const dataSource = (this._data && this._data.data_source) || null;
      const dsInitId = (dataSource && dataSource.id) || null;
      const picker = new window.ErpCatalogPicker({
        title: "🔗 Vybrat existing data_source (vazba pres core.code = '" +
               coreCode + "')",
        endpoint: "/api/v1/erp/design/fw-data-source/list",
        listKey: "data_sources",
        coreId: 19,  // Krok 5.T Option C: framework_data_sources core
        initialSelectedId: dsInitId,

        labelField: "name",
        columns: [
          { headerName: "Code", field: "code", width: 220,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Nazev", field: "name", flex: 1, minWidth: 200,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Refresh", field: "refresh_type", width: 110,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Status", field: "status", width: 100,
            filter: "agTextColumnFilter", sortable: true },
          { headerName: "Operations", field: "operation_kinds", flex: 1,
            minWidth: 160, sortable: false, cellRenderer: opsRenderer },
          { headerName: "Ops #", field: "operation_count", width: 80,
            type: "numericColumn", sortable: true },
          { headerName: "v", field: "version", width: 60,
            type: "numericColumn", sortable: true },
          { headerName: "Pouzit ×", field: "is_used_count", width: 100,
            type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
        ],
        onSelect: (row) => {
          // Phase 38.4 Krok 14g-H+30 Etapa 5 (15.5.2026 vecer, Marti's
          // Varianta C "nechat stavajici jak jsou, zacit 1:1 k novemu
          // jadru"): picker je view-only. Pro vytvoreni noveho data_source
          // pro tento core klikni "➕ Novy" v toolbar pickeru.
          alert(
            "📖 View-only browse\n\n" +
            "Vybrane: '" + (row.name || row.code) + "' (id=" + row.id + ")\n\n" +
            "Marti's doctrine 1:1 vazba pres code: kazdy core ma vlastni\n" +
            "data_source s code = core.code. Stavajici data_sources se\n" +
            "nemichaji.\n\n" +
            "Pro vytvoreni noveho data_source pro core '" + coreCode + "'\n" +
            "klikni ➕ Novy vlevo nahore."
          );
        },
        // Phase 38.4 Krok 14g-H+30 Etapa 6 (FINALE): real wizard
        enableNew: true,
        enableEdit: false,
        enableDelete: false,
        onNew: () => self._openDataSourceCreateForm(picker, coreCode),
      });
      picker.open();
    }

    /**
     * Phase 38.4 Krok 14g-H+30 Etapa 6 (15.5.2026 vecer, Marti's Varianta C
     * "1:1 vazba pres code"): mini-form modal pro CREATE fw.data_source.
     * Pre-filled code = core.code (readonly auto-link). Po success refresh
     * picker grid + close picker + reopen Form 1 s tab='prehled'.
     */
    _openDataSourceCreateForm(picker, coreCode) {
      const self = this;
      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;

      // Mini overlay
      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10020;" +
        "display:flex;align-items:center;justify-content:center;";

      const modal = document.createElement("div");
      modal.style.cssText =
        "width:520px;max-width:95vw;background:#1a1f26;border:1px solid #2a3340;" +
        "border-radius:6px;display:flex;flex-direction:column;color:#cfd6df;" +
        "font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.5);";

      // Header
      const header = document.createElement("div");
      header.style.cssText =
        "padding:14px 18px;border-bottom:1px solid #2a3340;display:flex;" +
        "align-items:center;justify-content:space-between;";
      header.innerHTML =
        '<div style="font-size:14px;font-weight:600;color:#e8eef5;">' +
        '➕ Vytvorit novy datovy zdroj pro core ' +
        '<code style="background:#0f141a;padding:1px 6px;border-radius:3px;' +
        'color:#a8c4dc;font-size:12px;">' + coreCode + '</code></div>';
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "✕";
      closeBtn.style.cssText =
        "background:none;border:none;color:#7a8696;font-size:18px;cursor:pointer;padding:0 4px;";
      closeBtn.onclick = () => overlay.remove();
      header.appendChild(closeBtn);
      modal.appendChild(header);

      // Body — form fields
      const body = document.createElement("div");
      body.style.cssText = "padding:18px;display:flex;flex-direction:column;gap:14px;";

      const _mkField = (label, hint, isRequired) => {
        const wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;flex-direction:column;gap:4px;";
        const lbl = document.createElement("label");
        lbl.style.cssText = "color:#a8b4c2;font-size:11px;font-weight:500;";
        lbl.innerHTML = label + (isRequired
          ? ' <span style="color:#d4a8a8;">*</span>' : '');
        wrap.appendChild(lbl);
        if (hint) {
          const h = document.createElement("div");
          h.style.cssText = "color:#7a8696;font-size:10px;font-style:italic;";
          h.textContent = hint;
          wrap.appendChild(h);
        }
        return wrap;
      };

      // code (readonly — Marti's 1:1 doctrine, auto-link via code)
      const codeWrap = _mkField(
        "Code (auto-link na core)",
        "Marti's Varianta C: 1:1 vazba pres code. Hodnota = core.code, readonly.",
        true
      );
      const codeInput = document.createElement("input");
      codeInput.type = "text";
      codeInput.value = coreCode;
      codeInput.readOnly = true;
      codeInput.style.cssText =
        "padding:8px 10px;background:#1a2028;border:1px solid #3a4754;border-radius:4px;" +
        "color:#7a8696;font-size:12px;font-family:monospace;outline:none;cursor:not-allowed;";
      codeWrap.appendChild(codeInput);
      body.appendChild(codeWrap);

      // name (required)
      const nameWrap = _mkField(
        "Nazev",
        "Human-readable jmeno datoveho zdroje (UI label). Napr. 'IP whitelists data source'.",
        true
      );
      const nameInput = document.createElement("input");
      nameInput.type = "text";
      nameInput.placeholder = "Nazev datoveho zdroje";
      nameInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      nameWrap.appendChild(nameInput);
      body.appendChild(nameWrap);

      // refresh_type (dropdown)
      const refreshWrap = _mkField(
        "Refresh type",
        "Kdy data_source obnovuje data. 'manual' = vyzaduje user akci. " +
        "'on_open' = pri otevreni gridu. 'interval' = periodicky. " +
        "'on_event' = trigger jinou udalosti. Default 'manual'.",
        false
      );
      const refreshSelect = document.createElement("select");
      refreshSelect.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;";
      ["manual", "on_open", "interval", "on_event"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        refreshSelect.appendChild(opt);
      });
      refreshSelect.value = "manual";
      refreshWrap.appendChild(refreshSelect);
      body.appendChild(refreshWrap);

      // description (optional textarea)
      const descWrap = _mkField(
        "Popis (optional)",
        "Kratky popis k cemu data_source slouzi. Pro budouci developery / kolegyni.",
        false
      );
      const descInput = document.createElement("textarea");
      descInput.placeholder = "Volitelny popis...";
      descInput.rows = 3;
      descInput.style.cssText =
        "padding:8px 10px;background:#0f141a;border:1px solid #3a4754;border-radius:4px;" +
        "color:#e8eef5;font-size:12px;outline:none;resize:vertical;font-family:inherit;";
      descWrap.appendChild(descInput);
      body.appendChild(descWrap);

      modal.appendChild(body);

      // Footer
      const footer = document.createElement("div");
      footer.style.cssText =
        "padding:12px 18px;border-top:1px solid #2a3340;display:flex;" +
        "gap:10px;justify-content:flex-end;align-items:center;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText =
        "padding:8px 18px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;" +
        "border-radius:4px;cursor:pointer;font-size:12px;";
      cancelBtn.onclick = () => overlay.remove();
      footer.appendChild(cancelBtn);

      const createBtn = document.createElement("button");
      createBtn.type = "button";
      createBtn.textContent = "➕ Vytvorit";
      createBtn.style.cssText =
        "padding:8px 18px;background:#2a4760;border:1px solid #4a7ba8;color:#a8c4dc;" +
        "border-radius:4px;cursor:pointer;font-size:12px;font-weight:500;";
      createBtn.onclick = async () => {
        const code = codeInput.value.trim();
        const name = nameInput.value.trim();
        const refreshType = refreshSelect.value;
        const description = descInput.value.trim() || null;

        if (!name) { alert("Nazev je povinny."); nameInput.focus(); return; }

        createBtn.disabled = true;
        createBtn.textContent = "⏳ Vytvarim…";
        try {
          const r = await fetch("/api/v1/erp/design/fw-data-source", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: code,
              name: name,
              refresh_type: refreshType,
              description: description,
            }),
          });
          const data = await r.json().catch(() => ({}));
          if (!r.ok || !data.ok) {
            alert("Vytvoreni selhalo: " + (data.error || ("HTTP " + r.status)));
            createBtn.disabled = false;
            createBtn.textContent = "➕ Vytvorit";
            return;
          }
          // Success
          if (typeof _showToast === "function") {
            _showToast("Data_source '" + name + "' vytvoren", "success");
          }
          overlay.remove();
          // Close picker (auto-link via code-based vazba — uz je linknuto)
          if (picker && typeof picker.close === "function") {
            picker.close();
          } else if (picker && picker._overlay) {
            picker._overlay.remove();
          }
          // Reload Form 1 — vidime new data_source v 2. groupboxu
          self._dirty.clear();
          _markFormDirty(self, false);
          self._shell.close();
          setTimeout(() => {
            try {
              const reopenOpts = {
                initialTab: "prehled",
              };
              if (menuNode && menuNode.id) {
                reopenOpts.menuNodeId = menuNode.id;
              } else if (core && core.id) {
                reopenOpts.coreId = core.id;
              }
              new window.DesignSoudecekCoreForm(reopenOpts).open();
            } catch (e) {
              console.error("[DataSourceCreate] re-open failed:", e);
            }
          }, 150);
        } catch (e) {
          alert("Vytvoreni selhalo: " + (e.message || e));
          createBtn.disabled = false;
          createBtn.textContent = "➕ Vytvorit";
        }
      };
      footer.appendChild(createBtn);
      modal.appendChild(footer);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      setTimeout(() => nameInput.focus(), 50);
    }

    async _unassociateDataSource() {
      // Phase 38.4 Krok 14g-H+30 Etapa 5 (15.5.2026 vecer, Marti's
      // Varianta C "1:1 vazba pres code"): archive data_source where
      // code=core.code. Soft delete (status='archived'), defense in
      // depth — Marti muze kdykoli un-archive pres SQL.
      const dataSource = (this._data && this._data.data_source) || null;
      const core = (this._data && this._data.core) || null;
      if (!dataSource || !dataSource.id) {
        alert("Nelze archivovat: chybi data_source.");
        return;
      }
      const dsLabel = (dataSource.name || dataSource.code || "?");
      const coreLabel = core ? (core.label || core.code || "?") : "?";

      const decision = await _confirmDarkDialog({
        title: "Archivovat datovy zdroj",
        message:
          "Chces archivovat datovy zdroj?\n\n" +
          "  '" + dsLabel + "' (id=" + dataSource.id + ", code='" +
          (dataSource.code || "") + "')\n" +
          "  asociovany s core '" + coreLabel + "'\n\n" +
          "Soft delete: status -> 'archived'. Data zustavaji v DB.\n" +
          "Marti muze un-archivovat pres SQL nebo budouci 🗄️ Archiv tab.",
        ok: "Archivovat",
        cancel: "Zrusit",
      });
      if (decision !== true) return;

      try {
        const r = await fetch(
          "/api/v1/erp/design/fw-data-source/" +
          encodeURIComponent(dataSource.id) + "/archive",
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Archivace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Datovy zdroj archivovan", "success");
        }
        // Re-open Form 1 s tab='prehled' — vidime updated state (data_source=null)
        const menuNode = (this._data && this._data.menu_node) || null;
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        setTimeout(() => {
          try {
            new window.DesignSoudecekCoreForm({
              menuNodeId: menuNode ? menuNode.id : (core ? null : null),
              coreId: !menuNode && core ? core.id : null,
              initialTab: "prehled",
            }).open();
          } catch (e) {
            console.error("[Unassociate DS] re-open failed:", e);
          }
        }, 150);
      } catch (e) {
        alert("Archivace selhala: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+31 step 4 (15.5.2026 vecer, Marti's "stejne
    // ikonky pro Soudecek"): navigation + archive pro soudecekPicker.
    // ────────────────────────────────────────────────────────────────────

    /**
     * Switch na jiny menu_node (z soudecekPicker 🔗 picker). Close current
     * Form 1 + reopen with new menuNodeId. Standard navigation pattern.
     */
    _switchToMenuNode(newMenuNodeId) {
      if (!newMenuNodeId) return;
      const currentMenuNode = (this._data && this._data.menu_node) || null;
      if (currentMenuNode && currentMenuNode.id === newMenuNodeId) {
        // No-op — same menu_node
        return;
      }
      this._dirty.clear();
      _markFormDirty(this, false);
      this._shell.close();
      setTimeout(() => {
        try {
          new window.DesignSoudecekCoreForm({
            menuNodeId: newMenuNodeId,
            initialTab: "prehled",
          }).open();
        } catch (e) {
          console.error("[SoudecekPicker switch] re-open failed:", e);
        }
      }, 150);
    }

    /**
     * Archive aktualni soudecek (menu_node status='archived'). Soft delete
     * pres existing PATCH /design/menu_node/{id} s field_changes.
     * Po success: close Form 1 + reload tree (gone from sidebar).
     */
    async _archiveSoudecek() {
      const menuNode = (this._data && this._data.menu_node) || null;
      if (!menuNode || !menuNode.id) {
        alert("Nelze archivovat: chybi menu_node.");
        return;
      }
      const decision = await _confirmDarkDialog({
        title: "Archivovat soudeček",
        message:
          "Chceš archivovat soudeček?\n\n" +
          "  '" + (menuNode.label || menuNode.code || "?") + "' " +
          "(id=" + menuNode.id + ", code='" + (menuNode.code || "") + "')\n\n" +
          "Soft delete: status -> 'archived'. Data zustavaji v DB.\n" +
          "Soudeček zmizí ze stromu. Marti muze un-archivovat pres SQL nebo\n" +
          "budouci 🗄️ Archiv tab.",
        ok: "Archivovat",
        cancel: "Zrušit",
      });
      if (decision !== true) return;

      try {
        const r = await fetch(
          "/api/v1/erp/design/menu_node/" + encodeURIComponent(menuNode.id),
          {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              field_changes: { status: "archived" },
              expected_updated_at: menuNode.updated_at,
            }),
          }
        );
        if (!r.ok) {
          const errData = await r.json().catch(() => ({}));
          alert("Archivace selhala: " + (errData.error || ("HTTP " + r.status)));
          return;
        }
        if (typeof _showToast === "function") {
          _showToast("Soudeček archivován", "success");
        }
        this._dirty.clear();
        _markFormDirty(this, false);
        this._shell.close();
        // Reload tree — archived soudeček zmizí
        try {
          if (typeof window.reloadErpTree === "function") {
            await window.reloadErpTree();
          }
        } catch (eRefresh) {
          console.warn("[ArchiveSoudecek] tree refresh failed:", eRefresh);
        }
      } catch (e) {
        alert("Archivace selhala: " + (e.message || e));
      }
    }

    // ────────────────────────────────────────────────────────────────────
    // Phase 38.4 Krok 14g-H+31 step 7 (15.5.2026 vecer, Marti's "pridat
    // tlacitko pro edit"): edit handlery pro 3 pickery. Zatim placeholdery
    // — real edit modal prijde v Krok 14g-H+31 step 8 (po Marti's
    // rozhodnuti jaky scope: full detail vs jen label/description).
    // ────────────────────────────────────────────────────────────────────

    _openCoreEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.core\n\n" +
        "Vybrano: '" + (row.label || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8 (TBD scope: label +\n" +
        "description_user + description_system + layout_type? — Marti rozhodne)."
      );
    }

    _openDataSourceEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.data_source\n\n" +
        "Vybrano: '" + (row.name || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8.\n" +
        "Pole: name, refresh_type, description, row_memory, filter_delay_ms,\n" +
        "default_record_limit (krome immutable: code, version, status)."
      );
    }

    _openSoudecekEditForm(row) {
      if (!row || !row.id) { alert("Vyber radek pro editaci."); return; }
      alert(
        "✏️ Editovat fw.menu_node\n\n" +
        "Vybrano: '" + (row.label || row.code || "?") + "' (id=" + row.id + ")\n\n" +
        "Edit modal prijde v Krok 14g-H+31 step 8.\n" +
        "Pole: label, parent_id, sort_order, kind, visibility_scope,\n" +
        "description (krome immutable: code, id)."
      );
    }

    // Phase 38.4 Krok 14a-A1m #2 (12.5.2026 odpoledne): 📖 popup pro
    // description memo. Vybere entitu podle aktivniho tabu —
    // Soudecek tab → menu_node, Prehled tab → core.
    _openDescriptionsPopup() {
      // Vyber aktivni entity podle aktivniho tabu PageControl.
      const activeId = this._pc && typeof this._pc.getActiveId === "function"
        ? this._pc.getActiveId() : "soudecek";
      const data = this._data || {};
      let entityKind, entityLabel, descUser, descSystem, entityId;
      if (activeId === "prehled" && data.core && data.core.id) {
        entityKind = "core";
        entityId = data.core.id;
        entityLabel = data.core.label || data.core.code || "(bez labelu)";
        descUser = data.core.description_user;
        descSystem = data.core.description_system;
      } else {
        // Default: Soudecek tab / menu_node
        const mn = data.menu_node || {};
        entityKind = "menu_node";
        entityId = mn.id;
        entityLabel = mn.label || mn.code || "(bez labelu)";
        descUser = mn.description_user;
        descSystem = mn.description_system;
      }
      // Krok 14b+21 (14.5.2026 rano): entityId + onSaved -> popup ma 💾
      // Uložit button + PATCH backend. onSaved updates local spec
      // consistency (no reload nutny).
      const self = this;
      _buildDescriptionsPopup({
        entityKind: entityKind,
        entityId: entityId,
        entityLabel: entityLabel,
        descUser: descUser,
        descSystem: descSystem,
        onDirty: this._onDirty.bind(this),
        onSaved: function(payload) {
          if (entityKind === "core" && self._spec && self._spec.data && self._spec.data.core) {
            self._spec.data.core.description_user = payload.description_user;
            self._spec.data.core.description_system = payload.description_system;
          } else if (entityKind === "menu_node" && self._spec && self._spec.data && self._spec.data.menu_node) {
            self._spec.data.menu_node.description_user = payload.description_user;
            self._spec.data.menu_node.description_system = payload.description_system;
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

    _onRevertClick() {
      // Phase 38.4 Krok 14a-A1f #4: klik na dirty badge — confirm + revert.
      // Krok 14a-A1g #2 (12.5.2026 odpoledne): nahrazujeme native confirm()
      // za dark centered dialog (Marti's polish — UX konzistence).
      if (!this._dirty.size) return;
      const count = this._dirty.size;
      // A1q (12.5.2026 vecer): plural fix (1=zmenu, 2-4=zmeny, 5+=zmen)
      // + drop "Pole: ..." výpis (Marti's request, userove fieldKey nerozumi).
      const _wRevert = count === 1 ? "změnu" : (count < 5 ? "změny" : "změn");
      _confirmDarkDialog({
        title: "Vrátit změny?",
        message: "Vrátit " + count + " " + _wRevert + " do původního stavu?",
        // A1t: default Ano/Ne (Marti's polish — Vrátit/Zrušit lidsky matoucí)
      }).then(ok => {
        if (ok) this._revertAll();
      });
    }

    _revertAll() {
      // Iterace pres vsechny .erp-field-design wrappery v modal body —
      // kazdy ma attached _inst + _origVal + _kind (set v _field/_dropdown/_memo).
      if (!this._shell || !this._shell.body) return;
      const wraps = this._shell.body.querySelectorAll(".erp-field-design");
      wraps.forEach(w => {
        if (!w._inst || w._origVal == null) return;
        try {
          // Set original hodnotu
          if (w._kind === "dropdown") {
            w._inst.setValue(w._origVal);
            // Clear dirty styling (onChange neproběhne při setValue programmatically v některých variantách,
            // tak explicit cleanup)
            if (w._inst.trigger) {
              w._inst.trigger.style.borderLeft = "";
              w._inst.trigger.style.background = "";
            }
          } else {
            // _field / _memo — ErpInput / ErpMemo
            w._inst.setValue(w._origVal);
            const el = w._inst.input || w._inst.textarea;
            if (el) {
              el.style.borderLeft = "";
              el.style.background = "";
            }
          }
        } catch (e) {
          console.warn("revert field failed:", w._fieldKey, e);
        }
      });
      // Clear dirty state + hide save button
      this._dirty.clear();
      if (this._saveBtn) this._saveBtn.style.display = "none";
      if (this._dirtyBadge) {
        this._dirtyBadge.textContent = "";
        this._dirtyBadge.style.display = "none";
      }
    }

    open() {
      // Phase 38.4 Krok 14g-H+31 step 8 (15.5.2026 vecer, Marti's "Prehled
      // je 1. tab"): default na "prehled", "soudecek" jen pokud explicit
      // requested. Zachovava back-compat pro existing callers s initialTab.
      const initialTab = this.opts.initialTab === "soudecek" ? "soudecek" : "prehled";
      // Sjednoceny title napric obema akcemi (tree akce 1 + grid akce 2) —
      // form je stejny, jen jiny default tab. Uzivatel vidi scope (soudecek + core).
      const title = "Design: Soudeček + Core přehledu";

      this._shell = _buildModalShell({
        title: title,
        width: "920px",
        beforeClose: () => this._beforeCloseHandler(),
        // A1r (12.5.2026): cleanup global dirty tracking po close.
        onClose: () => _markFormDirty(this, false),
        // Phase 38.4 Krok 14a-A1m #2: 📖 callback — otevre popup s description
        // memo. Podle aktivniho tabu vybere entity (Soudecek tab → menu_node,
        // Prehled tab → core).
        onShowDescriptions: () => this._openDescriptionsPopup(),
      });
      document.body.appendChild(this._shell.overlay);

      // Loading placeholder
      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer — dirty badge (left, clickable → revert) + Save button (hidden) + Zavřít
      this._dirtyBadge = document.createElement("span");
      this._dirtyBadge.style.cssText = "color:#d4b88a;font-size:12px;margin-right:auto;display:none;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;";
      this._dirtyBadge.title = "Klik pro vrácení všech změn (po potvrzení)";
      this._dirtyBadge.addEventListener("click", () => this._onRevertClick());
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

      // Fetch data
      this._fetchData(initialTab);
    }

    _fetchData(initialTab) {
      const id = this.opts.menuNodeId || this.opts.menuNodeCode
        || this.opts.coreId || this.opts.coreCode;
      if (!id) {
        this._showError("Chybí ID — předej menuNodeId, menuNodeCode, coreId nebo coreCode.");
        return;
      }
      // Build URL — backend resolve podle typu identifiku.
      // Vsechny 4 endpointy vraci {menu_node, core, columns} — frontend
      // si poradi (Tab "Soudecek" empty pokud menu_node=null, Tab "Prehled"
      // empty pokud core=null).
      let url;
      if (this.opts.menuNodeId) {
        url = "/api/v1/erp/design/menu-node/" + encodeURIComponent(this.opts.menuNodeId);
      } else if (this.opts.coreId) {
        url = "/api/v1/erp/design/core/" + encodeURIComponent(this.opts.coreId);
      } else if (this.opts.coreCode) {
        url = "/api/v1/erp/design/core-by-code/" + encodeURIComponent(this.opts.coreCode);
      } else {
        // Phase 22.5.2026: menu-node-by-code fallback dropped (code column removed).
        // No usable identifier — surface error.
        this._showError("Chybi identifikator (menuNodeId/coreId/coreCode).");
        return;
      }
      fetch(url, { credentials: "same-origin", cache: "no-store" })
        .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject("HTTP " + r.status + ": " + t)))
        .then(data => {
          this._data = data || {};
          this._render(initialTab);
        })
        .catch(err => {
          console.error("DesignSoudecekCoreForm fetch failed:", err);
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

    _render(initialTab) {
      this._shell.body.innerHTML = "";

      // Build 2 tab content divs
      const soudecekDiv = this._buildSoudecekTab();
      const prehledDiv = this._buildPrehledTab();

      // ErpPageControl
      this._pc = new global.ErpPageControl(this._shell.body, {
        tabs: [
          // Phase 38.4 Krok 14g-H+31 step 8 (15.5.2026 vecer, Marti's
          // "Prohod ty dve zalozky"): Prehled je teď 1. tab (primary),
          // Soudecek se stava 2. tabem s názvem "Smazat později" —
          // predprava pro uplne smazani po prenesem parametrizace do
          // Prehled tabu (Marti's dlouhodoba vize).
          { id: "prehled", label: "Přehled", content: prehledDiv },
          { id: "soudecek", label: "Smazat později", content: soudecekDiv },
        ],
        activeId: initialTab,
      });
      // Phase 38.4 Krok 14a-A1e (12.5.2026 odpoledne): TabSheet stable height
      // — Marti's #3 polish: switching tab nemá uskakovat. Set min-height na
      // pageControl content area = vyssi z obou tab obsahu. Computed once
      // po render (oba taby maji content vyrenderovany, jen jeden visible).
      if (this._pc && this._pc.contentArea) {
        // Compute max height pres oba taby (musime docasne unhide oba)
        const maxH = this._computeMaxTabHeight(soudecekDiv, prehledDiv);
        if (maxH > 0) {
          this._pc.contentArea.style.minHeight = maxH + "px";
        }
      }
    }

    _computeMaxTabHeight(...tabContents) {
      // Trick: docasne ukaž každý tab content (hidden = false), zmer scrollHeight,
      // pak vrať zpet. Pages with display:none nemaji computed height.
      let maxH = 0;
      tabContents.forEach(div => {
        if (!div) return;
        const wasHidden = div.hidden;
        const prevDisplay = div.style.display;
        div.hidden = false;
        div.style.display = "block";
        div.style.position = "absolute";
        div.style.visibility = "hidden";
        const h = div.scrollHeight || 0;
        if (h > maxH) maxH = h;
        div.hidden = wasHidden;
        div.style.display = prevDisplay;
        div.style.position = "";
        div.style.visibility = "";
      });
      return maxH;
    }

    _buildSoudecekTab() {
      const root = document.createElement("div");
      root.className = "erp-design-tab-soudecek";
      const mn = (this._data && this._data.menu_node) || {};
      if (!mn || !mn.id) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;color:#8a96a4;font-style:italic;";
        empty.textContent = "Žádná data pro soudeček (menu_node nenalezeno).";
        root.appendChild(empty);
        return root;
      }

      // Dirty tracking — local closures
      const D = this._onDirty.bind(this);
      const _f = (l, v, key, o) => _field(l, v, Object.assign({fieldKey: key, onDirty: D}, o || {}));
      const _d = (l, v, items, key, o) => _dropdown(l, v, items, Object.assign({fieldKey: key, onDirty: D}, o || {}));

      // Section: Identifikace — ID readonly (PK), Kind je enum dropdown
      // Krok 14a-A1m #1: section title pair (user / system technical name).
      const idSec = _sectionBuild("Identifikace", "fw.menu_node — identita");
      idSec.grid.appendChild(_f("ID (menu_node.id)", mn.id, "mn.id", { mono: true, readonly: true }));
      idSec.grid.appendChild(_f("Code", mn.code, "mn.code", { mono: true }));
      idSec.grid.appendChild(_f("Label", mn.label, "mn.label"));
      idSec.grid.appendChild(_d("Kind", mn.kind, "kind", "mn.kind"));
      root.appendChild(idSec.wrap);

      // Section: Hierarchie — parent_id/parent_code readonly, status/visibility/
      // is_immutable jsou enum dropdowny
      const treeSec = _sectionBuild("Hierarchie a pořadí", "fw.menu_node — tree position + visibility");
      treeSec.grid.appendChild(_f("Parent ID", mn.parent_id, "mn.parent_id", { mono: true, readonly: true }));
      treeSec.grid.appendChild(_f("Parent Code", mn.parent_code, "mn.parent_code", { mono: true, readonly: true }));
      treeSec.grid.appendChild(_f("Sort Order", mn.sort_order, "mn.sort_order", { mono: true }));
      treeSec.grid.appendChild(_d("Status", mn.status, "status", "mn.status"));
      treeSec.grid.appendChild(_d("Visibility Scope", mn.visibility_scope, "visibility_scope", "mn.visibility_scope"));
      treeSec.grid.appendChild(_d("Is Immutable", mn.is_immutable, "bool_ano_ne", "mn.is_immutable"));
      root.appendChild(treeSec.wrap);

      // Section: Core vazba — FK readonly (vybira se pres picker, Krok 14b)
      const coreSec = _sectionBuild("Vazba na Core přehledu", "fw.menu_node — core_id FK + legacy chain");
      coreSec.grid.appendChild(_f("core_id (FK)", mn.core_id, "mn.core_id", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("menu_node_pk (legacy)", mn.menu_node_pk, "mn.menu_node_pk", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("framework_jadro_id", mn.framework_jadro_id, "mn.framework_jadro_id", { mono: true, readonly: true }));
      coreSec.grid.appendChild(_f("special_handler", mn.special_handler, "mn.special_handler"));
      root.appendChild(coreSec.wrap);

      // Phase 38.4 Krok 14a-A1m #2 (12.5.2026): popis je v separatnim popupu
      // (📖 ikona v header). Zadna inline Popis sekce v form. Krabicka pro
      // detailni popis core / soudecku — obdoba CLAUDE.md per entity.

      return root;
    }

    _buildPrehledTab() {
      // Phase 38.4 Krok 14g-H+31 step 2 (15.5.2026 vecer, Marti's
      // "vyrobit plnohodnotne FW componenty z provizornich inline
      // groupboxu"): full refactor — drop ~178 LOC inline kódu,
      // instantiate 2x ErpEntityPicker (corePicker + dsPicker).
      // Reusable pattern pripraven pro DataSource Operation editor
      // (Krok 14g-H+32: dalsi ErpEntityPicker pro DataSet picker).
      const root = document.createElement("div");
      root.className = "erp-design-tab-prehled";

      // Defensive: pokud entity_picker.js nenacten, ukaz error
      if (typeof window.ErpEntityPicker !== "function") {
        const err = document.createElement("div");
        err.style.cssText =
          "padding:20px;color:#e88;background:#3a1818;border:1px solid #5a2828;" +
          "border-radius:4px;font-size:13px;";
        err.textContent =
          "ErpEntityPicker komponenta nenactena (entity_picker.js missing). " +
          "Zkus hard reload prohlížeč (Ctrl+Shift+R).";
        root.appendChild(err);
        return root;
      }

      const menuNode = (this._data && this._data.menu_node) || null;
      const core = (this._data && this._data.core) || null;
      const hasCore = !!(core && core.id);
      const dataSource = (this._data && this._data.data_source) || null;
      const coreCode = hasCore ? (core.code || "") : "";
      const self = this;

      // Cell renderery sdilene mezi pickery
      const usedRenderer = function (params) {
        const v = params && params.value;
        if (v && v > 0) {
          return '<span title="Pouzit v ' + v + ' core(s)" ' +
                 'style="color:#7a8696;">🔗 ' + v + '×</span>';
        }
        return '';
      };
      const opsRenderer = function (params) {
        const v = params && params.value;
        if (!v) return '<span style="color:#5a6573;">—</span>';
        return '<span style="color:#a8b4c2;font-size:11px;">' + v + '</span>';
      };

      // ─── 0. SoudecekPicker (Soudeček — vazba na menu_node) ─────────────
      // Phase 38.4 Krok 14g-H+31 step 4 (15.5.2026 vecer, Marti's "drop
      // readOnly, dat soudecku stejne ikonky jako Prehled+Datovy zdroj —
      // vzhled sjednoceny, cilem do budoucna je smazat 1. tab Soudecek
      // a mit jen Prehled tab s parametrizaci"): full ErpEntityPicker.
      // - 🔗 Vybrat: switch na jiny menu_node (navigation)
      // - 🚫 Archivovat: soft delete menu_node (status='archived')
      // - ➕ Novy: disabled — pouzij "+ Novy soudecek" v tree footer
      this._soudecekPicker = new window.ErpEntityPicker({
        label: "Soudeček",
        subtitle: "fw.menu_node — aktualne editovany soudecek",
        idLabel: "Číslo",
        nameLabel: "Název soudečku",
        entity: menuNode ? {
          id: menuNode.id,
          name: menuNode.label || menuNode.code,
          code: menuNode.code,
        } : null,
        placeholderText: "(žádný soudeček — Form 3 mode)",
        pickerConfig: {
          title: "🔗 Vybrat jiný soudeček (switch na jiný menu_node)",
          endpoint: "/api/v1/erp/design/menu-nodes",
          listKey: "items",
          labelField: "label",
          // Phase 38.4 Krok 14g-H+31 step 5 (15.5.2026 vecer, Marti's
          // "pro zacatek jen ID + Label fixne, pozdeji ulozeni sestavy"):
          // minimal columns. TODO: persist user sestava (analog grid).
          columns: [
            { headerName: "ID", field: "id", width: 90,
              type: "numericColumn", sortable: true,
              filter: "agNumberColumnFilter" },
            { headerName: "Label", field: "label", flex: 1, minWidth: 240,
              filter: "agTextColumnFilter", sortable: true },
          ],
        },
        onPick: (row) => self._switchToMenuNode(row.id),
        onUnassociate: () => self._archiveSoudecek(),
        // Phase 38.4 Krok 14g-H+31 step 6 (15.5.2026 vecer, Marti's "jedna
        // komponenta pro vsechny 3 pripady"): showCreate=true, onCreate
        // volá existing wizard window._erpOpenNewSoudecekDialog (sjednoceni
        // s "+ Novy soudecek" v tree footer).
        showCreate: true,
        onEdit: (row) => self._openSoudecekEditForm(row),
        onCreate: (picker) => {
          if (typeof window._erpOpenNewSoudecekDialog !== "function") {
            alert(
              "Wizard pro novy soudecek neni nacten.\n\n" +
              "(window._erpOpenNewSoudecekDialog missing — pravdepodobne " +
              "STRATEGIE-API nebyl restartovan po deploy router.py changes.)"
            );
            return;
          }
          // Close picker pred wizard (avoid nesting modals confusion)
          if (picker && typeof picker.close === "function") {
            picker.close();
          } else if (picker && picker._overlay) {
            picker._overlay.remove();
          }
          // Wizard params: defaultParentId = current menuNode parent_id
          // (pokud existuje), onSuccess switch na new menu_node.
          const currentMenuNode = (self._data && self._data.menu_node) || null;
          window._erpOpenNewSoudecekDialog({
            defaultParentId: currentMenuNode
              ? (currentMenuNode.parent_id != null
                  ? currentMenuNode.parent_id
                  : null)
              : null,
            onSuccess: (newId) => {
              if (newId) self._switchToMenuNode(newId);
            },
          });
        },
      });
      this._soudecekPicker.mount(root);

      // ─── 1. CorePicker (Přehled) ──────────────────────────────────
      this._corePicker = new window.ErpEntityPicker({
        label: "Přehled",
        subtitle: "fw.core — vazba na core_id",
        idLabel: "Číslo",
        nameLabel: "Název definice přehledu",
        entity: core ? {
          id: core.id,
          name: core.label || core.code,
          code: core.code,
        } : null,
        placeholderText: "(žádný core — klik 🔗)",
        pickerConfig: {
          title: "🔗 Vybrat existing core přehled",
          endpoint: "/api/v1/erp/design/fw-core/list",
          listKey: "cores",
          labelField: "label",
          columns: [
            { headerName: "Code", field: "code", width: 220,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Label", field: "label", flex: 1, minWidth: 200,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Layout", field: "_layout_type_dropped", width: 0, hide: true,  // Phase fw.core slim 20.5.2026
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "v", field: "version", width: 60,
              type: "numericColumn", sortable: true },
            { headerName: "Použit ×", field: "is_used_count", width: 110,
              type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
          ],
        },
        onPick: (row) => self._associateCoreWithMenuNode(row.id, row.label, null),
        onUnassociate: () => self._unassociateCore(),
        onCreate: (picker) => self._openCoreCreateForm(picker),
        onEdit: (row) => self._openCoreEditForm(row),
        showCreate: true,
      });
      this._corePicker.mount(root);

      // ─── 2. DsPicker (Datový zdroj) — gated na hasCore ────────────
      this._dsPicker = new window.ErpEntityPicker({
        label: "Datový zdroj",
        subtitle: "fw.data_source — vazba pres code (s.code = c.code)",
        idLabel: "Číslo",
        nameLabel: "Název datového zdroje",
        entity: dataSource ? {
          id: dataSource.id,
          name: dataSource.name || dataSource.code,
          code: dataSource.code,
        } : null,
        placeholderText: hasCore
          ? "(žádný data_source — klik 🔗)"
          : "(nejdřív vyber core 👆)",
        disabled: !hasCore,
        disabledReason:
          "Datový zdroj se váže na core (přes code).\n" +
          "Nejdřív vyber/vytvoř core přehled v 1. řádku.",
        prefillCode: coreCode,
        pickerConfig: {
          title: "🔗 Vybrat existing data_source (vazba pres core.code = '" +
                 coreCode + "')",
          endpoint: "/api/v1/erp/design/fw-data-source/list",
          listKey: "data_sources",
          labelField: "name",
          columns: [
            { headerName: "Code", field: "code", width: 220,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Nazev", field: "name", flex: 1, minWidth: 200,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Refresh", field: "refresh_type", width: 110,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Status", field: "status", width: 100,
              filter: "agTextColumnFilter", sortable: true },
            { headerName: "Operations", field: "operation_kinds", flex: 1,
              minWidth: 160, sortable: false, cellRenderer: opsRenderer },
            { headerName: "Ops #", field: "operation_count", width: 80,
              type: "numericColumn", sortable: true },
            { headerName: "v", field: "version", width: 60,
              type: "numericColumn", sortable: true },
            { headerName: "Pouzit ×", field: "is_used_count", width: 100,
              type: "numericColumn", sortable: true, cellRenderer: usedRenderer },
          ],
          onSelect: (row) => {
            // Marti's Varianta C — view-only browse
            alert(
              "📖 View-only browse\n\n" +
              "Vybrane: '" + (row.name || row.code) + "' (id=" + row.id + ")\n\n" +
              "Marti's doctrine 1:1 vazba pres code: kazdy core ma vlastni\n" +
              "data_source s code = core.code. Stavajici data_sources se\n" +
              "nemichaji.\n\n" +
              "Pro vytvoreni noveho data_source pro core '" + coreCode + "'\n" +
              "klikni ➕ Novy vlevo nahore."
            );
          },
        },
        onUnassociate: () => self._unassociateDataSource(),
        onCreate: (picker) => self._openDataSourceCreateForm(picker, coreCode),
        onEdit: (row) => self._openDataSourceEditForm(row),
        showCreate: true,
      });
      this._dsPicker.mount(root);

      // Note: popis (📖 popup) zustava v header (separate flow).
      // _openCorePickerModal + _openDataSourcePickerModal jsou nyni
      // dead code (logic moved into ErpEntityPicker.pickerConfig).
      // Cleanup v separate commitu po smoke test.

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Form 3: Jadro pro radek (1 tab MVP, prepared for expansion)
  // ────────────────────────────────────────────────────────────────────


    global.DesignSoudecekCoreForm = DesignSoudecekCoreForm;
  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
