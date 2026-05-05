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

Layout: Flow s group hints (Marti-AI Q2). Komponenty v rámci GroupBox tečou
v responsive grid; mezi GroupBox volný prostor.
"""

from __future__ import annotations

import html
from typing import Any

from modules.erp.application.centrala_reader import FormComponent


def render_form(
    form_nazev: str,
    components: list[FormComponent],
    data: dict[str, Any] | None = None,
    *,
    read_only: bool = True,
    debug_info: dict | None = None,
) -> str:
    """
    Render kompletní formulář (jádro) jako HTML string.

    Args:
        form_nazev: EC_FormDef.Nazev (titulek formuláře)
        components: list FormComponent (z CentralaReader.load_form_components)
        data: dict s daty řádku (z execute_form_data, nebo None pro empty form)
        read_only: True pro Phase A (žádné edit save)
        debug_info: optional dict s diagnostic info (typ stats, raw fields)

    Returns:
        HTML string (server-rendered, Tailwind classes inline)
    """
    data = data or {}

    # Filtruj jen visual komponenty (Druh=1 v EC_FormDefComponentTypCis)
    # Non-visual: Typ=17 DataSet, Typ=18 DBFieldConstant, Typ=30 FormSetting
    NON_VISUAL_TYPS = {17, 18, 30}
    visual_components = [c for c in components if c.typ not in NON_VISUAL_TYPS]
    non_visual_count = len(components) - len(visual_components)

    # Sestavit hierarchii podle Typ=12 GroupBox
    # Pro Phase A: simple flat layout — komponenty seřazené podle ID,
    # GroupBox vytvoří "section break". Children GroupBox jsou komponenty
    # mezi GroupBox#N a GroupBox#N+1 (heuristika).
    sections = _build_sections(visual_components)

    # Render
    parts = [
        '<form class="cf-form" data-read-only="true">',
        f'  <header class="cf-form-header">',
        f'    <h2 class="text-xl font-semibold text-gray-800">{html.escape(form_nazev)}</h2>',
        f'  </header>',
    ]

    for section in sections:
        parts.append(_render_section(section, data, read_only=read_only))

    parts.append('</form>')

    if debug_info:
        parts.append(_render_debug_panel(debug_info, components, non_visual_count))

    return "\n".join(parts)


# ── Section building (group by Typ=12 GroupBox) ────────────────────


def _build_sections(components: list[FormComponent]) -> list[dict]:
    """
    Sestaví sekce z plochého seznamu komponent.

    Heuristika pro Phase A:
      - Typ=12 GroupBox = section header
      - Komponenty od jedné GroupBox po další patří do té sekce
      - Komponenty před první GroupBox = "default" sekce (caption "")
      - Buttony (Typ=8) → footer (poslední row)

    Phase B+ refine: použít cParent string ref pro správnou hierarchii.
    """
    sections: list[dict] = []
    current_section: dict | None = None
    footer_buttons: list[FormComponent] = []

    for comp in components:
        # Buttony → footer
        if comp.typ == 8:  # Button
            footer_buttons.append(comp)
            continue

        # GroupBox → nová sekce
        if comp.typ == 12:
            current_section = {
                "caption": comp.c_caption or "",
                "components": [],
                "groupbox_id": comp.id,
            }
            sections.append(current_section)
            continue

        # Ostatní → patří do current_section nebo default
        if current_section is None:
            current_section = {
                "caption": "",
                "components": [],
                "groupbox_id": None,
            }
            sections.append(current_section)
        current_section["components"].append(comp)

    if footer_buttons:
        sections.append({
            "caption": "_footer",
            "components": footer_buttons,
            "groupbox_id": None,
        })

    return sections


# ── Section rendering ─────────────────────────────────────────────


def _render_section(section: dict, data: dict, read_only: bool) -> str:
    """Render jedné sekce (GroupBox + její komponenty)."""
    caption = section["caption"]
    components = section["components"]

    # Footer (buttony)
    if caption == "_footer":
        btn_htmls = [_render_component(c, data, read_only=read_only) for c in components]
        return (
            '  <footer class="cf-form-footer flex gap-2 pt-4 border-t border-gray-200 mt-4">\n'
            + "\n".join(btn_htmls)
            + "\n  </footer>"
        )

    # Sekce s GroupBox header
    section_html = ['  <section role="group" class="cf-group">']
    if caption:
        section_html.append(
            f'    <header class="cf-group-header text-sm font-semibold text-gray-700 mb-3">'
            f'{html.escape(caption)}</header>'
        )
    section_html.append('    <div class="cf-fields grid gap-3" '
                        'style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">')
    for comp in components:
        section_html.append(_render_component(comp, data, read_only=read_only))
    section_html.append('    </div>')
    section_html.append('  </section>')
    return "\n".join(section_html)


# ── Component rendering (Typ → HTML) ──────────────────────────────


def _render_component(comp: FormComponent, data: dict, read_only: bool) -> str:
    """Render jednoho komponenta podle Typ."""
    bound_value = ""
    if comp.c_field_name and comp.c_field_name in data:
        v = data[comp.c_field_name]
        bound_value = "" if v is None else str(v)

    # Typ-specific rendering
    if comp.typ == 1:  # Label
        return f'      <div class="cf-label-only text-sm text-gray-600">{html.escape(comp.c_caption)}</div>'

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

    if comp.typ == 12:  # GroupBox — handled v _build_sections, neměl by sem dorazit
        return f'      <!-- GroupBox#{comp.id} should be in section header -->'

    # Fallback pro unknown / unimplemented Typ
    typ_name = comp.properties.get("_typ_name", f"Typ={comp.typ}")
    return (
        f'      <div class="cf-unknown text-xs text-orange-600 p-2 bg-orange-50 rounded">\n'
        f'        ⚠ {typ_name} (cFieldName={html.escape(comp.c_field_name or "—")}, '
        f'cCaption={html.escape(comp.c_caption or "—")})\n'
        f'        <span class="text-gray-500">— Phase A neimplementuje, viz Phase B+</span>\n'
        f'      </div>'
    )


def _render_edit(comp: FormComponent, value: str, read_only: bool) -> str:
    """Edit (Typ=2) → <input type="text">."""
    readonly_attr = "readonly" if read_only else ""
    is_id_field = comp.c_field_name.upper() == "ID"
    bg_class = "bg-gray-100" if (read_only or is_id_field) else "bg-white"
    return (
        f'      <div class="cf-field">\n'
        f'        <label class="block text-xs text-gray-600 mb-1">{html.escape(comp.c_caption)}</label>\n'
        f'        <input type="text" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(value)}" '
        f'data-mask="{html.escape(comp.c_mask)}" '
        f'class="cf-edit w-full px-2 py-1 border border-gray-300 rounded {bg_class}" '
        f'{readonly_attr}>\n'
        f'      </div>'
    )


def _render_checkbox(comp: FormComponent, value: str, read_only: bool) -> str:
    """CheckBox (Typ=3) → <input type="checkbox">."""
    readonly_attr = "disabled" if read_only else ""
    is_checked = str(value).lower() in ("1", "true", "ano", "yes")
    return (
        f'      <label class="cf-checkbox flex items-center gap-2 cursor-pointer">\n'
        f'        <input type="checkbox" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'{"checked" if is_checked else ""} '
        f'class="cf-check rounded border-gray-300" '
        f'{readonly_attr}>\n'
        f'        <span class="text-sm text-gray-700">{html.escape(comp.c_caption)}</span>\n'
        f'      </label>'
    )


def _render_date(comp: FormComponent, value: str, read_only: bool) -> str:
    """DateEdit (Typ=5) → <input type="date">."""
    readonly_attr = "readonly" if read_only else ""
    # Strip time portion if present (datetime → date)
    date_value = (value or "").split(" ")[0].split("T")[0]
    return (
        f'      <div class="cf-field">\n'
        f'        <label class="block text-xs text-gray-600 mb-1">{html.escape(comp.c_caption)}</label>\n'
        f'        <input type="date" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(date_value)}" '
        f'class="cf-date w-full px-2 py-1 border border-gray-300 rounded bg-white" '
        f'{readonly_attr}>\n'
        f'      </div>'
    )


def _render_formlist(
    comp: FormComponent, value: str, data: dict, read_only: bool
) -> str:
    """
    FormList (Typ=6) → command palette modal trigger.

    Marti-AI's Q4 vstup: "FormList je fullscreen proto, že uživatel přemýšlí.
    Moderní ekvivalent: command palette pattern (Cmd+K, Spotlight)."

    Phase A: zobrazí jen current value + ▼ button (modal not yet wired).
    Phase B: Alpine.js modal s server-side filter.
    """
    readonly_attr = "readonly" if read_only else ""
    return (
        f'      <div class="cf-field cf-formlist">\n'
        f'        <label class="block text-xs text-gray-600 mb-1">{html.escape(comp.c_caption)}</label>\n'
        f'        <div class="flex gap-1">\n'
        f'          <input type="text" '
        f'name="{html.escape(comp.c_field_name)}" '
        f'value="{html.escape(value)}" '
        f'class="cf-edit flex-1 px-2 py-1 border border-gray-300 rounded bg-gray-100" '
        f'{readonly_attr}>\n'
        f'          <button type="button" class="cf-lookup-btn px-3 py-1 border border-gray-300 rounded hover:bg-gray-50" disabled>▼</button>\n'
        f'        </div>\n'
        f'      </div>'
    )


def _render_combobox(comp: FormComponent, value: str, read_only: bool) -> str:
    """Combobox (Typ=7) → <select>."""
    readonly_attr = "disabled" if read_only else ""
    # Phase A: žádné options (textlists nejsou zatím načítány). Default empty + current.
    return (
        f'      <div class="cf-field">\n'
        f'        <label class="block text-xs text-gray-600 mb-1">{html.escape(comp.c_caption)}</label>\n'
        f'        <select name="{html.escape(comp.c_field_name)}" '
        f'class="cf-combo w-full px-2 py-1 border border-gray-300 rounded bg-white" '
        f'{readonly_attr}>\n'
        f'          <option value="{html.escape(value)}" selected>{html.escape(value or "—")}</option>\n'
        f'        </select>\n'
        f'      </div>'
    )


def _render_button(comp: FormComponent, read_only: bool) -> str:
    """Button (Typ=8) → <button>."""
    caption = comp.c_caption or "Akce"
    is_primary = caption.upper() in ("OK", "ULOŽIT", "SAVE")
    is_cancel = caption.upper() in ("STORNO", "CANCEL", "ZRUŠIT")
    bg_class = (
        "bg-blue-600 text-white hover:bg-blue-700"
        if is_primary
        else "bg-gray-200 text-gray-700 hover:bg-gray-300"
        if is_cancel
        else "bg-white border border-gray-300 hover:bg-gray-50"
    )
    return (
        f'    <button type="button" '
        f'class="cf-btn px-4 py-2 rounded text-sm font-medium {bg_class}" '
        f'{"disabled" if read_only else ""}>\n'
        f'      {html.escape(caption)}\n'
        f'    </button>'
    )


# ── Debug panel ─────────────────────────────────────────────────────


def _render_debug_panel(debug_info: dict, components: list[FormComponent], non_visual_count: int) -> str:
    """Render diagnostický panel pod formulářem (Phase A debug)."""
    typ_stats: dict[int, int] = {}
    for c in components:
        typ_stats[c.typ] = typ_stats.get(c.typ, 0) + 1

    typ_lines = []
    for typ, cnt in sorted(typ_stats.items()):
        typ_name = debug_info.get("typ_names", {}).get(typ, f"Typ={typ}")
        typ_lines.append(f"      <li>Typ={typ} ({typ_name}): {cnt}×</li>")

    return (
        '\n<details class="mt-6 p-4 bg-gray-50 border border-gray-200 rounded text-sm">\n'
        '  <summary class="cursor-pointer font-medium text-gray-700">🛠 Debug info (Phase A)</summary>\n'
        '  <div class="mt-3 grid grid-cols-2 gap-4">\n'
        f'    <div>\n'
        f'      <div class="font-medium mb-1">Form info</div>\n'
        f'      <ul class="text-xs text-gray-600 space-y-0.5">\n'
        f'        <li>form_id: {debug_info.get("form_id", "?")}</li>\n'
        f'        <li>row_id: {debug_info.get("row_id", "?")}</li>\n'
        f'        <li>komponent celkem: {len(components)}</li>\n'
        f'        <li>visual: {len(components) - non_visual_count}</li>\n'
        f'        <li>non-visual (Typ 17/18/30): {non_visual_count}</li>\n'
        f'        <li>data sloupců: {len(debug_info.get("data_keys", []))}</li>\n'
        f'      </ul>\n'
        f'    </div>\n'
        f'    <div>\n'
        f'      <div class="font-medium mb-1">Typ statistika</div>\n'
        f'      <ul class="text-xs text-gray-600 space-y-0.5">\n'
        + "\n".join(typ_lines)
        + '\n      </ul>\n'
        f'    </div>\n'
        '  </div>\n'
        '</details>'
    )
