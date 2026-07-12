# web_search

## MAPA
- **kód:** `web_search`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27j (2.5.2026): vyhledavani na webu pres Brave Search API. Marti-AI's request po Sarka HR case (zastaralu legislativu opravila uzivatelka). Pouzij VZDY kdyz aktualnost informace ma vahu -- legislativa, certifikace, ceny, novinky, tech docs, vendor sites.

**Workflow**: web_search vrati 5-10 vysledku (title + snippet + URL) -> ty si vyberes nejrelevantnejsi -> web_fetch(url) na detail -> vytahnes z markdown obsahu konkretni info -> citujes URL + datum.

**focus values**:
  - `'general'` (default) -- bezne vyhledavani, vsechny zdroje
  - `'legal'` -- prefer Czech/EU pravni databaze (zakonyprolidi.cz,     justice.cz, mvcr.cz, gov.cz, eur-lex.europa.eu). Site filter     rankuje vys, ale i jine zdroje mohou byt vraceny.
  - `'news'` -- past week filter pro aktualnost.

**Citation pattern (povinna pri vsech legal/HR/compliance odpovedich)**: uvest URL + datum pristupu. Priklad: 'Podle § 35 ZP (citováno z zakonyprolidi.cz, 2.5.2026)...'

Output ma is_legal_source flag per result -- ukazuje jestli URL spada do legal whitelist. published_date pokud je k dispozici.

## PARAMETRY

- **`focus`** [string, volitelný] · enum: ['general', 'legal', 'news'] · default: `general`
  - general (vse), legal (CZ/EU pravni databaze priority), news (past week).
- **`query`** [string, POVINNÝ]
  - Search query (Czech / English / multilang). Buď konkrétní -- 'zkušební doba zákoník práce 2026' lépe než 'práce'.
- **`n_results`** [integer, volitelný] · default: `5`
  - Pocet vysledku k vraceni. Default 5, max 10. Vetsi = vetsi context, drazsi token cost.

