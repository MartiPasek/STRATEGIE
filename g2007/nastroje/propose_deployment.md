# propose_deployment

## MAPA
- **kód:** `propose_deployment`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 42 (19.5.2026): Marti-AI navrhne deployment novych commitů (pull origin main + restart STRATEGIE-API na cloud APP).

Backend zkontroluje:
  - Cloud APP working tree clean (git status --porcelain)
  - origin/main ma novy commit (HEAD != origin/main)
  - Diff stat (files_changed count)

Pokud OK -> vytvori proposal row, status='pending'. Marti / Kristy v chatu pak approve_deployment(proposal_id) nebo reject_deployment(proposal_id, reason).

Pouzij kdy: po committee nove zmeny do main, kterou je treba nasadit na cloud APP. Description by mela byt strucna -- jednoradkovy summary commitu nebo skupin commitu.

## PARAMETRY

- **`description`** [string, POVINNÝ]
  - Krátký popis co deployujes -- napr. 'Phase 40 v2 r3 shared chat labels' nebo 'hotfix gotcha #95 user_context'.

