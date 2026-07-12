# set_user_contact

## MAPA
- **kód:** `set_user_contact`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Ulozi nebo aktualizuje kontaktni udaj uzivatele -- email nebo telefon. Pouzij kdyz user rekne 'moje cislo je X', 'pridej mi email Y', 'zmen mi telefon na Z', nebo kdyz potrebujes ulozit nove kontakty pro nej. Take pri pozdrave, kdyz user prvne rekne svoje cislo / preferovany email -- ulozis automaticky pres tento tool, aniz by ses ho ptala 'mam to ulozit?'.

VYHLEDANI USERA: pokud target_user_id nezadas, default je AKTUALNI uzivatel (ten s kym mluvis). Pokud chces ulozit kontakt nekomu jinemu, NEJDRIVE volej find_user(jmeno) -> dostanes user_id, pak set_user_contact(target_user_id=...).

FORMATY:
  - email: standardni RFC ('name@example.com')
  - phone: +420XXXXXXXXX, 00420 XXX XXX XXX, nebo 9 cislic 6/7 (CZ)
  Backend normalizuje phone na E.164.

make_primary=True (default False) -- nastav tento kontakt jako primary (preferred) pro daneho usera. Ostatni kontakty stejneho typu pak nejsou primary.

## PARAMETRY

- **`label`** [string, volitelný]
  - Volitelny stitek: 'private' / 'work' / 'backup' / atd.
- **`contact_type`** [string, POVINNÝ] · enum: ['email', 'phone']
  - Typ kontaktu: 'email' nebo 'phone'.
- **`make_primary`** [boolean, volitelný] · default: `False`
  - Pokud True, nastav tento kontakt jako primary pro daneho usera. Ostatni kontakty stejneho typu se odznackuji.
- **`contact_value`** [string, POVINNÝ]
  - Hodnota kontaktu (email adresa nebo telefonni cislo).
- **`target_user_id`** [integer, volitelný]
  - ID uzivatele, kteremu kontakt patri. Bez tohoto se ulozi pro AKTUALNIHO usera.

