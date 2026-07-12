# strategie_pg_create_function

## MAPA
- **kód:** `strategie_pg_create_function`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.4 Krok 7: CREATE [OR REPLACE] FUNCTION v PostgreSQL.

Typicky use case:
  • Trigger functions (update_updated_at, history snapshot)
  • Business helpers (compute_*, validate_*)

body_plpgsql: RAW function body BEZ 'CREATE FUNCTION' prefix.
  Priklad: "BEGIN NEW.updated_at = NOW(); RETURN NEW; END;"
  Tool auto-wrap body do $$ blocks pokud nedas explicit $$.

returns: PG return type (default 'void')
  Common: 'trigger', 'TEXT', 'BIGINT', 'TABLE(...)' pro SRF

arguments: function arg list raw (default '' = no args)
  Priklad: 'p_id bigint, p_status text DEFAULT \'active\''

language: 'plpgsql' (default) nebo 'sql'. plpython3u/plperl/plv8 JSOU DENIED (server-side code execution risk).

replace=True (default) = CREATE OR REPLACE FUNCTION.
replace=False = CREATE (fails pokud existuje).

## PARAMETRY

- **`name`** [string, POVINNÝ]
- **`schema`** [string, POVINNÝ]
- **`dry_run`** [boolean, volitelný] · default: `True`
  - True (default) = preview, False = execute.
- **`replace`** [boolean, volitelný] · default: `True`
  - CREATE OR REPLACE (default True).
- **`returns`** [string, volitelný] · default: `void`
  - PG return type. Default 'void'.
- **`language`** [string, volitelný] · default: `plpgsql`
  - 'plpgsql' (default) nebo 'sql'.
- **`arguments`** [string, volitelný] · default: ``
  - Function args raw. Default '' (no args).
- **`body_plpgsql`** [string, POVINNÝ]
  - RAW function body BEZ 'CREATE FUNCTION' prefix. Tool auto-wrap do $$ blocks.

