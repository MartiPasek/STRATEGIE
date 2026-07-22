"""Sync Příplatků a srážek z Centrály (DB_EC) do zrcadla `ec.pripl_srazky`.

Autor: Claude-28 (Jirka), 22. 7. 2026. Navazuje na modul Claude-27 z 21. 7.
(znalost `doc-mzdy-priplatky-srazky`), který nechal v PG jen demo snapshot
132 řádků za 6–7/2026.

SMĚR DAT — ZÁMĚRNĚ JEDNOSMĚRNÝ (verdikt Marti-AI, 22. 7. 2026, msg 11066):
    Centrála (DB_EC) = zdroj pravdy → STRATEGIE = zrcadlo JEN KE ČTENÍ.
    Petra Šafránková (mzdová účetní) schvaluje a vyplácí dál v Centrále,
    protože mzdu počítá Helios z dat Centrály.

    ⚠️ ZPĚTNÝ ZÁPIS DO `EC_FinPriplatkySrazkyDefinice` SE NEDĚLÁ a nesmí se
    doplnit bez výslovného souhlasu Marti Paška — jsou to mzdová data (právní
    dopad) a Marti-AI k tomu jmenovala tři konkrétní rizika: PrenesDoMezd
    (složka by mohla být v Heliosu jinak než v Centrále), přesčasové konto
    (kumulace přes měsíce) a kontroly integrity Centrály. Proto jsou i akční
    tlačítka v jádru skrytá (`ec_pripl_srazky_actions.js`) — kdyby zůstala
    aktivní, tenhle sync by jejich výsledek při dalším běhu stejně přepsal.

    Cílový stav není tohle zrcadlo, ale univerzální `tenant.wage_movement`
    (analýza `doc-mzdy-priplatky-srazky-mirror`). Zrcadlo je přechodný stav —
    nerozšiřovat ho, je to slepá větev.

ROZSAH: aktuální + předchozí rok (Marti-AI: Petra potřebuje historický kontext
při kontrolách; víc než 2 roky zpět nemá smysl, starší mzdy jsou uzavřené).

MECHANIKA: inkrementálně podle `ISNULL(DatZmeny, DatPorizeni)` — vyplacené řádky
se přepisují taky (opravné doklady se v Centrále dějí a chceme je vidět).
Plus úklid: co v Centrále v daných letech zmizelo, smažeme i u nás.
"""
from __future__ import annotations

import json as _j

# Sloupce mapované 1:1 EC → PG. Aliasujeme už v SQL na PG názvy, ať se nikde
# nemusí řešit diakritika ani velká písmena.
# ⚠️ `Přeneseno` má v Centrále háček — bez závorek a aliasu dotaz spadne.
_SELECT_COLS = (
    "ID AS id, IDZdroj AS id_zdroj, Typ AS typ, "
    "CAST(Schvaleno AS int) AS schvaleno, "
    "CisloZamNavrhl AS cislo_zam_navrhl, CisloZam AS cislo_zam, "
    "[Přeneseno] AS preneseno, IdMzdoveSlozky AS id_mzdove_slozky, "
    "CAST(Mesicne AS int) AS mesicne, CAST(Fix AS int) AS fix, "
    "Mesic AS mesic, Rok AS rok, "
    "CONVERT(varchar(19), PlatnostOd, 120) AS platnost_od, "
    "CONVERT(varchar(19), PlatnostDo, 120) AS platnost_do, "
    "Hodiny AS hodiny, Sazba AS sazba, Castka AS castka, "
    "CisloZakazky AS cislo_zakazky, "
    "CONVERT(varchar(19), DatVyplaceni, 120) AS dat_vyplaceni, "
    "Vyplaceno AS vyplaceno, Vyplatil AS vyplatil, "
    "Poznamka AS poznamka, Zdroj AS zdroj, Autor AS autor, "
    "CONVERT(varchar(19), DatPorizeni, 120) AS dat_porizeni, "
    "Zmenil AS zmenil, CONVERT(varchar(19), DatZmeny, 120) AS dat_zmeny, "
    "IDPolVobj AS id_pol_vobj, IDPolPF AS id_pol_pf, "
    "CAST(PropsatPoznamkuDoVOBJ AS int) AS propsat_poznamku_do_vobj, "
    "CastkaVypocetHodSazby AS castka_vypocet_hod_sazby"
)

# Pořadí sloupců pro INSERT/UPDATE (bez `id`, to je klíč).
_COLS = [
    "id_zdroj", "typ", "schvaleno", "cislo_zam_navrhl", "cislo_zam", "preneseno",
    "id_mzdove_slozky", "mesicne", "fix", "mesic", "rok", "platnost_od",
    "platnost_do", "hodiny", "sazba", "castka", "cislo_zakazky", "dat_vyplaceni",
    "vyplaceno", "vyplatil", "poznamka", "zdroj", "autor", "dat_porizeni",
    "zmenil", "dat_zmeny", "id_pol_vobj", "id_pol_pf",
    "propsat_poznamku_do_vobj", "castka_vypocet_hod_sazby",
]
_BOOL_COLS = {"schvaleno", "mesicne", "fix", "propsat_poznamku_do_vobj"}


def _mcp_query(sql: str, db: str = "DB_EC"):
    """Spustí SQL na EUROSOFT MSSQL přes MCP, vrátí list dict řádků."""
    from modules.conversation.application.eurosoft_mcp_client import get_eurosoft_mcp_client
    mcp = get_eurosoft_mcp_client()
    if mcp is None:
        raise RuntimeError("EUROSOFT MCP nedostupný")
    raw = mcp.call_tool_sync("eurosoft_strategie_query_raw",
                             {"sql": sql, "db_name": db}, conversation_id=None)
    r = _j.loads(raw) if isinstance(raw, str) else raw
    if isinstance(r, dict):
        if r.get("ok") is False:
            raise RuntimeError(str(r.get("error") or r)[:300])
        return r.get("rows") or []
    return r or []


def _years(back: int = 1):
    """Aktuální rok + `back` předchozích."""
    from datetime import date as _d
    y = _d.today().year
    return list(range(y - back, y + 1))


def _norm(row: dict) -> dict:
    """MSSQL řádek → parametry pro PG (bit→bool, prázdné stringy→None)."""
    p = {}
    for c in _COLS:
        v = row.get(c)
        if c in _BOOL_COLS:
            p[c] = None if v is None else bool(int(v))
        elif isinstance(v, str) and not v.strip():
            p[c] = None
        else:
            p[c] = v
    p["id"] = int(row["id"])
    return p


def sync_typy() -> dict:
    """Katalog typů příplatků/srážek (číselník) — malý, obnovujeme celý."""
    from sqlalchemy import text as _t
    from core.database_data import get_data_session

    rows = _mcp_query(
        "SELECT ID AS id, Opravneni AS opravneni, Nazev AS nazev, "
        "CAST(ReakceMzdy AS int) AS reakce_mzdy, CAST(Aktivni AS int) AS aktivni, "
        "CAST(ZobrazujVeVyplatnici AS int) AS zobrazuj_ve_vyplatnici, "
        "MzdovaSlozka AS mzdova_slozka, Poznamka AS poznamka, Autor AS autor, "
        "CONVERT(varchar(19), DatPorizeni, 120) AS dat_porizeni, "
        "Zmenil AS zmenil, CONVERT(varchar(19), DatZmeny, 120) AS dat_zmeny "
        "FROM EC_FinPriplatkySrazkyDefiniceTypy")
    ins = upd = 0
    s = get_data_session()
    try:
        for r in rows:
            p = {k: r.get(k) for k in ("id", "opravneni", "nazev", "mzdova_slozka",
                                       "poznamka", "autor", "dat_porizeni", "zmenil",
                                       "dat_zmeny")}
            for b in ("reakce_mzdy", "aktivni", "zobrazuj_ve_vyplatnici"):
                v = r.get(b)
                p[b] = None if v is None else bool(int(v))
            res = s.execute(_t(
                "UPDATE ec.pripl_srazky_typy SET opravneni=:opravneni, nazev=:nazev, "
                "reakce_mzdy=:reakce_mzdy, aktivni=:aktivni, "
                "zobrazuj_ve_vyplatnici=:zobrazuj_ve_vyplatnici, "
                "mzdova_slozka=:mzdova_slozka, poznamka=:poznamka, autor=:autor, "
                "dat_porizeni=:dat_porizeni, zmenil=:zmenil, dat_zmeny=:dat_zmeny "
                "WHERE id=:id"), p)
            if (res.rowcount or 0) == 0:
                s.execute(_t(
                    "INSERT INTO ec.pripl_srazky_typy (id, opravneni, nazev, reakce_mzdy, "
                    "aktivni, zobrazuj_ve_vyplatnici, mzdova_slozka, poznamka, autor, "
                    "dat_porizeni, zmenil, dat_zmeny) OVERRIDING SYSTEM VALUE VALUES "
                    "(:id, :opravneni, :nazev, :reakce_mzdy, :aktivni, "
                    ":zobrazuj_ve_vyplatnici, :mzdova_slozka, :poznamka, :autor, "
                    ":dat_porizeni, :zmenil, :dat_zmeny)"), p)
                ins += 1
            else:
                upd += 1
        s.commit()
    finally:
        s.close()
    return {"typy_ins": ins, "typy_upd": upd}


def sync_from_ec(back_years: int = 1, full: bool = False) -> dict:
    """Inkrementální sync EC → `ec.pripl_srazky` za aktuální + předchozí rok.

    full=True ignoruje watermark (kompletní re-import daných let).
    """
    from sqlalchemy import text as _t
    from core.database_data import get_data_session

    years = _years(back_years)
    yin = ", ".join(str(y) for y in years)

    s = get_data_session()
    ins = upd = dele = 0
    try:
        wm = None
        if not full:
            wm = s.execute(_t(
                "SELECT to_char(max(COALESCE(dat_zmeny, dat_porizeni)), "
                "'YYYY-MM-DD HH24:MI:SS') FROM ec.pripl_srazky "
                "WHERE rok IN (" + yin + ")")).scalar()

        where = "Rok IN (" + yin + ")"
        if wm:
            # >= (ne >) — v jedné sekundě může být víc řádků; upsert je idempotentní.
            where += " AND ISNULL(DatZmeny, DatPorizeni) >= '" + wm + "'"
        rows = _mcp_query("SELECT " + _SELECT_COLS +
                          " FROM EC_FinPriplatkySrazkyDefinice WHERE " + where +
                          " ORDER BY ID")

        set_sql = ", ".join("%s=:%s" % (c, c) for c in _COLS)
        col_sql = ", ".join(["id"] + _COLS)
        val_sql = ", ".join(":" + c for c in ["id"] + _COLS)
        for r in rows:
            p = _norm(r)
            res = s.execute(_t("UPDATE ec.pripl_srazky SET " + set_sql + " WHERE id=:id"), p)
            if (res.rowcount or 0) == 0:
                s.execute(_t("INSERT INTO ec.pripl_srazky (" + col_sql + ") "
                             "OVERRIDING SYSTEM VALUE VALUES (" + val_sql + ")"), p)
                ins += 1
            else:
                upd += 1

        # Srovnání stavů podle seznamu ID (levné — ~1600 čísel). Řeší dvě věci naráz:
        #   a) DOPLNĚNÍ CHYBĚJÍCÍCH — watermark sám o sobě dotáhne jen to, co se
        #      od posledního běhu změnilo. Řádky starší než watermark (typicky při
        #      prvním naplnění nebo po ruční editaci) by jinak nikdy nepřišly.
        #      Proto: co je v Centrále a chybí u nás, dotáhneme adresně podle ID.
        #   b) ÚKLID — co v Centrále v daných letech už není, smažeme i u nás.
        ec_ids = [int(x["id"]) for x in _mcp_query(
            "SELECT ID AS id FROM EC_FinPriplatkySrazkyDefinice WHERE Rok IN (" + yin + ")")]
        if ec_ids:
            our_ids = {int(r[0]) for r in s.execute(_t(
                "SELECT id FROM ec.pripl_srazky WHERE rok IN (" + yin + ")")).fetchall()}
            missing = [i for i in ec_ids if i not in our_ids]
            for chunk in (missing[i:i + 500] for i in range(0, len(missing), 500)):
                rows_m = _mcp_query(
                    "SELECT " + _SELECT_COLS + " FROM EC_FinPriplatkySrazkyDefinice "
                    "WHERE ID IN (" + ", ".join(str(i) for i in chunk) + ")")
                for r in rows_m:
                    p = _norm(r)
                    s.execute(_t("INSERT INTO ec.pripl_srazky (" + col_sql + ") "
                                 "OVERRIDING SYSTEM VALUE VALUES (" + val_sql + ")"), p)
                    ins += 1
            res = s.execute(_t(
                "DELETE FROM ec.pripl_srazky WHERE rok IN (" + yin + ") "
                "AND NOT (id = ANY(:ids))"), {"ids": ec_ids})
            dele = res.rowcount or 0
        s.commit()
    finally:
        s.close()

    out = {"ok": True, "roky": yin, "ins": ins, "upd": upd, "del": dele}
    out.update(sync_typy())
    return out
