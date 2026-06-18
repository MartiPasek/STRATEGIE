#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bakaláři — read-only průzkum schématu (Fáze 0).

Spustit na NOTEBOOKU, který má VPN do vnitřní sítě Nerudovky (Klárčin NTB).
Připojí se na Bakaláře (MSSQL), vypíše seznam tabulek + sloupce do souboru
`bakalari_schema_dump.txt` vedle skriptu. Ten soubor pak pošli Claudovi.

BEZPEČNOST:
  - Heslo se NEUKLÁDÁ do skriptu ani na disk — zadáš ho při spuštění.
  - Skript je čistě ČTECÍ (jen SELECT / INFORMATION_SCHEMA / sys.*).

PŘÍPRAVA (jednorázově):
  1) Nainstaluj Python 3 (python.org) — při instalaci zaškrtni "Add to PATH".
  2) V příkazové řádce:  pip install pymssql
  3) Ujisti se, že je zapnutá VPN do Nerudovky.
  4) Spusť:  python bakalari_explore.py
"""
import sys
import getpass
import datetime

# --- Připojení (NE tajné) ---------------------------------------------------
SERVER = "172.16.6.225"     # BAKALARI-TEST
PORT   = 1433
USER   = "BakaRO"           # read-only účet
DB     = "bakalari"
OUT    = "bakalari_schema_dump.txt"

# tabulky zajímavé pro ROZVRH (zvýrazníme je nahoře)
KEYWORDS = [
    "rozvrh", "hodin", "predmet", "předmět", "ucitel", "učitel", "trida", "třída",
    "mistnost", "místnost", "ucebna", "učebna", "vyuk", "výuk", "uvazek", "úvazek",
    "skupin", "kabinet", "zvon", "obdobi", "období", "lesson", "timetable",
    "teacher", "class", "room", "subject", "schedule", "den", "perioda",
]


def main():
    try:
        import pymssql
    except ImportError:
        print("CHYBA: chybí knihovna pymssql. Nainstaluj:  pip install pymssql")
        sys.exit(1)

    print(f"Připojuji se na {SERVER}:{PORT}, DB '{DB}', účet '{USER}'…")
    pwd = getpass.getpass("Heslo k účtu BakaRO (nezobrazí se): ")

    try:
        conn = pymssql.connect(server=SERVER, port=str(PORT), user=USER,
                               password=pwd, database=DB, login_timeout=15, timeout=60)
    except Exception as e:
        print("CHYBA připojení:", e)
        print("Zkontroluj: zapnutá VPN do Nerudovky, správné heslo, dostupnost serveru.")
        sys.exit(2)

    cur = conn.cursor()
    lines = []

    def w(s=""):
        lines.append(s)
        print(s)

    w("# BAKALÁŘI — průzkum schématu (read-only)")
    w(f"# {datetime.datetime.now():%Y-%m-%d %H:%M:%S}  ·  server={SERVER}  db={DB}")
    w()

    # 1) verze
    try:
        cur.execute("SELECT @@VERSION")
        w("## Verze SQL serveru")
        w(str(cur.fetchone()[0]))
        w()
    except Exception as e:
        w(f"(verze se nenačetla: {e})")

    # 2) tabulky + odhad počtu řádků
    tables = []  # (schema, table, rows)
    try:
        cur.execute(
            "SELECT s.name, t.name, COALESCE(SUM(p.rows),0) "
            "FROM sys.tables t "
            "JOIN sys.schemas s ON s.schema_id = t.schema_id "
            "LEFT JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) "
            "GROUP BY s.name, t.name ORDER BY s.name, t.name"
        )
        tables = [(r[0], r[1], int(r[2])) for r in cur.fetchall()]
    except Exception as e:
        w(f"(seznam tabulek se nenačetl: {e})")

    w(f"## Tabulky ({len(tables)} celkem)")
    w()

    def is_rozvrh(name):
        n = name.lower()
        return any(k in n for k in KEYWORDS)

    rozvrh = [t for t in tables if is_rozvrh(t[1])]
    w(f"### Pravděpodobně ROZVRHOVÉ tabulky ({len(rozvrh)}):")
    for sch, tab, rows in rozvrh:
        w(f"  - {sch}.{tab}  ({rows} řádků)")
    w()
    w("### Všechny tabulky (schema.tabulka · řádků):")
    for sch, tab, rows in tables:
        w(f"  {sch}.{tab} · {rows}")
    w()

    # 3) sloupce všech tabulek
    w("## Sloupce všech tabulek")
    try:
        cur.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, "
            "       CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION"
        )
        cur_tab = None
        for sch, tab, col, dt, maxlen, nullable in cur.fetchall():
            key = f"{sch}.{tab}"
            if key != cur_tab:
                w("")
                w(f"### {key}")
                cur_tab = key
            ln = f"  {col} : {dt}"
            if maxlen not in (None, -1):
                ln += f"({maxlen})"
            if nullable == "NO":
                ln += " NOT NULL"
            w(ln)
    except Exception as e:
        w(f"(sloupce se nenačetly: {e})")

    try:
        conn.close()
    except Exception:
        pass

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print()
    print(f"HOTOVO. Výstup uložen do: {OUT}")
    print("Pošli tenhle soubor Claudovi (Martinovi).")


if __name__ == "__main__":
    main()
