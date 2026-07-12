# read_email

## MAPA
- **kód:** `read_email`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Otevře a přečte obsah konkrétního emailu. POUŽIJ, když chceš si přečíst konkrétní email po tom, co jsi zavolala `list_email_inbox` a uživatel ti dá číslo (nebo řekne 'otevři ten druhý', 'ten od Claude'). Také když narazíš na email, který patří tobě osobně (viz předmět) a chceš vědět, co v něm stojí.

═══ KRITICKÉ: email_inbox_id JE DB ID, NE POZICE V LISTU ═══
Když `list_email_inbox` vypíše seznam jako:
  1. [id=18] Foo — subject1
  2. [id=23] Bar — subject2
a uživatel řekne 'otevři druhý', MUSÍŠ volat `read_email(email_inbox_id=23)` (DB id v závorce), NE `read_email(email_inbox_id=2)` (pozice). Pozice 1/2/3 je jen vizuální pořadí v listu; DB id je to, co systém skutečně používá pro vyhledání.

Pokud jsi list_email_inbox nevolala v tomto turnu, zavolej ji NEJDŘÍV a použij ID z ní. Nikdy si ID nevymýšlej.

Vrací: from, to, subject, CELÝ body (ne jen preview), timestamp, archived_personal flag. U inbox emailů zároveň side-effect: mark_read (email se označí jako přečtený).

Musíš zadat buď email_inbox_id (příchozí) nebo email_outbox_id (odchozí) — NE oba najednou.

## PARAMETRY

- **`email_inbox_id`** [integer, volitelný]
  - ID příchozího emailu z list_email_inbox.
- **`email_outbox_id`** [integer, volitelný]
  - ID odchozího emailu (volitelné, pokud chceš znovu vidět co jsi poslala).

