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
        enableExport: true,
        enableFilters: true,
        enableEdit: false,
        enableMasterDetail: false,
        detailRenderer: null,
        enableGrouping: false,
        enablePivot: false,
        enableRangeSelection: true,
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
      this.gridApi = window.agGrid.createGrid(this.container, gridOptions);

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
