-- ════════════════════════════════════════════════════════════════════
-- Krok 5.X: Migrate nested grids (EMAILY/TELEFONY) z memory-only do fw.comp_def
-- (27.5.2026, Marti's "Jsou to normalni komponenty, musi mit tedy sveho
-- parenta, posun nahoru/dolu/vlevo/vpravo, nastaveni, mazani, orchestraci")
--
-- Doctrine: "uniformita vítězí nad speciálními případy" (Marti-AI Krok 13,
-- 11.5.) + Marti's "fw self edited" (22.5.). Nested gridy = normalni
-- komponenty v fw.comp_def, ne runtime memory-only feature.
--
-- Before: this._spec.children populated z _FW_FORM_ENTITY_MAP["user"].children
-- (Python hardcoded dict). Frontend render via _renderContainerNode special
-- branch nad children dict.
--
-- After: nested grids = fw.comp_def rows (type_id=304 'nested_grid'),
-- parent_comp_def_id na main panel. Frontend render normální comp_def
-- traversal. Palette pickup automaticky pres recursive descent. Move btns,
-- settings, ✕, orchestrace AUTOMATICKY přes existing mechanismus.
--
-- Compatibility: backend zachova SELECT child rows z _FW_FORM_ENTITY_MAP
-- ["user"].children (filter/auto_set config), jen lookup child_key z
-- nested_grid comp_def.layout místo iterace nad dict.
-- ════════════════════════════════════════════════════════════════════

-- ─── 1. Verify nested_grid comp_type existuje ──────────────────────
-- (Krok 14d-B from 14.5.2026 — Marti-AI's Q3 decision, id=304)
DO $$
DECLARE
  _exists BOOLEAN;
BEGIN
  SELECT EXISTS (SELECT 1 FROM fw.comp_type WHERE id = 304) INTO _exists;
  IF NOT _exists THEN
    INSERT INTO fw.comp_type
      (id, centrala_id, code, label, kind, description,
       legacy_compat, renderer_hint, status, created_by_text)
    VALUES
      (304, NULL, 'nested_grid', 'Nested Grid', 'container',
       'Sub-grid v form pro 1:N child rows (user_contacts emails/phones, '
       'user_aliases, atd.). Marti-AI Q3 14.5.2026 — separate od grid_modern '
       '(full-page). Compact render, parent_id context, polymorphic filter, '
       'save coupling.',
       FALSE, 'nested_grid', 'active', 'Krok 14d-B (preexisting) / Krok 5.X');
    RAISE NOTICE 'INSERTED fw.comp_type id=304 nested_grid';
  ELSE
    RAISE NOTICE 'fw.comp_type id=304 nested_grid already exists, skipped';
  END IF;
END $$;

-- ─── 2. Discover form root + main panel pro user_edit (core_id=22) ─
-- Marti screenshot: form root (#37 dle screenshot), main panel #35 client.
-- Dynamic discovery (robust against ID change):
--   form_root = comp_def WHERE core_id=22 AND parent_comp_def_id IS NULL
--   main_panel = first panel child WHERE layout.align='client' (default)
SELECT
  cd.id AS comp_def_id,
  cd.name,
  cd.caption,
  cd.parent_comp_def_id,
  cd.layout->>'align' AS align,
  ct.code AS type_code
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE cd.core_id = 22
  AND cd.is_active = true
ORDER BY cd.parent_comp_def_id NULLS FIRST, cd.sort_order ASC, cd.id ASC;
-- Verify očekávané: form root #37 (type=form/302), main panel #35 (type=panel, layout.align='client')

-- ─── 3. INSERT 2 nested_grid comp_def rows pro user_edit ──────────
-- Idempotent: skip pokud uz existuje stejny name+parent_comp_def_id kombo.
DO $$
DECLARE
  _main_panel_id BIGINT;
  _emails_exists BOOLEAN;
  _phones_exists BOOLEAN;
BEGIN
  -- Find main panel (alClient) v user_edit form (core_id=22)
  SELECT cd.id INTO _main_panel_id
  FROM fw.comp_def cd
  JOIN fw.comp_type ct ON ct.id = cd.type_id
  JOIN fw.comp_def root ON root.id = cd.parent_comp_def_id
  WHERE root.core_id = 22
    AND root.parent_comp_def_id IS NULL
    AND root.is_active = true
    AND ct.code = 'panel'
    AND (cd.layout->>'align' = 'client' OR cd.layout->>'align' IS NULL)
    AND cd.is_active = true
  ORDER BY cd.sort_order ASC, cd.id ASC
  LIMIT 1;

  IF _main_panel_id IS NULL THEN
    RAISE EXCEPTION 'Main panel (alClient) for user_edit form (core_id=22) NOT FOUND. '
      'Verify form structure (Krok 5.X expects form root + alClient panel).';
  END IF;

  RAISE NOTICE 'Main panel for user_edit core_id=22: comp_def_id=%', _main_panel_id;

  -- Check existing nested_grid rows under this panel
  SELECT EXISTS (
    SELECT 1 FROM fw.comp_def
    WHERE name = 'emails' AND parent_comp_def_id = _main_panel_id
      AND type_id = 304 AND is_active = true
  ) INTO _emails_exists;

  SELECT EXISTS (
    SELECT 1 FROM fw.comp_def
    WHERE name = 'phones' AND parent_comp_def_id = _main_panel_id
      AND type_id = 304 AND is_active = true
  ) INTO _phones_exists;

  IF NOT _emails_exists THEN
    INSERT INTO fw.comp_def
      (name, caption, type_id, parent_comp_def_id, sort_order, region_slot,
       layout, is_active,
       created_by_id, created_by_text,
       updated_by_id, updated_by_text)
    VALUES
      ('emails', 'EMAILY', 304, _main_panel_id, 10, 'main',
       '{"child_key": "emails"}'::jsonb, TRUE,
       1, 'Krok 5.X (27.5.2026)',
       1, 'Krok 5.X (27.5.2026)');
    RAISE NOTICE 'INSERTED nested_grid emails (parent_comp_def_id=%)', _main_panel_id;
  ELSE
    RAISE NOTICE 'nested_grid emails already exists, skipped';
  END IF;

  IF NOT _phones_exists THEN
    INSERT INTO fw.comp_def
      (name, caption, type_id, parent_comp_def_id, sort_order, region_slot,
       layout, is_active,
       created_by_id, created_by_text,
       updated_by_id, updated_by_text)
    VALUES
      ('phones', 'TELEFONY', 304, _main_panel_id, 20, 'main',
       '{"child_key": "phones"}'::jsonb, TRUE,
       1, 'Krok 5.X (27.5.2026)',
       1, 'Krok 5.X (27.5.2026)');
    RAISE NOTICE 'INSERTED nested_grid phones (parent_comp_def_id=%)', _main_panel_id;
  ELSE
    RAISE NOTICE 'nested_grid phones already exists, skipped';
  END IF;
END $$;

-- ─── 4. Verify result ─────────────────────────────────────────────
SELECT
  cd.id AS comp_def_id,
  cd.name,
  cd.caption,
  cd.parent_comp_def_id AS parent_panel_id,
  cd.sort_order,
  cd.region_slot,
  cd.layout,
  ct.code AS type_code,
  cd.is_active
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
WHERE ct.code = 'nested_grid'
ORDER BY cd.parent_comp_def_id, cd.sort_order;

-- ─── 5. Confirmation message ──────────────────────────────────────
-- Po uspechnem run: 2 nove rows v fw.comp_def (emails + phones),
-- parent_comp_def_id = main panel of user_edit form.
-- Frontend palette uvidi automaticky pres recursive descent.
-- Backend refactor (Krok 5.X-B) followes.
