#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrace HR dat z DB_EC (MSSQL) -> mod.* (PostgreSQL).

Zdroje:  dbo.TabCisZam (+ TabCisZam_EXT), dbo.TabKontakty
Cíle:    mod.hr_party / hr_person / hr_person_address / hr_emergency_contact /
         hr_legal_entity / hr_person_role / hr_person_contact
Provenance: každý cílový řádek dostane záznam v mod.hr_source_ref
            (idempotence -> opakované spuštění nezduplikuje).

Vlastnosti:
  * idempotentní (přes hr_source_ref) -> lze pouštět opakovaně,
  * commit po každém zaměstnanci (chyba u jednoho nezhodí celek),
  * --dry-run (vše se na konci rollbackne, jen report),
  * --limit N (zmigruje jen prvních N zaměstnanců — pro test nanečisto),
  * RČ: plaintext do rodne_cislo + SHA-256 do rodne_cislo_hash; enc zatím NULL.

Spuštění (viz docs/hr_migrace_dbec_runbook.md):
  set MSSQL_DSN=DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=DB_EC;UID=...;PWD=...;TrustServerCertificate=yes
  set PG_DSN=host=... port=5432 dbname=data_db user=Marti-AI password=...
  set EUROSOFT_TENANT_ID=2
  python migrate_hr_from_dbec.py --limit 3 --dry-run   # zkouška nanečisto
  python migrate_hr_from_dbec.py --limit 3             # 3 zaměstnanci naostro
  python migrate_hr_from_dbec.py                       # vše
"""
import argparse
import datetime as dt
import hashlib
import os
import re
import sys

import pyodbc
import psycopg2

SRC_SYSTEM = "DB_EC"
T_ZAM = "dbo.TabCisZam"
T_EXT = "dbo.TabCisZam_EXT"
T_KON = "dbo.TabKontakty"
AUTHOR = "migrace DB_EC"
SENTINEL_FROM = dt.date(1900, 1, 1)  # když _DatumNastupu chybí (valid_from je NOT NULL)

# Druh (typ spojení) a Kam (umístění) -> contact_kind kód
DRUH = {1: "telefon", 2: "mobil", 3: "fax", 6: "email", 7: "www", 11: "skype"}
KAM = {0: "firemni", 1: "soukromy"}
DRUH_LABEL = {"telefon": "Telefon", "mobil": "Mobil", "fax": "Fax",
              "email": "E-mail", "www": "WWW", "skype": "Skype"}
KAM_LABEL = {"firemni": "firemní", "soukromy": "soukromý"}

# (flag v TabCisZam_EXT -> role_kind kód)
ROLE_FLAGS = [("_HPP", "zamestnanec_hpp"), ("_DPP", "zamestnanec_dpp"), ("_OSVC", "osvc_dodavatel")]

# _Firma -> seznam (idx, IČO, nazev) zaměstnavatelů
ENTITY_BY_FIRMA = {
    0: [("control",)],          # EUROSOFT - Control
    1: [("system",)],           # EUROSOFT - System
    2: [("control",), ("system",)],  # OBĚ
}
ENTITIES = {
    "control": {"nazev": "EUROSOFT - Control", "ico": "27960862"},
    "system": {"nazev": "EUROSOFT - System", "ico": "26411741"},
}


def s(v):
    """strip; prázdný řetězec -> None."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def as_bool(v):
    return bool(v) if v is not None else False


def as_date(v):
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    return v


def rc_hash(rc):
    if not rc:
        return None
    digits = re.sub(r"\D", "", rc)
    if not digits:
        return None
    return hashlib.sha256(digits.encode("utf-8")).hexdigest()


def join_cp(pop, orr):
    parts = [p for p in (s(pop), s(orr)) if p]
    return "/".join(parts) if parts else None


# ── provenance helpers ──────────────────────────────────────────────────────
def src_existing(pg, target_table, source_table, source_id):
    pg.execute(
        "SELECT target_id FROM mod.hr_source_ref "
        "WHERE source_system=%s AND source_table=%s AND source_id=%s AND target_table=%s",
        (SRC_SYSTEM, source_table, str(source_id), target_table),
    )
    row = pg.fetchone()
    return row[0] if row else None


def src_record(pg, target_table, target_id, source_table, source_id, batch):
    pg.execute(
        "INSERT INTO mod.hr_source_ref "
        "(target_table, target_id, source_system, source_table, source_id, migration_batch, created_by_text) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (source_system, source_table, source_id, target_table) DO NOTHING",
        (target_table, target_id, SRC_SYSTEM, source_table, str(source_id), batch, AUTHOR),
    )


# ── reference data ──────────────────────────────────────────────────────────
def ensure_contact_kinds(pg):
    for dcode, dlabel in DRUH_LABEL.items():
        for kcode, klabel in KAM_LABEL.items():
            pg.execute(
                "INSERT INTO mod.hr_contact_kind (code, label) VALUES (%s,%s) "
                "ON CONFLICT (code) DO NOTHING",
                (f"{dcode}_{kcode}", f"{dlabel} {klabel}"),
            )


def ensure_entity(pg, tenant_id, key, batch):
    """Upsert EUROSOFT entity -> vrať party_id."""
    info = ENTITIES[key]
    pid = src_existing(pg, "hr_party", "EUROSOFT_ENTITY", key)
    if pid:
        return pid
    # fallback: dohledej dle IČO (kdyby vznikla mimo source_ref)
    pg.execute("SELECT party_id FROM mod.hr_legal_entity WHERE ico=%s", (info["ico"],))
    row = pg.fetchone()
    if row:
        src_record(pg, "hr_party", row[0], "EUROSOFT_ENTITY", key, batch)
        return row[0]
    pg.execute(
        "INSERT INTO mod.hr_party (tenant_id, party_type, display_name, created_by_text) "
        "VALUES (%s,'legal_entity',%s,%s) RETURNING id",
        (tenant_id, info["nazev"], AUTHOR),
    )
    pid = pg.fetchone()[0]
    pg.execute(
        "INSERT INTO mod.hr_legal_entity (party_id, nazev, ico, created_by_text) "
        "VALUES (%s,%s,%s,%s)",
        (pid, info["nazev"], info["ico"], AUTHOR),
    )
    src_record(pg, "hr_party", pid, "EUROSOFT_ENTITY", key, batch)
    return pid


# ── jeden zaměstnanec ───────────────────────────────────────────────────────
def migrate_employee(pg, tenant_id, z, contacts, entities, batch, stats):
    zid = z["ID"]

    # 1) party (person)
    party_id = src_existing(pg, "hr_party", T_ZAM, zid)
    if party_id is None:
        display = " ".join(p for p in (s(z["Prijmeni"]), s(z["Jmeno"])) if p) or f"#{zid}"
        is_active = not as_bool(z["VyraditZPrehledu"])
        pg.execute(
            "INSERT INTO mod.hr_party (tenant_id, party_type, display_name, is_active, created_by_text) "
            "VALUES (%s,'person',%s,%s,%s) RETURNING id",
            (tenant_id, display, is_active, AUTHOR),
        )
        party_id = pg.fetchone()[0]
        src_record(pg, "hr_party", party_id, T_ZAM, zid, batch)
        stats["party"] += 1

    # 2) person
    person_id = src_existing(pg, "hr_person", T_ZAM, zid)
    if person_id is None:
        rc = s(z["RodneCislo"])
        pg.execute(
            "INSERT INTO mod.hr_person "
            "(party_id, jmeno, prijmeni, titul_pred, titul_za, datum_narozeni, "
            " rodne_cislo, rodne_cislo_hash, statni_prislusnost, rodne_prijmeni, "
            " pohlavi, misto_narozeni, stat_narozeni, narodnost, rodinny_stav, osobni_ic, "
            " is_active, created_by_text) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                party_id, s(z["Jmeno"]) or "?", s(z["Prijmeni"]) or "?",
                s(z["TitulPred"]), s(z["TitulZa"]), as_date(z["DatumNarozeni"]),
                rc, rc_hash(rc), s(z["StatniPrislus"]), s(z["RodnePrijmeni"]),
                z["Pohlavi"], s(z["MistoNarozeni"]), s(z["StatNarozeni"]),
                s(z["Narodnost"]), z["RodinnyStav"], s(z["OsobniIC"]),
                not as_bool(z["VyraditZPrehledu"]), AUTHOR,
            ),
        )
        person_id = pg.fetchone()[0]
        src_record(pg, "hr_person", person_id, T_ZAM, zid, batch)
        stats["person"] += 1

    # 3) adresy (trvalá / doručovací)
    for kind, pref in (("trvala", "AdrTrv"), ("dorucovaci", "AdrPrech")):
        sid = f"{zid}:{kind}"
        if src_existing(pg, "hr_person_address", T_ZAM, sid):
            continue
        ulice = s(z[pref + "Ulice"]); cp = join_cp(z[pref + "PopCislo"], z[pref + "OrCislo"])
        obec = s(z[pref + "Misto"]); psc = s(z[pref + "PSC"]); stat = s(z[pref + "Zeme"])
        if not any((ulice, cp, obec, psc, stat)):
            continue
        pg.execute(
            "INSERT INTO mod.hr_person_address "
            "(person_id, address_kind, ulice, cp, obec, psc, stat, created_by_text) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (person_id, kind, ulice, cp, obec, psc, stat, AUTHOR),
        )
        src_record(pg, "hr_person_address", pg.fetchone()[0], T_ZAM, sid, batch)
        stats["address"] += 1

    # 4) nouzový kontakt (AdrKont*)
    sid = f"{zid}:emergency"
    if not src_existing(pg, "hr_emergency_contact", T_ZAM, sid):
        ec = " ".join(p for p in (s(z["AdrKontJmeno"]), s(z["AdrKontPrijmeni"])) if p)
        if ec:
            pg.execute(
                "INSERT INTO mod.hr_emergency_contact (person_id, jmeno, created_by_text) "
                "VALUES (%s,%s,%s) RETURNING id",
                (person_id, ec, AUTHOR),
            )
            src_record(pg, "hr_emergency_contact", pg.fetchone()[0], T_ZAM, sid, batch)
            stats["emergency"] += 1

    # 5) role (z TabCisZam_EXT: _Firma + _HPP/_DPP/_OSVC)
    firma = z["_Firma"]
    employers = ENTITY_BY_FIRMA.get(firma, [])
    if firma is not None and not employers:
        stats["firma_undef"] += 1
    vfrom = as_date(z["_DatumNastupu"]) or SENTINEL_FROM
    vuntil = as_date(z["_DatumOdchodu"])
    is_active = not as_bool(z["_neaktivni"])
    for flag, kind in ROLE_FLAGS:
        if not as_bool(z[flag]):
            continue
        for (ekey,) in employers:
            emp_pid = entities[ekey]
            sid = f"{zid}:{kind}:{ekey}"
            if src_existing(pg, "hr_person_role", T_EXT, sid):
                continue
            attrs = '{"firma": "%s"%s}' % (
                ekey, ', "zkusebni": true' if as_bool(z["_Zkusebni"]) else "")
            pg.execute(
                "INSERT INTO mod.hr_person_role "
                "(person_id, party_id, role_kind, valid_from, valid_until, attrs, is_active, created_by_text) "
                "VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING id",
                (person_id, emp_pid, kind, vfrom, vuntil, attrs, is_active, AUTHOR),
            )
            src_record(pg, "hr_person_role", pg.fetchone()[0], T_EXT, sid, batch)
            stats["role"] += 1

    # 6) kontakty (TabKontakty)
    for k in contacts:
        if src_existing(pg, "hr_person_contact", T_KON, k["ID"]):
            continue
        kind = None
        d = DRUH.get(k["Druh"]); m = KAM.get(k["Kam"])
        if d and m:
            kind = f"{d}_{m}"
        val = s(k["Spojeni"])
        if not kind or not val:
            stats["contact_skip"] += 1
            continue
        pg.execute(
            "INSERT INTO mod.hr_person_contact "
            "(person_id, contact_kind, value, is_primary, created_by_text) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (person_id, kind, val, as_bool(k["Prednastaveno"]), AUTHOR),
        )
        src_record(pg, "hr_person_contact", pg.fetchone()[0], T_KON, k["ID"], batch)
        stats["contact"] += 1


def fetch_dicts(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="jen prvních N zaměstnanců")
    ap.add_argument("--dry-run", action="store_true", help="na konci rollback, jen report")
    ap.add_argument("--batch", default="dbec-" + dt.datetime.now().strftime("%Y%m%d-%H%M"))
    args = ap.parse_args()

    mssql_dsn = os.environ["MSSQL_DSN"]
    pg_dsn = os.environ["PG_DSN"]
    tenant_id = int(os.environ.get("EUROSOFT_TENANT_ID", "2"))

    mc = pyodbc.connect(mssql_dsn)
    mc.autocommit = True
    pgc = psycopg2.connect(pg_dsn)
    pg = pgc.cursor()

    # tenant sanity
    pg.execute("SELECT count(*) FROM public.tenants WHERE id=%s", (tenant_id,))
    if pg.fetchone()[0] != 1:
        print(f"VAROVÁNÍ: tenant_id={tenant_id} v public.tenants neexistuje!", file=sys.stderr)

    ensure_contact_kinds(pg)
    entities = {key: ensure_entity(pg, tenant_id, key, args.batch) for key in ENTITIES}
    pgc.commit()
    print(f"Entity: control=party#{entities['control']}, system=party#{entities['system']}")

    top = f"TOP ({args.limit}) " if args.limit else ""
    zam_cur = mc.cursor()
    zam_cur.execute(
        f"SELECT {top}"
        " z.ID, z.Jmeno, z.Prijmeni, z.RodnePrijmeni, z.TitulPred, z.TitulZa,"
        " z.DatumNarozeni, z.RodneCislo, z.Pohlavi, z.MistoNarozeni, z.StatNarozeni,"
        " z.Narodnost, z.RodinnyStav, z.StatniPrislus, z.OsobniIC, z.VyraditZPrehledu,"
        " z.AdrTrvUlice, z.AdrTrvOrCislo, z.AdrTrvPopCislo, z.AdrTrvMisto, z.AdrTrvPSC, z.AdrTrvZeme,"
        " z.AdrPrechUlice, z.AdrPrechOrCislo, z.AdrPrechPopCislo, z.AdrPrechMisto, z.AdrPrechPSC, z.AdrPrechZeme,"
        " z.AdrKontJmeno, z.AdrKontPrijmeni,"
        " e._Firma, e._HPP, e._DPP, e._OSVC, e._DatumNastupu, e._DatumOdchodu, e._neaktivni, e._Zkusebni"
        f" FROM {T_ZAM} z LEFT JOIN {T_EXT} e ON e.ID = z.ID"
        " ORDER BY z.ID"
    )
    employees = fetch_dicts(zam_cur)

    kon_cur = mc.cursor()
    stats = {k: 0 for k in ("party", "person", "address", "emergency", "role",
                            "contact", "contact_skip", "firma_undef", "err")}
    done = 0
    for z in employees:
        kon_cur.execute(
            f"SELECT ID, Druh, Kam, Spojeni, Prednastaveno FROM {T_KON} WHERE IDCisZam = ?",
            z["ID"],
        )
        contacts = fetch_dicts(kon_cur)
        try:
            migrate_employee(pg, tenant_id, z, contacts, entities, args.batch, stats)
            if not args.dry_run:
                pgc.commit()   # v dry-run necommitujeme, na konci rollback
            done += 1
        except Exception as exc:  # noqa
            pgc.rollback()
            stats["err"] += 1
            print(f"CHYBA u zaměstnance ID={z['ID']}: {exc}", file=sys.stderr)

    if args.dry_run:
        pgc.rollback()
        print(">>> DRY-RUN: vše vráceno (rollback).")

    print(f"\nZpracováno zaměstnanců: {done}/{len(employees)}  batch={args.batch}")
    for k in ("party", "person", "address", "emergency", "role", "contact",
              "contact_skip", "firma_undef", "err"):
        print(f"  {k:14s}: {stats[k]}")

    pg.close(); pgc.close(); mc.close()


if __name__ == "__main__":
    main()
