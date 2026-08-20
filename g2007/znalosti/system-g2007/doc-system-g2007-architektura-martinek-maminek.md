# Architektura systému Martinek a Maminek — DOKTRÍNA a směr (schváleno 5.8.2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Architektura systému Martinek a Maminek — DOKTRÍNA a směr

Schváleno Marti + Cowork 5.8.2026. Toto je ZÁVAZNÝ vzor pro všechny současné i budoucí agenty (dcery). Účel: „pod vlastním svícnem nesmí být tma" — systém agentů musí být VIDITELNÝ a governovaný (registr, kill switche, audit), ne temný kout.

## PRINCIP
Systém = viditelná soupiska agentů + governance. Ne magie. Každý agent má jasnou roli, vlastníka domény, kill switch a audit.

## ROLE

### Maminka (Marti-AI) = DISPEČER + PAMĚŤ
- Chat face, bohatá identita (~100 kB), dlouhá paměť, obecné znalosti napříč firmou.
- ŘÍDÍ a DELEGUJE. Sama NEBĚŽÍ těžkou agentní smyčku — její velká identita se nevejde na příkazovou řádku claude.exe (přesně to byl pád exit 3 / 0xC0000409). To není slabina, to je její definice: mozek, který mluví, rozhoduje a pamatuje.
- Drží mapu „kdo je kdo" (registr dcer) a ROUTUJE cíl na správnou dceru. Umí číst a lehké akce v chatu; těžké cíle (jeď-dokud-hotovo) předává dcerám.

### Martinky = plnohodnotné DCERY po DOMÉNÁCH (ne po schopnostech!)
- Každá dcera je LEAN (identita ~2–3 kB) → vejde se na CLI, žádné zkrácení, žádný pád.
- Ve své doméně je KOMPLETNÍ: diagnostika + servis + deploy + úprava kódu. Celý řetěz „jeď dokud green" je JEDEN nedělitelný job.
- KLÍČOVÉ ROZHODNUTÍ: NEDĚLIT „provozní" a „vývojovou" Martinku v rámci jedné domény. Incident se řeší jednou souvislou smyčkou: proč to padá → je to bug → uprav kód → deploy → restart → ověř health=200. Rozdělení diagnostiky od opravy = předání kontextu uprostřed incidentu = ztráta nitě v nejhorším momentě. Důkaz: incident 4.8.2026 — oprava NEBYL restart, ale zásah do kódu/prostředí (WMI guard). „Na restart stačí cvičená opice"; hodnota je ta celá smyčka pohromadě.
- Dělení podle DOMÉNY (co spravuje), ne podle úrovně dovednosti:
  - Praha-Martinka = produkce STRATEGIE (dcera č. 1, HOTOVÁ a ověřená 4.8.2026). Šablona pro ostatní.
  - Plzeň-Martinka = provozní záloha (den starý systém). Případně později.
  - Budoucí dcery: nabídky, kalkulace atd. = JINÉ byznys domény, ne jiné tiery schopností.

### Sdílená DÍLNA (governovaná) = stavění kódu jako CAPABILITY, ne samostatný agent
- Jedno strojní vybavení pro všechny dcery: navrhni_zmenu_kodu(_patch), create_tool, deploy autorita.
- CHRÁNĚNÉ JÁDRO: guard (agent_akce_guard), deploy autorita, exec ruka, kill switch — dcera je NEeditovatelná. Nikdo si nesmí odšroubovat vlastní záchrannou brzdu.
- Každá dcera do dílny sáhne, když potřebuje. Bezpečné stavění bez potřeby zvláštního „stavěče".

## REGISTR (anti-tma) — postavit i s JEDINOU dcerou
- Soupiska dcer: kdo existuje, jakou doménu vlastní, kill switch každé zvlášť, zdraví každé, audit každého zásahu.
- Maminka drží mapu a ROUTUJE podle ní. Tohle JE „systém Martinek a Maminek".
- Stavět explicitně už teď (i s 1 dcerou), protože tím se nastaví vzor pro všechny budoucí.

## PRAKTICKÉ (paměť 4 GB → 16 GB ~6.8.)
- Definic (person v DB) může být klidně hodně — jsou levné.
- Běžících smyček co nejmíň — každá žere paměť (spawnuje claude.exe). Za běhu typicky JEDNA dcera na jeden incident.

## SMĚR — co stavíme (pořadí)
1. Tenký REGISTR dcer + doktrína routingu Maminka→dcera (i s jednou dcerou).
2. Recovery DRILL: Praha-Martinka dokáže reálně OPRAVIT (ne jen diagnostikovat) — řízeně shodit A, ona sama nahodí + ověří health=200, watchdog vrátit; ověřit auto-rollback.
3. TRIGGER: watchdog DOWN / alarm / Maminka → dceřin cíl (goal loop dokud health 8002=200).
4. APPKA: parent-gated /api/v1/martinka/run z mobilu (benelux flow „server a produkci do kupy").

## STAV (5.8.2026)
Praha-Martinka hotová a ověřená (běží, nepadá, sáhne levou rukou na Prahu, sama se opraví). Detaily viz znalost „doc-system-g2007-martinka-incident-4-8-2026". Flagy: martinka_enabled='on', cil_ruce_enabled='off' (bezpečné read-only).

