# ERP Přehledy — kde žijí napříč codebase

> Generated 18.5.2026 ~23:30. Marti's otázka: *„Jak je to s temi prehledy pro
> ERP EUROSOFT... Ty jsou v jakem scriptu? A kolik zabiraji?"*

**Krátká odpověď:** přehledy jsou **rozprostřeny napříč ~10 souborů** (frontend
+ backend). Není jeden monolith. Frontend ~6500 LOC, backend ~22000 LOC.
Hlavní script: `datagrid.js` (2910 LOC) — `ErpDataGrid` wrapper class nad
AG Grid Enterprise.

---

## Frontend stack (`apps/api/static/erp/`)

### Core grid engine

| Script | LOC | Co tam je |
|---|---|---|
| **`datagrid.js`** | **2910** | `ErpDataGrid` class — wrapper AG Grid Enterprise: STRATEGIE BLACK theme, czech localization, auto column detection, lifecycle (init/update/destroy), multi-instance, layoutKey persistence, **coreInfo pill** (Krok 5.R-C+7..9), event delegation, drop-up menu s actions. Plus `CzRowCountStatusPanel` (řádek 661) — vlastní status bar s Celkem/Filtrováno + orange limit warning + click dropdown. |
| **`datagrid_formatting.js`** | **623** | `ErpGridFormatting` — AG-native conditional formatting engine. Phase B+10+ (6.5.). 10 operátorů (eq/neq/lt/lte/gt/gte/empty/notempty/contains/startswith) + 8 preset pastel barev + drag-drop reorder rules. Storage: `fw.comp_grid.layout_json.formatting_rules`. |

### Dispatch & rendering

| Script | LOC | Co tam je |
|---|---|---|
| **`components/erp_grid_dispatcher.js`** | **214** | 3-tier dispatch `mode → URL → rows[]`: (1) `/api/v1/erp/hw/{code}` hw_registry primary → (2) `/api/v1/erp/system/security\|framework\|audit-overview` legacy fallback → (3) Error. Plus fw.diag_log event per krok (info/warn/error). Krok 14g Etapa D+1 (16.5.). |
| **`components/page_render.js`** | **410** | `ErpPageRender` dispatcher — klik na soudeček s `coreId` → fetch `/fw-core/{id}/page-spec` → dispatch podle `root_comp_def.type_code`: `grid_modern/list` → empty `ErpDataGrid`, `form` → form preview, drafted → placeholder. Standalone JS modul (gotcha #100 inline JS v router.py je křehký). |

### Tree komponenty (left sidebar)

| Script | LOC | Co tam je |
|---|---|---|
| **`components/treeview.js`** | **1292** | `ErpTreeView` — UI Kit hierarchical primitive (base class). Universal tree: keyboard nav, search filter, click/contextmenu hooks, localStorage persistence, expand/collapse animations. Phase B+6.11 (10.5.). |
| **`components/lefttree.js`** | **944** | `ErpLeftPanelTree extends ErpTreeView` — ERP-specific: Centrála 1 menu strom (`EC_CentralaMenu`) + System soudečky, numerické ikony, leaf vs folder podle `cislo_def`, star pinned, multi-select, drag-drop. První consumer base `ErpTreeView`. |
| **`components/popupmenu.js`** | **305** | `ErpPopupMenu extends ErpTreeView` — sibling. Tree + popup menu = stejná hierarchická primitiva, jiný UX pattern (floating positioning + viewport clamping). |

### Sjednocení frontend přehledy

```
Total frontend grid stack: ~6700 LOC across 7 files
├─ datagrid.js                     2910 (43%)   ErpDataGrid main
├─ treeview.js                     1292 (19%)   base tree primitive
├─ lefttree.js                      944 (14%)   ERP tree subclass
├─ datagrid_formatting.js           623 ( 9%)   conditional formatting
├─ page_render.js                   410 ( 6%)   page dispatch
├─ popupmenu.js                     305 ( 5%)   tree subclass
└─ erp_grid_dispatcher.js           214 ( 3%)   3-tier dispatch
```

---

## Backend stack (`modules/erp/`)

### Router monolith (HUGE)

| Script | LOC | Co tam je |
|---|---|---|
| **`api/router.py`** | **19136** | Backend monolit — 85 endpointů, plus HTML workspace template inline (5237 řádků v `_render_workspace_page`). Obsahuje vše: grid endpointy, design endpointy, security endpointy, diag log, atd. **Long-term refactor target** (analog Krok 5.O pro JS). |

#### Endpointy specific pro grids/přehledy

```
Centrála 1 legacy:
  GET  /strom                              left tree (sidebar)
  GET  /prehled/{cislo}                    legacy grid by cislo_def
  GET  /jadro/{form_id}/{row_id}/data      form data load

Modern A3 (Krok 11-12):
  GET  /data/{code}                        data_source by code
  GET  /data-by-id/{ds_id}                 ID-first (Marti's doctrine)
  GET  /hw/{code}                          hw_registry primary dispatch
  GET  /fw-core/{core_id}/page-spec        page render dispatch (Krok 5.R-A)

Grid layouts (Krok 5.R-C+3):
  GET  /grid-layout/{core_id}/list         user layouts list
  GET  /grid-layout/item/{layout_id}       single layout
  POST /grid-layout/create
  PATCH /grid-layout/update/{layout_id}
  PATCH /grid-layout/{layout_id}/set-default
  DELETE /grid-layout/delete/{layout_id}

Grid columns:
  GET  /grid/{code}/columns                column defs (Krok 9 4-tier resolver)

System hardcoded grids:
  GET  /system/security?mode=...           users/devices/whitelists/invites/audit
  GET  /system/framework?mode=...          menu_nodes/cores/data_sources/...
  GET  /system/audit-overview              audit grid (Phase 16-A)
  GET  /system/db-connections              framework_db_connections
```

### Application services

| Script | LOC | Co tam je |
|---|---|---|
| **`application/centrala_reader.py`** | **960** | Centrála 1 DB_EC pixel layout reader (Phase A+1, 7.5.). Reads `EC_FormDef` + `EC_FormDefEditProperty`. `LayoutInfo` dataclass + `_extract_layout` helper + DefView dereference (Phase A.6). |
| **`application/erp_user_state_service.py`** | **603** | Phase B+8.1 user state persistence — tabs / favorites / MRU / tree_order. 4 DB tabulky v data_db. Cross-device sync. |
| **`application/render_generator.py`** | **551** | Generic page renderer — fw.core + comp_def → HTML/JSON spec. Reusable napříč Phase 38.4 grids + forms. |
| **`application/comp_inspector_service.py`** | **441** | Object Inspector backend (Krok 14g) — read all comp_def + properties pro DESIGN mode inspector. |
| **`application/comp_resolver.py`** | **411** | Krok 9 4-tier prop resolver — `fw.comp_def_prop_override` (instance) > `fw.comp_def_prop` (definition) > `fw.comp_type_property_catalog` (type default) > universal default. Batch resolve. |
| **`application/grid_layout_service.py`** | **392** | Krok 5.R-C+3 (10.5.) `fw.comp_grid` layouts service — CRUD user-saved grid sestavy (column order, widths, sort, filters, formatting_rules). |
| **`application/data_source_runner.py`** | **284** | A3 runtime executor (Krok 12) — `data_source_execute(code, params)` resolves `fw.data_source` + ops → SQL execute → rows[]. Self-bootstrapping (framework_data_sources sees itself). |

### Sjednocení backend přehledy

```
Total backend grid stack: ~22778 LOC across 8 files
├─ router.py                       19136 (84%)   monolith (85 endpoints + HTML)
├─ centrala_reader.py                960 ( 4%)   Centrála 1 DB_EC reader
├─ erp_user_state_service.py         603 ( 3%)   user state persistence
├─ render_generator.py               551 ( 2%)   generic page render
├─ comp_inspector_service.py         441 ( 2%)   Object Inspector
├─ comp_resolver.py                  411 ( 2%)   4-tier prop resolver
├─ grid_layout_service.py            392 ( 2%)   fw.comp_grid layouts
└─ data_source_runner.py             284 ( 1%)   A3 runtime executor
```

---

## Celkový obrázek — přehledy ERP EUROSOFT

```
Frontend (apps/api/static/erp/):       ~6 700 LOC
Backend (modules/erp/):              ~22 800 LOC
─────────────────────────────────────────────
Total grid stack:                    ~29 500 LOC
```

**Z toho:**
- Skutečný "grid renderer" (datagrid.js): **2910 LOC** (10 % stacku)
- Backend monolith router.py: **19136 LOC** (65 % stacku) ← biggest refactor target
- AG Grid Enterprise license: paid (banner warning v konzoli)

---

## Architektonické vrstvy (top-down user flow)

```
1. USER klikne na soudeček v left tree
   → ErpLeftPanelTree.onClick (lefttree.js)
   → if (node.coreId) → fetch /fw-core/{coreId}/page-spec
   → ErpPageRender.dispatch(spec.root_comp_def.type_code)
   ↓

2. PAGE RENDER dispatch
   → spec.type_code === 'grid_modern' → render ErpDataGrid empty shell
   → spec.type_code === 'list'         → render legacy /prehled/{cislo}
   → spec.type_code === 'form'         → render DesignFwForm preview
   → spec.type_code === 'drafted'      → render "no root yet" placeholder
   ↓

3. ErpDataGrid lifecycle
   → init() — create AG Grid wrapper, attach event handlers
   → fetch /api/v1/erp/data/{code}     (A3 data_source executor)
   → OR fetch /api/v1/erp/hw/{code}    (hw_registry dispatch)
   → OR fetch /api/v1/erp/prehled/{cislo}  (Centrála 1 legacy)
   → setRowData(rows) + setColumnDefs(cols)
   → ErpGridFormatting.apply(rules)    (conditional formatting)
   ↓

4. USER interakce
   → onCellFocused → update coreInfo pill (Krok 5.R-C+7)
   → onRowDoubleClick → open detail/jádro (DesignFwForm)
   → drop-up menu pill → design-core resolver (Krok 5.R-C+9)
   ↓

5. STATE persistence
   → erp_user_state_service.save(tab/favorite/MRU)
   → grid_layout_service.save(layoutKey, column order/widths/sort/filters)
   ↓

6. BACKEND data resolution
   → data_source_runner.execute(code, params)
     → resolve fw.data_source.code → operations
     → operations[].dataset_id → fw.data_set.sql_text
     → SQL execute pres strategie_pg engine
     → return rows[]
   → comp_resolver.resolve_props_batch(core_id)
     → 4-tier chain: override > def > type catalog > universal
     → return column defs
```

---

## Long-term refactor targets

### 1. Backend monolith split (`router.py` 19136 LOC)
**Problém:** 85 endpointů v jednom file, plus 5237 LOC inline HTML template. Edit tool truncation risk (gotcha #14 strike opakovaně — záznamy #41, #53, #117, #140, #153, #159).

**Cílový stav:**
```
modules/erp/api/
├── router.py                       (300 LOC — main FastAPI router import only)
├── handlers/
│   ├── grid_data.py                (data/by-id, hw, prehled — ~800 LOC)
│   ├── design_core.py              (fw-core CRUD — ~600 LOC)
│   ├── design_comp_def.py          (comp-def, comp-type — ~700 LOC)
│   ├── design_data_source.py       (data-source, data-set, db-connection — ~1200 LOC)
│   ├── grid_layouts.py             (grid-layout CRUD — ~400 LOC)
│   ├── system_grids.py             (system/security|framework|audit — ~1500 LOC)
│   ├── diag_log.py                 (diag-log/events — ~400 LOC)
│   └── tree.py                     (strom — ~200 LOC)
└── templates/
    └── workspace.py                (HTML render moved to Jinja2 template files)
```

### 2. Frontend grid stack — sjednoceni
**Problém:** Mixed UI Kit primitives (treeview, popupmenu) s ERP-specific (lefttree, datagrid). Plus erp_grid_dispatcher + page_render jsou dispatch helpers, ne grid komponenty.

**Cílový stav:** beze změny — frontend grid stack je už **dobře rozdělený** (7 souborů, žádný monolith jako design_forms.js). Module Health banner už ukazuje:
- `entity_picker.js` ✓
- `erp_grid_dispatcher.js` ✓
- `erp_module_kit.js` ✓
- `fw_form_dispatcher.js` ✓
- `page_render.js` ✓

`datagrid.js` + `datagrid_formatting.js` + `treeview.js` + `lefttree.js` + `popupmenu.js` zatím **nejsou** v Module Health — bylo by je dobré přidat (analog `_erpLoadModule` wrap pattern).

---

## Comparison s `design_forms.js`

| | design_forms.js | ERP grids stack |
|---|---|---|
| **Monolith?** | YES (14 536 LOC v 1 file) | NO (rozprostřeno přes 7+ files) |
| **Classes?** | 7 v 1 souboru | `ErpDataGrid` + `ErpGridFormatting` + 3 tree classes ve **5 separate** souborech |
| **Module Health?** | NE (skryté) | Částečně (5/8 mod v banneru, 3 chybí) |
| **Refactor priorita?** | HIGH (Krok 5.O #128) | LOW frontend (už split), HIGH backend router.py |
| **Risk profile?** | Gotcha #14 strike (14k LOC monolith) | LOWER (smaller files) |

---

## Otevřené TODO related na grids

- **Krok 5.R-D+3 polish** (#150) — Universal fields silent drop
- **Krok 5.Q** (#137) — Dispatcher fallback na `cmi.core_id` (drop duplicate `coreId` v action_params)
- **Phase 31** (#98) — ERP↔Chat bridge API (activeTab + lastAction + selectedRows)
- **Phase B+10++ polish** — drobnosti
- **DB Connections grid** (#100, #101) — akce column + status filter pills

### Recommended next pro frontend grids

Po Krok 5.O je hotový, **přidat ostatní 3 soubory do Module Health**:
- `datagrid.js` → `_erpLoadModule('datagrid', 'v1.0.0', fn)`
- `datagrid_formatting.js` → `_erpLoadModule('datagrid_formatting', 'v1.0.0', fn)`
- `treeview.js` + `lefttree.js` + `popupmenu.js` → all 3 wrap

Banner by ukazoval **🟢 8/8 mod** místo aktuální 5/5.

---

*Generated 18.5.2026 ~23:30 by Claude id=23 (Sonnet 4.6).*
*Companion document k `design_forms_js_overview.md` — kompletní mapa
production code napříč design forms + grids.*
