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
        "MAX(CASE WHEN P.Property='Left' THEN P.Value END) AS l "
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
    """Přenese rozložení z Centrály: groupboxy, zařazení polí, captiony,
    pořadí (Top/Left), typy (comp_type.centrala_id). Pole mimo Centrálu
    deaktivuje (is_active=false) — v DESIGN se dají kdykoli vrátit.

    Kódové gridy (typ 11/21) a tlačítka (typ 8) se NEpřenáší (logika je
    v Delphi) — groupboxy gridů se založí jako NEAKTIVNÍ placeholdery
    pro fázi 2, tlačítka jen hlásíme.
    """
    rep = {"groupboxes": 0, "fields_mapped": 0, "fields_hidden": 0,
           "grids_skipped": 0, "buttons_skipped": 0, "unmatched": []}

    # comp_type mapy: centrala_id → (id, code, kind) + code → id
    trows = s.execute(_t(
        "SELECT id, code, kind, centrala_id FROM fw.comp_type")).mappings().all()
    by_centrala = {int(r["centrala_id"]): r for r in trows if r["centrala_id"] is not None}
    by_code = {r["code"]: r for r in trows}
    if "groupbox" not in by_code:
        raise RuntimeError("fw.comp_type 'groupbox' nenalezen")

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

    # groupboxy s captionem → naše groupboxy (bez captionu = jen vizuální pás,
    # ten se překlenuje — děti jdou k jeho rodiči)
    def resolved_container(cid):
        """Vystoupej stromem na nejbližší groupbox S captionem (nebo root)."""
        seen = set()
        cur = cid
        while isinstance(cur, int) and cur in nodes and cur not in seen:
            seen.add(cur)
            n = nodes[cur]
            if int(n["typ"]) == 12 and (n.get("cap") or "").strip():
                return cur
            cur = parent_key(n)
        return None

    gb_map: dict[int, int] = {}   # Centrála groupbox cid → fw.comp_def.id
    gb_order = sorted(
        [c for c in comps if int(c["typ"]) == 12 and (c.get("cap") or "").strip()],
        key=lambda c: (as_int(c.get("t")), as_int(c.get("l"))))
    for i, gb in enumerate(gb_order):
        cid = int(gb["cid"])
        cap = (gb.get("cap") or "").strip()
        # obsahuje jen gridy? → placeholder (neaktivní) pro fázi 2
        child_typs = [int(n["typ"]) for n in comps if parent_key(n) == cid]
        only_grids = child_typs and all(t in (11, 21) for t in child_typs)
        name = "gb_centrala_%d" % cid
        row = s.execute(_t(
            "SELECT id FROM fw.comp_def WHERE core_id=:c AND name=:n"),
            {"c": core_id, "n": name}).first()
        layout = json.dumps({"label": cap, "border_mode": "top"})
        if row:
            gb_id = int(row[0])
            s.execute(_t(
                "UPDATE fw.comp_def SET caption=:cap, sort_order=:so, is_active=:act, "
                "layout=CAST(:lay AS jsonb), parent_comp_def_id=:par WHERE id=:id"),
                {"cap": cap, "so": (i + 1) * 10, "act": not only_grids,
                 "lay": layout, "par": client_panel_id, "id": gb_id})
        else:
            gb_id = int(s.execute(_t(
                "INSERT INTO fw.comp_def (core_id, type_id, name, caption, layout, "
                "is_active, sort_order, parent_comp_def_id, region_slot, created_by_text) "
                "VALUES (:c, :t, :n, :cap, CAST(:lay AS jsonb), :act, :so, :par, 'main', "
                "'Claude-24 @@COREIMPORT') RETURNING id"),
                {"c": core_id, "t": by_code["groupbox"]["id"], "n": name, "cap": cap,
                 "lay": layout, "act": not only_grids, "so": (i + 1) * 10,
                 "par": client_panel_id}).scalar())
        gb_map[cid] = gb_id
        rep["groupboxes"] += 1

    # pole: mapování FieldName → sloupec zdroje, caption, container, pořadí, typ
    mapped_cols: set[str] = set()
    for c in comps:
        typ = int(c["typ"])
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
        parent_id = gb_map.get(cont_cid, client_panel_id)
        cap = (c.get("cap") or "").strip() or col
        so = as_int(c.get("t")) * 10000 + as_int(c.get("l"))
        # typ přes centrala_id — jen leaf typy polí (grid/button/groupbox už odfiltrované)
        new_type = None
        ct = by_centrala.get(typ)
        if ct and ct["kind"] == "leaf" and ct["code"] not in ("grid", "gridpoldoklad", "button"):
            new_type = int(ct["id"])
        s.execute(_t(
            "UPDATE fw.comp_def SET caption=:cap, parent_comp_def_id=:par, "
            "sort_order=:so, is_active=true" +
            (", type_id=:tid" if new_type else "") + " WHERE id=:id"),
            dict({"cap": cap, "par": parent_id, "so": so, "id": g["id"]},
                 **({"tid": new_type} if new_type else {})))
        mapped_cols.add(col.lower())
        rep["fields_mapped"] += 1

    # pole zdroje, která na Centrála formuláři nejsou → schovat (kosmetika)
    for name_l, g in fields_by_name.items():
        if name_l in mapped_cols:
            continue
        if name_l not in {c.lower() for c in src_cols}:
            continue  # ne-datová komponenta (panel apod.)
        s.execute(_t("UPDATE fw.comp_def SET is_active=false WHERE id=:id"),
                  {"id": g["id"]})
        rep["fields_hidden"] += 1
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
    """Parsuje '<ec_form_id> [<zdroj>] [--force] [--map A=B,C=D]'. Vrací dict pro JSONResponse.

    --map = ruční mapování Centrála FieldName → sloupec zdroje pro případy,
    kdy auto-mapování (přesná shoda / alias z Centrála SQL / prefix) nestačí.
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
        force = "--force" in arg
        arg = arg.replace("--force", "").strip()
        if not arg:
            return {"ok": False,
                    "error": "použití: @@COREIMPORT <ec_form_id> [<zdroj>] [--force] [--map A=B,C=D]"}
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
        select_sql = _source_to_select(zdroj, cen["sql_select"])

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
                      {"sql": select_sql, "db": DEFAULT_DB_CONNECTION_ID, "id": dset_id})
        else:
            # pozn.: created_by je INTEGER (user id) → vynecháváme (autor = fw.core.created_by_text + git)
            dset_id = int(s.execute(_t(
                "INSERT INTO fw.data_set (code, version, sql_text, db_connection_id, status, is_system, is_immutable) "
                "VALUES (:c, 1, :sql, :db, 'active', false, false) RETURNING id"
            ), {"c": dset_code, "sql": select_sql, "db": DEFAULT_DB_CONNECTION_ID}).scalar())

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

        # 4. sloupce zdroje + spuštění nativního generátoru
        fields = _fields_of(s, select_sql)
        gen_out = _run_generator(core_id, fields, force)

        # 5. layout z Centrály: groupboxy + zařazení polí + captiony + pořadí
        #    + typy (centrala_id) + schování polí mimo Centrálu
        rep = _layout_from_centrala(s, core_id, cen, fields, user_map)
        s.commit()

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
                ["edit_select", select_sql[:120]],
                ["poli_v_datasetu", len(fields)],
                ["komponent_celkem", comp_cnt],
                ["groupboxy", rep["groupboxes"]],
                ["poli_namapovano", rep["fields_mapped"]],
                ["poli_schovano", rep["fields_hidden"]],
                ["gridy_preskoceny (faze 2)", rep["grids_skipped"]],
                ["tlacitka_preskocena (Delphi)", rep["buttons_skipped"]],
                ["nenamapovano (dopln --map)", ", ".join(rep["unmatched"]) or "—"],
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
