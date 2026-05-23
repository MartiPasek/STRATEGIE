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

  // Phase JS-9 (18.5.2026): mutual immunity wrap pro Module Health visibility.
  const _loader = (typeof global !== "undefined" && global._erpLoadModule)
    ? global._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "] init failed:", e); } };

  _loader("datagrid.js", "v1.0.0", function () {


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
    let boolCount = 0;  // počet hodnot, co jsou jen 0/1/true/false
    const sample = rows.slice(0, Math.min(rows.length, 50));
    for (const r of sample) {
      const v = r[name];
      if (v == null || v === "") { nullCount++; continue; }
      if (typeof v === "boolean") { boolCount++; continue; }
      if (typeof v === "number") {
        numCount++;
        if (v === 0 || v === 1) boolCount++;
        continue;
      }
      if (typeof v === "string") {
        // Date pattern (ISO yyyy-mm-dd or yyyy-mm-ddThh:mm:ss)
        if (/^\d{4}-\d{2}-\d{2}/.test(v)) { dateCount++; continue; }
        // Boolean string
        const low = v.toLowerCase();
        if (low === "true" || low === "false") { boolCount++; continue; }
        // Numeric string
        if (/^-?\d+(\.\d+)?$/.test(v)) {
          numCount++;
          if (v === "0" || v === "1") boolCount++;
          continue;
        }
        strCount++;
      } else {
        strCount++;
      }
    }
    const total = sample.length - nullCount;
    if (total === 0) {
      // Fallback heuristic: empty sample → check column name
      if (_looksLikeBooleanName(name)) return "boolean";
      if (_looksLikeNumericName(name)) return "number";
      return "string";
    }
    // Boolean: VŠECHNY non-null hodnoty jsou 0/1/true/false (bool count == total)
    // a column name vypadá jako boolean (Oblibene, Verejne, Aktivni, ...)
    // — vyhne se "Cislo" detekci jako boolean když má jen hodnoty 0,1.
    if (boolCount === total && _looksLikeBooleanName(name)) return "boolean";
    if (numCount / total > 0.8) return "number";
    if (dateCount / total > 0.8) return "date";
    // Mixed sample (např. Ikona má "0", "O", null) — heuristic na name
    if (numCount > 0 && _looksLikeNumericName(name)) return "number";
    return "string";
  }

  /**
   * Heuristic: vypadá column name jako numerický?
   * Pomáhá když sample data jsou mix nebo prázdné (typicky Centrála pattern
   * s rozsáhlými ID/Poradi sloupci kde záhlaví je jistější než data).
   */
  function _looksLikeNumericName(name) {
    if (!name) return false;
    const lower = String(name).toLowerCase();
    const NUMERIC_PATTERNS = [
      "cislo", "číslo",
      "poradi", "pořadí",
      "pocet", "počet",
      "mnozstvi", "množství",
      "castka", "částka", "cena",
      "vaha", "váha",
      "rok", "kod", "kód",
      "id_", "_id",
    ];
    for (const p of NUMERIC_PATTERNS) {
      if (lower.includes(p)) return true;
    }
    return false;
  }

  /**
   * Heuristic: vypadá column name jako boolean (flag) sloupec?
   * Centrála pattern: Oblibene, Verejne, Aktivni, Smazana, Pozadovat...,
   * Viditelne, Online, Offline, Nova, Povolen, Schvalen, Uzavren, ...
   */
  function _looksLikeBooleanName(name) {
    if (!name) return false;
    const lower = String(name).toLowerCase();
    const BOOL_PATTERNS = [
      "oblib", "verej", "aktiv", "smaz", "pozad",
      "viditel", "offline", "online",
      "povol", "schva", "uzavre", "vypnut", "zapnut",
      "is_", "has_",
    ];
    for (const p of BOOL_PATTERNS) {
      if (lower.includes(p)) return true;
    }
    return false;
  }

  /**
   * B+10 (6.5.2026): heuristic — vypadá column name jako STATUS column?
   * (Stav, Status, Druh, Typ + "stat", "stav", "status", "result", "uspech")
   * Plus exact data values musí matchnout known status keywords.
   */
  function _looksLikeStatusName(name) {
    if (!name) return false;
    const lower = String(name).toLowerCase();
    const STATUS_PATTERNS = [
      "stav", "status", "uspech", "result", "vysledek",
    ];
    for (const p of STATUS_PATTERNS) {
      if (lower.includes(p)) return true;
    }
    return false;
  }

  /**
   * B+10: heuristic — money/currency column detection.
   * "Cena", "Castka", "Suma", "Total", "Kc", "Eur", "Usd", "Kredit"...
   */
  function _looksLikeMoneyName(name) {
    if (!name) return false;
    const lower = String(name).toLowerCase();
    const MONEY_PATTERNS = [
      "cena", "castka", "částka", "suma", "total", "kc_", "_kc",
      "eur", "usd", "czk", "kredit", "credit", "debit", "saldo",
      "naklad", "vynos", "prijem", "vydaj", "zustatek",
    ];
    for (const p of MONEY_PATTERNS) {
      if (lower.includes(p)) return true;
    }
    return false;
  }

  /**
   * B+10: heuristic — key/code column detection.
   * "Kod", "Kód", "Klic", "ZkratkaC", "Identifier" — accent purple.
   */
  function _looksLikeKeyName(name) {
    if (!name) return false;
    const lower = String(name).toLowerCase();
    const KEY_PATTERNS = ["kod", "kód", "klic", "klíč", "zkrat", "identifier"];
    for (const p of KEY_PATTERNS) {
      if (lower.includes(p)) return true;
    }
    return false;
  }

  /**
   * B+10: case-insensitive value extraction (Centrála rows mohou mít
   * keys v různém case než column metadata).
   */
  function _getRowValueCI(row, fieldName) {
    if (!row || !fieldName) return undefined;
    if (row[fieldName] !== undefined) return row[fieldName];
    const lower = fieldName.toLowerCase();
    for (const k of Object.keys(row)) {
      if (k.toLowerCase() === lower) return row[k];
    }
    return undefined;
  }

  /**
   * B+10: row-level class rules (whole-row coloring).
   * Marti's UX: "Conditial cell and rows color".
   * Detekuje: deleted (Smazana=true), inactive (Aktivni=false),
   * row error (status field má error value), warn, success, info.
   */
  function _buildRowClassRules() {
    return {
      "erp-ag-row-deleted": (params) => {
        const d = params.data;
        if (!d) return false;
        const v = _getRowValueCI(d, "Smazana") ??
                  _getRowValueCI(d, "Deleted") ??
                  _getRowValueCI(d, "is_deleted");
        return v === true || v === 1 || v === "1";
      },
      "erp-ag-row-inactive": (params) => {
        const d = params.data;
        if (!d) return false;
        const v = _getRowValueCI(d, "Aktivni") ??
                  _getRowValueCI(d, "Aktivní") ??
                  _getRowValueCI(d, "Active") ??
                  _getRowValueCI(d, "is_active");
        if (v == null || v === "") return false;
        return v === false || v === 0 || v === "0";
      },
      "erp-ag-row-error": (params) => {
        const d = params.data;
        if (!d) return false;
        for (const k of Object.keys(d)) {
          if (_looksLikeStatusName(k) && _classifyStatusValue(d[k]) === "error") {
            return true;
          }
        }
        return false;
      },
      "erp-ag-row-warn": (params) => {
        const d = params.data;
        if (!d) return false;
        for (const k of Object.keys(d)) {
          if (_looksLikeStatusName(k) && _classifyStatusValue(d[k]) === "warn") {
            return true;
          }
        }
        return false;
      },
      "erp-ag-row-success": (params) => {
        const d = params.data;
        if (!d) return false;
        for (const k of Object.keys(d)) {
          if (_looksLikeStatusName(k) && _classifyStatusValue(d[k]) === "ok") {
            return true;
          }
        }
        return false;
      },
    };
  }

  /**
   * B+10: parse date string a vrátit "past" / "today" / "soon" (do 7 dnů)
   * / "future" / null pokud nelze parse.
   */
  function _classifyDate(value) {
    if (!value) return null;
    const m = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return null;
    const target = new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10));
    if (isNaN(target.getTime())) return null;
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffMs = target.getTime() - today.getTime();
    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return "past";
    if (diffDays === 0) return "today";
    if (diffDays <= 7) return "soon";
    return "future";
  }

  /**
   * B+10: classify status text value → "ok" / "warn" / "error" / "info" / null
   */
  function _classifyStatusValue(value) {
    if (value == null || value === "") return null;
    const s = String(value).toLowerCase().trim();
    // OK patterns
    if (/^(ok|hotovo|done|done\b|completed|aktivni|aktivní|published|publikov|schválen|povolen|valid|finished|uspes|úspěš|approved)/i.test(s)) {
      return "ok";
    }
    // Error / negative patterns
    if (/^(chyba|error|failed|selh|storno|cancel|zrušen|zrusen|rejected|invalid|expired|expir|odmít|odmit|smaz|deleted)/i.test(s)) {
      return "error";
    }
    // Warning / pending patterns
    if (/^(warn|pending|cekajici|čekající|waiting|in_progress|inprogress|pripravuje|připravuje|recenz|review)/i.test(s)) {
      return "warn";
    }
    // Info / neutral patterns
    if (/^(info|new|nov|draft|otevr|open)/i.test(s)) {
      return "info";
    }
    return null;
  }

  /**
   * Detect numeric column subtype: integer vs decimal.
   * Marti's UX: "Cisellne numericke hodnoty jsou v gridu defaultne
   * zobrazovane na 6 desetinych mist.. Stahni je na dve mista".
   * Pokud sample obsahuje hodnoty s desetinnou částí (v string formátu
   * "5448.000000" nebo native float s non-zero fraction), je to decimal.
   */
  function _detectNumericPrecision(name, rows) {
    if (!rows || rows.length === 0) return 0;
    const sample = rows.slice(0, Math.min(rows.length, 100));
    for (const r of sample) {
      const v = r[name];
      if (v == null || v === "") continue;
      // String s desetinnou tečkou (i kdyby digits po byly všechny 0)
      if (typeof v === "string" && v.includes(".")) return 2;
      // Native float s non-zero zlomkem
      if (typeof v === "number" && !Number.isInteger(v)) return 2;
    }
    return 0;
  }

  /**
   * CS locale numeric formatter — "1234.56" → "1 234,56", "0" → "0".
   * decimals=0 → bez ".00", decimals=2 → "1 234,56".
   */
  function _formatNumberCS(v, decimals) {
    if (v == null || v === "") return "";
    const n = (typeof v === "number") ? v : parseFloat(v);
    if (!Number.isFinite(n)) return String(v);
    return n.toLocaleString("cs-CZ", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  /**
   * ISO date(time) → CZ format "D.M.YYYY" (or "D.M.YYYY HH:MM" pokud time != 00:00).
   * Marti's UX: "Datum se zobrazuje ISO, zobrazuj prosim 25.5.1972...
   * Kdyz datetime ale time je nulovy, tak time nezobrazuj".
   */
  function _formatDateCS(v) {
    if (v == null || v === "") return "";
    const m = String(v).match(
      /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/
    );
    if (!m) return String(v);
    const y = m[1];
    const mo = parseInt(m[2], 10);
    const d = parseInt(m[3], 10);
    const dateStr = d + "." + mo + "." + y;
    const h = m[4], mi = m[5], s = m[6];
    if (h == null) return dateStr;
    // Time present — pokud all zeros, zobrazit jen datum
    const hN = parseInt(h, 10), miN = parseInt(mi, 10);
    const sN = s != null ? parseInt(s, 10) : 0;
    if (hN === 0 && miN === 0 && sN === 0) return dateStr;
    let timeStr = h + ":" + mi;
    if (s != null && sN !== 0) timeStr += ":" + s;
    return dateStr + " " + timeStr;
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
      // B+10 (6.5.2026): column-level coloring — money / key heuristics.
      // Money columns mají numeric formatter + zelená/červená per sign.
      // Key columns mají accent2 purple text + monospace feel.
      const isMoney = !isId && colType === "number" && _looksLikeMoneyName(c);
      const isKey = !isId && _looksLikeKeyName(c);
      if (isMoney) {
        def.cellClass = (def.cellClass ? def.cellClass + " " : "") +
                        "erp-ag-col-money";
      }
      if (isKey) {
        def.cellClass = (def.cellClass ? def.cellClass + " " : "") +
                        "erp-ag-col-key";
      }
      // Right-align numbers — cellClass approach (cellStyle nefunguje
      // pro flex container z B+4.6). Plus header label vpravo.
      if (colType === "number" && !isId) {
        def.cellClass = (def.cellClass ? def.cellClass + " " : "") +
                        "erp-ag-numeric";
        def.headerClass = "ag-right-aligned-header erp-ag-numeric-header";
        def.type = "numericColumn";
        // B+7+++ (6.5.2026): numeric value formatter — 6 decimals → 2.
        // Pokud sample je všechny integers (Cislo, Poradi, ID-like),
        // decimals=0. Jinak 2.
        const decimals = _detectNumericPrecision(c, rows);
        def.valueFormatter = (params) => _formatNumberCS(params.value, decimals);
        // B+10 (6.5.2026): conditional formatting — záporná = červená,
        // nula = dim. AG Grid cellClassRules vyhodnocuje per-cell.
        // B+10+ (6.5.2026): heuristics opt-in jen když options.heuristicsEnabled.
        if (opts && opts.heuristicsEnabled) {
          def.cellClassRules = {
            "erp-ag-numeric-negative": (params) => {
              const v = params.value;
              if (v == null || v === "") return false;
              const n = (typeof v === "number") ? v : parseFloat(v);
              return Number.isFinite(n) && n < 0;
            },
            "erp-ag-numeric-zero": (params) => {
              const v = params.value;
              if (v == null || v === "") return false;
              const n = (typeof v === "number") ? v : parseFloat(v);
              return Number.isFinite(n) && n === 0;
            },
          };
        }
      }
      // Center-align booleans (checkbox-like flag columns).
      // B+6.6c-fix3 (6.5.2026): Marti's "checkboxy by chteli vystredovat
      // na stred bunky".
      if (colType === "boolean") {
        def.cellClass = (def.cellClass ? def.cellClass + " " : "") +
                        "erp-ag-boolean";
        def.headerClass = "erp-ag-boolean-header";
        // Width hint — booleans nepotřebují širokou cellu
        if (!def.minWidth || def.minWidth > 80) def.minWidth = 60;
        // B+10: conditional — true = green, false = dim (heuristic, opt-in B+10+)
        if (opts && opts.heuristicsEnabled) {
          def.cellClassRules = {
            "erp-ag-bool-true": (params) => {
              const v = params.value;
              return v === true || v === 1 || v === "1" ||
                     String(v).toLowerCase() === "true";
            },
            "erp-ag-bool-false": (params) => {
              const v = params.value;
              if (v == null || v === "") return false;
              return v === false || v === 0 || v === "0" ||
                     String(v).toLowerCase() === "false";
            },
          };
        }
      }
      // B+7+++ (6.5.2026): date formatter — ISO → "D.M.YYYY" (CS).
      // Pokud datetime má time = 00:00:00, zobrazit jen datum.
      if (colType === "date") {
        def.valueFormatter = (params) => _formatDateCS(params.value);
        // B+10: conditional — past = red, today = accent, soon = amber (heuristic, opt-in B+10+)
        if (opts && opts.heuristicsEnabled) {
          def.cellClassRules = {
            "erp-ag-date-past": (params) => _classifyDate(params.value) === "past",
            "erp-ag-date-today": (params) => _classifyDate(params.value) === "today",
            "erp-ag-date-soon": (params) => _classifyDate(params.value) === "soon",
          };
        }
      }
      // B+10: Status column heuristic — column name vypadá jako "Stav"
      // a/nebo data values matchují status keywords (OK/Chyba/Pending).
      // B+10+ (6.5.2026): heuristic, opt-in.
      if (colType === "string" && _looksLikeStatusName(c) && opts && opts.heuristicsEnabled) {
        def.cellClassRules = {
          "erp-ag-status-ok": (params) => _classifyStatusValue(params.value) === "ok",
          "erp-ag-status-error": (params) => _classifyStatusValue(params.value) === "error",
          "erp-ag-status-warn": (params) => _classifyStatusValue(params.value) === "warn",
          "erp-ag-status-info": (params) => _classifyStatusValue(params.value) === "info",
        };
      }
      // Tooltip pro long content (truncated) — používá formatted value
      def.tooltipValueGetter = (params) => {
        const v = params.value;
        if (v == null) return "";
        // Pokud má valueFormatter, použij formatted (consistent s display)
        if (typeof def.valueFormatter === "function") {
          try { return def.valueFormatter(params); } catch (e) {}
        }
        return typeof v === "object" ? JSON.stringify(v) : String(v);
      };
      result.push(def);
    }
    return result;
  }

  // ── B+10++ (6.5.2026 Marti's drobnost): CS thousands separator status panel
  //
  // AG Grid Enterprise default agTotalRowCountComponent / agFilteredRowCountComponent
  // hardcoduje en-US formatNumberCommas → "1,000". Marti chce "1 000".
  // Custom panel implementuje IStatusPanel interface s Intl.NumberFormat("cs-CZ").
  // ─────────────────────────────────────────────────────────────────────

  const _CZ_NUM_FMT = new Intl.NumberFormat("cs-CZ");

  class CzRowCountStatusPanel {
    init(params) {
      this.params = params;
      this.api = params.api;
      this.label = params.label || "Celkem";
      this.mode = params.mode || "total";  // "total" | "filtered"
      this.eGui = document.createElement("div");
      this.eGui.className = "ag-status-name-value erp-cz-rowcount";
      this.refresh();
      // AG Grid v32 events for row count changes
      this._listener = () => this.refresh();
      try {
        this.api.addEventListener("modelUpdated", this._listener);
        this.api.addEventListener("filterChanged", this._listener);
      } catch (e) {}
      // B+10++ (Marti's drobnost 6.5.2026): klik na "Celkem" otevře limit
      // dropdown — jen v "total" módu a pokud je limit context set.
      this._clickListener = (ev) => this._onClick(ev);
      this.eGui.addEventListener("click", this._clickListener);
    }

    _getLimitContext() {
      try {
        const ctx = this.api.getGridOption
          ? this.api.getGridOption("context")
          : (this.api.gridOptionsService
              ? this.api.gridOptionsService.get("context")
              : null);
        return (ctx && ctx.limitContext) ? ctx.limitContext : null;
      } catch (e) {
        return null;
      }
    }

    refresh() {
      let n = 0;
      try {
        if (this.mode === "filtered") {
          // Displayed (after filter) — fall back na getDisplayedRowCount
          n = this.api.getDisplayedRowCount ? this.api.getDisplayedRowCount() : 0;
        } else {
          // Total — všechny rows including filtered out
          if (typeof this.api.getModel === "function") {
            const model = this.api.getModel();
            if (model && typeof model.getRowCount === "function") {
              // Server-side / infinite: model.getRowCount()
              n = model.getRowCount();
            } else if (model && model.rootNode && model.rootNode.allLeafChildren) {
              n = model.rootNode.allLeafChildren.length;
            } else {
              n = this.api.getDisplayedRowCount ? this.api.getDisplayedRowCount() : 0;
            }
          } else {
            n = this.api.getDisplayedRowCount ? this.api.getDisplayedRowCount() : 0;
          }
        }
      } catch (e) { n = 0; }
      const formatted = _CZ_NUM_FMT.format(n);

      // B+10++ (Marti's drobnost): limited state — orange + clickable + hint
      const limitCtx = (this.mode === "total") ? this._getLimitContext() : null;
      const isLimited = !!(limitCtx && limitCtx.hasMore);
      this.eGui.classList.toggle("erp-cz-rowcount-limited", isLimited);
      this.eGui.classList.toggle("erp-cz-rowcount-clickable", isLimited);
      // Custom dark hint via data-hint attribute (CSS pseudo-element).
      // Default browser title= replaced — Marti's drobnost "dark hint".
      if (isLimited) {
        this.eGui.setAttribute(
          "data-hint",
          "Limit dosažen — klikni pro změnu"
        );
      } else {
        this.eGui.removeAttribute("data-hint");
      }

      // B+10++ (Marti's drobnost 2): "(limit, má víc)" přesunuto z header
      // do status baru pro zvýraznění stavu.
      const limitMarker = isLimited
        ? ' <span class="erp-cz-rowcount-marker">(limit, má víc)</span>'
        : '';
      const caret = isLimited ? ' ▾' : '';

      this.eGui.innerHTML =
        '<span class="ag-status-name-value-label">' +
        this.label + ':</span> ' +
        '<span class="ag-status-name-value-value">' +
        formatted + caret +
        '</span>' +
        limitMarker;
    }

    _onClick(ev) {
      if (this.mode !== "total") return;
      const ctx = this._getLimitContext();
      if (!ctx || !ctx.hasMore) return;
      ev.stopPropagation();
      this._showLimitMenu(ctx);
    }

    _showLimitMenu(ctx) {
      // Close any existing menu
      this._closeLimitMenu();
      const menu = document.createElement("div");
      menu.className = "erp-cz-rowcount-menu";
      const opts = ctx.options || [1000, 10000, 50000, 100000];
      const current = parseInt(ctx.applied, 10);
      opts.forEach(opt => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "erp-cz-rowcount-menu-item";
        if (opt === current) btn.classList.add("active");
        const label = (opt >= 100000)
          ? "Vše (max 100k)"
          : _CZ_NUM_FMT.format(opt);
        btn.textContent = label;
        btn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          this._closeLimitMenu();
          if (typeof ctx.onChange === "function") {
            try { ctx.onChange(opt); } catch (e) { console.warn("limit onChange:", e); }
          }
        });
        menu.appendChild(btn);
      });
      // Position above the cell (status bar je dole, takže menu jde nahoru)
      const rect = this.eGui.getBoundingClientRect();
      menu.style.position = "fixed";
      menu.style.left = rect.left + "px";
      menu.style.bottom = (window.innerHeight - rect.top + 2) + "px";
      document.body.appendChild(menu);
      this._menu = menu;
      // Outside click closes
      this._outsideListener = (ev) => {
        if (!menu.contains(ev.target) && !this.eGui.contains(ev.target)) {
          this._closeLimitMenu();
        }
      };
      this._escListener = (ev) => {
        if (ev.key === "Escape") {
          ev.preventDefault();
          this._closeLimitMenu();
        }
      };
      setTimeout(() => {
        document.addEventListener("mousedown", this._outsideListener);
        document.addEventListener("keydown", this._escListener);
      }, 0);
    }

    _closeLimitMenu() {
      if (this._menu && this._menu.parentNode) {
        this._menu.parentNode.removeChild(this._menu);
      }
      this._menu = null;
      if (this._outsideListener) {
        document.removeEventListener("mousedown", this._outsideListener);
        this._outsideListener = null;
      }
      if (this._escListener) {
        document.removeEventListener("keydown", this._escListener);
        this._escListener = null;
      }
    }

    getGui() { return this.eGui; }

    destroy() {
      this._closeLimitMenu();
      if (this._clickListener && this.eGui) {
        try { this.eGui.removeEventListener("click", this._clickListener); } catch (e) {}
      }
      if (this._listener && this.api) {
        try {
          this.api.removeEventListener("modelUpdated", this._listener);
          this.api.removeEventListener("filterChanged", this._listener);
        } catch (e) {}
      }
    }
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
      // B+10+ (6.5.2026): user-defined conditional formatting state
      this._formattingRules = [];        // array of rule objects (viz datagrid_formatting.js)
      this._heuristicsEnabled = false;   // B+10 auto-classification = opt-in
      // ── Phase 38.4 Krok 14g-H+34 (22.5.2026 vecer, Marti): Excel mode toggle ──
      // Per-grid feature (Marti's "Je to funkce Gridu, ne globalni"):
      //   EXCEL = AG editable=true (inline cell edit ON), PROD = editable=false.
      //   Ctrl+Shift+E v gridu = toggle. Bez persist (reset reload, servisni mod).
      //   Visual: orange pill v footer (coreId:rowId button).
      this._excelMode = false;
      this._init();
      this._setupExcelModeToggle();
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
        layoutKey: null,          // string — identifikuje persistence scope, např. "core_30" (fw.core.id) / "core_-110" (System scope)
        autoLoadDefault: true,    // při init load effective_default ze server
        // Phase 38.4 Krok 5.R-C+7 (18.5.2026 vecer): coreInfo pill v toolbar
        // { coreId, refId?, coreCode?, coreLabel?, mode?, hardcoded?, extraInfo? }
        // Render: button "coreId:refId" vlevo PRED layout dropdown.
        // Klik → drop-up menu s informacemi (label, code, mode, ...).
        coreInfo: null,
        // B+10++ (6.5.2026): limit context pro status bar Celkem
        // { applied: int, hasMore: bool, options: [int...], onChange: (newLimit) => void }
        // Pokud null → status panel renderuje běžný "Celkem: N" bez click handleru.
        limitContext: null,
        // B+10+++++ (Marti's drobnost 6.5.2026 po návratu): hook pro custom
        // context menu items z jádra (Centrála 1). Array nebo fn(params)→array.
        // Items append po standard built-ins (cut/copy/export). Format AG Grid
        // MenuItemDef: { name, action, icon, shortcut, subMenu, ... }.
        // Příklad jádrový item:
        //   { name: "Otevřít detail", action: () => openJadro(params.node.data.ID) }
        customContextMenuItems: null,
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
        // B+10++++ (Marti's drobnost 6.5.2026 po návratu): toolbar přesunut
        // DO status baru (sloučení dvou řádek do jedné). Implementace:
        // toolbar element vytvořený mimo grid, po onGridReady přesunut do
        // .ag-status-bar-left-panel (DOM move zachovává event listenery).
        this.container.classList.add("erp-grid-with-toolbar", "erp-grid-toolbar-in-statusbar");
        this.toolbarEl = document.createElement("div");
        this.toolbarEl.className = "erp-grid-toolbar erp-grid-toolbar-in-statusbar";
        this.toolbarEl.innerHTML = this._renderToolbarHtml();
        this.gridContainer = document.createElement("div");
        this.gridContainer.className = "erp-grid-inner";
        this.container.appendChild(this.gridContainer);
        // Toolbar zůstane neviditelný stranou — `_relocateToolbarToStatusBar`
        // ho po onGridReady přesune do status baru.
        this.toolbarEl.style.display = "none";
        this.container.appendChild(this.toolbarEl);
        this._wireToolbar();
      }

      // Resolve columnDefs
      const rowData = this.options.rowData || [];
      let columnDefs = this.options.columnDefs;
      if (!columnDefs && this.options.autoColumns) {
        const cols = this.options.columns ||
          (rowData.length > 0 ? Object.keys(rowData[0]) : []);
        // B+10+ (6.5.2026): pass heuristicsEnabled flag — auto-classification
        // pro numeric/bool/date/status columns je teď opt-in (default off).
        const buildOpts = Object.assign({}, this.options, {
          heuristicsEnabled: this._heuristicsEnabled === true,
        });
        columnDefs = buildAutoColumnDefs(cols, rowData, buildOpts);
      }

      const opts = this.options;

      // Phase 35-E.4 Krok C+ fix #8+9 (9.5.2026 vecer, AG Grid issue #7373 + #8503):
      // initialState pro AG Grid v32+ — predcasne aplikuje columnState PRED
      // prvnim renderem (no flicker per issue #7373).
      //
      // KLICOVY DOPLNEK (issue #8503 + AG Grid official docs):
      // "The flex config does not work with a width config in the same column."
      // Pokud columnDef.flex je nastaveny, AG Grid IGNORUJE width — i z
      // initialState.columnState. Musime PRED AG Grid create stripnout flex
      // z columnDefs a SET width z initialLayout.
      //
      // Caller (renderSystemGrid / renderPrehled) muze pre-fetchnout layout
      // z DB a passnout cely layoutObj jako `initialLayout`. ErpDataGrid
      // si rozbali columnState + mutate columnDefs + nastavi _currentLayoutId.
      let initialColumnState = null;
      if (opts.initialLayout && opts.initialLayout.layout_json) {
        const lj = opts.initialLayout.layout_json;
        if (Array.isArray(lj.columns) && lj.columns.length > 0) {
          // Phase API Versioned Routing post-deploy fix #3 (23.5.2026 vecer
          // Marti's catch "sirka funguje, poradi ne"): DB snapshot ma items
          // bez colId (jen field). AG Grid v32+ initialState.columnState
          // VYZADUJE colId per item — bez colId state item ignored
          // (Issue #5111: "columns that can't be matched will be treated as
          // new columns and placed at the end"). Fix: normalize colId fallback
          // k field/column PRED passing do initialState. Pak match s
          // auto-generated colId v columnDefs (= field) funguje.
          initialColumnState = lj.columns
            .map(c => Object.assign({}, c, {
              colId: c.colId || c.field || c.column,
            }))
            .filter(c => !!c.colId);
          // Pre-set state aby guards (onGridSizeChanged, onFirstDataRendered)
          // fungovaly hned — _currentLayoutId truthy = persistovany layout.
          this._currentLayoutId = opts.initialLayout.id;
          this._formattingRules = Array.isArray(lj.formatting_rules)
            ? lj.formatting_rules.slice() : [];
          this._heuristicsEnabled = lj.heuristics_enabled === true;

          // KLICOVE: mutate columnDefs PRED AG Grid create — strip flex,
          // set width + reorder z initialLayout. AG Grid pak respektuje
          // jak width, tak poradi sloupcu.
          if (Array.isArray(columnDefs) && columnDefs.length > 0) {
            const widthByColId = {};
            const orderByColId = {};
            for (let i = 0; i < initialColumnState.length; i++) {
              const c = initialColumnState[i];
              const k = c.colId || c.field;
              if (!k) continue;
              orderByColId[k] = i;
              if (c.width != null && c.width > 0) {
                widthByColId[k] = c.width;
              }
            }
            columnDefs = columnDefs.map(d => {
              const k = d.colId || d.field;
              const savedW = widthByColId[k];
              const newDef = Object.assign({}, d);
              // Remove flex zcela (issue #8503 — AG Grid mix flex+width fail)
              delete newDef.flex;
              if (savedW != null) {
                newDef.width = savedW;
              }
              return newDef;
            });
            // Phase 35-E.4 Krok C+ fix #10 (9.5.2026 vecer Marti's report
            // "ted nefunguje jen poradi sloupcu"): reorder columnDefs podle
            // initialColumnState. AG Grid initialState.columnState pri v32
            // neoverridne columnDefs poradi — musime resort manualne.
            // Sloupce ne v initialColumnState (novejsi columnDefs nez DB
            // snapshot) zustaji na konci ve sve original poradi.
            columnDefs.sort((a, b) => {
              const aKey = a.colId || a.field;
              const bKey = b.colId || b.field;
              const aIdx = orderByColId[aKey];
              const bIdx = orderByColId[bKey];
              const aHas = aIdx != null;
              const bHas = bIdx != null;
              if (!aHas && !bHas) return 0;
              if (!aHas) return 1;   // not in saved state -> end
              if (!bHas) return -1;
              return aIdx - bIdx;
            });
            console.info(
              "[ErpDataGrid] columnDefs mutated for initialLayout — flex stripped, widths + order from DB:",
              columnDefs.slice(0, 5).map(d => ({ colId: d.colId, field: d.field, width: d.width }))
            );
          }
        }
      }

      // B+10+ (6.5.2026): merge user-defined formatting rules + heuristics.
      // Initial state: žádné user rules, heuristics off → empty rowClassRules.
      // Re-applied v _applyLayout() po načtení layout.
      const initialRowRules = this._buildEffectiveRowClassRules();
      const gridOptions = {
        columnDefs: columnDefs || [],
        rowData: rowData,
        // Phase API Versioned Routing post-deploy fix #4 (23.5.2026 vecer Marti's
        // catch "dvojnasobne probliknuti — postavi se spravne, pak ~400ms default,
        // pak zpet"): AG Grid v26+ DEFAULT behavior je "match columnDefs order na
        // kazde columnDefs update / data update / model update". Onen 400ms reset
        // = onModelUpdated event resyncuje columns s columnDefs order, ignoruje
        // applyColumnState order. Fix: maintainColumnOrder:true zachova user-applied
        // order napric updates (AG Grid v26 upgrade guide).
        maintainColumnOrder: true,
        // Krok C+ fix #8: initialState bez flicker (pokud caller pre-fetchnul)
        ...(initialColumnState ? {
          initialState: { columnState: initialColumnState },
        } : {}),
        // B+10 (6.5.2026): row-level conditional formatting.
        // B+10+ (6.5.2026): merge heuristics (opt-in) + user rules (compiled).
        rowClassRules: initialRowRules,
        // Default column behavior — Phase 38.4 Krok 5.R-D+3 (18.5.2026):
        // merge opts.defaultColDefExtra pro per-instance extension
        // (e.g. cellClassRules pro dirty tracking v page_render.js).
        defaultColDef: Object.assign({
          sortable: true,
          resizable: true,
          filter: opts.enableFilters !== false,
          floatingFilter: opts.enableFilters !== false,
          editable: opts.enableEdit === true,
        }, opts.defaultColDefExtra || {}),
        // Phase 38.4 Krok 5.R-D+3 (Marti's "UX delight zdarma"):
        // native AG Grid Ctrl+Z/Y undo edited cells + commit on blur.
        undoRedoCellEditing: true,
        undoRedoCellEditingLimit: 50,
        stopEditingWhenCellsLoseFocus: true,
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
        // B+10++ (6.5.2026 drobnost): Marti chce CS thousands separator
        // (1 000 ne 1,000). AG Grid native agTotalRowCountComponent
        // hardcoduje en-US comma format → custom status panel s Intl.
        // B+10+++ (6.5.2026 odpoledne): smazán "Filtrováno" (duplikát),
        // Celkem přesunut doprava (Marti: "ten zleva Celkem 1000 limit ma
        // vic presun do prava").
        statusBar: {
          statusPanels: [
            // B+10++++++ (Marti's drobnost 6.5.2026 po návratu — 2):
            // Selected přesunutý k pravé straně, oddělený tečkou od Celkem.
            { statusPanel: "agAggregationComponent", align: "left" },
            { statusPanel: "agSelectedRowCountComponent", align: "right" },
            { statusPanel: CzRowCountStatusPanel,
              statusPanelParams: { label: "Celkem", mode: "total" },
              align: "right" },
          ],
        },
        // B+10++ (6.5.2026): context passthrough — status panely + custom
        // components mají k němu přístup přes params.context.
        context: {
          limitContext: opts.limitContext || null,
        },
        // B+10++++ (Marti's drobnost 6.5.2026 po návratu): zakázat browser
        // native context menu na grid (Marti: "kdyz se klikne pravym
        // tlacitkem... kde neni zadna volba... se obevi tento dialog menu
        // — jde to zakazat?"). preventDefaultOnContextMenu: true potlačí
        // OS browser menu i když AG Grid sám nemá menu items pro daný target.
        preventDefaultOnContextMenu: true,
        // B+10+++++ (Marti's drobnost 6.5.2026 po návratu): hook pro custom
        // context menu items z jádra Centrály 1 (Marti: "budeme jej
        // potrebovat tam pridavat z jadra dalsi polozky"). Default behavior
        // = AG Grid built-ins (cut/copy/paste/export). Pokud caller předá
        // `customContextMenuItems` (array nebo fn), append po built-ins.
        getContextMenuItems: (params) => {
          const defaults = [
            "cut", "copy", "copyWithHeaders", "copyWithGroupHeaders", "paste",
            "separator", "export",
          ];
          // Phase 38.4 Krok 9-D (10.5.2026): Object Inspector item pokud
          // column má _comp_def_id (= je v fw framework). Marti-AI's
          // 9-iter konzultace UX: pravý-klik na buňce / hlavičce → modal.
          const oiItems = [];
          try {
            const col = params.column;
            const colDef = col ? col.getColDef() : null;
            if (colDef && colDef._comp_def_id && window.ErpObjectInspector) {
              const self = this;
              oiItems.push({
                name: "⚙️ Vlastnosti sloupce…",
                tooltip: "Object Inspector — editace properties + overrides",
                action: () => {
                  if (!self._objectInspector) {
                    self._objectInspector = new window.ErpObjectInspector({
                      gridCode: opts.gridCode || (opts.layoutKey ? String(opts.layoutKey) : null),
                      getCurrentUserId: () => (window._erpCurrentUserId || null),
                      getGridApi: () => self.gridApi,
                    });
                  }
                  self._objectInspector.showForColumn(colDef);
                },
              });
            }
          } catch (e) { console.warn("Object Inspector menu item failed:", e); }
          // Phase 38.4 (11.5.2026 vecer): DESIGN položky — jen když design
          // mód aktivní (window._erpDesignMode). Marti's spec: 3 různé hardcoded
          // formy podle kontextu kliku.
          //   • cell na řádku       → akce 3/3 "Jádro pro řádek" (row form)
          //   • header / footer     → akce 2/3 "Core přehledu"
          //   • tree row (jinde)    → akce 1/3 (router.py)
          // MVP placeholder = alert s identifikací; hardcoded formy přijdou dál.
          const designItems = [];
          try {
            if (window._erpDesignMode === true) {
              const col = params.column;
              const colDef = col ? col.getColDef() : null;
              const node = params.node;  // null pro header / no-row area
              const fieldName = colDef
                ? (colDef.field || colDef.colId || "-")
                : "-";
              const headerName = colDef
                ? (colDef.headerName || fieldName)
                : "(zadny sloupec)";
              const compDefId = colDef ? colDef._comp_def_id : null;
              const gridCode = opts.gridCode
                || (opts.layoutKey ? String(opts.layoutKey) : "-");
              const NL = String.fromCharCode(10);

              // Akce 2/3 — Core přehledu (vždy v design mode, na headeru i řádku)
              // Phase 38.4 Krok 14a (12.5.2026 rano): otevre DesignSoudecekCoreForm
              // s default focus na Tab "Přehled" (gridCode = fw.core.code).
              designItems.push({
                name: "Design: Core prehledu",
                tooltip: "Editace core prehledu (akce 2/3)",
                action: function () {
                  try {
                    if (typeof window.DesignSoudecekCoreForm !== "function") {
                      alert("DesignSoudecekCoreForm neni nactena (design_forms.js missing).");
                      return;
                    }
                    // gridCode je fw.core.code → backend `core-by-code` endpoint
                    // (via menu_node-by-code variant nepouzitelne, gridCode neni menu_node.code).
                    // Pouzijeme menuNodeCode (uvidi se v backend lookup), ale primarni cesta:
                    // backend dostane gridCode (= core.code), najde menu_node WHERE core_id = ?.
                    // Pro MVP: pouzijeme coreId path az frontend doplni core resolution.
                    // Zde primy backend hit pres `menu-node-by-code` neexistuje pro core code,
                    // takze pouzijeme novy intent endpoint. Workaround MVP: zkusime
                    // fetch /design/core-by-code/{gridCode} a po nem find_menu_node.
                    // gridCode = fw.core.code (z opts.gridCode v ErpDataGrid),
                    // tj. predame jako coreCode -> backend `core-by-code/{code}`
                    // endpoint, ktery vrati {menu_node, core, columns}.
                    new window.DesignSoudecekCoreForm({
                      coreCode: gridCode,
                      initialTab: "prehled",
                    }).open();
                  } catch (e) {
                    console.error("DesignSoudecekCoreForm (grid header) open failed:", e);
                    alert("Chyba otevreni Design formu: " + e.message);
                  }
                },
              });

              // Akce 3/3 — Jádro pro řádek (jen pokud klikáme na řádku)
              if (node && node.data) {
                const rowId = node.data.ID || node.data.id || node.data.Id || node.id || "-";
                designItems.push({
                  name: "Design: Jadro pro radek",
                  tooltip: "Editace jadra (row form) pro tento radek (akce 3/3)",
                  action: function () {
                    // Phase 38.4 Krok 14a: otevre DesignJadroRadekForm s gridCode + rowId.
                    try {
                      if (typeof window.DesignJadroRadekForm !== "function") {
                        alert("DesignJadroRadekForm neni nactena (design_forms.js missing).");
                        return;
                      }
                      new window.DesignJadroRadekForm({
                        gridCode: gridCode,
                        rowId: rowId,
                        headerName: headerName + " (field: " + fieldName + ")",
                        compDefId: compDefId,
                      }).open();
                    } catch (e) {
                      console.error("DesignJadroRadekForm open failed:", e);
                      alert("Chyba otevreni Design formu: " + e.message);
                    }
                  },
                });
              }
            }
          } catch (e) { console.warn("Design menu item failed:", e); }
          // Custom items z opts (per-grid extension) — array nebo fn
          let custom = [];
          try {
            if (typeof opts.customContextMenuItems === "function") {
              custom = opts.customContextMenuItems(params) || [];
            } else if (Array.isArray(opts.customContextMenuItems)) {
              custom = opts.customContextMenuItems;
            }
          } catch (e) { console.warn("customContextMenuItems failed:", e); }
          const all = [...defaults];
          if (oiItems.length > 0) all.push("separator", ...oiItems);
          if (designItems.length > 0) all.push("separator", ...designItems);
          if (custom.length > 0) all.push("separator", ...custom);
          return all;
        },
        // Excel-like keyboard nav (Marti's MVP standard 5.5.2026)
        enterMovesDown: true,
        enterMovesDownAfterEdit: true,
        // Events
        onGridReady: (params) => {
          this.gridApi = params.api;
          // Phase 38.4 Krok 5.R-C+7.2 (18.5.2026 vecer pozde): wire
          // cellFocused listener PO gridApi init (sync _wireToolbar bylo
          // pred onGridReady → gridApi null → listener se nezaregistroval).
          // Marti's spec: "pri scrolovani :ID se musi menit podle aktualni vety".
          if (this.options.coreInfo) {
            var selfFocus = this;
            try {
              params.api.addEventListener("cellFocused", function () {
                try {
                  var focused = params.api.getFocusedCell();
                  if (!focused) return;
                  var node = params.api.getDisplayedRowAtIndex(focused.rowIndex);
                  if (!node || !node.data) return;
                  var rowId = (node.data.id != null) ? node.data.id
                    : (node.data.ID != null) ? node.data.ID : null;
                  selfFocus._updateCoreInfoPill(rowId);
                } catch (e) { /* silent */ }
              });
            } catch (e) {
              console.warn("[ErpDataGrid] cellFocused wire failed:", e);
            }
          }
          // B+5.2: setup dirty tracking + auto-load default
          this._setupDirtyTracking();
          // Phase 35-E.4 Krok C+ fix2 (9.5.2026 vecer): pockame na
          // _autoLoadDefault promise PRED sizeColumnsToFit. Pokud
          // ulozeny layout existuje, applyColumnState aplikoval custom
          // sirky — sizeColumnsToFit by je proporcionalne prepisalo.
          // Pokud layout neexistuje, fit columns jako driv.
          // Phase API Versioned Routing post-deploy fix #5 (23.5.2026 vecer
          // Marti's catch "po 250ms se zavola default a poradi/sirka fuc...
          // CHCE TO DISABLOVAT TO -> autoLoadDefault SKIP applyColumnState"):
          // Pokud initialLayout je pre-fetched, _autoLoadDefault() je no-op
          // pro applyState (SKIP branch), ALE side-effecty (await listLayouts,
          // _refreshToolbar) trigger AG Grid onModelUpdated -> default
          // column order reset (i pri maintainColumnOrder:true, protoze
          // refresh toolbar mutate DOM toolbaru => layout shift => grid
          // resize => internal recompute).
          // Fix: skip _autoLoadDefault ENTIRELY when initialLayout passed.
          // _currentLayoutId uz nastaveno z initialLayout (line 1010).
          // Toolbar refresh udelame lehce v separate promise, bez state ops.
          const hasInitialLayout = !!this.options.initialLayout;
          const initLayout = (this.options.autoLoadDefault && this.options.layoutKey && !hasInitialLayout)
            ? this._autoLoadDefault()
            : Promise.resolve(null);
          // Lightweight toolbar refresh pro pripad pre-fetched initialLayout
          // (drozdneutralni — jen fetch list pro dropdown, zadny applyState)
          if (hasInitialLayout && this.options.layoutKey) {
            // Defer az po grid settle (po 600ms, mezi 500ms LOCK a beyond)
            setTimeout(() => {
              if (this._destroyed) return;
              this.listLayouts()
                .then(() => this._refreshToolbar())
                .catch(() => { /* silent */ });
            }, 600);
          }
          initLayout.finally(() => {
            if (this._destroyed) return;
            if (!this._currentLayoutId) {
              // Zadny default layout — fit columns (Marti's "grid roztazen")
              try { params.api.sizeColumnsToFit(); } catch (e) {}
            }
            // B+10++++ (Marti's drobnost 6.5.2026 po návratu): přesun toolbaru
            // do AG Grid status baru — sloučení dvou řádek do jedné.
            // 150ms aby AG Grid status bar měl čas se mountnout.
            setTimeout(() => this._relocateToolbarToStatusBar(), 150);
            // Phase 38.4 (11.5.2026 vecer): status bar right-click → akce 2/3
            // "Core přehledu". Marti's spec: pravý klik na patičku gridu
            // řeší přehled core, ne row jádro. AG Grid `getContextMenuItems`
            // tu oblast nezachycuje — attach DOM listener přímo.
            setTimeout(() => this._attachStatusBarDesignHandler(), 200);
          });
        },
        onFirstDataRendered: (params) => {
          // Po načtení prvního batch dat
          // Krok C+ fix2: guard — ulozeny layout ma prednost pred fit.
          if (this._currentLayoutId) {
            // Phase 35-E.4 Krok C+ fix #11 (9.5.2026 vecer Marti's
            // "pozice sloupcu nikoli"): AG Grid initialState.columnState
            // aplikuje width per columnDefs mutate ale REORDER columnDefs
            // ignoruje. Po prvnim data render volat applyColumnState s
            // applyOrder:true — widths uz jsou correct (z columnDefs
            // mutate), order se aplikuje navic. Mensi flicker (chvili
            // wrong order, pak reorder), ale order persistuje.
            if (this.options.initialLayout && this.options.initialLayout.layout_json) {
              const cols = this.options.initialLayout.layout_json.columns;
              if (Array.isArray(cols) && cols.length > 0) {
                try {
                  // Phase API Versioned Routing post-deploy fix (23.5.2026 vecer
                  // Marti's catch "problikne spravne pak rozhazi"):
                  // STRIP flex z cols PRED applyColumnState. Pokud cols[i].flex
                  // je truthy (z save snapshotu kde columns mely flex), AG Grid
                  // reapply flex -> grid se rozhazi na flex distribution.
                  // Plus defaultState: { flex: 0 } jako safety net.
                  // Fix 23.5. vecer: DB snapshot ma 'field' ale ne 'colId'.
                  // AG Grid applyColumnState VYZADUJE colId v state items - bez
                  // colId state ignored (37 columns drift smoke test).
                  // Normalize: colId = c.colId || c.field || c.column.
                  const stateNoFlex = cols
                    .map(c => Object.assign({}, c, {
                      colId: c.colId || c.field || c.column,
                      flex: 0,
                      flexAfter: undefined,
                    }))
                    .filter(c => !!c.colId); // drop entries bez identifier
                  // Diagnostic: snapshot before applyColumnState
                  const beforeState = params.api.getColumnState();
                  // Phase API Versioned Routing post-deploy fix #3 (23.5.2026 vecer
                  // Marti's catch "sirka funguje, poradi ne"): partial state s 5 z 38
                  // cols + applyOrder:true v AG Grid v32+ ignoruje order. Pri 33
                  // chybejicich cols Issue #5111 nedeterministic placement.
                  // Fix: build FULL state ze vsech grid cols, merge saved props
                  // pro 5 z initialLayout, pak sort by saved order index (saved
                  // first, ostatni v puvodnim columnDef poradi). Plne pokryty state
                  // = applyOrder se aplikuje deterministicky.
                  const savedByColId = {};
                  const savedOrder = {};
                  stateNoFlex.forEach((c, i) => {
                    savedByColId[c.colId] = c;
                    savedOrder[c.colId] = i;
                  });
                  const fullState = beforeState.map((c, origIdx) => {
                    const saved = savedByColId[c.colId];
                    if (saved) {
                      return Object.assign({}, c, saved, { flex: 0 });
                    }
                    return Object.assign({}, c, { flex: 0 });
                  });
                  // Sort: saved cols first (in saved order), pak ostatni v puvodnim poradi
                  fullState.sort((a, b) => {
                    const aIdx = savedOrder[a.colId];
                    const bIdx = savedOrder[b.colId];
                    const aHas = aIdx != null;
                    const bHas = bIdx != null;
                    if (!aHas && !bHas) {
                      // oba mimo saved — zachovat puvodni poradi z beforeState
                      const aOrig = beforeState.findIndex(x => x.colId === a.colId);
                      const bOrig = beforeState.findIndex(x => x.colId === b.colId);
                      return aOrig - bOrig;
                    }
                    if (!aHas) return 1;
                    if (!bHas) return -1;
                    return aIdx - bIdx;
                  });
                  params.api.applyColumnState({
                    state: fullState,
                    applyOrder: true,
                    defaultState: { flex: 0 },
                  });
                  console.info(
                    "[ErpDataGrid] full state apply — " + fullState.length +
                    " cols (" + stateNoFlex.length + " z layoutu first, " +
                    (fullState.length - stateNoFlex.length) + " ostatnich)"
                  );
                  // Defensive setColumnWidths PIXEL-PERFECT (parita s _applyLayout line 1645).
                  // Forces explicit widths z initialLayout — preventuje AG Grid auto-fit
                  // overriding pres flex inheritance nebo sizeColumnsToFit.
                  try {
                    const widths = stateNoFlex
                      .filter(c => c.width != null && c.width > 0 && !!c.colId)
                      .map(c => ({ key: c.colId, newWidth: c.width }));
                    if (widths.length > 0 && typeof params.api.setColumnWidths === "function") {
                      params.api.setColumnWidths(widths);
                      console.info("[ErpDataGrid] onFirstDataRendered → setColumnWidths(" + widths.length + " cols) defensive lock");
                    }
                  } catch (eSW) {
                    console.warn("[ErpDataGrid] setColumnWidths defensive failed:", eSW);
                  }
                  // Diagnostic: snapshot after (sync) — diff widths/order
                  const afterState = params.api.getColumnState();
                  const diff = [];
                  for (const a of afterState) {
                    const b = beforeState.find(x => x.colId === a.colId);
                    if (!b) continue;
                    if (b.width !== a.width || b.flex !== a.flex || b.hide !== a.hide) {
                      diff.push({ colId: a.colId, before: { w: b.width, flex: b.flex }, after: { w: a.width, flex: a.flex } });
                    }
                  }
                  console.info(
                    "[ErpDataGrid] onFirstDataRendered → applyColumnState(applyOrder:true) — column reorder z initialLayout"
                  );
                  if (diff.length > 0) {
                    console.info("[ErpDataGrid] applyColumnState changed " + diff.length + " columns:", diff.slice(0, 10));
                  }
                  // PERMANENT 500ms re-apply (Marti's catch 23.5. vecer): AG Grid
                  // ASYNC reapplikuje flex:1 po onModelUpdated (cca 250-500ms post
                  // applyColumnState). Diagnostic test ukazal:
                  //   post_apply: {w:80, flex:null}
                  //   after_250ms: {w:80, flex:1}   <- AG Grid reapply flex
                  // Width preserved ale flex:1 zpusobi re-distribute pri dalsim
                  // render. Fix: po 500ms (Marti's "prodlouzit ten cas") force
                  // re-apply setColumnWidths z afterState (= co byl spravne
                  // po applyColumnState). Slozitejsi prehledy (38+ cols)
                  // potrebuji vic casu na settle pred re-apply.
                  setTimeout(() => {
                    try {
                      const reWidths = afterState
                        .filter(c => c.width != null && c.width > 0 && !!c.colId)
                        .map(c => ({ key: c.colId, newWidth: c.width }));
                      if (reWidths.length > 0 && typeof params.api.setColumnWidths === "function") {
                        params.api.setColumnWidths(reWidths);
                        // Plus explicit setColumnState aby flex zustal 0 (preventuje budouci reapply)
                        // Fix #3 (23.5.2026 vecer): pridat applyOrder:true aby 500ms re-apply
                        // preservoval order z initial applyColumnState (afterState reflects
                        // post-apply order = saved layout order)
                        try {
                          const lockState = afterState.map(c => ({ colId: c.colId, width: c.width, flex: 0 }));
                          params.api.applyColumnState({
                            state: lockState,
                            applyOrder: true,
                            defaultState: { flex: 0 },
                          });
                        } catch (eL) { /* silent */ }
                        console.info(
                          "[ErpDataGrid] Layout LOCK 300ms post-render (" + reWidths.length + " cols, flex:0 forced)"
                        );
                      }
                      // Phase API Versioned Routing post-deploy fix #6 (23.5.2026 vecer):
                      // REVEAL grid container po LOCK doběhl (visibility:hidden -> visible).
                      // Hide bylo set v createGrid (line 1611). Tady release, user vidi
                      // grid az kdyz uz je final state. Plus clear safety timer.
                      try {
                        if (this._initVisibilityTimer) {
                          clearTimeout(this._initVisibilityTimer);
                          this._initVisibilityTimer = null;
                        }
                        if (this.gridContainer && this.gridContainer.style.visibility === 'hidden') {
                          this.gridContainer.style.visibility = 'visible';
                          console.info("[ErpDataGrid] gridContainer REVEAL (post-LOCK, no flicker)");
                        }
                      } catch (eR) { /* silent */ }
                    } catch (e) { /* silent */ }
                  }, 300);
                } catch (e) {
                  console.warn("[ErpDataGrid] reorder applyColumnState failed:", e);
                }
              }
              // Phase 22.5.2026: aplikuj formatting rules z initialLayout
              // (rules nactene v _init na line 992, ale _rebuildGridFormatting
              // se nikdy nezavolala — _applyLayout se pro initialLayout
              // cestu skipne pres skipApply guard v _autoLoadDefault).
              try {
                var hasRules = Array.isArray(this._formattingRules) && this._formattingRules.length > 0;
                if (hasRules || this._heuristicsEnabled === true) {
                  this._rebuildGridFormatting();
                  console.info(
                    "[ErpDataGrid] onFirstDataRendered → _rebuildGridFormatting (initialLayout rules count=" +
                    (this._formattingRules ? this._formattingRules.length : 0) +
                    ", heuristics=" + (this._heuristicsEnabled === true) + ")"
                  );
                }
              } catch (e) {
                console.warn("[ErpDataGrid] initialLayout rebuild formatting failed:", e);
              }
            }
            return;
          }
          try { params.api.sizeColumnsToFit(); } catch (e) {}
        },
        onGridSizeChanged: (params) => {
          // ResizeObserver-style: container width changed (window resize,
          // tree pane resize, atd.) → fit columns
          // Phase 35-E.4 Krok C+ fix (9.5.2026 vecer Marti's report): pokud
          // mame aplikovany ulozeny layout, sizeColumnsToFit NEPREPISE
          // custom sirky sloupcu. Tabs switch trigger onGridSizeChanged ->
          // bez guardu by reset persistovany state.
          if (this._currentLayoutId) return;
          try { params.api.sizeColumnsToFit(); } catch (e) {}
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
        // Phase 38.4 Krok 14b (12.5.2026 vecer): Enter na radku gridu = open detail.
        // Marti's spec: "Pri ENTER na radku gridu uzivatelu, nebo pres double clik
        // je treba otevrit toto jadro s formem".
        // Skip: pokud bunka v editing modu (Enter commituje edit) nebo Shift+Enter
        // (multi-select line break v cell editoru).
        onCellKeyDown: (event) => {
          const ev = event.event;
          if (!ev || ev.key !== "Enter") return;
          if (ev.shiftKey || ev.ctrlKey || ev.altKey || ev.metaKey) return;
          // Bunka v editing modu → ignoruj (Enter commituje edit)
          try {
            const editing = event.api.getEditingCells();
            if (Array.isArray(editing) && editing.length > 0) return;
          } catch (e) {}
          if (typeof opts.onRowEnter === "function") {
            ev.preventDefault();
            opts.onRowEnter(event.data, ev);
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

      // Phase API Versioned Routing post-deploy fix #6 (23.5.2026 vecer Marti's
      // catch "po 300ms problikne vsechny na 80px"): AG Grid Issue #9959 —
      // "Column widths with flex setting are calculated by the grid AFTER initial
      // render, which causes layout flashes". AG Grid post-render rekalkuluje
      // flex widths (i kdyz initialState ma explicit widths) -> 80px each = container
      // width / 38 cols. Vidi se ~300ms flash, pak 500ms LOCK vrati spravne widths.
      // Fix: visibility:hidden na gridContainer az do LOCK doby, pak show. Zadny
      // user-visible flash. Onen "right way to apply columnState without flickering"
      // z [Issue #7373] — hide DOM behem initial render flicker window.
      if (opts.initialLayout && this.gridContainer) {
        try {
          this.gridContainer.style.visibility = 'hidden';
          // Phase API Versioned Routing post-deploy fix #11 (23.5.2026 vecer
          // Marti's "zkratit visibilitu"): safety net 1500ms -> 800ms.
          // Reveal hook v 500ms LOCK setTimeout zkracen na 300ms.
          this._initVisibilityTimer = setTimeout(() => {
            try { if (this.gridContainer) this.gridContainer.style.visibility = 'visible'; } catch (e) {}
          }, 800);
        } catch (e) { /* silent */ }
      }
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
     * "core_<id>" — z toho extrahuje core_id. Pokud chybí, vrací null.
     *
     * Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer, Marti's "prehled_cislo musi
     * uplne zmizet"): rename z "prehled_<cislo>" → "core_<id>" — neutralni
     * scope key, ne Centrala 1 reference.
     */
    _layoutApiBase() {
      const key = this.options.layoutKey;
      if (!key || typeof key !== "string") return null;
      // Krok 5.U (23.5.2026): polymorphic scope — Marti's Q8=A path prefix.
      // Accept "core_<id>" OR "ds_<id>" formats. Frontend pass full scopeKey
      // do URL (backend parsuje stejnou regex).
      const m = key.match(/^(core|ds)_(-?\d+)$/);
      if (!m) {
        console.warn("ErpDataGrid: layoutKey expected 'core_<id>' OR 'ds_<id>', got:", key);
        return null;
      }
      return { scopeKey: key, scopeKind: m[1], scopeId: parseInt(m[2], 10) };
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
          "/api/v1/erp/grid-layout/" + base.scopeKey + "/list",
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
      const lj = layoutObj.layout_json || {};
      const cols = lj.columns;
      if (!Array.isArray(cols) || cols.length === 0) return false;
      try {
        // Phase 35-E.4 Krok C+ fix2+5 (9.5.2026 vecer): diag log pred/po
        // applyColumnState — uvidime co AG Grid skutecne aplikuje.
        console.info(
          "[ErpDataGrid] applyColumnState input cols=" + cols.length +
          " — first cols sample:",
          cols.slice(0, 3).map(c => ({ colId: c.colId, width: c.width, flex: c.flex, hide: c.hide }))
        );
        // Phase 35-E.4 Krok C+ fix5 (9.5.2026 vecer): Marti's
        // "problikne a zcucne" — AG Grid render correct width chvili,
        // pak flex z columnDef redistribuuje proporcionalne.
        //
        // Trojvrstvy fix:
        // a) Force-clear flex na vsech columnDefs pres updateGridOptions —
        //    columnDef flex: 0 zustane permanentne.
        // b) applyColumnState s flex:0 v state items + defaultState.
        // c) setColumnWidths defensive po applyColumnState pro pixel-perfect.
        //
        // (a) musi byt PRVNI — bez toho AG Grid pri kazdem render zase
        // distribuuje proporcionalne (state items maji prednost jen na
        // prvni render, columnDef si AG Grid pamatuje permanentne).
        try {
          const currentDefs = this.gridApi.getColumnDefs ? this.gridApi.getColumnDefs() : null;
          if (Array.isArray(currentDefs) && currentDefs.length > 0) {
            // Phase 35-E.4 Krok C+ fix7 (9.5.2026 vecer): Marti's tip
            // "Flex je autosize". Pixel-perfect persistence vyzaduje
            // ZLOMIT AG Grid auto-distribute na columnDef level:
            //   - flex: 0 (no proportional)
            //   - suppressSizeToFit: true (sizeColumnsToFit ho preskoci)
            // Per-column saved width z DB pak drzi permanentne.
            const newDefs = currentDefs.map(d => Object.assign({}, d, {
              flex: 0,
              suppressSizeToFit: true,
            }));
            if (typeof this.gridApi.setGridOption === "function") {
              this.gridApi.setGridOption("columnDefs", newDefs);
            } else if (typeof this.gridApi.updateGridOptions === "function") {
              this.gridApi.updateGridOptions({ columnDefs: newDefs });
            } else if (typeof this.gridApi.setColumnDefs === "function") {
              this.gridApi.setColumnDefs(newDefs);
            }
          }
        } catch (e) {
          console.warn("[ErpDataGrid] columnDefs flex/suppressSizeToFit failed:", e);
        }
        this.gridApi.applyColumnState({
          state: cols,
          applyOrder: true,
          defaultState: { flex: 0 },
        });
        // Defensive setColumnWidths po applyColumnState pro pixel-perfect.
        try {
          const widths = cols
            .filter(c => c.width != null && c.width > 0)
            .map(c => ({ key: c.colId, newWidth: c.width }));
          if (widths.length > 0 && typeof this.gridApi.setColumnWidths === "function") {
            this.gridApi.setColumnWidths(widths);
          }
        } catch (e) {
          console.warn("[ErpDataGrid] setColumnWidths failed:", e);
        }
        // Po-apply state pro porovnani
        try {
          const after = this.gridApi.getColumnState();
          console.info(
            "[ErpDataGrid] applyColumnState DONE — getColumnState() po:",
            after.slice(0, 3).map(c => ({ colId: c.colId, width: c.width, flex: c.flex, hide: c.hide }))
          );
        } catch (e) {}
        // B+10+ (6.5.2026): extract conditional formatting state z layout
        this._formattingRules = Array.isArray(lj.formatting_rules)
          ? lj.formatting_rules.slice()
          : [];
        this._heuristicsEnabled = lj.heuristics_enabled === true;
        // Re-apply formatting po column state change
        this._rebuildGridFormatting();
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
     *
     * Phase 35-E.4 Krok C+ fix #8: pokud caller pre-fetchnul layout a passnul
     * jako `initialLayout`, AG Grid uz aplikoval columnState pres `initialState`
     * gridOption (issue #7373 workaround) — preskocime applyColumnState.
     * Stejne ale fetchneme list pro toolbar dropdown.
     */
    async _autoLoadDefault() {
      const key = this.options.layoutKey;
      // Phase API Versioned Routing post-deploy fix #7 (23.5.2026 vecer Marti's
      // catch "Znovu volas to autoloaddefault... DISABLUJ HO JAKO PREDTIM"):
      // HARD GUARD na samotnem function body. I kdyby caller (init or
      // resetToDefault) volal _autoLoadDefault PRES Fix #5 condition, pokud
      // initialLayout passed -> early return BEZ listLayouts() side-effects.
      // Belt-and-suspenders: caller guard (Fix #5) + callee guard (Fix #7).
      // Caller-side reset (resetToDefault button) override pres allowReload=true
      // (NIKDO ne pase tuto option zatim, ale future-proof pro user reset action).
      if (this.options.initialLayout) {
        console.info(
          "[ErpDataGrid] _autoLoadDefault " + (key || "(no key)") +
          " → HARD SKIP (initialLayout passed, Fix #7)"
        );
        return;
      }
      const skipApply = false;  // unreachable after early return, kept for clarity
      const result = await this.listLayouts();
      if (skipApply) {
        // Phase API Versioned Routing post-deploy fix #2 (23.5.2026 vecer
        // Marti's catch "drifting zmizelo, presto efekt je stejny... Neco
        // zavola autoLoadDefault"): initialLayout pre-applied via initialState,
        // ALE _currentLayoutId zustaval null -> initLayout.finally callback
        // (line ~1322) si myslel "zadny layout" a volal sizeColumnsToFit()
        // = proporcionalni flex distribuce -> 38 cols rozhazeno na ~80px each.
        // Fix: nastavit _currentLayoutId z initialLayout.id, aby finally
        // callback poznal "layout existuje, fit SKIP".
        try {
          const il = this.options.initialLayout;
          if (il && il.id != null) {
            this._currentLayoutId = il.id;
            this._currentLayoutName = il.name || null;
            this._isDirty = false;
          }
        } catch (e) { /* silent */ }
        console.info(
          "[ErpDataGrid] autoLoadDefault " + key +
          " → SKIP applyColumnState + lock _currentLayoutId=" +
          (this._currentLayoutId != null ? this._currentLayoutId : "null") +
          " (initialLayout pre-applied via gridOptions.initialState)"
        );
      } else if (result && result.effective_default) {
        const lid = result.effective_default.id;
        const lname = result.effective_default.name;
        const applied = this._applyLayout(result.effective_default);
        console.info(
          "[ErpDataGrid] autoLoadDefault " + key + " → applied layout #" +
          lid + " '" + lname + "' (success=" + applied + ")"
        );
      } else {
        console.info(
          "[ErpDataGrid] autoLoadDefault " + key +
          " → no effective_default (shared=" +
          ((result && result.shared) ? result.shared.length : 0) +
          ", personal=" +
          ((result && result.personal) ? result.personal.length : 0) +
          "). Tip: Save As → ⭐ Označit jako výchozí."
        );
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
        layout_json: {
          columns: this.getCurrentColumnState(),
          // B+10+ (6.5.2026): persist conditional formatting state
          formatting_rules: this._formattingRules || [],
          heuristics_enabled: this._heuristicsEnabled === true,
        },
      };
      const r = await fetch("/api/v1/erp/grid-layout/" + base.scopeKey, {
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
        layout_json: {
          columns: this.getCurrentColumnState(),
          // B+10+ (6.5.2026): persist conditional formatting state
          formatting_rules: this._formattingRules || [],
          heuristics_enabled: this._heuristicsEnabled === true,
        },
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

    /** Vrací aktuální AG Grid column state — pro saveAsLayout / updateLayout.
     *
     * Phase 35-E.4 Krok C+ fix3+4 (9.5.2026 vecer):
     *
     * Bug #1: getColumnState() pro flex sloupce vraci `width: 80` (default),
     * NE current rendered pixel width. AG Grid tracks flex distribution,
     * nikoliv pixel snapshot. Marti's DB ukazala width: 80 vsude → dukaz.
     *
     * Bug #2: Default columnDefs (buildAutoColumnDefs line 539) maji
     * `flex: 1` pro vsechny non-ID sloupce. Pri manual resize AG Grid
     * NEZRUSI flex → applyColumnState pak `flex` ma prednost pred `width`
     * → custom sirky se ztrati pri load.
     *
     * Fix: getActualWidth() per column pro real pixel snapshot + strip flex.
     * Save snapshot = explicit widths lock. Po load `flex: null` + `width`
     * → AG Grid respektuje pixel width. Trade-off: po load grid neni
     * responsive (flex distribution off), ale persistent widths drzi.
     */
    getCurrentColumnState() {
      if (this._destroyed || !this.gridApi) return [];
      try {
        const raw = this.gridApi.getColumnState();
        // Phase 22.5.2026: triple-fallback width capture (Marti's "po reload
        // se zmeny neprojevily" — width: 80 vsude v DB). getActualWidth() fix
        // z 9.5.2026 nestacil. Pridana DOM measurement jako 3. fallback.
        //   1. col.getActualWidth() (API — funguje pro non-flex)
        //   2. col.getColDef().actualWidth / width (columnDef snapshot)
        //   3. DOM measurement (querySelector ag-header-cell pres colId)
        //   4. raw c.width (poslední fallback — defaultní 80 pro flex)
        const captured = raw.map(c => {
          let actualWidth = null;
          let source = "none";
          try {
            const col = this.gridApi.getColumn(c.colId);
            if (col) {
              if (typeof col.getActualWidth === "function") {
                const w = col.getActualWidth();
                if (w != null && w > 0) {
                  actualWidth = w;
                  source = "getActualWidth";
                }
              }
              if (actualWidth == null && typeof col.getColDef === "function") {
                const def = col.getColDef();
                if (def && def.actualWidth != null && def.actualWidth > 0) {
                  actualWidth = def.actualWidth;
                  source = "colDef.actualWidth";
                } else if (def && def.width != null && def.width > 0) {
                  actualWidth = def.width;
                  source = "colDef.width";
                }
              }
            }
          } catch (e) {}
          if (actualWidth == null && this.containerEl) {
            try {
              var safeId = String(c.colId || "").replace(/"/g, "");
              var sel = '[col-id="' + safeId + '"].ag-header-cell';
              var headerEl = this.containerEl.querySelector(sel);
              if (headerEl) {
                var rect = headerEl.getBoundingClientRect();
                if (rect && rect.width > 0) {
                  actualWidth = Math.round(rect.width);
                  source = "DOM";
                }
              }
            } catch (e) {}
          }
          if (actualWidth == null) {
            actualWidth = c.width;
            source = "raw";
          }
          return Object.assign({}, c, {
            width: actualWidth,
            flex: 0,
            __widthSource: source,
          });
        });
        try {
          var sources = {};
          captured.forEach(function (c) {
            sources[c.__widthSource] = (sources[c.__widthSource] || 0) + 1;
          });
          console.info(
            "[ErpDataGrid] getCurrentColumnState — width sources:", sources,
            "first 3 cols:",
            captured.slice(0, 3).map(function (c) {
              return { colId: c.colId, width: c.width, source: c.__widthSource };
            })
          );
        } catch (e) {}
        return captured.map(function (c) {
          var clean = Object.assign({}, c);
          delete clean.__widthSource;
          return clean;
        });
      }
      catch (e) { return []; }
    }

    // ── B+10+ (6.5.2026): conditional formatting API ──────────────────

    /** Vrací aktuální user-defined formatting rules (array). */
    getFormattingRules() {
      return this._formattingRules.slice();
    }

    /** Set new rules + re-apply to grid. */
    setFormattingRules(rules) {
      this._formattingRules = Array.isArray(rules) ? rules.slice() : [];
      this._rebuildGridFormatting();
      this._isDirty = true;
      this._notifyLayoutChange();
    }

    getHeuristicsEnabled() {
      return this._heuristicsEnabled === true;
    }

    setHeuristicsEnabled(enabled) {
      const newVal = !!enabled;
      if (this._heuristicsEnabled === newVal) return;
      this._heuristicsEnabled = newVal;
      this._rebuildGridFormatting();
      this._isDirty = true;
      this._notifyLayoutChange();
    }

    /**
     * B+10+ (6.5.2026): build aggregate rowClassRules — heuristics (opt-in)
     * + compiled user rules. Helper pro _init + _rebuildGridFormatting.
     */
    _buildEffectiveRowClassRules() {
      const merged = {};
      if (this._heuristicsEnabled) {
        Object.assign(merged, _buildRowClassRules());
      }
      const Fmt = (typeof window !== "undefined") ? window.ErpGridFormatting : null;
      if (Fmt && this._formattingRules && this._formattingRules.length > 0) {
        const compiled = Fmt.compile(this._formattingRules, []);
        Object.assign(merged, compiled.rowClassRules);
      }
      return merged;
    }

    /**
     * B+10+ (6.5.2026): re-apply formatting state to AG Grid.
     * Calls gridApi.setColumnDefs + setGridOption("rowClassRules", ...).
     * Trigger po: layout load, user rules edit, heuristics toggle.
     */
    _rebuildGridFormatting() {
      if (this._destroyed || !this.gridApi) return;
      const Fmt = (typeof window !== "undefined") ? window.ErpGridFormatting : null;
      // Per-column cellClassRules from user formatting_rules
      const compiled = (Fmt && this._formattingRules && this._formattingRules.length > 0)
        ? Fmt.compile(this._formattingRules, [])
        : { cellClassRulesByCol: {}, rowClassRules: {} };
      // Get current column defs, rebuild s heuristics flag + user rules merged
      try {
        // Easiest path: re-build column defs from current rowData using
        // buildAutoColumnDefs + heuristicsEnabled flag, then merge user rules.
        const rowData = [];
        try {
          this.gridApi.forEachNode(node => { if (node.data) rowData.push(node.data); });
        } catch (e) {}
        const cols = this.options.columns ||
          (rowData.length > 0 ? Object.keys(rowData[0]) : []);
        const buildOpts = Object.assign({}, this.options, {
          heuristicsEnabled: this._heuristicsEnabled === true,
        });
        // Krok 5.U Fáze H++++ (23.5.2026): per-column formatting i pro
        // autoColumns:false grids — Marti's catch "obarvovaci schema se
        // v pickup komponente neaplikuje na grid".
        // Catalog picker (autoColumns:false, explicit opts.columns) měl
        // newDefs=null → per-column cellClassRules skip → grid bez obarveni.
        // Fix: pokud autoColumns false, klonuj current columnDefs z gridApi
        // (zachová explicit definitions caller's) + merge user rules.
        let newDefs = null;
        if (cols.length > 0 && this.options.autoColumns) {
          // Auto path — rebuild from rowData + heuristics
          newDefs = buildAutoColumnDefs(cols, rowData, buildOpts);
        } else {
          // Explicit columnDefs path (picker, custom grids) — clone current
          // defs aby merge user rules nebyl side-effect na caller's options.
          try {
            const currentDefs = this.gridApi.getColumnDefs() || [];
            newDefs = currentDefs.map(d => Object.assign({}, d));
          } catch (e) { /* fallback: žádný column rules apply */ }
        }
        // Merge per-column user rules into newDefs cellClassRules
        if (newDefs) {
          for (const def of newDefs) {
            const userRules = compiled.cellClassRulesByCol[def.field];
            if (userRules) {
              def.cellClassRules = Object.assign({}, def.cellClassRules || {}, userRules);
            }
          }
          this.gridApi.setGridOption("columnDefs", newDefs);
        }
        // Row-level: merge heuristics (opt-in) + user
        const effRowRules = this._buildEffectiveRowClassRules();
        this.gridApi.setGridOption("rowClassRules", effRowRules);
        // Force redraw to re-evaluate class rules immediately
        try { this.gridApi.redrawRows(); } catch (e) {}
      } catch (e) {
        console.warn("ErpDataGrid._rebuildGridFormatting failed:", e);
      }
    }

    /** Otevři formatting rules editor — modal s drag-drop priority listem. */
    async openFormattingEditor() {
      const Fmt = (typeof window !== "undefined") ? window.ErpGridFormatting : null;
      if (!Fmt) {
        alert("ErpGridFormatting nebyl naloaděn — zkontroluj <script src=\"/static/erp/datagrid_formatting.js\">");
        return;
      }
      // Build columns metadata pro editor (field + headerName + type)
      const colDefs = (this.gridApi && this.gridApi.getColumnDefs) ? this.gridApi.getColumnDefs() : [];
      const columnsMeta = colDefs
        .filter(c => c && c.field)
        .map(c => ({
          field: c.field,
          headerName: c.headerName || c.field,
          type: (c.cellDataType || "string"),
        }));
      const result = await Fmt.openEditor({
        rules: this._formattingRules,
        columns: columnsMeta,
        onSave: async (newRules) => {
          this.setFormattingRules(newRules);
        },
      });
      // result === null → user canceled, _formattingRules netknuté.
      // result === array → onSave proběhlo, state již updated.
      return result;
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
      // B+6.3+ (5.5.2026): native <select> nahrazen ErpDropdown — wire-up
      // proběhne v _refreshToolbar (lazy create instance do .erp-layout-mount).
      // Phase 38.4 Krok 5.R-C+7.3 (18.5.2026 vecer pozde, Marti's "pill
      // sama meni velikost pri scrolovani, paticka se trese"): fixed
      // min-width + borderless + zone separation + 24px gap.
      var _ci = this.options.coreInfo;
      var _ciLabel = "";
      if (_ci && _ci.coreId != null) {
        _ciLabel = String(_ci.coreId) + ":";
      }
      // Pill: borderless, monospace, min-width 90px (drzi "-110:23" i "30:1234567"),
      // tabular-nums (PROPORCIONALNI cislice — vzdy stejna sirka per digit).
      var _ciBtn = _ciLabel
        ? ('<div class="erp-toolbar-coreinfo-zone" style="display:flex;align-items:center;">' +
           '<button data-erp-coreinfo-btn ' +
           'class="erp-toolbar-coreinfo" ' +
           'title="Klik: info o jádru" ' +
           'style="min-width:90px;padding:4px 8px 4px 0;' +
           'background:transparent;border:none;color:#a8b4c2;' +
           'font-family:ui-monospace,Consolas,Monaco,monospace;' +
           'font-size:11px;font-weight:600;font-variant-numeric:tabular-nums;' +
           'text-align:left;cursor:pointer;border-radius:3px;' +
           'transition:background 0.15s,color 0.15s;">' +
           _ciLabel + '</button></div>' +
           '<div style="width:24px;flex:0 0 24px;"></div>')
        : "";
      return (
        '<div class="erp-toolbar-left" style="display:flex;align-items:center;">' +
          _ciBtn +
          '<div class="erp-toolbar-layout-zone" style="display:flex;align-items:center;">' +
            '<div class="erp-layout-mount" data-erp-layout-mount></div>' +
            '<span class="erp-dirty-indicator" data-erp-dirty hidden>*</span>' +
          '</div>' +
        '</div>' +
        '<div class="erp-toolbar-right">' +
          '<button class="erp-toolbar-btn" data-erp-fmt-btn ' +
            'title="Barevná pravidla (per layout)">🎨 Pravidla</button>' +
          '<button class="erp-toolbar-btn" data-erp-save-btn hidden ' +
            'title="Uložit změny do aktuální sestavy">💾 Uložit</button>' +
          '<button class="erp-toolbar-btn" data-erp-saveas-btn ' +
            'title="Uložit aktuální stav jako novou sestavu">+ Uložit jako…</button>' +
          '<button class="erp-toolbar-btn" data-erp-manage-btn ' +
            'title="Spravovat sestavy (rename, delete, set default)">⋮</button>' +
        '</div>'
      );
    }

    /**
     * B+10++++ (Marti's drobnost 6.5.2026 po návratu): přesun toolbar
     * elementu do AG Grid status baru — sloučení dvou řádek do jedné.
     *
     * AG Grid status bar má 3 zóny: left, center, right (přes statusBar
     * config s align). Custom statusPanel by chtěl rebuild z null. Místo
     * toho: DOM move existujícího toolbarEl do .ag-status-bar-left-panel.
     * Event listenery zachované (DOM appendChild = move).
     *
     * Fallback: pokud status bar element neexistuje (AG Grid neinitnul),
     * toolbar zůstane na své původní pozici (skrytý).
     */
    /**
     * Phase 38.4 (11.5.2026 vecer): pravý klik na status bar gridu vyvolá
     * akci 2/3 — Core přehledu. Marti's spec: footer = core přehledu,
     * řádek = jádro pro větu, soudeček v tree = soudeček + core mgmt.
     *
     * Gated na window._erpDesignMode (per-browser flag z footer dropdown).
     */
    _attachStatusBarDesignHandler() {
      if (!this.gridContainer || this._destroyed) return;
      var statusBar = this.gridContainer.querySelector(".ag-status-bar");
      if (!statusBar) return;  // Status bar disabled na tomto gridu
      if (statusBar._erpDesignAttached) return;  // Idempotent
      statusBar._erpDesignAttached = true;
      var self = this;
      statusBar.addEventListener("contextmenu", function (ev) {
        if (window._erpDesignMode !== true) return;  // Žádný handler mimo design mode
        // Pokud user pravý-klikl na toolbar (button, dropdown) — nechej
        // jeho own handler, neotevřej design alert.
        if (ev.target && ev.target.closest(".erp-grid-toolbar")) return;
        ev.preventDefault();
        var NL = String.fromCharCode(10);
        var gridCode = (self.options.gridCode)
          || (self.options.layoutKey ? String(self.options.layoutKey) : "-");
        var info = "Design akce 2/3: CORE PREHLEDU" + NL + NL +
          "Grid: " + gridCode + NL + NL +
          "Tato akce = editace core prehledu (sloupce, layout, default filter)." + NL +
          "Hardcoded form prijde priste." + NL + NL +
          "(Trigger: pravy klik na paticku gridu)";
        alert(info);
      });
    }

    _relocateToolbarToStatusBar(retryCount) {
      if (!this.toolbarEl || !this.gridContainer) return;
      retryCount = retryCount || 0;
      // AG Grid v32 status bar DOM:
      //   .ag-status-bar
      //     .ag-status-bar-left
      //       .ag-name-value (panels with align="left")
      //     .ag-status-bar-center
      //     .ag-status-bar-right
      const statusBar = this.gridContainer.querySelector(".ag-status-bar");
      if (!statusBar) {
        // Status bar mount může být later — retry max 5× (250ms total)
        if (retryCount < 5) {
          setTimeout(() => this._relocateToolbarToStatusBar(retryCount + 1), 50);
        }
        return;
      }
      const leftPanel = statusBar.querySelector(".ag-status-bar-left")
        || statusBar.querySelector(".ag-status-bar-left-panel")
        || statusBar;
      // Move toolbar do leftPanelu (DOM move = listenery zachované)
      this.toolbarEl.style.display = "";  // zviditelni
      leftPanel.insertBefore(this.toolbarEl, leftPanel.firstChild);
    }

    _updateCoreInfoPill(newRefId) {
      // Phase 38.4 Krok 5.R-C+7.1+7.2 (18.5.2026 vecer): dynamic update
      // pill text pri cell focus change. Dvojtecka VZDY, i bez rowId.
      // Krok 5.R-C+8: store rowId pro drop-up menu actions.
      if (!this.toolbarEl || !this.options.coreInfo) return;
      var btn = this.toolbarEl.querySelector("[data-erp-coreinfo-btn]");
      if (!btn) return;
      var ci = this.options.coreInfo;
      var coreId = ci.coreId;
      if (coreId == null) return;
      this._currentRowId = newRefId;  // Krok 5.R-C+8: store for menu actions
      var label = String(coreId) + ":";
      if (newRefId != null) label += String(newRefId);
      btn.textContent = label;
    }

    _showCoreInfoMenu(btn) {
      // Phase 38.4 Krok 5.R-C+8 (18.5.2026 vecer pozde): rozsireny drop-up
      // menu — info section + akce (Design jádra / Form řádku / Kopírovat).
      var ci = this.options.coreInfo || {};
      var oldMenu = document.querySelector(".erp-toolbar-coreinfo-menu");
      if (oldMenu) { oldMenu.remove(); return; }
      var rowId = this._currentRowId;
      var self = this;
      // Phase 38.4 Krok 5.R-C+8.2 (18.5.2026 vecer): append na document.body
      // s position:fixed — bypass AG Grid status bar overflow:hidden clipping.
      // Pozice pres getBoundingClientRect(btn) — viewport relative.
      var _btnRect = btn.getBoundingClientRect();
      var menu = document.createElement("div");
      menu.className = "erp-toolbar-coreinfo-menu";
      menu.style.cssText =
        "position:fixed;" +
        "bottom:" + (window.innerHeight - _btnRect.top + 4) + "px;" +
        "left:" + _btnRect.left + "px;" +
        "z-index:10000;" +
        "background:#1a2030;border:1px solid #3a4a6a;border-radius:4px;" +
        "padding:0;color:#e8eef5;font-size:11px;line-height:1.5;" +
        "box-shadow:0 -2px 8px rgba(0,0,0,0.4);min-width:260px;" +
        "font-family:ui-monospace,Consolas,Monaco,monospace;";

      // ── Info section
      var info = '<div style="padding:8px 12px;">';
      if (ci.coreLabel) info += '<div style="font-weight:600;margin-bottom:6px;color:#a8b4c2;font-family:system-ui,sans-serif;">' + this._escHtml(ci.coreLabel) + '</div>';
      var rows = [];
      if (ci.coreId != null) rows.push(["Core ID", String(ci.coreId)]);
      if (rowId != null) rows.push(["Row ID", String(rowId)]);
      if (ci.coreCode) rows.push(["Code", ci.coreCode]);
      if (ci.refId != null) rows.push(["Data src", String(ci.refId) + (ci.refCode ? " (" + ci.refCode + ")" : "")]);
      if (ci.rootCompDefId != null) rows.push(["Root cmp", String(ci.rootCompDefId) + (ci.rootTypeCode ? " (" + ci.rootTypeCode + ")" : "")]);
      if (ci.mode) rows.push(["Mode", ci.mode]);
      for (var i = 0; i < rows.length; i++) {
        info += '<div style="display:flex;gap:8px;"><span style="color:#7a8696;min-width:70px;">' +
          this._escHtml(rows[i][0]) + ':</span><code style="color:#7aa8d4;font-variant-numeric:tabular-nums;">' +
          this._escHtml(rows[i][1]) + '</code></div>';
      }
      if (ci.hardcoded) info += '<div style="color:#d4a878;margin-top:6px;font-style:italic;font-family:system-ui,sans-serif;">⚙ hardcoded grid</div>';
      info += '</div>';

      // ── Akce section
      var pillText = String(ci.coreId != null ? ci.coreId : "?") + ":" + (rowId != null ? rowId : "");
      var actions =
        '<div style="border-top:1px solid #2a3a5a;padding:4px 0;font-family:system-ui,sans-serif;">' +
        '<button type="button" data-erp-menu-action="design-core" ' +
          'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;">' +
          '🎨 Otevřít Design jádra</button>' +
        (ci.hardcoded || ci.coreId == null || ci.coreId < 0
          ? ''
          : '<button type="button" data-erp-menu-action="row-form" ' +
            'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;' +
            (rowId == null ? "opacity:0.4;cursor:not-allowed;" : "") + '" ' +
            (rowId == null ? "disabled" : "") + '>' +
            '🔗 Otevřít form řádku' + (rowId != null ? " #" + rowId : "") + '</button>') +
        '<button type="button" data-erp-menu-action="copy-id" ' +
          'style="display:block;width:100%;text-align:left;padding:6px 12px;background:transparent;border:none;color:#e8eef5;cursor:pointer;font-size:11px;">' +
          '📋 Kopírovat <code style="color:#7aa8d4;">' + this._escHtml(pillText) + '</code></button>' +
        '</div>';

      menu.innerHTML = info + actions;

      // Hover effect for action buttons
      var menuBtns = menu.querySelectorAll("button[data-erp-menu-action]");
      menuBtns.forEach(function (mb) {
        mb.addEventListener("mouseenter", function () {
          if (!mb.disabled) mb.style.background = "rgba(122,168,212,0.1)";
        });
        mb.addEventListener("mouseleave", function () { mb.style.background = "transparent"; });
        mb.addEventListener("click", function (ev) {
          ev.stopPropagation();
          var action = mb.getAttribute("data-erp-menu-action");
          self._handleMenuAction(action, ci, rowId, pillText, menu);
        });
      });

      // Append na document.body (bypass parent overflow clipping)
      document.body.appendChild(menu);
      var closeFn = function (e) {
        if (!menu.contains(e.target) && e.target !== btn) {
          menu.remove();
          document.removeEventListener("click", closeFn, true);
        }
      };
      setTimeout(function () { document.addEventListener("click", closeFn, true); }, 0);
    }

    _handleMenuAction(action, ci, rowId, pillText, menu) {
      // Phase 38.4 Krok 5.R-C+8 (18.5.2026): drop-up menu actions
      if (action === "copy-id") {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(pillText).then(function () {
              // Toast feedback
              var toast = document.createElement("div");
              toast.style.cssText =
                "position:absolute;bottom:8px;right:8px;z-index:1001;" +
                "background:#3a5a3a;color:#fff;padding:4px 10px;border-radius:3px;font-size:11px;";
              toast.textContent = "✓ Zkopírováno";
              menu.appendChild(toast);
              setTimeout(function () { try { toast.remove(); } catch (e) {} menu.remove(); }, 1200);
            });
          } else {
            console.warn("clipboard API unavailable");
            menu.remove();
          }
        } catch (e) { console.warn("clipboard write failed:", e); menu.remove(); }
        return;
      }
      if (action === "design-core") {
        // Phase 38.4 Krok 5.R-C+9 (18.5.2026 vecer pozde): resolve negative
        // synthetic coreId → positive fw.core row via /design/core-by-code
        // endpoint (Krok 5.R-C+5.1 backend fallback pres fw.menu_node.menu_node_pk).
        // Pro positive coreId (fw.core grid) — direct pass.
        menu.remove();
        if (ci.coreId == null) return;
        if (typeof window.DesignFwForm !== "function") {
          alert("DesignFwForm třída není načtena.");
          return;
        }
        var _openDesignFwForm = function (resolvedCoreId) {
          try {
            var fwf = new window.DesignFwForm({ coreId: 23, rowId: resolvedCoreId });
            if (typeof fwf.open === "function") fwf.open();
          } catch (e) {
            console.error("[coreinfo menu] DesignFwForm failed:", e);
            alert("Otevření Design jádra selhalo: " + (e.message || e));
          }
        };
        if (ci.coreId >= 0) {
          // Positive — direct pass, fw.core row existuje
          _openDesignFwForm(ci.coreId);
          return;
        }
        // Negative synthetic — resolve via fw.menu_node.menu_node_pk
        fetch("/api/v1/erp/design/core-by-code/" + encodeURIComponent("core_" + ci.coreId),
              { credentials: "include" })
          .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
          })
          .then(function (data) {
            if (data && data.core && data.core.id != null) {
              _openDesignFwForm(data.core.id);
            } else {
              alert("Tento hardcoded grid (core " + ci.coreId + ") nemá fw.core záznam.\n" +
                    "Synthetic ID by chtělo cleanup (task #18 — range conventions).");
            }
          })
          .catch(function (e) {
            console.error("[coreinfo menu] core-by-code resolve failed:", e);
            alert("Resolve core_id selhalo: " + (e.message || e));
          });
        return;
      }
      if (action === "row-form") {
        menu.remove();
        if (rowId == null) return;
        // Volat existing openFwFormForRow helper z router.py inline JS
        if (typeof window._openFwFormForRow === "function" && ci.coreId != null) {
          window._openFwFormForRow("core_" + ci.coreId, rowId, null);
        } else if (typeof window.DesignFwForm === "function" && ci.coreId != null) {
          // Fallback: direct DesignFwForm
          try {
            var fwf = new window.DesignFwForm({ coreId: ci.coreId, rowId: rowId });
            if (typeof fwf.open === "function") fwf.open();
          } catch (e) {
            console.error("[coreinfo menu] row-form failed:", e);
          }
        }
        return;
      }
    }

    _escHtml(s) {
      var div = document.createElement("div");
      div.textContent = String(s == null ? "" : s);
      return div.innerHTML;
    }

    _wireToolbar() {
      // Phase 38.4 Krok 5.R-C+8.1 hotfix (18.5.2026 vecer pozde): event
      // delegation z toolbarEl parent. Direct ciBtn.addEventListener
      // (Krok 5.R-C+7) nereagoval po deploy — pravdepodobne AG Grid CSS
      // layer suppression nebo render race po _relocateToolbarToStatusBar.
      // Delegation z parent je resilient k DOM moves + Enterprise layers.
      if (this.toolbarEl) {
        var selfPill = this;
        this.toolbarEl.addEventListener("click", function (ev) {
          var pillBtn = ev.target && ev.target.closest
            ? ev.target.closest("[data-erp-coreinfo-btn]")
            : null;
          if (pillBtn) {
            ev.stopPropagation();
            console.info("[ErpDataGrid pill] click delegated, opening menu");
            selfPill._showCoreInfoMenu(pillBtn);
          }
        });
      }
      // Phase 38.4 Krok 5.R-C+7.2: cellFocused wire moved to onGridReady
      // (gridApi neexistuje yet v _wireToolbar — sync vola _init pred
      // async onGridReady callback).
      if (!this.toolbarEl) return;
      // Layout dropdown handler je přidán uvnitř _refreshToolbar při lazy
      // ErpDropdown create (B+6.3+ refactor).
      const saveBtn = this.toolbarEl.querySelector("[data-erp-save-btn]");
      const saveAsBtn = this.toolbarEl.querySelector("[data-erp-saveas-btn]");
      const manageBtn = this.toolbarEl.querySelector("[data-erp-manage-btn]");

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

      // B+10+ (6.5.2026): formatting rules editor button
      const fmtBtn = this.toolbarEl.querySelector("[data-erp-fmt-btn]");
      if (fmtBtn) {
        fmtBtn.addEventListener("click", async () => {
          await this.openFormattingEditor();
        });
      }
    }

    /** Build items array pro ErpDropdown z listLayouts() result. */
    _buildLayoutItems(result) {
      const items = [{ value: "", label: "— bez sestavy —" }];
      if (result && result.shared && result.shared.length > 0) {
        items.push({ divider: true, label: "🔵 Sdílené" });
        for (const l of result.shared) {
          const star = l.is_default ? " ⭐" : "";
          items.push({ value: l.id, label: l.name + star });
        }
      }
      if (result && result.personal && result.personal.length > 0) {
        items.push({ divider: true, label: "👤 Moje" });
        for (const l of result.personal) {
          const star = l.is_default ? " ⭐" : "";
          items.push({ value: l.id, label: l.name + star });
        }
      }
      return items;
    }

    /** Refresh toolbar UI (dropdown items + button states). */
    async _refreshToolbar() {
      if (!this.toolbarEl) return;
      const mount = this.toolbarEl.querySelector("[data-erp-layout-mount]");
      const dirty = this.toolbarEl.querySelector("[data-erp-dirty]");
      const saveBtn = this.toolbarEl.querySelector("[data-erp-save-btn]");
      if (!mount) return;

      // Fetch list + build items
      const result = await this.listLayouts();
      const items = this._buildLayoutItems(result);
      const currentValue = (this._currentLayoutId != null) ? this._currentLayoutId : "";

      // Lazy-create / reuse ErpDropdown instance
      const HasErpDD = (typeof window !== "undefined" && typeof window.ErpDropdown === "function");
      const wrapperLost = this._layoutDropdown
        && this._layoutDropdown.wrapperElement
        && !mount.contains(this._layoutDropdown.wrapperElement());
      if (HasErpDD) {
        if (!this._layoutDropdown || wrapperLost) {
          if (this._layoutDropdown) {
            try { this._layoutDropdown.destroy(); } catch (e) {}
            this._layoutDropdown = null;
          }
          mount.innerHTML = "";
          this._layoutDropdown = new window.ErpDropdown(mount, {
            items: items,
            value: currentValue,
            placeholder: "— bez sestavy —",
            onChange: async (val) => {
              if (val === "" || val == null) {
                await this.resetToDefault();
                await this._refreshToolbar();
                return;
              }
              await this.loadLayoutById(parseInt(val, 10));
              await this._refreshToolbar();
            },
          });
        } else {
          this._layoutDropdown.setItems(items);
          this._layoutDropdown.setValue(currentValue, /*silent*/true);
        }
      } else {
        // Fallback — pokud ErpDropdown není načtený, render native select
        const optionsHtml = items.map(it => {
          if (it.divider) return '<optgroup label="' + this._escapeHtml(it.label || "") + '">';
          return '<option value="' + this._escapeHtml(String(it.value)) + '"' +
                 (it.value === currentValue ? ' selected' : '') + '>' +
                 this._escapeHtml(it.label) + '</option>';
        }).join("");
        mount.innerHTML = '<select class="erp-layout-select-fallback">' + optionsHtml + '</select>';
        const fallbackSel = mount.querySelector("select");
        if (fallbackSel && !fallbackSel._wired) {
          fallbackSel._wired = true;
          fallbackSel.addEventListener("change", async (ev) => {
            const id = ev.target.value;
            if (!id) { await this.resetToDefault(); await this._refreshToolbar(); return; }
            await this.loadLayoutById(parseInt(id, 10));
            await this._refreshToolbar();
          });
        }
      }

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

    // ── B+5.3.2: Custom dark theme modal helper ─────────────────────

    /**
     * Show custom modal dialog with dark theme.
     * Returns Promise resolving to button.value or null (Esc/cancel).
     *
     * opts: { title, bodyHtml, buttons: [{label, value, primary?, destructive?, handler?(modal)}] }
     */
    _showModal(opts) {
      return new Promise((resolve) => {
        const backdrop = document.createElement("div");
        backdrop.className = "erp-modal-backdrop";
        const modal = document.createElement("div");
        modal.className = "erp-modal";
        // Header (title + close ×) + body kontejner. Footer buttons appendneme přes ErpButton níže.
        modal.innerHTML =
          '<div class="erp-modal-header">' +
            '<h3>' + this._escapeHtml(opts.title || "") + '</h3>' +
            '<button class="erp-modal-close" type="button" aria-label="Zavřít">×</button>' +
          '</div>' +
          '<div class="erp-modal-body">' + (opts.bodyHtml || "") + '</div>' +
          '<div class="erp-modal-footer"></div>';
        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);
        // Krok 5.U Fáze H+H++ (23.5.2026): stack-aware z-index — Marti's catch
        // "Ulozit jako popup je schovany za pickerem" + "tolikrat klik = tolikrat
        // instance" potvrzuje modal SE OTEVÍRÁ ale je POD picker overlay.
        //
        // Default CSS z-index 200 je pod ErpCatalogPicker overlay (10010).
        // Picker overlay NEMÁ className (jen inline style v catalog_picker.js
        // line 134), takže className-based querySelector ho minul.
        //
        // Fix H++: skenuj VŠECHNY body-level children s computed
        // position:fixed (catches arbitrary overlays bez className), spočítej
        // max z-index, posuň o +10. Plus hard floor Math.max(_maxZ+10, 10020)
        // jako pojistka — vždy nad ErpCatalogPicker (10010) i kdyby scan selhal.
        try {
          const _bodyChildren = document.querySelectorAll("body > *");
          let _maxZ = 200;  // CSS fallback baseline
          _bodyChildren.forEach((el) => {
            if (el === backdrop) return;  // skip self
            const _s = window.getComputedStyle(el);
            if (_s.position !== "fixed") return;  // jen fixed-positioned overlays
            const z = parseInt(_s.zIndex, 10);
            if (!isNaN(z) && z > _maxZ) _maxZ = z;
          });
          // Hard floor 10020 — vždy nad ErpCatalogPicker (10010) i kdyby
          // scan nenašel žádný overlay (defensive).
          backdrop.style.zIndex = String(Math.max(_maxZ + 10, 10020));
        } catch (e) {
          // Last-resort fallback — hard-coded high value nad ErpCatalogPicker.
          backdrop.style.zIndex = "10020";
        }

        let resolved = false;
        const buttonInstances = [];  // ErpButton instances pro cleanup + Enter trigger

        const close = (val) => {
          if (resolved) return;
          resolved = true;
          document.removeEventListener("keydown", onKey);
          // Destroy ErpButton instances (uvolni listeners)
          buttonInstances.forEach(b => { try { b.destroy(); } catch (e) {} });
          backdrop.remove();
          resolve(val);
        };
        const onKey = (ev) => {
          if (ev.key === "Escape") close(null);
          else if (ev.key === "Enter" && ev.target.tagName !== "TEXTAREA") {
            // Find primary button → trigger jeho onClick
            const primaryIdx = (opts.buttons || []).findIndex(b => b.primary);
            if (primaryIdx >= 0 && buttonInstances[primaryIdx]) {
              ev.preventDefault();
              buttonInstances[primaryIdx].click();
            }
          }
        };

        modal.querySelector(".erp-modal-close").addEventListener("click", () => close(null));
        backdrop.addEventListener("click", (ev) => {
          if (ev.target === backdrop) close(null);
        });
        document.addEventListener("keydown", onKey);

        // Footer — render buttons přes ErpButton (B+6.1 dogfooding)
        const footer = modal.querySelector(".erp-modal-footer");
        const HasErpBtn = (typeof window !== "undefined" && typeof window.ErpButton === "function");
        (opts.buttons || []).forEach((b) => {
          const variant = b.primary
            ? "primary"
            : (b.destructive ? "destructive" : "secondary");
          const onClick = () => {
            try {
              const val = (typeof b.handler === "function") ? b.handler(modal) : b.value;
              close(val);
            } catch (e) {
              alert("Modal action error: " + (e.message || e));
              close(null);
            }
          };
          if (HasErpBtn) {
            const erpBtn = new window.ErpButton(footer, {
              label: b.label,
              variant: variant,
              size: "medium",
              onClick: onClick,
            });
            buttonInstances.push(erpBtn);
          } else {
            // Fallback — pokud ErpButton není načtený, fallback na nativní button
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "erp-btn" +
              (variant === "primary" ? " erp-btn-primary"
              : variant === "destructive" ? " erp-btn-destructive"
              : "");
            btn.textContent = b.label;
            btn.addEventListener("click", onClick);
            footer.appendChild(btn);
            // Stub instance (jen click() shim) aby Enter handler fungoval
            buttonInstances.push({ click: () => btn.click(), destroy: () => {} });
          }
        });

        // Auto-focus first input nebo primary button
        setTimeout(() => {
          const focusTarget =
            modal.querySelector(".erp-modal-body input, .erp-modal-body textarea, .erp-modal-body select");
          if (focusTarget) {
            focusTarget.focus();
            if (focusTarget.select) { try { focusTarget.select(); } catch (e) {} }
            return;
          }
          // Fallback — focus primary button (přes ErpButton.focus())
          const primaryIdx = (opts.buttons || []).findIndex(b => b.primary);
          if (primaryIdx >= 0 && buttonInstances[primaryIdx]) {
            const inst = buttonInstances[primaryIdx];
            if (typeof inst.focus === "function") {
              try { inst.focus(); } catch (e) {}
            } else if (inst.element) {
              try { inst.element().focus(); } catch (e) {}
            }
          }
        }, 60);
      });
    }

    /** Custom confirm dialog (Promise<boolean>). */
    _modalConfirm(opts) {
      return this._showModal({
        title: opts.title || "Potvrdit",
        bodyHtml:
          '<div class="erp-modal-field">' +
            '<p style="margin:0; line-height:1.5;">' + this._escapeHtml(opts.message || "") + '</p>' +
          '</div>',
        buttons: [
          { label: opts.cancelLabel || "Zrušit", value: false },
          {
            label: opts.confirmLabel || "OK",
            value: true,
            primary: !opts.destructive,
            destructive: !!opts.destructive,
          },
        ],
      }).then(v => v === true);
    }

    async _openSaveAsDialog() {
      const result = await this._showModal({
        title: "Uložit jako novou sestavu",
        bodyHtml:
          '<div class="erp-modal-field">' +
            '<label for="erp-save-name">Název sestavy:</label>' +
            '<input type="text" id="erp-save-name" placeholder="Můj pohled" maxlength="80">' +
          '</div>' +
          '<div class="erp-modal-field">' +
            '<label>Typ:</label>' +
            '<div class="erp-radio-group">' +
              '<label><input type="radio" name="erp-scope" value="user" checked> ' +
                '👤 Osobní <span class="erp-field-hint" style="display:inline; margin:0 0 0 4px;">— jen pro tebe</span></label>' +
              '<label><input type="radio" name="erp-scope" value="shared"> ' +
                '🔵 Sdílený <span class="erp-field-hint" style="display:inline; margin:0 0 0 4px;">— pro všechny uživatele (admin)</span></label>' +
            '</div>' +
          '</div>' +
          '<div class="erp-modal-field">' +
            '<div class="erp-checkbox-group">' +
              '<label><input type="checkbox" id="erp-save-default" checked> ' +
                '⭐ Označit jako výchozí <span class="erp-field-hint" style="display:inline; margin:0 0 0 4px;">— auto-load při otevření přehledu</span></label>' +
            '</div>' +
          '</div>',
        buttons: [
          { label: "Zrušit", value: null },
          {
            label: "Uložit",
            primary: true,
            handler: (m) => {
              const name = m.querySelector("#erp-save-name").value.trim();
              if (!name) {
                alert("Vyplň název sestavy.");
                return undefined;  // continues — but Promise resolves with undefined
              }
              const scope = m.querySelector("input[name='erp-scope']:checked").value;
              const isDefault = m.querySelector("#erp-save-default").checked;
              return { name, scope, isDefault };
            },
          },
        ],
      });
      if (!result || !result.name) return;
      try {
        await this.saveAsLayout(result);
        await this._refreshToolbar();
        this._toast("Sestava '" + result.name + "' vytvořena.");
      } catch (e) {
        this._toast("Chyba: " + (e.message || e), "error");
      }
    }

    async _openManagePanel() {
      const result = await this.listLayouts();
      if (!result) {
        this._toast("Nelze načíst seznam sestav.", "error");
        return;
      }
      const all = [
        ...(result.shared || []).map(l => ({...l, _section: "shared"})),
        ...(result.personal || []).map(l => ({...l, _section: "personal"})),
      ];

      let bodyHtml;
      if (all.length === 0) {
        bodyHtml = '<div class="erp-modal-empty">Zatím žádné uložené sestavy.<br>Vytvoř první přes <strong>+ Uložit jako…</strong></div>';
      } else {
        bodyHtml =
          '<table class="erp-modal-table">' +
            '<thead><tr>' +
              '<th>Název</th>' +
              '<th>Typ</th>' +
              '<th>Stav</th>' +
              '<th></th>' +
            '</tr></thead>' +
            '<tbody>' +
              all.map(l => {
                const isCurrent = (l.id === this._currentLayoutId);
                const cls = isCurrent ? ' class="erp-current"' : '';
                const typeIcon = l._section === "shared" ? "🔵 Sdílená" : "👤 Osobní";
                const stateBadges = [];
                if (l.is_default) stateBadges.push('⭐ výchozí');
                if (isCurrent) stateBadges.push('✓ aktivní');
                return (
                  '<tr' + cls + ' data-erp-row-id="' + l.id + '" data-erp-row-name="' + this._escapeHtml(l.name) + '">' +
                    '<td>' + this._escapeHtml(l.name) +
                      (l.description ? '<br><span style="font-size:11px;color:var(--muted)">' + this._escapeHtml(l.description) + '</span>' : '') +
                    '</td>' +
                    '<td>' + typeIcon + '</td>' +
                    '<td>' + stateBadges.join(", ") + '</td>' +
                    '<td><div class="erp-row-actions">' +
                      '<button class="erp-modal-action" data-erp-action="setdefault" ' +
                        (l.is_default ? 'disabled ' : '') + 'title="Označit jako výchozí">⭐</button>' +
                      '<button class="erp-modal-action" data-erp-action="rename" title="Přejmenovat">✏️</button>' +
                      '<button class="erp-modal-action destructive" data-erp-action="delete" title="Smazat">🗑️</button>' +
                    '</div></td>' +
                  '</tr>'
                );
              }).join("") +
            '</tbody>' +
          '</table>';
      }

      // Show modal s "table actions" handlers — modal nezavřeme po actionu, musíme refreshnout uvnitř
      let modalEl = null;
      const modalP = this._showModal({
        title: "Správa sestav",
        bodyHtml: bodyHtml,
        buttons: [
          { label: "Zavřít", value: null },
        ],
      });

      // Setup row action handlers — backdrop už je v DOMu
      modalEl = document.querySelector(".erp-modal-backdrop:last-of-type .erp-modal");
      if (modalEl) {
        modalEl.querySelectorAll("[data-erp-action]").forEach(btn => {
          btn.addEventListener("click", async (ev) => {
            ev.stopPropagation();
            const tr = btn.closest("tr[data-erp-row-id]");
            if (!tr) return;
            const id = parseInt(tr.getAttribute("data-erp-row-id"), 10);
            const name = tr.getAttribute("data-erp-row-name");
            const action = btn.getAttribute("data-erp-action");
            try {
              if (action === "setdefault") {
                await this.setDefaultLayout(id);
                this._toast("Sestava '" + name + "' je výchozí.");
              } else if (action === "rename") {
                const newName = await this._modalPrompt({
                  title: "Přejmenovat sestavu",
                  label: "Nový název:",
                  defaultValue: name,
                  maxLength: 80,
                });
                if (!newName || !newName.trim() || newName.trim() === name) return;
                await this._renameLayout(id, newName.trim());
                this._toast("Přejmenováno na '" + newName + "'.");
              } else if (action === "delete") {
                const ok = await this._modalConfirm({
                  title: "Smazat sestavu",
                  message: "Opravdu smazat sestavu '" + name + "'? Tato akce je nevratná.",
                  confirmLabel: "Smazat",
                  destructive: true,
                });
                if (!ok) return;
                await this.deleteLayout(id);
                this._toast("Sestava '" + name + "' smazána.");
              }
              // Close modal + refresh + reopen (jednoduchý refresh — UI re-renders)
              const backdrop = modalEl.closest(".erp-modal-backdrop");
              if (backdrop) backdrop.remove();
              await this._refreshToolbar();
              this._openManagePanel();  // re-open with fresh data
            } catch (e) {
              this._toast("Chyba: " + (e.message || e), "error");
            }
          });
        });
      }
      await modalP;
    }

    /** Custom prompt dialog (Promise<string|null>). */
    _modalPrompt(opts) {
      return this._showModal({
        title: opts.title || "Zadej hodnotu",
        bodyHtml:
          '<div class="erp-modal-field">' +
            (opts.label ? '<label for="erp-prompt-input">' + this._escapeHtml(opts.label) + '</label>' : '') +
            '<input type="text" id="erp-prompt-input" ' +
              'value="' + this._escapeHtml(opts.defaultValue || "") + '" ' +
              (opts.maxLength ? 'maxlength="' + opts.maxLength + '" ' : '') +
              (opts.placeholder ? 'placeholder="' + this._escapeHtml(opts.placeholder) + '" ' : '') +
            '>' +
          '</div>',
        buttons: [
          { label: "Zrušit", value: null },
          {
            label: opts.confirmLabel || "OK",
            primary: true,
            handler: (m) => {
              const v = m.querySelector("#erp-prompt-input").value;
              return v;
            },
          },
        ],
      });
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

    /** Toast notification — fixed bottom-right, dark theme. */
    _toast(msg, kind) {
      // B+5.3.2: fixed-position toast (žádné dependency na toolbar DOM)
      console.info("[ErpDataGrid]", msg);
      let toast = document.body.querySelector(".erp-toast-fixed");
      if (toast) toast.remove();
      toast = document.createElement("div");
      toast.className = "erp-toast-fixed" + (kind === "error" ? " erp-toast-error" : "");
      toast.textContent = msg;
      document.body.appendChild(toast);
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => {
        if (toast && toast.parentNode) {
          toast.style.opacity = "0";
          setTimeout(() => toast.remove(), 400);
        }
      }, 3000);
    }

    // ── Phase 38.4 Krok 14g-H+34 (22.5.2026 vecer): Excel mode toggle ────
    //
    // Per-grid feature, Marti's "dva toogle mody, nez to vsechno doladime".
    // Ctrl+Shift+E uvnitr gridu = toggle EXCEL <-> PROD mode.
    //
    //   PROD (default)  = AG editable=false, no inline cell edit
    //   EXCEL (servisni) = AG editable=true, AG default dvojklik = cell edit
    //
    // Bez persist (reset reload, vědomé zapnutí = servisní mód = bezpečnost).
    // Visual indikátor: orange pill v footer (coreId:rowId button).

    _setupExcelModeToggle() {
      if (this._destroyed || !this.container) return;
      this._onContainerKeydown = this._onContainerKeydown.bind(this);
      this.container.addEventListener("keydown", this._onContainerKeydown);
    }

    _onContainerKeydown(ev) {
      // Ctrl+Shift+E => toggle Excel mode (E case-insensitive)
      if (ev.ctrlKey && ev.shiftKey && (ev.key === "E" || ev.key === "e")) {
        ev.preventDefault();
        ev.stopPropagation();
        this._toggleExcelMode();
      }
    }

    _toggleExcelMode() {
      this._excelMode = !this._excelMode;
      const mode = this._excelMode ? "EXCEL" : "PROD";
      console.info("[ErpDataGrid] Mode switch:", mode, "layoutKey:", this.options.layoutKey);

      // 1) AG Grid editable update - refresh column defs in-place
      if (this.gridApi) {
        try {
          const colDefs = this.gridApi.getColumnDefs();
          if (Array.isArray(colDefs)) {
            colDefs.forEach(cd => {
              if (cd && typeof cd === "object") {
                cd.editable = this._excelMode;
              }
            });
            // AG v32+: setGridOption preferred; fallback setColumnDefs
            if (typeof this.gridApi.setGridOption === "function") {
              this.gridApi.setGridOption("columnDefs", colDefs);
            } else if (typeof this.gridApi.setColumnDefs === "function") {
              this.gridApi.setColumnDefs(colDefs);
            }
          }
        } catch (e) {
          console.warn("[ErpDataGrid] Excel mode AG refresh failed:", e);
        }
      }

      // 2) Pill orange in footer (coreId:rowId zone)
      this._applyExcelModePillStyle();

      // 3) Toast notification
      this._toast(
        this._excelMode
          ? "⚠ EXCEL mode ON — inline cell edit povolen (servisní)"
          : "🔒 PROD mode — editování gridu zakázáno",
        this._excelMode ? "error" : null
      );

      // 4) Krok 5.Y (23.5.2026): expose global Excel mode flag + fire event
      //    pro Save button visibility v grid toolbar (page_render.js listener).
      try {
        window._erpExcelMode = this._excelMode;
        window.dispatchEvent(new CustomEvent("erp:excel-mode-change", {
          detail: { excelMode: this._excelMode, layoutKey: this.options.layoutKey },
        }));
      } catch (_e) {}
    }

    _applyExcelModePillStyle() {
      if (!this.toolbarEl) return;
      const btn = this.toolbarEl.querySelector("[data-erp-coreinfo-btn]");
      if (!btn) return;
      if (this._excelMode) {
        // Warm amber/orange - "servisní mód, pozor"
        btn.style.background = "#d4a04a";
        btn.style.color = "#1a1410";
        btn.style.fontWeight = "700";
        btn.style.borderColor = "#a8782f";
        btn.title = "EXCEL mode ON — Ctrl+Shift+E pro návrat do PROD";
      } else {
        // Reset to default (inline styles cleared, CSS class takes over)
        btn.style.background = "";
        btn.style.color = "";
        btn.style.fontWeight = "";
        btn.style.borderColor = "";
        btn.title = "";
      }
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
      // B+6.3+ (5.5.2026): cleanup ErpDropdown layout selector
      if (this._layoutDropdown) {
        try { this._layoutDropdown.destroy(); } catch (e) {}
        this._layoutDropdown = null;
      }
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

  }); // _erpLoadModule end
})(typeof window !== "undefined" ? window : this);
