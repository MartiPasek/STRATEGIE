-- ============================================================================
-- Krok H+5 — INSERT nový artifact row 'vytvorit_edit_jadro_2'
-- ============================================================================
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw schema).
--
-- Post-INSERT akce:
--   1. Marti pošle Claude RETURNING id z této INSERTu
--   2. Claude updateuje header v scripts/executable_artifacts/vytvorit_edit_jadro_2.py
--      `# ID: TBD` → `# ID: <vrácený_id>`
--   3. Commit + push + cloud deploy
--   4. Klik "Ano, vygeneruj" v UI dialog (DesignFwForm empty_container)
--      → POST /sandbox/execute/vytvorit_edit_jadro_2 → auto-sync (file → DB
--      UPSERT) → sandbox subprocess execute → comp_def hierarchy created
--
-- POZN: Source je INSERT-uted jako '' (prazdny string) — auto-sync na první
-- execute call načte z disku + UPSERT (Marti's "git je truth, DB je cache").
-- ============================================================================

BEGIN;

INSERT INTO fw.executable_artifact (
    code, artifact_type, source, description
) VALUES (
    'vytvorit_edit_jadro_2',
    'python',
    '',  -- placeholder; auto-sync z disku na first execute call
    'Krok H+5 (26.5.2026): Auto-generate comp_def hierarchy '
    'pro drafted edit core (form root + main panel + per-column inputs). '
    'Spousteno z DesignFwForm empty_container dialog. '
    'File: scripts/executable_artifacts/vytvorit_edit_jadro_2.py'
)
RETURNING id, code, artifact_type, LENGTH(source) AS source_chars, updated_at;

COMMIT;

-- Po INSERT — pošli mi vrácený id (např. id=2).
-- Updateuju header file + commit. Pak Marti deploy + smoke test.
