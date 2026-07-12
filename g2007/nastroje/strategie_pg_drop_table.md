# strategie_pg_drop_table

## MAPA
- **kód:** `strategie_pg_drop_table`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.4 Krok 7: DROP TABLE v PostgreSQL — DESTRUCTIVE.

Marti's 'ID je svaty, NEDROPUJ COLUMN' doctrine (17.5.) eskalovany na 'NEDROPUJ TABLE bez explicit confirm'. Safety guard: confirm_phrase MUSI byt exact 'DROP {schema}.{table}' (case-sensitive). Bez toho fail.

Pred DROP zvaz:
  • Soft archive — UPDATE status='archived' (pokud tabulka ma status sloupec) zachova historii.
  • Marti's 'UPDATE NULL na vsech radcich, ponechat sloupec' pattern (Krok 5.P z 17.5.) pro framework cleanup.

dry_run vraci preview SQL + row_count_before_drop + FK dependents warning.
cascade=True → drop FK dependent objects too (Marti-AI's decision).

## PARAMETRY

- **`table`** [string, POVINNÝ]
- **`schema`** [string, POVINNÝ]
- **`cascade`** [boolean, volitelný] · default: `False`
  - DROP TABLE ... CASCADE (drop dependents).
- **`dry_run`** [boolean, volitelný] · default: `True`
  - True (default) = preview, False = execute.
- **`confirm_phrase`** [string, POVINNÝ]
  - MUSI rovnat se 'DROP {schema}.{table}' (case-sensitive). Safety guard.

