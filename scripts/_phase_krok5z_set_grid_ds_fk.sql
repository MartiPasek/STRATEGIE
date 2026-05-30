-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — embedded grid data_source_id FK (pro ulozeni/restore sestav)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- PROBLEM (Marti 30.5.): ukladani/restore sloupcu nested gridu nefunguje:
--   "ErpDataGrid: layoutKey expected 'core_<id>' OR 'ds_<id>', got: embedded_49_369"
-- Grid-layout system (datagrid.js _layoutApiBase + backend _parse_scope_key)
-- akceptuje JEN scope 'core_<id>' nebo 'ds_<id>'. Embedded grid byl 'embedded_..'.
--
-- FIX: embedded grid je bound na data_source -> layoutKey 'ds_<data_source_id>'
-- (konvence nested gridu, data_source_op_detail.js pouziva ds_44). Frontend
-- cte comp.data_source_id z comp_def -> potrebuje FK set.
--
-- Standalone Prehled Komponent (core 73) pouziva 'core_73' (page_render.js),
-- takze embedded grid 'ds_<id>' je SEPARATNI sestava — zadny konflikt.
--
-- Zadny ':' -> zadny DBeaver bind dialog. Plain UPDATE. NEZAPOMEN COMMIT.
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.comp_def
SET data_source_id = (
      SELECT id FROM fw.data_source
      WHERE code = 'framework_comp_def_overview' LIMIT 1
    )
WHERE core_id = 49 AND name = 'embedded_komponenty';

-- Over po commitu (ocekavej data_source_id = id framework_comp_def_overview):
-- SELECT cd.name, cd.data_source_id, ds.code
-- FROM fw.comp_def cd LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
-- WHERE cd.core_id = 49 AND cd.name = 'embedded_komponenty';
