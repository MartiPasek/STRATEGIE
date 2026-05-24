/*
 * ErpDataSourceOpDetailRenderer
 * ─────────────────────────────────────────────────────────────────────
 * Custom AG Grid detail cell renderer pro master-detail pattern
 * (Marti's 24.5.2026 Krok 6 — Varianta B nested ErpDataGrid).
 *
 * Použití (z page_render.js MASTER_DETAIL_REGISTRY):
 *
 *   "framework_data_sources": {
 *     detailCellRenderer: function() {
 *       return new window.ErpDataSourceOpDetailRenderer();
 *     },
 *     detailRowHeight: 240,
 *   },
 *
 * Renderer fetch ops přes /api/v1/erp/design/fw-data-source/{id}/operations
 * + vytvoří nested ErpDataGrid s plnou paletou features:
 *   - layoutKey "data_source_op" (SHARED napříč všech master rows)
 *   - autoLoadDefault: true (restore last sestava)
 *   - autoColumns: true (auto-build z first row keys)
 *   - compact: true (rowHeight 26, headerHeight 32)
 *   - enableFilters: true (floating filter row + glow + pravý-klik popup)
 *   - enableMasterDetail: false (kaskáda level 2 přijde later)
 *
 * Wrapped v _erpLoadModule pattern (Module Health visibility).
 */
(function () {
  "use strict";

  var loader = (typeof window !== "undefined" && window._erpLoadModule)
    ? window._erpLoadModule
    : function (id, ver, fn) { try { fn(); } catch (e) { console.error("[" + id + "]", e); } };

  loader("data_source_op_detail.js", "v1.0.0", function () {

    function ErpDataSourceOpDetailRenderer() {}

    ErpDataSourceOpDetailRenderer.prototype.init = function (params) {
      var self = this;
      var masterRow = params.data || {};
      var masterId = masterRow.id || masterRow.Id || masterRow.ID;

      // Container — full width, fixed height per detailRowHeight option.
      // Padding & border styling pres CSS .ag-details-row + .ag-details-grid
      // (Marti's 24.5.2026 Krok 5 polish).
      self._eGui = document.createElement("div");
      self._eGui.className = "erp-data-source-op-detail";
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

      var url = "/api/v1/erp/design/fw-data-source/" + encodeURIComponent(masterId) + "/operations";
      console.log("[ErpDataSourceOpDetailRenderer] fetch:", url);

      fetch(url, { credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (json) {
          var rows = (json && json.ok && Array.isArray(json.rows)) ? json.rows : [];
          console.log("[ErpDataSourceOpDetailRenderer] received", rows.length, "ops pro masterId=" + masterId);

          // Vytvoř nested ErpDataGrid s plnou paletou features
          try {
            self._nestedGrid = new window.ErpDataGrid(self._eGui, {
              rowData: rows,
              autoColumns: true,                // build columns z first row keys
              enableFilters: true,              // floating filter + glow + popup
              rowSelection: "single",           // single row selection v detail
              compact: true,                    // rowHeight 26, headerHeight 32

              // SHARED layout napříč VŠECH master rows (Marti's spec 3)
              layoutKey: "data_source_op",
              gridCode: "data_source_op",
              autoLoadDefault: true,            // restore default sestava

              // Disable kaskáda zatím (level 2 = data_set přijde later)
              enableMasterDetail: false,

              // Compact toolbar — pokud má toolbar, je v statusbaru via layoutKey
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

    console.log("[ErpDataSourceOpDetailRenderer] registered (v1.0.0)");
  });
})();
