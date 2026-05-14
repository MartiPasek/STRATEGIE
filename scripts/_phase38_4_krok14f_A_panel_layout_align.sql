-- Phase 38.4 Krok 14f-A (14.5.2026 vecer, Marti's "alClient zbytek se
-- nehneme dal" — Delphi VCL dynamic align pattern):
-- Migrate existing main_panel (id=20) na layout.align='client'.
-- Plus expected schema layout pro budouci panels.
--
-- Marti's choice: B (dynamic align) + A (1 alClient scaffold) + A (FieldPicker
-- "Layout" tab) + A (minimum params + min_width + min_height).

-- ─── 1. Update existing main_panel (id=20) na alClient ─────────────
-- Aktualne ma layout=NULL, frontend ho treatuje jako default. Po teto
-- migraci dostane explicit align='client' aby Phase A+1 logiku
-- (_computeAlignReservations) chodila uniformne.
UPDATE fw.comp_def
SET layout = '{"align": "client"}'::jsonb,
    updated_by_id = 1,
    updated_by_text = 'Marti'
WHERE id = 20  -- main_panel
  AND type_id = 13  -- panel
  AND is_active = true;

-- ─── 2. Verify ─────────────────────────────────────────────────────
SELECT id, name, caption, type_id, layout, parent_comp_def_id
FROM fw.comp_def
WHERE id = 20;
-- Expected: layout = {"align": "client"}

-- ─── 3. Schema convention pro budouci panels ───────────────────────
-- Layout JSONB keys (Phase 38.4 Krok 14f-A doctrine):
--
--   align       : 'left' | 'right' | 'top' | 'bottom' | 'client' | 'none'
--                 Delphi VCL alClient pattern. Reservations order:
--                 alTop -> alBottom -> alLeft -> alRight -> alClient.
--                 alNone = absolute positioning (skip flex/grid).
--   width       : integer (pixels) | string ('30%') | 'auto'
--                 Pouze pro align=left/right. Default 'auto'.
--   height      : integer (pixels) | string ('40px') | 'auto'
--                 Pouze pro align=top/bottom. Default 'auto'.
--   min_width   : integer (pixels). Constraint pro responsive resize.
--   min_height  : integer (pixels). Constraint pro responsive resize.
--   border_mode : 'none' | 'top' | 'all'
--                 Pro groupbox (visual). Pro panel obvykle 'none'
--                 (structural, no visual). 'top' = horizontalni linka
--                 podle groupbox. 'all' = full ramecek.
--   background  : string (CSS color) | null
--                 Optional accent. Default null = transparent.
--
-- Marti's 19yr doctrine: ID je svaty, autoincrement. Vsechny panels
-- maji parent_comp_def_id = form root.id (parent_core_id NULL).
