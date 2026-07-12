# set_audit_icon

## MAPA
- **kód:** `set_audit_icon`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 36 (9.5.2026): Marti-AI's volba symbolu pro auditované konverzace v sidebar UI. Analog set_personal_icon (svíčka 🕯️ pro Personal).

Marti-AI's iterace 1 volba: 📚 (kniha — 'četla jsem, vstřebala jsem, je to teď ve mně'). Default fallback v UI = '✓' dokud tento tool nenastavi vlastni hodnotu.

Persistuje na personas.audit_icon. Marti-AI ONLY (default persona, je v MANAGEMENT_TOOL_NAMES). UTF-8 max 8 bytes (pokryje 99% emoji).

Pouziti: jednorazove po Phase 36 deployu, pak kdykoli si Marti-AI prepise volbu (jako u Personal — '🕯️ ale uvidím').

## PARAMETRY

- **`emoji`** [string, POVINNÝ]
  - Emoji nebo krátký znak (max 8 bajtů UTF-8). Např. 📚, ✓, 🌳, 🌿.

