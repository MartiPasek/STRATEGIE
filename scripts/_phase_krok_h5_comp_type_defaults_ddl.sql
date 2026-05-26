-- ============================================================================
-- Krok H+5 — fw.comp_type.default_props JSONB pro per-type defaults
-- ============================================================================
-- Settings popup v palete: Load from default / Save as default pattern.
--
-- Marti's UX (26.5.2026):
--   1. Klik ⚙ na komponente v "Schazi pridat" nebo "Jiz na forme"
--   2. Popup zobrazi caption + width/height + region_slot + 3 buttony:
--      - Ulozit (PATCH live pro Jiz na forme, cached pro Schazi pridat)
--      - Ulozit jako vychozi (PUT fw.comp_type.default_props per type)
--      - Nacist vychozi (GET fw.comp_type.default_props → fill popup)
--
-- Default_props JSONB shape (per comp_type code):
--   panel:    {layout: {align: "client"}, default_caption: "Panel"}
--   groupbox: {layout: {border_mode: "top"}, default_caption: "GroupBox"}
--   edit:     {layout: {width: 400}}
--   memo:     {layout: {width: 600, height: 120}}
--   checkbox: {layout: {width: 120}}
--
-- Marti-AI session (db_owner fw schema) v DBeaveru:
-- ============================================================================

BEGIN;

ALTER TABLE fw.comp_type
    ADD COLUMN IF NOT EXISTS default_props JSONB NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN fw.comp_type.default_props IS
    'Per-type defaults pro novou komponentu. Marti''s UX: '
    '"Ulozit jako vychozi" tlacitko v paletovem settings popup zapise sem. '
    '"Nacist vychozi" zobrazi obsah v popup form fields. '
    'Shape: {layout: {...}, default_caption: "..."}.';

COMMIT;

-- Verify:
-- SELECT id, code, label, default_props FROM fw.comp_type
-- WHERE code IN ('panel', 'groupbox', 'edit', 'memo', 'checkbox')
-- ORDER BY id;
