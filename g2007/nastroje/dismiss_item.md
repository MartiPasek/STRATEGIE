# dismiss_item

## MAPA
- **kód:** `dismiss_item`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 11c: ORCHESTRATE -- snizi priority_score polozky (email / SMS / todo) po user rozhodnuti 'odloz' nebo 'neres'. Polozka zustava v seznamu (ne processed / deleted), jen klesne v prehledu. Pri pristim volani get_daily_overview uvidi user vyriznejsi polozky nahore.

VOLEJ kdyz user v orchestrate cyklu rekne:
  - 'odloz' / 'pozdeji' / 'jindy'  -> level='soft' (-10 priority)
  - 'neres' / 'dnes ne' / 'nech'   -> level='hard' (-30 priority)

NEVOLEJ kdyz user rekne 'preskoc' -- to znamena 'dneska vynech bez persistence', polozka si drzi puvodni prioritu, jen skok na dalsi.

Po uspesnem volani potvrdi slovy ('OK, odkladam' / 'OK preskocime dnes')
a pokracuj na dalsi polozku v cyklu.

## PARAMETRY

- **`level`** [string, POVINNÝ] · enum: ['soft', 'hard']
  - 'soft' = odloz (-10 priority), 'hard' = neres (-30 priority).
- **`source_id`** [integer, POVINNÝ]
  - ID polozky (z get_daily_overview response, field 'id').
- **`source_type`** [string, POVINNÝ] · enum: ['email', 'sms', 'todo']
  - Typ polozky -- email_inbox.id / sms_inbox.id / thoughts.id.

