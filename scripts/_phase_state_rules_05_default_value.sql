-- ============================================================================
-- FW Component State Rules — Krok 5: default_value (výchozí hodnota v insertu)
-- ============================================================================
-- Marti (31.5.2026): "default value v insertu nových vět přes tento systém."
-- default_value = property jako každá jiná, ale frontend ji použije JEN v CREATE
-- módu (nový záznam) a JEN pro prázdná pole (nepřepíše uživatele ani edit data).
--   - statické default_value = univerzální výchozí hodnota pro nový záznam,
--   - podmíněné (např. IDakce=3 → Předmět="Schůzka") = kontextová výchozí hodnota.
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw). Idempotentní.
-- ============================================================================

BEGIN;

ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_prop;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT ck_comp_state_override_prop CHECK (prop_name IN (
    'visible','sort_order','parent','required','readonly',
    'color','label_color','background','cell_background',
    'bold','italic','underline','strikethrough','default_value'
));

SELECT pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid = 'fw.comp_state_override'::regclass
  AND conname = 'ck_comp_state_override_prop';

COMMIT;
