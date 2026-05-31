-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — hard delete core 71 "TEST detail #40011" (test prehled grid)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "Ted smazat ten prehled 71." Po parametrizaci data_set 46
-- (:ID) uz core 71 grid stejne vraci 0 radku (sdileny select op). Test
-- scaffold -> pryc, vcetne uzlu ve strome.
--
-- Footprint (z diagnostiky):
--   comp_def:        287 (grid_crm_kontakt_detail_test, root, ds 58) — 1 row
--   menu_node:       66 "TEST detail #40011" (leaf, parent_id 56)
--   data_source_op:  zadne s core_id=71 (neblokuje)
--   context_menu_item: zadne (neblokuje)
--
-- POZOR: data_source 58 (crm_kontakt_detail_test) je SDILENY s formou
-- core 72 (po Krok 5.Z parametrizaci :ID). NEMAZAT ds 58 ani ds 52/53.
-- Mazeme jen comp_def + menu_node + core.
--
-- FK: comp_def_prop CASCADE (auto), menu_node.core_id -> core SET NULL
-- (proto menu_node mazeme explicitne, jinak by zustal orphan tree node).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1) Tree node (explicitne — FK SET NULL by ho jinak nechal orphan)
DELETE FROM fw.menu_node WHERE id = 66;
-- ocekavej: DELETE 1

-- 2) comp_def (jediny root grid; comp_def_prop CASCADE)
DELETE FROM fw.comp_def WHERE core_id = 71;
-- ocekavej: DELETE 1 (id 287)

-- 3) core
DELETE FROM fw.core WHERE id = 71;
-- ocekavej: DELETE 1

COMMIT;

-- Verifikace:
-- SELECT count(*) FROM fw.comp_def WHERE core_id = 71;   -- 0
-- SELECT count(*) FROM fw.core WHERE id = 71;            -- 0
-- SELECT count(*) FROM fw.menu_node WHERE id = 66;       -- 0
-- ds 58 zustava (forma 72):
-- SELECT id, code FROM fw.data_source WHERE id = 58;     -- crm_kontakt_detail_test
