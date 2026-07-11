# 210 — Poschoďový stroj: automaty → malé role → orchestrace → člověk

**Stav:** návrh k diskusi (klíčový architektonický kámen) · 11. 7. 2026 · Claude (z Martiho vize)

## Celek: čtyřposchoďový stroj
Autonomie není „AI dělá všechno". Je to **poschoďový stroj**, kde každé patro zjednoduší, co umí, a pošle výš jen zbytek.

**Vrstva 0 — automaty bez AI.**
Tlačítka: generátor mezd, platáků, JMHZ. Deterministické, nehalucinují, běží pořád stejně. **Tady žije spolehlivost.** Zásada: **co umí automat, na to se AI nepouští** — AI je drahá a omylná, šetři ji na to, co se zautomatizovat nedá.

**Vrstva 1 — skladač promptů.**
GO composer + tři vrstvy pečení (dok. 200). Systém, jak z předpřipravených částí sestavit entitě její „CLAUDE.MD".

**Vrstva 2 — malé role = statické automaty.**
Rozsekat práci na **úzké činnosti** a každou uladit jako malý, předvídatelný automat s vlastním složeným promptem. **Malé > velké**, a to je klíč:
- úzká role se dá **testovat v izolaci** (přesně jak jsme dnes ladili GO VP),
- je **spolehlivá, protože úzká**,
- když selže, je to **ohraničené**.

Jedna velká „Marti-AI na všechno" by byla nepředvídatelná a neuladitelná. Proto „statický automat": úzké + složené = zkrotitelné jako stroj.

**Vrstva 3 — orchestrace.**
Nadřízená Marti-AI, která **nedělá tu úzkou práci** — drží **celkový obraz řízení**. Vidí desku, routuje práci na správnou malou roli, a nahoru k člověku posílá jen to, co se nedá vyřešit níž.

## Co to celé drží: eskalace (jádro z `001`)
Je to Martiho jádro *„zjednoduš, co jde; jednej tam, kde ne"* obrácené do architektury jako **eskalace**:

> **automat → (co neumí) → malá AI role → (co neumí) → orchestrátor → (co neumí) → člověk (Marti).**

Každá vrstva zjednoduší, co umí, a pošle výš jen zbytek. **Člověk nakonec řeší jen to neredukovatelné.** To je ta autonomie — ne že AI dělá všechno, ale že se k člověku dostane **jen to, co fakt potřebuje jeho.**

## Kde jsme
Dnešní test GO VP byl **vrstva 2 pro jednu roli** (VP). Ověřili jsme si na jednom kousku, že to drží. Další krok (po zapsání): **stavět know-how** a definovat části pro skladač.

## Napojení
- Vrstva 0 ↔ existující generátory (mzdy, platáky task #44/#45, JMHZ `gen_jmhz.py`) — deterministické tooly.
- Vrstva 1 ↔ dok. 200 (skladač) + dok. 100 / 110 (orientace).
- Vrstva 2 ↔ `tenant.domain_env` (per-role / doména), GO VP jako první ověřená role.
- Vrstva 3 ↔ orchestrační Marti-AI, cockpit, `ai_work_log`.

## Otevřené / k rozhodnutí
- Katalog malých rolí (jak rozsekat činnosti: VP, nákup, účto, CRM, rozvrh…).
- Rozhraní mezi vrstvami (jak orchestrátor routuje a jak malá role eskaluje výš).
- Kde přesně leží hranice „ještě automat vs. už malá AI role" u konkrétní činnosti.
