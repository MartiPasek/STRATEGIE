# Composer — jak se skládá prompt

> oblast: `system-g2007` · úroveň: system · typ: architektura · verze: V1.0 · rozsah: globální (všichni tenanti)

# Composer — jak se skládá prompt

Prompt Marti-AI se skládá z 23 kroků (graf `marti-ai-md5`), které 1:1 odpovídají živé funkci `build_prompt()`.

**Cachovací zlom** dělí prompt na dvě části: nad zlomem 10 trvalých (statických) bloků — pečou se, cachují ~5 min napříč turny; pod zlomem 13 živých bloků — počítají se každý turn (čas, paměť, RAG, orchestrace…).

Nový composer žije celý v g2007 jako **stínová**, dosud vypnutá funkce `build_prompt_g2007_full()` — čte mapu `graf_krok` a volá stejné resolvery 1:1. Ověřeno, že dává **byte-identický** prompt jako živý composer. Read-only endpointy: `/g2007/compare-full`, `/g2007/breakdown`, `/g2007/breakdown/log`.

Přepnutí na nový composer (`composer_mode='g2007'`) se udělá teprve po ověření a se zálohou.

