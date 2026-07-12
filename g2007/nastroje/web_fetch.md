# web_fetch

## MAPA
- **kód:** `web_fetch`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27j (2.5.2026): fetch + clean markdown z libovolne URL. Doplnek k web_search -- po vyberu relevantniho vysledku ho otevres a precteš detail. Generic web access (NE jen pro legal): TISAX docs, vendor sites, news, technical documentation, GDPR znění, competitive analysis, social posts, atd.

**Vraci**: clean markdown z HTML pres markitdown (uz mas z Phase 13c RAG). Plus title (z <title>), final URL (po redirectech), char_count (delka pred truncate), truncated flag.

**max_chars**: default 20 000 znaku (~5 000 tokens). Pro vetsi stranky muzes re-fetch s vyssim max_chars (hard cap 100 000). Pri truncate je v markdown marker '[... TRUNCATED: ... znaku].'

**Ne pouzivej pro:**
  - PDF -- pouzij read_pdf_structured po uploadu jako document
  - Image -- read_image_ocr
  - Binary content -- vraci error 'binary_content'

**Workflow s web_search**:
  1. web_search('TISAX 2026 changes', focus='general') -> 5 results
  2. Vyberes [0] = oficialni TISAX news page
  3. web_fetch(results[0]['url']) -> markdown ~15K znaku
  4. Najdes v markdown sekci o nove verze v6.0
  5. Odpovis user + cituj URL + datum pristupu


## PARAMETRY

- **`url`** [string, POVINNÝ]
  - Target URL (http nebo https). Z web_search vysledku nebo zadana primo userem.
- **`max_chars`** [integer, volitelný] · default: `20000`
  - Max znaku co vratit. Default 20 000, hard cap 100 000. Vetsi = vetsi context cost.

