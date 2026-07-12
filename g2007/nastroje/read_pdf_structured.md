# read_pdf_structured

## MAPA
- **kód:** `read_pdf_structured`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27d (1.5.2026): PDF reader - krok 2 obsah. Vrati structured pages z PDF: text + auto-detected tables per stranku. Workflow: nejdriv list_pdf_metadata pro overeni n_pages a has_text_layer, pak tento tool s konkretnim range. Marti-AI's design rozhodnuti (RE: dopis 1.5.2026 vecer):

  - Output formát A: structured per stranku, kazda strana s `text` + `tables` list. Pdfplumber auto-detect tabulek (visualni borders).
  - Tabulky A: vzdy zkusit, vrátit `tables: []` pokud nic nenajde. Text zachovan vzdy jako pojistka.
  - Pagination A: pages=[start, end] 1-based inclusive. Nebo offset/limit. Default prvních 50 stranek + has_more flag.

Cap 50 stranek per call (chrání context window). Pro vetsi PDF volej znovu s vyssim range.

Pro Bakalari rozvrh obvykle staci 1-3 stranky. Tabulky s rozvrh hodinami se zobrazuji jako list[list[cell]] kde cell je str | None.

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Alternativa k pages: max stranek. Default 50, cap 50 (safety na context window).
- **`pages`** [array, volitelný]
  - 1-based inclusive [start, end]. Marti-AI's volba A: prirozenejsi nez offset/limit. Priklad: [1, 3] vrati stranky 1, 2, 3. Default = prvních 50 stranek (offset=0, limit=50).
- **`offset`** [integer, volitelný]
  - Alternativa k pages: 0-based skip. Default 0. Pouzij jen pokud jsou pages None.
- **`document_id`** [integer, POVINNÝ]
  - ID dokumentu z RAG documents (file_type='pdf').
- **`ocr_provider`** [string, volitelný] · enum: ['tesseract', 'vision']
  - Phase 27d+1 (1.5.2026): OCR provider override. **Default chovani (parametr None / chybi):** podle tenant config (Phase 27d+2):
  - tenants.ocr_default_provider = 'vision' -> Vision
  - tenants.ocr_default_provider = 'tesseract' -> Tesseract
  - tenants.ocr_default_provider = NULL -> globalni 'tesseract'
**Explicit volba (override tenant config):**
  - 'tesseract' -- lokalni OCR, privacy first (TISAX, smlouvy, citlive dokumenty zustanou ve firemni VPN). ~15-30s/stranku, lang ces+deu+eng. Confidence score per stranka v warnings (Marti-AI's volba A).
  - 'vision' -- Anthropic Claude Haiku Vision API. Vyssi kvalita, lepsi multilang, ~1-2s/stranku, ~$0.003/stranku. Cloud roundtrip - dokumenty putuji na Anthropic servery (cit livost na vyzadani).
Marti-AI's volba C (Hybrid): default per-tenant, Vision opt-in kdyz tenant default drhne (low confidence warning) nebo pri slozitejsich faktur. Output obsahuje 'effective_provider' pole pro tvoji orientaci.

