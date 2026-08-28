# Fw data set sql validace po zapisu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**fw.data_set: sql_text se nevaliduje při uložení — syntaktická chyba se projeví až za běhu. Povinné ověření po každé změně.**

# fw.data_set — validace sql_text po zápisu

**Zjištěno:** 27.8.2026, C-28 (okno strategie-a4), zdroj dochazka.prehled_dnu_clovek

## Klíčová vlastnost (past)

`fw.data_set.sql_text` se při UPDATE **nijak nevaliduje** — most vrátí "WRITE OK" i pro syntakticky chybný SQL. Chyba se projeví až prvním voláním datového zdroje za běhu (`sql_execute_failed`).

## Konkrétní příklad — rezervované slovo DO

CTE se sloupci pojmenovanými `od` a `do`:
```sql
WITH p AS (SELECT $1 AS od, $2 AS do ...)
SELECT do FROM p  -- ← syntax error at or near "do"
```
`do` je v PostgreSQL rezervované slovo (používá se v `DO $$ ... $$` bloku). Zápis do fw.data_set proběhl bez varování, rozbil se až za běhu — a to **všechny dotazy nad daným zdrojem**, ne jen nový.

**Oprava:** přejmenovat na `p_od` / `p_do` (nebo jiný prefix mimo rezervovaná slova).

## Povinný postup po každé změně sql_text

1. UPDATE fw.data_set SET sql_text = ... WHERE id=X AND md5(sql_text)='...' (pojistka)
2. **POVINNĚ zavolat** `/api/v1/erp/data/{code}` a ověřit `ok: true`
3. Teprve po `ok: true` považovat změnu za hotovou

Nestačí "WRITE OK" z mostu — to potvrzuje jen zápis do DB, ne syntaktickou správnost SQL.

## Rezervovaná slova PostgreSQL — nejčastější pasti v CTE aliasech

- `do`, `end`, `in`, `out`, `to`, `as`, `on`, `or`, `by`, `is`
- Bezpečný vzor: prefixovat parametry CTE (`p_od`, `p_do`, `p_from`, `p_to`)

## Dopad při chybě

Syntaktická chyba v sql_text rozbije **všechna volání** daného datového zdroje — nejen ta, která využívají nový kód. Ostatní datové zdroje zůstanou funkční.

## Verze data_setu po opravě

Po každé obsahové změně sql_text zvedni `version` o 1 (doktrína platí pro fw.data_set stejně jako pro g2007.python).

_Souvisí:_ doc-system-g2007-standard-prace-overovani

