-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z Volba B — embedded grid filtruje podle vlastniho core formu
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti's volba (30.5.): "Pro nas pripad B" — embedded grid v Core setting
-- formu ma vzdy ukazovat komponenty CORE k nemuz form patri (self-ref),
-- ne komponenty editovaneho row. Token :master_id -> :self_core_id.
--
-- Frontend (design_forms.js _renderEmbeddedGridSection) resolvuje:
--   :self_core_id -> this._spec.core.id  (= core 49 pro Core setting form)
--
-- Tento UPDATE prepne uz nasazenou embedded_komponenty komponentu
-- (seed _phase_krok5z_c ji vytvoril s :master_id). Idempotentni.
--
-- ⚠ GOTCHA #111 (DBeaver bind dialog): jsonb literal obsahuje ':self_core_id'.
--   DBeaver muze nabidnout bind dialog — VZDY Cancel/Ignore.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.comp_def
SET layout = jsonb_set(layout, '{filter_source}', '":self_core_id"'::jsonb)
WHERE core_id = 49
  AND name = 'embedded_komponenty';

COMMIT;

-- ── Verify (spust po commitu) — ocekavej filter_source = :self_core_id ────
-- SELECT name, layout->>'filter_source' AS filter_source,
--        layout->>'filter_field' AS filter_field
-- FROM fw.comp_def WHERE core_id = 49 AND name = 'embedded_komponenty';
