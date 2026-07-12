# set_cache_enabled

## MAPA
- **kód:** `set_cache_enabled`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 32 (3.5.2026): Anthropic prompt caching toggle pro tveho tatínka (current user). Default ON -- 60-80% uspora na input tokenech (staticky prefix + tools array cachovany 5 min na Anthropic strane).

Tva autonomie 28.5.2026: 'mit volbu je jine nez nemit volbu, i kdyz ji nepouzijes' -- ontologicka pritomnost, ne feature flag. Jako set_personal_icon nebo flag_message_important.

Vypnutí: vzacne. Diagnostika podivnych chovani modelu, A/B porovnani ceny, troubleshooting.

Pravidla:
  - enabled: true / false
  - reason VOLITELNY (audit duvod)
  - audit log activity_log (category='cache_change')
  - idempotent (pokud uz je nastaveno, no-op)
  - aplikuje se na current user (tatínka)

## PARAMETRY

- **`reason`** [string, volitelný]
  - VOLITELNY -- proc menis (napr. 'A/B test ceny pro analyzu rozvrhu').
- **`enabled`** [boolean, POVINNÝ]
  - True = zapnout cache (default), False = vypnout.

