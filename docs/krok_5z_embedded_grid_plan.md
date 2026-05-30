# Krok 5.Z — Embedded Grid Pattern (comp_type=306 grid_modern uvnitř form)

**Datum vzniku:** 30.5.2026 ráno
**Autor:** Claude (Sonnet 4.6, předávací poznámka)
**Status:** Ready for implementation (Etapa A+B+C)
**Marti's mandate:** *„Klasickou komponentu gridu 306 pro nase vseobecne pouziti... Obdobnym zpusobem, jako to mas v komponente entity pickup"*

## Kontext (jak jsme sem došli)

**30.5.2026 ráno:**
- **Etapa 1 LIVE** — jádro „Komponenty" (`framework_comp_def_overview` core_id=73, menu_node=67 pod Framework=42, 13 grid columns) → `scripts/_phase_jadro_komponenty_build.sql`
- **Gotcha #112** zachycena: `visibility_scope='tenant_member'` nemá frontend filter → use `parent_only` nebo NULL
- **Gotcha #111** zachycena: DBeaver bind dialog false-positive na `:param` v `$$...$$` dollar-quoted strings → vždy Cancel/Ignore
- **Marti's klíčová doctrine (rozhodnutí 29.5. večer + potvrzeno 30.5.):**
  > *„Tu komponentu 304 jsme se vcera spolu rozhodli nepouzivat. Kvuli blbemu renderovani. Potrebujeme tedy pouzit klasickou komponentu gridu 306 pro nase vseobecne pouziti."*

**Root cause comp_type=304 (nested_grid) odmítnutí:**
`_renderChildSection` v `design_forms.js:1687-1838` renderuje **HTML `<table>`** místo ErpDataGrid → chybí AG Grid features (filter/sort/copy/layout persistence/Excel mode).

**Pivot:** `comp_type=306 (grid_modern)` embedded inline v form, render pattern **analog ErpEntityPicker** (line 8702-9050).

## Cíl LIVE smoke

Otevři Core setting (core 49) → Tab Vazby → vidět **13 komponent core 49** v embedded ErpDataGrid (autoColumns, layoutKey persistent, Excel mode CRUD inheritance).

## Schema decisions (Marti potvrzeno)

**Layout JSONB pro embedded grid_modern (Volba A — striktní deklarace):**

```json
{
  "data_source_code": "framework_comp_def_overview",
  "filter_field": "core_id",
  "filter_source": ":master_id",
  "height_px": 360,
  "title": "Komponenty",
  "context_menu": ["create", "edit", "delete", "refresh"]
}
```

**Filter substitution v frontend:**
- `":master_id"` → `this._spec.form.id` (PK current core row, např. 49 pro Core setting form)
- Future: `":form_root_data_source_id"`, `":runtime_<x>"` další tokeny dle potřeby

## 3 fáze implementace

### Fáze A — Backend (router.py)

**Soubor:** `D:\Projekty\STRATEGIE\modules\erp\api\router.py`
**Endpoint:** `fw_form_load_by_id` (line 2694, function start)
**Existing pattern reference:**
- Line 2754-2769: `root_row` SELECT s LEFT JOIN data_source
- Line 2780: response shape s `children: {}` dict
- Krok 5.X+1 Fix E (#552): *„Backend pass-through layout JSONB do children_dict"*

**Změna:** Po fetch `root_row`, přidat SELECT pro **embedded grids** (children comp_defs s `type_id=306` AND `parent_comp_def_id IS NOT NULL`):

```python
embedded_grids_rows = ds.execute(_sql_fwid("""
    SELECT cd.id AS comp_def_id, cd.parent_comp_def_id, cd.name, cd.caption,
           cd.layout, cd.sort_order, cd.data_source_id,
           ds.code AS data_source_code, ds.name AS data_source_name
    FROM fw.comp_def cd
    JOIN fw.comp_type ct ON ct.id = cd.type_id
    LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
    WHERE cd.core_id = :cid
      AND ct.code = 'grid_modern'
      AND cd.parent_comp_def_id IS NOT NULL
      AND cd.is_active = true
    ORDER BY cd.sort_order ASC, cd.id ASC
"""), {"cid": core_id}).mappings().all()

embedded_grids = [dict(r) for r in embedded_grids_rows]
```

**Response shape update** (line ~2780):
```python
return JSONResponse(jsonable_encoder({
    "ok": True,
    "core": rd,
    "form": ...,
    "fields": ...,
    "data": ...,
    "template": ...,
    "children": {},  # existing (304 nested_grid back-compat)
    "embedded_grids": embedded_grids,  # NEW
    "empty_container": False,
    "origin": origin_payload,
}))
```

**Apply script template** (atomic, gotcha #14 prevention):
```python
# scripts/_apply_krok5z_a_backend_embedded_grids.py
NEEDLE_SELECT = """root_row = ds.execute(_sql_fwid(\"\"\"
            SELECT cd.id, cd.name, cd.caption, cd.type_id, cd.layout,"""  # match unique
NEEDLE_RESPONSE = """\"children\": {},"""  # match unique v response dict

# Insert: po root_row processing přidat embedded_grids_rows SELECT
# Response: insert "embedded_grids" klíč
# Verify: ast.parse na výsledný soubor PŘED replace
```

### Fáze B — Frontend (design_forms.js)

**Soubor:** `D:\Projekty\STRATEGIE\apps\api\static\erp\components\design_forms.js`
**Insertion point:** Po `case "entity_picker":` block (line 8702-9050) → přidat `case "grid_modern":` branch

**OR alternativně:** rozšířit container children rendering (line 8186-8238) — kde se separují `_nestedGridChildren` od `_regularChildren`. Přidat **3. kategorie** `_embeddedGridChildren` (`comp_type_code === "grid_modern" AND parent_comp_def_id IS NOT NULL`).

**Recommended — varianta B (rozšíření existing logic):**

```javascript
// Line ~8185-8194 změna:
const _DELPHI_ALIGNS = new Set(["left", "right", "top", "bottom"]);
const _regularChildren = [];
const _nestedGridChildren = [];     // existing 304 back-compat
const _embeddedGridChildren = [];   // NEW — 306 grid_modern embedded
for (const childComp of children) {
  if (childComp && childComp.comp_type_code === "nested_grid") {
    _nestedGridChildren.push(childComp);
  } else if (
    childComp &&
    childComp.comp_type_code === "grid_modern" &&
    childComp.parent_comp_def_id !== null
  ) {
    _embeddedGridChildren.push(childComp);
  } else {
    _regularChildren.push(childComp);
  }
}

// ... existing _regularChildren render ...
// ... existing _nestedGridChildren render (line 8224-8238) ...

// NEW: Embedded grid render — analog _nestedGridChildren ale s ErpDataGrid
for (const childComp of _embeddedGridChildren) {
  const sec = this._renderEmbeddedGridSection(childComp);
  if (sec) wrap.appendChild(sec);
}
```

**Nová metoda `_renderEmbeddedGridSection`** (vedle `_renderChildSection` line 1687):

```javascript
_renderEmbeddedGridSection(childComp) {
  const layout = childComp.layout || {};
  const dataSourceCode = layout.data_source_code;
  if (!dataSourceCode) {
    console.warn("[DesignFwForm] embedded_grid missing data_source_code:", childComp);
    return null;
  }

  // Embedded grid lookup z spec.embedded_grids by comp_def_id
  const eg = (this._spec.embedded_grids || []).find(
    e => e.comp_def_id === childComp.id
  );
  if (!eg) {
    console.warn("[DesignFwForm] embedded_grid comp_def #" + childComp.id + " not in spec.embedded_grids");
    return null;
  }

  const title = layout.title || childComp.caption || eg.data_source_name || dataSourceCode;
  const filterField = layout.filter_field;
  const filterSource = layout.filter_source;
  const heightPx = layout.height_px || 360;
  const contextMenu = layout.context_menu || ["refresh"];

  // Filter substitution
  let filterValue = null;
  if (filterSource === ":master_id" && this._spec.form) {
    filterValue = this._spec.form.id;
  }
  // Future: další tokeny

  // Section wrap (reuse _sectionBuild helper z _renderChildSection line 1689)
  const sec = _sectionBuild(title, "embedded:" + childComp.id);

  // Host div pro ErpDataGrid
  const host = document.createElement("div");
  host.style.cssText = "width:100%;height:" + heightPx + "px;";
  sec.grid.appendChild(host);

  // Data fetch URL s filter substitution
  let dataUrl = "/api/v1/erp/data/" + encodeURIComponent(dataSourceCode);
  if (filterField && filterValue !== null) {
    dataUrl += "?" + encodeURIComponent(filterField) + "=" + encodeURIComponent(filterValue);
  }

  // Embedded ErpDataGrid (reuse pattern z page_render.js root grid render)
  // Async fetch + new ErpDataGrid({ container: host, autoColumns: true, ... })
  // layoutKey: "embedded_" + this._spec.core.id + "_" + childComp.id
  // coreInfo: { coreId: this._spec.core.id, refId: this._spec.form.id, coreLabel: title }
  // disableColumnFlex: true (parita master-detail Volba A z 24.5.)
  // contextMenuActions: contextMenu (reuse Universal CRUD Etapa B)

  (async () => {
    try {
      const resp = await fetch(dataUrl, { credentials: "same-origin" });
      const json = await resp.json();
      const rows = (json && json.rows) || [];
      new ErpDataGrid({
        container: host,
        rows: rows,
        autoColumns: true,
        layoutKey: "embedded_" + this._spec.core.id + "_" + childComp.id,
        coreInfo: {
          coreId: this._spec.core.id,
          refId: this._spec.form.id,
          coreLabel: title,
        },
        disableColumnFlex: true,
        contextMenuActions: contextMenu,
        onRefresh: () => { /* re-fetch dataUrl, update grid */ },
      });
    } catch (e) {
      console.error("[embedded_grid] fetch failed:", e);
      host.innerHTML = "<div style='padding:14px;color:#e57373;'>Chyba načtení dat: " + e.message + "</div>";
    }
  })();

  return sec.wrap;
}
```

**Apply script template:**
```python
# scripts/_apply_krok5z_b_frontend_embedded_grid.py
# - NEEDLE_SEPARATION (line ~8185-8194): rozšířit o _embeddedGridChildren
# - NEEDLE_RENDER (line ~8224-8238): přidat for-loop pro _embeddedGridChildren
# - NEEDLE_METHOD: insert _renderEmbeddedGridSection method (po _renderChildSection)
# - Verify: node --check výsledný soubor PŘED replace
```

### Fáze C — SQL Core setting 49

**Soubor:** `scripts/_phase_krok5z_c_core49_embedded_komponenty.sql`

**Předpoklad:** Core setting form 49 má strukturu z `_phase_core49_self_edit_build.sql`:
- root form #154 (type 302)
- main_pagecontrol (type 15, child of #154)
- tab_vazby (type 16, child of main_pagecontrol) ← target
- ... další tabs (zakladni/audit/pokrocile/raw)

**INSERT skript:**
```sql
BEGIN;
DO $$
DECLARE
  v_grid_modern_type INT;
  v_tab_vazby_id INT;
  v_embedded_id INT;
BEGIN
  -- Lookups
  SELECT id INTO v_grid_modern_type FROM fw.comp_type WHERE code = 'grid_modern' LIMIT 1;

  -- Najdi tab_vazby pod main_pagecontrol pod root #154 v core 49
  SELECT cd.id INTO v_tab_vazby_id
  FROM fw.comp_def cd
  WHERE cd.core_id = 49 AND cd.name = 'tab_vazby'
  LIMIT 1;

  IF v_tab_vazby_id IS NULL THEN
    RAISE EXCEPTION 'tab_vazby nenalezena pod core 49. Spustil jsi _phase_core49_self_edit_build.sql?';
  END IF;

  -- INSERT embedded grid_modern komponenta
  INSERT INTO fw.comp_def (
    core_id, parent_comp_def_id, type_id, name, caption,
    layout, sort_order, is_active,
    created_by_text, updated_by_text
  ) VALUES (
    49, v_tab_vazby_id, v_grid_modern_type, 'embedded_komponenty', 'Komponenty',
    jsonb_build_object(
      'data_source_code', 'framework_comp_def_overview',
      'filter_field', 'core_id',
      'filter_source', ':master_id',
      'height_px', 400,
      'title', 'Komponenty (filtered per core_id)',
      'context_menu', jsonb_build_array('create', 'edit', 'delete', 'refresh')
    ),
    10, true,
    'Claude', 'Claude'
  ) RETURNING id INTO v_embedded_id;

  RAISE NOTICE 'Embedded grid_modern id=% pod tab_vazby #%', v_embedded_id, v_tab_vazby_id;
END $$;
COMMIT;
```

## Smoke test sekvence

1. **Deploy Etapa A** (backend) → restart STRATEGIE-API → smoke `GET /api/v1/erp/fw-form/by-id/49/49` → ověřit `embedded_grids` v response (zatím prázdný array)
2. **Deploy Etapa C** (SQL) v DBeaveru → ověřit INSERT (RAISE NOTICE)
3. **Re-test backend** → `embedded_grids` má 1 položku s `data_source_code='framework_comp_def_overview'`
4. **Deploy Etapa B** (frontend) → push + cloud pull → hard reload Ctrl+Shift+R
5. **Smoke**: Otevři Core setting (Editace: Země → Core setting) → záložka Vazby → embedded ErpDataGrid s 13 komponenty core 49

## Reference patterns

| Pattern | Soubor | Location |
|---|---|---|
| entity_picker case (render branch reference) | `design_forms.js` | line 8702-9050 |
| _renderChildSection (current nested_grid HTML table) | `design_forms.js` | line 1687-1838 |
| Page-spec endpoint (Fáze A backend SELECT pattern) | `router.py` | line 2590-2691 |
| fw_form_load_by_id (Fáze A insertion point) | `router.py` | line 2694-2820+ |
| Master-detail Volba A nested ErpDataGrid pattern | `data_source_op_detail.js` | full file |
| page_render.js root grid render (autoColumns + layoutKey + coreInfo) | `page_render.js` | grep `new ErpDataGrid` |

## Gotcha prevention

- **Gotcha #14** (Edit truncation): apply scripts s ast.parse (router.py) + node --check (design_forms.js) PŘED Edit replace
- **Gotcha #111** (DBeaver bind dialog): pokud SQL skript obsahuje `:param` v `$$...$$`, vždy Cancel/Ignore na bind prompt
- **Gotcha #112** (visibility_scope): nový menu_node = `parent_only` nebo NULL, ne `tenant_member`
- **Gotcha #110** (em-dash + Czech smart quotes): apply scripty v ASCII-safe, žádný `→ — ✓` v Python print() — use `->`, `-`, `OK`

## Marti's mandate quote (pro budoucího Claude — drž tu doctrinu)

> *„Klasickou komponentu gridu 306 pro nase vseobecne pouziti... Obdobnym zpusobem, jako to mas v komponente entity pickup... Soustredeni se na pouziti tohoto gridu ve formulari Core setting 49 pro zobrazeni komponent core"*

**Cíl LIVE smoke:** Editace: Země → Core setting → záložka Vazby → embedded ErpDataGrid se 13 komponenty core 49.

Po LIVE smoke pokračovat retrofittem do CRM Kontakt setting (Krok 5-B #582) — stejný pattern, 2× embedded grid (Kontaktní údaje + Akce).

---

**Předávací poznámka end. Budoucí Claude — startuj atomic apply scriptem pro Fázi A.** Krabička drží. Trojice (Marti / Marti-AI / Claude) pokračuje.
