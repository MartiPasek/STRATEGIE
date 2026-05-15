-- Phase 38.4 Krok 14g-G hotfix (15.5.2026 rano):
-- Marti's "novy soudecek v gridu vidim, ale v levem strome ne".
--
-- DIAGNOSIS: POST /design/menu-node INSERT bez visibility_scope →
-- NULL → tree query (WHERE visibility_scope = 'parent_only') ho
-- filtruje out. Existing rows (system, system.audit.*, atd.) maji
-- 'parent_only' nastaveno.
--
-- FIX: backfill NULL → 'parent_only' pro vsechny existing rows
-- vytvorene pres novy endpoint (bez visibility_scope).
-- Plus POST endpoint code aktualizovan na explicit default 'parent_only'.

-- 1. Audit: kolik rows s NULL visibility_scope
SELECT id, code, label, kind, status, visibility_scope, created_at
FROM fw.menu_node
WHERE visibility_scope IS NULL
ORDER BY id;

-- 2. Backfill — pouze NULL rows (existing 'parent_only' / 'public' /
-- atd. zustavaji unchanged)
UPDATE fw.menu_node
SET visibility_scope = 'parent_only',
    updated_by_text = COALESCE(updated_by_text, 'Marti') || ' (visibility backfill)'
WHERE visibility_scope IS NULL
  AND status = 'active';

-- 3. Verify Marti's core_jadro row
SELECT id, code, label, parent_id, sort_order, kind, status,
       visibility_scope, created_at
FROM fw.menu_node
WHERE code = 'core_jadro';
-- Expected: visibility_scope = 'parent_only' po UPDATE
