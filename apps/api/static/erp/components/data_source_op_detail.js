/*
 * ErpDataSourceOpDetailRenderer
 * ─────────────────────────────────────────────────────────────────────
 * Custom AG Grid detail cell renderer pro master-detail pattern
 * (Marti's 24.5.2026 vecer — Volba A: drop HW, postavit FW chain).
 *
 * Použití (z page_render.js MASTER_DETAIL_REGISTRY):
 *
 *   "framework_data_sources": {
 *     detailCellRenderer: window.ErpDataSourceOpDetailRenderer,
 *     detailRowHeight: 180,
 *   },
 *
 * Renderer fetchne ops přes generic data_source_runner endpoint:
 *   /api/v1/erp/data/system_new.framework_data_source_ops?master_id={X}
 *
 * (FW chain: fw.data_set + fw.data_source + fw.data_source_op,
 *  deploy 24.5.2026, data_source.id = 44. SQL s :master_id bind param.)
 *
 * Nested ErpDataGrid s plnou paletou features:
 *   - layoutKey "ds_44" (validní formát fw.data_source.id)
 *     → nativní persistence sloupců přes fw.comp_grid (žádná nová tabulka)
 *   - autoLoadDefault: true (restore last saved sestava per layoutKey)
 *   - autoColumns: true (fallback build z first row keys pokud žádná sestava)
 *   - compact: true (rowHeight 26, headerHeight 32)
 *   - enableFilters: true (floating filter row + glow + pravý-klik popup)
 *   - enableMasterDetail: false (kaskáda level 2 přijde later)
 *
 * Marti's "fw self edited" doctrine (11.5.) — vše skrz fw infrastruktura,
 * nehardcodovat. Drop HW endpoint /design/fw-data-source/{id}/operations.
 *
 * Wrapped v _erpLoadModule pattern (Module Health visibility).
 */
(function () {
  "use strict";

  var loader = (typeof window !== "undefined" && window._erpLoadModule)
    ? window._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "]", e); } };

  loader("data_source_op_detail.js", "v2.0.0", function () {

    // FW chain code + layoutKey — deploy 24.5.2026 (data_source.id = 44).
    // Pokud někdy bude potřeba změnit code, změnit i layoutKey společně
    // (musí odpovídat fw.data_source.id pro validátor + fw.comp_grid lookup).
    var FW_DATA_SOURCE_CODE = "system_new.framework_data_source_ops";
    var FW_LAYOUT_KEY = "ds_44";

    function ErpDataSourceOpDetailRenderer() {}

    ErpDataSourceOpDetailRenderer.prototype.init = function (params) {
      var self = this;
      var masterRow = params.data || {};
      var masterId = masterRow.id || masterRow.Id || masterRow.ID;

      // Container — full width, fixed height per detailRowHeight option.
      // Padding & border styling pres CSS .ag-full-width-row.ag-row-level-1
      // + .erp-data-source-op-detail (Marti's 24.5.2026 v6 — Quartz v32+ class).
      self._eGui = document.createElement("div");
      self._eGui.className = "erp-data-source-op-detail";
      // height 100% (vyplnit detail row container fully).
      // Pari s detailRowHeight:180 fixed v page_render.js (autoHeight měl
      // timing race s async fetch → detail row stayed 0px).
      self._eGui.style.cssText = "width:100%; height:100%; box-sizing:border-box;";

      if (!masterId) {
        self._eGui.innerHTML = '<div style="padding:12px;color:var(--muted,#8a8d96);">' +
          '⚠ Master row nemá ID — detail nelze fetchovat.</div>';
        return;
      }

      // Ověř, že ErpDataGrid class je dostupný
      if (typeof window.ErpDataGrid !== "function") {
        self._eGui.innerHTML = '<div style="padding:12px;color:var(--danger,#e57373);">' +
          '⚠ ErpDataGrid komponenta není načtena (datagrid.js missing).</div>';
        return;
      }

      // Generic data_source_runner endpoint s :master_id bind param.
      // FW chain (fw.data_set + fw.data_source + fw.data_source_op) deploy 24.5.2026.
      var url = "/api/v1/erp/data/" + encodeURIComponent(FW_DATA_SOURCE_CODE) +
                "?master_id=" + encodeURIComponent(masterId);
      console.log("[ErpDataSourceOpDetailRenderer] fetch FW:", url);

      fetch(url, { credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (json) {
          // data_source_runner response shape: { ok, rows, columns, ... }
          var rows = (json && json.ok && Array.isArray(json.rows)) ? json.rows : [];
          console.log("[ErpDataSourceOpDetailRenderer] received", rows.length,
                      "ops pro masterId=" + masterId);

          // Vytvoř nested ErpDataGrid s plnou paletou features
          try {
            self._nestedGrid = new window.ErpDataGrid(self._eGui, {
              rowData: rows,

              // FW layout persistence — fw.comp_grid lookup per layoutKey.
              // Validní formát "ds_<fw.data_source.id>" prochází validatorem.
              // autoLoadDefault: true → restore user's last saved sestava (sloupce,
              // šířky, sort, filters, formatting rules). Pokud žádná sestava
              // ještě neexistuje, fallback na autoColumns (build z first row keys).
              layoutKey: FW_LAYOUT_KEY,
              autoLoadDefault: true,
              autoColumns: true,                // fallback pokud žádná saved sestava

              enableFilters: true,              // floating filter + glow + popup
              rowSelection: "single",           // single row selection v detail
              compact: true,                    // rowHeight 26, headerHeight 32

              // Marti's 24.5.2026 catch: nested grids s saved layoutem
              // si nepřejí flex distribution — sloupce by se "analogicky
              // roztáhli na celou šířku gridu" i přes saved widths.
              // disableColumnFlex=true → buildAutoColumnDefs cols bez flex +
              // suppressSizeToFit + skip sizeColumnsToFit() v init/resize.
              disableColumnFlex: true,

              // Disable kaskáda zatím (level 2 = data_set přijde later)
              enableMasterDetail: false,
            });
          } catch (e) {
            console.warn("[ErpDataSourceOpDetailRenderer] nested grid create failed:", e);
            self._eGui.innerHTML = '<div style="padding:12px;color:var(--danger,#e57373);">' +
              '⚠ Detail grid create failed: ' + (e.message || e) + '</div>';
          }
        })
        .catch(function (err) {
          console.warn("[ErpDataSourceOpDetailRenderer] fetch failed:", url, err);
          self._eGui.innerHTML = '<div style="padding:12px;color:var(--danger,#e57373);">' +
            '⚠ Fetch ops failed: ' + (err.message || err) + '</div>';
        });
    };

    ErpDataSourceOpDetailRenderer.prototype.getGui = function () {
      return this._eGui;
    };

    ErpDataSourceOpDetailRenderer.prototype.destroy = function () {
      // Cleanup nested grid (memory) když master row collapse
      if (this._nestedGrid) {
        try {
          if (typeof this._nestedGrid.destroy === "function") {
            this._nestedGrid.destroy();
          }
        } catch (e) {
          console.warn("[ErpDataSourceOpDetailRenderer] destroy nested failed:", e);
        }
        this._nestedGrid = null;
      }
      this._eGui = null;
    };

    // Export na window pro page_render.js MASTER_DETAIL_REGISTRY
    window.ErpDataSourceOpDetailRenderer = ErpDataSourceOpDetailRenderer;

    console.log("[ErpDataSourceOpDetailRenderer] registered (v2.0.0 — FW chain)");
  });
})();
