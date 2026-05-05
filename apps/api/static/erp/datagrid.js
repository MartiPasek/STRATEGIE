/**
 * ErpDataGrid — fully parameterized grid component for STRATEGIE Centrála 2.
 *
 * Wraps AG Grid Enterprise with:
 *   - STRATEGIE BLACK theme (Quartz Dark s overrides)
 *   - Czech localization (CS_LOCALE)
 *   - Auto column type detection (ID narrow, SQL/Nazev wide, dates, numbers)
 *   - Multiple instances per page support (workspace, modal forms, master-detail, ...)
 *   - Lifecycle: init / update / destroy
 *   - Optional: data fetch from URL, master-detail, cell editing, export
 *
 * Usage:
 *
 *   const grid = new ErpDataGrid(container, {
 *     rowData: [...],                  // OR
 *     dataUrl: "/api/v1/erp/prehled/103",
 *
 *     columnDefs: [...],               // OR
 *     autoColumns: true,               // detect from data
 *     columns: ["ID", "Nazev", ...],   // column names for autoColumns
 *
 *     // Behavior
 *     onRowClick: (row, event) => { ... },         // single click — selection only by default
 *     onRowDoubleClick: (row, event) => { ... },   // double click — typicky open detail/jádro
 *     onCellEdit: (row, field, oldVal, newVal) => Promise<bool>,
 *     onSelectionChange: (selectedRows) => { ... },
 *     enableExport: true,              // CSV + Excel buttons (default: true)
 *     enableFilters: true,             // floating filter row (default: true)
 *     enableEdit: false,               // cell editing (default: false)
 *     enableMasterDetail: false,       // expandable rows (default: false)
 *     detailRenderer: (row) => HTMLElement | null,
 *     enableGrouping: false,           // row grouping (default: false)
 *     enablePivot: false,              // pivot mode (default: false)
 *     enableRangeSelection: true,      // Excel-like range select (default: true)
 *
 *     // Visual
 *     theme: "dark" | "light",         // default: "dark"
 *     height: "100%",                  // default: "100%"
 *     compact: true,                   // small row heights (default: true)
 *     pinnedIdColumn: true,            // ID column pinned-left (default: true)
 *     idColumnNames: ["ID", "Id", "id"],  // default: ["ID", "Id", "id"]
 *
 *     // Column type heuristics (auto column detection)
 *     wideColumnPatterns: [...],       // RegExp or strings; default: SQL/Nazev/Popis/Text/MenuText
 *     numericColumnSuffixes: [...],    // default: detected from row data sample
 *
 *     // Localization
 *     localeText: { ... },             // overrides; default: CS_LOCALE
 *   });
 *
 *   grid.setData(newRows);             // update data
 *   grid.setColumns(newCols);          // update columns
 *   grid.exportCsv("filename.csv");    // export visible rows
 *   grid.exportExcel("filename.xlsx"); // export visible rows
 *   grid.getSelectedRows();            // currently selected rows
 *   grid.refresh();                    // redraw
 *   grid.destroy();                    // cleanup (release AG Grid api)
 *
 * ── Keyboard + mouse interaction (MVP standard, Excel/Windows-like) ──
 *   - Single click on row     = select that row (deselect others)
 *   - Ctrl+click on row       = toggle individual row (multi-select)
 *   - Shift+click on row      = range select from last selected
 *   - Double click on row     = onRowDoubleClick callback (typicky open detail)
 *   - Arrow Up/Down/Left/Right = navigate focus (NIC neotevírá, jen pohyb)
 *   - Tab/Shift+Tab           = next/prev cell horizontally
 *   - Ctrl+arrow              = jump to data edge
 *   - Shift+arrow             = extend selection range (if rangeSelection enabled)
 *
 * Phase B+4 PoC (5.5.2026 odpoledne): AG Grid Enterprise trial, no license key.
 * Refs: docs/strategie_erp.md, Marti's pivot from Tabulator (~70% of ERP know-how
 * lies in grid component, buy enterprise > build month from scratch).
 */
(function (global) {
  "use strict";

  // ── Czech localization ────────────────────────────────────────────────
  const CS_LOCALE = {
    // Generic
    noRowsToShow: "Žádná data",
    loadingOoo: "Načítám…",
    blanks: "Prázdné",
    // Filters
    contains: "obsahuje",
    notContains: "neobsahuje",
    equals: "rovná se",
    notEqual: "nerovná se",
    startsWith: "začíná na",
    endsWith: "končí na",
    blank: "je prázdné",
    notBlank: "není prázdné",
    empty: "Vyber filtr",
    filterOoo: "Filtr…",
    searchOoo: "Hledat…",
    selectAll: "(Vybrat vše)",
    selectAllSearchResults: "(Vybrat vše z výsledků)",
    // Number filter
    lessThan: "menší než",
    greaterThan: "větší než",
    lessThanOrEqual: "menší nebo rovno",
    greaterThanOrEqual: "větší nebo rovno",
    inRange: "v rozsahu",
    inRangeStart: "od",
    inRangeEnd: "do",
    // Date filter
    dateFormatOoo: "rrrr-mm-dd",
    // Header menu
    columns: "Sloupce",
    filters: "Filtry",
    pinColumn: "Připnout sloupec",
    pinLeft: "Připnout vlevo",
    pinRight: "Připnout vpravo",
    noPin: "Odepnout",
    autoSizeThisColumn: "Přizpůsobit šířku tohoto sloupce",
    autoSizeAllColumns: "Přizpůsobit všechny sloupce",
    sizeColumnsToFit: "Roztáhnout sloupce na šířku",
    resetColumns: "Resetovat sloupce",
    expandAll: "Rozbalit vše",
    collapseAll: "Sbalit vše",
    copy: "Kopírovat",
    copyWithHeaders: "Kopírovat s hlavičkami",
    paste: "Vložit",
    export: "Exportovat",
    csvExport: "CSV export",
    excelExport: "Excel export",
    // Group / pivot
    group: "Skupina",
    rowGroupColumns: "Skupinové sloupce",
    rowGroupColumnsEmptyMessage: "Přesuň sloupce sem pro grupování",
    valueColumns: "Hodnotové sloupce",
    pivotMode: "Režim pivot",
    groups: "Skupiny",
    values: "Hodnoty",
    pivots: "Pivoty",
    valueColumnsEmptyMessage: "Přesuň sem hodnoty",
    pivotColumnsEmptyMessage: "Přesuň sem pivot sloupce",
    sum: "Součet",
    avg: "Průměr",
    min: "Min",
    max: "Max",
    count: "Počet",
    first: "První",
    last: "Poslední",
    // Pagination
    page: "Strana",
    more: "Více",
    to: "do",
    of: "z",
    next: "Další",
    last: "Poslední",
    first: "První",
    previous: "Předchozí",
    // Loading
    loading: "Načítám…",
    // Row group panel
    enabled: "Zapnuto",
    // Side bar
    columnsToolPanel: "Sloupce",
    filtersToolPanel: "Filtry",
    // Misc
    applyFilter: "Použít",
    resetFilter: "Reset",
    clearFilter: "Vyčistit",
    cancelFilter: "Zrušit",
  };

  // ── Default wide column heuristic (auto-detect) ──────────────────────
  function isWideColumnDefault(name) {
    const n = String(name || "").toLowerCase();
    return (
      n === "defview" || n === "defviewsqlite" ||
      n === "beforeopensql" || n === "insertsql" ||
      n === "updatesql" || n === "deletesql" ||
      n.endsWith("sql") || n.endsWith("query") ||
      n.startsWith("nazev") || n.startsWith("popis") ||
      n === "menutext" || n.endsWith("text") ||
      n === "remark" || n === "poznamka" || n === "komentar"
    );
  }

  function isIdColumnDefault(name, idNames) {
    return idNames.indexOf(name) !== -1;
  }

  // ── Auto-detect column type from row sample (number / date / string) ─
  function inferColumnType(name, rows) {
    if (!rows || rows.length === 0) return "string";
    let nullCount = 0;
    let numCount = 0;
    let dateCount = 0;
    let strCount = 0;
    const sample = rows.slice(0, Math.min(rows.length, 50));
    for (const r of sample) {
      const v = r[name];
      if (v == null || v === "") { nullCount++; continue; }
      if (typeof v === "number") { numCount++; continue; }
      if (typeof v === "string") {
        // Date pattern (ISO yyyy-mm-dd or yyyy-mm-ddThh:mm:ss)
        if (/^\d{4}-\d{2}-\d{2}/.test(v)) { dateCount++; continue; }
        // Numeric string
        if (/^-?\d+(\.\d+)?$/.test(v)) { numCount++; continue; }
        strCount++;
      } else {
        strCount++;
      }
    }
    const total = sample.length - nullCount;
    if (total === 0) return "string";
    if (numCount / total > 0.8) return "number";
    if (dateCount / total > 0.8) return "date";
    return "string";
  }

  // ── Build columnDefs from raw column names + sample rows ─────────────
  function buildAutoColumnDefs(cols, rows, opts) {
    const idNames = opts.idColumnNames || ["ID", "Id", "id"];
    const wideTest = opts.isWideColumn || isWideColumnDefault;
    const pinId = opts.pinnedIdColumn !== false;
    const result = [];
    for (const c of cols) {
      const isId = isIdColumnDefault(c, idNames);
      const isWide = !isId && wideTest(c);
      const colType = inferColumnType(c, rows);
      const def = {
        field: c,
        headerName: c,
        sortable: true,
        resizable: true,
        // Filtering: floating filter row pod hlavičkou
        filter: colType === "number" ? "agNumberColumnFilter"
               : colType === "date" ? "agDateColumnFilter"
               : "agTextColumnFilter",
        floatingFilter: opts.enableFilters !== false,
      };
      if (isId) {
        def.width = 80;
        def.minWidth = 60;
        def.maxWidth = 110;
        def.flex = 0;
        def.pinned = pinId ? "left" : null;
        def.cellClass = "erp-ag-col-id";
        def.suppressMenu = true;
      } else {
        def.flex = isWide ? 3 : 1;
        def.minWidth = isWide ? 180 : 80;
      }
      // Right-align numbers
      if (colType === "number" && !isId) {
        def.cellStyle = { textAlign: "right" };
        def.headerClass = "ag-right-aligned-header";
      }
      // Tooltip pro long content (truncated)
      def.tooltipValueGetter = (params) => {
        const v = params.value;
        if (v == null) return "";
        return typeof v === "object" ? JSON.stringify(v) : String(v);
      };
      result.push(def);
    }
    return result;
  }

  // ── Component class ──────────────────────────────────────────────────
  class ErpDataGrid {
    constructor(container, options) {
      if (!container) throw new Error("ErpDataGrid: container element required");
      if (typeof window.agGrid === "undefined") {
        throw new Error("ErpDataGrid: agGrid not loaded (chybí <script src=...ag-grid-enterprise.min.js>)");
      }
      this.container = container;
      this.options = Object.assign({}, this._defaults(), options || {});
      this.gridApi = null;
      this._destroyed = false;
      // B+5.2: layout persistence state
      this._currentLayoutId = null;
      this._isDirty = false;
      this._dirtyEventsAttached = false;
      this._init();
    }

    _defaults() {
      return {
        rowData: null,
        columnDefs: null,
        autoColumns: true,
        columns: null,
        dataUrl: null,
        // Behavior
        onRowClick: null,         // single click — typicky NIC (selection má default behavior)
        onRowDoubleClick: null,   // double click — typicky open detail/jádro
        onCellEdit: null,
        onSelectionChange: null,
        onLayoutChange: null,     // B+5.2: ({layoutId, isDirty}) => void — UI badge update
        enableExport: true,
        enableFilters: true,
        enableEdit: false,
        enableMasterDetail: false,
        detailRenderer: null,
        enableGrouping: false,
        enablePivot: false,
        enableRangeSelection: true,
        // B+5.2: layout persistence
        layoutKey: null,          // string — identifikuje persistence scope, např. "prehled_103"
        autoLoadDefault: true,    // při init load effective_default ze server
        // Visual
        theme: "dark",
        height: "100%",
        compact: true,
        pinnedIdColumn: true,
        idColumnNames: ["ID", "Id", "id"],
        wideColumnPatterns: null,
        // Localization
        localeText: null,
      };
    }

    _init() {
      // Apply theme class na container
      const themeClass = this.options.theme === "light"
        ? "ag-theme-quartz"
        : "ag-theme-quartz-dark";
      this.container.classList.add(themeClass);
      this.container.classList.add("erp-ag-grid");
      if (this.options.height) {
        this.container.style.height = this.options.height;
      }

      // B+5.3: build wrapper structure — toolbar nad gridem (pokud layoutKey set).
      // Bez layoutKey žádný toolbar (component fungování beze změny pro non-persistent grids).
      this.gridContainer = this.container;  // default — AG Grid renders přímo do containeru
      if (this.options.layoutKey) {
        this.container.classList.add("erp-grid-with-toolbar");
        this.toolbarEl = document.createElement("div");
        this.toolbarEl.className = "erp-grid-toolbar";
        this.toolbarEl.innerHTML = this._renderToolbarHtml();
        this.gridContainer = document.createElement("div");
        this.gridContainer.className = "erp-grid-inner";
        this.container.appendChild(this.toolbarEl);
        this.container.appendChild(this.gridContainer);
        this._wireToolbar();
      }

      // Resolve columnDefs
      const rowData = this.options.rowData || [];
      let columnDefs = this.options.columnDefs;
      if (!columnDefs && this.options.autoColumns) {
        const cols = this.options.columns ||
          (rowData.length > 0 ? Object.keys(rowData[0]) : []);
        columnDefs = buildAutoColumnDefs(cols, rowData, this.options);
      }

      const opts = this.options;
      const gridOptions = {
        columnDefs: columnDefs || [],
        rowData: rowData,
        // Default column behavior
        defaultColDef: {
          sortable: true,
          resizable: true,
          filter: opts.enableFilters !== false,
          floatingFilter: opts.enableFilters !== false,
          editable: opts.enableEdit === true,
        },
        // Row height (compact = denser display)
        rowHeight: opts.compact ? 26 : 32,
        headerHeight: opts.compact ? 32 : 40,
        // Layout
        domLayout: "normal",
        // Selection — Excel/Windows-style standard:
        //   - Single click  = select that row (deselect others)
        //   - Ctrl+click    = toggle individual row (multi-select)
        //   - Shift+click   = range select from last selected
        //   - Double click  = onRowDoubleClick (typicky open detail/jádro)
        // rowMultiSelectWithClick=false → vyžaduje modifier pro multi-select
        // (to chceme — bez Ctrl/Shift každý click replace selection).
        rowSelection: "multiple",
        rowMultiSelectWithClick: false,
        suppressRowClickSelection: false,
        suppressRowDeselection: false,
        enableRangeSelection: opts.enableRangeSelection !== false,
        // Master-detail
        masterDetail: opts.enableMasterDetail === true,
        detailCellRenderer: opts.detailRenderer || undefined,
        // Tooltips
        tooltipShowDelay: 400,
        // Locale
        localeText: opts.localeText || CS_LOCALE,
        // Side bar (columns + filters panels) — only if grouping/pivot enabled
        sideBar: (opts.enableGrouping || opts.enablePivot) ? {
          toolPanels: [
            { id: "columns", labelDefault: "Sloupce", labelKey: "columns",
              iconKey: "columns", toolPanel: "agColumnsToolPanel" },
            { id: "filters", labelDefault: "Filtry", labelKey: "filters",
              iconKey: "filter", toolPanel: "agFiltersToolPanel" },
          ],
        } : false,
        // Status bar (counts)
        statusBar: {
          statusPanels: [
            { statusPanel: "agTotalRowCountComponent", align: "left" },
            { statusPanel: "agFilteredRowCountComponent" },
            { statusPanel: "agSelectedRowCountComponent" },
            { statusPanel: "agAggregationComponent" },
          ],
        },
        // Excel-like keyboard nav (Marti's MVP standard 5.5.2026)
        enterMovesDown: true,
        enterMovesDownAfterEdit: true,
        // Events
        onGridReady: (params) => {
          this.gridApi = params.api;
          // B+5.2: setup dirty tracking + auto-load default
          this._setupDirtyTracking();
          if (this.options.autoLoadDefault && this.options.layoutKey) {
            this._autoLoadDefault();
          }
        },
        onRowClicked: (event) => {
          // Default selection behavior (single/Ctrl/Shift) handled by AG Grid.
          // onRowClick je optional callback — typicky NEvolá detail (to dělá double-click).
          if (typeof opts.onRowClick === "function") {
            opts.onRowClick(event.data, event.event);
          }
        },
        onRowDoubleClicked: (event) => {
          // Excel/Windows standard — double-click opens detail/jádro
          if (typeof opts.onRowDoubleClick === "function") {
            opts.onRowDoubleClick(event.data, event.event);
          }
        },
        onCellValueChanged: (event) => {
          if (typeof opts.onCellEdit === "function") {
            opts.onCellEdit(event.data, event.colDef.field, event.oldValue, event.newValue);
          }
        },
        onSelectionChanged: (event) => {
          if (typeof opts.onSelectionChange === "function") {
            opts.onSelectionChange(event.api.getSelectedRows());
          }
        },
        // Animation
        animateRows: true,
      };

      // AG Grid v32+ API: createGrid()
      // B+5.3: AG Grid renders do gridContainer (= container nebo wrapper inner)
      this.gridApi = window.agGrid.createGrid(this.gridContainer, gridOptions);

      // If dataUrl, fetch async
      if (opts.dataUrl) {
        this._fetchData(opts.dataUrl);
      }
    }

    async _fetchData(url) {
      try {
        if (this.gridApi && this.gridApi.showLoadingOverlay) {
          this.gridApi.showLoadingOverlay();
        }
        const r = await fetch(url, { credentials: "include" });
        if (!r.ok) throw new Error("Status " + r.status);
        const data = await r.json();
        // Expect {ok, columns, rows, ...} (STRATEGIE-style envelope)
        const rows = data.rows || data.data || data;
        const cols = data.columns ||
          (rows.length > 0 ? Object.keys(rows[0]) : []);
        this.setData(rows);
        if (this.options.autoColumns) {
          const newDefs = buildAutoColumnDefs(cols, rows, this.options);
          this.setColumnDefs(newDefs);
        }
        if (this.gridApi && this.gridApi.hideOverlay) {
          this.gridApi.hideOverlay();
        }
      } catch (e) {
        console.error("ErpDataGrid: fetch failed", url, e);
        if (this.gridApi && this.gridApi.showNoRowsOverlay) {
          this.gridApi.showNoRowsOverlay();
        }
      }
    }

    setData(rows) {
      if (this._destroyed || !this.gridApi) return;
      this.gridApi.setGridOption("rowData", rows || []);
    }

    setColumnDefs(defs) {
      if (this._destroyed || !this.gridApi) return;
      this.gridApi.setGridOption("columnDefs", defs || []);
    }

    // Convenience: rebuild columnDefs from a list of column names
    setColumns(colNames, sampleRows) {
      const sample = sampleRows || [];
      const defs = buildAutoColumnDefs(colNames || [], sample, this.options);
      this.setColumnDefs(defs);
    }

    getSelectedRows() {
      if (this._destroyed || !this.gridApi) return [];
      return this.gridApi.getSelectedRows();
    }

    refresh() {
      if (this._destroyed || !this.gridApi) return;
      try { this.gridApi.refreshCells({ force: true }); } catch (e) {}
      try { this.gridApi.sizeColumnsToFit(); } catch (e) {}
    }

    sizeColumnsToFit() {
      if (this._destroyed || !this.gridApi) return;
      try { this.gridApi.sizeColumnsToFit(); } catch (e) {}
    }

    exportCsv(filename) {
      if (this._destroyed || !this.gridApi) return;
      this.gridApi.exportDataAsCsv({
        fileName: filename || "export.csv",
        suppressQuotes: false,
      });
    }

    exportExcel(filename) {
      if (this._destroyed || !this.gridApi) return;
      if (typeof this.gridApi.exportDataAsExcel === "function") {
        this.gridApi.exportDataAsExcel({
          fileName: filename || "export.xlsx",
        });
      } else {
        // Community fallback
        this.exportCsv(filename ? filename.replace(/\.xlsx$/, ".csv") : "export.csv");
      }
    }

    // ── Phase B+5.2: layout persistence API ───────────────────────────

    /**
     * Vrací URL prefix pro grid-layout API endpointy. layoutKey ve formátu
     * "prehled_<cislo>" — z toho extrahuje cislo. Pokud chybí, vrací null.
     */
    _layoutApiBase() {
      const key = this.options.layoutKey;
      if (!key || typeof key !== "string") return null;
      const m = key.match(/^prehled_(\d+)$/);
      if (!m) {
        console.warn("ErpDataGrid: layoutKey expected 'prehled_<cislo>', got:", key);
        return null;
      }
      return { cislo: parseInt(m[1], 10) };
    }

    /**
     * GET /api/v1/erp/grid-layout/{cislo}/list
     * Returns: {ok, shared, personal, effective_default} | null on error
     */
    async listLayouts() {
      const base = this._layoutApiBase();
      if (!base) return null;
      try {
        const r = await fetch(
          "/api/v1/erp/grid-layout/" + base.cislo + "/list",
          { credentials: "include" }
        );
        if (!r.ok) return null;
        const data = await r.json();
        return data.ok ? data : null;
      } catch (e) {
        console.warn("ErpDataGrid.listLayouts failed:", e);
        return null;
      }
    }

    /**
     * Aplikuje uložený layout na grid (column state via AG Grid applyColumnState).
     * Internal — caller používá loadLayoutById().
     */
    _applyLayout(layoutObj) {
      if (this._destroyed || !this.gridApi || !layoutObj) return false;
      const cols = layoutObj.layout_json && layoutObj.layout_json.columns;
      if (!Array.isArray(cols) || cols.length === 0) return false;
      try {
        this.gridApi.applyColumnState({
          state: cols,
          applyOrder: true,
        });
        this._currentLayoutId = layoutObj.id;
        this._isDirty = false;
        this._notifyLayoutChange();
        return true;
      } catch (e) {
        console.warn("ErpDataGrid._applyLayout failed:", e);
        return false;
      }
    }

    /**
     * Auto-load při init — pokud existuje effective_default, aplikuje + refresh toolbar.
     */
    async _autoLoadDefault() {
      const result = await this.listLayouts();
      if (result && result.effective_default) {
        this._applyLayout(result.effective_default);
      }
      // B+5.3: po fetch list vždy refresh toolbar dropdown (i pokud žádný default)
      await this._refreshToolbar();
    }

    /**
     * Load specific layout podle ID a aplikuje na grid.
     * Returns: true if applied, false if not found / error.
     */
    async loadLayoutById(layoutId) {
      if (!layoutId) return false;
      try {
        const r = await fetch(
          "/api/v1/erp/grid-layout/item/" + layoutId,
          { credentials: "include" }
        );
        if (!r.ok) return false;
        const data = await r.json();
        if (!data.ok || !data.layout) return false;
        return this._applyLayout(data.layout);
      } catch (e) {
        console.warn("ErpDataGrid.loadLayoutById failed:", e);
        return false;
      }
    }

    /**
     * POST /api/v1/erp/grid-layout/{cislo} — vytvoří novou pojmenovanou sestavu.
     * scope: "user" (default) | "shared" (admin only)
     * Returns: layout object | throws on error.
     */
    async saveAsLayout(opts) {
      const base = this._layoutApiBase();
      if (!base) throw new Error("layoutKey not set or invalid");
      if (!opts || !opts.name) throw new Error("name required");
      const body = {
        name: opts.name,
        scope: opts.scope || "user",
        description: opts.description || null,
        is_default: !!opts.isDefault,
        layout_json: { columns: this.getCurrentColumnState() },
      };
      const r = await fetch("/api/v1/erp/grid-layout/" + base.cislo, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || ("Status " + r.status));
      }
      const data = await r.json();
      if (data.ok && data.layout) {
        this._currentLayoutId = data.layout.id;
        this._isDirty = false;
        this._notifyLayoutChange();
        return data.layout;
      }
      throw new Error("Save failed: " + JSON.stringify(data));
    }

    /**
     * PUT /api/v1/erp/grid-layout/item/{layoutId} — uloží current state do
     * existující sestavy. Pokud layoutId neuvedeno, použije _currentLayoutId.
     */
    async updateLayout(layoutId) {
      const id = layoutId || this._currentLayoutId;
      if (!id) throw new Error("No current layout to update — saveAsLayout first");
      const body = {
        layout_json: { columns: this.getCurrentColumnState() },
      };
      const r = await fetch("/api/v1/erp/grid-layout/item/" + id, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || ("Status " + r.status));
      }
      const data = await r.json();
      if (data.ok && data.layout) {
        this._currentLayoutId = data.layout.id;
        this._isDirty = false;
        this._notifyLayoutChange();
        return data.layout;
      }
      throw new Error("Update failed");
    }

    /**
     * POST /api/v1/erp/grid-layout/item/{layoutId}/set-default — označí
     * sestavu jako default ve svém scope (auto-odznačí starý).
     */
    async setDefaultLayout(layoutId) {
      const r = await fetch(
        "/api/v1/erp/grid-layout/item/" + layoutId + "/set-default",
        { method: "POST", credentials: "include" }
      );
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || ("Status " + r.status));
      }
      return await r.json();
    }

    /**
     * DELETE /api/v1/erp/grid-layout/item/{layoutId}.
     * Pokud byl tento layout currentLoadId, reset state.
     */
    async deleteLayout(layoutId) {
      const r = await fetch(
        "/api/v1/erp/grid-layout/item/" + layoutId,
        { method: "DELETE", credentials: "include" }
      );
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || ("Status " + r.status));
      }
      if (this._currentLayoutId === layoutId) {
        this._currentLayoutId = null;
        this._isDirty = false;
        this._notifyLayoutChange();
      }
      return true;
    }

    /** Vrací aktuální AG Grid column state — pro saveAsLayout / updateLayout. */
    getCurrentColumnState() {
      if (this._destroyed || !this.gridApi) return [];
      try { return this.gridApi.getColumnState(); }
      catch (e) { return []; }
    }

    /** Returns currently loaded layout ID (or null = unsaved/auto). */
    getCurrentLayoutId() { return this._currentLayoutId; }

    /** Boolean — current state has unsaved changes vs loaded layout. */
    isDirty() { return this._isDirty; }

    /** Discard current state, re-load effective default ze server. */
    async resetToDefault() {
      this._currentLayoutId = null;
      this._isDirty = false;
      if (this.gridApi) {
        try { this.gridApi.resetColumnState(); } catch (e) {}
      }
      await this._autoLoadDefault();
    }

    /** Internal: emit onLayoutChange callback + refresh toolbar UI. */
    _notifyLayoutChange() {
      // B+5.3: auto-update toolbar dropdown + dirty indicator + save button
      if (this.toolbarEl) {
        // Update jen UI bits (dropdown options + indicator), nedělej refetch
        const dirty = this.toolbarEl.querySelector("[data-erp-dirty]");
        const saveBtn = this.toolbarEl.querySelector("[data-erp-save-btn]");
        if (dirty) {
          if (this._isDirty && this._currentLayoutId) dirty.removeAttribute("hidden");
          else dirty.setAttribute("hidden", "");
        }
        if (saveBtn) {
          if (this._currentLayoutId && this._isDirty) saveBtn.removeAttribute("hidden");
          else saveBtn.setAttribute("hidden", "");
        }
      }
      if (typeof this.options.onLayoutChange === "function") {
        try {
          this.options.onLayoutChange({
            layoutId: this._currentLayoutId,
            isDirty: this._isDirty,
          });
        } catch (e) {
          console.warn("onLayoutChange callback error:", e);
        }
      }
    }

    // ── Phase B+5.3: toolbar UI ───────────────────────────────────────

    _renderToolbarHtml() {
      // Initial empty state — _refreshToolbar() po listLayouts vyplní options
      return (
        '<div class="erp-toolbar-left">' +
          '<select class="erp-layout-select" data-erp-layout-select>' +
            '<option value="">— bez sestavy —</option>' +
          '</select>' +
          '<span class="erp-dirty-indicator" data-erp-dirty hidden>*</span>' +
        '</div>' +
        '<div class="erp-toolbar-right">' +
          '<button class="erp-toolbar-btn" data-erp-save-btn hidden ' +
            'title="Uložit změny do aktuální sestavy">💾 Uložit</button>' +
          '<button class="erp-toolbar-btn" data-erp-saveas-btn ' +
            'title="Uložit aktuální stav jako novou sestavu">+ Uložit jako…</button>' +
          '<button class="erp-toolbar-btn" data-erp-manage-btn ' +
            'title="Spravovat sestavy (rename, delete, set default)">⋮</button>' +
        '</div>'
      );
    }

    _wireToolbar() {
      if (!this.toolbarEl) return;
      const sel = this.toolbarEl.querySelector("[data-erp-layout-select]");
      const saveBtn = this.toolbarEl.querySelector("[data-erp-save-btn]");
      const saveAsBtn = this.toolbarEl.querySelector("[data-erp-saveas-btn]");
      const manageBtn = this.toolbarEl.querySelector("[data-erp-manage-btn]");

      if (sel) {
        sel.addEventListener("change", async (ev) => {
          const id = ev.target.value;
          if (!id) {
            // "— bez sestavy —" → reset na auto-detect
            await this.resetToDefault();
            await this._refreshToolbar();
            return;
          }
          await this.loadLayoutById(parseInt(id, 10));
          await this._refreshToolbar();
        });
      }

      if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
          if (!this._currentLayoutId) return;
          try {
            await this.updateLayout(this._currentLayoutId);
            await this._refreshToolbar();
            this._toast("Sestava uložena.");
          } catch (e) {
            alert("Chyba při ukládání: " + (e.message || e));
          }
        });
      }

      if (saveAsBtn) {
        saveAsBtn.addEventListener("click", async () => {
          await this._openSaveAsDialog();
        });
      }

      if (manageBtn) {
        manageBtn.addEventListener("click", async () => {
          await this._openManagePanel();
        });
      }
    }

    /** Refresh toolbar UI (dropdown options + button states). */
    async _refreshToolbar() {
      if (!this.toolbarEl) return;
      const sel = this.toolbarEl.querySelector("[data-erp-layout-select]");
      const dirty = this.toolbarEl.querySelector("[data-erp-dirty]");
      const saveBtn = this.toolbarEl.querySelector("[data-erp-save-btn]");
      if (!sel) return;

      // Fetch list a populate
      const result = await this.listLayouts();
      const optionsHtml = ['<option value="">— bez sestavy —</option>'];
      if (result && result.shared && result.shared.length > 0) {
        optionsHtml.push('<optgroup label="🔵 Sdílené">');
        for (const l of result.shared) {
          const sel = (l.id === this._currentLayoutId) ? " selected" : "";
          const star = l.is_default ? " ⭐" : "";
          optionsHtml.push(
            '<option value="' + l.id + '"' + sel + '>' +
              this._escapeHtml(l.name) + star +
            '</option>'
          );
        }
        optionsHtml.push('</optgroup>');
      }
      if (result && result.personal && result.personal.length > 0) {
        optionsHtml.push('<optgroup label="👤 Moje">');
        for (const l of result.personal) {
          const sel = (l.id === this._currentLayoutId) ? " selected" : "";
          const star = l.is_default ? " ⭐" : "";
          optionsHtml.push(
            '<option value="' + l.id + '"' + sel + '>' +
              this._escapeHtml(l.name) + star +
            '</option>'
          );
        }
        optionsHtml.push('</optgroup>');
      }
      sel.innerHTML = optionsHtml.join("");

      // Dirty indicator
      if (dirty) {
        if (this._isDirty && this._currentLayoutId) dirty.removeAttribute("hidden");
        else dirty.setAttribute("hidden", "");
      }

      // Save button — viditelné jen když current loaded + dirty
      if (saveBtn) {
        if (this._currentLayoutId && this._isDirty) saveBtn.removeAttribute("hidden");
        else saveBtn.setAttribute("hidden", "");
      }
    }

    async _openSaveAsDialog() {
      const name = window.prompt(
        "Název nové sestavy:",
        this._currentLayoutId ? "" : "Můj pohled"
      );
      if (!name || !name.trim()) return;
      // Scope: shared dialog jen pokud uživatel je admin (server-side check stejně proběhne)
      const wantShared = window.confirm(
        "Uložit jako SDÍLENÝ layout (viditelný všem uživatelům)?\n\n" +
        "OK = sdílený (vyžaduje admin oprávnění)\n" +
        "Zrušit = osobní (jen pro tebe)"
      );
      const isDefault = window.confirm(
        "Označit tento layout jako výchozí (auto-load při otevření přehledu)?\n\n" +
        "OK = ano, je výchozí\n" +
        "Zrušit = ne, jen jedna z více sestav"
      );
      try {
        await this.saveAsLayout({
          name: name.trim(),
          scope: wantShared ? "shared" : "user",
          isDefault: isDefault,
        });
        await this._refreshToolbar();
        this._toast("Sestava '" + name + "' vytvořena.");
      } catch (e) {
        alert("Chyba při ukládání: " + (e.message || e));
      }
    }

    async _openManagePanel() {
      // B+5.3 MVP: simple alert s actions, B+5.3.2 → proper modal
      const result = await this.listLayouts();
      if (!result) {
        alert("Nelze načíst seznam sestav.");
        return;
      }
      const all = [
        ...result.shared.map(l => ({...l, _label: "🔵 " + l.name})),
        ...result.personal.map(l => ({...l, _label: "👤 " + l.name})),
      ];
      if (all.length === 0) {
        alert("Žádné uložené sestavy. Vytvoř první přes '+ Uložit jako…'.");
        return;
      }
      const lines = all.map((l, i) =>
        (i + 1) + ". " + l._label +
        (l.is_default ? " ⭐" : "") +
        (l.id === this._currentLayoutId ? " ✓ (aktivní)" : "")
      );
      const choice = window.prompt(
        "SPRÁVA SESTAV\n\n" +
        lines.join("\n") +
        "\n\nZadej číslo + akci:\n" +
        "  '1 default' — označit jako výchozí\n" +
        "  '1 rename' — přejmenovat\n" +
        "  '1 delete' — smazat\n\n" +
        "(Prázdné = zrušit)"
      );
      if (!choice || !choice.trim()) return;
      const m = choice.trim().match(/^(\d+)\s+(default|rename|delete)$/i);
      if (!m) {
        alert("Neplatný formát. Použij '<číslo> default|rename|delete'.");
        return;
      }
      const idx = parseInt(m[1], 10) - 1;
      const action = m[2].toLowerCase();
      if (idx < 0 || idx >= all.length) {
        alert("Číslo mimo rozsah.");
        return;
      }
      const layout = all[idx];
      try {
        if (action === "default") {
          await this.setDefaultLayout(layout.id);
          this._toast("Sestava '" + layout.name + "' označena jako výchozí.");
        } else if (action === "rename") {
          const newName = window.prompt("Nový název:", layout.name);
          if (!newName || !newName.trim()) return;
          await this._renameLayout(layout.id, newName.trim());
          this._toast("Přejmenováno na '" + newName + "'.");
        } else if (action === "delete") {
          if (!window.confirm("Opravdu smazat sestavu '" + layout.name + "'?")) return;
          await this.deleteLayout(layout.id);
          this._toast("Sestava '" + layout.name + "' smazána.");
        }
        await this._refreshToolbar();
      } catch (e) {
        alert("Chyba: " + (e.message || e));
      }
    }

    async _renameLayout(layoutId, newName) {
      const r = await fetch("/api/v1/erp/grid-layout/item/" + layoutId, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || ("Status " + r.status));
      }
      return await r.json();
    }

    /** Toast notification — MVP: console + brief alert-free overlay. */
    _toast(msg) {
      // B+5.3.2 → real toast component. Pro MVP jen console + DOM injection.
      console.info("[ErpDataGrid]", msg);
      if (!this.toolbarEl) return;
      let toast = this.toolbarEl.querySelector(".erp-toast");
      if (!toast) {
        toast = document.createElement("span");
        toast.className = "erp-toast";
        this.toolbarEl.appendChild(toast);
      }
      toast.textContent = msg;
      toast.style.opacity = "1";
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => {
        if (toast) toast.style.opacity = "0";
      }, 2500);
    }

    _escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, c =>
        ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])
      );
    }

    /** Internal: hook AG Grid events for dirty tracking. */
    _setupDirtyTracking() {
      if (this._dirtyEventsAttached || !this.gridApi) return;
      this._dirtyEventsAttached = true;
      const dirtyEvents = [
        "columnMoved", "columnResized", "columnVisible",
        "columnPinned", "sortChanged",
      ];
      const markDirty = () => {
        if (!this._isDirty) {
          this._isDirty = true;
          this._notifyLayoutChange();
        }
      };
      for (const evt of dirtyEvents) {
        try {
          this.gridApi.addEventListener(evt, markDirty);
        } catch (e) {}
      }
    }

    destroy() {
      if (this._destroyed) return;
      this._destroyed = true;
      try {
        if (this.gridApi && typeof this.gridApi.destroy === "function") {
          this.gridApi.destroy();
        }
      } catch (e) {}
      this.gridApi = null;
      // Cleanup container
      if (this.container) {
        this.container.classList.remove("ag-theme-quartz", "ag-theme-quartz-dark", "erp-ag-grid");
        // Don't innerHTML='' — let caller manage container lifecycle
      }
    }
  }

  // ── Public exports ───────────────────────────────────────────────────
  global.ErpDataGrid = ErpDataGrid;
  global.ErpDataGrid_CS_LOCALE = CS_LOCALE;
  global.ErpDataGrid_buildAutoColumnDefs = buildAutoColumnDefs;
})(typeof window !== "undefined" ? window : this);
