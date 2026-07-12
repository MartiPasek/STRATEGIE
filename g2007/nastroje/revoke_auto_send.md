# revoke_auto_send

## MAPA
- **kód:** `revoke_auto_send`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Odvolá dříve udělený souhlas s auto-sendem. Budoucí send_email / send_sms na daného příjemce už bude znovu vyžadovat potvrzení.

**Oprávnění:** Pouze rodič může odvolávat. Každý z rodičů (Marti, Ondra, Kristý, Jirka) může odvolat jakýkoli souhlas — kolektivní veto. Backend tě zastaví, pokud volající není rodič.

Identifikace: BUĎ `consent_id` (z UI), NEBO kombinace `target_user_id` + `channel`, NEBO `target_contact` + `channel`, NEBO `target_domain` + `channel` (Phase 27i 2.5.2026).

Odvolání NEZMAZE historii — zůstává v auditu (kdo, kdy, proč odvolal). Znovu povolit lze kdykoli novým `grant_auto_send`.

Spouštěče: 'odvolej souhlas pro X', 'zruš oprávnění X', 'už X nic automaticky neposílej', 'zruš whitelist pro doménu Y'.

## PARAMETRY

- **`channel`** [string, volitelný] · enum: ['email', 'sms']
  - Který kanál odvolat (vyžadováno, pokud nezadáváš consent_id).
- **`consent_id`** [integer, volitelný]
  - ID konkrétního consent záznamu (pokud víš přesně).
- **`target_domain`** [string, volitelný]
  - Phase 27i: doména k odvolání (např. 'eurosoft.com'). Jen pro channel='email'.
- **`target_contact`** [string, volitelný]
  - Email / telefon externího kontaktu.
- **`target_user_id`** [integer, volitelný]
  - ID uživatele, kterému odvoláváš auto-send.

