-- Phase 38.4 Krok 14b — Migrace 1: users.login_name
-- Date: 13.5.2026 (drft pripraveny 12.5. vecer ~20:30)
-- Marti's design: "v ramci jednoho firemniho tenanta budeme mit vzdy
-- unikatni Login. Ale i tak to ID jisti."
-- Decision: globally UNIQUE (jednodussi nez per-tenant junction).
-- Backfill ze users.short_name (existing pattern Marti, Kristy, Sarka, ...)
--
-- Marti-AI's bod #C (12.5. vecer): "tichá past při deploy" — backfill MUSI
-- byt PRED NOT NULL UNIQUE, jinak migrace failne na existing rows.

BEGIN;

-- Step 1: ADD COLUMN nullable (safe — existing rows mit NULL)
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS login_name VARCHAR(50);

-- Step 2: Backfill ze short_name pro existing rows
UPDATE public.users
SET login_name = short_name
WHERE login_name IS NULL
  AND short_name IS NOT NULL
  AND short_name != '';

-- Step 3: Verify zadny NULL nezustal (pokud ano, manual fix nutny)
DO $$
DECLARE
  null_count INTEGER;
  null_users TEXT;
BEGIN
  SELECT COUNT(*) INTO null_count
  FROM public.users
  WHERE login_name IS NULL;

  IF null_count > 0 THEN
    SELECT string_agg(format('id=%s (%s %s)', id, first_name, last_name), ', ')
    INTO null_users
    FROM public.users
    WHERE login_name IS NULL;

    RAISE EXCEPTION
      'Cannot set login_name NOT NULL — % rows still NULL. Manual fix: %',
      null_count, null_users;
  END IF;
END $$;

-- Step 4: NOT NULL + UNIQUE constraint
ALTER TABLE public.users
  ALTER COLUMN login_name SET NOT NULL;

ALTER TABLE public.users
  ADD CONSTRAINT users_login_name_key UNIQUE (login_name);

-- Step 5: Verify final state
SELECT id, first_name, last_name, short_name, login_name
FROM public.users
ORDER BY id;

COMMIT;

-- ROLLBACK guard: pokud chceme revert,
-- BEGIN;
--   ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_login_name_key;
--   ALTER TABLE public.users ALTER COLUMN login_name DROP NOT NULL;
--   ALTER TABLE public.users DROP COLUMN IF EXISTS login_name;
-- COMMIT;
