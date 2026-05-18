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

    function _renderEmptyGrid(mainContent, tab, rootCd, coreId) {
      // Phase 38.4 Krok 5.R-D (18.5.2026 rano, Marti's "zasadni posun v Gridu"):
      // real ErpDataGrid s data_source rows. AG Grid autoColumns=true → sam
      // detect columns z prvniho row keys (Marti's doctrine "nativni grid
      // inteligentni sam od sebe").
      const dsInfo = rootCd.data_source_id
        ? ' · data_source #' + rootCd.data_source_id +
          (rootCd.data_source_code ? ' (' + _esc(rootCd.data_source_code) + ')' : '')
        : ' · bez data_source';
      const gridHostId = 'erp-page-grid-' + coreId;
      mainContent.innerHTML =
        '<div style="padding:20px;display:flex;flex-direction:column;height:100%;">' +
        '<h2 style="margin:0 0 12px;font-weight:500;color:#e8eef5;">📊 ' +
        _esc(tab.label || "Přehled") + '</h2>' +
        '<p style="color:#7a8696;font-size:11px;margin:0 0 12px;font-style:italic;">' +
        'Root: ' + _esc(rootCd.name || '?') +
        ' (' + _esc(rootCd.type_code) + ', comp_def #' + rootCd.id + ')' +
        _esc(dsInfo) +
        '</p>' +
        '<div id="' + gridHostId + '" style="flex:1 1 auto;min-height:0;' +
        'border:1px solid #2a3340;border-radius:4px;background:#0f141a;' +
        'overflow:hidden;">' +
        '<div style="padding:20px;text-align:center;color:#5d6975;font-style:italic;">' +
        '⏳ Načítám rows…' +
        '</div></div></div>';

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
      // Fallback na code path zachovan pro defense in depth.
      const fetchUrl = rootCd.data_source_id
        ? '/api/v1/erp/data-by-id/' + rootCd.data_source_id + '?limit=500'
        : '/api/v1/erp/data/' + encodeURIComponent(rootCd.data_source_code) + '?limit=500';
      // Phase 38.4 Krok 5.R-D+2 (18.5.2026 rano, Marti's "inline editing
      // v DESIGN, PRODUCTION read-only"): detect design mode pri instantiate.
      // Toggle DESIGN/PRODUCTION = user musi re-klik na tab pro re-render.
      const isDesignMode = (typeof window !== "undefined" && window._erpDesignMode === true);
      fetch(fetchUrl, { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
          if (!data || !data.ok) {
            throw new Error((data && data.error) || 'data fetch failed');
          }
          const rows = Array.isArray(data.rows) ? data.rows : [];
          gridHost.innerHTML = "";
          try {
            new window.ErpDataGrid(gridHost, {
              rowData: rows,
              autoColumns: true,
              rowSelection: "single",
              // Krok 5.R-D+2 inline edit MVP (Marti's "service mode pro designery"):
              // AG Grid native enableEdit + onCellEdit. NO save flow yet —
              // Marti's "test z UI a pak rozhodneme co dal".
              enableEdit: isDesignMode,
              onCellEdit: function (ev) {
                console.info("[page_render cell edit]", {
                  field: ev && ev.colDef && ev.colDef.field,
                  oldValue: ev && ev.oldValue,
                  newValue: ev && ev.newValue,
                  row: ev && ev.data,
                  ds_id: rootCd.data_source_id,
                });
              },
            });
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
            _renderEmptyGrid(mainContent, tab, rootCd, coreId);
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

    global.ErpPageRender = {
      dispatchPageRender: dispatchPageRender,
    };

  });
})(window);
