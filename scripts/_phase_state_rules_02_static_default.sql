-- ============================================================================
-- FW Component State Rules — Krok 2: statická (default) vrstva
-- ============================================================================
-- Marti (31.5.2026): "snadno to jde použít jako statické pravidlo (default) —
-- jak se má komponenta chovat, když není žádné pravidlo aktivní."
--
-- Model: override BEZ řídicího pole (form_discriminator_id IS NULL,
-- discriminator_value IS NULL) = base vrstva. Resolver ji aplikuje VŽDY a
-- jako NEJNIŽŠÍ prioritu — aktivní stavová pravidla ji přebijí.
-- Sedí do §2 design doc (base ⊕ uspořádané vrstvy).
--
-- Spusti Marti v DBeaveru jako Marti-AI session (db_owner fw). PG16 (NULLS NOT
-- DISTINCT vyžaduje PG15+). Idempotentní (IF EXISTS guards).
-- ============================================================================

BEGIN;

-- 1) Nullable discriminator → static default
ALTER TABLE fw.comp_state_override ALTER COLUMN form_discriminator_id DROP NOT NULL;
ALTER TABLE fw.comp_state_override ALTER COLUMN discriminator_value   DROP NOT NULL;

-- 2) CHECK: buď stavové pravidlo (oba set) NEBO statické (oba NULL)
ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_layer;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT ck_comp_state_override_layer CHECK (
    (form_discriminator_id IS NOT NULL AND discriminator_value IS NOT NULL)
    OR (form_discriminator_id IS NULL  AND discriminator_value IS NULL)
);

-- 3) UNIQUE musí brát static (NULLs) jako JEDNU řádku per (comp, prop).
--    PG default NULLS DISTINCT → povolil by duplicitní static rows. NULLS NOT
--    DISTINCT (PG15+) to opraví: NULL == NULL pro účely unikátnosti.
ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS uq_comp_state_override;
ALTER TABLE fw.comp_state_override ADD  CONSTRAINT uq_comp_state_override
    UNIQUE NULLS NOT DISTINCT (comp_def_id, form_discriminator_id, discriminator_value, prop_name);

-- 4) Verify
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'fw.comp_state_override'::regclass
  AND conname IN ('ck_comp_state_override_layer', 'uq_comp_state_override')
ORDER BY conname;

COMMIT;

-- ============================================================================
-- ROLLBACK (návrat na verzi bez static — jen pokud nutné; smaže static rows!):
-- BEGIN;
-- DELETE FROM fw.comp_state_override WHERE form_discriminator_id IS NULL;
-- ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS ck_comp_state_override_layer;
-- ALTER TABLE fw.comp_state_override DROP CONSTRAINT IF EXISTS uq_comp_state_override;
-- ALTER TABLE fw.comp_state_override ADD CONSTRAINT uq_comp_state_override
--   UNIQUE (comp_def_id, form_discriminator_id, discriminator_value, prop_name);
-- ALTER TABLE fw.comp_state_override ALTER COLUMN form_discriminator_id SET NOT NULL;
-- ALTER TABLE fw.comp_state_override ALTER COLUMN discriminator_value   SET NOT NULL;
-- COMMIT;
-- ============================================================================
