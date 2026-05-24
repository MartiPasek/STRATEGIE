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
    // (musí odpovídat fw.data_source.id pro validátor + fw.comp_grid lookup +
    // coreInfo.coreId pro footer pill).
    var FW_DATA_SOURCE_CODE = "system_new.framework_data_source_ops";
    var FW_DATA_SOURCE_ID = 44;
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

      // Marti's 24.5.2026 vecer doctrine: uniform parity s master grid path
      // (page_render.js line 401-419). Pre-fetch data + layout přes Promise.all,
      // předat initialLayout do ErpDataGrid → AG Grid použije initialState.
      // columnState authority při startup, žádný late _applyLayout race
      // (saved widths drží pixel-perfect od prvního renderu).
      //
      // Marti's intuice: "v master fw gridu jsi injectnul zvenku coreInfo +
      // initialLayout, detail grid path je asymmetrický → widths broken".
      // Fix = uniform pre-fetch flow, ne patch _applyLayout pozdě po reflow.
      var dataUrl = "/api/v1/erp/data/" + encodeURIComponent(FW_DATA_SOURCE_CODE) +
                    "?master_id=" + encodeURIComponent(masterId);
      var layoutUrl = "/api/v1/erp/grid-layout/" + encodeURIComponent(FW_LAYOUT_KEY) + "/list";
      console.log("[ErpDataSourceOpDetailRenderer] fetch FW data + layout:", dataUrl, "+", layoutUrl);

      Promise.all([
        fetch(dataUrl, { credentials: "same-origin" }).then(function (r) { return r.json(); }),
        fetch(layoutUrl, { credentials: "same-origin" }).then(function (r) { return r.json(); })
                                                         .catch(function () { return null; }),
      ])
        .then(function (results) {
          var dataJson = results[0];
          var layoutList = results[1];
          // data_source_runner response shape: { ok, rows, columns, ... }
          var rows = (dataJson && dataJson.ok && Array.isArray(dataJson.rows)) ? dataJson.rows : [];
          // grid-layout/list response shape: { ok, shared:[], personal:[], effective_default }
          var initialLayout = (layoutList && layoutList.ok && layoutList.effective_default)
                              ? layoutList.effective_default : null;
          console.log("[ErpDataSourceOpDetailRenderer] received", rows.length,
                      "ops pro masterId=" + masterId,
                      "+ layout=", initialLayout ? ("#" + initialLayout.id + " '" + initialLayout.name + "'") : "(none)");

          // Vytvoř nested ErpDataGrid s plnou paletou features
          try {
            self._nestedGrid = new window.ErpDataGrid(self._eGui, {
              rowData: rows,

              // FW layout persistence — uniform parity s master grid:
              //   - layoutKey: fw.comp_grid scope key (ds_44)
              //   - initialLayout: pre-fetched saved sestava (master path)
              //     → AG Grid použije initialState.columnState authority při
              //     startup, applyColumnState s saved widths PRED prvním
              //     renderem (žádný container-fit override race).
              //     Plus onFirstDataRendered fix #11 path s 300ms re-apply
              //     LOCK pro reflow protection (active jen pokud initialLayout).
              //   - autoLoadDefault DROP: initialLayout ho zastupuje, AG Grid
              //     hasInitialLayout short-circuit by autoLoadDefault stejně skipl.
              //   - autoColumns: fallback build z first row keys pokud
              //     initialLayout=null (žádná saved sestava ještě neexistuje).
              layoutKey: FW_LAYOUT_KEY,
              initialLayout: initialLayout,
              autoColumns: true,                // fallback pokud initialLayout=null

              enableFilters: true,              // floating filter + glow + popup
              rowSelection: "single",           // single row selection v detail
              compact: true,                    // rowHeight 26, headerHeight 32

              // Marti's 24.5.2026 catch po Volba A: pill v paticce
              // (IDCore + IDref) je native ErpDataGrid feature ovládaná
              // přes options.coreInfo. Master grid path (page_render.js)
              // ho injektne, detail nested grid musí taky.
              //   - coreId: fw.data_source.id detail chain (44)
              //   - refId: master row id (jeden z fw.data_source rows)
              //   - coreCode: FW chain code (system_new.framework_data_source_ops)
              //   - coreLabel: human-readable per master row
              coreInfo: {
                coreId: FW_DATA_SOURCE_ID,
                refId: masterId,
                coreCode: FW_DATA_SOURCE_CODE,
                coreLabel: "Operace data sourcu #" + masterId,
              },

              // Marti's 24.5.2026 catch: nested grids s saved layoutem
              // si nepřejí flex distribution — sloupce by se "analogicky
              // roztáhli na celou šířku gridu" i přes saved widths.
              // disableColumnFlex=true → buildAutoColumnDefs cols bez flex +
              // suppressSizeToFit + skip sizeColumnsToFit() v init/resize.
              disableColumnFlex: true,

              // Universal CRUD Etapa F (24.5.2026 vecer Marti's "tlacitka
              // musi byt zevnitr fw komponenty"): nested detail grid taky
              // dostane vlastni CRUD toolbar. Pro ted: zadne ops (data_source_op
              // nema vlastni ops zatim) -> gridActions vsechny false -> 4
              // buttons visible, 3 disabled, jen Obnovit aktivni. Drz
              // "stejne zobrazit, stejne funkce" napric master + detail.
              gridActions: {
                has_insert: false,
                has_edit: false,
                has_delete: false,
                edit_core_id: null,
              },
              contextMenuActions: ["create", "edit", "delete", "refresh"],

              // Refresh callback - ErpDataGrid internal Obnovit button vola
              // tento handler. Re-fetch ops rows pro tohohle master_id.
              onRefresh: function () {
                try {
                  fetch(dataUrl, { credentials: "same-origin" })
                    .then(function (r) { return r.json(); })
                    .then(function (j) {
                      if (j && j.ok && Array.isArray(j.rows) && self._nestedGrid
                          && self._nestedGrid.gridApi) {
                        self._nestedGrid.gridApi.setGridOption("rowData", j.rows);
                      }
                    });
                } catch (e) {
                  console.warn("[detail onRefresh]", e);
                }
              },

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
