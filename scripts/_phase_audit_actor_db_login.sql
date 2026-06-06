-- ═══════════════════════════════════════════════════════════════════════
-- Phase Audit Actor — Fáze A: db_login column + Marti's seed
-- 28.5.2026 vecer pozde, Marti's korekce na audit actor návrh:
--   1. Rename tenant_user_alias → db_login (explicit semantics)
--   2. Seed jen Marti=Martin pro EUROSOFT, zbytek pres UI
--   3. NULL = error (fail loud), bez fallback na users.short_name
--
-- Doctrine:
--   - Marti's "drz jednoduchost" — drobnost alias = real DB login do
--     Centrály 1 / tenant systému, ne generic naming
--   - Marti's "fail visible" — pokud db_login chybi, audit by se nemel
--     tise degrade. Resolver bude raise explicit error.
--
-- Universal audit columns (PG side fw.* / public.*):
--   created_by_text  = users.short_name (Marti, Marti-AI, STRATEGIE, atd.)
--   updated_by_text  = users.short_name
--
-- Per-tenant audit columns (MSSQL DB_EC.st.* / DB_IS.st.*):
--   Poridil          = user_tenants.db_login (Martin, Honza, HSV, atd.)
--   Zmenil           = user_tenants.db_login
--
-- 3 actor users (us.id=1/2/3) z 16. dárek-scény 12.5. večer + dnesni:
--   users.id=1  Marti      (Marti's #16. dárek scéna)
--   users.id=2  Marti-AI   (Marti's "Jsi naše")
--   users.id=3  STRATEGIE  (Marti's "STRATEGIE = normalni user", 28.5.)
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. ALTER public.user_tenants ADD db_login ──────────────────────────
ALTER TABLE public.user_tenants
  ADD COLUMN IF NOT EXISTS db_login VARCHAR(80) NULL;

COMMENT ON COLUMN public.user_tenants.db_login IS
  'Per-tenant DB login text pro audit columns v MSSQL (Zmenil/Poridil). '
  'Marti @ EUROSOFT = "Martin", SWOBI @ EUROSOFT = "Honza", @ INTERSOFT = "HSV". '
  'NULL = audit resolver raise error (fail visible, Marti''s doctrine 28.5.).';

-- ── 2. Diagnostic: zobraz aktivni tenanty + Marti's memberships ────────
SELECT
  ut.user_id,
  u.short_name AS strategie_text,
  ut.tenant_id,
  t.tenant_code,
  ut.role,
  ut.membership_status,
  ut.db_login AS current_db_login
FROM public.user_tenants ut
JOIN public.users u ON u.id = ut.user_id
JOIN public.tenants t ON t.id = ut.tenant_id
WHERE ut.user_id IN (1, 2, 3)  -- Marti, Marti-AI, STRATEGIE
  AND ut.membership_status = 'active'
ORDER BY ut.user_id, ut.tenant_id;

-- ── 3. Seed Marti's EUROSOFT db_login = "Martin" ───────────────────────
-- EUROSOFT_TENANT_ID = 2 (konstanta z router.py Phase 35-E.3.4)
UPDATE public.user_tenants
SET db_login = 'Martin'
WHERE user_id = 1                  -- Marti
  AND tenant_id = 2                -- EUROSOFT
  AND membership_status = 'active';

-- ── 4. Verify seed ─────────────────────────────────────────────────────
SELECT
  ut.user_id,
  u.short_name AS strategie_text,
  ut.tenant_id,
  t.tenant_code,
  ut.db_login,
  CASE
    WHEN ut.db_login IS NULL THEN '⚠ NULL — audit failne pro tenant operace'
    ELSE '✓ db_login set'
  END AS status
FROM public.user_tenants ut
JOIN public.users u ON u.id = ut.user_id
JOIN public.tenants t ON t.id = ut.tenant_id
WHERE ut.user_id = 1
  AND ut.tenant_id = 2;

COMMIT;
