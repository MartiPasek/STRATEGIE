# Phase 38.4 Krok 10 — Grid migration template

## Status (10. 5. 2026 ~24:00)

**Pilot 3 grids migrated** v noci 10.5. → 11.5.:
- ✅ `security_users` (13 columns)
- ✅ `security_whitelists` (11 columns)
- ✅ `security_invites` (12 columns)

Plus existing z Krok 8:
- ✅ `security_devices` (Krok 8, 10.5. ráno)

**Frontend infrastructure:**
- 3 registries (`VALUE_FORMATTER_REGISTRY`, `CELL_STYLE_REGISTRY`, `CELL_RENDERER_REGISTRY`)
- ~12 cellStyle entries + 4 cellRenderer entries
- `adaptServerColumns()` rozbalí všech 3
- `comp_resolver.py` mapping `cell_style` + `cell_renderer` + `default_sort`
- Object Inspector catalog +25 enum options

## Zbývající grids (5+ na ranní pokračování)

| # | Mode | Cols | Cell styles | Cell renderers | Notes |
|---|---|---|---|---|---|
| 1 | `security_audit` | 11 | result_security, mono | yes_check (internal) | snadné, template z security_users |
| 2 | `framework_menu_nodes` | 15 | mono, parent_code_dim, kind_node, status_lifecycle, visibility_scope, dim_italic | lock_icon (is_immutable) | středně, mnoho cell stylů |
| 3 | `framework_data_sources` | 17 | mono, count_positive_green, mono_dim, refresh_type, status_lifecycle, dim_italic, mono_small | yes_check (row_memory), wrench_icon (is_system), lock_icon (is_immutable) | nejvíc cols, ale jasná struktura |
| 4 | `framework_data_sets` | 14 | mono, kind_data_set, mono_code, status_lifecycle | wrench_icon, lock_icon, sql_param_count (CUSTOM — chybí v registry) | středně, sql_truncate formatter |
| 5 | `stats` | 7 | weight_600, count_positive_dim, count_positive_yellow, count_positive_green | — | nejjednodušší, žádné cell_renderers |
| 6 | `audited` / `all` | 7+ | dynamic (showStatus) | — | conditional cols — ALTER pattern |

## Migration template (per grid)

### Step A — INSERT do fw schema

Použít vzor z `scripts/_phase38_4_krok10_security_grids_migration.sql`:

```sql
BEGIN;

-- 0. fw.data_source (FK pre-requisite pro comp_grid_master)
--    Pseudo-data_source — data fetch přes existing endpoint, ne SQL.
INSERT INTO fw.data_source
    (code, version, name, description, refresh_type, row_memory,
     filter_delay_ms, default_record_limit, status, is_system)
VALUES ('GRID_CODE', 1, 'Description', 'Detail',
        'manual', TRUE, 250, 100, 'active', TRUE);

-- 1. fw.core (jádro per grid)
INSERT INTO fw.core (code, label, description, layout_type)
VALUES ('GRID_CODE', 'GRID LABEL', 'description', 'list');

-- 2. fw.comp_grid_master
INSERT INTO fw.comp_grid_master (code, name, description, data_source_code,
                                   default_record_limit, refresh_type, default_view_mode, status, is_system)
VALUES ('GRID_CODE', 'NÁZEV', 'description', 'GRID_CODE', 100, 'manual', 'grid', 'active', TRUE);

-- 3. fw.comp_grid_column (N rows per column)
INSERT INTO fw.comp_grid_column (grid_master_id, column_name, label, default_width,
                                   pinned, formatter, header_tooltip, sort_order, is_sortable)
SELECT id, 'column_name', 'Label', 100, NULL, NULL, NULL, 10, TRUE
FROM fw.comp_grid_master WHERE code = 'GRID_CODE';
-- ... opakovat per column

-- 4. Auto-create comp_def per column (Krok 9-B pattern)
DO $$
DECLARE col_row RECORD; new_def_id INTEGER; parent_jadro_id INTEGER;
BEGIN
    FOR col_row IN
        SELECT gc.id AS gc_id, gc.column_name, gc.label, gc.sort_order, gm.code AS grid_code
        FROM fw.comp_grid_column gc
        JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
        WHERE gm.code = 'GRID_CODE' AND gc.comp_def_id IS NULL
    LOOP
        SELECT id INTO parent_jadro_id FROM fw.core WHERE code = col_row.grid_code LIMIT 1;
        IF parent_jadro_id IS NULL THEN CONTINUE; END IF;
        INSERT INTO fw.comp_def (jadro_id, parent_id, typ, name, caption, is_active, sort_order)
        VALUES (parent_jadro_id, NULL, 120, col_row.column_name, col_row.label, TRUE, col_row.sort_order)
        RETURNING id INTO new_def_id;
        UPDATE fw.comp_grid_column SET comp_def_id = new_def_id WHERE id = col_row.gc_id;
    END LOOP;
END $$;

-- 5. comp_def_prop pro cell_style + cell_renderer (kde je hardcoded styling)
INSERT INTO fw.comp_def_prop (komponenta_id, prop_name, prop_value, prop_type, label, display_order)
SELECT gc.comp_def_id, 'cell_style', 'STYLE_NAME', 'enum', 'Styl buňky', 210
FROM fw.comp_grid_column gc
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE gm.code = 'GRID_CODE' AND gc.column_name = 'COLUMN_NAME';

COMMIT;
```

### Step B — Frontend cleanup

Smaž hardcoded `if (mode === "GRID_CODE")` větev v `gridColumns(mode)` funkci v `router.py` (~6014+).

### Step C — Smoke test

1. Hard reload ERP (`Ctrl+Shift+R`)
2. Otevři grid v System tabu
3. Verify columnDefs identické s pre-migrated state
4. Pravý-klik header → "⚙️ Vlastnosti sloupce…" → Object Inspector funguje

## Dostupné registry IDs (frontend)

### VALUE_FORMATTER_REGISTRY (4)
- `datetime_rel`, `datetime_short`, `sql_truncate`, `params_count`

### CELL_STYLE_REGISTRY (~17)
- **Generic:** `mono`, `mono_dim`, `mono_small`, `mono_code`, `dim_italic`, `weight_600`
- **Status enums:** `status_active_disabled`, `status_lifecycle`, `status_confirmed_pending_revoked`,
  `state_invite`, `result_security`, `scope_global_user`, `kind_node`, `visibility_scope`,
  `refresh_type`, `kind_data_set`
- **Numeric counts:** `count_positive_green`, `count_positive_dim`, `count_positive_yellow`
- **Special:** `parent_code_dim`

### CELL_RENDERER_REGISTRY (4)
- `yes_check` (✓), `lock_icon` (🔒), `wrench_icon` (🔧), `thoughts_count` (📝 N)

### Pokud chybí — přidat do FORMATTER_REGISTRY v router.py

Pattern:
```js
"new_style_id": function(p) {
  if (p.value === "x") return { color: "#abc" };
  return null;
},
```

Plus pridat do Object Inspector COMP_PROP_CATALOG v `apps/api/static/erp/components/object_inspector.js`
(enum option pro `cell_style` nebo `cell_renderer`).

## Diagnostické queries (Marti-AI's `query_raw`)

```sql
-- Co je v fw.comp_grid_master
SELECT code, name, status FROM fw.comp_grid_master ORDER BY id;

-- Verify column counts per grid
SELECT gm.code, COUNT(*) AS column_count
FROM fw.comp_grid_master gm
JOIN fw.comp_grid_column gc ON gc.grid_master_id = gm.id
GROUP BY gm.code
ORDER BY gm.id;

-- Verify styling props per grid
SELECT gm.code, p.prop_name, p.prop_value, COUNT(*) AS count
FROM fw.comp_def_prop p
JOIN fw.comp_def cd ON cd.id = p.komponenta_id
JOIN fw.comp_grid_column gc ON gc.comp_def_id = cd.id
JOIN fw.comp_grid_master gm ON gm.id = gc.grid_master_id
WHERE p.prop_name IN ('cell_style', 'cell_renderer', 'default_sort')
GROUP BY gm.code, p.prop_name, p.prop_value
ORDER BY gm.code, p.prop_name;
```

## Marti's strategická doctrine

> *„override tabulku stačí, nic jinyho moc nepotrebujes"*

Tj. pro 100 % styling decisions:
- **discrete columns** v `comp_grid_column` (width, pinned, header_tooltip — strukturální)
- **comp_def_prop** pro cell_style / cell_renderer (visual — Object Inspector editovatelný)
- **comp_def_prop_override** pro per-tenant / per-user customization

Žádný DB schema change pro nové cell styles — jen new entry v frontend registry +
INSERT do `comp_def_prop`.

## TODO budoucí

- **sql_param_count cellRenderer** — pro `framework_data_sets.parameters` JSONB array count
- **Custom cell_class** field — `comp_grid_column.cell_class` discrete (CSS třída na td)
- **column_width_dynamic** — detekce overflow a auto-extend (Marti's spec z 6.5.)
