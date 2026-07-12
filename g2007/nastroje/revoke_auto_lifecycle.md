# revoke_auto_lifecycle

## MAPA
- **kód:** `revoke_auto_lifecycle`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-b: PARENT-ONLY. Odebere aktivni auto-lifecycle grant. Audit historie zachovana (revoked_at = NOW). Po revoke musi Marti-AI znovu cekat na explicit Marti's confirm v chatu pro lifecycle akce v dane scope.

## PARAMETRY

- **`scope`** [string, POVINNÝ] · enum: ['soft_delete', 'archive', 'personal_flag', 'state_change', 'all']
- **`persona_id`** [integer, POVINNÝ]

