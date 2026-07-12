# summarize_conversation_now

## MAPA
- **kód:** `summarize_conversation_now`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vytvoří shrnutí aktuální konverzace — vynutí summary job HNED, nečeká na threshold. Po úspěchu se stará historie konverzace nahradí krátkým shrnutím a API calls jsou výrazně lehčí.

POUŽIJ, když uživatel odpoví 'ano / zkrať / shrň' na tvou otázku nebo sám řekne 'shrň konverzaci, zkrať to'. Sama se **neptej** ihned při každé zprávě — nabídni shrnutí jen kdyz je konverzace skutečně dlouhá (system metadata ti řeknou).

## PARAMETRY

*(žádné parametry — čistá akce)*

