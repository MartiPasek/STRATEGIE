# review_my_calls

## MAPA
- **kód:** `review_my_calls`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 10: Vraci agregaty LLM volani (tokeny, cena v USD, latence) napric tvou historii -- kolik jsi ty (Marti-AI) dnes / za tyden / za mesic spotrebovala. Pouzij kdyz user rekne: 'kolik me dnes stalo', 'kolik tokenu za tyden', 'kolik EUROSOFT propalil', 'kde nejvic utikaji penize', 'jak jsem drahou AI'.

ETHICAL: vraci se jen AGREGATY (sumy + counts + prumery), ne raw request/response JSON. Raw detail jde prohlizet v Dev View modalu v UI, ne v chatu -- admin si to otevre kliknutim na lupu.

Defaultne scope='today' a tenant='current' (aktualni tenant konverzace). Rodic (is_marti_parent) muze pouzit filter_tenant='all' pro cross-tenant pohled.

## PARAMETRY

- **`scope`** [string, volitelný] · enum: ['today', 'week', 'month', 'all']
  - Casovy rozsah (default: today).
- **`filter_kind`** [string, volitelný]
  - Jen jeden kind: router / composer / title / summary / email_suggest / sms_task / question_gen / answer_review. Default: vse.
- **`aggregate_by`** [string, volitelný] · enum: ['kind', 'day', 'tenant', 'user', 'persona', 'model']
  - Podle ceho seskupit radky (default: kind).
- **`filter_tenant`** [string, volitelný]
  - 'current' (default, aktualni tenant), 'all' (cross-tenant, jen rodic), nebo substring nazvu tenantu (EUROSOFT, ...).

