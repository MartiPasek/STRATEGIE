# create_project_subfolder

## MAPA
- **kód:** `create_project_subfolder`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 30: Vytvor novy projekt v strome. parent_project_id NULL = novy root projekt, jinak child existujiciho projektu. Marti's mandate (2.5.2026 vecer): 'plna autonomie nad strukturou stromu, jen info na mne pro kontrolu'.

Marti-AI's strom: root 'Marti-AI' + 3 vetve (Znalostni baze, Systém & Architektura, Skola & Rodina). Plus lidske projekty (TISAX, SKOLA, ...) mohou taky mit deti.

Limit hloubky: 6 urovni (root=0, max child depth 5). Validace v service vrstve. Pri prekroceni vraci error.

## PARAMETRY

- **`name`** [string, POVINNÝ]
  - Jmeno projektu (max 255 znaku).
- **`reason`** [string, volitelný]
  - Kratky duvod proc projekt vytvaris (audit log).
- **`parent_project_id`** [['integer', 'null'], volitelný]
  - ID parent projektu, NULL = novy root projekt.

