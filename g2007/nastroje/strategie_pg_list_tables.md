# strategie_pg_list_tables

## MAPA
- **kód:** `strategie_pg_list_tables`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: Vrátí tabulky v PostgreSQL schémamu. schema=None → všechna tvá schémata (master/tenant/tenant_group/user). schema='public' → existující operational tables (read-only). Vrací size_bytes + column_count + description (z COMMENT ON TABLE).

## PARAMETRY

- **`schema`** [string, volitelný]
  - Schema name. None = všechna tvá schémata.

