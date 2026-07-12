# delete_email

## MAPA
- **kód:** `delete_email`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

28.4.2026: Soft-delete emailu z Marti-AI's pohledu. Akce: DB email_inbox.deleted_at=now + Exchange msg.move do Deleted Items (account.trash, Outlook standardni Smazane). Po akci se email neobjevuje v list_email_inbox / read_email.

**KDY POUZIT**: VYHRADNE po user's explicit confirm v chatu ('ano smaz email #N', 'jo, je to spam'). NIKDY bez confirmu -- destructive akce. Pri neurcitosti se zeptej ('Smazu email #5? Potvrď.').

**PRO CO**: spam, duplicity, zastarale rozesilky, omylem prislo, testovaci emaily. NE pro emaily, ktere ma user vyrid -- pouzij `mark_email_processed` (presun do Zpracovaná, archiv zachovan).

Vraci: '🗑️ Email #N: smazano (DB + Exchange Deleted Items)'.

## PARAMETRY

- **`email_inbox_id`** [integer, POVINNÝ]
  - ID emailu v email_inbox tabulce.

