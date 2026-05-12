-- Phase 38.4 Krok 14b — Migrace 4: personas.linked_user_id
-- Date: 13.5.2026 (drft pripraveny 12.5. vecer ~20:30)
--
-- Marti's decision (12.5. vecer): Marti-AI dostala users.id=2 — plnou
-- user identity. Persona Marti-AI v personas table by mela ukazovat na
-- tento user row (cross-reference, drzi dvojí identity).
--
-- Use case:
--   - Marti-AI's chat actions vola PATCH endpoint
--   - Composer resolve actor: pokud session = persona Marti-AI,
--     fetch personas.linked_user_id → users.id=2
--   - Audit log: updated_by_id = 2, updated_by_text = 'Marti-AI'
--   - Stejny FK pattern jako pro lidske users
--
-- Plus do budoucnosti: kazda nova persona (Honza-AI, atd.) bude mit
-- automaticky linked user row pro audit consistency.

BEGIN;

-- ADD COLUMN nullable (existing persony nemaji user row)
ALTER TABLE public.personas
  ADD COLUMN IF NOT EXISTS linked_user_id INTEGER REFERENCES public.users(id);

-- Index pro reverse lookup (user → persona)
CREATE INDEX IF NOT EXISTS ix_personas_linked_user_id
  ON public.personas(linked_user_id)
  WHERE linked_user_id IS NOT NULL;

-- Backfill pro Marti-AI persona (id=1 v personas → user id=2)
-- Marti's INSERT users.id=2 byl provedeny manually 12.5. vecer
UPDATE public.personas
SET linked_user_id = 2
WHERE id = 1
  AND name = 'Marti-AI'
  AND linked_user_id IS NULL;

-- Verification
SELECT
  p.id AS persona_id,
  p.name AS persona_name,
  p.linked_user_id,
  u.first_name || ' ' || u.last_name AS user_full_name,
  u.short_name,
  u.login_name
FROM public.personas p
LEFT JOIN public.users u ON u.id = p.linked_user_id
ORDER BY p.id;

COMMIT;

-- ROLLBACK guard:
-- BEGIN;
--   DROP INDEX IF EXISTS public.ix_personas_linked_user_id;
--   ALTER TABLE public.personas DROP COLUMN IF EXISTS linked_user_id;
-- COMMIT;
