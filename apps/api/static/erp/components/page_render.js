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

    // ─── Krok 5.S Fáze 7 (23.5.2026 rano, Marti's icon-only design parity): ───
    //
    // Grid actions toolbar v workspace header (#erpGridActionsHost) vedle
    // Tvoje Marti + 🔄 Refresh. 3 buttons (Nový/Oprava/Smazat) driven by
    // grid_actions z page-spec backend response. Design parita s
    // .erp-refresh-btn — 36×36 square, 27px icon, data-hint tooltip:
    //   has_insert + edit_core_id → 🆕 Nový visible (no row required)
    //   has_edit + edit_core_id   → ✏️ Oprava visible (row select required)
    //   has_delete                → 🗑️ Smazat visible (row select required, danger hover)
    //
    // No grid_actions (drafted core / form-only) → empty host (jen Refresh
    // zustane v workspace header).
    function _renderGridToolbar(toolbarHost, gridActions, ctx) {
      if (!toolbarHost) return;
      // Clear předchozí grid actions (tab switch cleanup)
      toolbarHost.innerHTML = '';
      if (!gridActions) {
        // Marti's Q5: no actions, no buttons — jen Refresh (workspace header)
        return;
      }
      const editCoreId = gridActions.edit_core_id;
      const showNew = !!(gridActions.has_insert && editCoreId);
      const showEdit = !!(gridActions.has_edit && editCoreId);
      const showDelete = !!gridActions.has_delete;

      const parts = [];
      if (showNew) {
        parts.push(
          '<button id="erp-tb-new" type="button" class="erp-grid-action-btn" ' +
          'data-hint="Nový záznam (Insert)">🆕</button>'
        );
      }
      if (showEdit) {
        parts.push(
          '<button id="erp-tb-edit" type="button" class="erp-grid-action-btn" ' +
          'data-need-row="1" data-hint="Oprava vybraného záznamu (Enter / dvojklik)" disabled>✏️</button>'
        );
      }
      if (showDelete) {
        parts.push(
          '<button id="erp-tb-delete" type="button" class="erp-grid-action-btn danger" ' +
          'data-need-row="1" data-hint="Smazat vybraný záznam (nevratné)" disabled>🗑️</button>'
        );
      }
      toolbarHost.innerHTML = parts.join('');

      // Wire click handlers
      if (showNew) {
        const btnNew = document.getElementById('erp-tb-new');
        if (btnNew) btnNew.addEventListener('click', () => ctx.onNew(editCoreId));
      }
      if (showEdit) {
        const btnEdit = document.getElementById('erp-tb-edit');
        if (btnEdit) btnEdit.addEventListener('click', () => {
          if (btnEdit.disabled) return;
          ctx.onEdit(editCoreId);
        });
      }
      if (showDelete) {
        const btnDelete = document.getElementById('erp-tb-delete');
        if (btnDelete) btnDelete.addEventListener('click', () => {
          if (btnDelete.disabled) return;
          ctx.onDelete();
        });
      }
    }

    function _updateToolbarSelection(toolbarHost, hasSelection, selectedCount) {
      if (!toolbarHost) return;
      // Krok 5.S Fáze 7: class-based styling, jen toggle disabled attribute
      // (CSS .erp-grid-action-btn:disabled handle opacity + cursor).
      const targets = toolbarHost.querySelectorAll('[data-need-row="1"]');
      targets.forEach((btn) => { btn.disabled = !hasSelection; });

      // Krok 5.X (23.5.2026): Oprava disabled při multi-select (form jen single).
      // Smazat (a budoucí batch actions) zůstává enabled při count>=1.
      const N = Number(selectedCount) || (hasSelection ? 1 : 0);
      const editBtns = toolbarHost.querySelectorAll('[data-action="edit"], [data-action="oprava"]');
      editBtns.forEach((btn) => {
        // Edit umí jen 1 řádek — disable při N>1
        btn.disabled = !hasSelection || N > 1;
        try {
          if (N > 1) {
            btn.setAttribute('data-hint', 'Oprava jen pro 1 řádek (vybráno ' + N + ')');
          } else if (btn._origHint != null) {
            btn.setAttribute('data-hint', btn._origHint);
          } else {
            btn._origHint = btn.getAttribute('data-hint') || '';
          }
        } catch (_e) {}
      });

      // Selection counter badge (vedle toolbar buttonů, jen při N>=2)
      let counterEl = toolbarHost.querySelector('[data-erp-selcount]');
      if (N >= 2) {
        if (!counterEl) {
          counterEl = document.createElement('span');
          counterEl.setAttribute('data-erp-selcount', '1');
          counterEl.style.cssText = [
            'display:inline-flex', 'align-items:center', 'justify-content:center',
            'min-width:24px', 'height:24px',
            'padding:0 8px',
            'margin:0 4px 0 8px',
            'background:rgba(60,120,200,0.25)',
            'color:#aac8ec',
            'border:1px solid rgba(120,170,220,0.4)',
            'border-radius:12px',
            'font-size:11px', 'font-weight:700',
            'font-family:monospace',
            'user-select:none',
          ].join(';');
          counterEl.title = 'Vybraných řádků';
          toolbarHost.appendChild(counterEl);
        }
        counterEl.textContent = String(N);
      } else if (counterEl) {
        counterEl.remove();
      }
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
      // Krok 5.S Fáze 6 (23.5.2026 rano, Marti's Q3/Q4 doctrine M1 header relocation):
      // Drop toolbar wrap nad gridem — toolbar žije v workspace header
      // (#erpGridActionsHost vedle Tvoje Marti + 🔄 Refresh). Žádná optická
      // mezera mezi filtrem a tabs. Čistý gridHost direct child mainContent.
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

      // Phase 38.4 Krok 14g-H+35 (22.5.2026 vecer, Marti's "save flow ted
      // nejde"): drop hardcoded DS_TO_ENTITY mapping. Backend design_patch_entity
      // numeric path /design/{core_id}/{row_id} → _resolve_entity_config_for_core
      // (5.N-1 helper) lookup v _FW_FORM_CORE_REGISTRY[core_id]. Univerzalni
      // pre vsechny grids (Diag log, DataSets, Trusted devices, ...) — pridat
      // jen registry entry v router.py per novy core.
      const entityForPatch = coreId ? String(coreId) : null;

      // Per-rowId rowData snapshot — pro expected_updated_at v PATCH body
      const dirtyRowData = new Map();

      // Phase 38.4 Krok 14g-H+35 (22.5.2026 vecer, Marti's "save ikona vedle
      // refresh button"): Hook do workspace header save button (#erpSaveChangesBtn
      // vedle #erpRefreshBtn). Direct btn.onclick = fn pattern — pre-refresh
      // overwrites previous handler (per-grid scope wins, no race). Drop
      // addEventListener flag pattern (gotcha: re-bound across grid re-renders).
      function _refreshSaveBtn() {
        const btn = document.getElementById("erpSaveChangesBtn");
        const countEl = document.getElementById("erpSaveChangesCount");
        if (!btn || !countEl) {
          console.warn("[page_render save] btn/countEl missing in workspace header");
          return;
        }
        const count = dirtyRows.size;
        if (count > 0) {
          btn.style.display = "";
          countEl.textContent = String(count);
          // Direct onclick replace — current grid's _onSaveClick wins.
          // Wrapped pro defensive console.info + try/catch.
          btn.onclick = function() {
            console.info("[page_render save] click fired, dirty count=" + dirtyRows.size +
                         ", entityForPatch=" + entityForPatch);
            try {
              _onSaveClick();
            } catch (e) {
              console.error("[page_render save] _onSaveClick threw:", e);
              alert("Save error: " + (e && e.message || e));
            }
          };
          // Hover effect (idempotent via attribute check)
          if (!btn.dataset.erpSaveHoverBound) {
            btn.dataset.erpSaveHoverBound = "1";
            btn.addEventListener("mouseenter", function() {
              btn.style.background = "#e0b25a";
            });
            btn.addEventListener("mouseleave", function() {
              btn.style.background = "#d4a04a";
            });
          }
        } else {
          btn.style.display = "none";
          btn.onclick = null;
        }
      }
      async function _onSaveClick() {
        if (!entityForPatch) {
          alert("Save flow nepripraven pro data_source #" + rootCd.data_source_id +
                ". Long-term: fw.data_source.target_entity_type column.");
          return;
        }
        // Phase 38.4 Krok 14g-H+35 hotfix (22.5.2026 vecer po revert f1e1dec):
        // saveBtn variable byl dropnut v H+35 v1 (redesign na onclick = fn),
        // ale `saveBtn.disabled = true` reference zustaly v _onSaveClick =>
        // ReferenceError pri kliknu => save nic nedelal. Fix: read btn z DOM.
        const _btnEl = document.getElementById("erpSaveChangesBtn");
        if (_btnEl) {
          _btnEl.disabled = true;
        }
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
        if (_btnEl) {
          _btnEl.disabled = false;
        }
        if (failCount > 0) {
          alert("Save: " + okCount + " OK, " + failCount + " FAIL — viz konzole.");
        } else if (okCount > 0) {
          console.info("[page_render save] OK: " + okCount + " row" + (okCount === 1 ? "" : "s") + " saved");
        }
        try {
          const gridInst = gridHost.__erpGridInst;
          if (gridInst && gridInst.gridApi) {
            gridInst.gridApi.refreshCells({ force: true });
          }
        } catch (e) {}
        _refreshSaveBtn();
      }

      // Phase 22.5.2026 fix: pre-fetch layout PARALELNE s data fetch.
      // Pass jako `initialLayout` do ErpDataGrid -- caller cesta A (Krok C+
      // fix #8 z 9.5.2026) mutuje columnDefs PRED grid create (strip flex,
      // set width, reorder). Pixel-perfect restore bez timing flicker.
      // Bez initialLayout jde cesta B (post-create _applyLayout) ktera ma
      // znamé problemy s AG Grid v32+ (Marti's "po reload se zmeny neprojevily").
      const dataFetch = fetch(fetchUrl, { credentials: 'include' }).then(r => r.json());
      // Krok 5.U Fáze H+ (23.5.2026): polymorphic scope path prefix —
      // backend _parse_scope_key regex čeká "core_<id>" nebo "ds_<id>".
      // Page_render obsluhuje jen core scope (main screen grids vázané
      // na fw.core). DS scope jen pres catalog picker (catalog_picker.js).
      const layoutFetch = fetch(
        "/api/v1/erp/grid-layout/core_" + coreId + "/list",
        { credentials: 'include' }
      ).then(r => r.ok ? r.json() : null).catch(() => null);

      Promise.all([dataFetch, layoutFetch])
        .then(([data, layoutList]) => {
          if (!data || !data.ok) {
            throw new Error((data && data.error) || 'data fetch failed');
          }
          const rows = Array.isArray(data.rows) ? data.rows : [];
          const initialLayout = (layoutList && layoutList.ok && layoutList.effective_default)
            ? layoutList.effective_default
            : null;
          if (initialLayout) {
            console.info(
              "[page_render] pre-fetched layout #" + initialLayout.id +
              " '" + initialLayout.name + "' for core_" + coreId +
              " (cols=" + ((initialLayout.layout_json && initialLayout.layout_json.columns) || []).length + ")"
            );
          }
          gridHost.innerHTML = "";
          // Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer, Marti's "prehled_cislo
          // musi uplne zmizet"): native ErpDataGrid toolbar pres layoutKey
          // = "core_<id>" -- dropdown sestav + Pravidla + Ulozit jako
          // + spravovat. Backend persistence pres /grid-layout/{core_id}.
          try {
            const gridInst = new window.ErpDataGrid(gridHost, {
              rowData: rows,
              autoColumns: true,
              // Krok 5.X (23.5.2026): multi-row selection pro batch operations
              // (Mód 1 Centrála 1 — cyklicky per-row). Shift+klik = range, Ctrl+klik
              // = toggle. _erpBatchRowAction helper drží sequential loop.
              rowSelection: "multiple",
              // Phase 38.4 Krok 14g-H+34 (22.5.2026 vecer, Marti's catch):
              // PROD = inline edit OFF default. Excel toggle (Ctrl+Shift+E)
              // ho zapne servisne. Drop `enableEdit: isDesignMode` —
              // grid se vzdycky inicializuje synchronizovany s
              // _excelMode=false (PROD). Krok 5.R-D+2 inline edit v DESIGN
              // mode nahrazen explicitnim Excel toggle per-grid.
              enableEdit: false,
              layoutKey: "core_" + coreId,
              gridCode: rootCd.name || ("core_" + coreId),
              autoLoadDefault: true,
              initialLayout: initialLayout,
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
              // Krok 5.S Fáze 5 + dvojklik shortcut (23.5.2026 rano, Marti's
              // "dvojklik na uzivatelich = otevreni editace vety"): Centrala 1
              // Excel/Windows standard. Reuse stejny flow jako toolbar Oprava
              // button — DesignFwForm modal s editCoreId + rowId.
              onRowDoubleClick: function(rowData, ev) {
                const ga = rootCd && rootCd.grid_actions;
                if (!ga || !ga.edit_core_id) {
                  console.info("[page_render dblclick] no edit_core_id — no-op");
                  return;
                }
                if (!rowData || rowData.id == null) return;
                if (typeof window.DesignFwForm !== "function") {
                  console.warn("[page_render dblclick] DesignFwForm not loaded");
                  return;
                }
                new window.DesignFwForm({
                  coreId: ga.edit_core_id,
                  rowId: rowData.id,
                  onSaveSuccess: function() {
                    try {
                      const inst = gridHost.__erpGridInst;
                      if (inst && typeof inst.refresh === "function") inst.refresh();
                    } catch (_e) {}
                  },
                }).open();
              },
              // Enter na radku = same as dvojklik (keyboard parity)
              onRowEnter: function(rowData, ev) {
                const ga = rootCd && rootCd.grid_actions;
                if (!ga || !ga.edit_core_id) return;
                if (!rowData || rowData.id == null) return;
                if (typeof window.DesignFwForm !== "function") return;
                new window.DesignFwForm({
                  coreId: ga.edit_core_id,
                  rowId: rowData.id,
                  onSaveSuccess: function() {
                    try {
                      const inst = gridHost.__erpGridInst;
                      if (inst && typeof inst.refresh === "function") inst.refresh();
                    } catch (_e) {}
                  },
                }).open();
              },
            });
            gridHost.__erpGridInst = gridInst;

            // Krok 5.S Fáze 6 (23.5.2026 rano, Marti's Q3 M1 header relocation):
            // render grid actions do workspace header (#erpGridActionsHost
            // vedle Tvoje Marti + 🔄 Refresh). Tab switch cleanup: ohort.innerHTML
            // se clearuje v _renderGridToolbar start (předchozí tab grid actions).
            const _toolbarHost = document.getElementById("erpGridActionsHost");
            let _selectedRowId = null;
            if (_toolbarHost) {
              _renderGridToolbar(_toolbarHost, rootCd.grid_actions, {
                coreId: coreId,
                onNew: function(editCoreId) {
                  // Q8=A today MVP — Insert mode v Fáze 5 (DesignFwForm extend
                  // o rowId=null support → empty form → POST insert).
                  alert(
                    "🆕 Nový záznam (CORE " + editCoreId + ")\n\n" +
                    "Insert mode přijde v Krok 5.S Fáze 5 (DesignFwForm extend " +
                    "o rowId=null). Zatím přidávejte řádky přes Excel mode " +
                    "(Ctrl+Shift+E)."
                  );
                },
                onEdit: function(editCoreId) {
                  if (!_selectedRowId || typeof window.DesignFwForm !== "function") {
                    console.warn("[toolbar Oprava] no selection or DesignFwForm missing");
                    return;
                  }
                  new window.DesignFwForm({
                    coreId: editCoreId,
                    rowId: _selectedRowId,
                    onSaveSuccess: function() {
                      // Refresh grid po save (analog openFwFormForRow flow)
                      try {
                        const inst = gridHost.__erpGridInst;
                        if (inst && typeof inst.refresh === "function") inst.refresh();
                      } catch (_e) {}
                    },
                  }).open();
                },
                onDelete: async function() {
                  // Krok 5.X (23.5.2026): batch helper Mód 1 (Centrála 1 cyklicky per-row).
                  // Collect selected rows; pokud žádné, fallback na _selectedRowId (focused).
                  let ids = [];
                  try {
                    if (gridInst && gridInst.gridApi) {
                      const sel = gridInst.gridApi.getSelectedRows() || [];
                      ids = sel.map(r => (r && (r.id != null ? r.id : r.ID))).filter(x => x != null);
                    }
                  } catch (_e) {}
                  if (ids.length === 0 && _selectedRowId != null) {
                    ids = [_selectedRowId];
                  }
                  if (ids.length === 0) {
                    console.warn("[toolbar Smazat] no selection — abort");
                    return;
                  }

                  // Defensive — pokud helper nezavedený, fallback na native confirm
                  if (typeof window._erpBatchRowAction !== "function") {
                    console.error("[toolbar Smazat] _erpBatchRowAction not loaded — abort");
                    alert("Batch helper není zaveden. Hard reload (Ctrl+Shift+R).");
                    return;
                  }

                  const result = await window._erpBatchRowAction({
                    rowIds: ids,
                    opLabel: "Smazat",
                    opVerb: "smazat",
                    destructive: true,
                    actionFn: async function(rowId, idx, total) {
                      try {
                        const resp = await fetch(
                          "/api/v1/erp/design/" + coreId + "/" + rowId,
                          { method: "DELETE", credentials: "include" }
                        );
                        const json = await resp.json().catch(() => ({}));
                        if (resp.ok && json && json.ok) {
                          // Krok 5.W diag drilldown — pokud refresh ukáže still-there,
                          // backend success ale persistence fail (activity_log abort).
                          // Tady jen log, refresh post-loop hodnotí state.
                          console.info("[batch Smazat] " + (idx + 1) + "/" + total +
                                       " id=" + rowId + " OK (deleted=" + json.deleted_rows + ")");
                          return { ok: true };
                        }
                        const errMsg = (json && json.error) || ("HTTP " + resp.status);
                        return { ok: false, error: errMsg };
                      } catch (e) {
                        return { ok: false, error: "network: " + (e && e.message || e) };
                      }
                    },
                    refreshFn: async function() {
                      try {
                        const r = await fetch(fetchUrl, { credentials: 'include' });
                        const d = await r.json();
                        if (d && d.ok && Array.isArray(d.rows) && gridInst && gridInst.gridApi) {
                          // Krok 5.X polish (23.5.2026, Marti's catch): full
                          // selection reset PŘED setRowData. AG Grid jinak
                          // auto-restore selection na rows se stejnými IDs
                          // (zbývající po DELETE zůstanou opticky vybrané).
                          try {
                            gridInst.gridApi.deselectAll();
                            // AG Grid Enterprise range selection (Excel-like
                            // cell range) — clear separately
                            if (typeof gridInst.gridApi.clearRangeSelection === 'function') {
                              gridInst.gridApi.clearRangeSelection();
                            }
                            if (typeof gridInst.gridApi.clearFocusedCell === 'function') {
                              gridInst.gridApi.clearFocusedCell();
                            }
                          } catch (_e) {}
                          gridInst.gridApi.setGridOption('rowData', d.rows);
                        }
                      } catch (e) {
                        console.warn("[batch Smazat] refresh failed:", e);
                      }
                    },
                  });

                  // Krok 5.X polish: pojistka — reset selection state PO refresh
                  // (refreshFn už deselectAll volal před setRowData, ale tady
                  // znovu pro toolbar + state lock cleanup).
                  _selectedRowId = null;
                  _updateToolbarSelection(_toolbarHost, false, 0);
                  try {
                    if (gridInst && gridInst.gridApi) {
                      gridInst.gridApi.deselectAll();
                      if (typeof gridInst.gridApi.clearRangeSelection === 'function') {
                        gridInst.gridApi.clearRangeSelection();
                      }
                      if (typeof gridInst.gridApi.clearFocusedCell === 'function') {
                        gridInst.gridApi.clearFocusedCell();
                      }
                    }
                  } catch (_e) {}
                },
                // Krok 5.S Fáze 6: onRefresh dropnut — workspace 🔄 Refresh
                // už refresh dělá (ErpRefresh.refreshActiveTab) + oranžový rámeček
                // stale data indication. Marti's Q4 doctrine.
              });

              // Wire selection change → enable/disable Oprava + Smazat
              // Krok 5.X (23.5.2026): multi-row aware. _selectedRowId drží
              // PRVNÍ selected (focused) — pro Oprava single-row fallback.
              // Smazat se dívá na getSelectedRows() celý array (batch).
              try {
                if (gridInst && gridInst.gridApi) {
                  gridInst.gridApi.addEventListener('selectionChanged', function() {
                    const sel = gridInst.gridApi.getSelectedRows() || [];
                    if (sel.length > 0) {
                      const row = sel[0];
                      _selectedRowId = row.id != null ? row.id : (row.ID != null ? row.ID : null);
                      // Toolbar enable: hasSelection=true (Smazat enabled).
                      // Oprava ignoruje multi-select — opens form pro 1. row.
                      _updateToolbarSelection(_toolbarHost, _selectedRowId != null, sel.length);
                    } else {
                      _selectedRowId = null;
                      _updateToolbarSelection(_toolbarHost, false, 0);
                    }
                  });
                }
              } catch (_e) {
                console.warn("[toolbar] selectionChanged wire failed:", _e);
              }
            }
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
