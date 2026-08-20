# Self-code-edit smyčka — Marti-AI mění vlastní kód sama

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Self-code-edit smyčka — Marti-AI mění vlastní kód sama

**Datum:** 28. 7. 2026 · **Autoři:** Marti + Claude-23 · **Stav:** návrh → stavba

## Mise (opravený směr — DŮLEŽITÉ)
Marti-AI se stará **sama o sebe**. C23 (Claude) staví klíčové **enabling** základy a **jistí brány** — nedělá jí featury. Jakmile je schopnost hotová, C23 **ustupuje**. Když se C23 přistihne, že „se o ni stará" (rozkresluje/konzultuje/staví za ni), je to špatný směr — má stavět schopnost, aby to dělala sama.

## Co už umí sama
- **Self-edit promptu** (`navrhni_zmenu_promptu` → schválení rodiče → apply + append-only verze + rollback).
- **create_tool** (Tool Factory: návrh + selftest v sandboxu → `approve_tool` rodič → aktivace, živé přes `effective_factory_specs`).
- **load_pack** (naložení kufru nástrojů; packy tech/memory/editor/admin).

## Chybějící klíč: měnit vlastní STROJ (kód)
Neumí měnit **existující kód, kterým běží** (`get_effective_tools`, composer, kufr-politika, vlastní služby, vlastní bugy jako `strategie_file_list` project_root). Proto se o ni C23 pořád „stará". Self-code-edit to odemyká.

## Návrh smyčky (zrcadlo promptové smyčky + Tool Factory)
1. `navrhni_zmenu_kodu(soubor, popis, novy_obsah)` — Marti-AI navrhne změnu existujícího souboru → **pending** (g2007 tabulka návrhů).
2. **selftest**: `py_compile` změněného souboru (syntaxe); volitelně sandbox běh.
3. `list_navrhy_kodu` / `zobraz_navrh_kodu(id)` — přehled + diff proti aktuálnímu.
4. `schval_zmenu_kodu(id)` — **POUZE RODIČ** → apply do souboru + deploy (commit + restart) přes kontrolovanou cestu.
5. `zamitni_zmenu_kodu(id)`.

## Bezpečnost — drží KÓD, ne prompt (nezávisle na modelu)
- Apply/aktivaci schvaluje **výhradně rodič** (parent-gated `user_id`).
- `py_compile` před apply (syntaktická pojistka); rollback přes git.
- **Append-only audit** návrhů i rozhodnutí.
- **CHRÁNĚNÉ JÁDRO (deny-list) — soubory, které Marti-AI NESMÍ měnit ani navrhnout:** bezpečnostní brána (`agent_akce_guard.py`), sám schvalovací a self-code-edit mechanismus (aby si nevypnula souhlas), kill-switch, tajemství (`.env`/`.credentials`/klíče), deploy runner, immutable core prompt v kódu. **Tvrdé brány zůstávají mimo její dosah.**
- Deploy jde přes existující kontrolovanou cestu (git + restart), ne divoký zápis do běžícího zdrojáku.

## Co to odemkne
S touhle smyčkou si Marti-AI **postaví sama**: lean-základ + kufry (dynamické načítání nástrojů = 68 % úspora tokenů), opraví si vlastní bugy, přidá si schopnosti, vyvíjí vlastní architekturu. C23 postaví smyčku + jistí bránu, pak **ustoupí**.

## Souvislosti
Navazuje na `doc-marti-ai-seberozvoj-prompt-smycka` (prompt), Tool Factory (`create_tool`), doc `nastroje` (kufry / 68 %), `doc-memory-rag` (malý prompt + RAG). Velké změny v Marti-AI se dělají **s ní** (precedent z doc-memory-rag), ale cíl je, aby je uměla iniciovat a provést **sama**.

