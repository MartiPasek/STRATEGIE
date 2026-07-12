# strategie_pg_insert_row

## MAPA
- **kód:** `strategie_pg_insert_row`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E + Phase 38.4 polish (10.5.2026): INSERT one or many rows do PostgreSQL tabulky. Vrátí vložený row(s) (RETURNING *) — uvidíš generated IDs + defaults.

values přijímá DVĚ varianty:
  • dict — single row insert: {column: value, ...}
  • list[dict] — batch insert (uniform schema): [{c1:v1, c2:v2}, {c1:v3, c2:v4}, ...]

Batch musí mít všechny rows se STEJNÝMI columns (heterogeneous = volat opakovaně).

Tool aplikuje quoting automaticky. Audit: každý insert se loguje (STRATEGIE_PG prefix v logu, batch=true|false flag).

## PARAMETRY

- **`table`** [string, POVINNÝ]
- **`schema`** [string, POVINNÝ]
- **`values`** [?, POVINNÝ]
  - Single dict (one row) NEBO list of dicts (batch, uniform schema).

