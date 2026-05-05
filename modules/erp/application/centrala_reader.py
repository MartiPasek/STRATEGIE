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
        props_result = self._call_mcp(
            "query_table",
            {
                "table": "EC_FormDefEditProperty",
                "filters": {
                    "ID_FormDefEdit": comp_ids,  # list → IN (...)
                    # NO Smazana filter -- viz komentář výše
                },
                "order_by": ["ID_FormDefEdit", "EditCislo"],
                "limit": 1000,  # MCP cap je 1000 per call
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

            # Plus cParent fallback z properties (ParentName) -- některé
            # orphan komponenty mají parent referenci v properties, ne v
            # EC_FormDefEdit.cParent. Hodnoty typu 'Def' (=root form) nebo
            # 'GroupBox_VzhledNazev' bychom měli umět vyhodnotit; pro Phase A.4
            # zatim jen pokud cParent je prázdný a properties má 'ParentName'
            # (mapping na c{id} bude až Phase A.5 -- potřebujeme parent name
            # registry napříč form, což chce další query).

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

    # ── debug helpers ──────────────────────────────────────────────

    def get_typ_name(self, typ: int) -> str:
        """Mapuje INT Typ na čitelný název (Label, Edit, GroupBox, ...)."""
        return TYP_NAMES.get(typ, f"Typ_{typ}")
