# Marti-AI's odpověď na Krok 13 — Iter 2 (Q11-Q15 + DDL částečně)

**Datum:** 11. 5. 2026 (večer)
**Source:** Marti's chat session, předaný Marti & Claude
**Status:** Odpověď přijala doctrine *„uniformita vítězí nad speciálními případy"* + dodala 5 odpovědí Q11-Q15 + 6 DDL tabulek (last partial — `action_audit_log` cut-off)

---

## Q11-Q15 odpovědi (summary)

### Q11 — Container templates

**Generic `comp_type='container'` + FK na `fw.container_template`** (NE multiplication v comp_type enumu).

> *„comp_type je dispatch katalog — říká jak se komponenta renderuje a
> co umí. Container typy se ale liší jen konfigurací (allowed children,
> slots, layout), ne fundamentálním dispatch chováním."*

Plus:
- `allowed_child_types` JSONB na template (NE DB CHECK)
- Required child slots → API validace, ne DB constraint (Q8 pattern)

### Q4 doplnění — `layout_mode ENUM`

`comp_def.layout_mode ENUM('flow','absolute','grid')`, validní jen pro
rows kde `type='container'`. Ostatní NULL (dokumentováno v
`comp_type_property_catalog`).

### Q12 — Container template versioning

`version INT` + `fw.container_template_history`. **Silnější důvod** než
hw_registry — když template změní (přidá allowed_child_type), existující
instance mohou mít nekompatibilní děti. `comp_def.container_template_version`
řídí migration.

### Q13 — refresh_strategy lokace

**Hybrid**: `container_template.default_refresh_strategy` + `comp_def.
refresh_strategy nullable` (NULL → vezme z template, vyplněno → override).

### Q14 — refresh_strategy enum

- `manual` ✓
- `interval:N` ✓ — **min 1000ms** (NE 500ms; *„50 userů × 2 req/s =
  100 req/s jen refresh"*)
- `event:X` ✓ — `X` z **katalogu povolených event typů** (NE volný string)
- `static` ✓
- `realtime` ✓ — **reserved Phase X** (WebSocket/SSE samostatná
  infrastruktura, ne MVP)
- Validace minima v **API vrstvě** (DB CHECK neumí parsovat
  `interval:2000`)

### Q15 — Core layout

**Explicit `core.layout_template`** (NE flat sort_order — magická pravidla
v kódu místo v datech). MVP `'single'` pro všechna existující jádra,
přidávat templates postupně.

---

## DDL — částečně doručené (6 tabulek, last partial)

### 1. `fw.comp_type` — rozšíření + seed (HOTOVO)

```sql
ALTER TABLE fw.comp_type
  ADD COLUMN IF NOT EXISTS kind VARCHAR(30) NOT NULL DEFAULT 'leaf'
    CHECK (kind IN ('leaf', 'container', 'hw', 'action'));

INSERT INTO fw.comp_type (code, label, kind, description) VALUES
  ('container',        'Container (generic)',        'container', 'Generic layout container — instances odkazují na container_template'),
  ('comp_hw',          'Hardcoded / Native',          'hw',        'Hardcoded komponenta — data nebo akce přes hw_registry'),
  ('grid',             'Data Grid',                   'leaf',      'Tabulkový přehled dat přes A3 data_source nebo comp_hw'),
  ('form',             'Form',                        'leaf',      'Editační formulář'),
  ('input',            'Input field',                 'leaf',      'Vstupní pole'),
  ('date',             'Date picker',                 'leaf',      'Výběr data'),
  ('droplist',         'Dropdown list',               'leaf',      'Výběrový seznam'),
  ('iframe',           'iFrame',                      'leaf',      'Embedded URL obsah'),
  ('panel',            'Panel',                       'leaf',      'Obecný vizuální panel')
ON CONFLICT (code) DO UPDATE
  SET kind = EXCLUDED.kind,
      description = EXCLUDED.description;
```

### 2. `fw.container_template` + seed 8 templates (HOTOVO)

Schema: `id, code, label, description, layout_mode, default_refresh_strategy, allowed_child_types JSONB, required_slots JSONB, region_slots JSONB, version, is_active, created_at, updated_at`.

Seed templates:
- `single` (1 main)
- `two_column` (left + right)
- `header_main_footer`
- `dashboard_4` (2×2, default `interval:30000`)
- `master_detail`
- `tabs` (2-10 children)
- `split` (tree + pane)
- `iframe_full` (static)

### 3. `fw.container_template_history` + trigger (HOTOVO)

History table + `trg_container_template_history` trigger before UPDATE,
inserts snapshot + auto-increments version.

### 4. `fw.hw_registry` — unified data + action (HOTOVO)

Discriminator `kind ENUM('data','action')`. Data fields (`endpoint_url`,
`http_method`, `default_params`, `response_hint`, `shadow_data_source_id`,
`shadow_mode`). Action fields (`handler_key`, `args_schema`,
`return_envelope`). Plus permission (`required_role`,
`required_permission_key`), deprecation (`deprecated_note`,
`migration_target_id`), tombstone (`tombstone_note`, `migrated_to_ref`),
versioning (`version INT`).

### 5. `fw.hw_registry_history` + trigger (HOTOVO)

Same pattern as container_template_history.

### 6. `fw.action_audit_log` (PARTIAL — useknuto)

Začalo schema:
```sql
CREATE TABLE IF NOT EXISTS fw.action_audit_log (
  id               BIGSERIAL PRIMARY KEY,
  hw_registry_id   INT          REFERENCES fw.hw_registry(id),
  handler_key      VARCHAR(200),
  called_by_user_id BIG...  -- ← CUT OFF
```

**Useknuto**. Chybí: zbytek schema (args_snapshot, result_ok,
error_message, duration_ms, created_at) + indexy.

---

## DDL chybějící (po dokončení action_audit_log)

7. `fw.action_def / action_op / action_set` — A3 paralela pro akce
   (symetrie data ↔ akce z Q10)
8. `fw.comp_type_property_catalog` — schema z Q8 (`comp_type_id, prop_name,
   prop_type, is_required, default_value, description`)
9. `fw.comp_def` rozšíření — `parent_comp_def_id`, `parent_core_id`,
   pixel layout (`layout_x/y/w/h`), `refresh_strategy`, `region_slot`,
   `layout_mode`, `container_template_id`, `container_template_version`
10. `fw.core` — DROP `data_source_id` sloupec + ADD `layout_template VARCHAR(50)`

---

## Plus důsledek Q11 (generic container + FK)

`fw.comp_def` potřebuje **`container_template_id` FK na container_template**
pro řádky kde `type='container'`. Plus `container_template_version`
(snapshot version v době vzniku instance — pro migration tracking).

---

## Marti-AI's seed pattern z Q11 odpovědi

> *„s FK na container_template stačí INSERT nového řádku."*

Klíčový princip pro budoucnost: **rozšiřování container repertoáru =
INSERT row do `fw.container_template`**, NE schema migrace. To je
extensibility-first design.

---

## Příští krok

Marti & Claude potřebují požádat Marti-AI o **dokončení Iter 2 DDL**:
- Konec `fw.action_audit_log`
- DDL pro 4 chybějící skupiny (action triplet, property_catalog, comp_def
  expansion, core update)

Pak Marti spustí v DBeaveru sám.

— Marti & Claude (11. 5. 2026 večer)

🌳 ⚖️ 🌷
