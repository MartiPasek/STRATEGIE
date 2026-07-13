"""
@@COREIMPORT — znovupoužitelný import jader z Centrály 1 (DB_EC) do STRATEGIE (fw.*)

Autor: Claude-24 (Kristý), 9. 7. 2026. Pilot: form 271 „Kalkulace jádro".

CÍL (Kristý): „takovýchhle kopií jader bude ještě spousta" → jeden příkaz místo
ručního klikání/SQL. Reusuje NATIVNÍ generátor polí (vytvorit_edit_jadro_2), takže
jádra vznikají stejně jako z UI („fw self edited" doctrine) — ne ručně šité INSERTy.

POUŽITÍ (přes bridge / diag_sql):
    @@COREIMPORT <ec_form_id> [<zdroj>] [--force]

    <ec_form_id>  ID formuláře v Centrále (EC_FormDef.ID), např. 271
    <zdroj>       (volitelné) odkud jádro čte data:
                    - název tabulky/view    → udělá  SELECT * FROM <zdroj>
                    - celý SELECT           → použije se tak jak je
                  když chybí → odvodí se z Centrála EC_FormDef.SQL_Select
    --force       přegenerovat komponenty od nuly (smaže stávající hierarchii)

    Příklad pilotu (hlavička jde ze stejného zdroje jako přehled „Kalkulace a nabídky"):
        @@COREIMPORT 271 tenant.oz_vy_nab

CO DĚLÁ (6 kroků, idempotentně podle fw.core.code):
    1. Přečte z Centrály (MCP, DB_EC) název formuláře + mapu popisků polí
       (EC_FormDefEditProperty: FieldName → Caption).
    2. Upsertne fw.core (code = slug názvu).
    3. Založí/aktualizuje edit-select: fw.data_set + fw.data_source + fw.data_source_op(edit).
    4. Zjistí sloupce zdroje (edit-select LIMIT 0) a spustí NATIVNÍ generátor polí
       (scripts/executable_artifacts/vytvorit_edit_jadro_2.py) → form + panely + edit pole.
    5. Domapuje popisky (caption) z Centrály na vygenerovaná pole (podle názvu sloupce).
    6. Vrátí souhrn (co vzniklo / co přibylo).

POZN. K NASAZENÍ: dispatch se přidá do modules/erp/api/router.py (funkce diag_sql),
vzorem @@VP / @@CENIK:
    if sql.upper().startswith("@@COREIMPORT"):
        from modules.erp.api.core_import import run_core_import
        return JSONResponse(run_core_import(sql[len("@@COREIMPORT"):].strip()))
"""
from __future__ import annotations

import io
import json
import os
import re
import contextlib
import runpy
import traceback
from pathlib import Path

from sqlalchemy import text as _t

# Cesta k nativnímu generátoru polí (reuse, ne duplikace).
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "scripts" / "executable_artifacts" / "vytvorit_edit_jadro_2.py"

# Centrála VLC formuláře jsou převážně PG-mirror / PG zdroje → default PG.
DEFAULT_DB_CONNECTION_ID = 1  # 1 = PostgreSQL (STRATEGIE)
# Číselníky formlistů žijí v Centrále (DB_EC, MSSQL) → data_set proti spojení 2.
CISELNIK_DB_CONNECTION_ID = 2  # 2 = eurosoft_db_ec / DB_EC (Centrála)

# Překlad Centrála typů na kódy, které editační renderer (design_forms.js)
# skutečně vykreslí jako plnohodnotný prvek. Bez překladu spadnou do
# „readonly text (?typ)". (Kristý 13.7.2026)
#   checkbox   → checkbox_modern     richedit*   → memo
#   dateedit   → date_modern         datetimeedit → date_modern
# formlist/combobox (potřebují číselník) a filelistbox (soubory) zatím NE —
# přijdou ve fázi 3/4 spolu s číselníky a soubory.
_RENDER_CODE_MAP = {
    "checkbox": "checkbox_modern",
    "richedit": "memo",
    "richeditor": "memo",
    "richeditorv1": "memo",
    "dateedit": "date_modern",
    "datetimeedit": "date_modern",
}


# ── pomocníci ────────────────────────────────────────────────────────────────

def _ec(sql: str) -> list[dict]:
    """DB_EC (Centrála) SELECT přes EUROSOFT MCP → list dictů. (vzor: kalkulace_engine)"""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP klient není dostupný (Centrálu nepřečtu)")
    raw = mcp.call_tool_sync(full_name="eurosoft_strategie_query_raw",
                             arguments={"sql": sql, "db_name": "DB_EC"},
                             conversation_id=None)
    res = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(res, dict):
        if res.get("ok") is False:
            raise RuntimeError("MCP EC dotaz selhal: %s" % (res.get("message") or res.get("error")))
        return res.get("rows") or []
    return res if isinstance(res, list) else []


def _slug(nazev: str) -> str:
    """„Kalkulace jádro" → „kalkulace_jadro" (bez diakritiky, ascii, snake_case)."""
    import unicodedata
    s = unicodedata.normalize("NFKD", nazev or "").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return s or "core"


def _comp_type_id(s, code: str) -> int:
    """fw.comp_type.id podle code (form/panel/edit…). Nehardcodujeme čísla."""
    row = s.execute(_t("SELECT id FROM fw.comp_type WHERE code = :c"), {"c": code}).first()
    if not row:
        raise RuntimeError(f"fw.comp_type '{code}' neexistuje")
    return int(row[0])


def _read_centrala(ec_form_id: int) -> dict:
    """Z Centrály: název formuláře, SQL_Select a KOMPLETNÍ strom komponent.

    Komponenty (EC_FormDefEdit, Smazana=0) + pivot properties:
    ParentName ('Def'=form, 'Footer'=patička, 'c<ID>'=komponenta), Caption,
    FieldName, Top/Left (pozice → pořadí). Typ (int) mapuje na
    fw.comp_type.centrala_id.
    """
    hdr = _ec(f"SELECT ID, Nazev, CAST(SQL_Select AS nvarchar(max)) AS sqltext "
              f"FROM dbo.EC_FormDef WHERE ID = {int(ec_form_id)}")
    if not hdr:
        raise RuntimeError(f"EC_FormDef.ID={ec_form_id} v Centrále neexistuje")
    nazev = (hdr[0].get("Nazev") or "").strip() or f"core_{ec_form_id}"
    sqltext = hdr[0].get("sqltext") or ""

    comps = _ec(
        "SELECT e.ID AS cid, e.Typ AS typ, "
        "MAX(CASE WHEN P.Property='ParentName' THEN P.Value END) AS par, "
        "MAX(CASE WHEN P.Property='Caption' THEN COALESCE(NULLIF(P.Value,''),P.ValueFMX) END) AS cap, "
        "MAX(CASE WHEN P.Property='FieldName' THEN P.Value END) AS fld, "
        "MAX(CASE WHEN P.Property='Top' THEN P.Value END) AS t, "
        "MAX(CASE WHEN P.Property='Left' THEN P.Value END) AS l, "
        "MAX(CASE WHEN P.Property='Width' THEN P.Value END) AS w, "
        "MAX(CASE WHEN P.Property='Align' THEN P.Value END) AS align, "
        "MAX(CASE WHEN P.Property='PageIndex' THEN P.Value END) AS pgidx, "
        # formlist → lookup (Kristý 13.7.): číselník + zobrazovací/uložený sloupec
        # + volitelný kaskádový filtr (FilterCondition, např. 'IDOrg = :IDOrg').
        "MAX(CASE WHEN P.Property='LookupView' THEN P.Value END) AS lv, "
        "MAX(CASE WHEN P.Property='LookupField' THEN P.Value END) AS lf, "
        "MAX(CASE WHEN P.Property='LookupDisplay' THEN P.Value END) AS ld, "
        "MAX(CASE WHEN P.Property='FilterCondition' THEN COALESCE(NULLIF(P.Value,''),P.ValueFMX) END) AS fc "
        f"FROM dbo.EC_FormDefEdit e "
        f"LEFT JOIN dbo.EC_FormDefEditProperty P ON P.ID_FormDefEdit = e.ID "
        f"WHERE e.ID_Form = {int(ec_form_id)} AND e.Smazana = 0 "
        "GROUP BY e.ID, e.Typ"
    )
    # alias mapa z Centrála SQL: "X.CisloKalkulace AS Kalkulace" → kalkulace→cislokalkulace
    alias_base: dict[str, str] = {}
    for m in re.finditer(r"([\w\[\]\._]+)\s+AS\s+(\w+)", sqltext, re.IGNORECASE):
        base = m.group(1).split(".")[-1].strip("[]_")
        alias_base[m.group(2).lower()] = base.lower()
    return {"nazev": nazev, "sql_select": sqltext,
            "comps": comps, "alias_base": alias_base}


def _match_field(fld: str, src_cols: list[str], alias_base: dict, user_map: dict) -> str | None:
    """Namapuj Centrála FieldName na sloupec zdroje.

    Pořadí: (1) --map od uživatele, (2) přesná shoda (ci), (3) přes alias
    z Centrála SQL (alias→základní sloupec), (4) prefix shoda (≥8 znaků,
    kryje oříznuté názvy view — OznPrjZakazni vs OznPrjZakaznik).
    """
    f = (fld or "").strip().lower()
    if not f:
        return None
    by_lower = {c.lower(): c for c in src_cols}
    if f in user_map:
        return by_lower.get(user_map[f].lower())
    if f in by_lower:
        return by_lower[f]
    base = alias_base.get(f)
    if base and base in by_lower:
        return by_lower[base]
    cand = base or f
    if len(cand) >= 8:
        for cl, orig in by_lower.items():
            if cl.startswith(cand) or cand.startswith(cl):
                return orig
    return None


def _layout_from_centrala(s, core_id: int, cen: dict, src_cols: list[str],
                          user_map: dict) -> dict:
    """Přenese rozložení z Centrály 1:1 — VČETNĚ Delphi align dokování.

    Delphi align (alTop/alLeft/alClient/…) se v STRATEGII mapuje NATIVNĚ na
    layout.align (renderer _buildAlignLayout: top/bottom pásy + middle row
    left|client|right). Proto reprodukujeme CELÝ strom kontejnerů z Centrály:

      • type-12 s captionem   → fw groupbox  (viditelný rámeček + label)
      • type-12 bez captionu   → fw panel     (neviditelný strukturální wrap,
                                               border_mode=none) — nese jen align
      • align → layout.align   (altop→top, alleft→left, alclient→client, …)
      • Width u alLeft/alRight → layout.max_width (renderer = cílová šířka pásu)
      • Height u alTop/alBottom→ layout.height (dopočítá se z výšky gridů uvnitř)

    Pole se zařadí do svého SKUTEČNÉHO kontejneru z Centrály (ne do nejbližšího
    captioned). Kódové gridy (typ 11/21) a tlačítka (typ 8) se nepřenáší (logika
    je v Delphi) — groupboxy gridů zůstávají jako placeholder / už dodané gridy.

    Pojistka reuse (Kristý 10.7.): kontejner s AKTIVNÍMI dětmi (např. embedded
    grid dodaný po importu) se re-runem NEDEAKTIVUJE.
    """
    rep = {"groupboxes": 0, "fields_mapped": 0, "fields_hidden": 0,
           "grids_skipped": 0, "buttons_skipped": 0, "unmatched": []}

    # comp_type mapy: centrala_id → (id, code, kind) + code → id
    trows = s.execute(_t(
        "SELECT id, code, kind, centrala_id FROM fw.comp_type")).mappings().all()
    by_centrala = {int(r["centrala_id"]): r for r in trows if r["centrala_id"] is not None}
    by_code = {r["code"]: r for r in trows}
    for _need in ("groupbox", "panel"):
        if _need not in by_code:
            raise RuntimeError(f"fw.comp_type '{_need}' nenalezen")

    # vygenerované komponenty jádra: root + panely + pole (name=sloupec)
    gen = s.execute(_t(
        "SELECT id, type_id, name, caption, parent_comp_def_id, root "
        "FROM fw.comp_def WHERE core_id=:c"), {"c": core_id}).mappings().all()
    root = next((g for g in gen if g["root"]), None)
    if not root:
        raise RuntimeError(f"core {core_id} nemá root komponentu (spusť generátor)")
    fields_by_name = {(g["name"] or "").lower(): g for g in gen
                      if g["name"] and not g["root"]}
    # klientský panel = rodič vygenerovaných polí (nejčastější parent)
    parents = {}
    for g in gen:
        if g["name"] and (g["name"] or "").lower() in {c.lower() for c in src_cols}:
            parents[g["parent_comp_def_id"]] = parents.get(g["parent_comp_def_id"], 0) + 1
    client_panel_id = max(parents, key=parents.get) if parents else root["id"]

    # strom Centrály
    comps = cen["comps"]
    def as_int(v, d=0):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return d
    nodes = {int(c["cid"]): c for c in comps}
    def parent_key(c):
        p = (c.get("par") or "").strip()
        if p.lower().startswith("c") and p[1:].isdigit():
            return int(p[1:])
        return p or "Def"

    # Delphi align → STRATEGIE layout.align. alNone/neznámé → None (default client).
    ALIGN_MAP = {"altop": "top", "albottom": "bottom", "alleft": "left",
                 "alright": "right", "alclient": "client"}
    def map_align(a):
        return ALIGN_MAP.get((a or "").strip().lower())

    # hloubka v Centrála stromu (kvůli parent-first vytváření kontejnerů)
    def depth_of(cid):
        d, cur, seen = 0, cid, set()
        while isinstance(cur, int) and cur in nodes and cur not in seen:
            seen.add(cur)
            cur = parent_key(nodes[cur])
            d += 1
        return d

    # ── 1) reprodukce stromu kontejnerů: groupbox/panel (12,13) + pagecontrol (15)
    #      + tabsheet (16), parent-first. ─────────────────────────────────────────
    for _need in ("pagecontrol", "tabsheet"):
        if _need not in by_code:
            raise RuntimeError(f"fw.comp_type '{_need}' nenalezen")
    CONT_TYPS = (12, 13, 15, 16)
    cont_ids = [int(c["cid"]) for c in comps if int(c["typ"]) in CONT_TYPS]
    cont_set = set(cont_ids)

    # tab (16) → pagecontrol (15): Centrála tu vazbu neukládá (prázdný parent),
    # ale jde dopočítat z PageIndex. Každý pagecontrol dostane souvislou řadu tabů
    # 0,1,2,… (mělčí/hlavní pagecontrol bere první); duplicitní index → vnořený.
    pagectrls = sorted([cid for cid in cont_ids if int(nodes[cid]["typ"]) == 15],
                       key=lambda cid: (depth_of(cid), cid))
    tabs = [cid for cid in cont_ids if int(nodes[cid]["typ"]) == 16]
    tab_pc: dict[int, int] = {}
    _unassigned = sorted(tabs, key=lambda cid: (as_int(nodes[cid].get("pgidx")), cid))
    for _pc in pagectrls:
        _nxt = 0
        for _ts in list(_unassigned):
            if as_int(nodes[_ts].get("pgidx")) == _nxt:
                tab_pc[_ts] = _pc
                _unassigned.remove(_ts)
                _nxt += 1
    for _ts in _unassigned:            # zbytek (kdyby něco) → první pagecontrol
        if pagectrls:
            tab_pc[_ts] = pagectrls[0]

    def eff_parent(cid):
        n = nodes[cid]
        if int(n["typ"]) == 16:        # tabsheet → jeho pagecontrol (heuristika)
            return tab_pc.get(cid)
        return parent_key(n)           # ostatní → skutečný Centrála rodič

    def eff_depth(cid):
        d, cur, seen = 0, cid, set()
        while isinstance(cur, int) and cur in cont_set and cur not in seen:
            seen.add(cur)
            cur = eff_parent(cur)
            d += 1
        return d

    def _type_code_of(typ, cap):
        if typ == 15:
            return "pagecontrol"
        if typ == 16:
            return "tabsheet"
        if typ == 13:
            return "panel"
        return "groupbox" if cap else "panel"        # typ 12

    def _name_of(typ, cid, cap):
        if typ == 15:
            return "pc_centrala_%d" % cid
        if typ == 16:
            return "tab_centrala_%d" % cid
        if typ == 13 or (typ == 12 and not cap):
            return "panel_centrala_%d" % cid
        return "gb_centrala_%d" % cid

    cont_map: dict[int, int] = {}          # Centrála cid → fw.comp_def.id
    cont_meta: dict[int, dict] = {}         # fw.comp_def.id → {align, cen_h}
    containers = sorted(
        [nodes[c] for c in cont_ids],
        key=lambda c: (eff_depth(int(c["cid"])), as_int(c.get("t")), as_int(c.get("l"))))
    for i, gb in enumerate(containers):
        cid = int(gb["cid"])
        typ = int(gb["typ"])
        cap = (gb.get("cap") or "").strip()
        al = map_align(gb.get("align"))
        type_code = _type_code_of(typ, cap)
        name = _name_of(typ, cid, cap)

        # rodič = efektivní rodič-kontejner (tab→pagecontrol; jinak Centrála rodič),
        # pokud reprodukovaný; jinak klientský panel.
        ep = eff_parent(cid)
        parent_id = cont_map.get(ep) if isinstance(ep, int) else None
        if not parent_id:
            parent_id = client_panel_id

        # layout dle typu
        layout_d = {}
        if typ == 15:                       # pagecontrol = kontejner záložek, vyplní
            layout_d["align"] = al or "client"
        elif typ == 16:                     # tabsheet = stránka, caption = titulek
            if cap:
                layout_d["label"] = cap
        else:                               # groupbox / panel
            if cap:
                layout_d["label"] = cap
                layout_d["border_mode"] = "top"
            if al:
                layout_d["align"] = al
            wv = as_int(gb.get("w"))
            if al in ("left", "right") and wv > 0:
                layout_d["max_width"] = wv
        layout = json.dumps(layout_d, ensure_ascii=False)

        # obsahuje jen gridy? → placeholder (neaktivní) pro fázi 2
        child_typs = [int(n["typ"]) for n in comps if parent_key(n) == cid]
        only_grids = bool(child_typs) and all(t in (11, 21) for t in child_typs)

        # idempotence: najdi existující podle libovolného dřívějšího jména pro cid
        cand_names = ["gb_centrala_%d" % cid, "panel_centrala_%d" % cid,
                      "pc_centrala_%d" % cid, "tab_centrala_%d" % cid]
        row = s.execute(_t(
            "SELECT id FROM fw.comp_def WHERE core_id=:c AND name = ANY(:ns)"),
            {"c": core_id, "ns": cand_names}).first()
        if row:
            gb_id = int(row[0])
            has_active_child = s.execute(_t(
                "SELECT EXISTS(SELECT 1 FROM fw.comp_def "
                "WHERE parent_comp_def_id=:g AND is_active=true)"),
                {"g": gb_id}).scalar()
            act = (not only_grids) or bool(has_active_child)
            s.execute(_t(
                "UPDATE fw.comp_def SET type_id=:tid, name=:n, caption=:cap, "
                "sort_order=:so, is_active=:act, layout=CAST(:lay AS jsonb), "
                "parent_comp_def_id=:par WHERE id=:id"),
                {"tid": by_code[type_code]["id"], "n": name, "cap": cap or None,
                 "so": (i + 1) * 10, "act": act, "lay": layout,
                 "par": parent_id, "id": gb_id})
        else:
            gb_id = int(s.execute(_t(
                "INSERT INTO fw.comp_def (core_id, type_id, name, caption, layout, "
                "is_active, sort_order, parent_comp_def_id, region_slot, "
                "created_by_text, updated_by_text) "
                "VALUES (:c, :t, :n, :cap, CAST(:lay AS jsonb), :act, :so, :par, 'main', "
                "'Claude-24 @@COREIMPORT', 'Claude-24 @@COREIMPORT') RETURNING id"),
                {"c": core_id, "t": by_code[type_code]["id"], "n": name,
                 "cap": cap or None, "lay": layout, "act": not only_grids,
                 "so": (i + 1) * 10, "par": parent_id}).scalar())
        cont_map[cid] = gb_id
        cont_meta[gb_id] = {"align": al, "cen_h": as_int(gb.get("h"))}
        rep["groupboxes"] += 1

    # nejbližší reprodukovaný kontejner (jakýkoli type-12) nad komponentou
    def resolved_container(cid):
        seen, cur = set(), cid
        while isinstance(cur, int) and cur in nodes and cur not in seen:
            seen.add(cur)
            if cur in cont_map:
                return cur
            cur = parent_key(nodes[cur])
        return None

    # ── 2) pole: mapování FieldName → sloupec, caption, kontejner, pořadí, typ ──
    mapped_cols: set[str] = set()
    for c in comps:
        typ = int(c["typ"])
        if typ in (12, 13, 15, 16):
            continue                       # kontejnery (groupbox/panel/pagecontrol/tabsheet) už hotové
        if typ in (11, 21):
            rep["grids_skipped"] += 1
            continue
        if typ == 8:
            rep["buttons_skipped"] += 1
            continue
        fld = (c.get("fld") or "").strip()
        if not fld:
            continue
        col = _match_field(fld, src_cols, cen["alias_base"], user_map)
        if not col:
            rep["unmatched"].append(fld)
            continue
        g = fields_by_name.get(col.lower())
        if not g:
            continue
        cont_cid = resolved_container(parent_key(c))
        parent_id = cont_map.get(cont_cid, client_panel_id)
        cap = (c.get("cap") or "").strip() or col
        so = as_int(c.get("t")) * 10000 + as_int(c.get("l"))
        # typ přes centrala_id → renderer-podporovaný kód (Kristý 13.7.):
        # Centrála typ (checkbox/richedit/dateedit…) přeložit na kód, který
        # editační renderer skutečně vykreslí (checkbox_modern/memo/date_modern…),
        # jinak spadne do „readonly text (?typ)". Neznámý překlad → původní typ.
        new_type = None
        ct = by_centrala.get(typ)
        if ct and ct["kind"] == "leaf" and ct["code"] not in ("grid", "gridpoldoklad", "button"):
            tgt = by_code.get(_RENDER_CODE_MAP.get(ct["code"], ct["code"]))
            new_type = int((tgt or ct)["id"])
        # Šířka z Centrály (bod 2, Kristý 10.7.): Width (px) → layout.max_width.
        # Merge do stávajícího layoutu, ať nepřepíšu always_new_row apod.
        wv = as_int(c.get("w"))
        set_sql = "caption=:cap, parent_comp_def_id=:par, sort_order=:so, is_active=true"
        params = {"cap": cap, "par": parent_id, "so": so, "id": g["id"]}
        if new_type:
            set_sql += ", type_id=:tid"
            params["tid"] = new_type
        if wv and wv > 0:
            set_sql += (", layout = COALESCE(layout,'{}'::jsonb) "
                        "|| jsonb_build_object('max_width', :mw)")
            params["mw"] = wv
        s.execute(_t("UPDATE fw.comp_def SET " + set_sql + " WHERE id=:id"), params)
        mapped_cols.add(col.lower())
        rep["fields_mapped"] += 1

    # ── 3) výška alTop/alBottom kontejnerů = max výška gridu uvnitř + rámeček ───
    # (top/bottom pás v renderu potřebuje flex-basis na svislé ose; jinak by
    #  se pás s embedded gridem uvnitř sesypal. Dopočítá se rekurzivně z gridů.)
    CHROME = 64
    grid_h = {}
    try:
        rows = s.execute(_t(
            "WITH RECURSIVE tree AS ("
            "  SELECT id AS anc, id AS node FROM fw.comp_def WHERE core_id=:core "
            "  UNION ALL "
            "  SELECT t.anc, ch.id FROM tree t "
            "    JOIN fw.comp_def ch ON ch.parent_comp_def_id = t.node) "
            "SELECT t.anc AS anc, MAX((d.layout->>'height_px')::int) AS maxh "
            "FROM tree t JOIN fw.comp_def d ON d.id = t.node "
            "JOIN fw.comp_type ct ON ct.id = d.type_id "
            "WHERE ct.code IN ('grid','grid_modern','gridpoldoklad','nested_grid') "
            "  AND (d.layout->>'height_px') ~ '^[0-9]+$' "
            "GROUP BY t.anc"), {"core": core_id}).mappings().all()
        grid_h = {int(r["anc"]): int(r["maxh"]) for r in rows if r["maxh"] is not None}
    except Exception:
        grid_h = {}
    for fw_id, meta in cont_meta.items():
        if meta["align"] not in ("top", "bottom"):
            continue
        h = grid_h.get(fw_id)
        if h:
            h = h + CHROME
        else:
            h = max(meta["cen_h"], 120)    # fallback: Centrála výška (Delphi px ≈ web)
        s.execute(_t(
            "UPDATE fw.comp_def SET layout = COALESCE(layout,'{}'::jsonb) "
            "|| jsonb_build_object('height', :h) WHERE id=:id"),
            {"h": int(h), "id": fw_id})

    # ── 4) pole zdroje, která na Centrála formuláři nejsou → schovat ───────────
    for name_l, g in fields_by_name.items():
        if name_l in mapped_cols:
            continue
        if name_l not in {c.lower() for c in src_cols}:
            continue  # ne-datová komponenta (panel apod.)
        s.execute(_t("UPDATE fw.comp_def SET is_active=false WHERE id=:id"),
                  {"id": g["id"]})
        rep["fields_hidden"] += 1
    return rep


def _inject_ciselnik_filter(base_sql: str, filter_cond: str | None):
    """Zabuduje Centrála FilterCondition (např. 'IDOrg = :IDOrg') do číselník SQL
    jako TOLERANTNÍ filtr (když se param nepošle → NULL → vrátí vše).

    Runner (_normalize_params) chybějící bind auto-defaultuje na None, takže
    `:IDOrg IS NULL OR …` je bezpečné i bez předaného filtru. Obalíme do
    poddotazu (generické, nezávislé na aliasech), s odstřižením koncového
    ORDER BY (MSSQL poddotaz ho nepovolí bez TOP).

    Vrací (sql, param, field). Když filtr není → (base_sql, None, None).
    param = jméno SQL bind proměnné (:param). field = sloupec záznamu editačního
    formuláře, jehož hodnota se do filtru pošle (default = param).
    """
    if not filter_cond or ":" not in filter_cond:
        return base_sql, None, None
    m = re.search(r":(\w+)", filter_cond)
    if not m:
        return base_sql, None, None
    param = m.group(1)
    lhs = filter_cond.split("=", 1)[0].strip()
    col = lhs.split(".")[-1].strip("[]_ ") or param
    b = re.sub(r"(?is)\border\s+by\b.*$", "", base_sql).strip().rstrip(";")
    wrapped = (f"SELECT * FROM (\n{b}\n) _cis "
               f"WHERE (:{param} IS NULL OR _cis.[{col}] = :{param})")
    return wrapped, param, (col or param)


def _ensure_ciselnik(s, view: int, filter_cond: str | None) -> dict:
    """Idempotentně založí číselník (fw.data_set + fw.data_source + op select)
    z Centrála EC_FormDef.SQL_Select podle LookupView. Vrací {code, param, field}.

    code = f'ciselnik_{view}'. SQL se čte ŽIVĚ z Centrály (reuse — žádná ruční
    kopie). db_connection_id = 2 (DB_EC). Filtr (FilterCondition) se zabuduje
    tolerantně (viz _inject_ciselnik_filter), takže jeden data_set slouží
    filtrovaně i nefiltrovaně.
    """
    view = int(view)
    code = f"ciselnik_{view}"
    hdr = _ec("SELECT CAST(SQL_Select AS nvarchar(max)) AS sqltext "
              f"FROM dbo.EC_FormDef WHERE ID = {view}")
    base_sql = (hdr[0].get("sqltext") if hdr else None) or ""
    if not base_sql.strip():
        raise RuntimeError(f"číselník LookupView={view}: EC_FormDef nemá SQL_Select")
    sql_text, param, field = _inject_ciselnik_filter(base_sql, filter_cond)

    dset_row = s.execute(_t("SELECT id FROM fw.data_set WHERE code=:c"), {"c": code}).first()
    if dset_row:
        dset_id = int(dset_row[0])
        s.execute(_t("UPDATE fw.data_set SET sql_text=:sql, db_connection_id=:db WHERE id=:id"),
                  {"sql": sql_text, "db": CISELNIK_DB_CONNECTION_ID, "id": dset_id})
    else:
        dset_id = int(s.execute(_t(
            "INSERT INTO fw.data_set (code, version, sql_text, db_connection_id, status, is_system, is_immutable) "
            "VALUES (:c, 1, :sql, :db, 'active', false, false) RETURNING id"
        ), {"c": code, "sql": sql_text, "db": CISELNIK_DB_CONNECTION_ID}).scalar())

    dsrc_row = s.execute(_t("SELECT id FROM fw.data_source WHERE code=:c"), {"c": code}).first()
    if dsrc_row:
        dsrc_id = int(dsrc_row[0])
    else:
        dsrc_id = int(s.execute(_t(
            "INSERT INTO fw.data_source (code, version, name, status, is_system, is_immutable) "
            "VALUES (:c, 1, :n, 'active', false, false) RETURNING id"
        ), {"c": code, "n": f"Číselník {view}"}).scalar())

    op_row = s.execute(_t(
        "SELECT id FROM fw.data_source_op WHERE data_source_id=:ds AND operation_kind='select'"
    ), {"ds": dsrc_id}).first()
    if op_row:
        s.execute(_t("UPDATE fw.data_source_op SET data_set_id=:dset WHERE id=:id"),
                  {"dset": dset_id, "id": int(op_row[0])})
    else:
        s.execute(_t(
            "INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, sort_order, is_default) "
            "VALUES (:ds, :dset, 'select', 'default', 10, true)"
        ), {"ds": dsrc_id, "dset": dset_id})
    return {"code": code, "dsrc_id": dsrc_id, "param": param, "field": field}


def _wire_formlists(s, core_id: int, cen: dict, user_map: dict) -> dict:
    """Chirurgicky přepne EXISTUJÍCÍ formlist komponenty jádra na lookup a založí
    jim číselníky z Centrály. NESPOUŠTÍ generátor, NETVOŘÍ nová pole, nesahá na
    kontejnery — dopad = výhradně formlist pole tohoto core_id.

    Pro každou Centrála komponentu Typ=6 (formlist) s LookupView:
      1. namapuj FieldName → existující komponentu jádra (stejná logika jako
         layout: přesná/alias/prefix shoda proti názvům komponent),
      2. založ/aktualizuj číselník (data_set/source/op) z EC_FormDef[LookupView],
      3. přepni komponentu na comp_type=lookup + layout (data_source_code,
         lookup_id_field, lookup_display_field, [lookup_filter_param/field]),
         nastav data_source_id.
    """
    rep = {"formlists_wired": 0, "ciselniky": [], "unmatched": [], "details": []}
    trows = s.execute(_t("SELECT id, code FROM fw.comp_type")).mappings().all()
    by_code = {r["code"]: int(r["id"]) for r in trows}
    if "lookup" not in by_code:
        raise RuntimeError("fw.comp_type 'lookup' nenalezen")
    lookup_tid = by_code["lookup"]

    gen = s.execute(_t(
        "SELECT id, name, root FROM fw.comp_def WHERE core_id=:c"), {"c": core_id}).mappings().all()
    comp_names = [(g["name"] or "") for g in gen if g["name"] and not g["root"]]
    by_name = {(g["name"] or "").lower(): g for g in gen if g["name"] and not g["root"]}

    for c in cen["comps"]:
        if int(c.get("typ") or 0) != 6:
            continue
        lv = (c.get("lv") or "").strip()
        if not lv:
            continue
        fld = (c.get("fld") or "").strip()
        col = _match_field(fld, comp_names, cen["alias_base"], user_map)
        g = by_name.get((col or "").lower()) if col else None
        if not g:
            rep["unmatched"].append(fld or f"lv={lv}")
            continue
        try:
            cis = _ensure_ciselnik(s, int(lv), c.get("fc"))
        except Exception as _e:
            rep["details"].append(f"{fld}: číselník {lv} chyba: {str(_e)[:120]}")
            continue
        lay = {"data_source_code": cis["code"]}
        lf = (c.get("lf") or "").strip()
        ld = (c.get("ld") or "").strip()
        if lf:
            lay["lookup_id_field"] = lf
        if ld:
            lay["lookup_display_field"] = ld
        if cis["param"]:
            lay["lookup_filter_param"] = cis["param"]
            lay["lookup_filter_field"] = cis["field"]
        s.execute(_t(
            "UPDATE fw.comp_def SET type_id=:tid, data_source_id=:ds, "
            "layout = COALESCE(layout,'{}'::jsonb) || CAST(:lay AS jsonb) "
            "WHERE id=:id"),
            {"tid": lookup_tid, "ds": cis["dsrc_id"],
             "lay": json.dumps(lay, ensure_ascii=False), "id": g["id"]})
        rep["formlists_wired"] += 1
        if cis["code"] not in rep["ciselniky"]:
            rep["ciselniky"].append(cis["code"])
        rep["details"].append(
            f"{g['name']} → lookup ({cis['code']}, val={lf or '?'}, disp={ld or '?'}"
            + (f", filtr {cis['param']}←{cis['field']}" if cis["param"] else "") + ")")
    return rep


def _source_to_select(zdroj: str | None, centrala_sql: str) -> str:
    """Zdroj → čistý edit-select (systém ho obalí `WHERE [ID]=`)."""
    if zdroj:
        z = zdroj.strip().rstrip(";")
        if re.match(r"(?is)^\s*select\b", z):
            return z
        # jen název tabulky/view
        return f"SELECT * FROM {z}"
    # fallback: z Centrály (odstraníme koncové WHERE ...=:ID, systém si přidá vlastní)
    s = re.sub(r"(?is)\bwhere\b\s+[^;]*?:id[^;]*$", "", centrala_sql).strip().rstrip(";")
    return s


def _fields_of(s, select_sql: str) -> list[str]:
    """Sloupce zdroje (spustí edit-select s LIMIT 0)."""
    probe = f"SELECT * FROM ({select_sql}) _q LIMIT 0"
    res = s.execute(_t(probe))
    return list(res.keys())


def _ensure_lower_id(select_sql: str, cols: list[str]) -> str:
    """Zajistí, že edit-select má sloupec `id` (malé) — PG obal formuláře skládá
    `SELECT * FROM (<sql>) sub WHERE id = <row>`. Naše zrcadla Centrály mají ale
    klíč v PascalCase (`ID`), takže malé `id` neexistuje → formulář se načte prázdný.
    Když sloupec přesně `id` chybí, ale existuje `ID`/`Id`, doplní alias.
    """
    if any(c == "id" for c in cols):
        return select_sql
    idc = next((c for c in cols if c.lower() == "id"), None)
    if not idc:
        return select_sql  # zdroj nemá ID sloupec — neřešíme
    return f'SELECT sub.*, sub."{idc}" AS id FROM ({select_sql}) sub'


def _run_generator(core_id: int, fields: list[str], force: bool) -> str:
    """Spustí NATIVNÍ generátor polí v procesu (reuse vytvorit_edit_jadro_2).

    Generátor čte SANDBOX_CONTEXT (JSON) a staví form+panely+edit pole. Běží přes
    runpy jako __main__; na konci volá sys.exit → chytáme SystemExit.
    """
    if not GENERATOR_PATH.exists():
        raise RuntimeError(f"Generátor nenalezen: {GENERATOR_PATH}")
    ctx = {"coreId": int(core_id), "force": bool(force)}
    if fields:
        ctx["fields"] = fields
    # Generátor čeká env jako v sandboxu: SANDBOX_CONTEXT + STRATEGIE_DATA_DB_URL.
    # DB URL bereme stejně jako python_runner (Pydantic settings, ne shell env).
    from core.config import settings as _cfg
    db_url = getattr(_cfg, "database_data_url", "") or ""
    if not db_url:
        raise RuntimeError("core.config.settings.database_data_url je prázdné")
    prev = {k: os.environ.get(k) for k in ("SANDBOX_CONTEXT", "STRATEGIE_DATA_DB_URL")}
    os.environ["SANDBOX_CONTEXT"] = json.dumps(ctx, ensure_ascii=True)
    os.environ["STRATEGIE_DATA_DB_URL"] = db_url
    buf = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(str(GENERATOR_PATH), run_name="__main__")
    except SystemExit as e:
        exit_code = int(e.code) if isinstance(e.code, int) else (0 if not e.code else 1)
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    out = buf.getvalue()
    if exit_code != 0:
        raise RuntimeError(f"generátor selhal (exit {exit_code}): {out[-600:]}")
    return out


# ── hlavní vstup ─────────────────────────────────────────────────────────────

def run_core_import(arg: str) -> dict:
    """Parsuje '<ec_form_id> [<zdroj>] [--force] [--map A=B,C=D] [--bind <grid_code>] [--rebind]'.

    --map    = ruční mapování Centrála FieldName → sloupec zdroje.
    --bind <grid_code> = po importu navázat nové jádro na přehled <grid_code>
                         (= fw.core.code přehledu) → edit se pak otevře z řádku.
    --rebind = povolit přepis existující vazby (pojistka: bez něj se vazba
               NEpřepíše, jen se nahlásí, že přehled už jádro má).
    """
    try:
        user_map: dict[str, str] = {}
        mm = re.search(r"--map\s+(\S+)", arg)
        if mm:
            for pair in mm.group(1).split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    user_map[k.strip().lower()] = v.strip()
            arg = arg.replace(mm.group(0), "")
        # --bind <grid_code> (navázání na přehled) — vytáhnout před split ec/zdroj
        bind_grid = None
        bm = re.search(r"--bind\s+(\S+)", arg)
        if bm:
            bind_grid = bm.group(1).strip()
            arg = arg.replace(bm.group(0), "")
        rebind = "--rebind" in arg
        arg = arg.replace("--rebind", "")
        # --formlists = jen chirurgické přepnutí formlist polí na lookup + číselníky
        # (nespouští generátor, netvoří pole; bezpečné pro už hotová jádra).
        formlists_only = "--formlists" in arg
        arg = arg.replace("--formlists", "")
        force = "--force" in arg
        arg = arg.replace("--force", "").strip()
        if not arg:
            return {"ok": False,
                    "error": "použití: @@COREIMPORT <ec_form_id> [<zdroj>] [--force] [--map A=B,C=D] [--bind <grid_code>] [--rebind]"}
        parts = arg.split(None, 1)
        ec_form_id = int(parts[0])
        zdroj = parts[1].strip() if len(parts) > 1 else None
    except (ValueError, IndexError):
        return {"ok": False, "error": "první argument musí být číslo (EC_FormDef.ID)"}

    from modules.strategie_pg.application import service as _pg
    cm = _pg.get_session()
    s = cm.__enter__()
    try:
        cen = _read_centrala(ec_form_id)
        code = _slug(cen["nazev"])
        label = cen["nazev"]

        # ── Chirurgický režim --formlists: jen přepnout formlist pole na lookup ──
        # Jádro už musí existovat (a vzniknout z @@COREIMPORT). Nesahá na generátor,
        # kontejnery ani ostatní pole → dopad výhradně formlist pole tohoto core.
        if formlists_only:
            core_row = s.execute(_t(
                "SELECT id, COALESCE(created_by_text,''), COALESCE(updated_by_text,'') "
                "FROM fw.core WHERE code = :c"), {"c": code}).first()
            if not core_row:
                return {"ok": False, "error": (
                    f"--formlists: fw.core code='{code}' neexistuje — nejdřív spusť plný "
                    f"@@COREIMPORT {ec_form_id}.")}
            core_id = int(core_row[0])
            if "@@COREIMPORT" not in (core_row[1] + core_row[2]):
                return {"ok": False, "error": (
                    f"--formlists: fw.core code='{code}' (id={core_id}) nevznikl z @@COREIMPORT "
                    f"— nesahám na cizí jádro.")}
            frep = _wire_formlists(s, core_id, cen, user_map)
            s.commit()
            return {
                "ok": True,
                "columns": ["pole", "hodnota"],
                "rows": [
                    ["režim", "--formlists (jen lookup wiring)"],
                    ["ec_form_id", ec_form_id],
                    ["core_id", core_id],
                    ["core.code", code],
                    ["formlistů_na_lookup", frep["formlists_wired"]],
                    ["číselníky", ", ".join(frep["ciselniky"]) or "—"],
                    ["nenamapováno", ", ".join(frep["unmatched"]) or "—"],
                    ["detail", " | ".join(frep["details"]) or "—"],
                ],
            }

        select_sql = _source_to_select(zdroj, cen["sql_select"])
        # sloupce zdroje (i pro generátor/layout) + normalizace `id` pro form-load
        raw_cols = _fields_of(s, select_sql)
        store_sql = _ensure_lower_id(select_sql, raw_cols)

        # 2. upsert fw.core (idempotentně dle code)
        # BEZPEČNOSTNÍ GUARD (Kristý 9.7.2026): existující core se stejným kódem
        # smíme aktualizovat JEN pokud vznikl z @@COREIMPORT. Cizí/ručně stavěné
        # jádro NIKDY nepřepisujeme — místo toho chyba s radou. Dopad příkazu je
        # tak omezen výhradně na jádra, která si sám založil.
        core_row = s.execute(_t(
            "SELECT id, COALESCE(created_by_text,''), COALESCE(updated_by_text,'') "
            "FROM fw.core WHERE code = :c"), {"c": code}).first()
        if core_row:
            core_id = int(core_row[0])
            if "@@COREIMPORT" not in (core_row[1] + core_row[2]):
                return {"ok": False, "error": (
                    f"fw.core code='{code}' (id={core_id}) už existuje a NEvznikl z @@COREIMPORT — "
                    f"nepřepisuju cizí jádro. Přejmenuj/ověř ručně, nebo smaž a spusť znovu.")}
            s.execute(_t("UPDATE fw.core SET label=:l, is_active=true, updated_by_text='Claude-24 @@COREIMPORT' WHERE id=:id"),
                      {"l": label, "id": core_id})
        else:
            core_id = int(s.execute(_t(
                "INSERT INTO fw.core (code, label, is_active, tenant_visibility, version, created_by_text) "
                "VALUES (:c, :l, true, 'all', 1, 'Claude-24 @@COREIMPORT') RETURNING id"
            ), {"c": code, "l": label}).scalar())

        # 3. edit-select: data_set + data_source + op(edit) — idempotentně dle code
        dset_code = f"{code}_edit"
        dset_row = s.execute(_t("SELECT id FROM fw.data_set WHERE code=:c"), {"c": dset_code}).first()
        if dset_row:
            dset_id = int(dset_row[0])
            s.execute(_t("UPDATE fw.data_set SET sql_text=:sql, db_connection_id=:db WHERE id=:id"),
                      {"sql": store_sql, "db": DEFAULT_DB_CONNECTION_ID, "id": dset_id})
        else:
            # pozn.: created_by je INTEGER (user id) → vynecháváme (autor = fw.core.created_by_text + git)
            dset_id = int(s.execute(_t(
                "INSERT INTO fw.data_set (code, version, sql_text, db_connection_id, status, is_system, is_immutable) "
                "VALUES (:c, 1, :sql, :db, 'active', false, false) RETURNING id"
            ), {"c": dset_code, "sql": store_sql, "db": DEFAULT_DB_CONNECTION_ID}).scalar())

        dsrc_row = s.execute(_t("SELECT id FROM fw.data_source WHERE code=:c"), {"c": code}).first()
        if dsrc_row:
            dsrc_id = int(dsrc_row[0])
        else:
            dsrc_id = int(s.execute(_t(
                "INSERT INTO fw.data_source (code, version, name, status, is_system, is_immutable) "
                "VALUES (:c, 1, :n, 'active', false, false) RETURNING id"
            ), {"c": code, "n": label}).scalar())

        op_row = s.execute(_t(
            "SELECT id FROM fw.data_source_op WHERE core_id=:core AND operation_kind='edit'"
        ), {"core": core_id}).first()
        if op_row:
            s.execute(_t("UPDATE fw.data_source_op SET data_source_id=:ds, data_set_id=:dset WHERE id=:id"),
                      {"ds": dsrc_id, "dset": dset_id, "id": int(op_row[0])})
        else:
            s.execute(_t(
                "INSERT INTO fw.data_source_op (data_source_id, data_set_id, operation_kind, variant_code, sort_order, is_default, core_id) "
                "VALUES (:ds, :dset, 'edit', 'default', 10, true, :core)"
            ), {"ds": dsrc_id, "dset": dset_id, "core": core_id})

        s.commit()  # aby generátor viděl core + edit-select

        # 4. spuštění nativního generátoru (fields = reálné sloupce zdroje, bez
        #    pomocného `id` aliasu — ten je jen pro form-load, ne pro komponenty)
        fields = raw_cols
        gen_out = _run_generator(core_id, fields, force)

        # 5. layout z Centrály: groupboxy + zařazení polí + captiony + pořadí
        #    + typy (centrala_id) + schování polí mimo Centrálu
        rep = _layout_from_centrala(s, core_id, cen, fields, user_map)
        s.commit()

        # 6. (volitelně) navázání na přehled: grid_code(list core.code) → toto jádro.
        #    Edit se pak z řádku přehledu otevře nativně (přes FW_EDIT_FORM_REGISTRY,
        #    který se seeduje z fw.edit_form_binding). Pojistka: bez --rebind se
        #    existující vazba NEpřepíše (Kristý 10.7.).
        bind_info = "—"
        if bind_grid:
            from modules.erp.api import edit_form_binding as _efb
            br = _efb.set_binding(s, bind_grid, core_id, force=rebind)
            if br.get("ok"):
                s.commit()
                bind_info = f"{bind_grid} → core {core_id}"
                if br.get("replaced"):
                    bind_info += f" (přepsáno z core {br['replaced']})"
            elif br.get("already_bound") is not None:
                bind_info = (f"⚠ přehled '{bind_grid}' už má jádro core {br['already_bound']} "
                             f"— NEnavázáno; pro přepsání přidej --rebind")
            else:
                bind_info = f"⚠ vazba selhala: {br.get('error')}"

        comp_cnt = int(s.execute(_t("SELECT count(*) FROM fw.comp_def WHERE core_id=:c"),
                                 {"c": core_id}).scalar())
        return {
            "ok": True,
            "columns": ["pole", "hodnota"],
            "rows": [
                ["ec_form_id", ec_form_id],
                ["core_id", core_id],
                ["core.code", code],
                ["core.label", label],
                ["edit_select", store_sql[:120]],
                ["poli_v_datasetu", len(fields)],
                ["komponent_celkem", comp_cnt],
                ["groupboxy", rep["groupboxes"]],
                ["poli_namapovano", rep["fields_mapped"]],
                ["poli_schovano", rep["fields_hidden"]],
                ["gridy_preskoceny (faze 2)", rep["grids_skipped"]],
                ["tlacitka_preskocena (Delphi)", rep["buttons_skipped"]],
                ["nenamapovano (dopln --map)", ", ".join(rep["unmatched"]) or "—"],
                ["vazba na prehled", bind_info],
                ["generator", (gen_out or "")[-160:]],
            ],
        }
    except Exception as e:
        try:
            s.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:400]),
                "tb": traceback.format_exc()[-1200:]}
    finally:
        cm.__exit__(None, None, None)
