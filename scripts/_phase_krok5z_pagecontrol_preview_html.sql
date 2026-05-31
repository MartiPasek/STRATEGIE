-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — pagecontrol preview_html (Page control addable v Preview palete)
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "Ted bych do preview potreboval pridat komponentu Page control"
--
-- pagecontrol uz JE v Preview whitelistu (field_picker_modal.js ~977) i v
-- comp-types listu (kind='container' AND status='active'). Chybi mu jen
-- preview_html -> karta v Preview ukazovala "(no preview)" misto mockupu.
--
-- preview_html = HTML mockup do gallery karty (field_picker_modal.js
-- _renderGalleryCard: previewScope.innerHTML). Tabs strip (Tab 1 aktivni
-- modry + Tab 2/3 sede) + content plocha. Stejny tmavy styl jako grid_modern.
--
-- Po pridani pagecontrolu z palety vznikne prazdny pagecontrol (zadny
-- tabsheet) -> render ukaze placeholder "PageControl #X - zadny tabsheet" ->
-- Marti prida zalozky pres + button (Krok 5.J-B4).
--
-- Drop z Preview: design_forms.js drop handler ma pagecontrol/tabsheet
-- v isContainer (direct create, bez column pickeru) — 30.5. edit.
--
-- PG string literal concat: sousedni 'quoted' literaly se spoji automaticky.
-- NEZAPOMEN COMMIT.
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.comp_type
SET preview_html =
'<div style="display:flex;flex-direction:column;width:100%;padding:2px;">'
  '<div style="display:flex;gap:2px;">'
    '<span style="background:#3a8aa8;color:#e8eef5;font-size:8px;font-weight:600;padding:3px 8px;border-radius:3px 3px 0 0;">Tab 1</span>'
    '<span style="background:#2a3340;color:#8a96a4;font-size:8px;padding:3px 8px;border-radius:3px 3px 0 0;">Tab 2</span>'
    '<span style="background:#2a3340;color:#8a96a4;font-size:8px;padding:3px 8px;border-radius:3px 3px 0 0;">Tab 3</span>'
  '</div>'
  '<div style="background:#0f1419;border:1px solid #2a3340;border-radius:0 3px 3px 3px;height:30px;"></div>'
'</div>'
WHERE code = 'pagecontrol';

-- Over po commitu (ocekavej preview_html NOT NULL):
-- SELECT id, code, label, kind, left(preview_html, 50) AS preview
-- FROM fw.comp_type WHERE code = 'pagecontrol';
