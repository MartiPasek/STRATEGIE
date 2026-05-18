/**
 * DesignDataSetEditor — extracted standalone JS module.
 *
 * Phase JS-3 (18.5.2026 ~22:50): extract z design_forms.js.
 * DataSet SQL editor (Krok 5.L power-tool)
 *
 * Loaded AFTER design_form_helpers.js (which exports _erpDFH).
 * Imports utilities via global._erpDFH destructure.
 */
(function (global) {
  "use strict";

  const _DFH = global._erpDFH || {};
  const { _esc, _ensureToastContainer, _ensureToastStyles, _showToast, _markFormDirty } = _DFH;
  const { _dirtyForms, _loadUserOverrides, _saveUserOverride, OVERRIDES_LS_KEY, DESIGN_FIELD_PALETTE } = _DFH;
  const { _getTooltipEl, _showTooltip, _hideTooltip, _installDarkTooltips, _promptDarkDialog } = _DFH;
  const { _confirmDarkDialog, _buildModalShell, _buildDescriptionsPopup, _field, _memo } = _DFH;
  const { _dropdown, _readonlyInput, _openFieldSettingsPopup, _resolveColor, LABEL_OVERRIDES } = _DFH;
  const { HINT_OVERRIDES, _applyInitialColor, _applyInitialSectionOverrides, _reapplyOverridesForSection, _reapplyOverridesForField } = _DFH;
  const { _reapplyOverridesInDOM, _reapplyAllOverridesInDOM, _installFieldLabelRightClick, _resolveLabel, _resolveHint } = _DFH;
  const { _sectionKeyFromTitle, _sectionBuild, ENUM_ITEMS } = _DFH;

  class DesignDataSetEditor {
    constructor(opts) {
      this.opts = opts || {};
      this.dataSetId = this.opts.dataSetId || null;
      this.onComplete = this.opts.onComplete || null;
      this._spec = null;     // { data_set, use_count } z GET
      this._state = null;    // { sql_text, db_connection_id, db_connection, description } — kind dropped (Krok 5.L-D); db_connection legacy fallback (Krok 5.M-D)
      this._shell = null;
      this._aceEd = null;
      this._isCreateMode = (this.dataSetId == null);
      this._dbConnections = [];  // Krok 5.M-D: fetched at open()
    }

    async open() {
      const title = this._isCreateMode
        ? "➕ Nový data_set (SQL primitiv)"
        : ("📄 Data set #" + this.dataSetId);
      this._shell = _buildModalShell({
        title: title,
        width: "900px",
        onClose: () => this._cleanup(),
      });
      document.body.appendChild(this._shell.overlay);

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

      // Krok 5.M-D: pre-fetch db connections z DB (single source of truth)
      this._dbConnections = await _fetchDbConnections();

      if (this._isCreateMode) {
        this._spec = { data_set: null, use_count: 0 };
        // Default = first active connection (sort_order 10 = strategie_pg)
        const defaultConn = this._dbConnections.find(c => c.is_active) || null;
        this._state = {
          sql_text: "",
          db_connection_id: defaultConn ? defaultConn.id : null,
          db_connection: defaultConn ? defaultConn.default_db : "data_db",
          description: "",
        };
        this._render();
      } else {
        this._fetchData();
      }
    }

    _cleanup() {
      if (this._aceEd && typeof this._aceEd.destroy === "function") {
        try { this._aceEd.destroy(); } catch (e) {}
      }
      this._aceEd = null;
    }

    async _fetchData() {
      try {
        const r = await fetch(
          "/api/v1/erp/design/data-set/" + encodeURIComponent(this.dataSetId),
          { method: "GET", credentials: "include" }
        );
        if (!r.ok) {
          const eb = await r.json().catch(() => ({}));
          throw new Error(eb.error || ("HTTP " + r.status));
        }
        this._spec = await r.json();
        if (!this._spec || !this._spec.ok) throw new Error("Neplatná response");
        const ds = this._spec.data_set || {};
        // Krok 5.M-D: db_connection_id (FK) primary, db_connection (legacy string) fallback
        this._state = {
          sql_text: ds.sql_text || "",
          db_connection_id: ds.db_connection_id != null ? ds.db_connection_id : null,
          db_connection: ds.db_connection || "data_db",  // legacy semantic (dc.default_db)
          description: ds.description || "",
        };
        this._render();
      } catch (e) {
        console.error("[DesignDataSetEditor] _fetchData failed:", e);
        this._shell.body.innerHTML = "";
        const err = document.createElement("div");
        err.style.cssText = "padding:24px;color:#e57373;font-size:13px;";
        err.textContent = "Načtení selhalo: " + (e.message || e);
        this._shell.body.appendChild(err);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";
      this._cleanup();

      const wrap = document.createElement("div");
      wrap.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:14px;";

      // Edit mode: identity pill + use count
      if (!this._isCreateMode && this._spec && this._spec.data_set) {
        const ds = this._spec.data_set;
        const idRow = document.createElement("div");
        idRow.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap;";

        const pill = document.createElement("div");
        pill.style.cssText = "display:inline-flex;align-items:center;gap:6px;padding:5px 10px;background:#0a0f14;border:1px dashed #2a3340;border-radius:3px;color:#7ed4e8;font-family:monospace;font-size:12px;";
        pill.innerHTML = "🔒 <span>" + (ds.code || "(NULL)") + "</span>" +
          " <span style=\"color:#6a7684;\">· id=" + ds.id + "</span>";
        idRow.appendChild(pill);

        const useBadge = document.createElement("div");
        useBadge.style.cssText = "padding:4px 10px;border-radius:3px;font-size:11px;font-weight:600;" +
          (this._spec.use_count > 0
            ? "background:rgba(125,212,168,0.15);color:#7ed4a8;border:1px solid rgba(125,212,168,0.3);"
            : "background:#1a1f26;color:#6a7684;border:1px solid #2a3340;");
        useBadge.textContent = "🔗 použito v " + this._spec.use_count + " operacích";
        idRow.appendChild(useBadge);

        wrap.appendChild(idRow);
      }

      // Header section — db_connection + description
      // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): Kind dropdown dropped.
      const sec = document.createElement("div");
      sec.style.cssText = "display:flex;flex-direction:column;gap:10px;padding:12px;background:#0f1419;border:1px solid #2a3340;border-radius:4px;";

      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px 12px;align-items:center;";

      const _lbl = (text) => {
        const l = document.createElement("label");
        l.textContent = text;
        l.style.cssText = "color:#a8b4c2;font-size:12px;";
        return l;
      };
      const _inputStyle = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;";

      // DB connection dropdown — Krok 5.M-D: optgroup z fetched fw.db_connection
      const dbSelect = _buildDbConnSelect(
        this._dbConnections,
        this._state.db_connection_id,
        { fallbackValue: this._state.db_connection }
      );
      dbSelect.addEventListener("change", () => {
        const v = dbSelect.value;
        if (v.startsWith("legacy:")) {
          this._state.db_connection_id = null;
          this._state.db_connection = v.slice("legacy:".length);
        } else {
          this._state.db_connection_id = parseInt(v, 10);
          // Update legacy fallback z connection row pro consistency
          const c = this._dbConnections.find(x => String(x.id) === v);
          this._state.db_connection = c ? c.default_db : this._state.db_connection;
        }
      });
      grid.appendChild(_lbl("DB connection"));
      grid.appendChild(dbSelect);

      // Description input
      const descInput = document.createElement("input");
      descInput.type = "text";
      descInput.value = this._state.description || "";
      descInput.placeholder = "Krátký popis účelu primitive";
      descInput.style.cssText = _inputStyle;
      descInput.addEventListener("input", () => { this._state.description = descInput.value; });
      grid.appendChild(_lbl("Popis"));
      grid.appendChild(descInput);

      sec.appendChild(grid);
      wrap.appendChild(sec);

      // SQL editor
      const sqlLabel = document.createElement("div");
      sqlLabel.style.cssText = "font-size:11px;color:#a8b4c2;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;";
      sqlLabel.textContent = "📝 SQL TEXT (parameters: :param_name)";
      wrap.appendChild(sqlLabel);

      const editorHost = document.createElement("div");
      wrap.appendChild(editorHost);

      if (typeof global.ErpRichEdit === "function") {
        this._aceEd = new global.ErpRichEdit(editorHost, {
          value: this._state.sql_text || "",
          language: "sql",
          theme: "monokai",
          height: "320px",
          lineNumbers: true,
          onChange: (val) => { this._state.sql_text = val; },
          onBlur: () => this._refreshParamHint(),
        });
      } else {
        const ta = document.createElement("textarea");
        ta.style.cssText = "padding:8px;background:#0a0f14;border:1px solid #2a3340;color:#cfd6df;font-family:monospace;font-size:12px;width:100%;box-sizing:border-box;min-height:320px;";
        ta.value = this._state.sql_text || "";
        ta.addEventListener("input", () => { this._state.sql_text = ta.value; });
        editorHost.appendChild(ta);
        this._aceEd = { value: () => ta.value, destroy: () => {} };
      }

      this._paramHint = document.createElement("div");
      this._paramHint.style.cssText = "padding:6px 8px;background:#0a0f14;border:1px dashed #2a3340;color:#8a96a4;font-size:11px;font-style:italic;";
      wrap.appendChild(this._paramHint);
      this._refreshParamHint();

      // Sprint C (17.5.2026 dop.): ▶ Test SQL button — ad-hoc execute SQL
      // s LIMIT 10 preview. Marti's "Kristý/Jirka chce vidět co spustila".
      const testBar = document.createElement("div");
      testBar.style.cssText = "display:flex;gap:8px;align-items:center;margin-top:4px;";

      const testBtn = document.createElement("button");
      testBtn.type = "button";
      testBtn.innerHTML = '<span style="color:#7ed4a8;font-weight:700;margin-right:4px;">▶</span>Test SQL (LIMIT 10)';
      testBtn.style.cssText = "padding:6px 14px;background:#1f4858;border:1px solid #3a8aa8;color:#7ed4e8;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;";
      testBtn.title = "Spustí draft SQL proti vybranému DB connection (jen SELECT, LIMIT 10).";

      const testHint = document.createElement("span");
      testHint.style.cssText = "color:#8a96a4;font-size:11px;font-style:italic;";
      testHint.textContent = "Tip: použij :limit parameter pro vlastní LIMIT v SQL.";
      testBar.appendChild(testBtn);
      testBar.appendChild(testHint);
      wrap.appendChild(testBar);

      // Test result panel (initially empty)
      this._testResult = document.createElement("div");
      this._testResult.style.cssText = "display:none;border:1px solid #2a3340;border-radius:3px;background:#0a0f14;padding:8px;overflow:auto;max-height:280px;";
      wrap.appendChild(this._testResult);

      testBtn.addEventListener("click", async () => {
        const sql = this._state.sql_text || "";
        if (!sql.trim()) {
          if (typeof _showToast === "function") _showToast("SQL text je prázdný", "error", 2500);
          return;
        }
        if (this._state.db_connection_id == null) {
          if (typeof _showToast === "function") _showToast("Vyber DB connection PŘED testem", "error", 2500);
          return;
        }
        testBtn.disabled = true;
        const origText = testBtn.innerHTML;
        testBtn.innerHTML = '<span style="margin-right:4px;">⏳</span>Spouštím…';
        this._testResult.style.display = "block";
        this._testResult.innerHTML = '<div style="color:#8a96a4;font-size:11px;font-style:italic;padding:8px;">⏳ Spouštím SQL test (LIMIT 10)…</div>';
        try {
          const r = await fetch("/api/v1/erp/design/data-set/test", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              sql_text: sql,
              db_connection_id: this._state.db_connection_id,
              limit: 10,
            }),
          });
          const data = await r.json().catch(() => ({}));
          if (!r.ok || !data.ok) {
            this._testResult.innerHTML =
              '<div style="color:#e57373;font-size:12px;font-weight:600;margin-bottom:6px;">❌ Test failed</div>' +
              '<pre style="margin:0;padding:8px;background:#000;color:#ffaaaa;font-family:monospace;font-size:11px;border-radius:3px;white-space:pre-wrap;">' +
              (data.error || ("HTTP " + r.status)) +
              '</pre>';
            return;
          }
          // Success — render result table
          const rows = data.rows || [];
          const cols = data.columns || [];
          const header =
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
            '<div style="color:#7ed4a8;font-size:12px;font-weight:600;">✓ Test OK · ' + data.row_count + ' řádků · ' + data.execution_ms + ' ms</div>' +
            '<div style="color:#8a96a4;font-size:11px;">' + (data.db_connection.label || data.db_connection.code) + '</div>' +
            '</div>';
          if (rows.length === 0) {
            this._testResult.innerHTML = header +
              '<div style="padding:12px;text-align:center;color:#8a96a4;font-style:italic;">(prázdný resultset — 0 řádků)</div>';
            return;
          }
          // Compact HTML table
          let tableHtml = '<table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:11px;">';
          tableHtml += '<thead><tr style="background:#1a1f26;">';
          for (const c of cols) {
            tableHtml += '<th style="padding:4px 8px;border:1px solid #2a3340;color:#7ba8d4;text-align:left;font-weight:600;">' +
              String(c).replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m])) + '</th>';
          }
          tableHtml += '</tr></thead><tbody>';
          for (const row of rows) {
            tableHtml += '<tr>';
            for (const c of cols) {
              const v = row[c];
              const str = v == null ? '<em style="color:#666;">NULL</em>' :
                String(v).replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m]));
              tableHtml += '<td style="padding:3px 8px;border:1px solid #2a3340;color:#cfd6df;vertical-align:top;">' + str + '</td>';
            }
            tableHtml += '</tr>';
          }
          tableHtml += '</tbody></table>';
          this._testResult.innerHTML = header + tableHtml;
        } catch (e) {
          this._testResult.innerHTML =
            '<div style="color:#e57373;font-size:12px;padding:8px;">❌ Test failed: ' +
            String(e.message || e).replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m])) +
            '</div>';
        } finally {
          testBtn.disabled = false;
          testBtn.innerHTML = origText;
        }
      });

      this._shell.body.appendChild(wrap);
    }

    _refreshParamHint() {
      if (!this._paramHint) return;
      const sql = this._state.sql_text || "";
      const matches = sql.match(/:[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
      const unique = Array.from(new Set(matches));
      if (unique.length === 0) {
        this._paramHint.textContent = "Detected parameters: (none — zapiš `:param_name` v SQL)";
        this._paramHint.style.color = "#8a96a4";
      } else {
        this._paramHint.innerHTML = "Detected parameters: <strong style=\"color:#7ed4e8;\">" + unique.join(", ") + "</strong>";
        this._paramHint.style.color = "#cfd6df";
      }
    }

    async _onSaveClick() {
      // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): kind dropped.
      const sqlText = this._state.sql_text || "";
      if (!sqlText.trim()) {
        if (typeof _showToast === "function") _showToast("SQL text je povinný", "error", 2500);
        return;
      }

      this._saveBtn.disabled = true;
      this._saveBtn.innerHTML = "⏳ Ukládám…";

      try {
        if (this._isCreateMode) {
          // POST create — Krok 5.M-D: db_connection_id (FK) preferred
          const body = {
            code: null,  // Marti's NULL doctrine
            sql_text: sqlText,
            description: this._state.description.trim() || null,
          };
          if (this._state.db_connection_id != null) {
            body.db_connection_id = this._state.db_connection_id;
          } else {
            body.db_connection = this._state.db_connection;  // legacy fallback
          }
          const r = await fetch("/api/v1/erp/design/data-set/create", {
            method: "POST", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          const respData = await r.json().catch(() => ({}));
          if (!r.ok || !respData.ok) throw new Error(respData.error || ("HTTP " + r.status));
          if (typeof _showToast === "function") {
            _showToast("Data set vytvořen (id=" + respData.data_set_id + ")", "success", 2500);
          }
          if (typeof this.onComplete === "function") {
            try { this.onComplete(respData); } catch (e) {}
          }
          setTimeout(() => this._shell.close(), 600);
        } else {
          // PATCH edit
          // Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026): kind diff dropped.
          // Krok 5.M-D: db_connection_id (FK) preferred diff.
          const initialDs = (this._spec && this._spec.data_set) || {};
          const patch = {};
          if (this._state.sql_text !== (initialDs.sql_text || "")) patch.sql_text = this._state.sql_text;
          // FK diff (preferred). Legacy string fallback only if FK unset.
          if (this._state.db_connection_id != null) {
            if (this._state.db_connection_id !== (initialDs.db_connection_id || null)) {
              patch.db_connection_id = this._state.db_connection_id;
            }
          } else if (this._state.db_connection !== (initialDs.db_connection || "")) {
            patch.db_connection = this._state.db_connection;  // legacy
          }
          const newDesc = this._state.description.trim() || null;
          if (newDesc !== (initialDs.description || null)) patch.description = newDesc;

          if (Object.keys(patch).length === 0) {
            if (typeof _showToast === "function") _showToast("Žádné změny", "info", 2000);
            this._shell.close();
            return;
          }

          const r = await fetch("/api/v1/erp/design/data-set/update/" + encodeURIComponent(this.dataSetId), {
            method: "PATCH", credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(patch),
          });
          const respData = await r.json().catch(() => ({}));
          if (!r.ok || !respData.ok) throw new Error(respData.error || ("HTTP " + r.status));
          if (typeof _showToast === "function") {
            _showToast("Data set uložen (" + respData.updated_fields.join(", ") + ")", "success", 2500);
          }
          if (typeof this.onComplete === "function") {
            try { this.onComplete(respData); } catch (e) {}
          }
          setTimeout(() => this._shell.close(), 600);
        }
      } catch (e) {
        console.error("[DesignDataSetEditor] save failed:", e);
        if (typeof _showToast === "function") {
          _showToast("Uložení selhalo: " + (e.message || e), "error", 4000);
        }
        this._saveBtn.disabled = false;
        this._saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      }
    }
  }

  // Export
  // ────────────────────────────────────────────────────────────────────

  // ══════════════════════════════════════════════════════════════════════
  // Phase 38.4 Krok 14g Etapa F Sprint D (17.5.2026 dop., Marti's "Kristý/
  // Jirka z UI"): DesignDbConnectionEditor — form pro create/edit
  // fw.db_connection rows (label, description, scope, atd.).
  //
  // Constructor: { connId: int|null, onComplete?: fn }
  //   null = create mode (TODO: bude added per use case, MVP edit-only)
  //   int  = edit existing
  // ══════════════════════════════════════════════════════════════════════

  global.DesignDataSetEditor = DesignDataSetEditor;
})(typeof window !== "undefined" ? window : this);
