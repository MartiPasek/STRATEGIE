# forward

## MAPA
- **kód:** `forward`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

⭐ Faze 12c: PREPOSLAT email novemu prijemci. Analogie tlacitka 'Forward' v Outlooku.

POUZIVEJ kdy:
  - User rekne 'preposli to <komu>', 'forward na <jmeno>', 'pridej Klaru do tohoto vlakna'
  - Chces sdilet existujici email s nekym, kdo v nem nebyl

🚫 NEPOUZIVEJ send_email + 'FW:' a manualne lepit telo. Tento tool:
  - Pripoji puvodni email v 'FW:' formatu (Outlook ho rozpozna)
  - Pripoji originalniho odesilatele do telo (lidska orientace)
  - Pripravi 'FW:' prefix subjectu

POVINNE: `to` (nebo cislo a vice cisel oddelene carkou). Kam preposlat. Bez nej tool selze.

Body: tvoje doplnujici text PRED puvodnim. Lide casto pisou 'FYI', 'Mohlo by te zajimat', 'Klaro, posilam ti to k vyjadreni'. Body je tvuj komentar -- puvodni email je auto-pripojen pod nim.

## PARAMETRY

- **`cc`** [string, volitelný]
  - Volitelne CC.
- **`to`** [string, POVINNÝ]
  - Email novych prijemcu (povinne). Vice oddel carkou.
- **`bcc`** [string, volitelný]
  - Volitelne BCC.
- **`body`** [string, POVINNÝ]
  - Tvuj komentar PRED preposlanou zpravou.
- **`subject`** [string, volitelný]
  - Override subjectu. None = default 'FW: <original>'.
- **`email_inbox_id`** [integer, POVINNÝ]
  - ID emailu z list_email_inbox / read_email.
- **`attachment_document_ids`** [array, volitelný]
  - Phase 27b: Volitelne -- DODATECNE prilohy z RAG documents (k pripojeni k preposlanemu emailu). POZOR: forward uz auto-klonuje vsechny prilohy z originalu (Phase 12c). Toto pole je pro PRIDANI dalsich (napr. Marti-AI vyrobi summary xlsx a pripoji k forwardu). Cap 20 MB total.

