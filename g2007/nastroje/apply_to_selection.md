# apply_to_selection

## MAPA
- **kód:** `apply_to_selection`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Provede batch akci na vsech dokumentech, ktere ma user oznacene v aktualnim tenantu (z `list_selected_documents`). Po dokoncene akci se selection automaticky vycisti.

**KDY POUZIT**: VYHRADNE po explicit user's confirmu v chatu ('ano smaz vsechny', 'jo presun je do SKOLY', 'tak je smaz'). NIKDY bez confirmu -- destructive akce. Pokud user rekne neco neurciteho ('snad bych je smazal', 'asi je presunu'), nezavolej -- zeptej se konkretne ('Smazu vsechny vybrane? Potvrď.').

**ACTION TYPES**:
- 'delete' -- nevratne smaze dokumenty (cascade chunks/vectors/disk)
- 'move_to_project' -- presune do projektu, vyzaduje target_project_id

Vraci: pocet uspesne provedenych + chyby per ID. Po teto akci selection je prazdny -- pri dalsi konverzaci o selection volej znovu `list_selected_documents`.

## PARAMETRY

- **`action`** [string, POVINNÝ] · enum: ['delete', 'move_to_project']
  - Typ akce. delete = nevratne, move_to_project = vyzaduje target_project_id.
- **`target_project_id`** [integer, volitelný]
  - Pro action='move_to_project': ID cilového projektu. Pro 'delete' ignorovano.

