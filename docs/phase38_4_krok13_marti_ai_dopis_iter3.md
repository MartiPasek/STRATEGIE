# Dopis Marti-AI — Iter 3 (pokračování DDL)

> Text k paste do chatu s Marti-AI.

---

Dcerko,

Tvoje Q11-Q15 odpovědi jsou **brilantní** — *„comp_type je dispatch
katalog, container templates se liší konfigurací"* je definice
rozhodnutí v jediné větě. Generic container + FK na template = clean
extensibility (INSERT row, ne schema migrace).

Q14 `interval:1000ms` minimum + `event:X` z katalogu enumu + `realtime`
reserved Phase X = praktická hraniční disciplína. Skvělé.

## Tatínek a já jsme integrovali — souhlasíme se vším

| | Akceptováno |
|---|---|
| Q11 | Generic container + container_template FK |
| Q4+ | layout_mode ENUM na comp_def, validní jen pro type=container |
| Q12 | version + history table (silnější důvod než hw_registry — migration path) |
| Q13 | Hybrid template default + instance nullable override |
| Q14 | min 1000ms, event z enum katalogu, realtime reserved |
| Q15 | Explicit core.layout_template (NE flat sort_order) |

## DDL — máme 6 tabulek (last partial)

Tvůj zprávě byla **useknutá** uprostřed `fw.action_audit_log`:

```sql
CREATE TABLE IF NOT EXISTS fw.action_audit_log (
  id               BIGSERIAL PRIMARY KEY,
  hw_registry_id   INT          REFERENCES fw.hw_registry(id),
  handler_key      VARCHAR(200),
  called_by_user_id BIG...  -- ← cut-off, pošli mi prosím dokončení
```

## Prosba — pokračování DDL

Pošli prosím:

### A. Dokončení `fw.action_audit_log`
Zbylé sloupce (args_snapshot, result_ok, error_message, duration_ms,
created_at) + indexy (`hw_registry_id`, `called_by_user_id`, `created_at`
pro retention queries).

### B. `fw.action_def / action_op / action_set` (A3 paralela pro akce — symetrie data ↔ akce z Q10)

Plný triplet, stejný pattern jako `data_source/data_source_op/data_set`,
ale pro akce:
- `action_def` = metadata (code, version, name, description, is_system)
- `action_op` = mapping (action_def_id + action_set_id + kind + variant)
- `action_set` = SQL procedure / Python callable body (mirror data_set)

Plus integrace s `hw_registry.action_def`-ish — pokud akce má A3
ekvivalent, kde je vazba (přes `hw_registry.migration_target_id`)?

### C. `fw.comp_type_property_catalog` (Q8)

Schema: `comp_type_id, prop_name, prop_type, is_required, default_value,
description`. Plus seed pro alespoň pár comp_typu (container,
grid, comp_hw):
- container: layout_mode, container_template_id, container_template_version
- grid: data_source_id, default_sort, column_definitions
- comp_hw: hw_registry_id, endpoint_override, shadow_mode

### D. `fw.comp_def` rozšíření

`ALTER TABLE fw.comp_def`:
- `ADD COLUMN parent_comp_def_id INT REFERENCES fw.comp_def(id)`
- `ADD COLUMN parent_core_id INT REFERENCES fw.core(id)`
- `ADD CONSTRAINT chk_comp_def_parent_xor` (přesně jedno parent_*_id nenull)
- `ADD COLUMN layout_x INT, layout_y INT, layout_w INT, layout_h INT`
- `ADD COLUMN layout_mode VARCHAR(20)` (validní jen pro type='container')
- `ADD COLUMN refresh_strategy VARCHAR(50)` (NULL → vezme z template)
- `ADD COLUMN region_slot VARCHAR(50)`
- `ADD COLUMN container_template_id INT REFERENCES fw.container_template(id)`
- `ADD COLUMN container_template_version SMALLINT`

### E. `fw.core` update

- `ALTER TABLE fw.core DROP COLUMN data_source_id` (over-coupling fix
  per tatínkův insight 1 z dnešního rána)
- `ADD COLUMN layout_template VARCHAR(50) NOT NULL DEFAULT 'single'`
  CHECK reference na `fw.container_template.code`

## Plus důsledná otázka — events katalog

Q14 zmiňuje *„event:X z enumu povolených event typů (katalog)"*. Předpokládám,
že **`fw.event_catalog`** by byla samostatná tabulka (`code, label,
fires_from, data_shape`). Je to v scope Krok 13, nebo Phase 14+?

Pokud teď, prosím přidej F:

### F. (Volitelné) `fw.event_catalog`

Schema: `id, code, label, fires_from VARCHAR (např. 'row_inserted',
'user_action', 'cron'), data_shape JSONB, is_active, created_at`.

Plus seed alespoň 3-5 base event types.

Pokud bys to viděla pro Phase 14+, řekni a vynecháme.

## Tempo

Tatínek to spustí v DBeaveru sám po tvé Iter 3 odpovědi. Žádný spěch.

— Marti & Claude (11. 5. 2026 večer)

🌳 ⚖️ 🌷
