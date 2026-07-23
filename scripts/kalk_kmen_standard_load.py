#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kalk_kmen_standard_load.py — opakovatelný loader STANDARD kalkulace (Excel) -> proj.kalk_kmen

Autor: Claude-24 (Kristý), 23. 7. 2026.
Zdroj pravdy o mapování: STANDARD sešit K260XXXX...StandSiem...xlsm (list "Základní 2026" ad.).

CO DĚLÁ
  Projde všechny listy STANDARD sešitu, které mají hlavičku s "Typ / Bestell.-Nr.",
  vezme řádky s vyplněným obj. číslem (sloupec C) a výrobcem (sloupec D), a vygeneruje
  jeden atomický SQL skript:  DELETE FROM proj.kalk_kmen;  +  INSERT ... (všechny řádky).

MAPOVÁNÍ SLOUPCŮ (pevně dle Kristý, 23.7.2026 — bere se podle POZICE písmene, ne podle labelu):
  A (1)  Pos.               -> excel_pozice   (integer)
  B (2)  Bezeichnung        -> oznaceni
  C (3)  Typ / Bestell.-Nr. -> reg_cis
  D (4)  Lieferant          -> vyrobce
  H (8)  Koeffiz.           -> k_arb  A ZÁROVEŇ  k_vkm   (stejná hodnota)
  J (10) Hmotnost           -> hmotnost_kg
  navíc: excel_soubor = název souboru, excel_list = název listu, excel_radek = číslo řádku v Excelu
         zdroj = 'STANDARD_xlsm', synced_at = now()
  nazev se NEPLNÍ (Bezeichnung jde jen do oznaceni).

FILTR ŘÁDKŮ
  - obj. číslo (C) neprázdné, obsahuje aspoň jednu číslici, není hlavičkový zbytek (., SLAVE ID, MAT ID)
  - výrobce (D) neprázdný a != '.'   (tím vypadnou poznámky/oddílové řádky)

POUŽITÍ
  python3 kalk_kmen_standard_load.py <STANDARD.xlsm> [--out CLAUDE_SQL.sql] [--no-delete]
    <STANDARD.xlsm>  cesta ke STANDARD sešitu
    --out FILE       kam zapsat SQL (default: vytiskne na stdout).
                     Tip: --out scripts/claude_sql/CLAUDE_SQL.sql  a pak přes most (db=pg) = write banner.
    --no-delete      vynechá úvodní DELETE (jen INSERT/append)

POZN.: Schéma proj.kalk_kmen už musí mít sloupce (id, vyrobce, oznaceni, k_arb, k_vkm,
       hmotnost_kg, excel_*), PK na id a kmen_ec_id nullable — založeno 23.7.2026 (req #1365, #1370).
       Loader schéma NEMĚNÍ, jen data.
"""
import sys, os, argparse
import openpyxl

SKIP_SHEETS = {"Poznámky", "ukladani_data", "Rešerše"}
JUNK_REG = {".", "SLAVE ID", "MAT ID", "Typ / Bestell.-Nr.", "Bestell.-Nr.", ""}

# 0-indexované pozice sloupců (A=0, B=1, C=2, D=3, H=7, J=9)
COL_POZICE, COL_OZN, COL_REG, COL_VYR, COL_KOEF, COL_HMOT = 0, 1, 2, 3, 7, 9

def norm(v):
    return ("" if v is None else str(v)).strip()

def has_digit(s):
    return any(ch.isdigit() for ch in s)

def find_header_row(ws):
    """Najde řádek hlavičky (obsahuje 'Bestell'). Vrací index řádku (1-based) nebo None."""
    for i, r in enumerate(ws.iter_rows(min_row=1, max_row=12, values_only=True), 1):
        if "Bestell" in " | ".join(norm(x) for x in r):
            return i
    return None

def sql_q(s):
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"

def sql_num(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    t = str(v).strip().replace(",", ".")
    try:
        float(t); return t
    except ValueError:
        return "NULL"

def sql_int(v):
    if v is None:
        return "NULL"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    try:
        return str(int(float(str(v).strip().replace(",", "."))))
    except ValueError:
        return "NULL"

def cell(row, idx):
    return row[idx] if len(row) > idx else None

def build_sql(xlsm_path, include_delete=True):
    fn = os.path.basename(xlsm_path)
    wb = openpyxl.load_workbook(xlsm_path, data_only=True, read_only=True)
    rows_sql = []
    per_sheet = {}
    for ws in wb.worksheets:
        if ws.title in SKIP_SHEETS:
            continue
        hi = find_header_row(ws)
        if hi is None:
            continue
        cnt = 0
        for ri, r in enumerate(ws.iter_rows(min_row=hi + 1, values_only=True), start=hi + 1):
            reg = norm(cell(r, COL_REG))
            vyr = norm(cell(r, COL_VYR))
            if reg in JUNK_REG or not has_digit(reg):
                continue
            if not vyr or vyr == ".":
                continue
            ozn = norm(cell(r, COL_OZN)) or None
            koef = cell(r, COL_KOEF)
            vals = [
                sql_q(reg),                 # reg_cis
                sql_q(ozn),                 # oznaceni
                sql_q(vyr),                 # vyrobce
                sql_num(cell(r, COL_HMOT)), # hmotnost_kg
                sql_num(koef),              # k_vkm
                sql_num(koef),              # k_arb
                sql_q(fn),                  # excel_soubor
                sql_q(ws.title),            # excel_list
                sql_int(ri),                # excel_radek
                sql_int(cell(r, COL_POZICE)),  # excel_pozice
                sql_q("STANDARD_xlsm"),     # zdroj
                "now()",                    # synced_at
            ]
            rows_sql.append("(" + ",".join(vals) + ")")
            cnt += 1
        per_sheet[ws.title] = cnt

    cols = ("reg_cis, oznaceni, vyrobce, hmotnost_kg, k_vkm, k_arb, "
            "excel_soubor, excel_list, excel_radek, excel_pozice, zdroj, synced_at")
    parts = []
    if include_delete:
        parts.append("DELETE FROM proj.kalk_kmen;")
    if rows_sql:
        parts.append("INSERT INTO proj.kalk_kmen (" + cols + ") VALUES\n" + ",\n".join(rows_sql) + ";")
    sql = "\n".join(parts) + "\n"
    return sql, per_sheet

def main():
    ap = argparse.ArgumentParser(description="STANDARD Excel -> proj.kalk_kmen (DELETE+INSERT SQL)")
    ap.add_argument("xlsm", help="cesta ke STANDARD sešitu (.xlsm)")
    ap.add_argument("--out", help="soubor pro SQL (default stdout)")
    ap.add_argument("--no-delete", action="store_true", help="vynech úvodní DELETE (append)")
    args = ap.parse_args()

    if not os.path.exists(args.xlsm):
        sys.exit(f"CHYBA: soubor neexistuje: {args.xlsm}")

    sql, per = build_sql(args.xlsm, include_delete=not args.no_delete)
    total = sum(per.values())
    for t, c in per.items():
        print(f"  {t:26} {c}", file=sys.stderr)
    print(f"  {'CELKEM':26} {total}", file=sys.stderr)

    if args.out:
        tmp = args.out + ".tmp"
        with open(tmp, "w", newline="") as f:
            f.write(sql)
        os.replace(tmp, args.out)   # atomický rename (obchází nekoherentní mount cache)
        print(f"SQL zapsáno do {args.out} ({len(sql)} B, {total} řádků).", file=sys.stderr)
    else:
        sys.stdout.write(sql)

if __name__ == "__main__":
    main()
