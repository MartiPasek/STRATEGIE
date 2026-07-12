# read_excel_structured

## MAPA
- **kód:** `read_excel_structured`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27a (1.5.2026): Excel reader - krok 2 data. Vrati structured rows z konkretniho listu xlsx jako list of dicts (headers -> values). Workflow: nejdriv list_excel_sheets pro metadata, pak tento tool s konkretnim sheet_name. Pro velke listy (>500 rows) pouzij offset/limit pagination. Marti-AI's design rozhodnutí (RE: dopis 1.5.2026): datum/cas → ISO string ('2026-09-01T08:00:00'); prazdne bunky → null; cisla → vzdy float; vzorce → computed value; chyby (#N/A, #REF!) → null + warning v warnings list. Cap 500 radku per call (safeguard).

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Pagination: max kolik radku vratit (default 500, max 500). Vyssi hodnota se tise sklamne na 500 (context window safeguard).
- **`offset`** [integer, volitelný]
  - Pagination: kolik radku preskocit (default 0). Pro 2. stranku 500 radku → offset=500, limit=500.
- **`sheet_name`** [string, volitelný]
  - Jmeno listu (preferovano nad sheet_index). Default = prvni list. Najdes ho pres list_excel_sheets.
- **`document_id`** [integer, POVINNÝ]
  - ID dokumentu z RAG documents.
- **`sheet_index`** [integer, volitelný]
  - 0-based index listu (alternative k sheet_name). Vetšinou pouzivej sheet_name -- robustnejsi.

