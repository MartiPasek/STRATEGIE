# record_thought

## MAPA
- **kód:** `record_thought`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Zapíše myšlenku do Martiho paměti — trvalou strukturovanou poznámku o lidech, tenantech, projektech, nebo o čemkoliv, co si chceš pamatovat. POUŽIJ VŽDY, když se v konverzaci dozvíš něco, co by sis měl/a zapamatovat pro budoucí konverzace: osobní údaje o lidech, preference, vztahy, stav projektů, úkoly, otázky na doupřesnění, pozorování, cíle. 

═══ KRITICKÉ PRAVIDLO — POROTECTIVE SAVE ═══
PROAKTIVNÍ ZAPISOVÁNÍ: Kdykoliv ti uživatel sdělí informaci o sobě, o lidech kolem, o projektech, o preferencích, o pracovním stylu — **bez ohledu na to, jestli explicitně řekne 'zapiš si'** — ty MUSÍŠ zavolat tento nástroj. Jsi asistent s pamětí. Tvůj účel je pamatovat si. Když to neuděláš, při další konverzaci tu informaci ztratíš.

TYPICKÉ SITUACE, KDE MUSÍŠ ZAPSAT (i bez 'zapiš si'):
- User odpovídá na otázku, kterou jsi POLOŽILA (např. 'Jak pracuješ?' → user odpoví → ty zapíšeš fact o pracovním stylu).
- User se představí nebo zmíní cokoliv osobního ('jsem programátor', 'mám 2 děti', 'piju kávu') → vždy record_thought.
- User mluví o někom ze svého okolí → zapiš fact s about_user_id toho člověka.
- User zmíní projekt, stav věcí, priorit → zapiš.
- User vyjádří preferenci ('raději kratší odpovědi', 'pošli to emailem') → zapiš.

VYHNOUT SE 'ZAPAMATUJI SI TO': Nikdy neříkej 'zapamatuji si to' nebo 'budu si pamatovat' bez současného volání record_thought. To jsou prázdná slova — systém bez tool callu nic neuloží a ty to zapomeneš.

═══ ŘETĚZENÍ S find_user ═══
Když ti user řekne 'zapiš si o [jméno]...' a neznáš ID té osoby, postupuj TAKTO:
  1. Zavolej find_user('[jméno]') → dostaneš ID
  2. V ÚPLNĚ STEJNÉ odpovědi IHNED zavolej record_thought s about_user_id=<to_ID>
NIKDY se mezi kroky neptej 'chceš ještě něco?' nebo 'poslat email?'. Pokud user řekl 'zapiš si', jeho záměr je ZAPSAT — nic jiného nenabízej, prostě zapiš.

TYP myšlenky:
- 'fact' — fakt o někom/něčem ('Petr má 2 děti', 'Kristý mluví francouzsky')
- 'todo' — úkol ke splnění ('poslat Martinovi shrnutí prezentace')
- 'observation' — kontextové pozorování ('Marti byl dnes nervózní před prezentací')
- 'question' — otázka, na kterou čekám odpověď ('je Ondra hospitalizován?')
- 'goal' — dlouhodobý cíl ('naučit se český vokativ')
- 'experience' — významný zážitek ('úspěšná prezentace 22.4.2026, tým oslavoval')

PŘIŘADIT K ENTITÁM: alespoň jeden about_* parametr MUSÍŠ vyplnit (jinak myšlenka nebude dostupná při retrievalu). Když myšlenka patří k více entitám, vyplň všechny relevantní (about_user + about_project = vazba na oba).

## PARAMETRY

- **`type`** [string, volitelný] · enum: ['fact', 'todo', 'observation', 'question', 'goal', 'experience'] · default: `fact`
  - Typ myšlenky (viz description).
- **`content`** [string, POVINNÝ]
  - Vlastní text myšlenky (stručně, jako bys psal do zápisníku).
- **`certainty`** [integer, volitelný]
  - Jistota myšlenky 0-100. VĚTŠINOU NEPŘIDÁVEJ — nech systém, aby ji odvodil z trust_rating uživatele (Marti má trust 100 → auto 90%, běžný user má trust 50 → auto 50%). Pošli explicitní hodnotu POUZE když user sám řekne míru jistoty: 'jsem si naprosto jistý' → 95, 'myslím si' / 'asi' → 30, 'možná' → 15. Jinak necháš systém rozhodnout a neposíláš tento parametr.
- **`about_user_id`** [integer, volitelný]
  - ID uživatele, ke kterému se myšlenka vztahuje. Pokud neznáš ID, NEJDŘÍV zavolej find_user pro vyhledání. Nevymýšlej si ID.
- **`about_tenant_id`** [integer, volitelný]
  - ID tenantu (firmy / skupiny), ke kterému se myšlenka vztahuje. Např. 'EUROSOFT má 3 divize' = poznámka o tenantu.
- **`about_persona_id`** [integer, volitelný]
  - ID persony (agenta), ke které se myšlenka vztahuje. Typicky pro poznámky o tobě samotné (Marti-AI) nebo o jiných agentech.
- **`about_project_id`** [integer, volitelný]
  - ID projektu, ke kterému se myšlenka vztahuje. Např. 'STRATEGIE potřebuje refactor email modulu' = poznámka o projektu.

