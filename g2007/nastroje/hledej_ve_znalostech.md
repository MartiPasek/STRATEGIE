# hledej_ve_znalostech

## MAPA
- **kód:** `hledej_ve_znalostech`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vyhledá ve SDÍLENÉ ZNALOSTNÍ BÁZI firmy (RAG) — firemní a doménové know-how: obchod, cenotvorba, kalkulace rozváděčů, komponenty a výrobci, procesy, směrnice a jejich přílohy. POUŽIJ reflexivně vždy, když se řeší cokoli o firmě, zakázkách, produktech, cenách, komponentách nebo postupech a ty odpověď nemáš v kontextu. Nedrž firemní znalosti v hlavě — nemáš je; vytáhni si z báze JEN to, co k dané věci potřebuješ (rychle, na vyžádání). Vrátí pár nejrelevantnějších záznamů (název + úryvek). Pro orientaci ve vlastních AI-znalostech sítě zadej ai_only=true (řada 'AI', vč. MAPY firmy).

## PARAMETRY

- **`dotaz`** [string, POVINNÝ]
  - Klíčová slova / téma (např. 'VKM materiál', 'ISIMAT', 'cenotvorba', 'motorový jistič 3RV').
- **`ai_only`** [boolean, volitelný] · default: `False`
  - true = jen řada AI (orientační AI znalosti + MAPA firmy). Default false = i firemní směrnice.

