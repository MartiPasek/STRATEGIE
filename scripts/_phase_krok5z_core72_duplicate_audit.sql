-- ============================================================================
-- Krok 5.Z — Core 72 duplicate comp_def audit (PŘED cleanupem)
-- ============================================================================
-- 31.5.2026, po LIVE multi-table save (15/15 bindingů aktivních).
-- Marti: "Ukladani chodi WEB I FIRMA TEXT, pokracuj."
--
-- Cil: zjistit duplicitni leaf comp_defy v core 72 (zejmena fld_test_firma_*),
-- ktere maji stejny field name. Save flow `_field_layout_map` je keyed by name
-- (last-wins) -> nedeterministicky save pokud existuji 2+ comp_defy se stejnym
-- jmenem. Po LIVE save vime ze FirmaText/FirmaWeb (s column_name) maji binding;
-- duplikaty BEZ column_name binding nedostaly.
--
-- READ-ONLY audit. Nic nemaze. Spusti Marti v DBeaveru (Marti-AI session).
-- ============================================================================

-- ── A) Vsechny leaf comp_defy core 72 (mimo containery) + binding stav ──────
SELECT
    cd.id                                           AS comp_def_id,
    cd.name,
    cd.layout->>'column_name'                       AS column_name,
    cd.layout->>'caption'                           AS caption,
    cd.parent_comp_def_id,
    cd.type_id,
    ct.code                                          AS type_code,
    cd.is_active,
    cd.sort_order,
    -- binding stav: kterou tabulku ten field uklada?
    cd.layout->'save'->>'table'                      AS save_table,
    cd.layout->'save'->>'column'                     AS save_column,
    (cd.layout->'save'->>'readonly')                 AS save_readonly,
    (cd.layout ? 'save')                             AS has_binding
FROM fw.comp_def cd
LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE cd.core_id = 72
  AND cd.is_active = TRUE
  AND ct.code NOT IN ('panel','groupbox','pagecontrol','tabsheet','grid_modern')
ORDER BY
    COALESCE(cd.layout->>'column_name', cd.name),
    cd.id;

-- ── B) DUPLIKATY: stejny effective field name vicekrat ──────────────────────
-- effective name = column_name pokud existuje, jinak name.
-- Tohle jsou kandidati na smazani (ponechat ten s column_name + binding).
WITH leaf AS (
    SELECT
        cd.id,
        cd.name,
        cd.layout->>'column_name'                    AS column_name,
        COALESCE(cd.layout->>'column_name', cd.name) AS eff_name,
        (cd.layout ? 'save')                         AS has_binding,
        cd.sort_order,
        cd.parent_comp_def_id
    FROM fw.comp_def cd
    LEFT JOIN fw.comp_type ct ON ct.id = cd.type_id
    WHERE cd.core_id = 72
      AND cd.is_active = TRUE
      AND ct.code NOT IN ('panel','groupbox','pagecontrol','tabsheet','grid_modern')
)
SELECT
    eff_name,
    COUNT(*)                                          AS pocet,
    array_agg(id ORDER BY has_binding DESC, id)       AS comp_def_ids,
    array_agg(
        id::text || CASE WHEN has_binding THEN ' [binding]' ELSE ' [BEZ]' END
        ORDER BY has_binding DESC, id
    )                                                 AS detail
FROM leaf
GROUP BY eff_name
HAVING COUNT(*) > 1
ORDER BY eff_name;

-- ============================================================================
-- Interpretace B:
--   pocet=1  -> ok, zadny duplikat
--   pocet>1  -> duplikat. Ponechat id s [binding], smazat ostatni [BEZ].
-- Po auditu pripravim cileny DELETE jen na konkretni [BEZ] id (idempotentni).
-- ============================================================================
