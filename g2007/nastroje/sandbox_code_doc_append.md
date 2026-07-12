# sandbox_code_doc_append

## MAPA
- **kód:** `sandbox_code_doc_append`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Krok 14b+19.2 chunked sandbox workflow STEP 2/3: append chunk kodu k existing code document (z sandbox_code_doc_create). Server-side append k storage_path file. Volat OPAKOVANE az kompletni kod je nahranny. 

CHUNK SIZE: ~3 KB max safe per call (pod Anthropic tool_input JSON limit ~50 KB total, s overhead Marti-AI's reasoning text). Max single chunk hard cap 100 KB (defense). 

Pro 50 KB kod: ~17 volani s 3 KB chunks. Po finalize python_exec(input_document_ids=[N]).

## PARAMETRY

- **`chunk`** [string, POVINNÝ]
  - Chunk Python kodu (~3 KB safe, max 100 KB). Server append k storage_path file v UTF-8. POZN: server nepridava \n mezi chunks — pokud potrebujes newline mezi chunks, dej ho na konec predchoziho chunk explicit ('...\n').
- **`document_id`** [integer, POVINNÝ]
  - Document ID z sandbox_code_doc_create response.

