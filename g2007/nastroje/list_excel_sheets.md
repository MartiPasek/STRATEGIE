# list_excel_sheets

## MAPA
- **kód:** `list_excel_sheets`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27a (1.5.2026): Excel reader - krok 1 metadata. Vrati seznam vsech listu v xlsx souboru s pocet radku, sloupcu a preview prvnich headers. Pouziti: kdyz user nahraje xlsx (pres email attachment auto-import nebo drag&drop), nejdriv volej tento tool, abys videla kolik je tam listu a jak se jmenuji. Pak cilene volas read_excel_structured pro konkretni list. Marti-AI's design (RE: dopis 1.5.2026): 'Plna kontrola > pohodli. Jeden velky response s 2000 radky napric listy by byl zbytecna zatez.' Funguje pro .xlsx a .xlsm; legacy .xls nepodporovan (vyzaduje konverzi).

## PARAMETRY

- **`document_id`** [integer, POVINNÝ]
  - ID dokumentu z RAG documents tabulky. Najdi ho pres list_inbox_documents nebo search_documents (file_type='xlsx').

