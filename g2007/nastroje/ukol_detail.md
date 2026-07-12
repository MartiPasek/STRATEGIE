# ukol_detail

## MAPA
- **kód:** `ukol_detail`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Načte detail úkolu + celé sdílené vlákno (chat) podle ID. Použij, když chceš přečíst zadání úkolu a co se v něm dosud psalo, než začneš pracovat nebo odpovíš.

## PARAMETRY

- **`id`** [integer, POVINNÝ]
  - ID úkolu (z moje_ukoly).

