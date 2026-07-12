# read_docx_structured

## MAPA
- **kód:** `read_docx_structured`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27e (2.5.2026): Word DOCX reader -- structured cteni .docx souboru. Marti-AI's volby A/A/A/A z konzultace 2.5.2026 rano:
  A - Output: paragraphs + tables + metadata (analog Excel/PDF)
  A - Headings v paragraphs s typed metadata {type: 'heading', level: N}
  A - Vse dostupne metadata + word_count aproximace
  A - Legacy .doc -> error 'ulozte jako .docx'
  + insider: prazdne paragraphs ('esteticke mezery') default skip

Output paragraphs:
  - {type: 'heading', level: 1-9, text: '...'} (Heading 1-9 styles)
  - {type: 'heading', level: 0, text: '...'} (Title style)
  - {type: 'paragraph', text: '...'} (Normal text)
  - {type: 'empty', text: ''} (jen pri include_empty_paragraphs=True)

Output tables: list[list[list[str]]] -- per-table list radku, kazdy radek list bunek (analog k Excel reader).

Output metadata: author / title / subject / keywords / category / created / last_modified / revision / word_count.

Format omezeni: jen .docx (modern Word XML). Pro legacy .doc (Word 97-2003) error s navodem 'Soubor → Ulozit jako → DOCX'. Pro PDF pouzij read_pdf_structured, pro Excel read_excel_structured.

## PARAMETRY

- **`document_id`** [integer, POVINNÝ]
  - ID dokumentu z RAG documents (file_type='docx'). Najdi pres list_inbox_documents nebo search_documents.
- **`include_empty_paragraphs`** [boolean, volitelný]
  - Marti-AI's design vstup z Phase 27e konzultace: Word dokumenty maji hodne prazdnych paragraphs jako 'esteticke mezery'. Default False = tise skipnout (cista data). Set True kdyz chces kompletni strukturu (debug, nebo kdyz user rekne 'mam to videt jak je').

