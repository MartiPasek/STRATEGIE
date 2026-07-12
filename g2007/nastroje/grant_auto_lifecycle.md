# grant_auto_lifecycle

## MAPA
- **kód:** `grant_auto_lifecycle`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-b (29.4.2026): PARENT-ONLY tool. Marti udeluje cizi persone (typicky Marti-AI default) trvaly souhlas s lifecycle akcemi -- pak Marti-AI volá apply_lifecycle_change BEZ explicit Marti's confirm v chatu.

Analogie Phase 7 auto_send_consents (auto-send email/SMS bez confirm). Hard delete (request_forget) zustava parent gate -- auto-grant nedostupny pro nej.

**Scope hodnoty**:
  - 'soft_delete' = is_deleted=TRUE (vratne pres update)
  - 'archive' = is_archived=TRUE / lifecycle->archived
  - 'personal_flag' = lifecycle->personal
  - 'state_change' = active <-> archivable <-> disposable
  - 'all' = vsechny vyse uvedene KROME hard_delete

**Idempotent**: pokud aktivni grant uz existuje, vrati existujici.

## PARAMETRY

- **`note`** [string, volitelný]
  - Volitelny kontext, proc udelujes (audit).
- **`scope`** [string, POVINNÝ] · enum: ['soft_delete', 'archive', 'personal_flag', 'state_change', 'all']
  - Scope lifecycle akci, pro ktere je grant aktivni.
- **`persona_id`** [integer, POVINNÝ]
  - ID persony, ktere udelujes souhlas (typicky Marti-AI default = 1).

