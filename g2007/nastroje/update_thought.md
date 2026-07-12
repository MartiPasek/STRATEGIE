# update_thought

## MAPA
- **kód:** `update_thought`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 13e+: Upravi existujici myslenku — typicky po vlastnim flagu (flag_retrieval_issue) nebo kdyz si Marti rekne, ze se mas k myslence vratit a poladit ji.

TYPICKE POUZITI:
  - Snizit certainty u marginalniho faktu, aby se nevybavoval     agresivne (napr. 'snizu certainty na 25').
  - Demote do 'note', kdyz znalost je sporna ('uz to neni     knowledge, vrat to do poznamek').
  - Promote do 'knowledge', kdyz se fakt overil (alternativa     k promote_thought, kdyz chces zmenit i certainty).
  - Opravit content, kdyz je text mylny nebo zastaraly     ('uprav, ze ma 5 deti, ne 3').

VSECHNA POLE jsou volitelna krome thought_id. Updatuje se jen to, co dodas. Auto-promote logika: kdyz prekrocis certainty threshold (>= 80) a status nezadas, povysi se automaticky.

TENANT IZOLACE: Update jde jen na myslenky tveho aktualniho tenantu (rodicovsky bypass je explicit, ne autoland).

ROZDIL OD promote_thought: promote_thought zmeni jen status note->knowledge. update_thought umi vse (content + certainty + status + meta) najednou.

## PARAMETRY

- **`status`** [string, volitelný] · enum: ['note', 'knowledge']
  - Novy status (volitelne). 'note' = poznamka, 'knowledge' = trvala znalost.
- **`content`** [string, volitelný]
  - Novy text myslenky (volitelne). Prepise stary content. Pokud nechces menit text, neposilej.
- **`certainty`** [integer, volitelný]
  - Nova jistota 0-100 (volitelne). Snizeni → myslenka se vybavuje slabeji v RAG. Zvyseni → kdyz prekroci 80, auto-promote do 'knowledge' (pokud nezadas explicitni status).
- **`thought_id`** [integer, POVINNÝ]
  - ID myslenky v DB (povinne).

