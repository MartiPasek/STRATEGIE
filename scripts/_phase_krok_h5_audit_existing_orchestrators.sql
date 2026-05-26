-- ============================================================================
-- Krok H+5 audit — existing fw.executable_artifact orchestrators
-- ============================================================================
-- Marti 26.5.2026 odpoledne: pred zalozenim 'vytvorit_edit_jadro_2' musime
-- vedet co tam je z Krok F/G (puvodni orchestrator chain — beze zmeny).
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw schema).
-- ============================================================================

-- ── Step 1: schema fw.executable_artifact ────────────────────────────────
SELECT '=== Step 1: fw.executable_artifact REAL columns ===' AS section;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'executable_artifact'
ORDER BY ordinal_position;


-- ── Step 2: existing rows (metadata, NE code body) ──────────────────────
SELECT '=== Step 2: Existing orchestrator rows (metadata) ===' AS section;

SELECT id, code, version, description,
       LENGTH(script_body) AS script_chars,
       status, is_system,
       created_at, updated_at
FROM fw.executable_artifact
ORDER BY id;
-- Posli mi vystup — budu vedet ktery row je Krok F/G/G+/G++ a jeho id


-- ── Step 3: existing fw.core #55 (Marti's screenshot empty container) ────
SELECT '=== Step 3: fw.core #55 + chain (kontext pre H+5) ===' AS section;

SELECT c.id AS core_id, c.code, c.label, c.layout_type,
       c.template_id, c.tenant_visibility, c.status,
       COUNT(cd.id) AS comp_def_count
FROM fw.core c
LEFT JOIN fw.comp_def cd ON cd.core_id = c.id AND cd.parent_comp_def_id IS NULL
WHERE c.id = 55
GROUP BY c.id;
-- Expected: comp_def_count=0 (drafted = no root component)


-- ── Step 4: ktere data_source_op pointuji na core 55 ─────────────────────
SELECT '=== Step 4: data_source_op routing na core 55 ===' AS section;

SELECT op.id, op.operation_kind, op.variant_code,
       op.data_source_id, op.data_set_id,
       op.description
FROM fw.data_source_op op
WHERE op.id = 35  -- z screenshot "Editace: Operace data sourcu #35"
   OR EXISTS (
       SELECT 1 FROM fw.executable_artifact ea
       WHERE ea.script_body ILIKE '%55%'  -- vague — coreId v code body?
   );
-- Posli mi vystup — uvidim jak je ID 55 propojene s op + data_source chain
