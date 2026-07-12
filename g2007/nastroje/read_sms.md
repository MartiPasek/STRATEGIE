# read_sms

## MAPA
- **kód:** `read_sms`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Otevre a precte CELY text prichozi SMS. Pouzij kdyz user chce slyset obsah konkretni SMS po list_sms_inbox -- 'precti mi tu prvni', 'co tam pise', 'otevri tu od Kristy'. list_sms_inbox vraci jen preview (100 znaku); pro plny text musis volat tento tool.

Side-effect: pokud SMS jeste nebyla precteno (read_at IS NULL), tool ji oznaci jako precteno (mark_read).

ID JE DB ID, NE POZICE V LISTU. Kdyz list_sms_inbox vypise '1. SMS' s id=12, volej read_sms(sms_inbox_id=12), NE read_sms(sms_inbox_id=1).

## PARAMETRY

- **`sms_inbox_id`** [integer, POVINNÝ]
  - ID prichozi SMS z list_sms_inbox.

