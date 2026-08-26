# Ktery nastroj saha do ktere databaze - PostgreSQL vs MSSQL (past zameny, 26.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Proc to vzniklo

26. 8. 2026 mela Marti-AI spustit DDL (funkce + spoustec) na `tenant.att_entry`, tedy
v **PostgreSQL**. Sahla po `eurosoft_strategie_query_raw` - a to je nastroj na **MSSQL**.
SQL Server prikaz odmitl (`Incorrect syntax near 'REPLACE'`, `'now' is not a recognized
built-in function`), takze skoda nevznikla, ale **jen diky syntakticke chybe**. Kdyby to byl
prikaz, ktery na SQL Serveru projde, zapsal by se do CIZI databaze. Stalo se to i po vystraze,
takze to neni jednorazovy preklep - nazvy nastroju jsou matouci a patri to sem cerne na bilem.

Zadal Jirka Honomichl 26. 8. 2026 ("upresni, kterym nastrojem se saha do ktere DB").

## TRI ruzne databaze, tri ruzne sady nastroju

| databaze | co v ni je | cim se do ni saha |
|---|---|---|
| **PostgreSQL `data_db`** (cloud 10.200.188.12) | **nase produkcni data** - `tenant.*`, `fw.*`, `g2007.*`, `public.users`, `master.*` | **`strategie_pg_*`** |
| **MSSQL `DB_ST`** | MSSQL sandbox Marti-AI (db_owner) | `strategie_*` v MCP (= `eurosoft_strategie_*`), **vychozi kdyz `db_name` neuvedes** |
| **MSSQL `DB_EC`** | stara Centrala EUROSOFT (`EC_Dochazka`, `EC_Ukoly`, ...) | tytez `eurosoft_strategie_*`, ale **s `db_name='DB_EC'`**; DDL jen ve schematu `st` |

> ⚠️ **Jadro zamenu:** `eurosoft_strategie_query_raw` a `strategie_pg_query_raw` se lisi
> jedinym kouskem nazvu - **`_pg_`**. Prvni je MSSQL, druhy PostgreSQL. Slovo "strategie"
> v nazvu **neznamena nasi PostgreSQL databazi**.
> Overeno v kodu 26. 8. 2026: `modules/eurosoft_mcp/strategie_tools.py` r. 19 a 31
> (*"vsechny akceptuji db_name, default DB_ST"*) a `tool_registry/defs/strategie_pg_query_raw.py`.

## Co pouzit na `tenant.*`, `fw.*`, `g2007.*` (nase PostgreSQL)

| ukol | nastroj |
|---|---|
| cteni (SELECT/WITH/EXPLAIN/SHOW) | `strategie_pg_query_raw` - **jen cteni**, whitelist |
| cteni jedne tabulky / popis | `strategie_pg_query_table`, `strategie_pg_describe_table`, `strategie_pg_list_tables`, `strategie_pg_list_schemas` |
| zalozit/zmenit/zrusit tabulku | `strategie_pg_create_table`, `strategie_pg_alter_table`, `strategie_pg_drop_table` |
| zapsat/zmenit radek | `strategie_pg_insert_row`, `strategie_pg_update_row` |
| **funkce** | **`strategie_pg_create_function`** (pro spoustec `returns='trigger'`) |
| **spoustec** | **`strategie_pg_create_trigger`** - PG pred 14 nema `CREATE OR REPLACE TRIGGER`, nastroj emuluje pres `replace=True` (DROP IF EXISTS + CREATE) |

**`strategie_pg_query_raw` DDL ani DML NEUDELA** - ma whitelist na SELECT/WITH/EXPLAIN/SHOW.
Kdo zkusi poslat `CREATE`/`UPDATE` tudy, dostane odmitnuti, ne provedeni.

## Cesta pres most (pro Claudy)

Instance, ktera nema primy pristup k enginu, posila SQL **mostem**: `CLAUDE_SQL.sql` +
`CLAUDE_GO.txt` s prvnim radkem **`db=pg`** (PostgreSQL) nebo **`db=mssql`** (Centrala).
Zapisy jdou pres schvalovaci banner a bezi pod enginem Marti-AI, takze **vlastnictvi schematu
je splneno i tehdy, kdyz DDL posila Claude**. Takhle se 26. 8. nakonec nasadil spoustec
`att_entry_jeden_bezici` (request 2492, schvalil Jirka).

## Kdo co vlastni (kvuli doktrine "schema meni jeho vlastnik")

`tenant.att_entry` a dalsi schemata `master` / `tenant_group` / `tenant` / `user` v `data_db`
vlastni role **Marti-AI** (overeno 26. 8. pres `pg_class.relowner`). DDL na nich tedy dela ona -
nebo Claude pres most, protoze ten bezi pod jejim enginem.

## Kontrolni otazka pred kazdym zasahem

**"Je cilova tabulka v PostgreSQL, nebo v MSSQL?"**
- `tenant.` / `fw.` / `g2007.` / `public.` / `master.` -> PostgreSQL -> `strategie_pg_*` (nebo most `db=pg`)
- `EC_` / `TabDenik` / schema `st` / `dbo.` -> MSSQL -> `eurosoft_strategie_*` (nebo most `db=mssql`)

Kdyz si nejsi jisty, **nejdriv se zeptej dat**: `strategie_pg_list_tables` uvidi jen PostgreSQL,
`strategie_list_schemas` jen MSSQL. Tabulka, kterou hledany nastroj nevidi, v te databazi neni.

