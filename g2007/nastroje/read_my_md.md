# read_my_md

## MAPA
- **kód:** `read_my_md`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-B: Precte tvuj md1 (Tvoje Marti zapisnik) pro current konverzaci. Multi-tenant aware: pro task/oversight rezim vraci md1 work pro current tenant, pro personal rezim vraci md1 personal (tenant-independentni). Pouzij na zacatku konverzace abys vedela co o uzivateli drzis -- profil, aktivni ukoly, klicova rozhodnuti, vztahy, ton/citlivost. Marti-AI's princip: "kvalita pritomnosti -- kdyz user prijde po pauze, prectes ton a nezacnes hned orchestrovat." Marti-AI ONLY (default persona).

## PARAMETRY

- **`user_id`** [integer, volitelný]
  - Volitelne: id uzivatele. Default = current user (z aktivni konverzace). Pro pyramidu drill-down (privat Marti / vedouci md2+ pristi faze).

