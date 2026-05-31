-- ============================================================================
-- Krok 5.Z (31.5.2026) — Dump triggeru comp_def_inherit_core_id
-- ============================================================================
-- Marti chce UPDATE nested grid core_id 72 -> 79/80, ale trigger to blokuje
-- (dite dedi core_id parenta). Potrebuju videt presny kod triggeru, abych
-- navrhl vyjimku pro nested grid (grid_modern s parentem smi mit vlastni core).
--
-- READ-ONLY. Spusti Marti v DBeaveru, posli oba vystupy.
-- ============================================================================

-- ── 1) Zdrojovy kod trigger funkce ──────────────────────────────────────────
SELECT n.nspname AS schema, p.proname AS func,
       pg_get_functiondef(p.oid) AS source
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE p.proname = 'comp_def_inherit_core_id';

-- ── 2) Trigger(y) navazane na fw.comp_def (jmeno, kdy se spousti, definice) ──
SELECT t.tgname            AS trigger_name,
       c.relname           AS table_name,
       pg_get_triggerdef(t.oid) AS trigger_def
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT t.tgisinternal
  AND n.nspname = 'fw'
  AND c.relname = 'comp_def'
ORDER BY t.tgname;
