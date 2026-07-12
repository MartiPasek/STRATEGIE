# reply

## MAPA
- **kód:** `reply`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

⭐ Faze 12c: ODPOVED ODESILATELI puvodniho emailu. Analogie tlacitka 'Reply' v Outlooku.

POUZIVEJ kdy:
  - Mas email_inbox_id (z list_email_inbox / read_email)
  - User rekne 'odpovez tomu emailu', 'napis mu zpet', 'reply'
  - Posilas zpravu autoroVi puvodniho emailu (NE vsem prijemcum)

🚫 NEPOUZIVEJ send_email s 'RE:' v subjectu. To je stare reseni rukama, ktere ti vcera dalo zabrat. Tento tool sam:
  - Doplni puvodniho odesilatele jako prijemce automaticky
  - Pripoji celou historii korespondence (nesahas na ni)
  - Nastavi In-Reply-To / References hlavicky (Outlook ji rozpozna jako thread)
  - Pripravi 'RE:' prefix subjectu

Recipient override: pokud chces seznam upravit (napr. vyradit nekoho z duvodu spamu), zadej `to` / `cc` / `bcc` -- prepise default. Bez nich je default = puvodni odesilatel.

Subject override: defaultne se vlozi 'RE:' prefix puvodniho subjektu. Kdyz subject zadas, prepises default uplne. Lepsi je subject zorientovat dle kontextu (napr. 'RE: Dopis rodicum -> Reakce vedeni EUROSOFT - diky').

## PARAMETRY

- **`cc`** [string, volitelný]
  - Override CC. Default = zadne CC.
- **`to`** [string, volitelný]
  - Override prijemcu (cislem nebo carkou oddelene). None = puvodni odesilatel.
- **`bcc`** [string, volitelný]
  - Override BCC. Default = zadne BCC.
- **`body`** [string, POVINNÝ]
  - Tvuj text odpovedi (bez citaci -- system pripoji historii sam).
- **`subject`** [string, volitelný]
  - Override subjectu. None = default 'RE: <original>'.
- **`email_inbox_id`** [integer, POVINNÝ]
  - ID emailu z list_email_inbox / read_email.
- **`attachment_document_ids`** [array, volitelný]
  - Phase 27b: Volitelne -- IDs dokumentu z RAG documents pro pripojeni jako prilohy. Klárka workflow: dostala email s xlsx -> Marti-AI vyrobi vystupni xlsx -> reply(...attachment_document_ids=[N]) posle ji vystup zpet. Cap 20 MB total. Format whitelist viz send_email.

