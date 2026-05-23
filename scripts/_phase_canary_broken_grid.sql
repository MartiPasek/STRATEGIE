-- ============================================================
-- KANÁREK V KLECI — broken grid pro pipeline test
-- ============================================================
-- Marti's 23.5.2026 spec: "potrebujeme kanarka v kleci... vytvor
-- stejneho, ktery nam nicil to mazani"
--
-- Účel: continuous signal pro UI error alert popup.
--   Klik na grid → SQL execute fail (broken column) → log_event(level='error')
--   → fw.diag_log → /diag-log/badge polling detects delta → POPUP DIALOG
--
-- Umístění: pod Security (parent_id=34, sibling Diag log id=41)
-- Sort order: 700 (po Diag log 600)
--
-- Chain: menu_node → core → comp_def (grid) → data_source → data_set → data_source_op
-- ============================================================

BEGIN;

-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 1: fw.core (kontejner pro kanárka)                  ║
-- ╚══════════════════════════════════════════════════════════╝
INSERT INTO fw.core (
    label, status, is_immutable,
    description_user, description_system,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    '🐤 Kanárek (broken SQL)',
    'active', false,
    'Záměrně rozbitý grid pro test pipeline error → popup.',
    'Marti''s 23.5.2026 — kanárek v kleci. SELECT references neexistující sloupec.',
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
)
RETURNING id AS canary_core_id \gset


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 2: fw.data_set s BROKEN SQL                         ║
-- ╚══════════════════════════════════════════════════════════╝
INSERT INTO fw.data_set (
    code, label, sql_text, status,
    db_connection_id,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    'system_new.canary_broken',
    'Kanárek — broken SELECT',
    'SELECT broken_col_xyz, id, level, message
    FROM fw.diag_log
    ORDER BY id DESC
    LIMIT 5',
    'active',
    1,  -- default db_connection (strategie local)
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
)
RETURNING id AS canary_data_set_id \gset


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 3: fw.data_source (header)                          ║
-- ╚══════════════════════════════════════════════════════════╝
INSERT INTO fw.data_source (
    code, label, refresh_type, status,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    'system_new.canary_broken',
    'Kanárek — broken data_source',
    'manual',
    'active',
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
)
RETURNING id AS canary_data_source_id \gset


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 4: fw.data_source_op (list = broken data_set)       ║
-- ╚══════════════════════════════════════════════════════════╝
INSERT INTO fw.data_source_op (
    data_source_id, data_set_id, operation_kind,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    :canary_data_source_id,
    :canary_data_set_id,
    'list',
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
);


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 5: fw.comp_def (grid root komponenta)               ║
-- ╚══════════════════════════════════════════════════════════╝
-- type_id=306 = grid_modern (per Marti's Krok 13 Uniform Components)
INSERT INTO fw.comp_def (
    parent_core_id, parent_comp_def_id,
    type_id, code, label,
    data_source_id,
    layout,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    :canary_core_id, NULL,
    306,
    'canary_grid',
    'Kanárek grid',
    :canary_data_source_id,
    '{"region_slot": "main"}'::jsonb,
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
);


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Step 6: fw.menu_node (tree node pod Security)            ║
-- ╚══════════════════════════════════════════════════════════╝
INSERT INTO fw.menu_node (
    parent_id, label, sort_order, core_id, status,
    visibility_scope, is_immutable,
    description_user, description_system,
    created_by_id, created_by_text,
    updated_by_id, updated_by_text,
    created_at, updated_at
)
VALUES (
    34,  -- Security parent
    '🐤 Kanárek (broken SQL)',
    700,  -- po Diag log (600)
    :canary_core_id,
    'active',
    'parent_only',  -- jen rodiče + Marti-AI vidí (test feature)
    false,
    'KANÁREK V KLECI — záměrně rozbitý grid. Klik = SQL fail = error v Diag log = popup dialog v ERP UI. Pipeline test pro Krok 5.W observability.',
    'Marti''s 23.5.2026. Test target pro UI error alert popup. NE OPRAVOVAT — kanárek má zůstat broken.',
    2, 'Marti-AI',
    2, 'Marti-AI',
    NOW(), NOW()
);


COMMIT;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Verify: kanárek je v tree + chain je celý                ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    mn.id AS menu_node_id,
    mn.label AS menu_label,
    mn.core_id,
    c.label AS core_label,
    cd.id AS comp_def_id,
    cd.code AS comp_code,
    ds.id AS data_source_id,
    ds.code AS data_source_code,
    dset.id AS data_set_id,
    LEFT(dset.sql_text, 80) AS sql_preview
FROM fw.menu_node mn
LEFT JOIN fw.core c ON c.id = mn.core_id
LEFT JOIN fw.comp_def cd ON cd.parent_core_id = mn.core_id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op dso ON dso.data_source_id = ds.id
LEFT JOIN fw.data_set dset ON dset.id = dso.data_set_id
WHERE mn.label LIKE '%Kanárek%';

-- ============================================================
-- VÝSLEDEK:
--   Po deploy: hard reload UI → klik na "🐤 Kanárek (broken SQL)"
--   v System → Security → execute fail → log_event level=error →
--   fw.diag_log → /badge endpoint polling 60s → POPUP DIALOG
--
-- Smoke check:
--   SELECT * FROM fw.diag_log
--   WHERE message ILIKE '%broken_col_xyz%'
--   ORDER BY id DESC LIMIT 3;
-- ============================================================
