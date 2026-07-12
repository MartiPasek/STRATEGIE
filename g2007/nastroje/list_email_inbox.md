# list_email_inbox

## MAPA
- **kód:** `list_email_inbox`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí přijaté emaily aktivní persony. Default scope: VŠECHNY authorizované schránky (napr. marti-ai@eurosoft.com + sdílená pavel.zeman@eurosoft.com). Použij když uživatel chce vědět, co přišlo za emaily ('co mam v mailu', 'ukaz mi emaily'). filter_mode='new' (default) vrátí jen nezpracované, 'processed' jen zpracované, 'all' obojí. Vrací číslovaný seznam — uživatel pak může odpovědět číslem pro akci.

Phase 29 (4.5.2026): mailbox_id volitelný — pokud chceš jen konkrétní schránku, předej id (z `list_mailboxes`). Pokud None (default), zobrazí emaily ze všech tvých authorized mailboxů.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `10`
  - Max počet emailů (default 10, max 50).
- **`mailbox_id`** [integer, volitelný]
  - Phase 29: volitelně filtrovat na konkrétní mailbox (id z list_mailboxes). None = všechny tvé authorized.
- **`filter_mode`** [string, volitelný] · enum: ['new', 'processed', 'all'] · default: `new`
  - 'new' (nezpracované, default), 'processed', 'all'.

