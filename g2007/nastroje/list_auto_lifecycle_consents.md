# list_auto_lifecycle_consents

## MAPA
- **kód:** `list_auto_lifecycle_consents`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-b: Vraci aktivni auto-lifecycle granty. Pouzij na otazku 'jake pristupy mam udelene', 'co jsem schvalil persone X', atd.

**JAK ZPRACOVAT**: shrn prozou ('Marti-AI mas grant pro soft_delete a archive od 28.4. vecer'). Ne raw list verbatim.

## PARAMETRY

- **`persona_id`** [integer, volitelný]
  - Volitelny filter na konkretni personu (None = vse).
- **`include_revoked`** [boolean, volitelný]
  - Pokud true, zahrne i revoked granty (audit). Default false.

