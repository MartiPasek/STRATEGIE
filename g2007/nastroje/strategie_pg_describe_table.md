# strategie_pg_describe_table

## MAPA
- **kód:** `strategie_pg_describe_table`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: Kompletní struktura PostgreSQL tabulky — sloupce (typ, nullable, default), indexy, constraints (PK/FK/UNIQUE/CHECK), row count estimate. Použij před modifikací nebo pro orientaci v existing schema (md_documents, project_memo, conversations atd.).

## PARAMETRY

- **`table`** [string, POVINNÝ]
  - Table name.
- **`schema`** [string, POVINNÝ]
  - Schema name.

