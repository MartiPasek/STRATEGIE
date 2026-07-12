# mark_sms_processed

## MAPA
- **kód:** `mark_sms_processed`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Oznaci prichozi SMS jako VYRIZENOU (processed_at = now). SMS zustane v sms_inbox tabulce, ale uz se nepocita do 'novych' (get_daily_overview, list_sms_inbox).

Pouzij kdyz user rekne:
  - 'tahle SMS je vyrizena' / 'tu SMS oznac jako vyrizenou'
  - po REPLY pres send_sms -- pokud Marti-AI odpovedela na incoming
  - 'preskoc tu, neresim'
  - 'tady neni co odpovidat, oznac jako hotove'

ROZDIL od dismiss_item(sms, soft/hard): dismiss_item snizi priority (SMS bude v dalsim overview niz, ale STALE pocitana jako 'k vyrizeni'). mark_sms_processed JI UPLNE VYRADI z 'novych' -- jako kdyby user kliknul 'oznacit jako precteny+vyrizeny' v UI.

Idempotentni: pokud uz je processed, nedela nic (success no-op).

## PARAMETRY

- **`sms_inbox_id`** [integer, POVINNÝ]
  - ID prichozi SMS z list_sms_inbox.

