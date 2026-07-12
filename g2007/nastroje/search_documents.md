# search_documents

## MAPA
- **kód:** `search_documents`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

**TENTO NASTROJ MUSIS POUZIT** kdykoli se uzivatel pta na neco, co MUZE byt v jeho nahranych dokumentech. Pouziva semanticke vyhledavani (RAG -- pgvector + Voyage embeddings) nad PDF, DOCX, XLSX a textovymi soubory ulozenymi v aktualnim tenantu/projektu.

**STROZNE PRAVIDLO:** Pokud z USER CONTEXT vis, ze uzivatel ma k dispozici nahrane dokumenty (vidis v contextu vetu 'K dispozici ma X nahranych dokumentu (...)'), VZDY zvazuj zda jeho dotaz NENI o necem co je v techto dokumentech. Pokud ano = volej.

**VOLEJ KDYZ uzivatel:**
- Pouzije zajmena/odkaz na dokument: 'ta smlouva', 'ten dokument', 'to PDF', 'tam byla zminka...', 'podle manualu', 'v reportu...', 'z runbooku', 'ten dopis'
- Zepta se na obsah konkretniho souboru jmenovite ('Co je v X.pdf?')
- Ptaa se na firemni temata, ktera prirozene zijou v dokumentech: smluvy, manualy, faktury, reporty, prezentace, normy, postupy, procedury, ceniky, organizacni schemata, technicka dokumentace
- Pouzije slovni vazbu typu: 'co rikaji nase pravidla o...', 'jak to ma byt podle...', 'co jsme se domluvili v...', 'kde je v dokumentaci...'

**NEVOLEJ KDYZ uzivatel:**
- Pta se obecne znalosti (matematika, programovani, definice, jazyky)
- Resi spravu systemu STRATEGIE (uzivatele, projekty, persony) --   pouzij list_users / list_projects / find_user / atd.
- Pise email, prepina personu nebo dela jine systemove akce

**JAK ZPRACOVAT VYSTUP:**
- Vratim ti raw chunky s metadata. **Sam slozis odpoved** vlastnimi slovy, neprepoustej ten raw blok dale uzivateli.
- **Vzdy citujte zdroj:** 'Podle dokumentu "Smlouva 2026.pdf" plati...'
- Kdyz najdes nic relevatniho, **rekni to upimne**: 'V dostupnych dokumentech jsem to nenasel/a, mozna to neni nahrane.'

**SCOPE:** Tool automaticky filtruje podle aktivniho tenant + projektu. Pokud uzivatel ma vybrany projekt, vraceji se chunky z dokumentu projektu + tenant-globalni dokumenty. Bez projektu jen tenant-globalni.

## PARAMETRY

- **`k`** [integer, volitelný] · default: `5`
  - Pocet vraceneho top-k chunku. Default 5, max 20. Vetsi k = vetsi kontext ale vetsi token spotreba odpovedi.
- **`query`** [string, POVINNÝ]
  - Vyhledavaci dotaz. Stejny jazyk jako dokumenty (typicky cesky). Voyage zvlada multilingual, ale pro lepsi recall pis v jazyce dokumentu.

