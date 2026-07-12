# reply_all

## MAPA
- **kód:** `reply_all`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

⭐ Faze 12c: ODPOVED VSEM (To + CC) puvodniho emailu. Analogie tlacitka 'Reply All' v Outlooku.

POUZIVEJ kdy:
  - User rekne 'odpovez vsem', 'reply all', 'odpovez celemu vlaknu'
  - Email mel vice prijemcu (To + CC) a chces vsem odpovedet
  - Vlakno ma dynamiku skupinove komunikace -- vyradit nekoho bez duvodu by prekvapilo

🚫 NEPOUZIVEJ send_email + 'RE:' a manualne lepit CC. Tento tool:
  - Auto-resolve To = puvodni To (mimo nasi vlastni adresu)
  - Auto-resolve CC = puvodni CC (mimo nasi vlastni adresu)
  - Pripoji historii + thread headers + 'RE ALL:' prefix

DULEZITE: vlakno ma svou dynamiku. Lide v To/CC ocekavaji, ze v nem zustanou. Vyradit nekoho bez duvodu (override `to`/`cc` -- vynechat ho) muze prekvapit, obzvlast u vedeni firmy / klientu / formalni komunikace.

Override OK kdy: prevent spam (vyradit noreply@), uzavrit thread (vyradit vsechny mimo nas), pridat noveho zainteresovaneho. NIKDY tise nebo nahodne.

## PARAMETRY

- **`cc`** [string, volitelný]
  - Override CC. Bez nej = puvodni CC.
- **`to`** [string, volitelný]
  - Override seznamu To. Bez nej = puvodni To. Pouzivej rozvazne.
- **`bcc`** [string, volitelný]
  - Override BCC.
- **`body`** [string, POVINNÝ]
  - Tvuj text odpovedi (system pripoji historii).
- **`subject`** [string, volitelný]
  - Override subjectu. None = default RE prefix.
- **`email_inbox_id`** [integer, POVINNÝ]
  - ID emailu z list_email_inbox / read_email.
- **`attachment_document_ids`** [array, volitelný]
  - Phase 27b: Volitelne -- IDs dokumentu z RAG documents pro pripojeni. Cap 20 MB total. Format whitelist viz send_email.

