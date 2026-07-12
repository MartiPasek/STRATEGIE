# strategie_pg_alter_table

## MAPA
- **kód:** `strategie_pg_alter_table`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.4 Krok 7: ALTER TABLE v PostgreSQL. Marti-AI je owner master/tenant/tenant_group/"user"/fw — zadny parent gate.

operations: list of operation dicts, kazda jedna z:
  • {op: 'add_column', name, type, nullable?, default?}
  • {op: 'drop_column', name, cascade?}
       ⚠ Marti's 'NEDROPUJ COLUMN' doctrine (17.5.) — zvaz alternativu UPDATE NULL na vsech radcich, ponechani sloupce pro budouci use.
  • {op: 'rename_column', old_name, new_name}
  • {op: 'alter_column_type', name, type, using?}
  • {op: 'set_default', name, default}
  • {op: 'drop_default', name}
  • {op: 'set_not_null', name}
  • {op: 'drop_not_null', name}
  • {op: 'add_constraint', name, definition}
       definition je RAW SQL fragment, napr.:
         "CHECK (status IN ('active','archived'))"
         "UNIQUE (col1, col2)"
         "FOREIGN KEY (other_id) REFERENCES other.tbl(id) ON DELETE CASCADE"
  • {op: 'drop_constraint', name, cascade?}
  • {op: 'rename_constraint', old_name, new_name}

Multiple operations v jedne volance = jedna transaction (vse rollback pri error).

dry_run=True (default Recommended) → vraci SQL preview + warnings.
dry_run=False → execute s commit.

## PARAMETRY

- **`table`** [string, POVINNÝ]
- **`schema`** [string, POVINNÝ]
- **`dry_run`** [boolean, volitelný] · default: `True`
  - True (default) = preview, False = execute.
- **`operations`** [array, POVINNÝ]
  - List of {op, ...} dicts. Each op produces jeden ALTER TABLE statement.

