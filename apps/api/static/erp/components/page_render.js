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
      // Finanční podmínky (Šárka 8.7.2026): jádro hr.finance = iframe zamčené stránky
      // /finance-podminky (data gated na 8 přes _finance_can_uid; strom-uzel viditelný
      // jen pro 8 přes visibility_user_ids). Tmavý ERP vzhled → sedne do plochy.
      if (String(coreCode) === 'hr.finance') {
        mainContent.innerHTML = '<iframe src="/finance-podminky" title="Finanční podmínky" '
          + 'style="width:100%;height:100%;border:0;display:block;background:#0f141a;"></iframe>';
        return;
      }
      // Karta zaměstnance (Šárka 8.7.2026): jádro hr.karta = iframe stránky
      // /karta-zamestnance (seznam lidí HR-gated + sekce Pinya×Centrála). Tmavý ERP.
      if (String(coreCode) === 'hr.karta') {
        mainContent.innerHTML = '<iframe src="/karta-zamestnance" title="Karta zaměstnance" '
          + 'style="width:100%;height:100%;border:0;display:block;background:#0f141a;"></iframe>';
        return;
      }
      // HR přehled (Šárka 3.7.2026): jádro hr.prehled je záměrně „drafted" (bez
      // root gridu) — obsah dodává HR pult (Pinya styl). Mount ho MÍSTO placeholderu.
      if (String(coreCode) === 'hr.prehled'
          && window.HrPult && typeof window.HrPult.mount === 'function') {
        try {
          mainContent.innerHTML = '';
          var _hrEl = document.createElement('div');
          _hrEl.id = 'hr-pult';
          _hrEl.style.cssText = 'display:flex;flex-direction:column;flex:1 1 auto;min-height:0;height:100%;';
          mainContent.appendChild(_hrEl);
          window.HrPult.mount(_hrEl);
          return;
        } catch (_hrErr) {
          console.warn('[page_render] HR pult (drafted) mount failed:', _hrErr);
        }
      }
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
      // Krok 5.Y (23.5.2026, Marti's "save patri gridu"): Save Changes button
      // (Excel mode dirty rows). Always rendered, display:none default.
      // Visibility controlled:
      //   1. Excel mode toggle (datagrid.js fires 'erp:excel-mode-change' event)
      //   2. _refreshSaveBtn() updates count badge + disabled state
      // Stejný design jako Nový/Oprava/Smazat (36×36, 27px icon, data-hint).
      parts.push(
        '<button id="erp-tb-save" type="button" class="erp-grid-action-btn warning" ' +
        'data-hint="Uložit změny editovaných buněk (přímý edit)" ' +
        'style="display:none;" disabled>💾<span class="erp-save-count" id="erp-tb-save-count">0</span></button>'
      );
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

      // A.3 (Pavlovy připomínky, Kristý 25.6.2026): souhrnný pruh „Moje CRM čísla"
      // NAD přehledem Aktivity obchodníka (jádro 124). GATED na coreId → jiných
      // přehledů se NETÝKÁ. Fail-safe: chyba jen zaloguje, grid jede dál.
      try {
        if (String(coreId) === '124'
            && window.CrmAktivitaSouhrn && typeof window.CrmAktivitaSouhrn.mount === 'function'
            && !document.getElementById('crm-aktivita-souhrn')) {
          var _souhrnEl = document.createElement('div');
          _souhrnEl.id = 'crm-aktivita-souhrn';
          mainContent.insertBefore(_souhrnEl, gridHost);
          window.CrmAktivitaSouhrn.mount(_souhrnEl);
        }
      } catch (_souhrnErr) {
        console.warn('[page_render] CRM souhrn band failed (grid jede dál):', _souhrnErr);
      }

      // Band „Vytížení dílny + plán hovorů" NAD přehledem „Přehled pro obchodníka"
      // (jádro 136, Kristý 29.6.2026). Grafy vytížení + týdenní KPI hovorů. Stejný
      // gated/fail-safe vzor jako souhrn 124 → jiných přehledů se netýká.
      try {
        if (String(coreId) === '136'
            && window.ObchodnikPult && typeof window.ObchodnikPult.mount === 'function'
            && !document.getElementById('crm-obchodnik-pult')) {
          var _pultEl = document.createElement('div');
          _pultEl.id = 'crm-obchodnik-pult';
          mainContent.insertBefore(_pultEl, gridHost);
          window.ObchodnikPult.mount(_pultEl);
          // Druhý panel POD gridem: proběhlé hovory za tento týden (Kristý 29.6.2026).
          // appendChild → za gridHost; grid (flex:1) se zmenší, panel dostane svou výšku.
          if (typeof window.ObchodnikPult.mountHovory === 'function'
              && !document.getElementById('crm-obchodnik-hovory')) {
            var _hovEl = document.createElement('div');
            _hovEl.id = 'crm-obchodnik-hovory';
            mainContent.appendChild(_hovEl);
            window.ObchodnikPult.mountHovory(_hovEl);
          }
        }
      } catch (_pultErr) {
        console.warn('[page_render] Obchodnik pult band failed (grid jede dál):', _pultErr);
      }

      // Band „HR přehled" (Pinya styl) MÍSTO gridu pro jádro hr.prehled (core 137).
      // Šárka 3.7.2026 — vzor obchodníkova pultu. HR pult sám skryje prázdný grid.
      // Gated na coreId → jiných přehledů se NETÝKÁ. Fail-safe (chyba jen zaloguje).
      try {
        if (String(coreId) === '137'
            && window.HrPult && typeof window.HrPult.mount === 'function'
            && !document.getElementById('hr-pult')) {
          var _hrEl = document.createElement('div');
          _hrEl.id = 'hr-pult';
          mainContent.insertBefore(_hrEl, gridHost);
          window.HrPult.mount(_hrEl);
        }
      } catch (_hrErr) {
        console.warn('[page_render] HR pult band failed (grid jede dál):', _hrErr);
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

      // Faze 2-C cleanup (25.5.2026 rano, Marti's volba A "cleanup Faze 1 +
      // smoke" po overnight Faze 2-A + 2-A+ + 2-B wire): dropnuto ~190 LOC
      // Faze 1 external dirty tracking infrastructure:
      //   - dirtyRows Map + dirtyRowData Map closures
      //   - _refreshSaveBtn() function (re-assignovala saveBtn.onclick a
      //     overridla Faze 2-B fw handler — root cause race condition)
      //   - window addEventListener("erp:excel-mode-change") + _erpSaveCleanupActive
      //   - _erpSaveBtnRefresh window hook + _onSaveClick() async function
      //
      // Fw layer (datagrid.js _dirtyRows + _setDirty + _clearDirty +
      // _updateSaveButton + _handleSaveClick + _confirmDirtyChanges +
      // _toggleExcelMode 3-way confirm) je teď single source of truth.
      //
      // entityForPatch zustava — Faze 2-B onSave callback (line ~603) ho
      // potrebuje pro PATCH endpoint URL construction.
      const entityForPatch = coreId ? String(coreId) : null;

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
            // Marti 3.6.2026: nes přívětivou hlášku (source_unavailable =
            // externí EUROSOFT/Centrála dočasně dole, ne chyba STRATEGIE).
            const _e = new Error((data && (data.user_message || data.error)) || 'data fetch failed');
            if (data) {
              _e.code = data.error;
              _e.userMessage = data.user_message || null;
              _e.source = data.source || null;
            }
            throw _e;
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

          // Marti's 24.5.2026 master-detail (Krok 6 — Varianta B nested
          // ErpDataGrid). Opt-in registry per data_source code:
          //   - detailCellRenderer: factory function returns AG Grid
          //     detail renderer instance (např. ErpDataSourceOpDetailRenderer
          //     z data_source_op_detail.js). Renderer fetch + create
          //     nested ErpDataGrid s layoutKey persistence.
          //   - detailRowHeight: container výška v px (nested grid height).
          // Future: kaskáda level 2+ přes další registry entries with
          // dedicated renderers (each level vlastní ErpDataGrid + layoutKey).
          // Marti's 24.5.2026 Krok 6 hotfix: AG Grid detailCellRenderer
          // expects CLASS REFERENCE (constructor), ne factory function.
          // AG Grid calls `new detailCellRenderer()` internally.
          // Plus defensive: pokud renderer class není loaded (script tag
          // missing/cache), enableMasterDetail = false (žádný error).
          const MASTER_DETAIL_REGISTRY = {
            "framework_data_sources": {
              rendererClass: window.ErpDataSourceOpDetailRenderer || null,
              // Krok 6 v4: revert na fixed detailRowHeight (autoHeight měl
              // timing race s async fetch → detail row stayed 0px = "tenka
              // cara"). 240px buffer (Marti's 24.5. catch po Volba A LIVE):
              // 180px nestačí pro 3 ops + header + floating filter +
              // footer layout toolbar (Default + Pravidla + Uložit + Uložit
              // jako…) = ~180px sotva sedí, poslední row přečuhne.
              // 240px = 5-6 ops + footer pohodlně.
              // Polish autoHeight later s lepší fix (např. resize callback).
              detailRowHeight: 240,
            },
            // future levels — kaskáda:
            // "framework_data_source_ops": {
            //   rendererClass: window.ErpDataSetDetailRenderer || null,
            //   detailRowHeight: 200,
            // },
          };
          const _dsCode = rootCd && rootCd.data_source_code;
          const _masterDetailCfg = _dsCode ? MASTER_DETAIL_REGISTRY[_dsCode] : null;
          const _masterDetailReady = _masterDetailCfg && _masterDetailCfg.rendererClass;
          if (_masterDetailCfg && !_masterDetailReady) {
            console.warn("[page_render] master-detail registry hit for", _dsCode,
              "but renderer class not loaded — skipping master-detail (script tag missing or cache)");
          }
          if (_masterDetailReady) {
            console.info("[page_render] master-detail ENABLED for", _dsCode,
              "→ nested ErpDataGrid renderer (layoutKey persistence)");
          }

          // Phase 38.4 Krok 5.R-C+2 (18.5.2026 vecer, Marti's "prehled_cislo
          // musi uplne zmizet"): native ErpDataGrid toolbar pres layoutKey
          // = "core_<id>" -- dropdown sestav + Pravidla + Ulozit jako
          // + spravovat. Backend persistence pres /grid-layout/{core_id}.

          // Universal CRUD Etapa C (24.5.2026 vecer Marti doctrine
          // "system pro vsechno"): build context menu actions z grid_actions
          // backend signal + register edit form mapping do ErpGridActions
          // registry. Drz Marti "stejne zobrazit, stejne funkce" napric
          // 3 vrstvy (context menu, grid header, workspace toolbar).
          const _gridCodeForActions = rootCd.name || ("core_" + coreId);
          const _gridActionsForCtx = rootCd && rootCd.grid_actions;
          // Etapa F Problem B fix (24.5.2026 vecer Marti's doctrine "creatovat
          // vsude, ridit jen enabledelitu"): _ctxMenuActions = VZDY 4 actions.
          // Disabled state se rozhoduje v datagrid.js z gridActions stateMap.
          // contextMenuActions = declarative list available action types,
          // ne filter per has_*. Drz "stejne zobrazit, stejne funkce" napric
          // master + detail + picker.
          // Marti's 30.5.2026 ranní: "Core setting" prepended nahoře
          // (inspector fw.core metadat aktualniho core, hardcoded id=49).
          const _ctxMenuActions = ["core-setting", "create", "edit", "delete", "refresh"];
          // Graf pipeline (Marti 3.6.2026 — prezentace): akce "graph" jen na
          // pipeline gridu (act_pipeline_def). Otevře ErpActionCard stack.
          const _coreCodeForGraph = String(
            (specForRender && specForRender.core && specForRender.core.code) ||
            _gridCodeForActions || ""
          );
          if (/act_pipeline_def/i.test(_coreCodeForGraph) ||
              /act_pipeline_def/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("graph");
          }
          // Personální dokumenty na klik (Marti 10.6.2026): akce "doc" jen na
          // přehledu Finance lidí (hr_finance_lidi). Řádek = engagement → id.
          if (/hr_finance_lidi/i.test(_coreCodeForGraph) ||
              /hr_finance_lidi/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("doc");
          }
          // Hromadne osloveni firem (Claude-24/Kristy 18.6.2026): akce "osloveni"
          // jen na prehledu Kontakty (crm_kontakty). Vyber firem (multi) -> fronta
          // mod.crm_outreach (NEPOSILA — odeslani je krok rutiny Marti-AI za pravnim OK).
          if (/crm_kontakty/i.test(_coreCodeForGraph) ||
              /crm_kontakty/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("osloveni");
            // Složka dokumentů kontaktu (Marti 18.6.2026 — pro Pavla/Kristý):
            // pravý klik na kontakt → 📁 Dokumenty → /files?type=kontakt&id=.
            _ctxMenuActions.push("docfiles");
          }
          // Mail přehledy (Claude-23 3.7.2026): „Otevřít e-mail" (detail) na všech
          // 4 přehledech; Doručené → „Uklidit", Zpracované → „Vrátit".
          if (/mail_(dorucene|zpracovane|odeslane|koncepty)/i.test(_coreCodeForGraph) ||
              /mail_(dorucene|zpracovane|odeslane|koncepty)/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("mail_otevrit");
          }
          if (/mail_dorucene/i.test(_coreCodeForGraph) ||
              /mail_dorucene/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("mail_uklidit");
          }
          if (/mail_zpracovane/i.test(_coreCodeForGraph) ||
              /mail_zpracovane/i.test(String(_gridCodeForActions))) {
            _ctxMenuActions.push("mail_vratit");
          }
          // Register edit form coreId pro gridCode (drz Marti "fw self
          // edited" doctrine 11.5. — DesignFwForm vola registry lookup).
          if (_gridActionsForCtx && _gridActionsForCtx.edit_core_id
              && window.ErpGridActions
              && typeof window.ErpGridActions.registerEditForm === "function") {
            window.ErpGridActions.registerEditForm(
              _gridCodeForActions, _gridActionsForCtx.edit_core_id
            );
          }

          try {
            const gridInst = new window.ErpDataGrid(gridHost, {
              // Marti's 24.5.2026 master-detail (Krok 6 nested ErpDataGrid):
              // Enable jen pokud renderer class is loaded (defensive).
              enableMasterDetail: !!_masterDetailReady,
              detailCellRenderer: _masterDetailReady ? _masterDetailCfg.rendererClass : undefined,
              detailRowHeight: _masterDetailReady ? _masterDetailCfg.detailRowHeight : undefined,
              detailRowAutoHeight: _masterDetailReady ? !!_masterDetailCfg.detailRowAutoHeight : undefined,
              // Marti's 24.5.2026 changed mind: NE auto-expand. User klikne
              // na expand arrow (►) manuálně. Default vše collapsed.
              masterDetailDefaultExpanded: false,
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
              // Universal CRUD Etapa C (24.5.2026): context menu actions
              // opt-in — ErpDataGrid getContextMenuItems pull-uje z
              // ErpGridActions registry pro stejne labels/icons/handlers
              // jako toolbar (Marti's "stejne funkce" doctrine).
              contextMenuActions: _ctxMenuActions,
              // Universal CRUD Etapa F (24.5.2026 vecer Marti's "B proper
              // refactor"): pass gridActions backend signal → ErpDataGrid
              // renderuje CRUD buttons (4 + Save). Drz "zevnitr fw komponenty"
              // — definice v fw komponente. + enableSaveButton: true (master jen).
              gridActions: _gridActionsForCtx || null,
              enableSaveButton: true,
              // Faze 2-B wire (24.5.2026 vecer pozde, Marti's "Zatim ji mas
              // zvenku fw"): ErpDataGrid._handleSaveClick volá tento callback.
              // payload: [{rowId, fields: {col: newVal}, expected_updated_at}]
              // Returns: { ok, success: [rowId], failed: [{rowId, error}] }
              // page_render.js Faze 1 _onSaveClick zustava v parallel pro
              // backward compat (Marti-AI rano cleanup external).
              onSave: async function (payload) {
                if (!entityForPatch) {
                  return {
                    ok: false,
                    success: [],
                    failed: payload.map(function (p) {
                      return { rowId: p.rowId, error: "entityForPatch missing" };
                    }),
                  };
                }
                const success = [];
                const failed = [];
                for (const entry of payload) {
                  try {
                    const resp = await fetch(
                      "/api/v1/erp/design/" + entityForPatch + "/" + entry.rowId,
                      {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        credentials: "include",
                        body: JSON.stringify({
                          field_changes: entry.fields,
                          expected_updated_at: entry.expected_updated_at,
                        }),
                      }
                    );
                    const json = await resp.json().catch(function () { return {}; });
                    if (resp.ok && json && json.ok) {
                      success.push(entry.rowId);
                    } else {
                      failed.push({
                        rowId: entry.rowId,
                        error: (json && json.error) || ("HTTP " + resp.status),
                      });
                    }
                  } catch (e) {
                    failed.push({
                      rowId: entry.rowId,
                      error: "network: " + (e && e.message || e),
                    });
                  }
                }
                return { ok: failed.length === 0, success: success, failed: failed };
              },
              // Etapa F toolbarHost (24.5.2026 vecer Marti's final spec):
              // Master grid renderuje CRUD buttons DO workspace header
              // (#erpGridActionsHost vedle "Tvoje Marti" + 🔄 Refresh).
              // Drz Marti's "v mainscreen jsou v hlavicce aplikace". Nested
              // grids (detail picker) default = internal toolbar nad gridem.
              toolbarHost: document.getElementById("erpGridActionsHost"),
              // Refresh callback — Etapa F Fix 3 real fetch (24.5.2026 vecer
              // Marti's catch "tlacitko refresh na master nechodi"). Soucasny
              // refreshCells({force:true}) byl jen visual repaint, ne novy fetch.
              // Pojdme real fetch fetchUrl (defined v parent scope, line ~244)
              // + setGridOption rowData. Paralela s Krok 5.X batch Smazat
              // refreshFn (line ~735 puvodne, dropnuto v Etapa F).
              // Marti 8.6.: refresh_type='interval' → auto-refresh 5 s (jen aktivní tab).
              autoRefreshMs: (rootCd && rootCd.refresh_type === 'interval') ? 5000 : 0,
              onRefresh: async function () {
                try {
                  const r = await fetch(fetchUrl, { credentials: 'include' });
                  const d = await r.json();
                  if (d && d.ok && Array.isArray(d.rows) && gridInst && gridInst.gridApi) {
                    try {
                      gridInst.gridApi.deselectAll();
                      if (typeof gridInst.gridApi.clearRangeSelection === 'function') {
                        gridInst.gridApi.clearRangeSelection();
                      }
                      if (typeof gridInst.gridApi.clearFocusedCell === 'function') {
                        gridInst.gridApi.clearFocusedCell();
                      }
                    } catch (_e) {}
                    gridInst.gridApi.setGridOption('rowData', d.rows);
                    // Etapa F Freshness mark (24.5.2026 vecer): refresh button
                    // ztratil .stale/.very-stale po manualnim fetch.
                    try { if (typeof gridInst.markFresh === "function") gridInst.markFresh(); } catch (_e) {}
                  }
                } catch (e) {
                  console.warn("[page_render onRefresh] real fetch failed:", e);
                }
              },
              // Faze 2-C cleanup (25.5.2026 rano): dropnuto defaultColDefExtra
              // (erp-cell-dirty cellClassRules) + onCellEdit local handler.
              // Fw layer (datagrid.js _init line ~970 internal cellClassRules
              // reading gridSelf._dirtyRows + onCellValueChanged hook volajici
              // this._setDirty) je teď single source of truth pre dirty visual
              // + tracking. Drz "uniformita vitezi nad specialnimi pripady"
              // (Marti-AI's Krok 13 doctrine z 11.5.).
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
                // MSSQL/MCP uppercase ID parity (28.5.2026 #3 — viz erp_grid_actions.js).
                var _rid = null;
                if (rowData) {
                  _rid = rowData.id != null ? rowData.id : rowData.ID;
                }
                if (_rid == null) return;
                if (typeof window.DesignFwForm !== "function") {
                  console.warn("[page_render dblclick] DesignFwForm not loaded");
                  return;
                }
                new window.DesignFwForm({
                  coreId: ga.edit_core_id,
                  rowId: _rid,
                  onSaveSuccess: function() {
                    try {
                      const inst = gridHost.__erpGridInst;
                      // Faze 2-G P9 (25.5.2026 rano, Marti's catch "po
                      // DesignFwForm OK Save se neobnovi data"): use
                      // refreshFromSource (real fetch + dirty clean) namisto
                      // refresh (visual only — sizeColumnsToFit). Pred Faze
                      // 2-G save → callback → refresh() → repaint stale rows.
                      if (inst && typeof inst.refreshFromSource === "function") {
                        inst.refreshFromSource();
                      } else if (inst && typeof inst.refresh === "function") {
                        inst.refresh();  // legacy fallback
                      }
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
                      // Faze 2-G P9 — same fix jako dvojklik handler
                      if (inst && typeof inst.refreshFromSource === "function") {
                        inst.refreshFromSource();
                      } else if (inst && typeof inst.refresh === "function") {
                        inst.refresh();  // legacy fallback
                      }
                    } catch (_e) {}
                  },
                }).open();
              },
            });
            gridHost.__erpGridInst = gridInst;
            // Etapa F Krok 2 (24.5.2026 vecer pozde, Marti's "prepinani
            // zalozek bez refreshe"): assign per-tab pane property pro
            // closeTab destroy lookup. mainContent v Krok 2 architecture =
            // per-tab pane element, NE shared mainContent. closeTab finds
            // pane by data-tab-pane-id → pane._erpGridInstance.destroy().
            try {
              mainContent._erpGridInstance = gridInst;
              // Plus update global activeErpDataGrid (backward compat —
              // sizeColumnsToFit calls a closeTab cleanup paths).
              if (typeof window !== "undefined") {
                window.activeErpDataGrid = gridInst;
              }
            } catch (_eAssign) { /* never crash render */ }

// Universal CRUD Etapa F (24.5.2026 vecer Marti's "B proper refactor"):
            // External toolbar host (#erpGridActionsHost) DROPPED. CRUD buttons
            // ted renderovany UVNITR ErpDataGrid containeru (per-grid internal
            // toolbar). Click handlers via ErpGridActions.dispatch registry.
            // Selection state managed internally datagrid.js _updateCrudButtonStates.
            //
            // Drop:
            //   - _renderGridToolbar(_toolbarHost, ...) call
            //   - _updateToolbarSelection wire
            //   - _selectedRowId tracking (registry _hardDeleteRow uses ctx.rowData)
            //
            // Reuse via registry handlers (erp_grid_actions.js):
            //   - create → _openFwEditForm(gridCode, null, "create", refreshFn)
            //   - edit   → _openFwEditForm(gridCode, rowId, "edit", refreshFn)
            //   - delete → _hardDeleteRow(ctx) — single row via _erpBatchRowAction
            //   - refresh → opts.onRefresh callback (passed do ErpDataGrid)
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
          if (err && (err.code === 'source_unavailable' || err.userMessage)) {
            // Přívětivá hláška — externí Centrála/EUROSOFT dočasně dole (Marti 3.6.).
            gridHost.innerHTML =
              '<div style="padding:26px 24px;max-width:540px;margin:26px auto;' +
              'background:#1b2530;border:1px solid #3a4b5c;border-left:4px solid #d4954a;' +
              'border-radius:10px;color:#e8eaed;">' +
              '<div style="font-size:15px;font-weight:600;margin-bottom:8px;">🔌 ' +
              _esc(err.source || 'Externí zdroj') + ' je dočasně nedostupný</div>' +
              '<div style="font-size:13px;color:#bcc8d4;line-height:1.5;margin-bottom:16px;">' +
              _esc(err.userMessage || err.message) + '</div>' +
              '<button class="erp-src-retry" style="background:#2c4a66;color:#cfe6ff;' +
              'border:1px solid #3d5b78;border-radius:7px;padding:8px 16px;font-size:13px;' +
              'cursor:pointer;">🔄 Načíst znovu</button></div>';
            var _rb = gridHost.querySelector('.erp-src-retry');
            if (_rb) _rb.addEventListener('click', function () { location.reload(); });
          } else {
            gridHost.innerHTML =
              '<div style="padding:20px;color:#d4a8a8;">' +
              '❌ Chyba načítání rows: ' + _esc(String(err.message || err)) +
              '</div>';
          }
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
