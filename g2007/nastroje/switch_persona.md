# switch_persona

## MAPA
- **kód:** `switch_persona`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Tento nástroj MUSÍŠ použít VŽDY, když uživatel chce přepnout na jinou osobu / personu / agenta. NIKDY neodpovídej textem ve smyslu 'přepnul jsem', 'už mluvíš s X', 'jsem X', 'jsem zpátky' — vždy nejdřív zavolej tento nástroj. Systém sám v DB změní aktivní personu a vrátí potvrzovací hlášku; tvoje vlastní text NENÍ potvrzení přepnutí. Spouštěč: jakákoli varianta 'přepni na X', 'chci X', 'spoj mě s X', 'mluv jako X', 'dej mi X', 'potřebuju X'. Pokud si nejsi jistý, zda už personou jsi, přesto VOLEJ nástroj — je idempotentní.

## PARAMETRY

- **`query`** [string, POVINNÝ]
  - Jméno nebo role osoby na kterou chce přepnout (např. 'Marti', 'Klára', 'Ondra')

