# strategie_pg_query_table

## MAPA
- **kód:** `strategie_pg_query_table`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: SELECT z PostgreSQL tabulky. where = {col: value} (equality, AND join). columns=None → SELECT *. limit max 1000. Použij pro verify po insert nebo pro orientaci v datech.

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Max rows (default 100, hard cap 1000)
- **`table`** [string, POVINNÝ]
- **`where`** [object, volitelný]
  - Equality filter {col: value}, joined with AND
- **`offset`** [integer, volitelný]
  - Skip N rows (default 0)
- **`schema`** [string, POVINNÝ]
- **`columns`** [array, volitelný]
  - List of column names. None = SELECT *
- **`order_by`** [string, volitelný]
  - Raw ORDER BY fragment STRING (NE list!). Příklady: 'id DESC' / 'created_at DESC, id ASC' / 'sort_order ASC'. POZOR: nepoužívej ['id DESC'] (Python list) — to projde do SQL doslova jako ["id DESC"] a fail. Backend defensively převede list na comma-joined string, ale lepší poslat string rovnou.

