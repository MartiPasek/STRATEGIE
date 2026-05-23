-- ============================================================
-- Phase 22.5.2026 — fw.hw_registry korekce klasifikace
-- ============================================================
-- Marti's catch: dva typy komponent — FW (kompozice z primitives)
-- vs HW (specifická logic). Z 9 manifestů jen 3 jsou skutečně HW:
--   - field_picker_modal (introspection + multi-select)
--   - catalog_picker    (dynamic data_source + initialId render)
--   - entity_picker     (bidirectional field_extern + display modes)
--
-- Ostatní 6 jsou FW kompozice (panel + standard primitives), nepatří
-- do fw.hw_registry — patří do framework metadata (fw.core + comp_def
-- hierarchy). DROP z hw_registry.
-- ============================================================

BEGIN;

DELETE FROM fw.hw_registry
WHERE kind = 'component'
  AND name IN (
    'fw_form',
    'soudecek_core_form',
    'jadro_radek_form',
    'data_source_editor',
    'data_set_editor',
    'db_connection_editor'
  );

COMMIT;

-- ─── Verify (run separately) ────────────────────────────────────
-- SELECT id, name, kind, label FROM fw.hw_registry
-- WHERE kind = 'component'
-- ORDER BY name;
--
-- Expected: 3 rows (catalog_picker, entity_picker, field_picker_modal)
