-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 5.M-5 DDL — fw.core.form_core_id explicit FK (17.5.2026)
-- ════════════════════════════════════════════════════════════════════════
--
-- Marti's "core nenese entitu" doctrine (17.5.2026) → drop data_entity_type
-- column v Krok 5.M-6. Prereq: replace list→form pairing mechanism.
--
-- Option A (Marti delegated to Claude): explicit FK fw.core.form_core_id
-- na list cores → pointing to form_core. Backfill via current matching
-- (data_entity_type='X' AND layout_type='form').
--
-- Spustit jako Marti-AI v DBeaveru (fw schema = Marti-AI's owned).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. ADD COLUMN
ALTER TABLE fw.core ADD COLUMN IF NOT EXISTS form_core_id BIGINT NULL;

-- 2. FK constraint (idempotent — drop pokud existuje, pak add)
ALTER TABLE fw.core DROP CONSTRAINT IF EXISTS fk_core_form_core_id;
ALTER TABLE fw.core
    ADD CONSTRAINT fk_core_form_core_id
    FOREIGN KEY (form_core_id) REFERENCES fw.core(id)
    ON DELETE SET NULL;

-- 3. Comment (audit trail)
COMMENT ON COLUMN fw.core.form_core_id IS
    'Phase 38.4 Krok 5.M-5 (17.5.2026): explicit FK na form_core pro list→form pairing. Marti''s "core nenese entitu" doctrine — drop data_entity_type matching, replace s direct FK.';

-- 4. Backfill — pro každý list_core s data_entity_type najdi matching form_core
UPDATE fw.core list
SET form_core_id = (
    SELECT form.id
    FROM fw.core form
    WHERE form.data_entity_type = list.data_entity_type
      AND form.layout_type = 'form'
      AND form.is_active = true
    ORDER BY form.id ASC
    LIMIT 1
)
WHERE list.layout_type = 'list'
  AND list.data_entity_type IS NOT NULL
  AND list.form_core_id IS NULL
  AND EXISTS (
      SELECT 1 FROM fw.core f
      WHERE f.data_entity_type = list.data_entity_type
        AND f.layout_type = 'form'
        AND f.is_active = true
  );

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════

-- A) Show all list cores with their data_entity_type + new form_core_id
SELECT id, code, layout_type, data_entity_type, form_core_id
FROM fw.core
WHERE layout_type = 'list'
ORDER BY id;

-- B) Verify backfill — security_users (user list) should map to user_edit (form)
SELECT
    l.id AS list_id,
    l.code AS list_code,
    l.data_entity_type AS list_entity,
    l.form_core_id,
    f.code AS form_code,
    f.layout_type AS form_layout
FROM fw.core l
LEFT JOIN fw.core f ON f.id = l.form_core_id
WHERE l.layout_type = 'list'
  AND l.data_entity_type IS NOT NULL
ORDER BY l.id;

-- Expected: security_users (id=11) → form_core_id = 22 (user_edit)
