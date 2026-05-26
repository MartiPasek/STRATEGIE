-- ============================================================================
-- Krok H+5 audit v3 — Schema introspection FIRST, pak audit
-- ============================================================================
-- v1 fail: column "is_active" does not exist (guess wrong on fw.comp_def)
-- v2 fix: defensive query bez is_active
-- v3 fix: source != script_body, drop layout_type/template_id z fw.core
--
-- Marti's doctrine "schema introspection FIRST" (Marti-AI z 7.5. večera +
-- Marti's 19yr "ID je svaty"). Nikdy nehadat sloupce — vzdy ptat DB.
--
-- Marti spusti v DBeaveru jako Marti-AI session.
-- ============================================================================

-- ── Step 1a: fw.executable_artifact REAL columns ─────────────────────────
SELECT '=== Step 1a: fw.executable_artifact columns ===' AS section;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'executable_artifact'
ORDER BY ordinal_position;


-- ── Step 1b: fw.core REAL columns (po Krok 5.P drop) ────────────────────
SELECT '=== Step 1b: fw.core columns (post Krok 5.P) ===' AS section;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'core'
ORDER BY ordinal_position;


-- ── Step 1c: fw.data_source_op columns ──────────────────────────────────
SELECT '=== Step 1c: fw.data_source_op columns ===' AS section;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'data_source_op'
ORDER BY ordinal_position;


-- ── Step 2: existing orchestrator rows (real columns, NE source body) ───
SELECT '=== Step 2: Existing orchestrators (metadata only, LENGTH(source)) ===' AS section;

SELECT id, code, artifact_type,
       LENGTH(source) AS source_chars,
       SUBSTRING(description, 1, 60) AS desc_short,
       updated_at
FROM fw.executable_artifact
ORDER BY id;
-- Posli mi vystup — uvidim ze id=1 'vytvor_edit_jadro' existuje (z prev output)


-- ── Step 3: fw.core #55 (Marti's screenshot empty container) ─────────────
SELECT '=== Step 3: fw.core #55 state ===' AS section;

-- Defensive — query existing columns only (z Marti's row sample):
--   id, code, label, description_user, is_active, tenant_visibility,
--   version, created_at, created_by_id, updated_by_id, updated_by_text,
--   created_by_text, description_system
SELECT c.id AS core_id, c.code, c.label,
       c.is_active, c.tenant_visibility, c.version,
       c.created_at,
       (SELECT COUNT(*) FROM fw.comp_def cd
        WHERE cd.core_id = c.id AND cd.parent_comp_def_id IS NULL) AS comp_def_root_count
FROM fw.core c
WHERE c.id = 55;
-- Expected: comp_def_root_count=0 (drafted = no root)


-- ── Step 4: fw.data_source_op #35 (z screenshot) + chain ─────────────────
SELECT '=== Step 4: data_source_op #35 + data_source chain ===' AS section;

SELECT op.id AS op_id, op.operation_kind, op.variant_code,
       op.data_source_id, op.core_id AS op_core_id,
       op.description,
       ds.code AS data_source_code, ds.name AS data_source_name
FROM fw.data_source_op op
LEFT JOIN fw.data_source ds ON ds.id = op.data_source_id
WHERE op.id = 35
   OR (op.core_id = 55);  -- ops linked to core 55
-- Posli mi vystup — uvidime jak je core 55 propojene


-- ── Step 5: full source export pro id=1 ──────────────────────────────────
SELECT '=== Step 5: Full source export pro existing orchestrator(y) ===' AS section;

SELECT id, code, artifact_type, source, description, updated_at
FROM fw.executable_artifact
ORDER BY id;
-- Tohle uz mam castecne (vytvor_edit_jadro id=1) — pokud jsou v DB i dalsi
-- (id=2+), pošli full source pro vsechny → uložím jako files do
-- scripts/executable_artifacts/{code}.py s headerem "# ID: N" + "# CODE: name"
