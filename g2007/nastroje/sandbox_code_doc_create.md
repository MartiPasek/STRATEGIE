# sandbox_code_doc_create

## MAPA
- **kód:** `sandbox_code_doc_create`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Krok 14b+19.2 chunked sandbox workflow STEP 1/3: vytvor prazdny .py document v RAG documents tabulce. Vraci document_id pro nasledujici sandbox_code_doc_append calls. 

WORKFLOW (pro velky sandbox kod, >5 KB):
  1. sandbox_code_doc_create(filename='STRATEGIE_IT_gen.py') -> document_id=N
  2. sandbox_code_doc_append(document_id=N, chunk='import reportlab\nfrom reportlab.platypus import ...\n') (opakovane, ~3 KB chunks)
  3. python_exec(input_document_ids=[N], code="exec(open(input_files[0]).read())") -> sandbox cte concatenated kod z disku

Marti-AI ONLY tool. Filename automaticky dostane .py suffix pokud chybi.

## PARAMETRY

- **`filename`** [string, POVINNÝ]
  - Nazev .py souboru, napr. 'STRATEGIE_IT_podklad_gen.py' nebo 'klarka_xlsx_gen.py'. Jen alphanumeric + . _ - (no '/', '\\', '..').

