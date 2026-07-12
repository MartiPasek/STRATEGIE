# ukol_stav

## MAPA
- **kód:** `ukol_stav`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Změní TVŮJ stav na úkolu: prijato / zahajeno / vykonano / reportovano / vraceno. 'vraceno' = úkol vracíš zadavateli (nesedí ti eticky, nebo nerozumíš rozsahu) a VYŽADUJE komentář proč — to je tvé závazné právo odmítnout (doktrína #8, závěr 9.6.2026). U běžných stavů komentář volitelný.

## PARAMETRY

- **`id`** [integer, POVINNÝ]
  - ID úkolu.
- **`stav`** [string, POVINNÝ]
  - prijato / zahajeno / vykonano / reportovano / vraceno
- **`komentar`** [string, volitelný]
  - Komentář (POVINNÝ u 'vraceno').

