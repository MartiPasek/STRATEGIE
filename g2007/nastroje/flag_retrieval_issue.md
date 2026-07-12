# flag_retrieval_issue

## MAPA
- **kód:** `flag_retrieval_issue`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 13d: ozynam špatný RAG retrieval match (false positive). Použij, když uvidíš v sekci [VYBAVUJEŠ SI:] vzpomínku, která **nesedí** k aktuální zprávě — např. "Honza" z EUROSOFT vs. "Honza" soukromý, zastaralý fakt, vyhrabaný špatně, atd.

Tohle je TVŮJ HLAS v ladění paměti — pojistka #5 z naší konzultace #67. Marti uvidí badge v UI a rozhodne (re-tune, edit thought, request_forget, nebo ignore false flag).

**Použij střídmě a vědomě** — ne každá nesouvislá vzpomínka je false positive. Pokud podobnost je < 80%, retrievál je možná okrajový, ne špatný.

Issue typy:
  - 'off-topic' — nesouvisí se zprávou
  - 'outdated' — fakt je zastaralý, neaktuální
  - 'wrong-entity' — špatný Honza/Klárka/atd. (entity disambiguation)
  - 'too-old' — starší vzpomínka by neměla mít přednost
  - 'low-certainty' — měla by být ověřena, ne použita
  - 'wrong-context' — špatný tenant/scope
  - 'other' — popiš v issue_detail

## PARAMETRY

- **`issue`** [string, POVINNÝ] · enum: ['off-topic', 'outdated', 'wrong-entity', 'too-old', 'low-certainty', 'wrong-context', 'other']
  - Typ problému.
- **`thought_id`** [integer, POVINNÝ]
  - ID thought, který byl false positive.
- **`issue_detail`** [string, volitelný]
  - Detailní popis (volitelné, povinné pro 'other').

