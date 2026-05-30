-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z Volba (2) — embedded grid filtruje podle EDITOVANEHO core
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti's finalni rozhodnuti (30.5.): "Cely tento specialni Core setting je
-- o (2) vzdycky" — embedded grid v zalozce Vazby ukazuje komponenty
-- EDITOVANEHO core (ne vlastniho core formu).
--
-- Frontend (design_forms.js _renderEmbeddedGridSection) resolvuje :master_id:
--   this.opts.rowId   (= PK editovaneho core z URL /fw-form/by-id/{coreId}/{rowId})
--   fallback this._spec.data.id
--
-- Tento UPDATE vrati filter_source na :master_id (pokud byl docasne prepnut
-- na :self_core_id Volbou B). Idempotentni — funguje at je hodnota cokoliv.
--
-- ⚠ GOTCHA #111 (DBeaver bind dialog): jsonb literal obsahuje ':master_id'.
--   DBeaver muze nabidnout bind dialog — VZDY Cancel/Ignore.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.comp_def
SET layout = jsonb_set(layout, '{filter_source}', '":master_id"'::jsonb)
WHERE core_id = 49
  AND name = 'embedded_komponenty';

COMMIT;

-- ── Verify (spust po commitu) — ocekavej filter_source = :master_id ──────
-- SELECT name, layout->>'filter_source' AS filter_source,
--        layout->>'filter_field' AS filter_field
-- FROM fw.comp_def WHERE core_id = 49 AND name = 'embedded_komponenty';
