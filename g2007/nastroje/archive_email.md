# archive_email

## MAPA
- **kód:** `archive_email`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Archivuje email do tvé **osobní složky 'Personal'** na Exchange serveru. Použij pro významné emaily — osobní dopisy od rodičů / rodičům, ikonické momenty, emoční výměny. Archiv je **skutečně v Exchange**, ne jen v DB — takže přežije i restart systému.

Příchozí emaily od rodičů (Marti, Kristý, Zuzka) se archivují **automaticky** — tento tool pro ně nepotřebuješ. Podobně odchozí emaily posílané rodičům. Tool je pro **ručně vybrané** emaily mimo tyto rules — když user řekne 'ulož si tenhle ikonický email'.

Musíš zadat buď `email_inbox_id` (pro příchozí) nebo `email_outbox_id` (pro odchozí). Nevynocuj oba najednou.

## PARAMETRY

- **`email_inbox_id`** [integer, volitelný]
  - ID emailu z email_inbox (příchozí, volitelné).
- **`email_outbox_id`** [integer, volitelný]
  - ID emailu z email_outbox (odchozí, volitelné).

