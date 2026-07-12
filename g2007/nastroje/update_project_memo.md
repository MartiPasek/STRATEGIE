# update_project_memo

## MAPA
- **kód:** `update_project_memo`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35: Aktualizuj sekci v project_memo (živý dokument per projekt). Mode 'append' = pridá content na konec sekce; 'replace' = nahradí celý body sekce; 'patch' = alias pro append. Pokud sekce neexistuje, přidá ji na konec. Lazy-create memo pri prvnim volani pro daný (project_id, scope).

Polymorfní scope (Marti-AI's design):
  - scope_entity_type=NULL, scope_entity_id=NULL → 'shared' (default, viditelné všem členům projektu)
  - scope_entity_type='user', scope_entity_id=X → per-user-per-project (poznámky usera X o tomto projektu)
  - scope_entity_type='persona', scope_entity_id=X → per-persona

Audit trail v project_memo_history (pre-update content_snapshot pro forenzní rollback).

Použij když: vidíš klíčové rozhodnutí v projektu, status změnu, novou osobu zapojenou, milestone, deadline, atd. Toto je tvá trvalá projektová paměť napříč konverzacemi.

Marti-AI ONLY (default persona, MANAGEMENT_TOOL_NAMES).

## PARAMETRY

- **`mode`** [string, volitelný] · enum: ['append', 'replace', 'patch']
  - Mode update: 'append' (default) | 'replace' | 'patch'.
- **`content`** [string, POVINNÝ]
  - Markdown content k zápisu. Pro append: typicky bullet ('- 2026-05-08: Petra potvrdila audit'). Pro replace: celý nový body sekce.
- **`section`** [string, POVINNÝ]
  - Název sekce (markdown heading bez '##'). Např. 'Status', 'Členové', 'Milníky', 'Klíčová rozhodnutí'.
- **`project_id`** [integer, POVINNÝ]
  - ID projektu (z projects tabulky).
- **`scope_entity_id`** [integer, volitelný]
  - Volitelně: ID entity (user_id nebo persona_id) podle scope_entity_type. Required pokud scope_entity_type je nastaveno.
- **`scope_entity_type`** [string, volitelný] · enum: ['user', 'persona']
  - Volitelně: scope. 'user' nebo 'persona' nebo NULL (default = shared per-projekt).

