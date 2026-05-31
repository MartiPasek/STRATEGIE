-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — grid_modern preview_html (addable Preview karta v palete)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "Potrebujeme Preview do palety" — grid_modern jako addable
-- komponenta v palete (Preview tab + comp-types dropdown).
--
-- preview_html = HTML mockup do karty (field_picker_modal.js: scope.innerHTML).
-- Nastavenim preview_html (NE NULL) se grid_modern objevi v /design/comp-types
-- listu (WHERE preview_html IS NOT NULL ...) -> Preview tab karta + addable +
-- dropdown option (uz nepotrebuje type_label fallback).
--
-- Po pridani gridu z palety vznikne prazdny grid_modern comp_def -> Marti ho
-- nakonfiguruje pres ⚙ "Nastaveni gridu" (data_source, filter, kind, align).
--
-- default_props: zakladni layout at novy grid neni uplne prazdny (height 400,
-- context_menu refresh). data_source_code doplni Marti pres ⚙.
--
-- Zadny ':' -> zadny DBeaver bind dialog. NEZAPOMEN COMMIT.
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.comp_type
SET preview_html =
'<div style="display:flex;flex-direction:column;gap:3px;width:100%;padding:2px;">'
  '<div style="display:flex;gap:3px;">'
    '<span style="flex:1;background:#2a3340;height:11px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#2a3340;height:11px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#2a3340;height:11px;border-radius:2px;"></span>'
  '</div>'
  '<div style="display:flex;gap:3px;">'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
  '</div>'
  '<div style="display:flex;gap:3px;">'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
    '<span style="flex:1;background:#0f1419;height:9px;border-radius:2px;"></span>'
  '</div>'
'</div>',
    default_props = COALESCE(default_props, '{}'::jsonb)
                    || jsonb_build_object('height_px', 400, 'context_menu', jsonb_build_array('refresh'))
WHERE code = 'grid_modern';

-- Over po commitu:
-- SELECT id, code, label, kind, left(preview_html, 40) AS preview, default_props
-- FROM fw.comp_type WHERE code = 'grid_modern';
