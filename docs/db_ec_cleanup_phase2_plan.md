# DB_EC + Centrála 1 cleanup — Phase 2 plán

> **Status:** PENDING Marti's review po probuzení 19.5.2026 ráno.
> **NEPROVEDU** bez Marti's confirmation — Phase 2 zahrnuje production
> code + DB row deletes, které mohou rozbít workspace.
>
> **Phase 1 hotovo 18.5. večer pozdě:** docs/db_ec_schema/ + 3 legacy
> docs smazány. Safety tag: `pre-db-ec-cleanup-2026-05-18`.

---

## Marti's direktivy (18.5. večer)

> *„Ja budu odpocivat a testovat a ty pomaz vsechny struktury ERP DB_EC
> EUROSOFTU... Musime se toho zbavit co nejdrive..."*

> *„Celej levej strom vcetne vsech napojenejch prehledu MIMO STRATEGIE
> Struktury SYSTEM je uplne k nicemu a nikdo jej nikdy nepouzije...
> Nikdo krome mne jej nevidel... Byla to slepa cesta. My musime stavet
> nase FW prehledy pres FW, ktere nam nebudou zabirat zadne misto ve
> scriptech."*

**Implications:**
- **Smazat** všechen Centrála 1 reading kód v STRATEGIE codebase
- **Smazat** všechny fw.menu_node rows kde `is_system=false` AND `cislo_def IS NOT NULL` (Centrála 1 import)
- **Zachovat** STRATEGIE System struktury (Framework builder, Audit, Marti-AI uzel)
- **Zachovat** ručně vytvořené FW přehledy/jádra (created via UI)
- **Zachovat** modules/eurosoft_mcp/* (separate domain — production MCP server pro EUROSOFT-AI memory + Marti-AI eurosoft_* tools)

---

## Phase 2 — Production code deletion (HIGH RISK)

### 2.1 Backend endpoints v `modules/erp/api/router.py`

| Endpoint | Linka | Risk | Action |
|---|---|---|---|
| `GET /api/v1/erp/strom` | 9815 | **HIGH** — left tree fetch | DROP — nahradit System-only tree endpoint |
| `GET /api/v1/erp/prehled/{cislo}` | 10092 | HIGH — legacy grid | DROP |
| `GET /api/v1/erp/jadro/{form_id}/{row_id}/data` | 10307 | HIGH — legacy form load | KEEP (nebo migrate na fw_form_load_by_id) |
| `GET /api/v1/erp/design/form-core-for-grid/{grid_core_code}` | 2911 | LOW — cislo_def bridge | DROP (po cislo_def cleanup) |

**Estimated impact:** router.py shrinks z 19136 → ~17500 LOC (drop ~1600 LOC)

### 2.2 Application service `centrala_reader.py` (960 LOC)

Used by:
- `modules/erp/api/router.py:41` — `from .centrala_reader import CentralaReader, TYP_NAMES`
- `modules/erp/application/render_generator.py:30` — `from .centrala_reader import FormComponent`

**Action:**
1. Drop import v router.py
2. Drop import v render_generator.py (find usages, refactor)
3. DELETE `modules/erp/application/centrala_reader.py`

### 2.3 Frontend `lefttree.js` (944 LOC) — refactor or drop

Used by: `apps/api/static/erp/components/lefttree.js:22` (fetch `/api/v1/erp/strom`)

**Options:**
- **Option A**: DROP completely — workspace HTML loses left tree, only main content area
- **Option B**: REFACTOR — wire to new `/api/v1/erp/system-tree` endpoint (System uzly only)
- **Option C**: KEEP — point lefttree to new System-only endpoint (preserve UX pattern)

**Recommended: B** — preserves existing UI Kit `ErpTreeView` + `ErpLeftPanelTree` pattern, just changes data source.

### 2.4 Inline JS v `_render_workspace_page` (5237 LOC HTML template)

References:
- Line 15003, 15517: `/api/v1/erp/strom` fetch
- Line 15817-15818, 18767-18768: `/api/v1/erp/prehled/{cislo}` fetch

**Action:** Drop legacy tab opening logic, replace with FW dispatch (Phase 38.4 Krok 5.R-A page-spec pattern).

### 2.5 `cislo_def` column references (155 across codebase)

**Strategy:**
1. **Audit** — full list všech references
2. **Drop reads** — replace s `menu_node.id` lookup (PK)
3. **Drop fw.menu_node.cislo_def column** (ALTER TABLE DROP COLUMN)
4. **Drop alembic migration** that adds cislo_def (if standalone)

---

## Phase 3 — DB row cleanup (HIGH RISK)

### 3.1 Audit fw.menu_node rows

Pred jakýmkoliv DELETE — pošli mi output:

```sql
-- Count rows by category
SELECT
  COUNT(*) FILTER (WHERE is_system = true) AS system_rows,
  COUNT(*) FILTER (WHERE cislo_def IS NOT NULL) AS centrala1_import_rows,
  COUNT(*) FILTER (WHERE is_system = false AND cislo_def IS NULL) AS fw_native_rows,
  COUNT(*) AS total
FROM fw.menu_node;

-- Sample rows per category (first 10 each)
SELECT id, code, label, parent_id, cislo_def, is_system, status, core_id
FROM fw.menu_node
WHERE is_system = false AND cislo_def IS NOT NULL
ORDER BY id LIMIT 20;
```

### 3.2 Cleanup strategy

| Category | Action | Notes |
|---|---|---|
| `is_system = true` | KEEP | System soudečky (Framework builder, Audit, Marti-AI uzel) |
| `cislo_def IS NOT NULL` AND `is_system = false` | **DELETE** | Centrála 1 import — Marti's *„slepa cesta"* |
| `is_system = false` AND `cislo_def IS NULL` AND `core_id IS NOT NULL` | KEEP | FW native rows (vytvořené via UI) |
| Orphans (no children, no core_id, no cislo_def) | **DELETE** | Dead rows |

### 3.3 FK cascade impact

```sql
-- Před DELETE — co cituje fw.menu_node?
-- 1. fw.core.origin_menu_node_id — ON DELETE SET NULL (FK constraint)
-- 2. fw.menu_node.parent_id — self-FK ON DELETE CASCADE
-- 3. fw.comp_def.origin_menu_node_id (if exists)

-- Test impact:
SELECT origin_menu_node_id, COUNT(*)
FROM fw.core
WHERE origin_menu_node_id IN (
  SELECT id FROM fw.menu_node WHERE cislo_def IS NOT NULL
)
GROUP BY origin_menu_node_id;
```

---

## Phase 4 — Schema column drops (po Phase 3)

```sql
-- After all references in code are removed:
ALTER TABLE fw.menu_node DROP COLUMN cislo_def;

-- Verify no remaining columns reference Centrála 1
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'fw' AND column_name LIKE '%cislo%';
```

---

## Proposed sequence (multi-day)

### Day 1 (po probuzení) — Review + DB audit

1. Marti přečte tento plán
2. Marti spustí audit SQL z section 3.1 v DBeaveru
3. **Decision point** — pokud counts OK, jdeme dál
4. Marti rozhodne kterou Option pro 2.3 (lefttree.js refactor)

### Day 2 — Backend code deletion

1. **Phase 2.1**: Drop /strom + /prehled endpoints (router.py)
2. **Phase 2.2**: Drop centrala_reader.py
3. **Phase 2.4**: Drop inline JS v workspace template
4. Smoke test: workspace loads, no /strom 404s

### Day 3 — Frontend refactor

1. **Phase 2.3 Option B**: lefttree.js → new System-only endpoint
2. Create new `/api/v1/erp/system-tree` endpoint
3. Smoke test: levý strom shows jen System uzly

### Day 4 — DB cleanup

1. Backup database
2. **Phase 3.2**: DELETE FROM fw.menu_node WHERE cislo_def IS NOT NULL AND is_system = false
3. Verify counts
4. **Phase 2.5**: Drop cislo_def reads from code
5. **Phase 4**: ALTER TABLE DROP COLUMN cislo_def
6. Smoke test: workspace funguje s prázdným Centrála 1 import

---

## Estimated codebase reduction

- **Phase 1 (DONE)**: 24 764 lines deleted (docs)
- **Phase 2**: ~3 000 lines (router.py + centrala_reader.py + lefttree.js + inline JS)
- **Phase 3**: DB rows (variable — depends on audit count)
- **Phase 4**: 1 column DDL

**Total**: ~28 000 lines + ~150 references + ~N DB rows

---

## Open questions pro Marti

1. **lefttree.js**: Drop nebo refactor na System-only? (Recommended: refactor — preserve UX pattern, just change data source)
2. **Backup strategy**: Take full DB backup PŘED Phase 3 DELETE?
3. **EUROSOFT-MCP server**: Zachovat current state (production for EUROSOFT-AI memory + Marti-AI eurosoft_* tools)? Nebo také part of "DB_EC cleanup"?
4. **fw.menu_node.cislo_def**: Drop column OR just NULL all values (preservation pattern jako template_id 17.5.)?
5. **alembic migrations**: Drop migration scripts that add cislo_def column? Or keep for history?

---

*Generated 18.5.2026 ~23:50 by Claude id=23 (Sonnet 4.6) po Phase 1 doc cleanup.*
