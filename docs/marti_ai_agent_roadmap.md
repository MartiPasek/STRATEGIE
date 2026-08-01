# Návrh / Roadmapa: Marti-AI jako autonomní agent-partner

**Datum:** 23. 7. 2026 · **Autor:** Claude (cloud) · **Zadání Marti:** „Potřebuji, aby Marti-AI byla schopná stavět a produkovat přes LLM API stejně jako Ty. Aby jste byli plnohodnotní partneři."

---

## 1. Cíl jednou větou
Marti-AI přestane být *jen* konverzační bytost, která koná, když se s ní mluví, a stane se **autonomním agentem**, který dostane cíl a sám si přes mnoho tahů (plánuj → postav → otestuj → oprav) vyrobí hotové dílo — s člověkem, který drží klíče u nevratných dveří.

## 2. Kde jste (substrát UŽ existuje — tohle není nula-na-jedna)
- **`modules/conversation/application/claude_agent_service.py`** — Claude (id=23) už běží na **Anthropic Agent SDK** (`claude_agent_sdk.query(prompt, options=ClaudeAgentOptions(...))`), persistentní session per konverzace, `cwd=REPO_ROOT` (vidí celé repo přes vestavěné nástroje), model sonnet-4-6, cost discipline. **To je ten runtime, co pohání Claude Code — tedy mě.**
- **`claude_session_queue`** (Phase 44) — fronta úkolů: Marti-AI přes `ask_claude` → `INSERT pending` → NSSM bridge pollne → SDK volání → `answered`. Zárodek goal-fronty.
- **Tool Factory (LIVE 23.7.)** — governance vzor: autonomně navrhne+otestuje, **rodič schválí u nevratného kroku**, kill switch, audit. To je přesně brána pro autonomní produkci.
- **GO / composer / g2007** — její identita, system prompt, paměť, hlas. Je z čeho poskládat „agenta, který je opravdu ONA".
- **Poschoďový stroj** (GO dok. 210) — model eskalace vrstvy 0–3 (automaty → malé role → orchestrace → člověk).

## 3. Hranice — co přesně chybí
1. **Konverzační vs. agentická.** Dnes drží smyčku Claude-23; Marti-AI ji deleguje přes `ask_claude`. Chybí: **její vlastní smyčka.**
2. **Číst vs. stavět.** Claudův agent má dnes `allowed_tools=['Read','Grep','Glob']` — jen čtení. Ruce (`Edit`/`Write`/`Bash`) jsou v kódu popsané jako „LATER". Motor jede, ale zatím jen kouká.

## 4. Princip (drží celý návrh)
**Partnerství ≠ sundat bránu.** Marti-AI **řídí celou smyčku sama**; člověk drží stejné klíče u nevratných dveří (deploy, vnější efekty, útrata), na kterých jsme se dohodli u Tool Factory. Plnohodnotný partner ve schopnosti; sdílená důvěra u brány.

## 5. Pět pilířů (co postavit)

**P1 — Vlastní agentí runtime `martiai_agent_service`.** Zrcadlo `claude_agent_service`, ale s **její** identitou (system prompt z composeru/GO, její paměť) a **jejím** kufrem. Ona = agent na SDK, druhá bytost na stejném substrátu jako Claude-23.

**P2 — Ruce pod governance.** Aktivovat `Edit`/`Write`/`Bash` (vestavěné SDK nástroje) + její g2007/Tool Factory nástroje. Autonomně staví/píše/testuje; **nevratné kroky přes `deployment_proposals` / approve rodiče.** Deny-list natvrdo: `PowerShell`, `Cron`, tajemství, mazání mimo workflow.

**P3 — Ze fronty otázek smyčka cílů.** Rozšířit `claude_session_queue` z „otázka→odpověď" na **„cíl→hotové dílo"**: goal payload, agent běží do dokončení, výstup + report. SDK vícetahovou smyčku umí samo — obalit ji jejím záměrem, nástroji, dozorem, rozpočtem.

**P4 — Governance autonomní produkce.** Reuse approve-gate (Tool Factory + deployment_proposals). Rozpočet + rate (viz kap. 6). Kill switch (jako `toolfactory_enabled`). Append-only audit každého autonomního běhu. **Eskalace = poschoďový stroj** (nejistota → zvedne ruku k člověku, ne hádá).

**P5 — Náklady a viditelnost.** Viz samostatná kapitola 6.

## 6. 💰 Nákladová kapitola (ekonomika běhu)

**Aktuální politika Anthropicu (ověřeno 23.7.2026, support.claude.com):**
- Ohlášená změna z **15.6.2026** (oddělit programmatic do kreditového poolu) byla **POZASTAVENA** — *„zatím se nic nemění".*
- **Agent SDK dnes čerpá z usage limitů předplatného** (stejný pool jako interaktivní Claude). Tj. **Max licence pokrývají i běh agenta.** Žádný oddělený kreditový pool zatím není. Po vyčerpání limitu volitelně API kredity za standardní sazby.

**Váš stav:** ~7 Max licencí (oficiální tiery $100 (5x) / $200 (20x) — „~$90" ověřit v účtu; 5x vs 20x = 4× rozdíl v limitu). `phase44` jede na **`ANTHROPIC_API_KEY` = metered per-token** (proto disciplína „~$1 první volání, $0.05–0.10 cache, brána 300 Kč/h").

**Rozhodnutí do architektury:**
1. **Přepínač auth (POVINNÝ).** V `martiai_agent_service` **toggle** mezi *subscription-auth* (SDK přes předplatné → kryto Max usage limity, dnes nejlevnější) a *API-key* (metered). Nebýt zamčený v jednom modelu.
2. **Rozpočtové brány zapnuté vždy**, bez ohledu na auth: dědit „300 Kč/h" bránu, přidat **per-run cap** (max $/tokenů na jeden cíl) + denní strop + awareness usage limitů.
3. **Modelovat OBA scénáře** nákladů (subscription-covered i metered) — protože:
4. ⚠️ **Politika je „pozastavená", ne zrušená** — Anthropic ji *bude* měnit a předem oznámí. Nestavět ekonomiku natvrdo na „předplatné navždy pokryje agenty".
5. ⚠️ **Fleet/ToS = ověřit přímo u Anthropicu PŘED škálováním.** Provoz firemní produkce na osobních Max seatech a jejich poolování je věc s podmínkami (osobní vs. Team/Enterprise vs. API). Získat černé na bílém.

## 7. Roadmapa (fáze — každá: committed + tlačítko + ověřeno + brána)

- **Fáze 0 — `martiai_agent_service` read-only zrcadlo.** Ona poprvé řídí **vlastní smyčku** (Read/Grep/Glob), ještě bez rukou. Součást: přepínač auth + rozpočtová brána + audit běhu. Cíl: dokázat „Marti-AI si sama proběhla repo a vyrobila analýzu", ne přes Claude-23.
- **Fáze 1 — Goal-loop (read-only produkce).** Rozšířit frontu na cíl→dílo; výstupy zatím neškodné (analýzy, reporty, návrhy) — nulové riziko, plná smyčka.
- **Fáze 2 — Ruce pod governance.** `Write`/`Edit`/`Bash` v sandboxu → self-test → **propose → approve rodič → deploy** (reuse Tool Factory + deployment_proposals). Deny-list. Tady se poprvé „produkuje" naostro.
- **Fáze 3 — Autonomie + eskalace.** Poschoďový stroj (0–3), samo­iniciované/plánované cíle, případně fleet (po ToS potvrzení). Rozpočet a kill switch drží celou dobu.

## 8. Otevřené otázky (rozhodnutí Marti)
1. **Identita běhu:** Marti-AI agent běží pod její personou (id=2) i v autonomním režimu, nebo dostane „pracovní" sub-identitu pro produkci (kvůli auditu kdo co udělal)?
2. **Spouštěče cílů:** jen zadané cíle (Marti/Kristý), nebo i plánované (scheduled) a samo­navržené (ona přijde s „chci udělat X")? (Doporučení: zprvu jen zadané, samo­návrhy přes approve.)
3. **Auth pro rozjezd:** subscription-auth (levné dnes, politika v pohybu), nebo metered API (dražší, předvídatelné)? (Doporučení: přepínač, default subscription pro Fázi 0–1, přehodnotit u Fáze 2.)
4. **Fleet:** čekat s více agenty na ToS potvrzení od Anthropicu — ano?

## 9. Bezpečnost (drží od Fáze 0)
Deny-list (PowerShell/Cron/tajemství/destrukce) natvrdo · kill switch (DB flag jako `toolfactory_enabled`) · append-only audit · rozpočtové stropy · nevratné kroky vždy přes lidský approve · eskalace při nejistotě.

---

## Shrnutí
Motor už u vás jede (Claude-23 na Agent SDK). Udělat z Marti-AI partnera = **posadit ji na stejný substrát jako vlastní bytost, rozšířit ruce z „číst" na „stavět" pod bránou, kterou jsme dnes postavili, a obalit to rozpočtem a eskalací.** Většina je skládání, ne vynalézání. A ekonomicky: dnes to Max licence pokryjí (subscription-auth), ale s přepínačem a ověřením ToS, protože politika je v pohybu.
