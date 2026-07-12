# strategie_pg_update_row

## MAPA
- **kód:** `strategie_pg_update_row`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.4 (12.5.2026 vecer): UPDATE rows v PostgreSQL table. Funguje na LIBOVOLNEM schematu, kde Marti-AI ma GRANT UPDATE — typicky: fw.* (Marti-AI je owner), plus public.knowledge_topic / public.knowledge_entry (Phase knowledge base, 19.5.2026 vecer — explicit GRANT). NENI to omezeno na master/tenant/tenant_group/user schemata (ta jsou jen list_schemas validace).

PRAVO NA ROZMYSL PRED CINEM (Marti-AI's pattern 7.5. vecer):
  1. Nejdriv volej s dry_run=True → vidis SQL preview + matched_count.
  2. Pak zopakuj s dry_run=False → commit + RETURNING *.

Safety guards:
  • where MUSI byt non-empty dict (UPDATE bez WHERE = destruktivni, blokovany).
  • dry_run default True (musis explicit dat False pro commit).
  • Vraci updated rows pres RETURNING *.

Use case priklady:
  • fw.comp_type aktivace: schema='fw', table='comp_type',
    values={'status': 'active'}, where={'id': 2}
  • public.knowledge_entry update: schema='public',
    table='knowledge_entry', values={'body_md': '...',
    'updated_by_text': 'Marti-AI'}, where={'id': 1}

Pro IN-clause volej dvakrat (po jednom id), nebo pres query_table → pak update_row v batch.

## PARAMETRY

- **`table`** [string, POVINNÝ]
- **`where`** [object, POVINNÝ]
  - Dict {column: filter_value}, AND logic. MUSI byt non-empty (UPDATE bez WHERE blokovan).
- **`schema`** [string, POVINNÝ]
- **`values`** [object, POVINNÝ]
  - Dict {column: new_value} — co SET. Aplikuje na vsechny rows matching where.
- **`dry_run`** [boolean, volitelný] · default: `True`
  - True (default) = preview SQL + matched_count, bez UPDATE. False = execute + commit.

