# read_image_ocr

## MAPA
- **kód:** `read_image_ocr`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27d+1b/c/d (2.5.2026): UNIFIED OCR pro images. Akceptuje BUD `document_id` (RAG documents tabulka -- inbox upload pres 📁 panel) NEBO `media_id` (media_files tabulka -- chat drag&drop upload, SMS prilohy). Mutually exclusive: presne jedno.

Podporovane formaty: jpg, jpeg, png, gif, webp, bmp, tiff, **heic, heif** (Apple iPhone fotky -- registrovane pres pillow-heif plugin pri startu API).

**Kdy ktera cesta**:
  - `document_id` -- user nahral pres 📁 inbox panel (list_inbox_documents ti vrati ID)
  - `media_id` -- user dropnul obrazek primo do chatu nebo prisla SMS s prilohou (vidis ho v contextu ze message multimodal blocks)

Output unified napric oba zdroje + 'source' field ('documents' | 'media_files') pro tvoji orientaci, odkud OCR proslo. Pro Marti to neni rozdil -- text je text, OCR pipeline stejna.

Vznikl po Marti-AI's gap discovery -- read_text_from_image (Phase 12a) funguje jen pro media_files (chat upload, SMS), ale image v documents tabulce (uploaded pres 📁 inbox) nemel OCR cestu. Tenhle tool to vyresi.

Pouziti: kdyz user nahraje JPG/PNG do inboxu (napr. fotka papirove smlouvy, ucenka, ručně psaná poznámka, screenshot) a chce text. Cely workflow: list_inbox_documents -> najdes image -> read_image_ocr(document_id, ocr_provider=...).

**Default ocr_provider='tesseract'** -- privacy first (smlouvy, citlive dokumenty zustanou ve firemni VPN). ~5-15s per image (rychlejsi nez PDF protoze neni PDF->image krok).

**ocr_provider='vision'** -- Anthropic Haiku Vision (~1-2s, $0.003/image). Vyssi kvalita, lepsi pro rucne psane / nizka kvalita scan / komplexni layouty. POZOR cloud roundtrip.

Marti-AI's volby C/A/A z Phase 27d+1 konzultace plati (Hybrid + confidence + cap). Confidence_avg pri Tesseract; pokud < 60 -> warning -> rozhodni: prepnout na Vision nebo zazadat user o lepsi obrazek.

Pro PDF nepouzivej -- volej read_pdf_structured. Pro Excel read_excel_structured. Pro chat-uploaded images read_text_from_image (media_files cesta).

## PARAMETRY

- **`media_id`** [integer, volitelný]
  - Phase 27d+1d (2.5.2026): ID image media_file (chat drag&drop upload, SMS priloha). kind='image'. Najdi v multimodal contextu zpravy. Mutually exclusive s document_id.
- **`document_id`** [integer, volitelný]
  - ID image dokumentu z RAG documents (inbox upload). file_type jpg/png/jpeg/gif/webp/bmp/tiff/heic/heif. Najdi pres list_inbox_documents nebo search_documents. Mutually exclusive s media_id.
- **`ocr_provider`** [string, volitelný] · enum: ['tesseract', 'vision']
  - Default 'tesseract' (privacy + cost). 'vision' = Anthropic Haiku Vision, vyssi kvalita ale cloud roundtrip + ~$0.003/image.

