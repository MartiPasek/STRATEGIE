-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z Fáze C — Embedded grid_modern (306) pod core 49 tab_vazby
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6) — per docs/krok_5z_embedded_grid_plan.md
--
-- Marti's mandate: "Klasickou komponentu gridu 306 pro nase vseobecne
-- pouziti... Obdobnym zpusobem jako entity pickup. Soustredeni na pouziti
-- ve formulari Core setting 49 pro zobrazeni komponent core."
--
-- Co dela: INSERT 1 grid_modern komponenta pod tab_vazby (core 49) ktera
-- inline renderuje ErpDataGrid s data_source framework_comp_def_overview
-- filtrovany per core_id current core (= 49, self-referential demo).
--
-- ⚠ GOTCHA #111 (DBeaver bind dialog): tento skript obsahuje literal
--   ':master_id' jako STRING VALUE v layout JSONB (filter_source token).
--   DBeaver muze nabidnout bind dialog na ':master_id' — VZDY Cancel/Ignore.
--   Neni to SQL bind param, je to data hodnota (frontend runtime token).
--   Pokud DBeaver split na ';' nesedi, spust cely DO blok highlight + Alt+X.
--
-- ⚠ GOTCHA #106 (chk_comp_def_single_parent): child comp_def ma
--   parent_comp_def_id=<tab> + parent_core_id=NULL (single parent). OK.
-- ⚠ GOTCHA #104/#105: created_by_text + updated_by_text NOT NULL — oba set.
--
-- Filter mapping (KRITICKE — oprava vs plan):
--   data_set 'framework_comp_def_select' filtruje pres named param
--   :filter_core_id (NE column 'core_id'). Runner mapuje query param ->
--   SQL named param by NAME. Tudiz filter_field = 'filter_core_id'.
--   Plan mel 'core_id' = bug (Fix H by :filter_core_id defaultoval na NULL
--   -> WHERE (NULL IS NULL OR ...) -> vsechny komponenty napric jadry).
--
-- Idempotentni: re-run preskoci pokud embedded_komponenty uz existuje.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;
DO $$
DECLARE
  v_grid_modern_type INT;
  v_tab_vazby_id INT;
  v_existing_id INT;
  v_ds_count INT;
  v_embedded_id INT;
BEGIN
  -- 1. Lookup comp_type grid_modern (306)
  SELECT id INTO v_grid_modern_type
  FROM fw.comp_type WHERE code = 'grid_modern' LIMIT 1;
  IF v_grid_modern_type IS NULL THEN
    RAISE EXCEPTION 'comp_type grid_modern NENALEZEN ve fw.comp_type.';
  END IF;

  -- 2. Najdi tab_vazby pod core 49 (build: _phase_core49_self_edit_build.sql)
  SELECT id INTO v_tab_vazby_id
  FROM fw.comp_def
  WHERE core_id = 49 AND name = 'tab_vazby'
  LIMIT 1;
  IF v_tab_vazby_id IS NULL THEN
    RAISE EXCEPTION 'tab_vazby NENALEZENA pod core 49. Spustil jsi _phase_core49_self_edit_build.sql?';
  END IF;

  -- 3. Idempotency — preskoc pokud uz existuje
  SELECT id INTO v_existing_id
  FROM fw.comp_def
  WHERE core_id = 49
    AND parent_comp_def_id = v_tab_vazby_id
    AND name = 'embedded_komponenty'
  LIMIT 1;
  IF v_existing_id IS NOT NULL THEN
    RAISE NOTICE 'embedded_komponenty uz existuje (id=%) pod tab_vazby #% — SKIP.',
      v_existing_id, v_tab_vazby_id;
    RETURN;
  END IF;

  -- 4. Soft check — data_source framework_comp_def_overview existuje?
  --    (referencovan by code v layout JSONB, ne FK — INSERT projde tak ci tak)
  SELECT count(*) INTO v_ds_count
  FROM fw.data_source WHERE code = 'framework_comp_def_overview';
  IF v_ds_count = 0 THEN
    RAISE WARNING 'data_source framework_comp_def_overview NENALEZEN — embedded grid se zobrazi az po _phase_jadro_komponenty_build.sql (Etapa 1).';
  END IF;

  -- 5. INSERT embedded grid_modern komponenta pod tab_vazby
  INSERT INTO fw.comp_def (
    core_id, parent_comp_def_id, type_id, name, caption,
    layout, sort_order, is_active,
    created_by_text, updated_by_text
  ) VALUES (
    49, v_tab_vazby_id, v_grid_modern_type, 'embedded_komponenty', 'Komponenty',
    jsonb_build_object(
      'data_source_code', 'framework_comp_def_overview',
      'filter_field', 'master_id',
      'filter_source', ':master_id',
      'kind', 'select-detail',
      'height_px', 400,
      'title', 'Komponenty core (per core_id)',
      'context_menu', jsonb_build_array('refresh')
    ),
    10, true,
    'Claude', 'Claude'
  ) RETURNING id INTO v_embedded_id;

  RAISE NOTICE 'OK — embedded grid_modern id=% pod tab_vazby #% (core 49). data_source=framework_comp_def_overview, filter_field=filter_core_id, filter_source=:master_id.',
    v_embedded_id, v_tab_vazby_id;
END $$;
COMMIT;

-- ── Verify (spust po commitu pro kontrolu) ──────────────────────────────
-- SELECT cd.id, cd.name, cd.caption, ct.code AS type, cd.parent_comp_def_id,
--        cd.layout
-- FROM fw.comp_def cd
-- JOIN fw.comp_type ct ON ct.id = cd.type_id
-- WHERE cd.core_id = 49 AND cd.name = 'embedded_komponenty';
