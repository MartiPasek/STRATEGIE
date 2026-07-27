# Inside-build — Marti-AI/app-Claude staví nástroje i automaty zevnitř pod app-bránou (návrh)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Inside-build — návrh (k projednání Marti/Kristý/Claude-24)

**Stav: NÁVRH 24.7.2026.** Cíl: inside systém (Marti-AI + app-Claude) umí ZEVNITŘ STRATEGIE navrhnout, postavit a spustit nástroje I automaty — bez Coworku — každý nový přes SCHVÁLENÍ rodiče v appce. Cowork (C23) schopnost připraví+zapne; stavění dělá inside systém. NENÍ náhrada Coworku (ten zůstává na těžkou přípravu); je to samostatnost na dostavování/ladění/debug/jištění produkce (hlavně když je člověk mimo PC, na dovolené).

## Princip
"Stav cokoli, brána je u schválení." Ne rigidní whitelist situací (příklady se nesmí stát doktrínou); každý NOVÝ nástroj/automat = per-item schválení rodiče přes appku před aktivací. Jednou schválený se používá volně. Konzistentní s Tool Factory + Cílovým režimem (audit = paradoxně víc bezpečí).

## Už existuje (stavební kameny)
- **Tool Factory** (tool_registry): create_tool → self-test sandbox → propose → rodič approve → active. Kill flag toolfactory_enabled, audit tool_audit, conflict-of-interest guard.
- **Framework g2007.automat**: spousteni+interval_min (hlídání), pozadavky (co dělá), pri_chybe, eskalace_agent+agent_prompt (eskalace na agenta, default Haiku), aktivni; běhy g2007.automat_run (vysledek, eskalovano_na, eskalace_vysledek).
- **Cílový režim** (staví Kristý+C24): app-approval + tabulka cílů + ClaudeAktivita audit.
- **martiai_agent_service**: agentí smyčka + metered failover (nasazeno 24.7.).
- Most, g2007 (sdílený mozek), zálohy (zaloha_prompt + externí CMIS immutable).
KLÍČ: poschoďový stroj (automat→Haiku→Claude→člověk) i governance jsou z velké části HOTOVÉ → inside-build = SPOJENÍ dílů, ne vynalézání.

## Co postavit (spojit díly)
1. **create_automat** (Tool Factory rozšířený o automaty): navrhne automat (kód, spousteni/interval, pozadavky, eskalace_agent+agent_prompt) → self-test → propose → rodič approve v appce → zápis g2007.automat aktivni → běží na frameworku.
2. **Definice úlohy automatu bezpečně:** (a) SQL check + prahová podmínka, (b) volání už schváleného nástroje, (c) malý generovaný krok. Vždy read-first; zásahy do produkce pod audit + eskalace; nevratné/efekty ven přes appku.
3. **Eskalační žebřík:** vrstva 0 automat mechanicky → 1 Haiku (agent_prompt, levné) → 2 Claude (app-Claude, když Haiku nevyřeší) → 3 člověk (appka). Framework má eskalace_agent/eskalovano_na; dořešit řetěz Haiku→Claude→člověk + prompt-šablony.
4. **App-approval kanál:** banner Cílového režimu (C24). Interim (než banner je): chat s Marti-AI (rodič), stejný vzor jako schval_metered_varku.
5. **App-Claude identita+paměť** (aby "Claude zevnitř" byl fakt já): system_prompt z Claude23.md, soukromé úložiště, perzistentní vlákno s ŘÍZENOU (nedestruktivní) kurací kontextu — agent sám řekne co plně zachovat/shrnout/zahodit. Paměť přes g2007 + privátní store.
6. **Governance (dno):** per-item app approval (rodič), audit každé akce (automat_run/ClaudeAktivita), read-first, nevratné/efekty ven přes appku, CMIS dno, kill switch, deny-list katastrofické, rozpočet+failover.

## Tok
Cowork (C23) připraví schopnost → inside (Marti-AI/app-Claude/člověk) navrhne automat → app banner → rodič schválí z mobilu → automat se postaví a běží. PRVNÍ REÁLNÝ TERČ: Eliščin watcher e-mailové schránky (e.kolarova@, soudeček VP) vznikne TOU cestou, ne opravou z Coworku zvenku.

## Fáze
- **A (must-have PŘED dovolenou):** create_automat + eskalace Haiku→Claude→appka + app-Claude identita/základ paměti → z mobilu postavit a spustit jednoduchý watcher/self-heal pod schválením. (Metered failover hotov.)
- **B:** bohatší kurace kontextu, víc typů úloh automatů, plnější toolset app-Claude.
- **C:** širší autonomie, plánované/samonavržené automaty, fleet (po ToS).

## Rozdělení práce
C23 (Cowork): create_automat, eskalační řetěz, app-Claude identita/paměť. Kristý+C24: Cílový režim app-approval UI + tabulka cílů (= schvalovací kanál). Sdílení přes g2007 + WORK_LOCK, střídání C23↔C24.

## Otevřené otázky
1. Jak inside definuje "co automat dělá" bezpečně (SQL check / volání schváleného nástroje / generovaný krok). 2. Haiku — který model + prompt-šablony vrstvy 1. 3. Interim approval (chat Marti-AI) vs appkový banner (C24) — kdy překlopit. 4. App-Claude perzistentní vlákno — kde a jak (tabulka + pravidla kurace). 5. Rozsah must-have automatů před dovolenou.

