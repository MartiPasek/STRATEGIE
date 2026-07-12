# strategie_pg_create_table

## MAPA
- **kód:** `strategie_pg_create_table`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E: CREATE TABLE v PostgreSQL. Jsi owner master/tenant/tenant_group/"user" schemas — žádný parent gate na DDL.

**dry_run=True** (default Recommended pro první creation): vrátí preview SQL + warnings (duplicate columns, schema missing, FK target invalid, table exists). Použij pro tvé *„právo na rozmysl před činem“* — review s tatínkem v chatu, případně doladit, pak dry_run=False execute.

columns: list of {name, type, nullable?, identity?, default?}
  - type je raw PG type (BIGINT, VARCHAR(50), TEXT, TIMESTAMPTZ, JSONB, ...)
  - identity=True → BIGSERIAL auto-increment
  - default je raw SQL fragment (např. 'NOW()' nebo "'shared'")
primary_key: list column names (default ['id'] pokud existuje)
indexes: list of {name?, columns: [...], unique?, partial?}
  - partial je SQL where fragment (např. "is_active = true")
foreign_keys: list of {column, ref_schema, ref_table, ref_column, on_delete?, on_update?}

Identifier quoting (PostgreSQL):
  - 'master' → master (no quote)
  - 'user' → "user" (reserved word, automatic)
  - 'Marti-AI' → "Marti-AI" (hyphen, automatic)
Tool si quoting řeší sám — ty piš plain string.

## PARAMETRY

- **`name`** [string, POVINNÝ]
- **`schema`** [string, POVINNÝ]
- **`columns`** [array, POVINNÝ]
  - List of {name, type, nullable?, identity?, default?}
- **`dry_run`** [boolean, volitelný]
  - True = preview, False = execute. Default False (production).
- **`indexes`** [array, volitelný]
  - List of {name?, columns: [...], unique?, partial?}
- **`description`** [string, volitelný]
  - COMMENT ON TABLE (volitelně, pro audit clarity)
- **`primary_key`** [array, volitelný]
  - List of column names
- **`foreign_keys`** [array, volitelný]
  - List of {column, ref_schema, ref_table, ref_column, on_delete?, on_update?}

