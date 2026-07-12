# approve_deployment

## MAPA
- **kód:** `approve_deployment`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 42 (19.5.2026): Marti nebo Kristy v chatu schvali pending deployment proposal -> backend volá git pull origin main + touch marker file -> NSSM watchdog STRATEGIE-RESTART-WATCHER detekuje marker a restartne STRATEGIE-API.

Pouze is_marti_parent=True (Marti id=1, Marti-AI id=2, Kristy id=11, Ondra, Jirka) mohou approve.

Po approve proposal status='deployed', deploy_completed_at = NOW(). Restart probehne asynchronně (par sekund), STRATEGIE-API bude kratce nedostupna -- typicky 5-15s graceful restart.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Optional krátké zdůvodnění souhlasu.
- **`proposal_id`** [integer, POVINNÝ]
  - ID proposal z deployment_proposals.

