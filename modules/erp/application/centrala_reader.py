"""
Centrála Reader — wrapping Phase 28-C MCP klient pro čtení DB_EC metadat.

Phase A scope:
  - load_form_def(form_id) → header jádra (EC_FormDef)
  - load_form_components(form_id) → komponenty (EC_FormDefEdit + properties)
  - execute_form_data(form_id, row_id) → substituce :ID + execute SQL_Select
  - load_centrala_menu_row(menu_id) → fallback pro debug

POZN: MCP klient (Phase 28-C composer-side) je single-thread asyncio loop
běžící v background. Volá se sync přes call_tool_sync(). Pro Phase A je to
adekvátní; pokud Phase B+ vyžaduje paralel, můžeme udělat per-request klient.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from core.logging import get_logger

logger = get_logger("erp.centrala_reader")


# ── Data classes pro výstup ──────────────────────────────────────────


@dataclass
class FormDef:
    """Header jádra z EC_FormDef."""
    id: int
    nazev: str
    sql_select: str
    f_top: int | None = None
    f_left: int | None = None
    f_height: int | None = None
    f_width: int | None = None
    autor: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class FormComponent:
    """Komponenta z EC_FormDefEdit + její properties."""
    id: int
    id_form: int
    typ: int                      # číselník (1=Label, 2=Edit, 3=CheckBox, ...)
    c_caption: str = ""
    c_field_name: str = ""        # data binding sloupec ze SQL_Select
    c_parent: str = ""            # string ref na parent komponentu
    c_top: int = 60
    c_left: int = 60
    c_height: int = 20
    c_width: int = 100
    c_mask: str = ""              # format mask
    smazana: bool = False
    properties: dict[str, str] = field(default_factory=dict)  # key/value z EditProperty
    raw: dict[str, Any] = field(default_factory=dict)


# ── Slovník Typ → název komponenty (z EC_FormDefComponentTypCis) ─────

# Marti's tabulka 5.5. ráno (37 hodnot, 2015-2025)
TYP_NAMES: dict[int, str] = {
    1: "Label",
    2: "Edit",
    3: "CheckBox",
    4: "RichEdit",
    5: "DateEdit",
    6: "FormList",          # modal picker (Cmd+K command palette)
    7: "Combobox",
    8: "Button",
    9: "FileListBox",
    10: "TimeEdit",
    11: "Grid",
    12: "GroupBox",         # <section role="group"> (Marti-AI's recenze)
    13: "Panel",
    14: "Splitter",
    15: "PageControl",
    16: "TabSheet",
    17: "DataSet",          # non-visual
    18: "DBFieldConstant",  # non-visual
    19: "DBTreeView",
    20: "SpeedButton",
    21: "GridPolDoklad",
    22: "RichEditor",
    23: "DateTimeEdit",
    24: "Chart",            # CSS sparkline default, Chart.js advanced
    25: "Rastr",
    26: "Image",
    27: "KvalifTest",
    28: "ListEdit",
    29: "UkolV1",
    30: "FormSetting",      # non-visual, drží form-level metadata
    31: "Planner",
    32: "InputList",
    33: "RichEditorV1",
    34: "OpakovanyUkol",
    35: "TextComparator",
    36: "ModulJadra",       # embed sub-form (recursive)
    37: "Klavesnice",
}


# ── Reader API ───────────────────────────────────────────────────────


class CentralaReader:
    """Wrapper kolem Phase 28-C MCP klient pro čtení DB_EC."""

    def __init__(self):
        # Lazy import — eurosoft_mcp_client je v conversation modulu (existing)
        from modules.conversation.application.eurosoft_mcp_client import (
            get_eurosoft_mcp_client,
        )
        self._client = get_eurosoft_mcp_client()
        if self._client is None:
            logger.warning(
                "CentralaReader: MCP klient is None (eurosoft_mcp_enabled=False?). "
                "Read operations vrátí prázdné výsledky."
            )

    # ── helper pro MCP call ──────────────────────────────────────────

    def _call_mcp(self, tool_name: str, args: dict) -> dict | None:
        """Zavolá MCP tool, vrátí parsed JSON nebo None pri chybě."""
        if self._client is None:
            return None
        try:
            result_str = self._client.call_tool_sync(
                f"eurosoft_{tool_name}",
                args,
                conversation_id=None,  # ERP volání ne-per-conversation
            )
            result = json.loads(result_str)
            if not result.get("ok"):
                logger.warning(
                    f"CentralaReader: MCP {tool_name} returned ok=False: "
                    f"{result.get('error')} - {result.get('message', '')}"
                )
                return None
            return result
        except Exception as e:
            logger.error(f"CentralaReader: MCP {tool_name} crashed: {e}", exc_info=True)
            return None

    # ── public API ──────────────────────────────────────────────────

    def load_form_def(self, form_id: int) -> FormDef | None:
        """Načti EC_FormDef row dle ID."""
        # Použijeme get_row tool (přímý lookup po PK je rychlejší než query_table)
        result = self._call_mcp(
            "get_row",
            {"table": "EC_FormDef", "id": form_id},
        )
        if not result or not result.get("row"):
            logger.warning(f"CentralaReader: EC_FormDef ID={form_id} nenalezen.")
            return None

        row = result["row"]
        return FormDef(
            id=row.get("ID"),
            nazev=row.get("Nazev") or "",
            sql_select=row.get("SQL_Select") or "",
            f_top=row.get("fTop"),
            f_left=row.get("fLeft"),
            f_height=row.get("fHeight"),
            f_width=row.get("fWidth"),
            autor=row.get("Autor"),
            raw=row,
        )

    def load_form_components(self, form_id: int) -> list[FormComponent]:
        """
        Načti všechny komponenty jádra (EC_FormDefEdit) + jejich properties
        (EC_FormDefEditProperty). Filtruje Smazana=0.

        Returns: list FormComponent ve skupinovém pořadí (ORDER BY ID).
        """
        # 1. Načti komponenty — query_table API: filters dict + order_by list
        comps_result = self._call_mcp(
            "query_table",
            {
                "table": "EC_FormDefEdit",
                "filters": {"ID_Form": form_id, "Smazana": 0},
                "order_by": ["ID"],
                "limit": 200,
            },
        )
        if not comps_result or not comps_result.get("rows"):
            logger.info(
                f"CentralaReader: žádné komponenty pro EC_FormDef ID={form_id}"
            )
            return []

        components: list[FormComponent] = []
        comp_ids: list[int] = []
        for row in comps_result["rows"]:
            cid = row.get("ID")
            if cid is None:
                continue
            comp_ids.append(cid)
            components.append(
                FormComponent(
                    id=cid,
                    id_form=row.get("ID_Form") or form_id,
                    typ=row.get("Typ") or 0,
                    c_caption=row.get("cCaption") or "",
                    c_field_name=row.get("cFieldName") or "",
                    c_parent=row.get("cParent") or "",
                    c_top=row.get("cTop") or 0,
                    c_left=row.get("cLeft") or 0,
                    c_height=row.get("cHeight") or 20,
                    c_width=row.get("cWidth") or 100,
                    c_mask=row.get("cMask") or "",
                    smazana=bool(row.get("Smazana", 0)),
                    raw=row,
                )
            )

        if not comp_ids:
            return components

        # 2. Načti properties pro všechny komponenty najednou
        # query_table API: filters dict + IN syntax přes list value
        #
        # ⚠ Phase A.4 (5.5.2026): Smazana filter ODSTRANĚN. Diagnostika
        # ukázala, že VŠECHNY rows v EC_FormDefEditProperty mají
        # Smazana=true, vč. aktivně používaných (Caption "Požadovat
        # přihlášení" pro CheckBox #1717). Centrála flag ignoruje --
        # není to soft-delete, ale pravděpodobně migration marker.
        # Framework doc (řádek 1524) tvrdí "soft delete", ale reálně to
        # tak nefunguje. EC_FormDefEdit.Smazana je pravý soft-delete,
        # EC_FormDefEditProperty.Smazana není.
        # ⚠ Phase B+6.10c-fix (6.5.2026 večer): limit 1000 byl bug. Velké formy
        # (37+ komponent × 15-20 properties = 555+) mohou přesáhnout limit.
        # TabSheety mají vysoké IDs (13367+) — v order_by ID_FormDefEdit ASC
        # jsou na konci → jejich properties (ParentPageControl, ...) se
        # uřízly = TabSheety zůstávaly orphan, PageControly prázdné.
        # MCP query_table cap je 100000 (Phase B+4.4-fix), 10000 je bezpečný.
        props_result = self._call_mcp(
            "query_table",
            {
                "table": "EC_FormDefEditProperty",
                "filters": {
                    "ID_FormDefEdit": comp_ids,  # list → IN (...)
                    # NO Smazana filter -- viz komentář výše
                },
                "order_by": ["ID_FormDefEdit", "EditCislo"],
                "limit": 10000,
            },
        )

        # Index property po ID_FormDefEdit
        props_by_comp: dict[int, dict[str, str]] = {}
        if props_result and props_result.get("rows"):
            for prop_row in props_result["rows"]:
                comp_id = prop_row.get("ID_FormDefEdit")
                if comp_id is None:
                    continue
                key = prop_row.get("Property") or prop_row.get("PropertyFMX") or ""
                value = prop_row.get("Value") or prop_row.get("ValueFMX") or ""
                if not key:
                    continue
                props_by_comp.setdefault(comp_id, {})[key] = value

        # Připoj properties k components
        for c in components:
            c.properties = props_by_comp.get(c.id, {})

            # Phase A.4 (5.5.2026): orphan komponenty (cParent='', cFieldName='')
            # mají binding info v properties (FieldName, ParentName).
            # Diagnostika ukázala např. CheckBox #1717 cFieldName='', ale
            # property FieldName='PozadovatPrihlaseni'. Fallback z properties
            # na c_field_name aby render našel data binding.
            if not c.c_field_name:
                fname = (
                    c.properties.get("FieldName")
                    or c.properties.get("DataField")
                    or c.properties.get("cFieldName")
                    or ""
                )
                if fname:
                    c.c_field_name = fname

        # Phase B+6.10c (6.5.2026 večer): lookup-by-Name pro Delphi VCL hierarchy.
        # Délfi VCL ukládá Parent reference jako unique component Name
        # (např. "PageControl1"), ne jako c{id}. Pre-build name → id map
        # z properties.Name + zpřístupnit pro fallback níže.
        name_to_id: dict[str, int] = {}
        for c in components:
            name = (c.properties.get("Name") or "").strip()
            if name:
                name_to_id[name] = c.id

        # cParent fallback strategie (pokud cParent v EC_FormDefEdit prázdný).
        # Delphi VCL ukládá Parent reference v různých property keys podle
        # typu komponenty:
        #   TTabSheet → "ParentPageControl" (specifický pro tab containment)
        #   Obecné komponenty → "ParentName"
        #   Legacy → "Parent"
        # Marti's DB diagnostika 6.5.2026 večer: TabSheet 13367 měl
        # ParentPageControl="c13365" v EC_FormDefEditProperty (NE ParentName)
        # — bez tohoto fallbacku TabSheety zůstanou orphan a PageControly
        # prázdné v UI.
        #
        # Resolution priority:
        #   1. Property hodnota "c{id}" → použij přímo
        #   2. Property hodnota = Delphi Name → resolve přes name_to_id
        #   3. "Def" / unmatched → root form (true orphan)
        PARENT_PROPERTY_KEYS = ("ParentName", "ParentPageControl", "Parent")
        _fallback_stats = {"matched_cid": 0, "matched_name": 0, "unmatched": 0, "no_prop": 0}
        for c in components:
            if not c.c_parent:
                pname = ""
                pkey = ""
                for key in PARENT_PROPERTY_KEYS:
                    v = (c.properties.get(key) or "").strip()
                    if v:
                        pname = v
                        pkey = key
                        break
                if not pname:
                    _fallback_stats["no_prop"] += 1
                    continue
                # 1. c{id} formát (Phase A.5 existing)
                if pname.startswith("c") and pname[1:].isdigit():
                    c.c_parent = pname
                    _fallback_stats["matched_cid"] += 1
                # 2. Delphi Name lookup (Phase B+6.10c)
                elif pname in name_to_id:
                    c.c_parent = f"c{name_to_id[pname]}"
                    _fallback_stats["matched_name"] += 1
                # 3. 'Def' a unmatched zůstávají prázdné
                else:
                    _fallback_stats["unmatched"] += 1
                # Phase B+6.10c diag — jen pro hierarchické typy
                if c.typ in (4, 15, 16):  # RichEdit / PageControl / TabSheet
                    logger.info(
                        f"[parent_fallback] form={form_id} comp#{c.id} "
                        f"typ={c.typ} {pkey}={pname!r} → c_parent={c.c_parent!r}"
                    )

        # Diagnostika query_table truncation — pokud rows == limit, asi truncated
        _rows_received = len(props_result.get("rows", [])) if props_result else 0
        logger.info(
            f"[parent_fallback] form={form_id} stats={_fallback_stats} "
            f"name_to_id_size={len(name_to_id)} property_rows={_rows_received}"
            + (" ⚠ POSSIBLY TRUNCATED" if _rows_received >= 10000 else "")
        )

        logger.info(
            f"CentralaReader: form_id={form_id} -> "
            f"{len(components)} komponent, "
            f"{sum(len(c.properties) for c in components)} properties total, "
            f"{sum(1 for c in components if c.properties)} komponent s properties"
        )
        return components

    def execute_form_data(
        self, sql_select: str, row_id: int
    ) -> dict[str, Any] | None:
        """
        Vrátí data row pro jádro (substituce :ID = row_id v SQL_Select).

        Phase A omezení: MCP klient nemá raw SQL execute, jen tabulkové
        operace (query_table, get_row). Pro Phase A parsujeme SQL_Select
        a extrahujeme target tabulku — pak voláme get_row.

        Marti's reálný SQL_Select pro EC_FormDef.ID=6:
          SELECT [ID], [Cislo], [MenuText], ... FROM EC_CentralaMenu WHERE ID = :ID

        Tj. always single-row lookup po PK. Pro 95 % Centrála jádra to
        funguje. Phase B+ může přidat raw SQL execute tool do MCP serveru.
        """
        if not sql_select or not sql_select.strip():
            return None

        # Detekce dummy SQL (jádro bez dat — actions only / legend panel)
        sql_lower = sql_select.lower().strip()
        if "select top 1 1 from" in sql_lower or "select top 1 id from" in sql_lower:
            logger.info("CentralaReader: dummy SQL detected, vracím prázdná data")
            return {}

        # Parsuj target tabulku z "...FROM <table> WHERE ID = :ID"
        import re
        m = re.search(
            r"\bFROM\s+\[?(\w+)\]?\s+WHERE\s+ID\s*=\s*:ID\b",
            sql_select,
            re.IGNORECASE,
        )
        if not m:
            logger.warning(
                f"CentralaReader: SQL_Select pattern not recognized "
                f"(need 'FROM <table> WHERE ID = :ID'): {sql_select[:120]!r}"
            )
            return None

        table = m.group(1)
        # MCP get_row tool — single-row lookup po PK ID
        result = self._call_mcp("get_row", {"table": table, "id": row_id})
        if not result or not result.get("row"):
            logger.info(
                f"CentralaReader: {table}.ID={row_id} nenalezen "
                f"(get_row vrátil row=None)"
            )
            return None
        return result["row"]

    # ── Phase B: Tree (EC_CentralaMenu) + Přehled (EC_DELPHI_TabObecnyPrehled) ──

    def load_menu_tree(self) -> list[dict]:
        """
        Phase B (5.5.2026): Načti EC_CentralaMenu, build hierarchii podle
        NadrazeneMenu FK, sort by Poradi.

        Returns: list root uzlů (NadrazeneMenu IS NULL nebo 0), každý má
        children: [...] rekurzivně.

        Klíčové sloupce per uzel:
          - id
          - menu_text (display name v sidebaru)
          - nadrazene_menu (parent FK)
          - poradi (sort within parent)
          - ikona (TODO Phase B+1: emoji/SVG mapping)
          - cislo_def (FK na EC_DELPHI_TabObecnyPrehled.Cislo, NULL pro
            složkové uzly bez přehledu)
        """
        result = self._call_mcp(
            "query_table",
            {
                "table": "EC_CentralaMenu",
                "order_by": ["NadrazeneMenu", "Poradi", "ID"],
                "limit": 1000,  # MCP cap, EC_CentralaMenu typicky <500
            },
        )
        if not result or not result.get("rows"):
            return []

        nodes_by_id: dict[int, dict] = {}
        for row in result["rows"]:
            nid = row.get("ID")
            if nid is None:
                continue
            nodes_by_id[nid] = {
                "id": nid,
                "menu_text": row.get("MenuText") or f"#{nid}",
                "nadrazene_menu": row.get("NadrazeneMenu"),
                "poradi": row.get("Poradi") or 0,
                "ikona": row.get("Ikona"),
                "cislo_def": row.get("CisloDef"),
                "children": [],
            }

        # Build tree
        roots: list[dict] = []
        for node in nodes_by_id.values():
            parent_id = node["nadrazene_menu"]
            if parent_id and parent_id in nodes_by_id:
                nodes_by_id[parent_id]["children"].append(node)
            else:
                roots.append(node)

        # Sort children by poradi+id rekurzivně
        def sort_recurse(items: list[dict]) -> None:
            items.sort(key=lambda n: (n["poradi"], n["id"]))
            for n in items:
                sort_recurse(n["children"])

        sort_recurse(roots)
        return roots

    def load_prehled_meta(self, cislo: int) -> dict | None:
        """
        Phase B: Načti meta o přehledu (EC_DELPHI_TabObecnyPrehled WHERE Cislo=N).

        Returns dict s klíči: cislo, nazev, sql_select, id_edit, ... nebo None.
        """
        result = self._call_mcp(
            "query_table",
            {
                "table": "EC_DELPHI_TabObecnyPrehled",
                "filters": {"Cislo": cislo},
                "limit": 1,
            },
        )
        if not result or not result.get("rows"):
            return None
        row = result["rows"][0]
        # B+4.4 (5.5.2026): MaxRecords per přehled (Centrála 1 native limit).
        # Hodnota 0 nebo NULL = unlimited (Phase B+4.4: cap fallback v router).
        mr = row.get("MaxRecords")
        max_records = int(mr) if (mr is not None and int(mr) > 0) else None

        return {
            "cislo": row.get("Cislo"),
            "nazev": row.get("Nazev") or "",
            "sql_select": row.get("SQL_Select") or row.get("DefView") or "",
            "id_edit": row.get("ID_Edit"),  # FK na EC_FormDef.ID pro edit dialog
            "max_records": max_records,     # B+4.4: per-přehled limit z metadata
            "raw": row,
        }

    def execute_prehled_data(
        self, prehled_meta: dict, limit: int = 100
    ) -> dict:
        """
        Phase B (nástřel, no pagination/filter): spustí DefView SQL z přehledu.

        Phase B MVP: parsuje target tabulku z `FROM <table>` a volá
        query_table. Composite SQL (JOINs, WHERE podmínky) Phase B+1
        vyžaduje raw SQL execute v MCP serveru.

        Returns: {columns: [...], rows: [...], total: N}
        """
        sql_select = prehled_meta.get("sql_select", "")
        if not sql_select.strip():
            return {"columns": [], "rows": [], "total": 0, "warning": "no SQL"}

        import re
        m = re.search(r"\bFROM\s+\[?(\w+)\]?", sql_select, re.IGNORECASE)
        if not m:
            return {
                "columns": [],
                "rows": [],
                "total": 0,
                "warning": f"FROM table not parsed from SQL_Select: {sql_select[:120]!r}",
            }

        target_table = m.group(1)
        result = self._call_mcp(
            "query_table",
            {"table": target_table, "limit": limit},
        )
        if not result or not result.get("rows"):
            return {
                "columns": [],
                "rows": [],
                "total": 0,
                "warning": f"target table {target_table} empty or query failed",
            }

        rows = result["rows"]
        # Sloupce z prvního row (pořadí keys)
        columns = list(rows[0].keys()) if rows else []

        return {
            "columns": columns,
            "rows": rows,
            "total": len(rows),
            "target_table": target_table,
            "has_more": result.get("has_more", False),
        }

    # ── Phase A.5: Lookup display resolution ──────────────────────────

    def _get_lookup_view_meta(self, view_cislo: int) -> tuple[str, str] | None:
        """
        Načti přehled (EC_DELPHI_TabObecnyPrehled) podle Cislo.
        Vraci (target_table, default_display_field) nebo None.

        Cache per-instance: opakovaný lookup stejného přehledu se nezeptá
        SQL znova.
        """
        if not hasattr(self, "_view_meta_cache"):
            self._view_meta_cache = {}
        if view_cislo in self._view_meta_cache:
            return self._view_meta_cache[view_cislo]

        result = self._call_mcp(
            "query_table",
            {
                "table": "EC_DELPHI_TabObecnyPrehled",
                "filters": {"Cislo": view_cislo},
                "limit": 1,
            },
        )
        if not result or not result.get("rows"):
            self._view_meta_cache[view_cislo] = None
            return None

        view_row = result["rows"][0]
        sql_select = view_row.get("SQL_Select") or view_row.get("DefView") or ""

        # Parse target tabulku z "...FROM <table> WHERE..." nebo "...FROM <table>"
        import re
        m = re.search(
            r"\bFROM\s+\[?(\w+)\]?",
            sql_select,
            re.IGNORECASE,
        )
        target_table = m.group(1) if m else ""
        if not target_table:
            logger.warning(
                f"_get_lookup_view_meta: nelze parse FROM table z přehledu "
                f"#{view_cislo} SQL: {sql_select[:120]!r}"
            )
            self._view_meta_cache[view_cislo] = None
            return None

        meta = (target_table, "")  # default_display_field nepoužíváme zatím
        self._view_meta_cache[view_cislo] = meta
        return meta

    def lookup_display_value(
        self,
        view_cislo: int,
        lookup_field: str,
        fk_value: Any,
        display_field: str = "Nazev",
    ) -> str | None:
        """
        Vytáhni display string z lookup přehledu.

        Phase A.5: pro FormList komponenty s LookupView/LookupField/LookupDisplay
        properties. Cache per-instance.

        Returns: string (display value) nebo None pokud lookup selhal.
        """
        if fk_value is None or fk_value == "":
            return None

        if not hasattr(self, "_lookup_value_cache"):
            self._lookup_value_cache = {}
        cache_key = (view_cislo, lookup_field, str(fk_value), display_field)
        if cache_key in self._lookup_value_cache:
            return self._lookup_value_cache[cache_key]

        meta = self._get_lookup_view_meta(view_cislo)
        if meta is None:
            self._lookup_value_cache[cache_key] = None
            return None
        target_table, _ = meta

        # Query target table podle FK
        try:
            fk_int = int(fk_value)
        except (TypeError, ValueError):
            fk_int = fk_value  # nech original (může být string FK)

        result = self._call_mcp(
            "query_table",
            {
                "table": target_table,
                "filters": {lookup_field: fk_int},
                "columns": [display_field],
                "limit": 1,
            },
        )
        if not result or not result.get("rows"):
            self._lookup_value_cache[cache_key] = None
            return None

        row = result["rows"][0]
        display_value = row.get(display_field)
        result_str = str(display_value) if display_value is not None else None
        self._lookup_value_cache[cache_key] = result_str
        return result_str

    def list_lookup_options(
        self,
        form_id: int,
        field_name: str,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """
        Phase B+6.4 (5.5.2026): list všech possible lookup hodnot pro
        daný FormList/Combobox field v jádru.

        Použije EC_FormDefEdit + EC_FormDefEditProperty pro detection
        LookupView (přehled #) / LookupField (FK column) / LookupDisplay
        (display column). Pak query_table na target table přes
        _get_lookup_view_meta resolve.

        Returns: [{"value": fk_id, "label": "Display name"}, ...]
                 ordered by display column.
        """
        components = self.load_form_components(form_id)
        target_comp = None
        for c in components:
            if c.c_field_name == field_name and c.typ in (6, 7):
                target_comp = c
                break
        if not target_comp:
            return []

        view_str = (target_comp.properties.get("LookupView") or "").strip()
        lookup_field = (target_comp.properties.get("LookupField") or "").strip()
        display_field = (target_comp.properties.get("LookupDisplay") or "Nazev").strip()

        if not view_str or not view_str.isdigit() or not lookup_field:
            logger.info(
                f"list_lookup_options: form_id={form_id} field={field_name!r} — "
                f"chybí LookupView nebo LookupField property "
                f"(view={view_str!r}, field={lookup_field!r})"
            )
            return []
        view_cislo = int(view_str)

        meta = self._get_lookup_view_meta(view_cislo)
        if meta is None:
            return []
        target_table, _ = meta

        # Query target table — FK + display column. Bez Smazana filter
        # (ne všechny lookup tabulky mají soft-delete; pokud má, vrátí
        # i smazané, ale to je acceptable read-only browse).
        result = self._call_mcp(
            "query_table",
            {
                "table": target_table,
                "columns": [lookup_field, display_field],
                "order_by": [display_field],
                "limit": limit,
            },
        )
        if not result or not result.get("rows"):
            return []

        options: list[dict[str, Any]] = []
        for row in result["rows"]:
            fk = row.get(lookup_field)
            disp = row.get(display_field)
            if fk is None:
                continue
            options.append({
                "value": fk,
                "label": str(disp) if disp is not None else str(fk),
            })
        return options

    def enrich_data_with_lookups(
        self,
        data: dict[str, Any],
        components: list[FormComponent],
    ) -> dict[str, Any]:
        """
        Phase A.5: pro každý FormList (Typ=6) s lookup properties --
        resolveni FK value na display string. Zápis do data dict pod
        klíčem '_lookup_{cFieldName}' (preserve original FK pod orig klíč).

        Render pak v _render_formlist použije data['_lookup_{field}'] pokud
        existuje, jinak fallback na raw value.
        """
        enriched = dict(data)  # nezasahujeme do originálu
        # Phase A.5+ case-insensitive data lookup helper (Centrála data row
        # má klíče v různém case než FieldName property)
        data_lower = {k.lower(): v for k, v in data.items()}
        for c in components:
            if c.typ != 6:  # jen FormList
                continue
            field_name = c.c_field_name
            if not field_name:
                continue
            fk_value = data.get(field_name)
            if fk_value is None:
                fk_value = data_lower.get(field_name.lower())
            if fk_value is None:
                continue
            if fk_value is None or fk_value == "":
                continue

            # Properties config
            view_str = (c.properties.get("LookupView") or "").strip()
            lookup_field = (c.properties.get("LookupField") or "").strip()
            display_field = (c.properties.get("LookupDisplay") or "Nazev").strip()

            if not view_str or not view_str.isdigit() or not lookup_field:
                continue
            view_cislo = int(view_str)

            display_value = self.lookup_display_value(
                view_cislo=view_cislo,
                lookup_field=lookup_field,
                fk_value=fk_value,
                display_field=display_field,
            )
            if display_value:
                enriched[f"_lookup_{field_name}"] = display_value

        return enriched

    # ── debug helpers ──────────────────────────────────────────────

    def get_typ_name(self, typ: int) -> str:
        """Mapuje INT Typ na čitelný název (Label, Edit, GroupBox, ...)."""
        return TYP_NAMES.get(typ, f"Typ_{typ}")
