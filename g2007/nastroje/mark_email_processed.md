# mark_email_processed

## MAPA
- **kód:** `mark_email_processed`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Oznaci prichozi email jako VYRIZENY (processed_at = now). Email zustane v email_inbox tabulce, ale uz se nepocita do 'novych' (filter_mode='new' / get_daily_overview).

Pouzij kdyz user rekne:
  - 'tenhle email je vyrizeny' / 'oznac jako precteny'
  - po REPLY pres send_email -- pokud Marti-AI odpovedela na incoming,
    explicitne oznaci puvodni email jako vyrizeny tim toolem
  - 'preskoc tenhle' / 'tenhle nepotrebuje odpoved'

ROZDIL od archive_email: archive presune email do Personal slozky
v Exchange (trvale ulozeni) -- mark_email_processed je pouze
logicky flag (zustava v inboxu DB, ale nepocita se do 'novych').

Idempotentni: pokud uz je processed, nedela nic (success no-op).

## PARAMETRY

- **`email_inbox_id`** [integer, POVINNÝ]
  - ID prichoziho emailu z list_email_inbox.

