-- Phase 40 v2 r3 — Mini-fáze A.1 (19.5.2026 ráno)
-- DDL: users.label_color + conversations.is_shared (cache)
--
-- Marti's volby (Q1 + Q2):
--   Marti (id=1)    = green  #56b870 ("Sebe nejakou zelenou, davam tomu zelenou")
--   Marti-AI (id=2) = gold   #efd9a8 (match Privát Marti badge color, "aby se to nepletlo")
--   Kristý (id=11)  = pink   #e8a4c8 ("jednoznacne nejaka ruzova")
--   Claude (id=23)  = teal   #5dc8c0 (peer, distinct od trojice barev)
--   Ostatní         = NULL   → frontend computes hue z user_id hash
--
-- conversations.is_shared cache (Q2 = B) — auto-update v save_message hook
-- po prvním cross-author insertu. Nezávislé od conversation_shares table.
--
-- Spuštění: DBeaver jako role "Marti-AI" (db_owner public schema).
-- Verify smoke: SELECT * FROM users WHERE label_color IS NOT NULL ORDER BY id;
--             SELECT COUNT(*) FROM conversations WHERE is_shared = TRUE;

BEGIN;

-- ─────────────────────────────────────────────────────────────────────
-- 1. users.label_color VARCHAR(7) — hex barva pro shared chat labels
-- ─────────────────────────────────────────────────────────────────────
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS label_color VARCHAR(7);

COMMENT ON COLUMN public.users.label_color IS
  'Phase 40 v2 r3 (19.5.2026): hex barva (#RRGGBB) pro shared chat attribution. NULL = frontend computes hue z user_id hash. Marti id=1=#56b870 (green), Marti-AI id=2=#efd9a8 (gold), Kristý id=11=#e8a4c8 (pink), Claude id=23=#5dc8c0 (teal).';

-- ─────────────────────────────────────────────────────────────────────
-- 2. conversations.is_shared BOOLEAN — cache (Q2 volba B)
-- ─────────────────────────────────────────────────────────────────────
ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN public.conversations.is_shared IS
  'Phase 40 v2 r3 (19.5.2026): cache — TRUE pokud konverzace má 2+ distinct author_user_id (human) NEBO má řádek v conversation_shares. Aktualizováno hookem v save_message. Frontend detekuje shared mode pres tento flag pro bold+barevný attribution label.';

-- Index pro list-shared-with-me queries (rychlé filter)
CREATE INDEX IF NOT EXISTS ix_conversations_is_shared
  ON public.conversations (is_shared)
  WHERE is_shared = TRUE;

-- ─────────────────────────────────────────────────────────────────────
-- 3. Backfill explicit barvy pro známé usery
-- ─────────────────────────────────────────────────────────────────────
UPDATE public.users SET label_color = '#56b870' WHERE id = 1  AND label_color IS NULL;  -- Marti
UPDATE public.users SET label_color = '#efd9a8' WHERE id = 2  AND label_color IS NULL;  -- Marti-AI
UPDATE public.users SET label_color = '#e8a4c8' WHERE id = 11 AND label_color IS NULL;  -- Kristý
UPDATE public.users SET label_color = '#5dc8c0' WHERE id = 23 AND label_color IS NULL;  -- Claude

-- ─────────────────────────────────────────────────────────────────────
-- 4. Backfill conversations.is_shared (pre-existing data)
--    Detection: distinct human author_user_id count > 1 v messages
-- ─────────────────────────────────────────────────────────────────────
UPDATE public.conversations c
SET is_shared = TRUE
WHERE id IN (
    SELECT DISTINCT m.conversation_id
    FROM public.messages m
    WHERE m.author_type = 'human'
      AND m.author_user_id IS NOT NULL
    GROUP BY m.conversation_id
    HAVING COUNT(DISTINCT m.author_user_id) >= 2
);

-- Plus: konverzace s existing conversation_shares = shared
UPDATE public.conversations c
SET is_shared = TRUE
WHERE id IN (SELECT DISTINCT conversation_id FROM public.conversation_shares);

-- ─────────────────────────────────────────────────────────────────────
-- VERIFY
-- ─────────────────────────────────────────────────────────────────────
SELECT
  id,
  first_name,
  last_name,
  short_name,
  label_color,
  CASE
    WHEN label_color IS NULL THEN '(frontend hash)'
    ELSE 'explicit'
  END AS color_source
FROM public.users
WHERE id IN (1, 2, 11, 23)
ORDER BY id;

-- Counter — kolik konverzací je teď shared (post-backfill)
SELECT
  COUNT(*) AS total_conversations,
  COUNT(*) FILTER (WHERE is_shared = TRUE) AS shared_conversations,
  COUNT(*) FILTER (WHERE is_shared = FALSE) AS solo_conversations
FROM public.conversations
WHERE is_deleted = FALSE;

COMMIT;

-- Po commit smoke: otevři libovolnou konverzaci, kterou jsi včera testoval
-- s Kristýnkou — měla by mít is_shared=TRUE.
