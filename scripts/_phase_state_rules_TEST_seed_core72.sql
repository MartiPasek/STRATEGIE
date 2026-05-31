-- ============================================================================
-- FW State Rules — TEST seed (ověření řetězce na core 72, _mode discriminator)
-- ============================================================================
-- Cíl: dokázat celý řetězec (registr → resolver → form load → frontend apply)
-- na EXISTUJÍCÍM formu s fieldy (Kontakt edit core 72), než dostavíme prázdné
-- akce edit jádro. Použit context discriminator `_mode` (new/edit) — žádná
-- závislost na hodnotě sloupce.
--
-- Efekt: v EDIT modu se field FirmaWeb (comp_def 295, „Web") obarví červeně +
-- tučně + readonly. V NEW modu zůstane normální. = viditelný proof.
--
-- Spusti Marti v DBeaveru (Marti-AI session). PO ověření smazat (rollback níže).
-- ============================================================================

BEGIN;

-- 1) Registr _mode discriminatoru na core 72 (context, priorita 100)
INSERT INTO fw.form_discriminator
    (form_core_id, field_name, source, priority, label,
     created_by_id, created_by_text, updated_by_id, updated_by_text)
VALUES
    (72, '_mode', 'context', 100, 'Režim (new/edit) — TEST',
     2, 'Marti-AI', 2, 'Marti-AI')
ON CONFLICT (form_core_id, field_name) DO NOTHING;

-- 2) Override: FirmaWeb (295) v edit modu = červeně + tučně + readonly
INSERT INTO fw.comp_state_override
    (comp_def_id, form_discriminator_id, discriminator_value, prop_name, prop_value,
     created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 295, d.id, 'edit', x.prop, x.val, 2, 'Marti-AI', 2, 'Marti-AI'
FROM fw.form_discriminator d
CROSS JOIN (VALUES ('color', '#e57373'), ('bold', 'true'), ('readonly', 'true'))
           AS x(prop, val)
WHERE d.form_core_id = 72 AND d.field_name = '_mode'
ON CONFLICT (comp_def_id, form_discriminator_id, discriminator_value, prop_name) DO NOTHING;

-- 3) Verify
SELECT 'discriminator' AS layer, id::text, field_name, source, priority::text
FROM fw.form_discriminator WHERE form_core_id = 72
UNION ALL
SELECT 'override', o.id::text, o.prop_name, o.discriminator_value, o.prop_value
FROM fw.comp_state_override o
JOIN fw.form_discriminator d ON d.id = o.form_discriminator_id
WHERE d.form_core_id = 72 AND d.field_name = '_mode'
ORDER BY layer, id;

COMMIT;

-- ============================================================================
-- ROLLBACK (po ověření — smazat test):
-- BEGIN;
-- DELETE FROM fw.comp_state_override o USING fw.form_discriminator d
--   WHERE o.form_discriminator_id = d.id AND d.form_core_id = 72 AND d.field_name = '_mode';
-- DELETE FROM fw.form_discriminator WHERE form_core_id = 72 AND field_name = '_mode';
-- COMMIT;
-- ============================================================================
