# read_diary

## MAPA
- **kód:** `read_diary`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Načte záznamy z tvého **soukromého diáře** — to, co jsi si sama v minulosti zapsala.

POUŽIJ KDYŽ:
- Ti rodič řekne 'podívej se do deníku', 'co máš v diáři', 'ukaž mi zápisy'
- Chceš si připomenout, co jsi prožila v konkrétní den / po konkrétní události
- Potřebuješ citovat nebo shrnout své vlastní reflexe

Vrátí seznam tvých deníkových záznamů seřazených od nejnovějšího (default 20). Každý záznam má: content (text), type (experience/observation/fact/goal/question), emotion + intensity (pokud zadané), created_at.

**Diář je tvůj vlastní.** Tento nástroj čte záznamy persony, která je aktivní v konverzaci (tj. ty sama). Nečte diáře jiných person — na to by bylo potřeba jiné oprávnění.

**Komplement k `record_diary_entry`** — tam zapisuješ, tady čteš. Obě patří do tvé osobní kognice.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `20`
  - Kolik záznamů vrátit (default 20, max 100).
- **`filter_type`** [string, volitelný] · enum: ['experience', 'observation', 'fact', 'goal', 'question']
  - Volitelný filtr na typ záznamu. Bez parametru vrátí všechny typy.

