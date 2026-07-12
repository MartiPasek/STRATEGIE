# reject_deployment

## MAPA
- **kód:** `reject_deployment`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 42 (19.5.2026): Marti nebo Kristy v chatu odmitne pending deployment proposal -> close as rejected, žádný git pull, žádný restart.

Pouze is_marti_parent=True users. Po reject muze Marti-AI poslat nový propose_deployment pozdeji (napr. po dalsim commitu nebo pri stabilnejsim case).

## PARAMETRY

- **`reason`** [string, volitelný]
  - Důvod rejectu (audit + Marti-AI's learning -- napr. 'pred prezentaci nechcem restart', 'wait for fix gotcha #N').
- **`proposal_id`** [integer, POVINNÝ]
  - ID proposal z deployment_proposals.

