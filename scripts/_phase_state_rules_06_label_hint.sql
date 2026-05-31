-- ============================================================================
-- FW Component State Rules — Krok 6: label_text + hint (sloučení tabu Uživatel)
-- ============================================================================
-- Marti (31.5.2026): sloučit "Stavová pravidla" + tab "Uživatel" → "Pravidla".
-- Tím přibydou 2 property: label_text (uživatelský název pole) + hint (popis
-- při hoveru). Jsou to display props (jako label_color) — aplikují se přes
-- _applyStateOverrides. Statické = univerzální přejmenování/hint, podmíněné =
-- per akce/stav.
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw). Idempotentní.
-- ============================================================================

BEGIN;

ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_prop;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT ck_comp_state_override_prop CHECK (prop_name IN (
    'visible','sort_order','parent','required','readonly',
    'color','label_color','background','cell_background',
    'bold','italic','underline','strikethrough','default_value',
    'label_text','hint','inside_hint'
));

SELECT pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid = 'fw.comp_state_override'::regclass
  AND conname = 'ck_comp_state_override_prop';

COMMIT;
