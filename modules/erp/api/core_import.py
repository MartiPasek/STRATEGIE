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
    """Z Centrály: název formuláře, jeho SQL_Select a mapa {sloupec_lower: popisek}.

    Popisky: v EC_FormDefEditProperty je per-komponenta FieldName (na co je pole
    napojené) a Caption (jak se jmenuje). Spárováním vznikne caption mapa.
    """
    hdr = _ec(f"SELECT ID, Nazev, CAST(SQL_Select AS nvarchar(max)) AS sqltext "
              f"FROM dbo.EC_FormDef WHERE ID = {int(ec_form_id)}")
    if not hdr:
        raise RuntimeError(f"EC_FormDef.ID={ec_form_id} v Centrále neexistuje")
    nazev = (hdr[0].get("Nazev") or "").strip() or f"core_{ec_form_id}"
    sqltext = hdr[0].get("sqltext") or ""

    prop = _ec(
        "SELECT e.ID AS c, "
        "MAX(CASE WHEN P.Property='FieldName' THEN P.Value END) AS fld, "
        "MAX(CASE WHEN P.Property='Caption' THEN COALESCE(NULLIF(P.Value,''),P.ValueFMX) END) AS cap "
        f"FROM dbo.EC_FormDefEdit e "
        f"LEFT JOIN dbo.EC_FormDefEditProperty P ON P.ID_FormDefEdit = e.ID "
        f"WHERE e.ID_Form = {int(ec_form_id)} "
        "GROUP BY e.ID"
    )
    caption_map: dict[str, str] = {}
    for r in prop:
        fld = (r.get("fld") or "").strip()
        cap = (r.get("cap") or "").strip()
        if fld and cap:
            caption_map[fld.lower()] = cap
    return {"nazev": nazev, "sql_select": sqltext, "caption_map": caption_map}


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
    prev = os.environ.get("SANDBOX_CONTEXT")
    os.environ["SANDBOX_CONTEXT"] = json.dumps(ctx, ensure_ascii=True)
    buf = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(str(GENERATOR_PATH), run_name="__main__")
    except SystemExit as e:
        exit_code = int(e.code) if isinstance(e.code, int) else (0 if not e.code else 1)
    finally:
        if prev is None:
            os.environ.pop("SANDBOX_CONTEXT", None)
        else:
            os.environ["SANDBOX_CONTEXT"] = prev
    out = buf.getvalue()
    if exit_code != 0:
        raise RuntimeError(f"generátor selhal (exit {exit_code}): {out[-600:]}")
    return out


def _apply_captions(s, core_id: int, caption_map: dict[str, str]) -> int:
    """Nastaví fw.comp_def.caption z Centrály (podle názvu pole = sloupec)."""
    if not caption_map:
        return 0
    rows = s.execute(_t(
        "SELECT id, name FROM fw.comp_def WHERE core_id = :c AND name IS NOT NULL"
    ), {"c": core_id}).mappings().all()
    n = 0
    for r in rows:
        cap = caption_map.get((r["name"] or "").lower())
        if cap:
            s.execute(_t("UPDATE fw.comp_def SET caption = :cap WHERE id = :id"),
                      {"cap": cap, "id": r["id"]})
            n += 1
    return n


# ── hlavní vstup ─────────────────────────────────────────────────────────────

def run_core_import(arg: str) -> dict:
    """Parsuje '<ec_form_id> [<zdroj>] [--force]' a provede import. Vrací dict pro JSONResponse."""
    try:
        force = "--force" in arg
        arg = arg.replace("--force", "").strip()
        if not arg:
            return {"ok": False, "error": "použití: @@COREIMPORT <ec_form_id> [<zdroj>] [--force]"}
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

        # 5. popisky z Centrály
        caps = _apply_captions(s, core_id, cen["caption_map"])
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
                ["popisku_z_centraly", caps],
                ["generator", (gen_out or "")[-300:]],
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
