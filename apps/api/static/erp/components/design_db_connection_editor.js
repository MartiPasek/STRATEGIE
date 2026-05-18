/**
 * DesignDbConnectionEditor — extracted standalone JS module.
 *
 * Phase JS-3 (18.5.2026 ~22:50): extract z design_forms.js.
 * DB connection editor (Sprint D power-tool)
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

  class DesignDbConnectionEditor {
    constructor(opts) {
      this.opts = opts || {};
      this.connId = this.opts.connId || null;
      this.onComplete = this.opts.onComplete || null;
      this._spec = null;     // raw row z fw.db_connection
      this._state = null;    // editable state
      this._shell = null;
      this._isCreateMode = (this.connId == null);
    }

    async open() {
      const title = this._isCreateMode
        ? "➕ Nový DB connection"
        : ("🔌 DB Connection #" + this.connId);
      this._shell = _buildModalShell({ title: title, width: "780px" });
      document.body.appendChild(this._shell.overlay);

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

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

      if (this._isCreateMode) {
        if (typeof _showToast === "function") {
          _showToast("Create nový connection zatím není v MVP — Marti přidá v DBeaveru (Sprint D Phase 2).", "info", 4000);
        }
        this._shell.close();
        return;
      }

      // Fetch single connection — reuse list endpoint, filter v JS
      try {
        const r = await fetch("/api/v1/erp/system/db-connections?include_inactive=true", { credentials: "include" });
        if (!r.ok) throw new Error("HTTP " + r.status);
        const data = await r.json();
        if (!data.ok || !Array.isArray(data.connections)) throw new Error("malformed");
        const found = data.connections.find(c => c.id === this.connId);
        if (!found) throw new Error("Connection #" + this.connId + " nenalezen");
        this._spec = found;
        this._state = {
          label: found.label || "",
          description: found.description || "",
          default_db: found.default_db || "",
          host: found.host || "",
          port: found.port != null ? String(found.port) : "",
          login_name: found.login_name || "",
          scope_databases: JSON.stringify(found.scope_databases || [], null, 2),
          is_active: !!found.is_active,
          sort_order: found.sort_order != null ? String(found.sort_order) : "0",
        };
        this._render();
      } catch (e) {
        console.error("[DesignDbConnectionEditor] fetch failed:", e);
        this._shell.body.innerHTML = "";
        const err = document.createElement("div");
        err.style.cssText = "padding:24px;color:#e57373;font-size:13px;";
        err.textContent = "Načtení selhalo: " + (e.message || e);
        this._shell.body.appendChild(err);
      }
    }

    _render() {
      this._shell.body.innerHTML = "";
      const wrap = document.createElement("div");
      wrap.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:12px;";

      // Identity pill (immutable code + tenant + db_type)
      const idRow = document.createElement("div");
      idRow.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:8px 12px;background:#0f1419;border-radius:3px;border:1px solid #2a3340;";
      idRow.innerHTML =
        '<span style="color:#7ed4e8;font-family:monospace;font-size:12px;">🔒 ' + (this._spec.code || "?") + '</span>' +
        '<span style="color:#6a7684;font-size:11px;">· id=' + this._spec.id + '</span>' +
        '<span style="color:#aaa;font-size:11px;">· ' + (this._spec.tenant_code || "—") + '</span>' +
        '<span style="color:#aa66cc;font-family:monospace;font-size:11px;">· ' + (this._spec.db_type || "?") + '</span>';
      wrap.appendChild(idRow);

      const _lbl = (text) => {
        const l = document.createElement("label");
        l.textContent = text;
        l.style.cssText = "color:#a8b4c2;font-size:12px;";
        return l;
      };
      const _inputStyle = "padding:6px 10px;background:#0a0f14;border:1px solid #2a3340;color:#e8eef5;border-radius:3px;font-size:13px;width:100%;box-sizing:border-box;";

      const _ipt = (val, placeholder) => {
        const i = document.createElement("input");
        i.type = "text";
        i.value = val || "";
        i.placeholder = placeholder || "";
        i.style.cssText = _inputStyle;
        return i;
      };

      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:130px 1fr;gap:10px 12px;align-items:center;";

      const labelInput = _ipt(this._state.label, "Label v dropdown");
      labelInput.addEventListener("input", () => { this._state.label = labelInput.value; });
      grid.appendChild(_lbl("Label"));
      grid.appendChild(labelInput);

      const descInput = _ipt(this._state.description, "Krátký popis účelu");
      descInput.addEventListener("input", () => { this._state.description = descInput.value; });
      grid.appendChild(_lbl("Description"));
      grid.appendChild(descInput);

      const hostInput = _ipt(this._state.host, "192.168.30.11 nebo 10.200.188.12");
      hostInput.addEventListener("input", () => { this._state.host = hostInput.value; });
      grid.appendChild(_lbl("Host"));
      grid.appendChild(hostInput);

      const portInput = _ipt(this._state.port, "1433 (MSSQL) / 5432 (PostgreSQL)");
      portInput.type = "number";
      portInput.addEventListener("input", () => { this._state.port = portInput.value; });
      grid.appendChild(_lbl("Port"));
      grid.appendChild(portInput);

      const defaultDbInput = _ipt(this._state.default_db, "DB_EC, data_db, ...");
      defaultDbInput.style.fontFamily = "monospace";
      defaultDbInput.addEventListener("input", () => { this._state.default_db = defaultDbInput.value; });
      grid.appendChild(_lbl("Default DB"));
      grid.appendChild(defaultDbInput);

      const loginInput = _ipt(this._state.login_name, "Marti-AI");
      loginInput.style.fontFamily = "monospace";
      loginInput.addEventListener("input", () => { this._state.login_name = loginInput.value; });
      grid.appendChild(_lbl("Login (audit)"));
      grid.appendChild(loginInput);

      const sortInput = _ipt(this._state.sort_order, "10, 20, 30, ...");
      sortInput.type = "number";
      sortInput.addEventListener("input", () => { this._state.sort_order = sortInput.value; });
      grid.appendChild(_lbl("Sort order"));
      grid.appendChild(sortInput);

      // is_active checkbox
      const activeWrap = document.createElement("div");
      activeWrap.style.cssText = "display:flex;gap:8px;align-items:center;";
      const activeCheck = document.createElement("input");
      activeCheck.type = "checkbox";
      activeCheck.checked = !!this._state.is_active;
      activeCheck.style.cssText = "width:16px;height:16px;cursor:pointer;";
      activeCheck.addEventListener("change", () => { this._state.is_active = activeCheck.checked; });
      activeWrap.appendChild(activeCheck);
      const activeHint = document.createElement("span");
      activeHint.style.cssText = "color:#8a96a4;font-size:11px;";
      activeHint.textContent = "is_active = true → dropdown visible, false → 'zatím neaktivní'";
      activeWrap.appendChild(activeHint);
      grid.appendChild(_lbl("Aktivní"));
      grid.appendChild(activeWrap);

      wrap.appendChild(grid);

      // scope_databases (JSONB array) — textarea editor
      const scopeLabel = document.createElement("div");
      scopeLabel.style.cssText = "font-size:11px;color:#a8b4c2;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;margin-top:8px;";
      scopeLabel.textContent = "Scope databases (JSON array)";
      wrap.appendChild(scopeLabel);

      const scopeHint = document.createElement("div");
      scopeHint.style.cssText = "color:#8a96a4;font-size:11px;font-style:italic;margin-top:-4px;";
      scopeHint.textContent = "MSSQL cross-DB SELECT scope (např. [\"DB_EC\",\"DB_IS\",\"DB-Ceniky\"]). PostgreSQL: jen [\"data_db\"].";
      wrap.appendChild(scopeHint);

      const scopeTa = document.createElement("textarea");
      scopeTa.style.cssText = "padding:8px;background:#0a0f14;border:1px solid #2a3340;color:#cfd6df;font-family:monospace;font-size:11px;width:100%;box-sizing:border-box;min-height:120px;border-radius:3px;";
      scopeTa.value = this._state.scope_databases || "[]";
      scopeTa.addEventListener("input", () => { this._state.scope_databases = scopeTa.value; });
      wrap.appendChild(scopeTa);

      this._shell.body.appendChild(wrap);
    }

    async _onSaveClick() {
      // Validate scope_databases JSON
      let scopeParsed;
      try {
        scopeParsed = JSON.parse(this._state.scope_databases || "[]");
        if (!Array.isArray(scopeParsed)) throw new Error("musi byt array");
      } catch (e) {
        if (typeof _showToast === "function") _showToast("scope_databases musí být validní JSON array: " + e.message, "error", 4000);
        return;
      }

      // Diff vs initial
      const init = this._spec;
      const patch = {};
      if (this._state.label !== (init.label || "")) patch.label = this._state.label;
      if ((this._state.description || "") !== (init.description || "")) patch.description = this._state.description.trim() || null;
      if (this._state.host !== (init.host || "")) patch.host = this._state.host || null;
      if (this._state.port !== (init.port != null ? String(init.port) : "")) {
        patch.port = this._state.port ? parseInt(this._state.port, 10) : null;
      }
      if (this._state.default_db !== (init.default_db || "")) patch.default_db = this._state.default_db || null;
      if (this._state.login_name !== (init.login_name || "")) patch.login_name = this._state.login_name || null;
      if (this._state.sort_order !== String(init.sort_order || 0)) patch.sort_order = parseInt(this._state.sort_order, 10) || 0;
      if (this._state.is_active !== !!init.is_active) patch.is_active = this._state.is_active;
      // scope_databases — compare as JSON normalized
      const initScopeStr = JSON.stringify(init.scope_databases || []);
      const newScopeStr = JSON.stringify(scopeParsed);
      if (newScopeStr !== initScopeStr) patch.scope_databases = scopeParsed;

      if (Object.keys(patch).length === 0) {
        if (typeof _showToast === "function") _showToast("Žádné změny", "info", 2000);
        this._shell.close();
        return;
      }

      this._saveBtn.disabled = true;
      this._saveBtn.innerHTML = "⏳ Ukládám…";
      try {
        const r = await fetch("/api/v1/erp/design/db-connection/update/" + encodeURIComponent(this.connId), {
          method: "PATCH", credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(patch),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data.ok) throw new Error(data.error || ("HTTP " + r.status));
        if (typeof _showToast === "function") {
          _showToast("Connection uložen (" + data.updated_fields.join(", ") + ")", "success", 2500);
        }
        // Invalidate cache pro dropdown — Marti's "KDE TO CACHUJES?" doctrine
        if (typeof _DB_CONNECTIONS_CACHE !== "undefined") _DB_CONNECTIONS_CACHE = null;
        if (typeof this.onComplete === "function") {
          try { this.onComplete(data); } catch (e) {}
        }
        setTimeout(() => this._shell.close(), 600);
      } catch (e) {
        console.error("[DesignDbConnectionEditor] PATCH failed:", e);
        if (typeof _showToast === "function") {
          _showToast("Uložení selhalo: " + (e.message || e), "error", 4000);
        }
        this._saveBtn.disabled = false;
        this._saveBtn.innerHTML = '<span style="color:#5dbf5d;font-weight:700;margin-right:6px;">✓</span>Uložit';
      }
    }
  }


  global.DesignDbConnectionEditor = DesignDbConnectionEditor;
})(typeof window !== "undefined" ? window : this);
