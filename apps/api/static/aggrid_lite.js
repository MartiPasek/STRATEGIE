/* aggrid_lite.js — sdílený wrapper nad AG Grid pro finanční přehledy. Marti 25.6.2026.
 * Načte AG Grid ENTERPRISE z cdnjs (fallback Community), quartz-dark.
 * Enterprise (po koupi licence) automaticky zapne: set-filtry (Excel styl),
 *   postranní panel sloupců+filtrů, seskupování přetažením, status bar se součty,
 *   export do Excelu. Community: základní filtry + CSV.
 * LICENCE: vlož klíč do window.AG_GRID_LICENSE_KEY (např. malým <script> na stránce
 *   nebo přes /static/ag_license.js). Bez klíče Enterprise běží v trialu (vodoznak).
 * API: AGLite.mount(el, columnDefs, rowData, {csvName,onRowClick,quickFilter,height,
 *   pageSize,grouping,totals:[poleNaSoucet]}) → gridApi. + AGLite.fmt {czk,num,yn}.
 */
(function () {
  const V = "32.2.0";
  const COMM = "https://cdnjs.cloudflare.com/ajax/libs/ag-grid/" + V;          // styles + community JS
  const ENTJS = "https://cdn.jsdelivr.net/npm/ag-grid-enterprise@" + V + "/dist/ag-grid-enterprise.min.js";
  let _ready = null;
  let ENT = false;

  function _css(href) {
    return new Promise((res) => {
      if (document.querySelector('link[href="' + href + '"]')) return res();
      const l = document.createElement("link");
      l.rel = "stylesheet"; l.href = href; l.onload = res; l.onerror = res;
      document.head.appendChild(l);
    });
  }
  function _js(src) {
    return new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }
  function ensure() {
    if (_ready) return _ready;
    _ready = (async () => {
      await _css(COMM + "/styles/ag-grid.css");
      await _css(COMM + "/styles/ag-theme-quartz.css");
      if (typeof window.agGrid === "undefined") {
        // Enterprise jen když je k dispozici licenční klíč (jinak Community = bez vodoznaku).
        if (window.AG_GRID_LICENSE_KEY) {
          try { await _js(ENTJS); } catch (e) { /* fallback níže */ }
        }
        if (typeof window.agGrid === "undefined") {
          await _js(COMM + "/ag-grid-community.min.js");
        }
      }
      ENT = !!(window.agGrid && window.agGrid.LicenseManager);
      if (ENT && window.AG_GRID_LICENSE_KEY) {
        try { window.agGrid.LicenseManager.setLicenseKey(window.AG_GRID_LICENSE_KEY); } catch (e) {}
      }
      if (!document.getElementById("aglite-style")) {
        const st = document.createElement("style");
        st.id = "aglite-style";
        st.textContent = `
          .aglite-wrap{display:flex;flex-direction:column;gap:8px}
          .aglite-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
          .aglite-q{flex:1;min-width:160px;max-width:360px;background:#0f1420;color:#e8edf6;
            border:1px solid #2a3547;border-radius:8px;padding:7px 11px;font-size:13px}
          .aglite-btn{background:#27313f;color:#cdd9ea;border:0;border-radius:8px;padding:7px 12px;
            font-size:12.5px;cursor:pointer}
          .aglite-btn:hover{background:#2f3b4d}
          .aglite-cnt{color:#8295ad;font-size:12px;margin-left:auto}
          .ag-theme-quartz-dark{--ag-background-color:#121826;--ag-header-background-color:#161d2c;
            --ag-odd-row-background-color:#141b29;--ag-row-hover-color:#1b2740;--ag-border-color:#232c3b;
            --ag-font-size:12.5px;--ag-font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
            --ag-foreground-color:#e8edf6;--ag-header-foreground-color:#8fa3bd;--ag-accent-color:#2563eb;
            --ag-row-border-color:#232c3b;--ag-cell-horizontal-padding:10px;--ag-header-height:36px;
            --ag-row-height:32px;--ag-control-panel-background-color:#161d2c}
          .aglite-link{color:#7fb0ff;text-decoration:underline;cursor:pointer}
          .aglite-clickrow:hover{cursor:pointer}
        `;
        document.head.appendChild(st);
      }
    })();
    return _ready;
  }

  async function mount(el, columnDefs, rowData, opts) {
    opts = opts || {};
    await ensure();
    if (typeof el === "string") el = document.getElementById(el);
    el.innerHTML = "";
    el.classList.add("aglite-wrap");
    const bar = document.createElement("div"); bar.className = "aglite-bar";
    let q = null;
    if (opts.quickFilter !== false) {
      q = document.createElement("input"); q.className = "aglite-q";
      q.placeholder = "🔎 Hledat ve všech sloupcích…"; bar.appendChild(q);
    }
    const expBtn = document.createElement("button"); expBtn.className = "aglite-btn";
    expBtn.textContent = ENT ? "⬇ Export Excel" : "⬇ Export CSV"; bar.appendChild(expBtn);
    const cnt = document.createElement("span"); cnt.className = "aglite-cnt"; bar.appendChild(cnt);
    el.appendChild(bar);
    const host = document.createElement("div");
    host.className = "ag-theme-quartz-dark";
    host.style.width = "100%";
    host.style.height = (opts.height || "calc(100vh - 240px)");
    el.appendChild(host);

    const go = {
      columnDefs: columnDefs,
      rowData: rowData || [],
      defaultColDef: {
        sortable: true, resizable: true, floatingFilter: true, minWidth: 70, flex: 1,
        filter: ENT ? "agSetColumnFilter" : true,
        enableRowGroup: ENT && opts.grouping !== false,
      },
      animateRows: true, rowHeight: 32, headerHeight: 36,
      enableCellTextSelection: true, ensureDomOrder: true,
      pagination: !!opts.pageSize, paginationPageSize: opts.pageSize || undefined,
      onModelUpdated: (e) => { try { cnt.textContent = e.api.getDisplayedRowCount() + " řádků"; } catch (x) {} },
    };
    // MASTER-DETAIL (vnořitelný) — jedna šablona pro všechny drill-down přehledy.
    // opts.masterDetail = { cols:[detailColDefs], load:fn(parentRow)->Promise([rows]),
    //   detail:{ cols, load, detail... } }  (rekurzivně pro víc úrovní; vyžaduje Enterprise)
    function _md(md) {
      var dgo = {
        columnDefs: md.cols,
        defaultColDef: { sortable: true, resizable: true, filter: ENT ? "agSetColumnFilter" : true, floatingFilter: false, flex: 1, minWidth: 70 },
        detailRowAutoHeight: true, rowHeight: 30, headerHeight: 32,
      };
      if (md.detail) { dgo.masterDetail = true; dgo.detailCellRendererParams = _md(md.detail); }
      return {
        detailGridOptions: dgo,
        getDetailRowData: function (p) {
          try { md.load(p.data).then(function (rows) { p.successCallback(rows || []); }); }
          catch (e) { p.successCallback([]); }
        },
      };
    }
    if (opts.masterDetail && ENT) {
      go.masterDetail = true;
      go.detailRowAutoHeight = true;
      go.detailCellRendererParams = _md(opts.masterDetail);
    }
    if (ENT) {
      go.sideBar = { toolPanels: ["columns", "filters"], position: "right" };
      if (opts.grouping !== false) go.rowGroupPanelShow = "always";
      if (opts.totals && opts.totals.length) {
        go.statusBar = { statusPanels: [
          { statusPanel: "agTotalAndFilteredRowCountComponent", align: "left" },
          { statusPanel: "agAggregationComponent", align: "right" },
        ] };
      }
    }
    if (opts.onRowClick) {
      go.onRowClicked = (ev) => {
        if (ev.event && ev.event.target && ev.event.target.closest && ev.event.target.closest("a")) return;
        opts.onRowClick(ev.data, ev);
      };
      go.rowClass = "aglite-clickrow";
    }
    const api = window.agGrid.createGrid(host, go);
    if (q) q.addEventListener("input", () => api.setGridOption("quickFilterText", q.value));
    expBtn.addEventListener("click", () => {
      const name = (opts.csvName || "export");
      if (ENT && api.exportDataAsExcel) api.exportDataAsExcel({ fileName: name + ".xlsx" });
      else api.exportDataAsCsv({ fileName: name + ".csv" });
    });
    return api;
  }

  const fmt = {
    czk: (p) => (p.value == null ? "" : Number(p.value).toLocaleString("cs-CZ", { maximumFractionDigits: 0 }) + " Kč"),
    num: (p) => (p.value == null ? "" : Number(p.value).toLocaleString("cs-CZ")),
    yn: (p) => (p.value ? "Ano" : (p.value === false ? "Ne" : "")),
  };

  window.AGLite = { ensure, mount, fmt, isEnterprise: () => ENT };
})();
