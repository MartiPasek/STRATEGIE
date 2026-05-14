-- Phase 38.4 Krok 14d-B (14.5.2026 večer, po Marti-AI consultation):
-- fw.comp_type INSERT nested_grid pro joined tables (sub-grid v form).
--
-- Marti-AI's Q3 decision: nový typ (b) — nested_grid v 300+ range.
-- Důvod (její vlastní slova): "grid_modern je full-page component
-- s vlastním toolbar, pagination, fetch lifecycle. Nested grid v formu
-- potřebuje jiné věci: parent_id context, polymorphic filter, save
-- coupling s parentem, žádnou vlastní pagination, compact render.
-- Reuse by znamenal přidávat speciální flagy do grid_modern dokud by
-- byl nečitelný. Nový typ je čistší. Přetrumfuji vlastní doktrínu
-- uniformity."
--
-- Marti-AI doctrine z 11.5. "Krok 13 NEW komponenty 300-349":
--   300 — container
--   301 — comp_hw
--   302 — form
--   303 — iframe
--   304 — TODO (free)
--
-- Next available id = 304 (nested_grid).

-- ─── 1. INSERT nested_grid ────────────────────────────────────
INSERT INTO fw.comp_type
  (id, centrala_id, code, label, kind, description,
   legacy_compat, renderer_hint, status, created_by_text)
VALUES
  (304, NULL, 'nested_grid', 'Nested Grid', 'container',
   'Sub-grid v form pro 1:N child rows (user_contacts emails/phones, '
   'user_aliases, atd.). Marti-AI''s Krok 14d Q3 — nový typ separate od '
   'grid_modern (full-page). Compact render, parent_id context, '
   'polymorphic filter, save coupling.',
   FALSE,           -- ne Centrála 1 compat (nový pattern)
   'nested_grid',   -- renderer hint pro frontend dispatch
   'active',        -- LIVE pro Krok 14d
   'Marti-AI');     -- design author (Q3 + Q5 doctrine)

-- ─── 2. Verify ────────────────────────────────────────────────
SELECT id, code, label, kind, status, renderer_hint, description
FROM fw.comp_type
WHERE id = 304;

-- ─── 3. Sanity check next available id v 300+ range ──────────
SELECT id, code, label, status
FROM fw.comp_type
WHERE id BETWEEN 300 AND 349
ORDER BY id;
