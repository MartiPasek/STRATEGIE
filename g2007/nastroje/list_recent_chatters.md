# list_recent_chatters

## MAPA
- **kód:** `list_recent_chatters`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí seznam uživatelů, kteří s tebou nedávno mluvili (napsali ti zprávu). Každý user s počtem zpráv a časem posledního dotyku. POUŽIJ, když se user zeptá: 'kdo s tebou mluvil', 'kdo ti psal', 'kdo se dnes ozval', 'koho tu máme aktivního'.

Není to totéž jako `list_conversations` — ta vrací seznam konverzací (titulků). Tento tool vrací **lidi** agregovaně.

## PARAMETRY

- **`hours`** [integer, volitelný] · default: `24`
  - Kolik hodin zpět hledat (default 24 = posledních 24 h).

