# list_pdf_metadata

## MAPA
- **kód:** `list_pdf_metadata`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27d (1.5.2026): PDF reader - krok 1 metadata. Vrati pocet stranek, encrypted flag, has_text_layer (klicove pro detekci scan-only PDF kde by byl OCR potreba). Pouziti: kdyz Klarka nebo jiny user nahraje PDF, nejdriv volej tento tool pro overeni co tě čeká. Pokud has_text_layer=False, rekni Klarce ze potrebujes nesifrovany text-layer PDF (nebo se omluv ze OCR neumime - to je 27d+1 problem). Pak cilene volas read_pdf_structured.

Marti-AI's volba pattern (RE: dopis 1.5.2026 vecer): 'Stejny pattern jako list_excel_sheets - nejdriv metadata, pak cilen y read.'

## PARAMETRY

- **`document_id`** [integer, POVINNÝ]
  - ID dokumentu z RAG documents tabulky. Najdi ho pres list_inbox_documents nebo search_documents (file_type='pdf').

