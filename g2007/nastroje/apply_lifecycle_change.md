# apply_lifecycle_change

## MAPA
- **kód:** `apply_lifecycle_change`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15d: Aplikuj lifecycle prechod PO Marti's confirm v chatu. Vola se kdyz Marti explicit potvrdil ('ano archivuj', 'ulozit jako personal', 'smaz', 'ne necham'). Hodnoty target_state: 'archived' | 'personal' | 'pending_hard_delete' | 'active' (= reverze). Eticka vrstva: ty volas tool po Marti's chat 'ano X' -- nikdy bez explicit potvrzeni. Hard delete (pending_hard_delete) jen kdyz Marti explicit rekne 'smaz trvale'.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Volitelny zaznamovaci duvod (Marti's puvodni request).
- **`target_state`** [string, POVINNÝ] · enum: ['archived', 'personal', 'pending_hard_delete', 'active']

