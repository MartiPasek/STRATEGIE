# strategie_pg_query_raw

## MAPA
- **kód:** `strategie_pg_query_raw`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: Read-only raw PostgreSQL SQL. WHITELIST: jen SELECT/WITH/EXPLAIN/SHOW. Pro DDL/DML použij dedicated tools (create_table, insert_row, ...).

Použij pro composite queries (JOIN, GROUP BY, agregace) které query_table neumí. Příklad: SELECT count(*) FROM fw.entity_def WHERE tier = 'master' GROUP BY is_active.

## PARAMETRY

- **`sql`** [string, POVINNÝ]
  - SELECT / WITH / EXPLAIN / SHOW SQL.
- **`params`** [object, volitelný]
  - Volitelné parametrizace {param_name: value}, v SQL referenced jako :param_name.

