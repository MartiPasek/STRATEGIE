-- ============================================================================
-- FW Component State Rules — Krok 3: cell_background (pozadí zadávací buňky)
-- ============================================================================
-- Marti (31.5.2026): "background = pozadí celé komponenty; přidat ještě pozadí
-- zadávací buňky (vstupního pole) zvlášť." → nový prop 'cell_background'.
-- background → aplikuje se na wrapper (celá komponenta), cell_background → na
-- input element (zadávací buňka).
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw). Idempotentní.
-- ============================================================================

BEGIN;

ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_prop;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT ck_comp_state_override_prop CHECK (prop_name IN (
    'visible','sort_order','parent','required','readonly',
    'color','background','cell_background','bold','italic','underline','strikethrough'
));

-- Verify
SELECT pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid = 'fw.comp_state_override'::regclass
  AND conname = 'ck_comp_state_override_prop';

COMMIT;
