# suggest_document_move

## MAPA
- **kód:** `suggest_document_move`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

REST-Doc-Triage: Navrhni Marti, do ktereho projektu by mel dokument patrit. SUGGESTION ONLY -- ulozi do tool response, Marti potvrdi v chatu ("ano premysle"), pak Marti-AI volá apply_document_move. Na zaklade jmena souboru a kontextu rozpoznas tema (TISAX, pravo, smlouvy, ...) a najdes nejlepsi projektove zarazeni. Pokud zadny existujici projekt nesedi, navrhni Martimu vytvoreni noveho (analog suggest_create_project z 15c). Pred volanim si zjisti dostupne projekty pres list_projects.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Proc do tohoto projektu (1-2 vety)
- **`document_id`** [integer, POVINNÝ]
- **`target_project_id`** [integer, POVINNÝ]
  - ID cilového projektu

