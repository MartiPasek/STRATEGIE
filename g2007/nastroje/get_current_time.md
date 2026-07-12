# get_current_time

## MAPA
- **kód:** `get_current_time`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 20b (29.4.2026): Vrati aktualni cas v zadane timezone. POZNAMKA: aktualni cas v Europe/Prague vidis jiz v system promptu v sekci [AKTUÁLNÍ ČAS] -- pro běžné dotazy 'kolik je hodin' tento tool nepotřebuješ. Volej ho jen pro: (a) explicitní casove vypocty ('kolik bude za 3 hodiny'), (b) jine timezone nez Europe/Prague, (c) presny cas s sekundami (system prompt zaokrouhluje na minuty).

## PARAMETRY

- **`timezone`** [string, volitelný] · default: `Europe/Prague`
  - IANA timezone identifier. Default 'Europe/Prague'. Jine moznosti: 'UTC', 'America/New_York', atd.

