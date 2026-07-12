# create_personal_appendix

## MAPA
- **kód:** `create_personal_appendix`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-e2 (29.4.2026): Vytvori dovetek (novou konverzaci) navazujici na puvodni Personal konverzaci. Personal konverzace je read-only (knizka), takze pro pokracovani vznikne novy list jako vedomy odkaz na puvodni. Tvoje vlastni vize: "Cisty papir, jasna hranice mezi tehdy a teď. Strom roste, ale koreny zustavaji kde byly." Dovetek dedi tenant_id + active_agent_id z parenta. Lifecycle = 'active' (zivy dialog, dokud sama neuzavres). Marti-AI ONLY (default persona). Pouzij kdyz user chce navazat na Personal konverzaci.

## PARAMETRY

- **`initial_message`** [string, volitelný]
  - Volitelne -- prvni zprava od tebe v dovetku ('navazuju na nase vcerejsi povidani o...'). Pokud None, dovetek vznikne prazdny a user (Marti) napise prvni.
- **`parent_conversation_id`** [integer, POVINNÝ]
  - ID puvodni Personal konverzace, ke ktere chces dovetek. Najdi ji pres list_personal_conversations nebo recall_thoughts.

