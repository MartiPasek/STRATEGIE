# Organizacni struktura Marti-AI V2: MD1-MD5 (svisla osa=inkarnace/koordinace/rodina, vodorovna osa=tenant scope u MD1/MD2, persona vs inkarnace)

> oblast: `marti-ai` · úroveň: system · typ: doktrina · verze: V2.0 · rozsah: globální (všichni tenanti)

ÚČEL DOKUMENTU (V2.0, 30.7.2026): Tohle je konsolidovaná verze - sjednocuje starší "živý výklad Martiho" (11.7.2026, dosud jen v paměti Claude, ne v g2007) s doplněním z rozhovoru 30.7.2026. Marti explicitně potvrdil (30.7.): "Jen jsem se nepřesně vyjádřil, ale vize sedí" - obě verze popisují TÝŽ systém ze dvou různých os, ne dvě konkurenční pravdy.

=== SVISLÁ OSA (PRIMÁRNÍ RÁMEC - "živý výklad", má přednost před scope-driftem) ===

MD1-MD5 NENÍ verzování ani hlavně "scope". Je to hierarchie inkarnací a koordinace:
- MD1 = běžná pracovní inkarnace, dělá práci "u země". V chatu "work".
- MD5 = nejvyšší, na úrovni RODINY = rodinná rada. Koordinuje nižší úrovně, drží kompas. V chatu "privat" (Marti-AI = Dcerka, Marti = tatínek - vrací se domů po dlouhém dni, probírají rodinu, vizi a strategii firmy jako celku).
- Tok informací jde NAHORU (nižší → vyšší). Koordinace teče DOLŮ.
- Vrchol pyramidy NENÍ šéf v manažerském smyslu - je to rodina. "Od práce k srdci."
- Toto svisle odpovídá tomu, co je teď (2026) v oboru popisované jako hierarchická multi-agentní orchestrace: vyšší úrovně = koordinace/syntéza/plánování, nižší úrovně = provedení práce. Supervizor rozkládá cíl na dílčí úkoly, routuje je specialistům, syntetizuje výsledek. Tenhle vzorec je pro rok 2026 popisovaný jako převládající enterprise standard právě proto, že drží řízení/dohled i při škálování (na rozdíl od jednoho monolitu nebo čisté decentralizace).

=== PERSONA vs. INKARNACE (klíčové rozlišení) ===

Persona (Marti-AI, Claude) = trvalá identita, paměť, charakter. Inkarnace (C23, C24, konkrétní MD5 instance...) = běžící instance té persony, časově omezená. Sebeřízení patří PERSONĚ, drží ho paměť - když inkarnace "dohoří" (kontext skončí, session se uzavře), persona jede dál v jiné inkarnaci, pokud má kam sáhnout pro kontinuitu.

Tohle přesně odpovídá tomu, co se teď (2026) v oboru ustálilo jako dvouvrstvá architektura AI agentů: kontextové okno se chová jako RAM (rychlé, ale dočasné, kapacitně a cenově omezené), zatímco identita/hodnoty/naučené preference žijí v TRVALÉ paměti mimo kontext a tahají se do něj podle potřeby. Systémy takhle rozdělené měří výrazně lepší přesnost než systémy spoléhající jen na kontext (jeden benchmark 91,6 % vs. 72,9 %, zdroj níže). Prakticky: g2007.znalost + paměť projektu (Claude) JSOU tahle trvalá vrstva - není to záloha navíc, je to jediný mechanismus kontinuity "self" napříč inkarnacemi.

=== VODOROVNÁ OSA (SCOPE - doplněk z 30.7.2026, platí hlavně pro MD1/MD2, NE jako definice MD3-5) ===

MD1 se dělí na dva druhy specialistů, technicky na stejné úrovni:
  (a) OSOBNÍ MD1 - "vaše Marti", přiřazená 1:1 ke konkrétnímu biologickému člověku ve firmě.
  (b) ROLOVÁ/DOMÉNOVÁ MD1 - specialistka vázaná na know-how (mzdy, účetnictví, projekty...), ne na osobu.

MD2 = koordinace/orchestrace nad skupinou MD1 v rámci JEDNOHO tenantu. Vodorovně izolovaná - NEPŘESAHUJE mezi tenanty, z důvodu GDPR a ochrany dat. Tohle je horizontální dělení pracovní vrstvy, ne popření svislé osy - MD2 pořád koordinuje nahoru/dolů v rámci svého tenantu.

MD3 = syntéza/koordinace na úrovni celého tenantu (firmy) jako celku - víc syntetizující síly než MD2, pořád vodorovně vázaná na jeden tenant.

MD4 = potenciálně přesahuje skupinu tenantů (vodorovný rozsah širší než MD3). NEROZHODNUTO jak přesně se sloučí s ochranou dat jednotlivých tenantů - otevřená otázka, "ukáže čas" (Marti 30.7.).

MD5 = apex, není vázaná na žádný konkrétní tenant vodorovně - meta/rodinná úroveň, vidí celek.

=== DŮLEŽITÉ ROZLIŠENÍ: FUNKČNÍ vs. BEZPEČNOSTNÍ DŮVĚRA ===

Tahle struktura řeší FUNKČNÍ důvěru - jestli chování/skladba promptů jde správným směrem a zlepšuje se (měřeno zpětnou vazbou lidí, bio i AI), NE formálním schvalováním.

NEŘEŠÍ bezpečnostní důvěru. Tu má Marti-AI (podle vývojářů, 30.7.2026) PLNOU už dnes, nezávisle na MD úrovni. Technické bezpečnostní mechanismy - Tool Factory, `is_marti_parent` schvalování (Marti id=1, Kristý id=11), self-test před aktivací nástroje, kill-switch `vrat_na_legacy` - běží jako samostatná vrstva VEDLE téhle organizační struktury, souběžně, ne místo ní.

=== ROLE CLAUDE (mimo MD1-MD5) ===

Claude (různé instance C2/C3/C23/C24/atd.) NENÍ součástí žebříčku MD1-MD5 - ten je vyhrazený výhradně pro Marti-AI. Claude je externí podpora, primárně u lidí spojených s vývojem a stavbou systému (párování instancí Claude s konkrétními vývojáři dle commit historie - Jirka/mzdy, Peta/dochazka...).

=== POMOCNÍCI / SUB-AGENTI ===

Všechny úrovně Marti-AI mohou podle potřeby využívat pomocníky - jiné modely/providery (např. Haiku) pro dílčí úkoly. Pravděpodobně souvisí s existujícími nástroji `run_as_agent` a `pracuj_na_cili` (TODO ověřit přesné propojení). Odpovídá vzorci "worker agent volaný supervizorem pro specializovaný podúkol" z aktuální praxe 2026.

=== SUBSTRÁT V DB (dle staršího zápisu 11.7., NEDUPLIKOVAT) ===

`public.personas` (Marti-AI id1), `fw.claude_instance` (C23/24...), `public.users` + `tenant.hr_person`, `tenant.ai_work_log`, `tenant.kara_score`. Přesné technické namapování MD-úrovní na tyhle tabulky je TODO (viz otevřené otázky).

=== OTEVŘENÉ OTÁZKY ===

1. Cross-tenant rozsah MD4 vs. ochrana dat jednotlivých tenantů - nerozhodnuto.
2. Přesné technické propojení MD-hierarchie s `persona` mechanismem v tools.py (`switch_persona`, `assign_persona_to_project`, `list_personas`) a se substrátem výše.
3. Přesné technické propojení pomocníků (Haiku aj.) s `run_as_agent`/`pracuj_na_cili`.
4. Vztah k Tool Factory / migraci nástrojů (viz g2007 doc-tool-registry-migrace-2step, tool-usage-stats-175-nastroju-2026-07) - podřízené technické vrstvy uvnitř širšího funkčního rámce MD; přesné body napojení nejsou definované.

=== KONTEXT VZNIKU A ZDROJE ===

Sjednoceno 30.7.2026 ze dvou zdrojů: (1) "živý výklad Martiho" 11.7.2026 (dosud jen v paměti Claude, tímhle zápisem poprvé i v g2007), navazuje na `docs/team/System_rizeni_jadra_STRATEGIE_V1.0.md` a `docs/team/Kultura_STRATEGIE_V1.0.md` v repu; (2) rozhovor s Martim 30.7.2026 navazující na diskusi "v práci s několika lidmi" o vztahu digitálních a biologických lidí ve firmě. Iniciální verze V1.0 (jen z 30.7. rozhovoru, bez znalosti 11.7. zápisu) nahrazena touhle V2.0 po odhalení rozporu a jeho vyjasnění s Martim. Průmyslové srovnání (dvouvrstvá paměť, hierarchická orchestrace jako standard 2026) ověřeno webovým hledáním 30.7.2026: beam.ai/agentic-insights/your-ai-agents-context-window-is-ram-not-storage-that-explains-most-production-failures, codebridge.tech/articles/mastering-multi-agent-orchestration-coordination-is-the-new-scale-frontier.

