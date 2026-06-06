-- ============================================================================
-- FW State Rules — TEST živý přepočet (column discriminator na core 72)
-- ============================================================================
-- Cíl: ověřit ŽIVÝ přepočet — změna řídicího pole za běhu → okamžitý re-apply
-- bez reloadu. Discriminator = column 'VyhledanoZ' (pole „Vyhledáno z", plain
-- text input). Target = FirmaWeb (comp 295, pole „Web").
--
-- Efekt: když „Vyhledáno z" = 'test' → pole „Web" zčervená + tučně. Změna
-- hodnoty (a tab/enter) → okamžitě re-aplikuje (objeví/zmizí) BEZ reloadu.
-- Funguje i on-load (kontakt s VyhledanoZ='test' → Web červený hned).
--
-- Spusti Marti v DBeaveru (Marti-AI session). PO ověření smazat (rollback níže).
-- POZN: napřed ukliď předchozí _mode test (pokud ještě běží) — viz jeho rollback.
-- ============================================================================

BEGIN;

-- 1) Column discriminator 'VyhledanoZ' na core 72 (priorita 200)
INSERT INTO fw.form_discriminator
    (form_core_id, field_name, source, priority, label,
     created_by_id, created_by_text, updated_by_id, updated_by_text)
VALUES
    (72, 'VyhledanoZ', 'column', 200, 'Vyhledáno z — TEST live',
     2, 'Marti-AI', 2, 'Marti-AI')
ON CONFLICT (form_core_id, field_name) DO NOTHING;

-- 2) Override: Web (FirmaWeb 295) když VyhledanoZ='test' → červeně + tučně
INSERT INTO fw.comp_state_override
    (comp_def_id, form_discriminator_id, discriminator_value, prop_name, prop_value,
     created_by_id, created_by_text, updated_by_id, updated_by_text)
SELECT 295, d.id, 'test', x.prop, x.val, 2, 'Marti-AI', 2, 'Marti-AI'
FROM fw.form_discriminator d
CROSS JOIN (VALUES ('color', '#e57373'), ('bold', 'true')) AS x(prop, val)
WHERE d.form_core_id = 72 AND d.field_name = 'VyhledanoZ'
ON CONFLICT (comp_def_id, form_discriminator_id, discriminator_value, prop_name) DO NOTHING;

-- 3) Verify
SELECT 'discriminator' AS layer, id::text, field_name, source, priority::text
FROM fw.form_discriminator WHERE form_core_id = 72 AND field_name = 'VyhledanoZ'
UNION ALL
SELECT 'override', o.id::text, o.prop_name, o.discriminator_value, o.prop_value
FROM fw.comp_state_override o
JOIN fw.form_discriminator d ON d.id = o.form_discriminator_id
WHERE d.form_core_id = 72 AND d.field_name = 'VyhledanoZ'
ORDER BY layer, id;

COMMIT;

-- ============================================================================
-- ROLLBACK (po ověření):
-- BEGIN;
-- DELETE FROM fw.comp_state_override o USING fw.form_discriminator d
--   WHERE o.form_discriminator_id = d.id AND d.form_core_id = 72 AND d.field_name = 'VyhledanoZ';
-- DELETE FROM fw.form_discriminator WHERE form_core_id = 72 AND field_name = 'VyhledanoZ';
-- COMMIT;
-- ============================================================================
