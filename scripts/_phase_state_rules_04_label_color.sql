-- ============================================================================
-- FW Component State Rules — Krok 4: label_color (barva labelu pole)
-- ============================================================================
-- Marti (31.5.2026): "přidej ještě tu poslední variantu — změnu barvy labelu."
-- color = barva hodnoty (value/input), label_color = barva popisku (label) zvlášť.
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw). Idempotentní.
-- ============================================================================

BEGIN;

ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_prop;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT ck_comp_state_override_prop CHECK (prop_name IN (
    'visible','sort_order','parent','required','readonly',
    'color','label_color','background','cell_background','bold','italic','underline','strikethrough'
));

SELECT pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid = 'fw.comp_state_override'::regclass
  AND conname = 'ck_comp_state_override_prop';

COMMIT;
