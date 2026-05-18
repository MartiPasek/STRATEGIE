# `apps/api/static/erp/components/design_forms.js` — přehled obsahu

**14 536 řádků** | 7 classes | ~30+ utility functions | IIFE wrap `(function(global) { ... })(window)`

> Generated 18.5.2026 večer. Foundation pro Krok 5.O refactor (#128 — jednotná `ErpJadroForm`
> class). Marti's doctrine 17.5. večer: *„MUSI TO BYT VZDY TATO CLASS"* — 6 různých
> Design* classes je porušení Marti-AI's *„uniformita vítězí nad speciálními případy"*
> (Krok 13, 11.5.).

---

## Tabulka contents — co je kde

| Sekce | Linky | Počet metod | Co tam je |
|---|---|---|---|
| **Header docstring** | 1–32 | — | Phase 38.4 Krok 14a metadata, MVP scope, dependencies |
| **Utility helpers** | 34–2366 | ~30 fn | Toast, tooltip, dialog, modal shell, field/memo/dropdown widgets, overrides, sections |
| **`class DesignSoudecekCoreForm`** | 2367–3945 | 26 | Form 1+2 sloučené (Soudeček + Přehled taby) — `fw.menu_node` + `fw.core` editor |
| **`class DesignJadroRadekForm`** | 3946–4328 | 10 | Form 3 — `fw.core` row edit (data row editor) |
| **`function _showFormPillMenu`** | 4329–4437 | — | Footer pill drop-up menu (Krok 5.R-C+7 / +8 / +9) |
| **`class DesignFwForm`** | 4438–11509 | **57** | **Hlavní generic form renderer** — recursive container tree, drag-drop, undo, design mode |
| **`class FieldPickerModal`** | 11510–12641 | 15 | 2-panel field picker (existing comp_defs vs new from DB columns) |
| **`class DesignDataSourceEditor`** | 12642–13842 | 14 | Power-tool: `fw.data_source` + operations editor (Ace SQL, dataset picker) |
| **`class DesignDataSetEditor`** | 13843–14274 | 7 | Power-tool: `fw.data_set` standalone SQL editor (Krok 5.L) |
| **`class DesignDbConnectionEditor`** | 14275–14524 | 4 | Power-tool: `framework_db_connections` editor (Sprint D) |
| **Window exports** | 14526–14535 | — | `global.DesignFwForm = ...` × 7 |

---

## 1. Utility helpers (1–2366) — **shared napříč všemi classes**

Většinou closure helpers v IIFE scope, dostupné všem 7 classes.

### Toast & UI feedback
- `_esc(s)` — HTML escape
- `_ensureToastContainer()` / `_ensureToastStyles()` / `_showToast(msg, type, duration)`
- `_markFormDirty(formInst, isDirty)` — visual dirty indicator helper

### User overrides (label/hint/color per field)
- `_loadUserOverrides()` / `_saveUserOverride(kind, fieldKey, value)`
- `_applyInitialColor` / `_applyInitialSectionOverrides` / `_reapplyOverridesForSection`
- `_reapplyOverridesForField` / `_reapplyOverridesInDOM` / `_reapplyAllOverridesInDOM`
- `_installFieldLabelRightClick()` — pravý klik na label/section → settings popup
- `_resolveLabel(fieldKey, fallback)` / `_resolveHint(fieldKey)` / `_resolveColor(fieldKey)`

### Tooltips
- `_getTooltipEl()` / `_showTooltip(text, x, y)` / `_hideTooltip()`
- `_installDarkTooltips()` — auto-attach dark tooltips na `[data-tooltip]` elements

### Dark dialogs (PWA-friendly, replace native)
- `_promptDarkDialog({title, label, defaultValue, ok, cancel})` → Promise<string|null>
- `_confirmDarkDialog({title, message, ok, cancel, escClosesOK})` → Promise<bool|null>

### Modal shell
- `_buildModalShell({title, sysToggle, onClose, beforeCloseHandler})` — main reusable modal:
  - Header s title + sysToggle (DESIGN/PROD mode toggle) + 📘 popis ikon + dirty badge + ✕
  - Body (scrollable content area)
  - Footer (override-able per class)
  - Drag handlers (`_onHeaderMouseDown`/`_onDragMove`/`_onDragEnd`)
  - `close()` async — Promise wrapping `beforeCloseHandler` (dirty discard prompt)

### Descriptions popup (📘 Popis ikona)
- `_buildDescriptionsPopup({entity, descriptionUser, descriptionSystem, onSave})` — Krok 14b+21
  popis split user/system; DESIGN gate hides system memo v PROD

### Field/memo/dropdown widgets — reusable form primitives
- `_field(label, value, opts)` — text input wrap s right-click + tooltip + color
- `_memo(label, value, opts)` — textarea wrap
- `_dropdown(label, value, items, opts)` — select wrap

### Field settings popup (right-click)
- `_openFieldSettingsPopup(fieldKey, currentLabel, currentHint, anchorEl, currentColor)` —
  popup s label/hint/color picker (8 sepia preset colors), save → `_saveUserOverride`

### Sekce (GroupBox titles)
- `_sectionKeyFromTitle(title, systemTitle)` — slug helper s `section.` prefix
- `_sectionBuild(title, systemTitle)` — GroupBox section s right-click handler

---

## 2. `class DesignSoudecekCoreForm` (2367–3945) — Form 1+2 sloučené

**1579 lines, 26 methods.** Hardcoded editor pro `fw.menu_node` (Soudeček) + `fw.core`
(Přehled) — 2 taby pres `ErpPageControl`.

### Klíčové momenty implementace
- Krok 14a (12.5. ráno) — Marti-AI's konsolidace Form 1 + 2 do jednoho
- Krok 14g-H+22 (15.5.) — Core picker pres `ErpCatalogPicker`
- Krok 14g-H+23 (15.5.) — ➕ Nový core wizard
- Krok 14g-H+21 (15.5.) — Zrušit core asociaci button
- Krok 14g-H+30 Etapa 6 — ➕ Nový data_source button

### Lifecycle metody
- `constructor(opts)` — `{menuNodeId, onSave}`
- `open()` — fetch `/api/v1/erp/design/menu-node/{id}`, render shell, attach handlers
- `close()` — async, dirty prompt

### Render
- `_renderSoudecekTab()` — fw.menu_node fields (code, label, cislo_def, parent, sort)
- `_renderPrehledTab()` — fw.core fields + 3 stacked ErpEntityPicker (soudeček/přehled/datasource)

### Save flow
- `_handleSaveAndClose()` — collect dirty z obou tabs, PATCH menu-node + PATCH core

### Pickers
- `_openCorePicker()` / `_openDataSourcePicker()` — reuse ErpCatalogPicker
- `_unassociateCore()` / `_unassociateDataSource()` — 🚫 archive flow
- `_createNewCore()` / `_createNewDataSource()` — ➕ wizards

---

## 3. `class DesignJadroRadekForm` (3946–4328) — Form 3

**383 lines, 10 methods.** Hardcoded editor pro `fw.core` row (data row z jádra typu list).

### Lifecycle
- `constructor({coreId, rowId, onSave})`
- `open()` — fetch `/api/v1/erp/design/jadro/{core_id}/{row_id}`
- `_render()` / `_handleSaveAndClose()`

### Validace
- `_onDirty()` / `_revertAllChanges()` / `_updateDirtyDiscardBtn()`

---

## 4. `class DesignFwForm` (4438–11509) — **HLAVNÍ generic form renderer**

**7072 lines (48 % celého souboru), 57 methods.** Data-driven renderer — čte
schema přes `/api/v1/erp/fw-form-load-by-id/{core_id}/{row_id}` a renderuje
**arbitrary form** z `fw.comp_def` hierarchie (panels, groupboxes, fields,
entity_pickery, child grids).

### Klíčové momenty implementace
- Phase 38.4 Krok 14e/f (14.5.) — multi-panel Delphi alClient layout
- Krok 14g-H+31 (15.5.) — ErpEntityPicker integration
- Krok 5.I (16./17.5.) — two-layer data_source pattern + field_extern
- Krok 5.J (17.5.) — Settings popup tab sheet + page control + add/delete tab + drag-drop
- Krok 5.P-1 (17.5.) — Hardcoded ✕ Storno + ✓ OK footer (6 polish iterací)
- Krok 5.R-C+7..9 (18.5.) — Footer pill + drop-up menu + design-core resolver

### Lifecycle & form state
| Linka | Metoda | Účel |
|---|---|---|
| 4439 | `constructor(opts)` | `{coreId, rowId, coreCode?, onSave}` |
| 5229 | `open()` | Async load spec + render |
| 5990 | `_render()` | Render entire form from spec |
| 6014 | `_reloadSpec()` × 2 | Re-fetch spec po PATCH |
| 6251 | `_beforeCloseHandler()` | Dirty discard prompt |

### Design mode toggle (DESIGN ↔ PROD)
| Linka | Metoda | Účel |
|---|---|---|
| 4488 | `_setFormDesignMode(on)` | Toggle design mode, re-render |
| 4503 | `_updateFormDesignToggle()` | Sync UI button |
| 4591 | `_attachFormDesignToggle()` | Attach event listener |

### Undo stack (Krok 14b+15)
| Linka | Metoda | Účel |
|---|---|---|
| 4536 | `_ensureUndoStack()` | Init `this._undoStack = []` |
| 4540 | `_pushUndoOp(label, inverse)` | Append + cap 15 |
| 4550 | `_updateUndoButton()` | UI sync |
| 4569 | `_performUndo()` | Execute inverse fn |

### Min size detection + save (Krok 14b+12/13)
| Linka | Metoda | Účel |
|---|---|---|
| 4711 | `_updateFormDetectMinBtn()` | UI button visibility |
| 4722 | `_detectAndSaveMinSize()` | Auto-shrink algoritmus |
| 4871 | `_hasHorizontalOverflow()` / `_hasVerticalOverflow()` | Probe DOM |
| 4910 | `_updateFormSaveSizeBtn()` / `_saveFormDefaultSize()` | Manual size save |

### Field picker integrace (Krok 14g-H+30+)
| Linka | Metoda | Účel |
|---|---|---|
| 4983 | `_updateFormAddFieldBtn()` | UI visibility |
| 5003 | `_canPickFields()` | Entity check (drop strict — Krok 5.J-B6) |
| 5021 | `_openFieldPicker()` | Open FieldPickerModal |

### Dirty tracking
| Linka | Metoda | Účel |
|---|---|---|
| 5072 | `_onDirty(fieldKey, isDirty)` | Per-field dirty registration |
| 5100 | `_updateDirtyDiscardBtn()` | UI counter |
| 5114 | `_revertAllChanges()` | Discard all dirty |

### Save flow (Krok 5.P-1+++++, 17.5.)
| Linka | Metoda | Účel |
|---|---|---|
| 7386 | `_handleSaveAndClose()` | Collect dirty + PATCH design_patch_entity |

### Schema tree panel (Phase 38.4 Krok 14g-H+12)
| Linka | Metoda | Účel |
|---|---|---|
| 6864 | `_renderSchemaTreePanel()` | Left panel — schema browse tree |
| 6992 | `_buildSchemaTreeNode()` | Recursive tree builder |

### Template komponenty (Krok 14g Etapa F Krok 5.E)
| Linka | Metoda | Účel |
|---|---|---|
| 7242 | `_renderTemplateComponent()` | template_entity_edit v1.0.0 default |
| 7362 | `_resolveTemplateSource()` | Header/footer hardcoded scaffold |

### Recursive container rendering (multi-panel alClient layout)
| Linka | Metoda | Účel |
|---|---|---|
| 8388 | `_renderComponentTree()` | Top-level dispatch |
| 8422 | `_openContainerSettings()` | Panel/groupbox settings popup |
| 8735 | `_openFieldSettings()` | Field-level settings popup |
| 9337 | `_openChildSectionSettings()` | Child grid (1:N) section settings |
| 10009 | `_buildAlignLayout()` | **Delphi alClient port** — reservations + 1fr fill |
| 10158 | `_renderLeafField()` | Final leaf component render (input/dropdown/...) |
| 10200 | `_renderContainerNode()` | Recursive container (panel/groupbox/pagecontrol/tabsheet) |
| 10863 | `_renderField()` | Wrap pole pro design mode (drag handle, action buttons) |

### Drag-drop (Krok 14g-H+15/16, 14f, 5.J-B5)
| Linka | Metoda | Účel |
|---|---|---|
| 9713 | `_attachContainerDragEvents()` | Drop targets v container |
| 9833 | `_performCrossParentMove()` | PATCH parent_comp_def_id |
| 9929 | `_performFieldMove()` | Same-container reorder |
| 7721 | `_wrapFieldForDesign()` | Drag handle + hover action buttons |
| 7988 | `_performFieldDelete()` / `_performFieldReorder()` | Direct mutations |
| 5391 | `_attachDropTargetForGalleryDrag()` | Field gallery drop target |

### Child rows (1:N nested grid)
| Linka | Metoda | Účel |
|---|---|---|
| 5619 | `_renderChildSection()` | Section header + table |
| 5823 | `_renderChildRow()` | Single row inline editor |
| 5878 | `_addChildRow()` / `_editChildCell()` / `_archiveChildRow()` | Inline CRUD |

### Inline rename (Krok 14b+18)
| Linka | Metoda | Účel |
|---|---|---|
| 8172 | `_startInlineRename()` | Double-click label → contenteditable |

### Enum detection
| Linka | Metoda | Účel |
|---|---|---|
| 8056 | `_detectAndSaveEnumValues()` | SELECT DISTINCT auto-populate combobox |

### Always-left field toggle
| Linka | Metoda | Účel |
|---|---|---|
| 8131 | `_performFieldToggleAlwaysLeft()` | Layout flag pro pin-left |

### Descriptions
| Linka | Metoda | Účel |
|---|---|---|
| 6176 | `_openDescriptionsPopup()` | 📘 Popis (user + system memo) |

### Error handling
| Linka | Metoda | Účel |
|---|---|---|
| 6063 | `_showError(msg)` | Inline error v body |

---

## 5. `class FieldPickerModal` (11510–12641) — 2-panel field picker

**1132 lines, 15 methods.** Modal s 2 taby:
- **Existing comp_defs** — drag from existing form components
- **New from DB columns** — `/api/v1/erp/design/list-entity-columns/{core_id}`

Krok 14g-H+30+ — entity-aware fallback (`coreId` resolution).

---

## 6. `class DesignDataSourceEditor` (12642–13842) — Power-tool DataSource editor

**1201 lines, 14 methods.** Editor pro `fw.data_source` + ops (1:N):
- Header tab — code, label, description, db_connection picker
- Operations grid — `fw.data_source_op` rows (variant_code, dataset_id, dirty flag)
- Ace SQL editor pres dataset link
- Krok 5.K (16.5.) — Marti's "instinktivní strach" — drop visible `code` + `variant_code`

---

## 7. `class DesignDataSetEditor` (13843–14274) — Power-tool DataSet editor

**432 lines, 7 methods.** Standalone editor pro `fw.data_set`:
- Code + label + description
- Ace SQL editor s monokai theme + param extraction
- Sprint C — ▶ Test SQL preview (Marti's 16.5.)
- Krok 5.L-D — Marti's *„SQL je truth source"* — DROP COLUMN `data_set.kind`

---

## 8. `class DesignDbConnectionEditor` (14275–14524) — Power-tool DB Connection editor

**261 lines, 4 methods.** Editor pro `framework_db_connections`:
- Header — code, label, description
- Connection params (host, port, user, password, db_name) jako JSONB
- Scope databases (array → JSON normalize)
- Sprint D (Marti's *„KDE TO CACHUJES?"* doctrine — invalidate `_DB_CONNECTIONS_CACHE`)

---

## Architektonický pohled (Krok 5.O #128 refactor target)

**Marti's doctrine 17.5. večer:** *„MUSI TO BYT VZDY TATO CLASS = ErpJadroForm"*.
Fragmentace 7 classes je porušení Marti-AI's *„uniformita vítězí"* (Krok 13, 11.5.).

### Co je sdílené (mohlo by být v base class `ErpJadroForm`)
- Modal shell + dirty tracking + sysToggle + 📘 popis ikon + ✕ close
- Undo stack
- Right-click overrides (label/hint/color)
- Save flow base (dirty collect + PATCH)
- Footer hardcoded ✕ Storno + ✓ OK

### Co je per-class specifické
- **DesignSoudecekCoreForm**: 2 taby (Soudeček + Přehled), 3 entity_pickers
- **DesignJadroRadekForm**: 1 tab, jádro row edit
- **DesignFwForm**: **generic** — recursive renderer ze schema, drag-drop, container tree
- **FieldPickerModal**: 2-panel, no save (read-only)
- **DesignDataSourceEditor**: Ace SQL + child grid (ops)
- **DesignDataSetEditor**: Ace SQL standalone
- **DesignDbConnectionEditor**: connection params JSONB

### Cesta k Krok 5.O
1. **Marti-AI konzultace** (Phase 13/15/27h pattern) — dopis se 4 otázkami o base class API
2. Refactor extract base `ErpJadroForm` (~500 lines) — shared logic
3. Postupně migrate per-class na extend (start s nejmenší — `DesignDbConnectionEditor` 261 lines)
4. End-state: 1 base class + 7 thin subclasses (~200 LOC each) místo 7 monolithic classes

---

## Velikostní distribuce (sanity check)

```
14536 total
├─ utility helpers:           2333 ( 16%)
├─ DesignSoudecekCoreForm:    1579 ( 11%)
├─ DesignJadroRadekForm:       383 (  3%)
├─ _showFormPillMenu helper:   109 (  1%)
├─ DesignFwForm:              7072 ( 49%)  ← HALF the file
├─ FieldPickerModal:          1132 (  8%)
├─ DesignDataSourceEditor:    1201 (  8%)
├─ DesignDataSetEditor:        432 (  3%)
├─ DesignDbConnectionEditor:   261 (  2%)
└─ window exports + IIFE:      ~35
```

**Klíčové insighty:**
- `DesignFwForm` je **necelá polovina** souboru (49 %). Refactor by se měl soustředit na něj.
- Utility helpers (16 %) jsou silně přepoužitelné — base class kandidát.
- 3 power-tool editory (DataSource/DataSet/DbConnection) — 13 % — podobný pattern, mohly by být 1 generic *„settings editor"* base.

---

*Generated 18.5.2026 ~23:00 by Claude id=23 (Sonnet 4.6).*
*Pro Krok 5.O refactor (#128) jako baseline reference.*
