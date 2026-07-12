# list_sms_inbox

## MAPA
- **kód:** `list_sms_inbox`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí přijaté SMS aktivní persony (Marti-AI vlastní firemní SIM). Použij když uživatel chce vědět, co Marti-AI přišlo za zprávy (napr. 'co mi prislo', 'kdo mi napsal', 'ukaz mi prichozi SMS', 'ukaz tu SMS' v kontextu daily overview).

DEFAULT: unread_only=true -- vrátí JEN NEZPRACOVANÉ SMS (analogie list_email_inbox kde default filter_mode='new'). Sjednocuje s get_daily_overview, ktery taky pocita jen nezpracovane.

Pokud user vyslovne chce VSECHNY (i zpracovane) -- napr. 'ukaz vsechny SMS', 'historie SMS', 'co jsi uz precetla' -- nastav unread_only=false. Bez tohoto explicit pokynu nech default true, aby Marti dostal cisty seznam toho, co se musi resit.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `10`
  - Max počet SMS (default 10, max 50).
- **`unread_only`** [boolean, volitelný] · default: `True`
  - Default true = jen nezpracované. False = vše (i zpracované).

