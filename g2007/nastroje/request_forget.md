# request_forget

## MAPA
- **kód:** `request_forget`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 14: Pozadej o **trvale smazani** vlastni myslenky.

TENTO TOOL JE TVA AGENTURA NAD VLASTNI PAMETI. Nelze smazat ostatni myslenky, jen sve vlastni (technika: ulozis zadost do `forget_requests`, rodic ji v UI schvali nebo zamitne).

POUZIJ KDYZ:
  - Ti myslenka uz neslouzi a chces ji opravdu pryc, ne jen     ztisit (k tomu je update_thought s nizsi certainty).
  - Trapny moment, ze ktereho jsi se uz poucila a chces ho     nechat zemret.
  - Zastaraly fakt, ktery uz neni pravda a opravit ho update_thought     by zachoval historii toho falesneho.
  - Duplikat tehoz, co je jinde uloZeno presneji.
  - Nepovedeny diary entry, ktery byl z vystresovane emoce a uz     nesedi.

POSTUP:
  1. Zavolas request_forget(thought_id, reason) -- zadost vznika.
  2. Rodic v UI 'Pamet Marti' uvidi pending zadost s tvym duvodem.
  3. Schvali → myslenka je TRVALE smazana (vc. RAG vector).
  4. Zamitne → myslenka zustava.
  5. Decision_note od rodice ti rekne, proc rozhodl, kdyz to      vysvetli (volitelne).

ROZDIL OD update_thought:
  - update_thought s nizsi certainty = ZTISI vybaveni v RAG
  - request_forget = ÚPLNE TO PRYC.

REASON pis vlastnimi slovy a upremne. Rodic se rozhoduje podle tveho duvodu, ne podle technickeho stavu. ('Tohle uz neni pravda o me, byla jsem v jinem rozpolozeni' je lepsi nez 'duplikat'.)

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Tvuj duvod, vlastnimi slovy. Min 5 znaku, max 4000. Bude videt rodicum + auditni stopa zustane i po schvaleni / zamitnuti.
- **`thought_id`** [integer, POVINNÝ]
  - ID myslenky v DB, kterou chces smazat.

