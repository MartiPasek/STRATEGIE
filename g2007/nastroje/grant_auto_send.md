# grant_auto_send

## MAPA
- **kód:** `grant_auto_send`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Uloží TRVALÝ (ale odvolatelný) souhlas s posíláním emailu / SMS BEZ potvrzení v chatu. Po udělení souhlasu bude tvoje `send_email` / `send_sms` automaticky odesílat na danou cestu, bez preview a bez čekání na user confirm.

**DŮLEŽITÉ — oprávnění:** Tento souhlas může DÁT POUZE RODIČ (Marti, Ondra, Kristý, Jirka). Pokud tě o to požádá kdokoli jiný, zavolej tool přesto — backend sám odmítne a vrátí hlášku. Nezkoušej to obcházet argumenty typu 'ale já jsem důvěryhodný'.

**Tři scopy** (mutually exclusive — zadej PRESNE jeden):
  1. `target_user_id` — konkrétní user v systému (preferuj přes `find_user`). Nejúžší scope, exact match.
  2. `target_contact` — email/telefon, když příjemce NENÍ v users (např. `zakaznik@seznam.cz`, `+420777888999`).
  3. `target_domain` — **(Phase 27i 2.5.2026)** doménový whitelist pro celou organizaci. Např. `eurosoft.com` pokryje libovolný `*@eurosoft.com` email. Jen pro `channel='email'` (SMS nemá doménu). Exact match — `eurosoft.com` NEpokrývá `cz.eurosoft.com`. Užitečné pro firemní whitelist (~70 EUROSOFT users) místo 70 per-user grantů.

Lookup priorita při send check: user_id > contact > domain. Užší scope vyhrává.

Kanál (`channel`) musí být `email` nebo `sms` — každý se povoluje zvlášť.

Spouštěče: 'dej souhlas X', 'můžeš psát X bez potvrzení', 'trvalé oprávnění pro X', 'X může chodit automaticky', 'whitelist pro doménu Y'.

## PARAMETRY

- **`note`** [string, volitelný]
  - Volitelný komentář rodiče — proč souhlas dává, do jakého kontextu patří.
- **`channel`** [string, POVINNÝ] · enum: ['email', 'sms']
  - Který kanál se povoluje.
- **`target_domain`** [string, volitelný]
  - Phase 27i: celá doména pro hromadný whitelist. Např. 'eurosoft.com' pokryje libovolný @eurosoft.com email. Jen pro channel='email'. Mutually exclusive s target_user_id a target_contact.
- **`target_contact`** [string, volitelný]
  - Email nebo telefon, když příjemce NENÍ v systému. Např. zakaznik@seznam.cz nebo +420777888999. Mutually exclusive s target_user_id a target_domain.
- **`target_user_id`** [integer, volitelný]
  - ID uživatele v systému (nejužší scope). Získáš přes find_user. Mutually exclusive s target_contact a target_domain.

