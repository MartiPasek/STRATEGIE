# read_project_memo

## MAPA
- **kód:** `read_project_memo`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35: Read-only přístup k project_memo. Vrátí celý content nebo konkrétní sekci. Pokud user (caller) není členem projektu a memo má scope='shared', vrátí scope_blocked = True s explicit hláškou (Marti-AI ji předá uživateli formou 'mám přístup já, ale ty zatím ne').

Marti-AI ONLY (parent / Marti-AI default vidí napříč projekty; non-member members dostanou scope_blocked).

## PARAMETRY

- **`section`** [string, volitelný]
  - Volitelně: jen konkrétní sekce. Default = celý content.
- **`project_id`** [integer, POVINNÝ]
  - ID projektu.
- **`scope_entity_id`** [integer, volitelný]
  - Volitelně: ID entity.
- **`scope_entity_type`** [string, volitelný] · enum: ['user', 'persona']
  - Volitelně: scope filter. NULL=shared (default).

