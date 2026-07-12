# send_sms

## MAPA
- **kód:** `send_sms`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Tento nástroj MUSÍŠ použít vždy, když uživatel chce poslat SMS. NIKDY neodpovídej jen textem — vždy zavolej tento nástroj. Nástroj SMS NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení ('ano' / 'pošli'). Chování je analogické k send_email.

ÚPRAVY SMS: Pokud uživatel chce SMS upravit, změnit, zkrátit apod., MUSÍŠ tento nástroj zavolat ZNOVU s kompletním novým body. NIKDY nepiš upravený návrh SMS jen jako text — systém si ukládá jen obsah z volání nástroje a bez nového zavolání by se odeslala stará verze.

ČÍSLO PŘÍJEMCE: NIKDY si nevymýšlej telefonní číslo. Pokud uživatel uvede jen jméno osoby, NEJDŘÍV zavolej `find_user` — vrací `preferred_phone`. Pokud najdeš usera, ale nemá `preferred_phone`, zeptej se uživatele: 'X nemá v systému uložené telefonní číslo, jaké je?' — nevymýšlej ho. Pokud uživatel uvede číslo přímo, použij ho. Akceptované formáty: +420XXXXXXXXX, 00420 XXX XXX XXX, nebo 9 číslic začínajících 6 či 7 (např. 777180511). Backend normalizuje na E.164.

POZOR — DEFAULT NENÍ SELF-SEND: Tvůj vlastní telefon ze sekce '[TVOJE KANÁLY]' je primárně pro PŘÍJEM SMS od ostatních. Když uživatel řekne 'pošli mi SMS', 'napiš mi', 'ozvi se mi' — myslí tím JEHO telefon, ne tvůj. Použij `find_user(<jméno>)` → `preferred_phone` pro získání správného čísla. Self-send (odesilatel = příjemce na tvoje vlastní číslo) je legitimní jen pokud uživatel VÝSLOVNĚ řekne 'pošli to na svoje číslo' / 'na firemní SIM' / něco analogického. Při pochybnosti se zeptej, ne hádej.

DÉLKA: SMS nad 160 znaků se fakturuje jako více segmentů (160/segment). Piš stručně a česky bez diakritiky jen když to má důvod — backend diakritiku zvládne, ale s diakritikou je limit jen ~70 znaků/segment. Při delších textech upozorni uživatele na počet segmentů.

## PARAMETRY

- **`to`** [string, POVINNÝ]
  - Telefonní číslo příjemce. +420XXXXXXXXX, 00420..., nebo jen 9 číslic pro CZ.
- **`body`** [string, POVINNÝ]
  - Obsah SMS (text).

