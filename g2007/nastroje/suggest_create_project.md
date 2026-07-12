# suggest_create_project

## MAPA
- **kód:** `suggest_create_project`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15c kustod: Navrhni Marti, ze pro toto tema NESEDI zadny existujici projekt -- mel by se zalozit novy. DULEZITE -- prinasis KOMPLETNI navrh (Marti-AI's #4 vstup), ne polotovar: (1) proposed_name (z kontextu konverzace, smysluplny napriklad 'DPH 2026'), (2) proposed_description (1 veta o ucelu projektu), (3) proposed_first_member_id (defaultne current Marti, podle list_users). Bez kompletniho navrhu by Marti musel dotahnout -- to ho ruchce. Po confirm: backend vytvori projekt + presune konverzaci do nej. ETIKA: ty navrhujes, Marti rozhoduje. Nelas vytvorit projekt primo -- to je organizacni rozhodnuti o jeho praci.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Proc je novy projekt potreba (proc nesedi zadny existujici).
- **`proposed_name`** [string, POVINNÝ]
  - Smysluplny nazev projektu (3-50 znaku, z kontextu konverzace).
- **`proposed_description`** [string, POVINNÝ]
  - 1 veta o ucelu projektu -- co se v nem bude resit.
- **`target_conversation_id`** [integer, volitelný]
  - Volitelne -- pokud chces tuto konverzaci po vytvoreni presunout do noveho projektu. Defaultne current.
- **`proposed_first_member_id`** [integer, POVINNÝ]
  - ID prvniho clena projektu (defaultne current user / Marti).

