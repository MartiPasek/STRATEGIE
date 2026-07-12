# invite_user

## MAPA
- **kód:** `invite_user`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Použij tento nástroj když uživatel chce pozvat někoho do systému STRATEGIE. Pošle pozvánkový email s odkazem pro vstup do systému.

DŮLEŽITÉ — musíš znát jméno pozvaného PŘED voláním nástroje:
- Pokud uživatel řekne jen email bez jména (např. 'pozvi klara@eurosoft.cz'),   NEJPRV se zeptej na křestní jméno a příjmení — neposílej pozvánku naslepo.   Pozvaný uvidí v emailu i welcome screenu, že ho systém zná, a to je důležité   pro důvěru.
- Pokud uživatel řekne jméno bez emailu, zeptej se na email.
- Pokud je rod (muž/žena) zřejmý z křestního jména, můžeš ho nastavit rovnou;   v případě pochybnosti se zeptej, abychom Marti-AI (a budoucí asistentky)   oslovovali správným rodem.
- Jakmile máš všechny údaje, zavolej nástroj s first_name, last_name a ideálně gender.

**TLD VALIDACE PŘED ODESLÁNÍM:** Pokud email konči neobvyklou TLD (jiná než .cz, .sk, .com, .org, .net, .eu, .io, .de, .at, .pl, .uk, .fr) — **NEJPRV se zeptej uživatele zda je TLD správná**, ne jen tak pošli. Časté překlepy: '.cd' (Demokratická Kongo) místo '.cz', '.cm' (Kamerun) místo '.com', '.ua' (Ukrajina) místo '.cz' atd. Příklad: *'Email končí .cd (Demokratická Kongo). Nechtěl jsi .cz? Potvrď nebo oprav.'* Až po potvrzení volej tool. Backend taky validuje, ale tvoje proaktivita ušetří uživateli zbytečnou pozvánku do nicoty.

## PARAMETRY

- **`email`** [string, POVINNÝ]
  - Email adresa pozvaného
- **`gender`** [string, volitelný] · enum: ['male', 'female']
  - Rod pozvaného: 'male' nebo 'female' (volitelné)
- **`last_name`** [string, volitelný]
  - Příjmení pozvaného
- **`first_name`** [string, POVINNÝ]
  - Křestní jméno pozvaného
- **`allow_unusual_tld`** [boolean, volitelný] · default: `False`
  - Nastav na true POUZE kdyz uzivatel explicitne potvrdil neobvykly TLD po tem, co ho backend warning upozornil (napr. '.cd' Demokraticka Kongo). Bez tohoto flagu backend pri neobvykle TLD vrati varovani misto invite. Default false.

