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

  // Esc helper
  function _esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
    );
  }

  // ────────────────────────────────────────────────────────────────────
  // Shared modal skeleton (reuse modal CSS z erp-modal patternu)
  // ────────────────────────────────────────────────────────────────────

  function _buildModalShell(opts) {
    // Returns { overlay, dialog, header, body, footer, close() }
    const overlay = document.createElement("div");
    overlay.className = "erp-modal-overlay";
    overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9000;display:flex;align-items:center;justify-content:center;";

    const dialog = document.createElement("div");
    dialog.className = "erp-modal-dialog erp-design-modal";
    dialog.style.cssText = "background:#1a1f26;border:1px solid #2a3340;border-radius:6px;width:" + (opts.width || "920px") + ";max-width:95vw;max-height:90vh;display:flex;flex-direction:column;color:#cfd6df;font-size:13px;box-shadow:0 12px 40px rgba(0,0,0,0.5);resize:both;overflow:hidden;";

    const header = document.createElement("div");
    header.className = "erp-modal-header";
    header.style.cssText = "padding:10px 16px;border-bottom:1px solid #2a3340;display:flex;align-items:center;justify-content:space-between;background:#141a20;";
    const title = document.createElement("div");
    title.className = "erp-modal-title";
    title.style.cssText = "font-size:14px;font-weight:600;color:#e8eef5;";
    title.textContent = opts.title || "Design";
    header.appendChild(title);
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.textContent = "×";
    closeBtn.style.cssText = "background:transparent;border:none;color:#8a96a4;font-size:22px;cursor:pointer;padding:0 6px;line-height:1;";
    closeBtn.setAttribute("aria-label", "Zavrit");
    header.appendChild(closeBtn);

    const body = document.createElement("div");
    body.className = "erp-modal-body";
    body.style.cssText = "padding:12px 16px;overflow:auto;flex:1 1 auto;min-height:300px;";

    const footer = document.createElement("div");
    footer.className = "erp-modal-footer";
    footer.style.cssText = "padding:10px 16px;border-top:1px solid #2a3340;display:flex;align-items:center;justify-content:flex-end;gap:8px;background:#141a20;";

    dialog.appendChild(header);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    overlay.appendChild(dialog);

    function close() {
      try { overlay.parentNode && overlay.parentNode.removeChild(overlay); } catch (e) {}
      document.removeEventListener("keydown", _onKey);
    }
    function _onKey(ev) {
      if (ev.key === "Escape") close();
    }
    closeBtn.addEventListener("click", close);
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) close();
    });
    document.addEventListener("keydown", _onKey);

    return { overlay, dialog, header, body, footer, title, close };
  }

  function _field(label, value, opts) {
    // Phase 38.4 Krok 14a-A1b (12.5.2026 dop.): UI Kit dogfooding + edit mode.
    // Default: editable (disabled=false). Save flow chybi (Krok 14b TODO) —
    // user-typed zmeny zustavaji v inputu, pri zavreni modalu se ztrati.
    //
    // Pouzij `opts.readonly = true` pro system metadata fields (ID,
    // created_at, updated_at, parent_code computed, framework_jadro_id atd.).
    // `opts.mono = true` pro monospace font (id, code, FK fields).
    opts = opts || {};
    const isReadonly = !!opts.readonly;
    const displayValue = (value == null || value === "") ? "" : String(value);

    // UI Kit cesta — pokud ErpInput zaregistrovan
    if (typeof global.ErpInput === "function") {
      const wrap = document.createElement("div");
      wrap.className = "erp-field erp-field-design" + (isReadonly ? " erp-field-readonly-uikit" : " erp-field-editable-uikit");
      wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
      const inp = new global.ErpInput(wrap, {
        type: "text",
        label: label,
        value: displayValue,
        disabled: isReadonly,  // jen system fields jsou disabled, ostatni RW
        placeholder: "—",
      });
      // Mono variant — override font styling
      if (opts.mono && inp.input) {
        inp.input.style.fontFamily = "ui-monospace,Consolas,monospace";
        inp.input.style.fontSize = "11px";
      }
      // Empty value placeholder
      if (!displayValue && inp.input) {
        inp.input.placeholder = "—";
      }
      return wrap;
    }

    // Fallback raw divs (pokud ErpInput.js nezaregistrován) — vzdy "ne-editable"
    // protoze raw div neumi typing. ErpInput musi byt nactenej (B+6.2).
    const wrap = document.createElement("div");
    wrap.className = "erp-field erp-field-fallback";
    wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;";
    const lab = document.createElement("label");
    lab.textContent = label;
    lab.style.cssText = "font-size:11px;color:#8a96a4;font-weight:500;";
    wrap.appendChild(lab);
    const val = document.createElement("div");
    val.className = "erp-readonly-value";
    val.style.cssText = "padding:5px 8px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;min-height:22px;color:#cfd6df;font-family:" + (opts.mono ? "ui-monospace,Consolas,monospace" : "inherit") + ";font-size:" + (opts.mono ? "11px" : "12px") + ";word-break:break-all;";
    if (!displayValue) {
      val.textContent = "—";
      val.style.color = "#5d6975";
    } else {
      val.textContent = displayValue;
    }
    wrap.appendChild(val);
    return wrap;
  }

  // Backward-compat alias (stara nazev pred Krok 14a-A1b refactor)
  const _readonlyInput = _field;

  function _sectionBuild(title) {
    const wrap = document.createElement("div");
    wrap.className = "erp-design-section";
    wrap.style.cssText = "margin-bottom:14px;";
    const hdr = document.createElement("div");
    hdr.textContent = title;
    hdr.style.cssText = "font-size:12px;font-weight:600;color:#a8b4c2;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #2a3340;";
    wrap.appendChild(hdr);
    const grid = document.createElement("div");
    grid.className = "erp-design-grid";
    grid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 14px;";
    wrap.appendChild(grid);
    return { wrap, grid };
  }

  // ────────────────────────────────────────────────────────────────────
  // Form 1+2 konsolidovany: Soudecek + Core prehledu (2 taby)
  // ────────────────────────────────────────────────────────────────────

  class DesignSoudecekCoreForm {
    constructor(opts) {
      this.opts = opts || {};
      // opts.menuNodeId (preferred) | opts.menuNodeCode | opts.coreId
      // opts.initialTab = 'soudecek' (default) | 'prehled'
      this._shell = null;
      this._pc = null;
      this._data = null;
    }

    open() {
      const initialTab = this.opts.initialTab === "prehled" ? "prehled" : "soudecek";
      const title = initialTab === "prehled"
        ? "Design: Core přehledu"
        : "Design: Soudeček + Core přehledu";

      this._shell = _buildModalShell({ title: title, width: "920px" });
      document.body.appendChild(this._shell.overlay);

      // Loading placeholder
      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

      // Footer — close button (MVP read-only)
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
        url = "/api/v1/erp/design/menu-node-by-code/" + encodeURIComponent(this.opts.menuNodeCode);
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
          { id: "soudecek", label: "Soudeček", content: soudecekDiv },
          { id: "prehled", label: "Přehled (Core)", content: prehledDiv },
        ],
        activeId: initialTab,
      });
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

      // Section: Identifikace — ID readonly (PK), ostatni editable
      const idSec = _sectionBuild("Identifikace");
      idSec.grid.appendChild(_field("ID (menu_node.id)", mn.id, { mono: true, readonly: true }));
      idSec.grid.appendChild(_field("Code", mn.code, { mono: true }));
      idSec.grid.appendChild(_field("Label", mn.label));
      idSec.grid.appendChild(_field("Kind", mn.kind));
      root.appendChild(idSec.wrap);

      // Section: Hierarchie — parent_id/parent_code readonly (FK + computed),
      // sort_order/status/visibility/is_immutable editable
      const treeSec = _sectionBuild("Hierarchie a pořadí");
      treeSec.grid.appendChild(_field("Parent ID", mn.parent_id, { mono: true, readonly: true }));
      treeSec.grid.appendChild(_field("Parent Code", mn.parent_code, { mono: true, readonly: true }));
      treeSec.grid.appendChild(_field("Sort Order", mn.sort_order, { mono: true }));
      treeSec.grid.appendChild(_field("Status", mn.status));
      treeSec.grid.appendChild(_field("Visibility Scope", mn.visibility_scope));
      treeSec.grid.appendChild(_field("Is Immutable", mn.is_immutable ? "ano" : "ne"));
      root.appendChild(treeSec.wrap);

      // Section: Core vazba — FK readonly (vybira se pres picker, Krok 14b)
      const coreSec = _sectionBuild("Vazba na Core přehledu");
      coreSec.grid.appendChild(_field("core_id (FK)", mn.core_id, { mono: true, readonly: true }));
      coreSec.grid.appendChild(_field("cislo_def (legacy)", mn.cislo_def, { mono: true, readonly: true }));
      coreSec.grid.appendChild(_field("framework_jadro_id", mn.framework_jadro_id, { mono: true, readonly: true }));
      coreSec.grid.appendChild(_field("special_handler", mn.special_handler));
      root.appendChild(coreSec.wrap);

      // Section: Popis
      if (mn.description) {
        const descSec = _sectionBuild("Popis");
        const descBox = document.createElement("div");
        descBox.style.cssText = "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;color:#cfd6df;font-size:12px;white-space:pre-wrap;grid-column:1/-1;";
        descBox.textContent = mn.description;
        descSec.grid.appendChild(descBox);
        root.appendChild(descSec.wrap);
      }

      return root;
    }

    _buildPrehledTab() {
      const root = document.createElement("div");
      root.className = "erp-design-tab-prehled";
      const core = (this._data && this._data.core) || null;
      if (!core || !core.id) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:20px;color:#8a96a4;font-style:italic;";
        empty.textContent = "Tento soudeček nemá Core přehledu (menu_node.core_id IS NULL). Folder / iframe / special — nezná list view.";
        root.appendChild(empty);
        return root;
      }

      // Section: Core identita — ID/version/parent_framework_id readonly,
      // ostatni editable. (Marti-AI's Q6 lineage: version+parent_framework_id
      // se updates pres create-new-version flow, ne in-place edit.)
      const idSec = _sectionBuild("Identifikace Core");
      idSec.grid.appendChild(_field("ID (core.id)", core.id, { mono: true, readonly: true }));
      idSec.grid.appendChild(_field("Code", core.code, { mono: true }));
      idSec.grid.appendChild(_field("Label", core.label));
      idSec.grid.appendChild(_field("Layout type", core.layout_type));
      idSec.grid.appendChild(_field("Data entity type", core.data_entity_type, { mono: true }));
      idSec.grid.appendChild(_field("Layout template", core.layout_template, { mono: true }));
      idSec.grid.appendChild(_field("Version", core.version, { mono: true, readonly: true }));
      idSec.grid.appendChild(_field("Parent framework ID", core.parent_framework_id, { mono: true, readonly: true }));
      root.appendChild(idSec.wrap);

      // Section: Popis
      if (core.description) {
        const descSec = _sectionBuild("Popis");
        const descBox = document.createElement("div");
        descBox.style.cssText = "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;color:#cfd6df;font-size:12px;white-space:pre-wrap;grid-column:1/-1;";
        descBox.textContent = core.description;
        descSec.grid.appendChild(descBox);
        root.appendChild(descSec.wrap);
      }

      // Section: Sloupce (preview, Krok 14b doplni inline editor)
      const colsSec = _sectionBuild("Sloupce (read-only preview) — inline editor Krok 14b");
      const cols = (this._data && this._data.columns) || [];
      if (cols.length === 0) {
        const empty = document.createElement("div");
        empty.style.cssText = "padding:8px 12px;color:#5d6975;font-style:italic;grid-column:1/-1;";
        empty.textContent = "Žádné sloupce (comp_def WHERE core_id=" + core.id + " is empty).";
        colsSec.grid.appendChild(empty);
      } else {
        const table = document.createElement("table");
        table.style.cssText = "grid-column:1/-1;width:100%;font-size:12px;border-collapse:collapse;";
        const thead = document.createElement("thead");
        thead.innerHTML = "<tr style=\"background:#141a20;color:#a8b4c2;text-align:left;\">" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">ID</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Field name</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Label</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Type</th>" +
          "<th style=\"padding:5px 8px;border-bottom:1px solid #2a3340;\">Sort</th>" +
          "</tr>";
        table.appendChild(thead);
        const tbody = document.createElement("tbody");
        cols.forEach(c => {
          const tr = document.createElement("tr");
          tr.style.cssText = "border-bottom:1px solid #1a2026;";
          tr.innerHTML =
            "<td style=\"padding:4px 8px;color:#5d6975;font-family:monospace;\">" + _esc(c.id) + "</td>" +
            "<td style=\"padding:4px 8px;font-family:monospace;\">" + _esc(c.field_name || c.code) + "</td>" +
            "<td style=\"padding:4px 8px;\">" + _esc(c.label) + "</td>" +
            "<td style=\"padding:4px 8px;color:#8a96a4;\">" + _esc(c.comp_type_id || c.type) + "</td>" +
            "<td style=\"padding:4px 8px;color:#5d6975;font-family:monospace;\">" + _esc(c.sort_order) + "</td>";
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        colsSec.grid.appendChild(table);
      }
      root.appendChild(colsSec.wrap);

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Form 3: Jadro pro radek (1 tab MVP, prepared for expansion)
  // ────────────────────────────────────────────────────────────────────

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
    }

    open() {
      const title = "Design: Jádro pro řádek";
      this._shell = _buildModalShell({ title: title, width: "920px" });
      document.body.appendChild(this._shell.overlay);

      const loading = document.createElement("div");
      loading.style.cssText = "padding:24px;text-align:center;color:#8a96a4;";
      loading.textContent = "Načítám…";
      this._shell.body.appendChild(loading);

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
      const url = "/api/v1/erp/design/core-by-code/" + encodeURIComponent(gridCode);
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

      // Section: Kontext kliku — vsechno readonly (jen orientacni informace)
      const ctxSec = _sectionBuild("Kontext kliku v gridu");
      ctxSec.grid.appendChild(_field("Grid (core.code)", this.opts.gridCode, { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_field("Řádek (ID)", this.opts.rowId, { mono: true, readonly: true }));
      ctxSec.grid.appendChild(_field("Klepnutý sloupec", this.opts.headerName, { readonly: true }));
      ctxSec.grid.appendChild(_field("comp_def_id sloupce", this.opts.compDefId, { mono: true, readonly: true }));
      root.appendChild(ctxSec.wrap);

      // Section: Jadro identita — ID/version readonly (PK + lineage), ostatni editable
      const core = (this._data && this._data.core) || null;
      if (core && core.id) {
        const idSec = _sectionBuild("Jádro (fw.core) — identita");
        idSec.grid.appendChild(_field("ID", core.id, { mono: true, readonly: true }));
        idSec.grid.appendChild(_field("Code", core.code, { mono: true }));
        idSec.grid.appendChild(_field("Label", core.label));
        idSec.grid.appendChild(_field("Layout type", core.layout_type));
        idSec.grid.appendChild(_field("Data entity type", core.data_entity_type, { mono: true }));
        idSec.grid.appendChild(_field("Version", core.version, { mono: true, readonly: true }));
        if (core.description) {
          const descBox = document.createElement("div");
          descBox.style.cssText = "padding:8px 10px;background:#0f141a;border:1px solid #2a3340;border-radius:3px;color:#cfd6df;font-size:12px;white-space:pre-wrap;grid-column:1/-1;margin-top:6px;";
          descBox.textContent = core.description;
          idSec.grid.appendChild(descBox);
        }
        root.appendChild(idSec.wrap);
      } else {
        const noCore = _sectionBuild("Jádro (fw.core)");
        const empty = document.createElement("div");
        empty.style.cssText = "padding:8px 12px;color:#5d6975;font-style:italic;grid-column:1/-1;";
        empty.textContent = "Žádné jádro pro grid '" + (this.opts.gridCode || "?") + "' (hardcoded view bez core entry, nebo grid neexistuje v fw.core).";
        noCore.grid.appendChild(empty);
        root.appendChild(noCore.wrap);
      }

      // Section: Picker poli (placeholder Krok 14c)
      const pickerSec = _sectionBuild("Picker polí (Krok 14c — dvoupanelový)");
      const pickerHint = document.createElement("div");
      pickerHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      pickerHint.textContent = "Vlevo dostupná pole (entity_def attributes), vpravo vybraná pro form. Drag-drop nebo dvojklik. Implementace v Kroku 14c.";
      pickerSec.grid.appendChild(pickerHint);
      root.appendChild(pickerSec.wrap);

      // Section: Data source (placeholder)
      const dsSec = _sectionBuild("Data source (Krok 14b — insert/update/upsert mode)");
      const dsHint = document.createElement("div");
      dsHint.style.cssText = "padding:14px;background:#0f141a;border:1px dashed #2a3340;border-radius:4px;color:#5d6975;font-style:italic;text-align:center;grid-column:1/-1;";
      dsHint.textContent = "fw.data_source linkovaný k tomuto jádru pro zápis. Mode: insert / update / upsert. Implementace v Kroku 14b.";
      dsSec.grid.appendChild(dsHint);
      root.appendChild(dsSec.wrap);

      return root;
    }
  }

  // ────────────────────────────────────────────────────────────────────
  // Export
  // ────────────────────────────────────────────────────────────────────

  global.DesignSoudecekCoreForm = DesignSoudecekCoreForm;
  global.DesignJadroRadekForm = DesignJadroRadekForm;

})(window);
