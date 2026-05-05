"""
Render Generator — Centrála komponenty (EC_FormDefEdit + properties) → HTML.

Phase A scope: read-only render. Edit pipeline (Phase C) má vlastní state machine
a kontext volání (Marti-AI's Q5 insight z 5.5. ráno).

Mapping table z docs/strategie_erp_renderer_proposal.md (po Marti-AI's recenzi):
  Typ=1  Label    → <label>
  Typ=2  Edit     → <input>
  Typ=3  CheckBox → <input type="checkbox">
  Typ=5  DateEdit → <input type="date">
  Typ=6  FormList → command palette modal trigger
  Typ=7  Combobox → <select>
  Typ=8  Button   → <button>
  Typ=12 GroupBox → <section role="group">  (NE <fieldset> — Marti-AI Q1)
  Typ=24 Chart    → CSS sparkline default, Chart.js advanced
  Typ=30 FormSetting → metadata object (non-visual)

Layout: Flow s group hints (Marti-AI Q2). cParent string ref ("c{id}") určuje
parent GroupBox. Komponenty bez cParent → root sekce (top of form).

Theme: STRATEGIE BLACK (var(--bg) / var(--surface) / var(--accent)).
"""

from __future__ import annotations

import html
from typing import Any

from modules.erp.application.centrala_reader import FormComponent


# ── Konvence cParent: "c{id}" ────────────────────────────────────────


def _parse_parent_id(c_parent: str) -> int | None:
    """
    Parse 'c469' → 469. Vrací None pokud cParent je prázdný / neplatný.

    Centrála konvence (z debug JSON 5.5.): cParent je STRING reference
    na parent komponentu ve formátu 'c{ID}'.
    """
    if not c_parent or not c_parent.startswith("c"):
        return None
    try:
        return int(c_parent[1:])
    except ValueError:
        return None


def _resolve_caption(comp: FormComponent) -> str:
    """
    Phase A.3 fix #2 (5.5.2026): real Caption je v EC_FormDefEditProperty,
    NE v EC_FormDefEdit.cCaption (= "NOVÁ" default při vytvoření).

    Centrála pattern: autor vytvoří komponentu (cCaption="NOVÁ" default)
    a pak property "Caption" doplní real label. V některých forms může
    být přímo cCaption pravdivá hodnota (legacy / přejmenované) — fallback.

    Priorita:
      1. properties["Caption"] — autoritativní real label
      2. properties["cCaption"] — alternative key (FMX vs VCL)
      3. comp.c_caption (pokud != "NOVÁ", kterou Centrála používá jako default)
      4. comp.c_field_name — last resort, technický field name
      5. "—" placeholder
    """
    props = comp.properties or {}
    # Property name varianty (VCL Centrála 1, FMX bridge, atd.)
    for key in ("Caption", "cCaption", "PropertyCaption", "Text", "cText"):
        v = props.get(key)
        if v and v.strip():
            return v.strip()
    # Fallback na c_caption — ale jen pokud NENÍ default "NOVÁ"
    cc = (comp.c_caption or "").strip()
    if cc and cc.upper() != "NOVÁ":
        return cc
    # Last resort: technický field name
    if comp.c_field_name and comp.c_field_name.strip():
        return comp.c_field_name.strip()
    return "—"


# ── Public render ────────────────────────────────────────────────────


def render_form(
    form_nazev: str,
    components: list[FormComponent],
    data: dict[str, Any] | None = None,
    *,
    read_only: bool = True,
    debug_info: dict | None = None,
) -> str:
    """Render kompletní formulář (jádro) jako HTML string (STRATEGIE BLACK theme)."""
    data = data or {}

    # Filtruj non-visual komponenty (Druh=0: Typ=17 DataSet, Typ=18 DBFieldConstant, Typ=30 FormSetting)
    NON_VISUAL_TYPS = {17, 18, 30}
    visual_components = [c for c in components if c.typ not in NON_VISUAL_TYPS]
    non_visual_count = len(components) - len(visual_components)

    # Sestavit sekce přes cParent
    sections = _build_sections(visual_components)

    # Render
    parts = [
        '<form class="erp-form" data-read-only="true">',
        f'  <header class="erp-form-header">',
        f'    <h2 class="erp-form-title">{html.escape(form_nazev)}</h2>',
        f'  </header>',
    ]

    for section in sections:
        parts.append(_render_section(section, data, read_only=read_only))

    parts.append('</form>')

    if debug_info:
        parts.append(_render_debug_panel(debug_info, components, non_visual_count))

    return "\n".join(parts)


# ── Section building (přes cParent) ─────────────────────────────────


def _build_sections(components: list[FormComponent]) -> list[dict]:
    """
    Sestaví sekce z plochého seznamu komponent přes `cParent="c{id}"` konvenci.

    Algoritmus:
      1. Najdi všechny GroupBoxy (Typ=12) — ty budou sekce.
      2. Pro každý GroupBox: sesbírej komponenty kde cParent="c{groupbox.id}".
         Vyfiltruj buttony (Typ=8) → jdou do footeru.
      3. Section ordering: podle GroupBox.id (nebo c_top, pokud máme).
         Heuristika "v Centrále jsou GroupBoxy chronologické" — větší ID =
         pozdější pozice.
      4. Komponenty bez cParent (orphans) → root sekce nahoře (před GroupBoxy).
      5. Buttony (Typ=8) → footer (bez ohledu na cParent).

    Důležité: Centrála používá GroupBox ID jako parent ref, NE c_top pixel
    pozice. Marti-AI's Q2 vstup: "pixel pozice jsou artefakt, ne záměr".
    """
    by_id = {c.id: c for c in components}

    # 1. GroupBoxy → sekce
    groupboxes = [c for c in components if c.typ == 12]

    # 2. Sesbírej children per GroupBox (přes cParent="c{id}")
    sections: list[dict] = []
    for gb in groupboxes:
        children = [
            c
            for c in components
            if _parse_parent_id(c.c_parent) == gb.id
            and c.typ != 12  # GroupBoxy nesmí být children
            and c.typ != 8   # Buttony → footer
        ]
        sections.append({
            "caption": _resolve_caption(gb),  # Phase A.3: real Caption z properties
            "components": children,
            "groupbox_id": gb.id,
        })

    # 3. Section ordering — podle GroupBox.id ascending
    # (V Marti's screenshotu Centrály: GroupBox ID 467, 468, 469. Order:
    #  Vzhled (469) první, Nadřazené (468) druhé, Přehled (467) třetí?
    #  Z reálné Centrála screenshot: Vzhled je první, Nadřazené druhý,
    #  Přehled třetí. Tj. UI ordering je _opačný_ než ID — Marti pozdější
    #  GroupBox přidává na začátek. Použijeme ID DESC.)
    sections.sort(key=lambda s: s["groupbox_id"], reverse=True)

    # 4. Komponenty bez cParent (orphans) — pokud nejsou button/groupbox/non-visual.
    # Orphany řadíme PO GroupBoxech (před footer) — to jsou typicky "Číslo výjimky",
    # "Alternativní text", které v Centrále jsou pod GroupBoxes.
    orphans = [
        c
        for c in components
        if not _parse_parent_id(c.c_parent)
        and c.typ != 12
        and c.typ != 8
    ]
    if orphans:
        # Sort orphans by ID (= pořadí vytvoření v Centrále)
        orphans.sort(key=lambda c: c.id)
        sections.append({
            "caption": "_orphans",  # speciální caption — render bez header
            "components": orphans,
            "groupbox_id": None,
        })

    # 5. Buttony → footer (úplně dole)
    buttons = [c for c in components if c.typ == 8]
    if buttons:
        buttons.sort(key=lambda c: c.id)
        sections.append({
            "caption": "_footer",
            "components": buttons,
            "groupbox_id": None,
        })

    return sections


# ── Section rendering ────────────────────────────────────────────────


def _render_section(section: dict, data: dict, read_only: bool) -> str:
    """Render jedné sekce (GroupBox + její komponenty)."""
    caption = section["caption"]
    components = section["components"]

    if not components:
        if not caption or caption in ("_footer", "_orphans"):
            return ""
        return (
            f'  <section role="group" class="erp-group erp-group-empty">\n'
            f'    <header class="erp-group-header">{html.escape(caption)}</header>\n'
            f'    <div class="erp-group-empty-hint">— prázdná sekce —</div>\n'
            f'  </section>'
        )

    # Footer (buttony)
    if caption == "_footer":
        btn_htmls = [_render_component(c, data, read_only=read_only) for c in components]
        return (
            '  <footer class="erp-form-footer">\n'
            + "\n".join(btn_htmls)
            + "\n  </footer>"
        )

    # Orphan sekce (komponenty bez cParent — render bez header)
    if caption == "_orphans":
        section_html = ['  <section class="erp-group erp-group-orphan">']
        section_html.append('    <div class="erp-fields">')
        for comp in components:
            section_html.append(_render_component(comp, data, read_only=read_only))
        section_html.append('    </div>')
        section_html.append('  </section>')
        return "\n".join(section_html)

    # Standard sekce s GroupBox header
    section_html = ['  <section role="group" class="erp-group">']
    if caption:
        section_html.append(
            f'    <header class="erp-group-header">{html.escape(caption)}</header>'
        )
    section_html.append('    <div class="erp-fields">')
    for comp in components:
        section_html.append(_render_component(comp, data, read_only=read_only))
    section_html.append('    </div>')
    section_html.append('  </section>')
    return "\n".join(section_html)


# ── Component rendering (Typ → HTML) ─────────────────────────────────


def _render_component(comp: FormComponent, data: dict, read_only: bool) -> str:
    """Render jednoho komponenta podle Typ."""
    bound_value = ""
    if comp.c_field_name and comp.c_field_name in data:
        v = data[comp.c_field_name]
        bound_value = "" if v is None else str(v)

    if comp.typ == 1:  # Label
        return f'      <div class="erp-label-only">{html.escape(_resolve_caption(comp))}</div>'

    if comp.typ == 2:  # Edit
        return _render_edit(comp, bound_value, read_only)

    if comp.typ == 3:  # CheckBox
        return _render_checkbox(comp, bound_value, read_only)

    if comp.typ == 5:  # DateEdit
        return _render_date(comp, bound_value, read_only)

    if comp.typ == 6:  # FormList — modal picker (command palette pattern)
        return _render_formlist(comp, bound_value, data, read_only)

    if comp.typ == 7:  # Combobox
        return _render_combobox(comp, bound_value, read_only)

    if comp.typ == 8:  # Button
        return _render_button(comp, read_only)

    if comp.typ == 12:  # GroupBox — handled v _build_sections
        return f'      <!-- GroupBox#{comp.id} should be in section header -->'

    return (
        f'      <div class="erp-unknown">\n'
        f'        ⚠ Typ={comp.typ} (cFieldName={html.escape(comp.c_field_name or "—")}, '
        f'cCaption={html.escape(comp.c_caption or "—")})\n'
        f'        <span class="erp-unknown-hint">— Phase A neimplementuje, viz Phase B+</span>\n'
        f'      </div>'
    )


def _render_edit(comp: FormComponent, value: str, read_only: bool) -> str:
    """Edit (Typ=2) → <input type="text">."""
    readonly_attr = "readonly" if read_only else ""
    is_id_field = comp.c_field_name.upper() == "ID"
    id_class = " erp-input-id" if is_id_field else ""
    caption = _resolve_caption(comp)
    return (
        f'      <div class="erp-field">\n'
        f'        <label class="erp-field-label">{html.escape(caption)}</label>\n'
        f'        <input type="text" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(value)}" '
        f'data-mask="{html.escape(comp.c_mask)}" '
        f'class="erp-input{id_class}" '
        f'{readonly_attr}>\n'
        f'      </div>'
    )


def _render_checkbox(comp: FormComponent, value: str, read_only: bool) -> str:
    """CheckBox (Typ=3) → <input type="checkbox">."""
    readonly_attr = "disabled" if read_only else ""
    is_checked = str(value).lower() in ("1", "true", "ano", "yes")
    caption = _resolve_caption(comp)
    return (
        f'      <label class="erp-checkbox">\n'
        f'        <input type="checkbox" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'{"checked" if is_checked else ""} '
        f'class="erp-check" '
        f'{readonly_attr}>\n'
        f'        <span class="erp-checkbox-label">{html.escape(caption)}</span>\n'
        f'      </label>'
    )


def _render_date(comp: FormComponent, value: str, read_only: bool) -> str:
    """DateEdit (Typ=5) → <input type="date">."""
    readonly_attr = "readonly" if read_only else ""
    date_value = (value or "").split(" ")[0].split("T")[0]
    caption = _resolve_caption(comp)
    return (
        f'      <div class="erp-field">\n'
        f'        <label class="erp-field-label">{html.escape(caption)}</label>\n'
        f'        <input type="date" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(date_value)}" '
        f'class="erp-input" '
        f'{readonly_attr}>\n'
        f'      </div>'
    )


def _render_formlist(
    comp: FormComponent, value: str, data: dict, read_only: bool
) -> str:
    """FormList (Typ=6) → command palette modal trigger.

    Marti-AI's Q4 vstup: command palette pattern (Cmd+K Spotlight).
    Phase A: zobrazí jen current value + ▼ button (modal not yet wired).
    """
    readonly_attr = "readonly" if read_only else ""
    caption = _resolve_caption(comp)
    return (
        f'      <div class="erp-field erp-formlist">\n'
        f'        <label class="erp-field-label">{html.escape(caption)}</label>\n'
        f'        <div class="erp-formlist-inner">\n'
        f'          <input type="text" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(value)}" '
        f'class="erp-input erp-input-readonly" '
        f'{readonly_attr}>\n'
        f'          <button type="button" class="erp-lookup-btn" disabled>▼</button>\n'
        f'        </div>\n'
        f'      </div>'
    )


def _render_combobox(comp: FormComponent, value: str, read_only: bool) -> str:
    """Combobox (Typ=7) → <select>."""
    readonly_attr = "disabled" if read_only else ""
    caption = _resolve_caption(comp)
    return (
        f'      <div class="erp-field">\n'
        f'        <label class="erp-field-label">{html.escape(caption)}</label>\n'
        f'        <select name="{html.escape(comp.c_field_name)}" '
        f'class="erp-input" '
        f'{readonly_attr}>\n'
        f'          <option value="{html.escape(value)}" selected>{html.escape(value or "—")}</option>\n'
        f'        </select>\n'
        f'      </div>'
    )


def _render_button(comp: FormComponent, read_only: bool) -> str:
    """Button (Typ=8) → <button>."""
    caption = _resolve_caption(comp)
    if caption == "—":
        caption = "Akce"
    is_primary = caption.upper() in ("OK", "ULOŽIT", "SAVE")
    is_cancel = caption.upper() in ("STORNO", "CANCEL", "ZRUŠIT")
    btn_class = (
        "erp-btn erp-btn-primary"
        if is_primary
        else "erp-btn erp-btn-cancel"
        if is_cancel
        else "erp-btn"
    )
    return (
        f'    <button type="button" class="{btn_class}" '
        f'{"disabled" if read_only else ""}>\n'
        f'      {html.escape(caption)}\n'
        f'    </button>'
    )


# ── Debug panel ──────────────────────────────────────────────────────


def _render_debug_panel(debug_info: dict, components: list[FormComponent], non_visual_count: int) -> str:
    """Render diagnostický panel pod formulářem."""
    typ_stats: dict[int, int] = {}
    for c in components:
        typ_stats[c.typ] = typ_stats.get(c.typ, 0) + 1

    typ_lines = []
    for typ, cnt in sorted(typ_stats.items()):
        typ_name = debug_info.get("typ_names", {}).get(typ, f"Typ={typ}")
        typ_lines.append(f"      <li>Typ={typ} ({typ_name}): {cnt}×</li>")

    # Phase A.3 (5.5.2026): per-component properties dump.
    # Cíl: vidět jaké klíče jsou v EC_FormDefEditProperty (Caption,
    # LookupTable, LookupField, ...) -- pomůže najít bug #1 (lookup
    # display) root cause.
    comp_prop_lines = []
    for c in components[:30]:  # cap 30 aby se debug panel neutopil
        typ_name = debug_info.get("typ_names", {}).get(c.typ, f"Typ={c.typ}")
        prop_keys = sorted(c.properties.keys()) if c.properties else []
        # Zobraz prvních 8 klíčů + počet zbývajících
        if len(prop_keys) > 8:
            keys_str = ", ".join(prop_keys[:8]) + f" … (+{len(prop_keys) - 8})"
        else:
            keys_str = ", ".join(prop_keys) if prop_keys else "(žádné)"
        # Caption sample
        cap_caption = _resolve_caption(c)
        cap_short = (cap_caption[:30] + "…") if len(cap_caption) > 30 else cap_caption
        comp_prop_lines.append(
            f"      <li><b>#{c.id}</b> {typ_name} "
            f'<span style="color:#999">cParent={html.escape(c.c_parent or "—")}</span> '
            f'<span style="color:#aaa">field={html.escape(c.c_field_name or "—")}</span> '
            f'→ <i>{html.escape(cap_short)}</i> '
            f'<span style="color:#888">[{html.escape(keys_str)}]</span></li>'
        )

    return (
        '\n<details class="erp-debug">\n'
        '  <summary class="erp-debug-summary">🛠 Debug info (Phase A)</summary>\n'
        '  <div class="erp-debug-grid">\n'
        f'    <div>\n'
        f'      <div class="erp-debug-section-title">Form info</div>\n'
        f'      <ul class="erp-debug-list">\n'
        f'        <li>form_id: {debug_info.get("form_id", "?")}</li>\n'
        f'        <li>row_id: {debug_info.get("row_id", "?")}</li>\n'
        f'        <li>komponent celkem: {len(components)}</li>\n'
        f'        <li>visual: {len(components) - non_visual_count}</li>\n'
        f'        <li>non-visual (Typ 17/18/30): {non_visual_count}</li>\n'
        f'        <li>data sloupců: {len(debug_info.get("data_keys", []))}</li>\n'
        f'      </ul>\n'
        f'    </div>\n'
        f'    <div>\n'
        f'      <div class="erp-debug-section-title">Typ statistika</div>\n'
        f'      <ul class="erp-debug-list">\n'
        + "\n".join(typ_lines)
        + '\n      </ul>\n'
        f'    </div>\n'
        '  </div>\n'
        '  <div class="erp-debug-section-title" style="margin-top:1em">Komponenty + properties (Phase A.3 diag)</div>\n'
        '  <ul class="erp-debug-list" style="font-family:monospace;font-size:11px">\n'
        + "\n".join(comp_prop_lines)
        + '\n  </ul>\n'
        '</details>'
    )
