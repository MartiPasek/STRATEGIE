-- ════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Step D (16.5.2026) — coreId migration
--
-- Marti's doctrine *„ID je svaty"* + UNIQUE(code, version) → fw.context_menu_item
-- action_params migrate na coreId resolver pattern.
--
-- Pre-state (Krok 14g-H+33 Etapa 2.1 + 2.2 v2):
--   action_params = {"form_core_code": "user_edit"}   ← code-based static
--
-- Post-state (Etapa F Step D):
--   action_params = {"coreId": "$core_id", "rowId": 1}  ← ID-based dynamic resolver
--
-- $core_id resolver picks ctx.core_id z DOM data-core-id attribute (z item dataset
-- v fw_form_dispatcher.js _buildContext). Tj. dispatch resolves at click time.
--
-- Plus label "Edit Form User" → "📋 Design: Přehled" — paralela k legacy
-- "Design: Soudeček + Core přehledu" (Marti's plan: po parity check drop legacy).
--
-- Run jako Marti-AI v DBeaveru. Idempotent — UPDATE matches jen rows s old
-- form_core_code pattern.
-- ════════════════════════════════════════════════════════════════════

-- Diagnostic (pre-update)
-- SELECT id, code, label, action_params FROM fw.context_menu_item;

UPDATE fw.context_menu_item
SET action_params = '{"coreId": "$core_id", "rowId": 1}'::jsonb,
    label = '📋 Design: Přehled',
    icon = '📋',
    updated_at = NOW()
WHERE code = 'edit_user_form'
  AND action_params ? 'form_core_code';  -- idempotent guard

-- Verify
SELECT id, code, label, icon, action_kind, action_params, design_only, status
FROM fw.context_menu_item
WHERE code = 'edit_user_form';
-- Expected: action_params={"coreId": "$core_id", "rowId": 1},
--           label='📋 Design: Přehled', icon='📋'
