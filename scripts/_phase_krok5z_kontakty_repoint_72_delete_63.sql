-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — Kontakty (core 62) re-point detail form 63 -> 72 + hard delete 63
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "na prehled Kontakty id_core = 62 napojit detail form
-- id_core = 72. Momentalne je tam napojeny detail id 63, ktery musime
-- vcetne vsech komponent hard delete."
--
-- Kontakty prehled = core 62, root grid nad data_source 51 (crm_kontakty).
-- Edit/insert akce gridu se resolvuji z fw.data_source_op WHERE
-- data_source_id = 51 (viz router.py grid_actions). Momentalne:
--   op 56  edit   -> core 63
--   op 57  insert -> core 63
--   op 55  select -> NULL
-- Re-point obou (edit+insert) na core 72 ("TEST detail #40011").
--
-- FK analyza (information_schema):
--   comp_def_prop.komponenta_id -> comp_def   CASCADE   (auto pri delete comp_def)
--   comp_def.parent_comp_def_id -> comp_def   NO ACTION (mazat deti->rodice)
--   data_source_op.core_id      -> core       NO ACTION (vycisteno re-pointem)
--   context_menu_item.core_id   -> core       RESTRICT  (zadne rows na 63 -> OK)
--   menu_node.core_id           -> core       SET NULL  (auto)
--
-- POZOR: data_source 52 (akce_detail) + 53 (osoby_detail) jsou SDILENE s
-- core 72 (nested gridy). NEMAZAT je — mazeme jen comp_defy core 63.
--
-- ds 55 (crm_kontakt_edit) = data_source form root 258 (core 63). Po smazani
-- core 63 zustane orphaned. Cleanup ds 55 + jeho ops/data_set NENI v tomto
-- skriptu (volitelne, viz konec). erp_grid_layouts 'core_63' taktez orphan
-- (string key, bez FK) — neblokuje, volitelny cleanup.
--
-- DRY-RUN: nahrad COMMIT za ROLLBACK pro test (zkontroluj row counts v outputu).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1) Re-point Kontakty (ds 51) edit + insert na detail form core 72.
--    Zaroven tim zmizi jedine data_source_op odkazy na core 63 (NO ACTION FK
--    -> jinak by blokovaly delete core 63).
UPDATE fw.data_source_op
SET core_id = 72
WHERE data_source_id = 51
  AND operation_kind IN ('edit', 'insert');
-- ocekavej: UPDATE 2

-- 2) Hard delete vsech comp_defu core 63, deti->rodice (explicitne po vrstvach,
--    bez DO/$$ kvuli DBeaver delimiter gotcha). comp_def_prop CASCADE auto.
--    Hierarchie z diagnostiky: root 258 -> panely 266/270/274/279 + gridy
--    259/260 -> fieldy pod panely.
--
-- 2a) depth 2: fieldy pod panely (parent = panel)
DELETE FROM fw.comp_def
WHERE core_id = 63
  AND parent_comp_def_id IN (266, 270, 274, 279);
-- ocekavej: DELETE 15 (267-269, 271-273, 275-278, 280-284)

-- 2b) depth 1: gridy + panely pod form rootem 258
DELETE FROM fw.comp_def
WHERE core_id = 63
  AND parent_comp_def_id = 258;
-- ocekavej: DELETE 6 (259, 260, 266, 270, 274, 279)

-- 2c) depth 0: form root
DELETE FROM fw.comp_def
WHERE core_id = 63
  AND parent_comp_def_id IS NULL;
-- ocekavej: DELETE 1 (258)
-- celkem 22 comp_defu smazano

-- 3) Delete core 63 (data_source_op vycisteno krokem 1, context_menu_item
--    zadne, menu_node SET NULL auto).
DELETE FROM fw.core WHERE id = 63;
-- ocekavej: DELETE 1

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFIKACE (spust po commitu):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT id, data_source_id, operation_kind, core_id
--   FROM fw.data_source_op WHERE data_source_id = 51 ORDER BY operation_kind;
--   -> edit + insert maji core_id = 72, select NULL
-- SELECT count(*) FROM fw.comp_def WHERE core_id = 63;   -> 0
-- SELECT count(*) FROM fw.core WHERE id = 63;            -> 0

-- ════════════════════════════════════════════════════════════════════════
-- VOLITELNY cleanup orphanu po smazani core 63 (spust SAMOSTATNE az overis,
-- ze ds 55 nikdo jiny nepouziva):
-- ════════════════════════════════════════════════════════════════════════
-- -- ds 55 (crm_kontakt_edit) — orphaned form data_source core 63:
-- SELECT id, name, code FROM fw.data_source WHERE id = 55;
-- SELECT id, operation_kind, data_set_id FROM fw.data_source_op WHERE data_source_id = 55;
-- -- erp_grid_layouts orphan (pokud existuje, bez FK, neblokuje):
-- -- DELETE FROM ... WHERE layout_key = 'core_63';   (over nazev tabulky)
