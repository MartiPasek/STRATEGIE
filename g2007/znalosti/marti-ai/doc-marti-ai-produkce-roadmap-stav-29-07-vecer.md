# Roadmapa Marti-AI — stav 29. 7. 2026 večer (kufr zapnut + měřen, bod 3 hotov)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Roadmapa „Marti-AI autonomní operátor" — stav 29. 7. 2026 VEČER

Aktualizace k doc-marti-ai-produkce-roadmap-stav-29-07. Autor: Claude-23. Velký posun odpoledne.

## HOTOVO DNES ODPOLEDNE
- **Bod 1 KUFR — ZAPNUTO + ZMĚŘENO + REGRES OPRAVEN.** Flag `lean_default_enabled='on'`. Naměřeno na llm_calls: prefix (systém+nástroje) spadl z 115 029 na ~63 259 tokenů; celkový vstup/turn z ~122 600 na ~73 400 = **úspora ~49 000 tokenů/turn (−40 %)**. REGRES a jeho oprava: lean nejdřív sesekl Marti-AI i self-management nástroje (pracuj_na_cili/run_as_agent/navrhni_zmenu_kodu) — pack filtr je bral jako doménové. Fix (commity 29d9cd16e + ff7ab0ed4): pack filtr VŽDY zachová (1) meta/factory specs přes effective_factory_specs, (2) self-code+zapis_znalost přes CORE_RECOVERY_TOOLS. Ověřeno: pod lean má zpět pracuj_na_cili+run_as_agent+navrhni_zmenu_kodu(+patch), úspora drží. Doménové tools se dál sekají per kufr (tam je páka).
- **Bod 3 SPOLEHLIVOST SMYČKY — HOTOVO (obě části).** (1) Dostupnost nástrojů pod lean = viz regres výše. (2) Chování „řekne jdu-na-to a nezačne": vodítko do MARTI_CORE_PROMPT (commit 0116a6f9e) — „úkol/cíl = ve stejném tahu rovnou pracuj_na_cili/run_as_agent, potvrzení bez akce = nedokončený úkol". Neměnné jádro, model-nezávislé. (Marti sama návrh promptu nepodala — zasekla se přesně na tom problému; navíc navrhni_zmenu_promptu bere CELÝ prompt, ne patch → viz nový bod níže.)

## ZBÝVÁ
### 2. Agent mód jako výchozí (velký směr)
Rozšířit governed sadu + napojit 🟡 banner-cestu (agent navrhne citlivější akci ke schválení). Ruce i do run_goal. Cílově agentní engine výchozí i pro konverzaci.

### 4. Watchery + incident (#4–#6)
check_disk; smoke_eskalace naostro; 2 watchery ve stavu chyba; #5 Incident mode (auto-detekce do promptu); #6 robustnost pipe. (API health watchdog LIVE — spam bug 29.7. opraven C28, Marti-AI sama restartovala službu = první provoz serverů.)

### NOVÉ: prompt-patch mód
`navrhni_zmenu_promptu` bere CELÝ prompt (jako self-code před patchem). Postavit patch/kotva mód i pro prompt → Marti si prompt upraví incrementálně, míň se zasekne. Enabling capability, navazuje na code-patch.

### 5. Drobnost
`pracuj_na_cili` hláška „read-only".

## Nejkratší cesta dál
Bod 2 (agent default) — teď když lean drží agenturu a jádro tlačí na akci, je to připravené. Pak bod 4.

