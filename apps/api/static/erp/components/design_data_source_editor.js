/**
 * DesignDataSourceEditor — extracted standalone JS module.
 *
 * Phase JS-5+6+7 (18.5.2026 ~23:45): extract z design_forms.js.
 * DataSource + operations editor (Krok 5.K power-tool)
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

  _loader("design_data_source_editor.js", "v1.0.0", function () {

    const _DFH = global._erpDFH || {};
    const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
    const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
    const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
    const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
    const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
    const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
    const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
    const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  class DesignDataSourceEditor {
    constructor(opts) {
      this.opts = opts || {};
      this.dataSourceId = this.opts.dataSourceId || null;  // null = new
      this.onComplete = this.opts.onComplete || null;
      this._spec = null;       // { source, operations } z GET full
      this._headerState = null; // { code, name, description, refresh_type, default_record_limit }
      this._opsState = [];     // Array of { variant_code, operation_kind, is_default, sort_order, data_set: {...} | data_set_id }
      this._shell = null;
      this._editors = [];      // tracked Ace editor instances pro destroy
      this._isCreateMode = (this.dataSourceId == null);
      this._dbConnections = [];  // Krok 5.M-D: fetched at open()
    }

    async open() {
      const title = this._isCreateMode
        ? "➕ Nový datový zdroj"
        : ("📦 Datový zdroj #" + this.dataSourceId);
      this._shell = _buildModalShell({
        title: title,
        width: "1100px",
        beforeClose: () => this._beforeCloseHandler(),
        onClose: () => this._cleanup(),
      });
      document.body.appendChild(this._shell.overlay);

      // Loading state
      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer
      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Storno";
      cancelBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;";
      cancelBtn.addEventListener("click", () => this._shell.close());
      this._shell.footer.appendChild(cancelBtn);

      this._saveBtn = document.createElement("button");
      this._saveBtn.type = "button";
      this._saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      this._saveBtn.style.cssText = "padding:6px 16px;background:#3a5a8a;border:1px solid #4a7ba8;border-radius:3px;color:#e8eef5;cursor:pointer;font-size:12px;font-weight:600;";
      this._saveBtn.addEventListener("click", () => this._onSaveClick());
      this._shell.footer.appendChild(this._saveBtn);

      // Krok 5.M-D: pre-fetch db connections z DB
      this._dbConnections = await _fetchDbConnections();

      if (this._isCreateMode) {
        // Init empty spec
        this._spec = { source: null, operations: [] };
        this._headerState = {
          code: "",
          name: "",
          description: "",
          refresh_type: "manual",
          default_record_limit: 10000,
        };
        this._opsState = [];
        this._render();
      } else {
        this._fetchData();
      }
    }

    _cleanup() {
      // Destroy Ace editor instances pro proper cleanup
      for (const ed of this._editors) {
        try { if (ed && typeof ed.destroy === "function") ed.destroy(); } catch (e) {}
      }
      this._editors = [];
    }

    async _beforeCloseHandler() {
      // TODO Krok 5.K-B3: dirty check pres _confirmDarkDialog
      return "close";
    }

    async _fetchData() {
      try {
        const r = await fetch(
          "/api/v1/erp/design/data-source/" + encodeURIComponent(this.dataSourceId) + "/full",
          { method: "GET", credentials: "include" }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error(eb.error || ("HTTP " + r.status));
        }
        this._spec = await r.json();
        if (!this._spec || !this._spec.ok) {
          throw new Error("Neplatná response (ok=false)");
        }
        // Init working state z loaded data
        const src = this._spec.source || {};
        this._headerState = {
          code: src.code || "",
          name: src.name || "",
          description: src.description || "",
          refresh_type: src.refresh_type || "manual",
          default_record_limit: src.default_record_limit || 10000,
        };
        this._opsState = (this._spec.operations || []).map(op => ({
          existing: true,  // marker — existing ops nelze editovat v MVP, jen read
          op_id: op.id,
          variant_code: op.variant_code,
          operation_kind: op.operation_kind,
          is_default: op.is_default,
          sort_order: op.sort_order,
          description: op.description,
          data_set: op.data_set,  // full inline display
        }));
        this._render();
      } catch (e) {
        console.error("[DesignDataSourceEditor] _fetchData failed:", e);
        this._shell.body.innerHTML = "";
        const err = document.createElement("div");
        err.style.cssText = "padding:24px;color:#e57373;font-size:13px;";
        err.textContent = "Načtení selhalo: " + (e.message || e);
        this._shell.body.appendChild(err);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";
      this._cleanup();  // destroy any existing editors before re-render

      const wrap = document.createElement("div");
      wrap.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:18px;";

      // Sekce 1: Header
      this._renderHeaderSection(wrap);

      // Sekce 2: Operations
      this._renderOpsSection(wrap);

      this._shell.body.appendChild(wrap);
    }

    _renderHeaderSection(parent) {
      const sec = document.createElement("div");
      sec.style.cssText = "display:flex;flex-direction:column;gap:10px;padding:12px;background:#0f1419;border:1px solid #2a3340;border-radius:4px;";

      const title = document.createElement("div");
      title.style.cssText = "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;text-transform:uppercase;padding-bottom:4px;border-bottom:1px solid #1f2630;";
      title.textContent = "📦 Hlavička";
      sec.appendChild(title);

      // 2-column grid
      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:120px 1fr;gap:10px 12px;align-items:center;";

      const _addInput = (label, key, type, placeholder, opts) => {
        const lbl = document.createElement("label");
        lbl.textContent = label;
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        grid.appendChild(lbl);

        let el;
        if (type === "textarea") {
          el = document.createElement("textarea");
          el.rows = 2;
          el.style.cssText = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;resize:vertical;min-height:40px;font-family:inherit;";
        } else if (type === "select") {
          el = document.createElement("select");
          el.style.cssText = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;cursor:pointer;";
          for (const opt of (opts || [])) {
            const optEl = document.createElement("option");
            optEl.value = opt.value;
            optEl.textContent = opt.label;
            el.appendChild(optEl);
          }
        } else {
          el = document.createElement("input");
          el.type = type || "text";
          el.style.cssText = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;";
        }
        el.value = this._headerState[key] != null ? String(this._headerState[key]) : "";
        if (placeholder) el.placeholder = placeholder;
        el.addEventListener("input", () => {
          if (type === "number") {
            const n = parseInt(el.value, 10);
            this._headerState[key] = isNaN(n) ? null : n;
          } else {
            this._headerState[key] = el.value;
          }
        });
        grid.appendChild(el);
      };

      // Krok 5.K-B4 (Marti's "code je matouci a navic"): kód NENÍ visible
      // jako input. V edit mode display jako read-only 🔒 pill (visual badge,
      // user vidí ID/code). V create mode auto-generated z name v save flow.
      if (!this._isCreateMode && this._spec && this._spec.source && this._spec.source.code) {
        const lbl = document.createElement("label");
        lbl.textContent = "Identita";
        lbl.style.cssText = "color:#a8b4c2;font-size:12px;";
        grid.appendChild(lbl);
        const pill = document.createElement("div");
        pill.style.cssText = "display:inline-flex;align-items:center;gap:6px;padding:5px 10px;background:#0a0f14;border:1px dashed #2a3340;border-radius:3px;color:#7ed4e8;font-family:monospace;font-size:12px;width:fit-content;";
        pill.innerHTML = "🔒 <span>" + (this._spec.source.code) + "</span>" +
          " <span style=\"color:#6a7684;\">· id=" + (this._spec.source.id || "?") + "</span>";
        grid.appendChild(pill);
      }
      _addInput("Název", "name", "text", "lidsky čitelný název (např. 'EUROSOFT Klienti')");
      _addInput("Popis", "description", "textarea", "Krátký popis účelu");
      _addInput("Refresh type", "refresh_type", "select", null, DDS_REFRESH_TYPES);
      _addInput("Default limit", "default_record_limit", "number", "10000");

      sec.appendChild(grid);
      parent.appendChild(sec);
    }

    _renderOpsSection(parent) {
      const sec = document.createElement("div");
      sec.style.cssText = "display:flex;flex-direction:column;gap:10px;padding:12px;background:#0f1419;border:1px solid #2a3340;border-radius:4px;";

      const headerRow = document.createElement("div");
      headerRow.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding-bottom:4px;border-bottom:1px solid #1f2630;";

      const title = document.createElement("div");
      title.style.cssText = "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;text-transform:uppercase;";
      title.textContent = "🔗 Operace (" + this._opsState.length + ")";
      headerRow.appendChild(title);

      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.textContent = "➕ Přidat operaci";
      addBtn.style.cssText = "padding:4px 12px;background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:11px;font-weight:600;";
      addBtn.addEventListener("click", () => this._showAddOpForm(sec, addBtn));
      headerRow.appendChild(addBtn);

      sec.appendChild(headerRow);

      // Existing ops list
      if (this._opsState.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:12px;color:#6a7684;font-size:12px;font-style:italic;text-align:center;";
        empty.textContent = "Žádné operace. Klikni ➕ Přidat operaci.";
        sec.appendChild(empty);
      } else {
        for (let i = 0; i < this._opsState.length; i++) {
          sec.appendChild(this._renderOpRow(this._opsState[i], i));
        }
      }

      parent.appendChild(sec);
    }

    _renderOpRow(op, idx) {
      const row = document.createElement("div");
      // Krok 5.K-B5: drop variant_code sloupec (Marti's strach), display
      // description + operation_kind + data_set summary + default + status.
      row.style.cssText = "display:grid;grid-template-columns:80px 1fr 60px 90px 30px;gap:8px;align-items:center;padding:8px 10px;background:#0a0f14;border:1px solid #1f2630;border-radius:3px;font-size:12px;";
      const isExisting = !!op.existing;
      if (!isExisting) {
        row.style.borderColor = "#3a8aa8";
        row.style.background = "#0a1820";
      }

      const _cell = (text, opts) => {
        const c = document.createElement("div");
        c.textContent = text;
        c.style.cssText = "color:#cfd6df;" + (opts && opts.mono ? "font-family:monospace;color:#7ed4e8;" : "");
        return c;
      };

      row.appendChild(_cell(op.operation_kind));
      // Description = primary human label. Fallback na data_set summary
      // pokud description chybí.
      // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): data_set.kind dropped.
      const humanLabel = op.description
        ? op.description
        : (op.data_set
            ? ("📄 " + (op.data_set.db_connection || "?"))
            : "(?)");
      row.appendChild(_cell(humanLabel));
      row.appendChild(_cell(op.is_default ? "✓ default" : ""));
      row.appendChild(_cell(isExisting ? "existing" : "new", { mono: true }));

      // Action button
      const actionBtn = document.createElement("button");
      actionBtn.type = "button";
      if (isExisting) {
        // Krok 5.K-B3 (17.5.2026 dopoledne, Marti's "ted je treba se k tomu
        // vratit a editovat"): existing op → ✏ Edit button → expand inline form
        // s pre-populated values + per-op PATCH save. Žádné 👁 read-only view.
        actionBtn.textContent = "✏";
        actionBtn.title = "Editovat operaci + SQL";
        actionBtn.style.cssText = "padding:2px 6px;background:transparent;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:11px;";
        actionBtn.addEventListener("click", () => this._showEditOpForm(row, op, idx, actionBtn));
      } else {
        actionBtn.textContent = "✕";
        actionBtn.title = "Odstranit operaci (nebyla uložena)";
        actionBtn.style.cssText = "padding:2px 6px;background:transparent;border:1px solid #5a2828;color:#e57373;border-radius:3px;cursor:pointer;font-size:11px;";
        actionBtn.addEventListener("click", () => {
          this._opsState.splice(idx, 1);
          this._render();
        });
      }
      row.appendChild(actionBtn);

      return row;
    }

    _showOpSqlReadOnly(op) {
      // Quick view existing data_set SQL — modal s ErpRichEdit read-only
      const overlay = document.createElement("div");
      overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:10030;display:flex;align-items:center;justify-content:center;";

      const dialog = document.createElement("div");
      dialog.style.cssText = "background:#141a20;border:1px solid #2a3340;border-radius:6px;width:900px;max-width:95vw;color:#e8eef5;font-size:13px;padding:16px;display:flex;flex-direction:column;gap:10px;box-shadow:0 12px 40px rgba(0,0,0,0.6);";

      const titleEl = document.createElement("div");
      titleEl.style.cssText = "font-weight:600;font-size:14px;";
      // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): data_set.kind dropped.
      titleEl.innerHTML = "📄 " + (op.data_set.code || "data_set") +
        " <span style=\"color:#7ed4e8;font-size:11px;font-weight:400;\">" +
        op.data_set.db_connection + "</span>";
      dialog.appendChild(titleEl);

      const editorHost = document.createElement("div");
      dialog.appendChild(editorHost);

      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "Zavřít";
      closeBtn.style.cssText = "padding:6px 16px;background:#2a3340;border:1px solid #3a4754;border-radius:3px;color:#cfd6df;cursor:pointer;font-size:12px;align-self:flex-end;";
      closeBtn.addEventListener("click", () => {
        try { document.body.removeChild(overlay); } catch (e) {}
      });
      dialog.appendChild(closeBtn);

      overlay.appendChild(dialog);
      document.body.appendChild(overlay);

      if (typeof global.ErpRichEdit === "function") {
        const ed = new global.ErpRichEdit(editorHost, {
          value: op.data_set.sql_text || "",
          language: "sql",
          theme: "monokai",
          readonly: true,
          height: "400px",
          lineNumbers: true,
        });
        this._editors.push(ed);
      } else {
        const fallback = document.createElement("pre");
        fallback.textContent = op.data_set.sql_text || "(prázdné)";
        fallback.style.cssText = "background:#0a0f14;padding:12px;border:1px solid #2a3340;color:#cfd6df;font-family:monospace;font-size:12px;max-height:400px;overflow:auto;";
        editorHost.appendChild(fallback);
      }
    }

    _showAddOpForm(container, addBtn) {
      addBtn.disabled = true;
      addBtn.style.opacity = "0.5";

      const formWrap = document.createElement("div");
      formWrap.style.cssText = "display:flex;flex-direction:column;gap:10px;padding:14px;background:#0a1820;border:2px solid #3a8aa8;border-radius:4px;margin-top:6px;";

      const formTitle = document.createElement("div");
      formTitle.style.cssText = "font-size:12px;font-weight:600;color:#7ed4e8;";
      formTitle.textContent = "➕ Nová operace";
      formWrap.appendChild(formTitle);

      // Sprint B (17.5.2026 dop.): Mode toggle — inline new vs existing data_set
      // Marti-AI's "uniformita vítězí" doctrine z 11.5. — reuse > duplicate inline.
      const modeBar = document.createElement("div");
      modeBar.style.cssText = "display:flex;gap:4px;padding:4px;background:rgba(20,26,32,0.7);border:1px solid #2a3340;border-radius:3px;";
      let _opMode = "inline";  // "inline" | "existing"
      const _modeBtns = {};
      [
        { value: "inline",   label: "📝 Nový SQL primitiv" },
        { value: "existing", label: "📎 Reuse existing data_set" }
      ].forEach((opt) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = opt.label;
        b.style.cssText =
          "padding:4px 12px;border-radius:3px;border:1px solid;font-size:11px;cursor:pointer;flex:1;" +
          (opt.value === _opMode
            ? "background:#1f4858;border-color:#3a8aa8;color:#7ed4e8;font-weight:600;"
            : "background:transparent;border-color:#3a4754;color:#8a96a4;font-weight:400;");
        b.addEventListener("click", () => {
          _opMode = opt.value;
          // Update buttons styling
          Object.values(_modeBtns).forEach((bb) => {
            const isActive = bb.dataset.value === _opMode;
            bb.style.cssText =
              "padding:4px 12px;border-radius:3px;border:1px solid;font-size:11px;cursor:pointer;flex:1;" +
              (isActive
                ? "background:#1f4858;border-color:#3a8aa8;color:#7ed4e8;font-weight:600;"
                : "background:transparent;border-color:#3a4754;color:#8a96a4;font-weight:400;");
          });
          // Toggle sections
          if (inlineSection) inlineSection.style.display = (_opMode === "inline") ? "" : "none";
          if (existingSection) existingSection.style.display = (_opMode === "existing") ? "" : "none";
        });
        b.dataset.value = opt.value;
        _modeBtns[opt.value] = b;
        modeBar.appendChild(b);
      });
      formWrap.appendChild(modeBar);

      // Holders for sections — defined later, referenced in mode toggle handler
      let inlineSection = null;
      let existingSection = null;
      let existingPickerSelect = null;  // <select> with data_set rows

      // Op header inputs (grid)
      const opGrid = document.createElement("div");
      opGrid.style.cssText = "display:grid;grid-template-columns:130px 1fr 130px 1fr;gap:8px 12px;align-items:center;";

      const _ipt = (placeholder) => {
        const i = document.createElement("input");
        i.type = "text";
        i.placeholder = placeholder || "";
        i.style.cssText = "padding:5px 8px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;";
        return i;
      };
      const _sel = (options) => {
        const s = document.createElement("select");
        s.style.cssText = "padding:5px 8px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;cursor:pointer;";
        for (const opt of options) {
          const o = document.createElement("option");
          o.value = opt.value;
          o.textContent = opt.label;
          s.appendChild(o);
        }
        return s;
      };
      const _lbl = (text) => {
        const l = document.createElement("label");
        l.textContent = text;
        l.style.cssText = "color:#a8b4c2;font-size:11px;";
        return l;
      };

      // Krok 5.K-B5 (17.5.2026, Marti's "z variant_code mam instinktivni strach"):
      // drop variant_code UI input. Auto-gen v save flow ('default', 'default_2'...).
      // Backend keeps column pro runtime lookup (data_source_runner.py:103).
      const kindSelect = _sel(DDS_OPERATION_KINDS);
      const isDefaultCheck = document.createElement("input");
      isDefaultCheck.type = "checkbox";
      isDefaultCheck.style.cssText = "width:16px;height:16px;cursor:pointer;";
      const sortInput = _ipt("0");
      sortInput.type = "number";

      opGrid.appendChild(_lbl("Kind:"));
      opGrid.appendChild(kindSelect);
      opGrid.appendChild(_lbl("Default:"));
      opGrid.appendChild(isDefaultCheck);
      opGrid.appendChild(_lbl("Sort order:"));
      opGrid.appendChild(sortInput);

      formWrap.appendChild(opGrid);

      // Sprint B: Inline section wrap (default visible)
      inlineSection = document.createElement("div");
      inlineSection.style.cssText = "display:flex;flex-direction:column;gap:8px;";
      formWrap.appendChild(inlineSection);

      // Data set inline form
      const setTitle = document.createElement("div");
      setTitle.style.cssText = "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;text-transform:uppercase;margin-top:8px;padding-bottom:4px;border-bottom:1px solid #1f2630;";
      setTitle.textContent = "📄 Inline Data Set";
      inlineSection.appendChild(setTitle);

      const setGrid = document.createElement("div");
      setGrid.style.cssText = "display:grid;grid-template-columns:130px 1fr 130px 1fr;gap:8px 12px;align-items:center;";

      // Krok 5.K-B4 (Marti's "code matouci a navic"): drop Code input —
      // auto-generated v save: <source_code>_<variant_code>
      // Krok 5.M-D: optgroup dropdown z fetched fw.db_connection.
      const defaultConn = (this._dbConnections || []).find(c => c.is_active) || null;
      const dbConnSelect = _buildDbConnSelect(
        this._dbConnections || [],
        defaultConn ? defaultConn.id : null,
        {}
      );
      // Compact size pro inline form
      dbConnSelect.style.padding = "5px 8px";
      dbConnSelect.style.fontSize = "12px";
      const setDescInput = _ipt("(volitelný popis)");

      setGrid.appendChild(_lbl("DB connection:"));
      setGrid.appendChild(dbConnSelect);
      setGrid.appendChild(_lbl("Description:"));
      const descWrap = document.createElement("div");
      descWrap.style.gridColumn = "2 / 5";
      descWrap.appendChild(setDescInput);
      setGrid.appendChild(descWrap);

      inlineSection.appendChild(setGrid);

      // SQL editor (Ace)
      const sqlLabel = document.createElement("div");
      sqlLabel.style.cssText = "font-size:11px;color:#a8b4c2;margin-top:4px;";
      sqlLabel.textContent = "SQL text (parameters: :param_name):";
      inlineSection.appendChild(sqlLabel);

      const editorHost = document.createElement("div");
      inlineSection.appendChild(editorHost);

      let aceEd = null;
      if (typeof global.ErpRichEdit === "function") {
        aceEd = new global.ErpRichEdit(editorHost, {
          value: "",
          language: "sql",
          theme: "monokai",
          height: "200px",
          lineNumbers: true,
          onBlur: () => this._refreshParamHint(aceEd, paramHint),
        });
        this._editors.push(aceEd);
      } else {
        // Fallback textarea
        const ta = document.createElement("textarea");
        ta.style.cssText = "padding:8px;background:#0a0f14;border:1px solid #2a3340;color:#cfd6df;font-family:monospace;font-size:12px;width:100%;box-sizing:border-box;min-height:200px;";
        ta.placeholder = "SELECT ... FROM ... WHERE col = :param";
        editorHost.appendChild(ta);
        aceEd = { value: () => ta.value, setValue: (v) => { ta.value = v; }, destroy: () => {} };
      }

      // Param hint panel
      const paramHint = document.createElement("div");
      paramHint.style.cssText = "padding:6px 8px;background:#0a0f14;border:1px dashed #2a3340;color:#8a96a4;font-size:11px;font-style:italic;";
      paramHint.textContent = "Detected parameters: (none yet — zapiš `:param_name` v SQL)";
      inlineSection.appendChild(paramHint);

      // Sprint B: Existing data_set section (hidden by default)
      existingSection = document.createElement("div");
      existingSection.style.cssText = "display:none;flex-direction:column;gap:8px;";
      formWrap.appendChild(existingSection);

      const exTitle = document.createElement("div");
      exTitle.style.cssText = "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;text-transform:uppercase;margin-top:8px;padding-bottom:4px;border-bottom:1px solid #1f2630;";
      exTitle.textContent = "📎 Existing data_set (uniform reuse)";
      existingSection.appendChild(exTitle);

      // Sprint B++ (17.5.2026 odp., Marti's "tu vcerejsi komponentu"):
      // ErpCatalogPicker (Krok 14g-H+22) 1:1 pattern — modal picker s plnym
      // AG Grid, filter, sort, drilldown. Replace inline grid (cramped) +
      // <select> (too primitive) — proven Centrála 1 parita UX.

      this._existingSelectedDs = null;

      // Inline action bar: 🔗 Vybrat button + selected display + 🚫 Zrušit
      const exActionBar = document.createElement("div");
      exActionBar.style.cssText = "display:flex;gap:8px;align-items:center;";

      const exPickBtn = document.createElement("button");
      exPickBtn.type = "button";
      exPickBtn.innerHTML = '🔗 Vybrat existing data_set';
      exPickBtn.style.cssText = "padding:6px 14px;background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;";
      exActionBar.appendChild(exPickBtn);

      const exSelectedInfo = document.createElement("div");
      exSelectedInfo.style.cssText = "flex:1;font-size:11px;color:#8a96a4;font-style:italic;";
      exSelectedInfo.textContent = "(žádný data_set vybrán)";
      exActionBar.appendChild(exSelectedInfo);

      const exClearBtn = document.createElement("button");
      exClearBtn.type = "button";
      exClearBtn.innerHTML = '🚫 Zrušit výběr';
      exClearBtn.title = "Zrušit vybraný data_set";
      exClearBtn.style.cssText = "padding:5px 10px;background:transparent;border:1px solid #5a2828;color:#e57373;border-radius:3px;cursor:pointer;font-size:11px;display:none;";
      exActionBar.appendChild(exClearBtn);

      existingSection.appendChild(exActionBar);

      // Preview pod button (SQL preview + metadata pro selected)
      const exPreview = document.createElement("div");
      exPreview.style.cssText = "padding:8px;background:#0a0f14;border:1px dashed #2a3340;color:#8a96a4;font-size:11px;min-height:60px;";
      exPreview.innerHTML = "<em>Klikni 🔗 Vybrat → otevře se picker → vyber data_set → zobrazí se preview SQL + metadata.</em>";
      existingSection.appendChild(exPreview);

      const _exUpdateDisplay = (ds) => {
        if (!ds) {
          exSelectedInfo.textContent = "(žádný data_set vybrán)";
          exSelectedInfo.style.color = "#8a96a4";
          exSelectedInfo.style.fontStyle = "italic";
          exClearBtn.style.display = "none";
          exPreview.innerHTML = "<em>Klikni 🔗 Vybrat → otevře se picker → vyber data_set → zobrazí se preview SQL + metadata.</em>";
          return;
        }
        exSelectedInfo.innerHTML =
          '<span style="color:#7ed4e8;font-family:monospace;font-weight:600;">' + (ds.code || "(no code)") + '</span>' +
          '<span style="color:#6a7684;"> · id=' + ds.id + '</span>' +
          '<span style="color:#aaa;"> · ' + (ds.db_connection || "?") + '</span>';
        exSelectedInfo.style.fontStyle = "normal";
        exClearBtn.style.display = "";
        exPreview.innerHTML =
          '<div style="color:#cfd6df;font-weight:600;margin-bottom:4px;">' + (ds.code || "(no code)") + ' · id=' + ds.id + '</div>' +
          '<div style="color:#7ba8d4;font-size:11px;margin-bottom:4px;">' + (ds.db_connection_label || ds.db_connection || "?") + '</div>' +
          (ds.description ? '<div style="color:#aaa;font-style:italic;margin-bottom:4px;">' + ds.description + '</div>' : '') +
          '<pre style="margin:0;padding:6px;background:#000;color:#7ed4a8;font-family:monospace;font-size:11px;max-height:120px;overflow:auto;border-radius:3px;">' +
            (ds.sql_text_preview || "(no SQL)") +
            (ds.sql_text_length > 200 ? '\n... (' + (ds.sql_text_length - 200) + ' more chars)' : '') +
          '</pre>';
      };

      exClearBtn.addEventListener("click", () => {
        this._existingSelectedDs = null;
        _exUpdateDisplay(null);
      });

      exPickBtn.addEventListener("click", () => {
        if (typeof global.ErpCatalogPicker !== "function") {
          alert("ErpCatalogPicker není načtený (catalog_picker.js).");
          return;
        }
        const picker = new global.ErpCatalogPicker({
          title: "🔗 Vybrat existing data_set (SQL primitiv)",
          endpoint: "/api/v1/erp/design/data-set-list",
          listKey: "data_sets",
          labelField: "code",
          columns: [
            { headerName: "ID", field: "id", width: 70, sortable: true, pinned: "left", filter: "agNumberColumnFilter" },
            { headerName: "Code", field: "code", width: 220, sortable: true, filter: "agTextColumnFilter",
              cellStyle: { fontFamily: "monospace", color: "#7ed4e8" },
              valueFormatter: function(p) { return p.value || "(no code)"; } },
            { headerName: "DB", field: "db_connection", width: 130, sortable: true, filter: "agTextColumnFilter",
              cellStyle: { fontFamily: "monospace", color: "#aaa" } },
            { headerName: "Description", field: "description", flex: 1, minWidth: 200, filter: "agTextColumnFilter",
              cellStyle: { color: "#aaa", fontStyle: "italic" } },
            { headerName: "SQL preview", field: "sql_text_preview", flex: 2, minWidth: 280, filter: "agTextColumnFilter",
              cellStyle: { fontFamily: "monospace", fontSize: "11px", color: "#7ed4a8" },
              valueFormatter: function(p) {
                if (!p.value) return "(empty)";
                var s = String(p.value).replace(/\s+/g, " ").trim();
                return s.length > 150 ? s.substring(0, 150) + "…" : s;
              } },
            { headerName: "Used ×", field: "use_count", width: 90, sortable: true, type: "numericColumn", filter: "agNumberColumnFilter",
              cellStyle: function(p) {
                if (p.value > 0) return { color: "#6aa84f", fontWeight: "500" };
                return { color: "#888" };
              } },
            { headerName: "Status", field: "status", width: 110, sortable: true, filter: "agTextColumnFilter",
              cellStyle: function(p) {
                if (p.value === "active") return { color: "#6aa84f" };
                if (p.value === "archived") return { color: "#888" };
                return null;
              } }
          ],
          onSelect: (row) => {
            this._existingSelectedDs = row || null;
            _exUpdateDisplay(row);
          }
        });
        picker.open();
      });

      // Action buttons
      const btnRow = document.createElement("div");
      btnRow.style.cssText = "display:flex;justify-content:flex-end;gap:8px;margin-top:6px;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Zrušit";
      cancelBtn.style.cssText = "padding:5px 12px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;border-radius:3px;cursor:pointer;font-size:12px;";
      cancelBtn.addEventListener("click", () => {
        formWrap.remove();
        addBtn.disabled = false;
        addBtn.style.opacity = "1";
      });

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.innerHTML = '<span style="color:#5dbf5d;margin-right:4px;">✓</span>Přidat operaci';
      okBtn.style.cssText = "padding:5px 12px;background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;";
      okBtn.addEventListener("click", () => {
        // Sprint B: validate dle aktivního modu
        const newOp = {
          existing: false,
          variant_code: null,  // resolved v _onSaveClick (default/_2/_3 logic)
          operation_kind: kindSelect.value,
          is_default: isDefaultCheck.checked,
          sort_order: parseInt(sortInput.value, 10) || (this._opsState.length * 10),
        };

        if (_opMode === "existing") {
          // Sprint B+ (17.5.): grid selection state instead of <select>.
          const ds = this._existingSelectedDs;
          if (!ds || !ds.id) {
            if (typeof _showToast === "function") _showToast("Vyber data_set v gridu (klikni na řádek)", "error", 2500);
            return;
          }
          newOp.data_set_id = parseInt(ds.id, 10);
          // Plus kopie summary pro display v ops list (op.data_set objekt)
          newOp.data_set = {
            id: ds.id,
            code: ds.code,
            db_connection: ds.db_connection,
            db_connection_id: ds.db_connection_id,
            description: ds.description,
            sql_text: ds.sql_text_preview,  // truncated, full text loaded přes /data-set/{id}
          };
        } else {
          // Inline new data_set
          // Krok 5.K-B5: auto-gen variant_code v _onSaveClick (default/_2/_3 per kind)
          // Plus data_set.code resolved tam taky.
          // Krok 5.M-D: db_connection_id (FK) preferred. Value může být "legacy:<str>"
          // pokud fetch fail (fallback array), jinak int FK.
          const sqlText = aceEd.value();
          if (!sqlText.trim()) {
            if (typeof _showToast === "function") _showToast("SQL text je povinný", "error", 2500);
            return;
          }
          const dbVal = dbConnSelect.value;
          const dataSetEntry = {
            // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): kind dropped.
            code: null,  // resolved v _onSaveClick (source_code + kind + suffix)
            sql_text: sqlText,
            description: setDescInput.value.trim() || null,
          };
          if (dbVal.startsWith("legacy:")) {
            dataSetEntry.db_connection = dbVal.slice("legacy:".length);
          } else {
            dataSetEntry.db_connection_id = parseInt(dbVal, 10);
          }
          newOp.data_set = dataSetEntry;
        }

        this._opsState.push(newOp);
        this._render();
      });

      btnRow.appendChild(cancelBtn);
      btnRow.appendChild(okBtn);
      formWrap.appendChild(btnRow);

      container.appendChild(formWrap);
    }

    _showEditOpForm(rowEl, op, idx, editBtn) {
      // Krok 5.K-B3: edit existing op — pre-populated values + per-op PATCH save.
      // Marti's "ted je treba se k tomu vratit a editovat".
      // Render expand form pod row.
      editBtn.disabled = true;
      editBtn.style.opacity = "0.5";

      const formWrap = document.createElement("div");
      formWrap.style.cssText = "display:flex;flex-direction:column;gap:10px;padding:14px;background:#0a1820;border:2px solid #3a8aa8;border-radius:4px;margin-top:6px;";

      const formTitle = document.createElement("div");
      formTitle.style.cssText = "font-size:12px;font-weight:600;color:#7ed4e8;";
      formTitle.textContent = "✏ Editace operace #" + op.op_id + " + data_set #" + (op.data_set && op.data_set.id);
      formWrap.appendChild(formTitle);

      // Op header
      const opGrid = document.createElement("div");
      opGrid.style.cssText = "display:grid;grid-template-columns:130px 1fr 130px 1fr;gap:8px 12px;align-items:center;";

      const _ipt = (val, ph) => {
        const i = document.createElement("input");
        i.type = "text";
        i.value = val != null ? String(val) : "";
        i.placeholder = ph || "";
        i.style.cssText = "padding:5px 8px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;";
        return i;
      };
      const _sel = (options, val) => {
        const s = document.createElement("select");
        s.style.cssText = "padding:5px 8px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:12px;width:100%;box-sizing:border-box;cursor:pointer;";
        for (const opt of options) {
          const o = document.createElement("option");
          o.value = opt.value;
          o.textContent = opt.label;
          if (opt.value === val) o.selected = true;
          s.appendChild(o);
        }
        return s;
      };
      const _lbl = (text) => {
        const l = document.createElement("label");
        l.textContent = text;
        l.style.cssText = "color:#a8b4c2;font-size:11px;";
        return l;
      };

      // Krok 5.K-B5: drop variant_code input z edit form (Marti's strach).
      // Backend column keeps existing value — not editable v UI.
      const kindSelect = _sel(DDS_OPERATION_KINDS, op.operation_kind);
      const isDefaultCheck = document.createElement("input");
      isDefaultCheck.type = "checkbox";
      isDefaultCheck.checked = !!op.is_default;
      isDefaultCheck.style.cssText = "width:16px;height:16px;cursor:pointer;";
      const sortInput = _ipt(op.sort_order, "0");
      sortInput.type = "number";

      opGrid.appendChild(_lbl("Kind:"));
      opGrid.appendChild(kindSelect);
      opGrid.appendChild(_lbl("Default:"));
      opGrid.appendChild(isDefaultCheck);
      opGrid.appendChild(_lbl("Sort order:"));
      opGrid.appendChild(sortInput);
      formWrap.appendChild(opGrid);

      // Data set inline
      const setTitle = document.createElement("div");
      setTitle.style.cssText = "font-size:11px;font-weight:600;color:#a8b4c2;letter-spacing:0.05em;text-transform:uppercase;margin-top:8px;padding-bottom:4px;border-bottom:1px solid #1f2630;";
      setTitle.textContent = "📄 Data Set #" + (op.data_set && op.data_set.id);
      formWrap.appendChild(setTitle);

      const setGrid = document.createElement("div");
      setGrid.style.cssText = "display:grid;grid-template-columns:130px 1fr 130px 1fr;gap:8px 12px;align-items:center;";

      const ds = op.data_set || {};
      // data_set.code je immutable po insertu (Marti's "ID je svaty" tradition) — read-only display
      const setCodeDisplay = document.createElement("div");
      setCodeDisplay.style.cssText = "padding:5px 8px;color:#7ed4e8;font-family:monospace;font-size:12px;background:#0f1419;border:1px dashed #2a3340;border-radius:3px;";
      setCodeDisplay.textContent = ds.code || "(?)";

      // Krok 5.M-D: optgroup dropdown z fetched fw.db_connection.
      // Pre-select prefer FK (ds.db_connection_id), fallback default_db string (ds.db_connection).
      const dbConnSelect = _buildDbConnSelect(
        this._dbConnections || [],
        ds.db_connection_id != null ? ds.db_connection_id : null,
        { fallbackValue: ds.db_connection || "data_db" }
      );
      dbConnSelect.style.padding = "5px 8px";
      dbConnSelect.style.fontSize = "12px";
      const setDescInput = _ipt(ds.description, "(volitelný popis)");

      setGrid.appendChild(_lbl("Code (locked):"));
      setGrid.appendChild(setCodeDisplay);
      setGrid.appendChild(_lbl("DB connection:"));
      setGrid.appendChild(dbConnSelect);
      setGrid.appendChild(_lbl("Description:"));
      const descWrap = document.createElement("div");
      descWrap.style.gridColumn = "2 / 5";
      descWrap.appendChild(setDescInput);
      setGrid.appendChild(descWrap);
      formWrap.appendChild(setGrid);

      // SQL editor
      const sqlLabel = document.createElement("div");
      sqlLabel.style.cssText = "font-size:11px;color:#a8b4c2;margin-top:4px;";
      sqlLabel.textContent = "SQL text:";
      formWrap.appendChild(sqlLabel);

      const editorHost = document.createElement("div");
      formWrap.appendChild(editorHost);

      let aceEd = null;
      if (typeof global.ErpRichEdit === "function") {
        aceEd = new global.ErpRichEdit(editorHost, {
          value: ds.sql_text || "",
          language: "sql",
          theme: "monokai",
          height: "260px",
          lineNumbers: true,
          onBlur: () => this._refreshParamHint(aceEd, paramHint),
        });
        this._editors.push(aceEd);
      } else {
        const ta = document.createElement("textarea");
        ta.style.cssText = "padding:8px;background:#0a0f14;border:1px solid #2a3340;color:#cfd6df;font-family:monospace;font-size:12px;width:100%;box-sizing:border-box;min-height:260px;";
        ta.value = ds.sql_text || "";
        editorHost.appendChild(ta);
        aceEd = { value: () => ta.value, destroy: () => {} };
      }

      const paramHint = document.createElement("div");
      paramHint.style.cssText = "padding:6px 8px;background:#0a0f14;border:1px dashed #2a3340;color:#8a96a4;font-size:11px;font-style:italic;";
      formWrap.appendChild(paramHint);
      this._refreshParamHint(aceEd, paramHint);

      // Buttons
      const btnRow = document.createElement("div");
      btnRow.style.cssText = "display:flex;justify-content:flex-end;gap:8px;margin-top:6px;";

      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Zrušit";
      cancelBtn.style.cssText = "padding:5px 12px;background:#2a3340;border:1px solid #3a4754;color:#cfd6df;border-radius:3px;cursor:pointer;font-size:12px;";
      cancelBtn.addEventListener("click", () => {
        formWrap.remove();
        editBtn.disabled = false;
        editBtn.style.opacity = "1";
      });

      const okBtn = document.createElement("button");
      okBtn.type = "button";
      okBtn.innerHTML = '<span style="color:#5dbf5d;margin-right:4px;">✓</span>Uložit operaci';
      okBtn.style.cssText = "padding:5px 12px;background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;";
      okBtn.addEventListener("click", async () => {
        okBtn.disabled = true;
        okBtn.innerHTML = "⏳ Ukládám…";
        try {
          // Diff op header vs initial (Krok 5.K-B5: variant_code dropped z UI)
          const opPatchBody = {};
          if (kindSelect.value !== op.operation_kind) opPatchBody.operation_kind = kindSelect.value;
          if (isDefaultCheck.checked !== !!op.is_default) opPatchBody.is_default = isDefaultCheck.checked;
          const newSort = parseInt(sortInput.value, 10);
          if (!isNaN(newSort) && newSort !== op.sort_order) opPatchBody.sort_order = newSort;

          // Diff data_set vs initial
          // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): kind dropped.
          // Krok 5.M-D: db_connection_id (FK) preferred. Value parsing — int FK or "legacy:<str>".
          const setPatchBody = {};
          const newSql = aceEd.value();
          if (newSql !== (ds.sql_text || "")) setPatchBody.sql_text = newSql;
          const dbVal = dbConnSelect.value;
          if (dbVal.startsWith("legacy:")) {
            const legacyStr = dbVal.slice("legacy:".length);
            if (legacyStr !== (ds.db_connection || "")) setPatchBody.db_connection = legacyStr;
          } else {
            const newFk = parseInt(dbVal, 10);
            if (newFk !== (ds.db_connection_id || null)) setPatchBody.db_connection_id = newFk;
          }
          const newDesc = setDescInput.value.trim() || null;
          if (newDesc !== (ds.description || null)) setPatchBody.description = newDesc;

          // Validate — alespoň 1 změna
          if (Object.keys(opPatchBody).length === 0 && Object.keys(setPatchBody).length === 0) {
            if (typeof _showToast === "function") _showToast("Žádné změny k uložení", "info", 2000);
            okBtn.disabled = false;
            okBtn.innerHTML = '<span style="color:#5dbf5d;margin-right:4px;">✓</span>Uložit operaci';
            return;
          }

          // PATCH data_set if changed
          if (Object.keys(setPatchBody).length > 0) {
            const r1 = await fetch("/api/v1/erp/design/data-set/update/" + encodeURIComponent(ds.id), {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(setPatchBody),
            });
            const respData1 = await r1.json().catch(() => ({}));
            if (!r1.ok || !respData1.ok) throw new Error(respData1.error || ("HTTP " + r1.status + " data-set"));
          }

          // PATCH op if changed
          if (Object.keys(opPatchBody).length > 0) {
            const r2 = await fetch("/api/v1/erp/design/data-source-op/update/" + encodeURIComponent(op.op_id), {
              method: "PATCH", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(opPatchBody),
            });
            const respData2 = await r2.json().catch(() => ({}));
            if (!r2.ok || !respData2.ok) throw new Error(respData2.error || ("HTTP " + r2.status + " data-source-op"));
          }

          if (typeof _showToast === "function") {
            _showToast("Operace uložena (data_set #" + ds.id + " · op #" + op.op_id + ")", "success", 2500);
          }
          // Reload full spec → refresh display
          formWrap.remove();
          await this._fetchData();
        } catch (e) {
          console.error("[DesignDataSourceEditor] edit op save failed:", e);
          if (typeof _showToast === "function") {
            _showToast("Uložení selhalo: " + (e.message || e), "error", 4000);
          }
          okBtn.disabled = false;
          okBtn.innerHTML = '<span style="color:#5dbf5d;margin-right:4px;">✓</span>Uložit operaci';
        }
      });

      btnRow.appendChild(cancelBtn);
      btnRow.appendChild(okBtn);
      formWrap.appendChild(btnRow);

      // Insert after row
      rowEl.parentNode.insertBefore(formWrap, rowEl.nextSibling);
    }

    _refreshParamHint(aceEd, paramHintEl) {
      // Krok 5.K-C parameter auto-extract
      const sqlText = aceEd.value() || "";
      const matches = sqlText.match(/:[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
      const unique = Array.from(new Set(matches));
      if (unique.length === 0) {
        paramHintEl.textContent = "Detected parameters: (none — zapiš `:param_name` v SQL)";
        paramHintEl.style.color = "#8a96a4";
      } else {
        paramHintEl.innerHTML = "Detected parameters: <strong style=\"color:#7ed4e8;\">" + unique.join(", ") + "</strong>";
        paramHintEl.style.color = "#cfd6df";
      }
    }

    async _onSaveClick() {
      if (!this._isCreateMode) {
        // Krok 5.K-B3 edit mode + Sprint B+++ (17.5.2026 odp.): PATCH header
        // diff + add new ops (Marti's "Reuse picker save flow").
        // Existing ops byly editované přes inline expand (per-op PATCH calls
        // už persistovány). Nove ops z "+Pridat operaci" form se posilaji
        // přes POST /design/data-source/{id}/op-create.
        const srcInitial = (this._spec && this._spec.source) || {};
        const headerPatch = {};
        if (this._headerState.name !== (srcInitial.name || "")) headerPatch.name = this._headerState.name.trim();
        if ((this._headerState.description || "") !== (srcInitial.description || "")) headerPatch.description = this._headerState.description.trim() || null;
        if (this._headerState.refresh_type !== srcInitial.refresh_type) headerPatch.refresh_type = this._headerState.refresh_type;
        if (this._headerState.default_record_limit !== srcInitial.default_record_limit) headerPatch.default_record_limit = this._headerState.default_record_limit || 10000;

        // Sprint B+++: detect new ops přidané v edit mode (existing=false)
        const newOps = (this._opsState || []).filter(o => !o.existing);

        if (Object.keys(headerPatch).length === 0 && newOps.length === 0) {
          if (typeof _showToast === "function") _showToast("Žádné změny", "info", 2000);
          this._shell.close();
          return;
        }

        this._saveBtn.disabled = true;
        this._saveBtn.innerHTML = "⏳ Ukládám…";
        try {
          // 1) POST each new op (Sprint B+++ flow)
          if (newOps.length > 0) {
            // Auto-gen variant_code: 1st kind → null, 2nd → "default_2", atd.
            // Use existing ops kind counts as starting point.
            const kindCounts = {};
            for (const ex of (this._opsState || []).filter(o => o.existing)) {
              const k = ex.operation_kind;
              kindCounts[k] = (kindCounts[k] || 0) + 1;
            }
            for (const op of newOps) {
              const k = op.operation_kind;
              kindCounts[k] = (kindCounts[k] || 0) + 1;
              const variantCode = kindCounts[k] === 1 ? null : "default_" + kindCounts[k];
              const opBody = {
                operation_kind: k,
                variant_code: variantCode,
                is_default: !!op.is_default,
                sort_order: op.sort_order || 0,
                description: op.description || null,
              };
              if (op.data_set_id) {
                opBody.data_set_id = op.data_set_id;
              } else if (op.data_set && typeof op.data_set === "object") {
                opBody.data_set = Object.assign({}, op.data_set, { code: null });  // NULL doctrine
              } else {
                throw new Error("Op nemá data_set_id ani inline data_set");
              }
              const opR = await fetch(
                "/api/v1/erp/design/data-source/" + encodeURIComponent(this.dataSourceId) + "/op-create",
                {
                  method: "POST", credentials: "include",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(opBody),
                }
              );
              const opD = await opR.json().catch(() => ({}));
              if (!opR.ok || !opD.ok) throw new Error(opD.error || ("op-create HTTP " + opR.status));
            }
            if (typeof _showToast === "function") {
              _showToast("Přidáno " + newOps.length + " operací", "success", 2500);
            }
          }

          // 2) PATCH header pokud změny (existing flow)
          if (Object.keys(headerPatch).length > 0) {
            const r = await fetch("/api/v1/erp/design/fw-data-source/update/" + encodeURIComponent(this.dataSourceId), {
            method: "PATCH", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(headerPatch),
          });
          const respData = await r.json().catch(() => ({}));
          if (!r.ok || !respData.ok) throw new Error(respData.error || ("HTTP " + r.status));
          if (typeof _showToast === "function") {
            _showToast("Header uložen (" + respData.updated_fields.join(", ") + ")", "success", 2500);
          }
          if (typeof this.onComplete === "function") {
            try { this.onComplete(respData); } catch (e) {}
          }
          setTimeout(() => this._shell.close(), 600);
          }  // end if (headerPatch.length > 0)
          else if (newOps.length > 0) {
            // Pouze new ops bez header changes — close after success toast (uz nahore)
            setTimeout(() => {
              this._shell.close();
              if (typeof this.onComplete === "function") {
                try { this.onComplete({ok: true, new_ops_count: newOps.length}); } catch (e) {}
              }
            }, 600);
          }
        } catch (e) {
          console.error("[DesignDataSourceEditor] edit save failed:", e);
          if (typeof _showToast === "function") {
            _showToast("Uložení selhalo: " + (e.message || e), "error", 4000);
          }
          this._saveBtn.disabled = false;
          this._saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
        }
        return;
      }

      // Validate header
      const name = this._headerState.name.trim();
      if (!name) {
        if (typeof _showToast === "function") _showToast("Název je povinný", "error", 2500);
        return;
      }
      if (this._opsState.length === 0) {
        if (typeof _showToast === "function") _showToast("Datový zdroj musí mít alespoň 1 operaci", "error", 2500);
        return;
      }

      // Krok 5.K-B5+ (17.5.2026, Marti's "nech to v DB NULL, aby bylo videt
      // ze s nim nikde nepracujes"): code je NULL pro new entities. Backend
      // refactor migration → drop column postupně. Existing hardcoded data_sources
      // mají code historicky (Krok 11-E etc.) — to ponecháme až po refactoru.
      // variant_code zůstává auto-gen "default"/"default_2" (backend lookup).
      const newOps = this._opsState.filter(o => !o.existing);

      // Krok 5.K-B6 (Marti's "variant_code NULL allowed"): 1st op kind → null,
      // 2nd same kind → "default_2", 3rd → "default_3". Backend runtime lookup
      // má NULL fallback (data_source_runner.py — :variant='default' OR variant_code IS NULL).
      const kindCounts = {};
      const operations = newOps.map((op) => {
        const k = op.operation_kind;
        kindCounts[k] = (kindCounts[k] || 0) + 1;
        const variantCode = kindCounts[k] === 1 ? null : "default_" + kindCounts[k];
        // Sprint B: pokud op je "existing data_set reference" → send data_set_id only
        // (backend POST bulk čeká EITHER data_set:{...} dict OR data_set_id int).
        if (op.data_set_id) {
          return {
            variant_code: variantCode,
            operation_kind: k,
            is_default: op.is_default,
            sort_order: op.sort_order,
            data_set_id: op.data_set_id,
          };
        }
        return {
          variant_code: variantCode,
          operation_kind: k,
          is_default: op.is_default,
          sort_order: op.sort_order,
          data_set: Object.assign({}, op.data_set, {
            code: null,  // Marti's NULL doctrine — neviditelný v UI, neviditelný v DB
          }),
        };
      });

      const payload = {
        source: {
          code: null,  // Marti's NULL doctrine
          name: name,
          description: this._headerState.description.trim() || null,
          refresh_type: this._headerState.refresh_type,
          default_record_limit: this._headerState.default_record_limit || 10000,
        },
        operations: operations,
      };

      this._saveBtn.disabled = true;
      this._saveBtn.innerHTML = "⏳ Ukládám…";

      try {
        const r = await fetch("/api/v1/erp/design/data-source/full", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const respData = await r.json().catch(() => ({}));
        if (!r.ok || !respData.ok) {
          throw new Error(respData.error || ("HTTP " + r.status));
        }
        if (typeof _showToast === "function") {
          _showToast("Datový zdroj vytvořen (id=" + respData.data_source_id + ")", "success", 2500);
        }
        if (typeof this.onComplete === "function") {
          try { this.onComplete(respData); } catch (e) { console.warn("[DesignDataSourceEditor] onComplete failed:", e); }
        }
        setTimeout(() => this._shell.close(), 600);
      } catch (e) {
        console.error("[DesignDataSourceEditor] save failed:", e);
        if (typeof _showToast === "function") {
          _showToast("Uložení selhalo: " + (e.message || e), "error", 4000);
        }
        this._saveBtn.disabled = false;
        this._saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // Phase 38.4 Krok 14g Etapa F Krok 5.L-B (17.5.2026, Marti's "DataSets
  // soudeček chce vlastní editor"): standalone editor pro fw.data_set SQL
  // primitives. Bez ops (data_set je low-level — pouze SQL + metadata).
  //
  // Backend Krok 5.L-A endpointy:
  //   GET  /design/data-set/{id}            — single detail + use_count
  //   POST /design/data-set/create          — single create (code=NULL default)
  //   PATCH /design/data-set/update/{id}    — existing z Krok 5.K-B3
  //
  // Constructor: { dataSetId: int|null, onComplete?: fn }
  //   null = create new mode
  //   int  = edit existing mode
  // ══════════════════════════════════════════════════════════════════════

  // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): DDS_KIND_OPTIONS dropped
  // — Marti's "V tom SQL textu muze byt cokoli... Chceme ho na neco?". Kind
  // sloupec smazán z fw.data_set (DROP COLUMN). SQL text je truth source.


    global.DesignDataSourceEditor = DesignDataSourceEditor;
  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
