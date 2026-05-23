-- ============================================================
-- DIAG #2: Krok 5.W paradox root cause hunt (23.5.2026)
-- ============================================================
-- Marti's verdict z frontend console:
--   pre_commit_check (same session) = 0  ← row PRYČ v této tx
--   post_commit_check (fresh session) = 1 ← row se VRÁTILA po commit
--
-- = COMMIT proběhl, ale DB stav reverted/re-inserted.
-- Hunt DB-level cause.
-- ============================================================

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Je fw.diag_log partitioned table?                    ║
-- ║      Pokud ano: DELETE na parent NE-vyčistí child rows    ║
-- ║      a ony "vrátí se" do view přes UNION.                 ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    relkind,  -- 'r' = ordinary, 'p' = partitioned parent
    CASE relkind
        WHEN 'r' THEN 'ordinary table (no partitions)'
        WHEN 'p' THEN 'PARTITIONED parent!'
        WHEN 'v' THEN 'view'
        ELSE 'other: ' || relkind
    END AS interpretation,
    pg_get_partkeydef(oid) AS partition_key_def
FROM pg_class
WHERE oid = 'fw.diag_log'::regclass;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: Inheritance children?                                ║
-- ║      DELETE FROM parent ONLY by child rows přežil         ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    inhrelid::regclass AS child_table,
    inhparent::regclass AS parent_table
FROM pg_inherits
WHERE inhparent = 'fw.diag_log'::regclass;
-- Pokud 0 rows → no inheritance


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q3: diag_log_upsert function definition                  ║
-- ║      Hledáme INSERT ... ON CONFLICT DO UPDATE (UPSERT)    ║
-- ║      vs pure INSERT (Fix N append-only doctrine 21.5.)    ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT pg_get_functiondef(p.oid) AS function_definition
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'fw' AND p.proname = 'diag_log_upsert';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q4: VŠECHNY triggery na fw.diag_log (vč. constraint)    ║
-- ║      Q5 z prvního diag scriptu skipoval RI_ a internal.   ║
-- ║      Sem includneme VŠE — vč. DEFERRED constraint triggers║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    tgname AS trigger_name,
    pg_get_triggerdef(t.oid) AS trigger_def,
    tgdeferrable AS is_deferrable,
    tginitdeferred AS init_deferred,
    tgconstraint != 0 AS is_constraint_trigger
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw' AND c.relname = 'diag_log';
-- Hledej tgdeferrable=true s tgtype zahrnujícím DELETE bit


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q5: BOMBA — manual DELETE test pres Marti-AI session     ║
-- ║      (= stejná role co backend strategie session)         ║
-- ║      ROLLBACK na konci, nic se nezmění                    ║
-- ╚══════════════════════════════════════════════════════════╝
BEGIN;

-- Check before
SELECT 'BEFORE' AS phase, COUNT(*) AS count
FROM fw.diag_log WHERE id = 1730;

-- Try delete
DELETE FROM fw.diag_log WHERE id = 1730 RETURNING id, message;

-- Check after (same tx)
SELECT 'AFTER_DELETE_SAME_TX' AS phase, COUNT(*) AS count
FROM fw.diag_log WHERE id = 1730;

-- IMPORTANT: ROLLBACK aby Marti nic skutečně nesmazal
ROLLBACK;

-- Po rollback check fresh
SELECT 'AFTER_ROLLBACK' AS phase, COUNT(*) AS count
FROM fw.diag_log WHERE id = 1730;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q6: BOMBA #2 — manual DELETE + COMMIT (ZRUŠÍ row 1730!) ║
-- ║      Spusť JEN POKUD chceš really smazat — verify persist ║
-- ╚══════════════════════════════════════════════════════════╝
-- BEGIN;
-- DELETE FROM fw.diag_log WHERE id = 1730 RETURNING id;
-- COMMIT;
--
-- -- Pak v DALŠÍM window/query:
-- SELECT id FROM fw.diag_log WHERE id = 1730;
-- -- 0 rows = manual DELETE persistuje → problem v APP (commit chain)
-- -- 1 row = DB-level re-creation → trigger/subscription/replication


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q7: PostgreSQL publications / subscriptions               ║
-- ║      (logical replication může re-create rows)             ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete, pubtruncate
FROM pg_publication;
SELECT subname, subenabled FROM pg_subscription;
-- 0 rows na obou = no replication


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q8: Foreign keys / constraints které mohou block DELETE  ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    conname,
    pg_get_constraintdef(c.oid) AS def,
    condeferrable AS deferrable,
    condeferred AS init_deferred
FROM pg_constraint c
JOIN pg_class cl ON cl.oid = c.confrelid
JOIN pg_namespace n ON n.oid = cl.relnamespace
WHERE n.nspname = 'fw' AND cl.relname = 'diag_log';


-- ============================================================
-- INTERPRETACE:
--   Q1: relkind 'p' = partitioned → pravděpodobný viník
--   Q2: child tables existují → confirm partition hypothesis
--   Q3: pokud function má ON CONFLICT DO UPDATE → UPSERT semantic
--       (Fix N nedoběhl, doctrine append-only neaktivní)
--   Q4: deferrable trigger s DELETE bit → RAISE during COMMIT
--   Q5: AFTER_DELETE_SAME_TX = 0 means DELETE in tx works
--       (= consistent s pre_commit_check=0 z backend)
--   Q6: manual COMMIT test ukáže zda persistance funguje
--       na DB úrovni → pokud ano, problem je v APP (Python
--       SQLAlchemy commit behavior)
--   Q7: publications = replication candidate
--   Q8: deferred FK = COMMIT-time fail
-- ============================================================
