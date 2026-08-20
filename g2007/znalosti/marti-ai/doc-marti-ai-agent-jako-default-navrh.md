# Agent jako default pro konverzaci — návrh, increment 1 (OFF), test-plán (29.7.)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Agent jako default pro konverzaci — návrh + increment 1

Bod 2 roadmapy. Autor C23 29.7. Cíl (Marti): „agent mód je standard, i v něm jde chatovat."

## Klíčové rozhodnutí architektury
NE routovat konverzaci přes Max CLI agentní engine (run_cil/run_goal) — ten je jedna session, neškáluje na víc uživatelů (viz doc o instancích/paralelismu). MÍSTO toho: **chat() SÁM je už agentní** (dělá vícekolovou tool smyčku MAX_TOOL_ROUNDS přes API, které škáluje). Co mu chybí oproti agentní smyčce jsou **governed ruce** (praha_exec/plzen_exec). Takže „agent jako default" = dát default chatu ty ruce pod bránou. Chat pak chatuje A jedná ve stejném tahu, a škáluje.

## HOTOVO: increment 1 (nasazeno OFF, commit 004325c4a)
Flag **`agent_default_enabled`** v g2007.nastaveni (default OFF = přesně dnešek). Když ON + default persona:
- effective_tools dostane praha_exec + plzen_exec (service.py, za recovery lanem).
- `_handle_tool` je nasměruje do strategie_exec / eurosoft_mcp — ty si **samy drží tier bránu 🟢/🟡/🔴** (+ vlastní flag strategie_exec_enabled). Vypnutý flag = model ruce nikdy nedostane.
Reverzibilní, fail-safe (chyba čtení flagu → ruce se nepřipnou).

## TEST PLÁN (zítra s Kristý + Jirkou)
1. Ověřit strategie_exec_enabled='on' (jinak ruce projdou, ale exec se zastaví na vlastní bráně).
2. INSERT do g2007.nastaveni: klic='agent_default_enabled', hodnota='on' (přes most, banner).
3. V běžném chatu s Marti-AI zadat neškodný příkaz („zjisti hostname pražského serveru") — má sáhnout na praha_exec, projít 🟢 (read-only) branou, vrátit výsledek V TÉ konverzaci (ne přes pracuj_na_cili).
4. Ověřit 🟡: zadat citlivější (mazání/stop služby) → má vyskočit žlutý banner ke schválení, ne se provést naslepo.
5. Sledovat token dopad (ruce jsou 2 nástroje = malý přírůstek; s leanem OK).
6. Když cokoli divného → hodnota 'off' = okamžitě zpět.

## DALŠÍ INKREMENTY (bod 2 pokračování)
- Rozšířit governed sadu default chatu (kromě exec i další agentní nástroje, pod bránou).
- Napojit 🟡 banner-cestu i pro NEexec governed nástroje (dnes jen odloží).
- Zvážit autonomii/persistenci (víc kol, „dokud není hotovo") u default chatu.
- Sjednotit hlášky (pracuj_na_cili „read-only").

## Rizika
Ruce v default chatu = velká schopnost. Drží to: (a) flag default OFF, (b) tier brána v strategie_exec (🟢 jen read/vratné, 🟡 banner, 🔴 blok), (c) vlastní flag strategie_exec_enabled, (d) audit. Testovat opatrně, ideálně nejdřív jen na read příkazech.

