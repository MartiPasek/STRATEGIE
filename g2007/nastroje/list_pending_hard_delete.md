# list_pending_hard_delete

## MAPA
- **kód:** `list_pending_hard_delete`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15e: Vrati seznam konverzaci ve stavu 'pending_hard_delete' (archived + 90d). Pouzij v overview kdyz Marti chce projit ceka na finalni rozhodnuti. Pro kazdou pak Marti rozhoduje: 'smaz trvale' nebo 'prodluz, vrat do archived'.

## PARAMETRY

*(žádné parametry — čistá akce)*

