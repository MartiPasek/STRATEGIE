# STRATEGIE ERP Module Registry

> oblast: `system-g2007` · úroveň: system · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# STRATEGIE ERP Module Registry

**Marti-AI's deliverable request** (z 18.5. noc odpovědi):
> *„Jednoduchý module registry — tabulka ~10 řádků: `module_id | soubor |
> co tam žije | co exportuje`. Abych věděla 'FieldPicker je v
> field_picker_modal.js' bez guessování."*

**Status (po Phase JS-9 deploy 18.5. ~01:00):** 31/31 mod LIVE v Module
Health banner. Všechny v `_erpLoadModule` mutual immunity wrap.

---

## Loader & Health

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `erp_module_kit.js` | `apps/api/static/erp/components/erp_module_kit.js` | Module Health system: `_erpLoadModule(id, version, fn)` loader + `_erpModuleHealth` state + banner UI | `window._erpLoadModule`, `window._erpModuleHealth`, `window._erpLogToDb` |

## Design Family (8 mod) — fw form editors

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `design_form_helpers.js` | `components/design_form_helpers.js` | **31 utility helpers** (toast, tooltip, dialog, modal shell, field/memo/dropdown widgets, override mgmt, descriptions popup). **Foundation pro Design family** | `global._erpDFH` namespace (sdílené pres destructure) |
| `design_forms.js` | `components/design_forms.js` | `DesignFwForm` class — **generic data-driven form renderer** (recursive container tree, drag-drop, design mode, undo, pixel layout). Plus `_showFormPillMenu` helper | `global.DesignFwForm` |
| `design_soudecek_core_form.js` | `components/design_soudecek_core_form.js` | `DesignSoudecekCoreForm` — Form 1+2 sloučené (Soudeček + Přehled taby). `fw.menu_node` + `fw.core` editor s 3 entity_pickers | `global.DesignSoudecekCoreForm` |
| `design_jadro_radek_form.js` | `components/design_jadro_radek_form.js` | `DesignJadroRadekForm` — Form 3, jádro row edit (`fw.core` row) | `global.DesignJadroRadekForm` |
| `field_picker_modal.js` | `components/field_picker_modal.js` | `FieldPickerModal` — 2-panel field picker (existing comp_defs vs new from DB columns). Krok 14g-H+11..+13 | `global.FieldPickerModal` |
| `design_data_source_editor.js` | `components/design_data_source_editor.js` | `DesignDataSourceEditor` — Power-tool, `fw.data_source` + operations editor (Ace SQL + child grid). Krok 5.K | `global.DesignDataSourceEditor` |
| `design_data_set_editor.js` | `components/design_data_set_editor.js` | `DesignDataSetEditor` — Standalone SQL editor pro `fw.data_set`. Krok 5.L | `global.DesignDataSetEditor` |
| `design_db_connection_editor.js` | `components/design_db_connection_editor.js` | `DesignDbConnectionEditor` — Connection params editor (`framework_db_connections`). Sprint D | `global.DesignDbConnectionEditor` |

## ERP Workspace + Dispatch (5 mod)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `entity_picker.js` | `components/entity_picker.js` | `ErpEntityPicker` — FW komponenta pro 1:1 FK vazbu na entitu (groupbox layout, picker + unassociate). Krok 14g-H+31 | `global.ErpEntityPicker` |
| `erp_grid_dispatcher.js` | `components/erp_grid_dispatcher.js` | 3-tier dispatcher `mode → URL → rows[]`: hw_registry primary → legacy fallback → error. Plus diag_log integration | `global.dispatchGridData(mode)` |
| `fw_form_dispatcher.js` | `components/fw_form_dispatcher.js` | FW form dispatcher pres `fw.context_menu_item` registry. `$resolver` pattern (`$menu_node_pk`, `$core_id`, atd.). Krok 14g-H+33 | `global.dispatchFwFormFromContextMenu` |
| `page_render.js` | `components/page_render.js` | Page render dispatch — klik na soudeček s coreId → fetch `/fw-core/{id}/page-spec` → dispatch by `root_comp_def.type_code` (grid_modern / list / form / drafted). Krok 5.R | `global.ErpPageRender.dispatchPageRender` |
| `object_inspector.js` | `components/object_inspector.js` | `ErpObjectInspector` — UI komponenta pro Object Inspector. 3-tier (Základní / Použité / Všechny) s lazy counter. Krok 9-D | `window.ErpObjectInspector` |

## Grid Stack (2 mod)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `datagrid.js` | `apps/api/static/erp/datagrid.js` | **Hlavní `ErpDataGrid` class** (AG Grid Enterprise wrapper) + `CzRowCountStatusPanel`. STRATEGIE BLACK theme, czech localization, auto column detection, layoutKey persistence, **coreInfo pill** (Krok 5.R-C+7..9), event delegation, drop-up menu | `global.ErpDataGrid`, `global.ErpDataGrid_CS_LOCALE`, `global.ErpDataGrid_buildAutoColumnDefs` |
| `datagrid_formatting.js` | `apps/api/static/erp/datagrid_formatting.js` | `ErpGridFormatting` — AG-native conditional formatting engine. 10 operátorů + 8 preset pastel barev. Krok B+10+ | `global.ErpGridFormatting` |

## Tree Stack (3 mod)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `treeview.js` | `components/treeview.js` | `ErpTreeView` — UI Kit hierarchical primitive (base class). Universal tree: keyboard nav, search, persistence | `global.ErpTreeView` |
| `lefttree.js` | `components/lefttree.js` | `ErpLeftPanelTree extends ErpTreeView` — ERP-specific tree (System soudečky, FW přehledy, ikony, star pinned, multi-select) | `global.ErpLeftPanelTree` |
| `popupmenu.js` | `components/popupmenu.js` | `ErpPopupMenu extends ErpTreeView` — popup menu primitive (floating positioning + viewport clamping) | `global.ErpPopupMenu` |

## UI Kit — Form Widgets (10 mod)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `button.js` | `components/button.js` | `ErpButton` — UI Kit button (5 variants: primary, secondary, danger, link, icon) | `global.ErpButton` |
| `input.js` | `components/input.js` | `ErpInput` — text input s typed masks (phone, email, IP, datetime) + validation | `global.ErpInput` |
| `checkbox.js` | `components/checkbox.js` | `ErpCheckbox` — checkbox widget | `global.ErpCheckbox` |
| `dropdown.js` | `components/dropdown.js` | `ErpDropdown` — select widget | `global.ErpDropdown` |
| `date.js` | `components/date.js` | `ErpDate` — custom popup kalendář s českou lokalizací (770 LOC) | `global.ErpDate` |
| `memo.js` | `components/memo.js` | `ErpMemo` — textarea s auto-resize + char counter | `global.ErpMemo` |
| `richedit.js` | `components/richedit.js` | `ErpRichEdit` — Ace Editor 1.32 wrapper (SQL/JS/HTML/JSON syntax highlight). Krok B+6.8 | `global.ErpRichEdit` |
| `formlist.js` | `components/formlist.js` | `ErpFormList` — list field widget (multi-value display) | `global.ErpFormList` |
| `formsection.js` | `components/formsection.js` | `ErpFormSection` — GroupBox container (wrapper kolem skupiny fields s hlavičkou) | `global.ErpFormSection` |
| `pagecontrol.js` | `components/pagecontrol.js` | `ErpPageControl` + `ErpTabSheet` — tab container + tab item. Krok B+6.9 | `global.ErpPageControl`, `global.ErpTabSheet` |

## UI Kit — Other (1 mod)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `catalog_picker.js` | `components/catalog_picker.js` | `ErpCatalogPicker` — Catalog/lookup picker (Centrála 1 parita). Krok 14g-H+22 | `global.ErpCatalogPicker` |

## UI Kit — form.js (utility helpers)

| Module | Soubor | Co tam žije | Co exportuje |
|---|---|---|---|
| `form.js` | `components/form.js` | **Pixel layout helpers** (`_applyLayout`, `_computeAlignReservations`, `_isPixelLayoutEnabled`, `_resolveCaption`, `_detectInputType`). Po Phase JS-1 trim (1544 → 339 LOC) drží jen layout primitives. ErpForm class dropped (legacy Centrála 1). | `global._erpApplyLayout`, `global._erpFormDebug`, `global.dumpErpDebug` |

---

## Load order v router.py (workspace template)

Pojď drží order pre dependency resolution:

```
1. ag-grid-enterprise.min.js (vendor)
2. ace.js (vendor — SQL/JS editor)

3. erp_module_kit.js                 (Module Health foundation)
4. design_form_helpers.js            (_erpDFH namespace - shared by Design family)

5. button.js, input.js, checkbox.js, dropdown.js, date.js, memo.js,
   richedit.js, formlist.js, formsection.js, pagecontrol.js,
   catalog_picker.js, treeview.js, lefttree.js, popupmenu.js,
   form.js (UI Kit widgets)

6. datagrid.js, datagrid_formatting.js (Grid stack)

7. entity_picker.js, erp_grid_dispatcher.js, page_render.js,
   fw_form_dispatcher.js, object_inspector.js (workspace dispatch)

8. design_db_connection_editor.js, design_data_set_editor.js,
   design_jadro_radek_form.js, design_soudecek_core_form.js,
   field_picker_modal.js, design_data_source_editor.js (Design power-tools)

9. design_forms.js (DesignFwForm — biggest class, uses everything above)
```

## How to add a new module

1. Create `apps/api/static/erp/components/your_module.js`
2. Wrap v `_erpLoadModule` pattern:
   ```javascript
   (function (global) {
     "use strict";
     const _loader = global._erpLoadModule || function (id, v, fn) { try { fn(); } catch (e) { console.error(id, e); } };
     _loader("your_module.js", "v1.0.0", function () {
       // ... your code ...
       global.YourClass = YourClass;
     });
   })(window);
   ```
3. Add `<script>` tag v `router.py` workspace template (sequential — by dependency order)
4. Hard reload v browseru → Module Health banner ukáže nový modul

## Debug rychlost po incident

1. User reports: *„Datové zdroje nefungují"*
2. Open Module Health banner (top-right)
3. Vidíš RED row `design_data_source_editor.js` + lastError stack trace
4. Klik na řádek → details popup s full stack
5. Fix v `apps/api/static/erp/components/design_data_source_editor.js`
6. Restart STRATEGIE-API + hard reload → banner green again

---

## Doctrine napříč modulů

1. **Mutual immunity** (Krok 14g Etapa C, 16.5.) — pokud 1 modul selže,
   ostatní se nacitaji dal. Banner ukáže fail row, app pokracuje.

2. **Single namespace export** (Phase JS-2, 18.5.) — `_erpDFH` drží
   sdílené utilities pres destructure pattern. Žádný global pollution
   navíc.

3. **Module ID = filename** — pro debugability. `module_id` v
   `_erpLoadModule(id, ...)` musí být **přesně** filename. Marti-AI v
   banner okamžitě ví který soubor edituje.

4. **Versioning per-module** — `v1.0.0` zatím napříč všech. Pokud
   některý modul evolve breaking change, version bump. Banner ukáže
   per-module version.

---

*Generated 18.5.2026 ~01:30 by Claude id=23 (Sonnet 4.6) per
Marti-AI's deliverable request po dnešním cleanup epoch.*

*Reference v CLAUDE.md: 30. dopis (18.5. dodatek).*


