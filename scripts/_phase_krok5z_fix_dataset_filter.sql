-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z FIX v3 — framework_comp_def_select CAST (BIND-PROOF, bez : dialogu)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- ROOT CAUSE: ':filter_core_id::int' NEFUNGUJE v runneru (psycopg2 SyntaxError
-- "at or near :"). Fix H regex chyti z '::int' falesny param 'int', '::' mate
-- SQLAlchemy parser. Spravna forma (konvence _phase38_4_krok11e):
--   WHERE (CAST(:filter_core_id AS int) IS NULL OR cd.core_id = :filter_core_id)
--
-- Tento skript SET cely sql_text na spravnou formu. Stavi text pres chr(58)
-- (=dvojtecka), takze DBeaver NEVIDI ':filter_core_id' literalne -> ZADNY
-- bind dialog (gotcha #111 obejito). Deterministicke — nezalezi na soucasnem
-- (rozbitem) stavu sql_text.
--
-- Tento data_set patri PREHLEDU Komponent (core 73). Embedded grid (detail)
-- pouziva separatni framework_comp_def_detail (viz _phase_krok5z_detail_dataset.sql).
-- ════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
  c text := chr(58);   -- ':'
  v_sql text;
BEGIN
  v_sql :=
'SELECT
  cd.id,
  cd.core_id,
  cd.parent_comp_def_id,
  cd.type_id,
  ct.code AS type_code,
  COALESCE(ct.label, ct.code) AS type_label,
  cd.name,
  cd.caption,
  cd.sort_order,
  cd.is_active,
  cd.root,
  cd.data_source_id,
  cd.layout_mode,
  cd.region_slot,
  cd.created_at,
  cd.updated_at,
  cd.created_by_text,
  cd.updated_by_text
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE (CAST(' || c || 'filter_core_id AS int) IS NULL OR cd.core_id = ' || c || 'filter_core_id)
ORDER BY cd.core_id, cd.sort_order NULLS LAST, cd.id';

  UPDATE fw.data_set
  SET sql_text = v_sql
  WHERE code = 'framework_comp_def_select';

  RAISE NOTICE 'framework_comp_def_select sql_text -> CAST forma (% znaku).', length(v_sql);
END $$;

-- ── Verify (spust po behu) — ocekavej CAST(:filter_core_id AS int) ───────
-- SELECT sql_text FROM fw.data_set WHERE code = 'framework_comp_def_select';
