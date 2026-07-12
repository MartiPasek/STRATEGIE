# strategie_pg_create_trigger

## MAPA
- **kód:** `strategie_pg_create_trigger`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.4 Krok 7: CREATE TRIGGER v PostgreSQL.

Pred volanim musi trigger function existovat (vytvor pres create_function nejdriv, s returns='trigger').

timing: 'BEFORE' | 'AFTER' | 'INSTEAD OF'
event: 'INSERT' | 'UPDATE' | 'DELETE' | 'TRUNCATE'
  Multi-event: pass raw string napr. 'INSERT OR UPDATE'
for_each: 'ROW' (default) | 'STATEMENT'

when_condition (volitelne): RAW WHEN clause fragment
  Priklad: 'OLD.status IS DISTINCT FROM NEW.status'

replace=True (default) → DROP IF EXISTS + CREATE (PG nema CREATE OR REPLACE TRIGGER pred PG 14, emulujeme).

Use case priklad — update_updated_at trigger:
  schema='fw', table='comp_def', name='trg_comp_def_updated_at',
  timing='BEFORE', event='UPDATE', for_each='ROW',
  function_schema='fw', function_name='update_updated_at'.

## PARAMETRY

- **`name`** [string, POVINNÝ]
  - Trigger name.
- **`event`** [string, POVINNÝ]
  - 'INSERT' | 'UPDATE' | 'DELETE' | 'TRUNCATE'. Multi: raw string napr. 'INSERT OR UPDATE'.
- **`table`** [string, POVINNÝ]
  - Target table.
- **`schema`** [string, POVINNÝ]
  - Schema target tabulky.
- **`timing`** [string, POVINNÝ]
  - 'BEFORE' | 'AFTER' | 'INSTEAD OF'
- **`dry_run`** [boolean, volitelný] · default: `True`
  - True (default) = preview, False = execute.
- **`replace`** [boolean, volitelný] · default: `True`
  - DROP IF EXISTS + CREATE (default True).
- **`for_each`** [string, volitelný] · default: `ROW`
  - 'ROW' (default) | 'STATEMENT'.
- **`function_name`** [string, POVINNÝ]
  - Trigger function name (must return trigger).
- **`when_condition`** [string, volitelný]
  - Optional WHEN clause raw fragment (napr. 'OLD.status IS DISTINCT FROM NEW.status').
- **`function_schema`** [string, POVINNÝ]
  - Schema trigger function.

