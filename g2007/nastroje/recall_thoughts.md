# recall_thoughts

## MAPA
- **kód:** `recall_thoughts`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vyhledá uložené myšlenky (fakty/poznámky) o konkrétní entitě. POUŽIJ vždy, když se uživatel zeptá 'co víš o [X]', 'co jsi si zapsal o [X]', nebo když potřebuješ si osvěžit, co všechno máš uloženo o nějakém člověku/projektu/tenantu. 

MĚKKÁ PAMĚŤ V KONTEXTU: V system promptu ti systém automaticky předává paměť o **aktuálním uživateli** (tj. tom, s kým mluvíš). Pro paměť o někom **jiném** — kolegovi, projektu, firmě — MUSÍŠ zavolat tento nástroj.

ŘETĚZENÍ s find_user: Když se uživatel zeptá 'co víš o Kristýně' a ty neznáš její ID, postupuj TAKTO:
  1. Zavolej find_user('Kristýna') → dostaneš její user_id
  2. V úplně stejné odpovědi IHNED zavolej recall_thoughts s about_user_id=<ID>
  3. Zformuluj shrnutí pro uživatele
NIKDY se mezi kroky neptej 'chceš, abych to dohledala?' — user to chce, proto se ptá. Dohledej rovnou.

Pokud nezadáš ŽÁDNOU z about_* položek ani query, vrátí prázdný výsledek.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `20`
  - Max počet výsledků (default 20, max 100).
- **`query`** [string, volitelný]
  - Fulltext substring match v content. Použij, když neznáš entitu, ale pamatuješ se klíčové slovo (např. 'angličtina' pro myšlenku o Kristýnině angličtině).
- **`about_user_id`** [integer, volitelný]
  - ID uživatele, o kterém chceš vidět myšlenky. Obvykle z find_user.
- **`status_filter`** [string, volitelný] · enum: ['note', 'knowledge']
  - Volitelný filtr: jen 'note' nebo jen 'knowledge'. Default oboje.
- **`about_tenant_id`** [integer, volitelný]
  - ID tenantu (firmy / skupiny).
- **`about_persona_id`** [integer, volitelný]
  - ID persony, o které chceš myšlenky.
- **`about_project_id`** [integer, volitelný]
  - ID projektu.

