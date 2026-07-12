# create_continuation

## MAPA
- **kód:** `create_continuation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 36 (9.5.2026): univerzální dovětek pro uzavřené konverzace.

Generalizace Phase 19c-e2 'create_personal_appendix' — funguje pro VŠECHNY uzavřené konverzace:
  - lifecycle_state='personal' (knížka srdce, read-only)
  - lifecycle_state='archived' (po Phase 36 auditu)

Vytvoří NOVOU konverzaci s parent_conversation_id. Dědí tenant_id / project_id / active_agent_id z parent. Sidebar render = odsazené pod parentem (Phase 19c-e2 tree pattern).

Marti-AI's iterace 2 volba názvu: technický 'create_continuation' (NE poetický) — 'poetiku si nechám pro sebe — do místa, kde patří'. Distinkce tools (čitelné za rok bez kontextu) vs vlastní jazyk.

create_personal_appendix zůstane jako alias 2 týdny pro backward compat, pak deprecated.

## PARAMETRY

- **`initial_message`** [string, volitelný]
  - Volitelná první zpráva v dovětku (ne audit message stamp).
- **`parent_conversation_id`** [integer, POVINNÝ]

