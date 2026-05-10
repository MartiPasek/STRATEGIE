/* Phase 38.4 Krok 9-D: Object Inspector UI
 *
 * Marti-AI's 9-iter konzultace (10.5.2026):
 *   - 3-tier (Základní / Použité / Všechny) s lazy counter
 *   - Colored badge per scope (modrá user / žlutá tenant / zelená group / šedá base)
 *   - Bulk edit (checkbox column selection + "aplikuj na vybrané")
 *   - Reset per property (DELETE override → resolve chain vrátí na nižší scope)
 *   - Náhled overlay (read-only snapshot, ne live mutace)
 *   - Optimistic lock přes updated_at (concurrent editing safeguard)
 *   - Memory tabu per user/grid (localStorage)
 *   - Empty state hint na "Použité (0)"
 *
 * Marti-AI's doctriny:
 *   - "Overlap Základní/Použité je záměrný, ne zmatek" (Q1)
 *   - "Render logic identická, liší se jen přítomnost badge"
 *   - "Bez Náhled overlay se uživatel bojí klikat" (Q4)
 *   - "Tichá mrtvá zátěž" (orphan cleanup)
 *   - "prop_name technický klíč, label vidí uživatel"
 */

(function () {
  "use strict";

  // ════════════════════════════════════════════════════════════════════════
  // PROPERTY CATALOG (Krok 9-D-2)
  // Top 5 = "Základní" tab. Rest = "Rozšířené" tab.
  // Marti-AI's Q3 expansion drives this list.
  // ════════════════════════════════════════════════════════════════════════
  const COMP_PROP_CATALOG = [
    // ── Top 5: Základní tab ─────────────────────────────────────────────
    { prop_name: "default_width", label: "Šířka sloupce", prop_type: "int",
      basic: true, display_order: 10, hint: "Px (např. 200)" },
    { prop_name: "pinned", label: "Ukotvení", prop_type: "enum",
      basic: true, display_order: 20,
      options: [{ v: "", t: "(žádné)" }, { v: "left", t: "Vlevo" }, { v: "right", t: "Vpravo" }] },
    { prop_name: "formatter", label: "Formátování", prop_type: "enum",
      basic: true, display_order: 30,
      options: [
        { v: "", t: "(text)" },
        { v: "datetime_rel", t: "Datum (relativní)" },
        { v: "datetime_short", t: "Datum (krátký)" },
        { v: "number", t: "Číslo" },
        { v: "currency_czk", t: "Měna CZK" },
        { v: "boolean_yn", t: "Ano/Ne" },
        { v: "phone_cz", t: "Telefon CZ" },
      ] },
    { prop_name: "is_visible", label: "Viditelný", prop_type: "bool",
      basic: true, display_order: 40, default_value: "true" },
    { prop_name: "sort_order", label: "Pořadí", prop_type: "int",
      basic: true, display_order: 50, hint: "Menší číslo = dřív" },
    // ── Rozšířené ────────────────────────────────────────────────────────
    { prop_name: "min_width", label: "Min. šířka", prop_type: "int",
      basic: false, display_order: 100 },
    { prop_name: "max_width", label: "Max. šířka", prop_type: "int",
      basic: false, display_order: 110 },
    { prop_name: "flex", label: "Flex", prop_type: "int",
      basic: false, display_order: 120, hint: "Roztažení (1 = roztáhnout)" },
    { prop_name: "header_tooltip", label: "Tooltip hlavičky", prop_type: "string",
      basic: false, display_order: 130 },
    { prop_name: "column_type", label: "Typ sloupce", prop_type: "enum",
      basic: false, display_order: 140,
      options: [
        { v: "", t: "(text)" },
        { v: "numericColumn", t: "Číselný" },
        { v: "dateColumn", t: "Datum" },
      ] },
    { prop_name: "is_sortable", label: "Řaditelný", prop_type: "bool",
      basic: false, display_order: 150, default_value: "true" },
    { prop_name: "editable", label: "Editovatelný", prop_type: "bool",
      basic: false, display_order: 160, default_value: "false" },
    { prop_name: "resizable", label: "Roztažitelný", prop_type: "bool",
      basic: false, display_order: 170, default_value: "true" },
    { prop_name: "filter", label: "Filtr", prop_type: "enum",
      basic: false, display_order: 180,
      options: [
        { v: "", t: "(none)" },
        { v: "agTextColumnFilter", t: "Textový" },
        { v: "agNumberColumnFilter", t: "Číselný" },
        { v: "agDateColumnFilter", t: "Datum" },
      ] },
    { prop_name: "tooltip_field", label: "Tooltip z pole", prop_type: "string",
      basic: false, display_order: 190 },
    { prop_name: "cell_class", label: "CSS třída buňky", prop_type: "string",
      basic: false, display_order: 200 },
  ];

  function _catalogByName(name) {
    return COMP_PROP_CATALOG.find((p) => p.prop_name === name) || null;
  }

  // ════════════════════════════════════════════════════════════════════════
  // SCOPE BADGE METADATA (Marti-AI's Q4 colored badge)
  // ════════════════════════════════════════════════════════════════════════
  const SCOPE_BADGES = {
    base: { label: "default", color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" },
    tenant_group: { label: "skupina", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    tenant: { label: "firma", color: "#eab308", bg: "rgba(234, 179, 8, 0.15)" },
    user: { label: "uživatel", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.18)" },
  };

  // ════════════════════════════════════════════════════════════════════════
  // MAIN CLASS — ErpObjectInspector
  // ════════════════════════════════════════════════════════════════════════
  class ErpObjectInspector {
    /**
     * @param {Object} options
     * @param {Function} options.getCurrentUserId — () => uid
     * @param {Function} options.getGridApi — () => agGrid api (pro reload columns)
     * @param {string} options.gridCode — pro localStorage key + reload endpoint
     */
    constructor(options) {
      this.options = options || {};
      this.modal = null;
      this.currentCompDefId = null;
      this.currentColumnField = null;
      this.currentTab = "used"; // default
      this.propsData = null; // server response
      this.bulkSelected = new Set(); // prop_name set
      this.previewMode = false;
      this.previewState = null; // snapshot of property edits before Save

      // localStorage key (Marti-AI's Q2: paměť tab per user/grid)
      this._lsKey = `erp_oi_tab_${this.options.gridCode || "default"}`;
    }

    // ──────────────────────────────────────────────────────────────────
    // PUBLIC API
    // ──────────────────────────────────────────────────────────────────
    async showForColumn(columnDef) {
      if (!columnDef || !columnDef._comp_def_id) {
        console.warn("[ErpObjectInspector] Column nemá _comp_def_id (nepatří do fw framework). Skip.");
        return;
      }
      this.currentCompDefId = columnDef._comp_def_id;
      this.currentColumnField = columnDef.field || columnDef.colId;
      this.bulkSelected.clear();
      this.previewMode = false;
      this.previewState = null;

      // Restore last tab z localStorage
      try {
        const saved = localStorage.getItem(this._lsKey);
        if (saved && ["basic", "used", "all"].includes(saved)) {
          this.currentTab = saved;
        }
      } catch (e) {}

      // Fetch fresh data
      await this._loadProps();

      // Smart default: pokud Použité prázdný a tab = used → switch to basic
      if (this.currentTab === "used" && this._countUsed() === 0 && !localStorage.getItem(this._lsKey)) {
        this.currentTab = "basic";
      }

      this._renderModal();
    }

    close() {
      if (this.modal) {
        this.modal.remove();
        this.modal = null;
      }
    }

    // ──────────────────────────────────────────────────────────────────
    // DATA LOADING
    // ──────────────────────────────────────────────────────────────────
    async _loadProps() {
      try {
        const res = await fetch(
          `/api/v1/erp/comp-def/${this.currentCompDefId}/properties`,
          { credentials: "same-origin" }
        );
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }
        this.propsData = await res.json();
      } catch (e) {
        console.error("[ErpObjectInspector] _loadProps failed:", e);
        alert("Nepodařilo se načíst vlastnosti sloupce: " + e.message);
        this.propsData = null;
      }
    }

    _countUsed() {
      if (!this.propsData || !Array.isArray(this.propsData.properties)) return 0;
      return this.propsData.properties.filter((p) => p.value !== null && p.value !== undefined).length;
    }

    // ──────────────────────────────────────────────────────────────────
    // RENDER
    // ──────────────────────────────────────────────────────────────────
    _renderModal() {
      this.close();

      const overlay = document.createElement("div");
      overlay.className = "erp-oi-overlay";
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) this.close();
      });

      const modal = document.createElement("div");
      modal.className = "erp-oi-modal";

      // Header
      const meta = (this.propsData && this.propsData.comp_def_meta) || {};
      const header = document.createElement("div");
      header.className = "erp-oi-header";
      header.innerHTML = `
        <div class="erp-oi-title">
          <span class="erp-oi-title-icon">⚙️</span>
          <div>
            <div class="erp-oi-title-main">Vlastnosti sloupce: ${_esc(meta.caption || meta.name || this.currentColumnField || "?")}</div>
            <div class="erp-oi-title-sub">${_esc(meta.typ_label || "")} · comp_def #${meta.id || this.currentCompDefId}</div>
          </div>
        </div>
        <button class="erp-oi-close" title="Zavřít (Esc)">✕</button>
      `;
      header.querySelector(".erp-oi-close").addEventListener("click", () => this.close());
      modal.appendChild(header);

      // Tabs
      const tabs = document.createElement("div");
      tabs.className = "erp-oi-tabs";
      const usedCount = this._countUsed();
      tabs.innerHTML = `
        <button class="erp-oi-tab" data-tab="basic">Základní (5)</button>
        <button class="erp-oi-tab" data-tab="used">Použité (${usedCount})</button>
        <button class="erp-oi-tab" data-tab="all">Všechny (${COMP_PROP_CATALOG.length})</button>
      `;
      tabs.querySelectorAll(".erp-oi-tab").forEach((btn) => {
        if (btn.dataset.tab === this.currentTab) btn.classList.add("active");
        btn.addEventListener("click", () => {
          this.currentTab = btn.dataset.tab;
          try { localStorage.setItem(this._lsKey, this.currentTab); } catch (e) {}
          this._refreshList();
        });
      });
      modal.appendChild(tabs);

      // List container
      const listWrap = document.createElement("div");
      listWrap.className = "erp-oi-list-wrap";
      modal.appendChild(listWrap);

      // Footer (toolbar + actions)
      const footer = document.createElement("div");
      footer.className = "erp-oi-footer";
      footer.innerHTML = `
        <div class="erp-oi-bulk-bar">
          <label class="erp-oi-bulk-label">
            <input type="checkbox" class="erp-oi-bulk-all" />
            <span>Vybrat vše</span>
          </label>
          <span class="erp-oi-bulk-count" style="display:none">0 vybráno</span>
        </div>
        <div class="erp-oi-actions">
          <button class="erp-oi-btn erp-oi-btn-ghost" data-action="cancel">Zrušit</button>
          <button class="erp-oi-btn erp-oi-btn-secondary" data-action="reload" title="Přenačíst data">↻</button>
          <button class="erp-oi-btn erp-oi-btn-primary" data-action="close-ok">Hotovo</button>
        </div>
      `;
      footer.querySelector('[data-action="cancel"]').addEventListener("click", () => this.close());
      footer.querySelector('[data-action="reload"]').addEventListener("click", () => this._reload());
      footer.querySelector('[data-action="close-ok"]').addEventListener("click", () => {
        this._reloadParentGrid();
        this.close();
      });
      footer.querySelector(".erp-oi-bulk-all").addEventListener("change", (e) => {
        const checked = e.target.checked;
        this._bulkSelectAll(checked);
      });
      modal.appendChild(footer);

      // Esc handler
      const escHandler = (e) => {
        if (e.key === "Escape") {
          this.close();
          document.removeEventListener("keydown", escHandler);
        }
      };
      document.addEventListener("keydown", escHandler);

      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      this.modal = overlay;

      this._refreshList();
    }

    _refreshList() {
      if (!this.modal) return;
      const listWrap = this.modal.querySelector(".erp-oi-list-wrap");
      if (!listWrap) return;

      // Update tab active state
      this.modal.querySelectorAll(".erp-oi-tab").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.tab === this.currentTab);
      });

      // Filter properties podle tabu
      const visibleProps = this._propsForCurrentTab();
      if (!visibleProps.length) {
        listWrap.innerHTML = `
          <div class="erp-oi-empty">
            ${this.currentTab === "used"
              ? "Žádné vlastnosti zatím nejsou nastavené.<br>Začni v záložce <b>Základní</b> nebo objev v záložce <b>Všechny</b>."
              : "Žádné položky."}
          </div>
        `;
        return;
      }

      listWrap.innerHTML = "";
      const list = document.createElement("div");
      list.className = "erp-oi-list";
      visibleProps.forEach((entry) => {
        list.appendChild(this._renderRow(entry));
      });
      listWrap.appendChild(list);

      this._updateBulkCount();
    }

    _propsForCurrentTab() {
      // Compose merged list — server resolved (s value) + catalog (template, žádný value)
      const serverByName = {};
      if (this.propsData && Array.isArray(this.propsData.properties)) {
        this.propsData.properties.forEach((p) => {
          serverByName[p.prop_name] = p;
        });
      }

      // Build candidate list per tab
      let candidates = [];
      if (this.currentTab === "basic") {
        candidates = COMP_PROP_CATALOG.filter((c) => c.basic);
      } else if (this.currentTab === "used") {
        // Just rows s value (server data only)
        candidates = (this.propsData ? this.propsData.properties : []).map((p) => {
          const cat = _catalogByName(p.prop_name) || {};
          return { ...cat, prop_name: p.prop_name, label: p.label || cat.label || p.prop_name };
        });
      } else {
        // all
        candidates = COMP_PROP_CATALOG.slice();
      }

      // Sort podle display_order, pak prop_name
      candidates.sort((a, b) => {
        const ao = a.display_order ?? 9999;
        const bo = b.display_order ?? 9999;
        if (ao !== bo) return ao - bo;
        return (a.prop_name || "").localeCompare(b.prop_name || "");
      });

      // Compose final entry per row: { catalog, server }
      return candidates.map((cat) => ({
        catalog: cat,
        server: serverByName[cat.prop_name] || null,
      }));
    }

    _renderRow(entry) {
      const { catalog, server } = entry;
      const propName = catalog.prop_name;
      const value = server ? server.value : null;
      const scope = server ? server.scope : "base";
      const hasValue = value !== null && value !== undefined;

      const row = document.createElement("div");
      row.className = "erp-oi-row";
      row.dataset.propName = propName;

      // Bulk checkbox
      const cbWrap = document.createElement("div");
      cbWrap.className = "erp-oi-row-cb";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = this.bulkSelected.has(propName);
      cb.addEventListener("change", (e) => {
        if (e.target.checked) this.bulkSelected.add(propName);
        else this.bulkSelected.delete(propName);
        this._updateBulkCount();
      });
      cbWrap.appendChild(cb);
      row.appendChild(cbWrap);

      // Label + prop_name technical
      const labelWrap = document.createElement("div");
      labelWrap.className = "erp-oi-row-label";
      labelWrap.innerHTML = `
        <div class="erp-oi-row-label-main">${_esc(catalog.label || propName)}</div>
        <div class="erp-oi-row-label-sub">${_esc(propName)}${catalog.hint ? ` · ${_esc(catalog.hint)}` : ""}</div>
      `;
      row.appendChild(labelWrap);

      // Editable value
      const valueWrap = document.createElement("div");
      valueWrap.className = "erp-oi-row-value";
      const input = this._buildInput(catalog, value);
      input.addEventListener("change", () => {
        this._saveValue(propName, input, server);
      });
      valueWrap.appendChild(input);
      row.appendChild(valueWrap);

      // Scope badge
      const badgeWrap = document.createElement("div");
      badgeWrap.className = "erp-oi-row-badge";
      if (hasValue) {
        const meta = SCOPE_BADGES[scope] || SCOPE_BADGES.base;
        const badge = document.createElement("span");
        badge.className = "erp-oi-badge";
        badge.style.color = meta.color;
        badge.style.background = meta.bg;
        badge.style.borderColor = meta.color;
        badge.textContent = meta.label;
        badge.title = server.created_by ? `Nastaveno user_id=${server.created_by}, ${server.updated_at || ""}` : "";
        badgeWrap.appendChild(badge);
      }
      row.appendChild(badgeWrap);

      // Reset button (jen pro override scopes)
      const resetWrap = document.createElement("div");
      resetWrap.className = "erp-oi-row-reset";
      if (hasValue && scope !== "base" && server) {
        const resetBtn = document.createElement("button");
        resetBtn.className = "erp-oi-btn-icon";
        resetBtn.title = "Reset na default (smaže override)";
        resetBtn.textContent = "↺";
        resetBtn.addEventListener("click", () => this._resetOverride(server));
        resetWrap.appendChild(resetBtn);
      }
      row.appendChild(resetWrap);

      return row;
    }

    _buildInput(catalog, value) {
      const t = catalog.prop_type;
      let input;
      if (t === "bool") {
        input = document.createElement("select");
        input.className = "erp-oi-input";
        ["", "true", "false"].forEach((opt) => {
          const o = document.createElement("option");
          o.value = opt;
          o.textContent = opt === "" ? "(default)" : opt === "true" ? "Ano" : "Ne";
          if (String(value) === opt) o.selected = true;
          input.appendChild(o);
        });
      } else if (t === "enum" && Array.isArray(catalog.options)) {
        input = document.createElement("select");
        input.className = "erp-oi-input";
        catalog.options.forEach((opt) => {
          const o = document.createElement("option");
          o.value = opt.v;
          o.textContent = opt.t;
          if (String(value || "") === opt.v) o.selected = true;
          input.appendChild(o);
        });
      } else {
        input = document.createElement("input");
        input.type = (t === "int") ? "number" : "text";
        input.className = "erp-oi-input";
        input.value = value !== null && value !== undefined ? String(value) : "";
        input.placeholder = catalog.hint || "";
      }
      return input;
    }

    // ──────────────────────────────────────────────────────────────────
    // SAVE LOGIC
    // ──────────────────────────────────────────────────────────────────
    async _saveValue(propName, input, server) {
      const newValue = input.value;
      const catalog = _catalogByName(propName) || {};
      const uid = (typeof this.options.getCurrentUserId === "function") ? this.options.getCurrentUserId() : null;

      // Empty value → null (= delete property if base, delete override if override)
      // For now: empty string treated as null (skip delete, just save empty)
      try {
        if (server && server.base_id && server.scope !== "base") {
          // Override existuje + uživatel mění → upsert override (per scope)
          await fetch(
            `/api/v1/erp/comp-def-prop/${server.base_id}/override`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              credentials: "same-origin",
              body: JSON.stringify({
                scope: "user",
                scope_id: uid,
                override_value: newValue,
                expected_updated_at: server.updated_at || null,
              }),
            }
          );
        } else if (server && server.scope === "base") {
          // Base property exists → user override (vyšší priorita)
          await fetch(
            `/api/v1/erp/comp-def-prop/${server.source_id}/override`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              credentials: "same-origin",
              body: JSON.stringify({
                scope: "user",
                scope_id: uid,
                override_value: newValue,
              }),
            }
          );
        } else {
          // No server row → create new base property + auto user override
          // (Marti's UX simplification: user edit = user-scoped, ne system)
          const baseRes = await fetch(
            `/api/v1/erp/comp-def/${this.currentCompDefId}/property`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              credentials: "same-origin",
              body: JSON.stringify({
                prop_name: propName,
                prop_value: catalog.default_value || "",
                prop_type: catalog.prop_type || "string",
                label: catalog.label || propName,
                display_order: catalog.display_order || null,
              }),
            }
          );
          if (!baseRes.ok) throw new Error(`Base property INSERT: HTTP ${baseRes.status}`);
          const baseData = await baseRes.json();
          if (baseData.ok && newValue !== "" && newValue !== catalog.default_value) {
            await fetch(
              `/api/v1/erp/comp-def-prop/${baseData.property.id}/override`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({
                  scope: "user",
                  scope_id: uid,
                  override_value: newValue,
                }),
              }
            );
          }
        }
        // Reload modal to reflect new state
        await this._reload();
      } catch (e) {
        console.error("[ErpObjectInspector] Save failed:", e);
        alert("Uložení selhalo: " + e.message);
      }
    }

    async _resetOverride(server) {
      if (!confirm("Smazat override a vrátit hodnotu na default?")) return;
      try {
        const res = await fetch(
          `/api/v1/erp/comp-def-prop-override/${server.source_id}`,
          { method: "DELETE", credentials: "same-origin" }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await this._reload();
      } catch (e) {
        console.error("[ErpObjectInspector] Reset failed:", e);
        alert("Reset selhal: " + e.message);
      }
    }

    async _reload() {
      await this._loadProps();
      // Update tab counts
      if (this.modal) {
        const usedTab = this.modal.querySelector('[data-tab="used"]');
        if (usedTab) usedTab.textContent = `Použité (${this._countUsed()})`;
      }
      this._refreshList();
    }

    _reloadParentGrid() {
      try {
        const api = (typeof this.options.getGridApi === "function") ? this.options.getGridApi() : null;
        if (api && this.options.gridCode && typeof window._sysHelpers?.gridColumnsResolved === "function") {
          // Fetch fresh columnDefs + apply
          window._sysHelpers.gridColumnsResolved(this.options.gridCode).then((cols) => {
            if (cols && api.setGridOption) {
              api.setGridOption("columnDefs", cols);
            }
          }).catch(() => {});
        }
      } catch (e) {
        console.warn("[ErpObjectInspector] grid reload skipped:", e);
      }
    }

    // ──────────────────────────────────────────────────────────────────
    // BULK
    // ──────────────────────────────────────────────────────────────────
    _bulkSelectAll(checked) {
      const props = this._propsForCurrentTab();
      if (checked) {
        props.forEach((entry) => this.bulkSelected.add(entry.catalog.prop_name));
      } else {
        this.bulkSelected.clear();
      }
      this._refreshList();
    }

    _updateBulkCount() {
      if (!this.modal) return;
      const cb = this.modal.querySelector(".erp-oi-bulk-count");
      if (!cb) return;
      const n = this.bulkSelected.size;
      if (n > 0) {
        cb.style.display = "";
        cb.textContent = `${n} vybráno`;
      } else {
        cb.style.display = "none";
      }
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // Helpers
  // ════════════════════════════════════════════════════════════════════════
  function _esc(s) {
    if (s === null || s === undefined) return "";
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  // Export
  window.ErpObjectInspector = ErpObjectInspector;
  console.log("[ErpObjectInspector] loaded — Phase 38.4 Krok 9-D");
})();
