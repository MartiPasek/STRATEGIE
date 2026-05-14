-- Phase 38.4 Krok 14d-A (14.5.2026 večer, Marti-AI consultation done):
-- user_contacts audit fields ALTER ADD + partial unique index
--
-- Marti-AI's design (Q1A + Q1B + Q1C):
--   Q1A — polymorphic zachovat
--   Q1B — partial unique index místo EXCLUDE constraint
--   Q1C — soft delete (status='archived' pattern)
--
-- Symetrie s parent users table (12.5. večer 16. dárek-scéna —
-- "system je taky user" doctrine, created_by_id / updated_by_id audit
-- fields).

-- ─── 1. Audit fields ADD ───────────────────────────────────────
ALTER TABLE public.user_contacts
  ADD COLUMN IF NOT EXISTS created_by_id   INT REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS created_by_text VARCHAR(255),
  ADD COLUMN IF NOT EXISTS updated_by_id   INT REFERENCES public.users(id),
  ADD COLUMN IF NOT EXISTS updated_by_text VARCHAR(255);

-- ─── 2. updated_at trigger (Marti-AI's Q7 z 9.5. pattern) ─────
-- Funkce update_updated_at() už existuje (z master tier 8.5. Phase
-- 35-E.3). Pokud chybí na public scheme, replicate:
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger na user_contacts (idempotent — drop if exists, then create)
DROP TRIGGER IF EXISTS user_contacts_updated_at_trigger ON public.user_contacts;
CREATE TRIGGER user_contacts_updated_at_trigger
BEFORE UPDATE ON public.user_contacts
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ─── 3. Partial unique index na is_primary (Marti-AI's Q1B) ───
-- Garantuje jen 1 primary per (user_id, contact_type) mezi aktivními
-- (status='active'). Archivované záznamy unconstrained — historický
-- "primary" z minulosti může spolu s current primary koexistovat.
--
-- Existing anomalie data (Marti id=1 má 2 primary phones): tato migrace
-- selže pokud aktivní data porušují constraint. Diagnostic SELECT před:

-- DIAGNOSTIC (run first, check zda jsou anomalie):
SELECT user_id, contact_type, COUNT(*) AS primary_count
FROM public.user_contacts
WHERE is_primary = true AND status = 'active'
GROUP BY user_id, contact_type
HAVING COUNT(*) > 1;
-- Pokud vrátí rows: vyřešit data PRED constraint create.

-- Fix anomalie data (pokud existují):
-- UPDATE public.user_contacts
-- SET is_primary = false
-- WHERE id IN (...)  -- IDs starých duplicate primary rows
--   AND is_primary = true;

-- Apply constraint:
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_contacts_primary
  ON public.user_contacts (user_id, contact_type)
  WHERE is_primary = true AND status = 'active';

-- ─── 4. Verify ────────────────────────────────────────────────
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'user_contacts'
ORDER BY ordinal_position;

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'user_contacts'
ORDER BY indexname;

SELECT trigger_name, event_manipulation, action_timing
FROM information_schema.triggers
WHERE event_object_table = 'user_contacts';
