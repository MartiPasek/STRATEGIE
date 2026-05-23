/**
 * page_render.js — generic page render pro fw.core+comp_def kontejnery
 *
 * Phase 38.4 Krok 5.R (17.5.2026 vecer, Marti's "JO, melo by to byt v
 * nezavislem js. TJ ten 5/5"):
 *   Klik na soudecek s coreId → fetch /fw-core/{id}/page-spec → dispatch
 *   podle root_comp_def.type_code (grid_modern/list → empty grid, form →
 *   form preview, drafted → "no root yet" placeholder).
 *
 * Architektura:
 *   - Standalone JS module (gotcha #100 — inline JS v router.py je krehky)
 *   - _erpLoadModule wrap (banner X/Y mod count)
 *   - Namespace window.ErpPageRender
 *   - Public API: dispatchPageRender(coreId, coreCode, tab, mainContent)
 *
 * Long-term (5.R-C/D/E):
 *   5.R-C: comp_def children s region_slot='column' → ErpDataGrid columnDefs
 *   5.R-D: data_source_id → fetch /api/v1/erp/data/{ds_code} → rowData
 *   5.R-E: form/frameless_form embedded render v page area
 */
(function (global) {
  "use strict";

  const _loader = (typeof global._erpLoadModule === "function")
    ? global._erpLoadModule
    : function (id, version, fn) { try { fn(); } catch (e) { console.error(id, e); } };

  const _logger = (typeof global._erpLogToDb === "function")
    ? { warn: (mod, msg, ctx) => global._erpLogToDb("warn", mod, msg, ctx),
        error: (mod, msg, ctx) => global._erpLogToDb("error", mod, msg, ctx) }
    : { warn: () => {}, error: () => {} };

  _loader("page_render.js", "v1.0.0", function () {

    // Defensive escapeHtml — pokud parent context ho ma, reuse, jinak fallback
    function _esc(s) {
      if (typeof global.escapeHtml === "function") return global.escapeHtml(s);
      const div = document.createElement("div");
      div.textContent = String(s == null ? "" : s);
      return div.innerHTML;
    }

    // ─── Render helpers ──────────────────────────────────────────────

    function _renderDraftedPlaceholder(mainContent, tab, coreCode, coreId) {
      mainContent.innerHTML =
        '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
        '<h2 style="margin:0 0 12px;font-weight:500;color:#e8eef5;">📊 ' +
        _esc(tab.label || "Přehled") + '</h2>' +
        '<p style="color:#a8b4c2;margin:0 0 8px;">' +
        'Asociovaný core: <strong>' + _esc(coreCode || "?") +
        '</strong> (id=' + coreId + ')</p>' +
        '<p style="color:#7a8696;font-size:13px;margin:0;">' +
        '⚠ Core je drafted — bez root komponenty. ' +
        'Pravý-klik → 🎨 Design → vybrat root type (form/grid/...).' +
        '</p></div>';
    }

    function _renderEmptyGrid(mainContent, tab, rootCd, coreId, specForRender) {
      // Phase 38.4 Krok 5.R-D (18.5.2026 rano, Marti's "zasadni posun v Gridu"):
      // real ErpDataGrid s data_source rows. AG Grid autoColumns=true → sam
      // detect columns z prvniho row keys (Marti's doctrine "nativni grid
      // inteligentni sam od sebe").
      const dsInfo = rootCd.data_source_id
        ? ' · data_source #' + rootCd.data_source_id +
          (rootCd.data_source_code ? ' (' + _esc(rootCd.data_source_code) + ')' : '')
        : ' · bez data_source';
      const gridHostId = 'erp-page-grid-' + coreId;
      // Phase 38.4 Krok 5.R-C+6.1 (18.5.2026 vecer pozde, Marti's "nadpis musi
      // taky pryc"): drop header div uplne. Grid host = jediny direct child
      // mainContent → max plochy. Parita s hardcoded #erpSysGridBody (Uzivatele
      // tab) co taky nema header. Meta info (Root + data_source) bude pripadne
      // budouci v patickce nebo title bar — pro ted plne native AG Grid.
      mainContent.innerHTML =
        '<div id="' + gridHostId + '" style="flex:1 1 auto;min-height:0;min-width:0;' +
        'width:100%;background:#0f141a;overflow:hidden;">' +
        '<div style="padding:20px;text-align:center;color:#5d6975;font-style:italic;">' +
        '⏳ Načítám rows…' +
        '</div></div>';

      const gridHost = document.getElementById(gridHostId);
      if (!gridHost) {
        console.error("[page_render] grid host element not found:", gridHostId);
        return;
      }

      // No data_source → dashed placeholder
      if (!rootCd.data_source_code) {
        gridHost.style.border = '1px dashed #3a4754';
        gridHost.innerHTML =
          '<div style="padding:20px;text-align:center;color:#5d6975;font-style:italic;' +
          'display:flex;align-items:center;justify-content:center;height:100%;">' +
          '(grid bez napojeneho data_source — design root v Krok 5.D root type picker)' +
          '</div>';
        return;
      }

      // ErpDataGrid neni nacten → fallback
      if (typeof window.ErpDataGrid !== "function") {
        gridHost.innerHTML =
          '<div style="padding:20px;text-align:center;color:#d4a8a8;">' +
          '⚠ ErpDataGrid komponenta neni nactena (datagrid.js missing).' +
          '</div>';
        return;
      }

      // Phase 38.4 Krok 5.R-D+1 (18.5.2026 rano, Marti's "refactor code na ID"):
      // Prefer /data-by-id/{id} over /data/{code}. Drop code='29' workaround.
      const fetchUrl = rootCd.data_source_id
        ? '/api/v1/erp/data-by-id/' + rootCd.data_source_id + '?limit=500'
        : '/api/v1/erp/data/' + encodeURIComponent(rootCd.data_source_code) + '?limit=500';
      const isDesignMode = (typeof window !== "undefined" && window._erpDesignMode === true);

      // Phase 38.4 Krok 5.R-D+3 (18.5.2026, Marti's "Stage 1 MVP, NIC VIC"):
      // Per-grid dirty tracker Map(rowId → {field: newValue}). Visual yellow
      // highlight + save button v meta area. Click → loop PATCH per dirty row.
      const dirtyRows = new Map();

      // Hardcoded entity_id mapping per data_source_id (pre-Stage 2 column
      // fw.data_source.target_entity_type). CORE 30 (ds #29) fw.core entity
      // = 23 (5.N-1 _FW_FORM_CORE_REGISTRY[23] → "core" config).
      const DS_TO_ENTITY = { 29: "23" };
      const entityForPatch = DS_TO_ENTITY[rootCd.data_source_id] || null;

      // Per-rowId rowData snapshot — pro expected_updated_at v PATCH body
      const dirtyRowData = new Map();

      // Phase 38.4 Krok 5.R-C+6.1 (18.5.2026 vecer): save dirty button
      // appendovan jako floating overlay (mainContent position:relative
      // parent), drop <p> header reference. DESIGN mode only.
      let saveBtn = null;
      function _ensureSaveBtn() {
        if (saveBtn) return saveBtn;
        if (!isDesignMode) return null;
        saveBtn = document.createElement("button");
        saveBtn.type = "button";
        saveBtn.className = "erp-page-grid-save-btn";
        saveBtn.style.cssText =
          "position:absolute;top:8px;right:16px;z-index:10;" +
          "padding:4px 12px;background:#3a5a3a;border:1px solid #4a7a4a;" +
          "border-radius:3px;color:#e8eef5;cursor:pointer;font-size:11px;font-weight:600;" +
          "display:none;";
        saveBtn.addEventListener("click", _onSaveClick);
        // Append to mainContent (parent has position:relative via .erp-main-content CSS)
        mainContent.appendChild(saveBtn);
        return saveBtn;
      }
      function _refreshSaveBtn() {
        const btn = _ensureSaveBtn();
        if (!btn) return;
        const count = dirtyRows.size;
        if (count > 0) {
          btn.style.display = "";
          btn.textContent = "💾 Uložit " + count;
        } else {
          btn.style.display = "none";
        }
      }
      async function _onSaveClick() {
        if (!entityForPatch) {
          alert("Save flow nepripraven pro data_source #" + rootCd.data_source_id +
                ". Long-term: fw.data_source.target_entity_type column.");
          return;
        }
        saveBtn.disabled = true;
        saveBtn.textContent = "⏳ Ukládám...";
        const entries = Array.from(dirtyRows.entries());
        let okCount = 0, failCount = 0;
        for (const [rowId, changes] of entries) {
          // Optimistic lock — expected_updated_at z row snapshot (5.M-5+1
          // doctrine, 17.5.). Bez nej backend vraci 400.
          const rowData = dirtyRowData.get(rowId) || {};
          const expectedUpdatedAt = rowData.updated_at || null;
          try {
            const resp = await fetch(
              "/api/v1/erp/design/" + entityForPatch + "/" + rowId,
              {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                  field_changes: changes,
                  expected_updated_at: expectedUpdatedAt,
                }),
              }
            );
            const json = await resp.json();
            if (resp.ok && json && json.ok) {
              dirtyRows.delete(rowId);
              dirtyRowData.delete(rowId);
              okCount++;
            } else {
              failCount++;
              console.error("[page_render save] row " + rowId + " failed:",
                            json && json.error);
            }
          } catch (e) {
            failCount++;
            console.error("[page_render save] row " + rowId + " network:", e);
          }
        }
        saveBtn.disabled = false;
        if (failCount > 0) {
          alert("Save: " + okCount + " OK, " + failCount + " FAIL — viz konzole.");
        }
        try {
          const gridInst = gridHost.__erpGridInst;
          if (gridInst && gridInst.gridApi) {
            gridInst.gridApi.refreshCells({ force: true });
          }
        } catch (e) {}
        _refreshSaveBtn();
      }

      fetch(fetchUrl, { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
          if (!data || !data.ok) {
            throw new Error((data && data.error) || 'data fetch failed');
          }
          const rows = Array.isArray(data.rows) ? data.rows : [];
          gridHost.innerHTML = "";
          // Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer, Marti's "prehled_cislo
          // musi uplne zmizet"): native ErpDataGrid toolbar pres layoutKey
          // = "core_<id>" — dropdown sestav + 🎨 Pravidla + + Uložit jako…
          // + ⋮ Spravovat. Backend persistence pres /grid-layout/{core_id}.
          try {
            const gridInst = new window.ErpDataGrid(gridHost, {
              rowData: rows,
              autoColumns: true,
              rowSelection: "single",
              enableEdit: isDesignMode,
              layoutKey: "core_" + coreId,
              gridCode: rootCd.name || ("core_" + coreId),
              autoLoadDefault: true,
              // Krok 5.R-C+7: coreInfo pill — fw.core context
              coreInfo: {
                coreId: coreId,
                refId: rootCd.data_source_id,
                coreCode: (specForRender && specForRender.core && specForRender.core.code) || null,
                coreLabel: (specForRender && specForRender.core && specForRender.core.label) || (tab && tab.label) || null,
                refCode: rootCd.data_source_code || null,
                rootCompDefId: rootCd.id,
                rootTypeCode: rootCd.type_code || null,
              },
              // Krok 5.R-D+3 dirty visual: cellClassRules per defaultColDefExtra
              // (datagrid.js pass-through z 5.R-D+3 P1 patch).
              defaultColDefExtra: {
                cellClassRules: {
                  "erp-cell-dirty": function (params) {
                    if (!params || !params.data || params.data.id == null) return false;
                    const dirty = dirtyRows.get(params.data.id);
                    if (!dirty) return false;
                    const field = params.colDef && params.colDef.field;
                    return field != null && Object.prototype.hasOwnProperty.call(dirty, field);
                  },
                },
              },
              // ErpDataGrid passes (rowData, fieldName, oldValue, newValue) — NOT event obj.
              onCellEdit: function (rowData, fieldName, oldValue, newValue) {
                if (!rowData || rowData.id == null) {
                  console.warn("[page_render cell edit] row.id missing — skip dirty track");
                  return;
                }
                const rowId = rowData.id;
                let entry = dirtyRows.get(rowId);
                if (!entry) {
                  entry = {};
                  dirtyRows.set(rowId, entry);
                }
                entry[fieldName] = newValue;
                // Snapshot rowData pro expected_updated_at v PATCH payload
                // (5.M-5+1 optimistic lock pattern z 17.5.).
                dirtyRowData.set(rowId, rowData);
                console.info("[page_render cell edit]",
                  { field: fieldName, oldValue, newValue, rowId,
                    ds_id: rootCd.data_source_id });
                try {
                  if (gridInst && gridInst.gridApi) {
                    gridInst.gridApi.refreshCells({ force: true });
                  }
                } catch (e) {}
                _refreshSaveBtn();
              },
            });
            gridHost.__erpGridInst = gridInst;
          } catch (e) {
            console.error("[page_render] ErpDataGrid init failed:", e);
            gridHost.innerHTML =
              '<div style="padding:20px;color:#d4a8a8;">' +
              '⚠ Grid init failed: ' + _esc(String(e.message || e)) +
              '</div>';
          }
        })
        .catch(err => {
          console.error("[page_render] data fetch failed:", err);
          try {
            _logger.error("page_render.js",
              "data fetch failed: " + (err && err.message || err),
              { extra: { core_id: coreId, ds_code: rootCd.data_source_code } });
          } catch (e) {}
          gridHost.innerHTML =
            '<div style="padding:20px;color:#d4a8a8;">' +
            '❌ Chyba načítání rows: ' + _esc(String(err.message || err)) +
            '</div>';
        });
    }

    function _renderFormPlaceholder(mainContent, tab, rootCd, coreCode, coreId) {
      mainContent.innerHTML =
        '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
        '<h2 style="margin:0 0 12px;font-weight:500;color:#e8eef5;">📋 ' +
        _esc(tab.label || "Form") + '</h2>' +
        '<p style="color:#a8b4c2;margin:0 0 8px;">' +
        'Asociovaný core: <strong>' + _esc(coreCode || "?") +
        '</strong> (id=' + coreId + ') · root type: ' + _esc(rootCd.type_code) +
        '</p>' +
        '<p style="color:#7a8696;font-size:13px;margin:0;">' +
        'Form layout v page area — render přijde v Krok 5.R-E. ' +
        'Zatím dvojklik v gridu otevře form modal (existing path).' +
        '</p></div>';
    }

    function _renderUnknownType(mainContent, rootCd) {
      mainContent.innerHTML =
        '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
        '<h2 style="margin:0 0 12px;color:#d4a878;">⚠ Neznámý typ root komponenty</h2>' +
        '<p style="color:#a8b4c2;">' +
        'type_code = "' + _esc(rootCd.type_code || "?") + '" (' + (rootCd.type_id || '?') + ') ' +
        'nepodporovaný v page render. Krok 5.R-B minimum pokrývá ' +
        'jen grid_modern/list/form/frameless_form.</p></div>';
    }

    function _renderFetchError(mainContent, err, coreCode, coreId) {
      mainContent.innerHTML =
        '<div class="erp-main-empty" style="padding:40px;text-align:center;">' +
        '<h2 style="margin:0 0 12px;color:#d4a8a8;">❌ Chyba načítání page-spec</h2>' +
        '<p style="color:#a8b4c2;">' + _esc(String(err && err.message || err)) + '</p>' +
        '<p style="color:#7a8696;font-size:13px;margin:8px 0 0;">' +
        'Asociovaný core: <strong>' + _esc(coreCode || "?") + '</strong> ' +
        '(id=' + coreId + ')</p></div>';
    }

    // ─── Public API ──────────────────────────────────────────────────

    /**
     * Dispatch page render pro fw.core+comp_def.
     *
     * @param {number} coreId — fw.core.id
     * @param {string|null} coreCode — fw.core.code (display only)
     * @param {object} tab — tab info {label, ...}
     * @param {HTMLElement} mainContent — target container
     */
    function dispatchPageRender(coreId, coreCode, tab, mainContent) {
      if (!coreId || !mainContent) {
        console.error("[page_render] dispatchPageRender: missing coreId/mainContent");
        return;
      }
      // Fix J Vrstva 5 (20.5. vecer): set window context PRED page-spec fetch.
      // _apiCall + _erpLogToDb pak auto-add core_id do headers + event body →
      // fw.diag_log row dostane grid/form attribution.
      try {
        window._erpActiveCoreId = coreId;
        window._erpActiveCompDefId = null; // reset comp_def — page-spec start
      } catch (_e) { /* never crash dispatchPageRender */ }
      fetch('/api/v1/erp/fw-core/' + coreId + '/page-spec', {
        credentials: 'include'
      })
        .then(r => r.json())
        .then(spec => {
          if (!spec || !spec.ok) {
            throw new Error((spec && spec.error) || 'page-spec fetch failed');
          }
          const rootCd = spec.root_comp_def;
          if (!rootCd) {
            _renderDraftedPlaceholder(mainContent, tab, coreCode, coreId);
            return;
          }
          const typeCode = rootCd.type_code || '';
          if (typeCode === 'grid_modern' || typeCode === 'list' || typeCode === 'list_root') {
            _renderEmptyGrid(mainContent, tab, rootCd, coreId, spec);
            return;
          }
          if (typeCode === 'form' || typeCode === 'frameless_form') {
            _renderFormPlaceholder(mainContent, tab, rootCd, coreCode, coreId);
            return;
          }
          _renderUnknownType(mainContent, rootCd);
        })
        .catch(err => {
          console.error('[page_render] fetch failed:', err);
          try {
            _logger.error("page_render.js",
              "page-spec fetch failed: " + (err && err.message || err),
              { extra: { core_id: coreId, core_code: coreCode } });
          } catch (e) {}
          _renderFetchError(mainContent, err, coreCode, coreId);
        });
    }

    // Phase 38.4 Krok 5.R-D+3 (18.5.2026): CSS injekt pro dirty cell visual.
    (function _injectDirtyCss() {
      const STYLE_ID = "erp-page-render-dirty-css";
      if (document.getElementById(STYLE_ID)) return;
      const style = document.createElement("style");
      style.id = STYLE_ID;
      style.textContent =
        ".erp-cell-dirty { background: #3a3520 !important; }";
      document.head.appendChild(style);
    })();

    global.ErpPageRender = {
      dispatchPageRender: dispatchPageRender,
    };

  });
})(window);
