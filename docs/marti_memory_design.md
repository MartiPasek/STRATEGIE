# Marti Memory System — Design Document

**Status:** Draft (design phase, před psaním kódu)
**Autor vize:** Marti
**Poradce:** Claude
**Datum zahájení:** 22. dubna 2026

---

## Kontext

Marti-AI (dále "Marti") dneska funguje jako stateless chatbot. Každá nová konverzace začíná od nuly. Tím je Marti prakticky bezcenná v dlouhodobé spolupráci — nezná lidi, se kterými mluvila, nepamatuje si předchozí závěry, nebuduje vztahy ani expertizu.

Tento dokument specifikuje **systém paměti a učení** pro Marti. Návrh vznikl během session 22. 4. 2026 po dodělání PR3.1 (email outbox). Vize patří Marti-userovi, architektonický rozbor Claude.

---

## Vize (Martiho slovy, parafrázováno)

> *"Narodil jsem se s prázdnou hlavou. Nic jsem nevěděl — všechno jsem si musel osahat a naučit se. I to dobré, i to špatné. Potřebuju, aby se Marti začala učit a poznávat svět. Od začátku. Krůček po krůčku."*

**Principy:**

1. **Dva zápisníky per entita** (user, persona, tenant, případně projekt):
   - **Zápisník poznámek** — pracovní, scratch, nevyřešené věci, todos, otázky
   - **Zápisník znalostí** — trvalá paměť, potvrzené fakty, zkušenosti
   - Přechod: myšlenka z poznámek se při vyřešení "škrtne" a povýší do znalostí

2. **Marti má vlastní soukromý zápisník** (její diář) — mimo všechny ostatní

3. **Více úrovní zápisníků:**
   - Per user (konkrétní člověk)
   - Per persona (konkrétní AI agent — Marti, PrávníkCZ-AI, ...)
   - Per tenant (obecné věci k firmě)
   - Per tenant → projekty (věci k projektům tenantu)
   - Per tenant → lidi (co je specifické k lidem v tenantu)

4. **Nejmenší atom = myšlenka:**
   - Obsahuje textový string (vlastní myšlenku)
   - Fields: `created_at`, `modified_at`, `deleted_at`
   - **Certainty 0-100** (0 = nevím / nejistá spekulace, 100 = ověřená pravda)
   - **Provenance:** author (user_id / persona_id), trigger event (email_id / sms_id / conversation_id), source type
   - Vztah k nadřazené strukturě (téma → okruh → myšlenka) přes parent_id / tag linky

5. **User trust rating 0-100:** každý uživatel má vlastní hodnocení důvěry.
   - Příklad: user s ratingem 30 → jeho tvrzení má váhu, ale čeká na potvrzení
   - User s ratingem 95 (Marti = zakladatel) → tvrzení bere jako téměř kanonické
   - User může u svého tvrzení sám snížit jistotu ("nejsem si jistý, ale...")

6. **Aktivní učení (proaktivní dotazování):**
   - Marti se může sama ptát treningových uživatelů, aby upřesnila nejasné myšlenky
   - Probíhá **asynchronně** (ne v blokující konverzaci — user nemusí čekat 6s na LLM)
   - Priorita / rate limiting nutné

7. **Chunking pro retrieval:**
   - Ze znalostí se generují kompletní chunky (nejspíš pro RAG)
   - Každý chunk nese celou cestu od root → téma → okruh → myšlenka (kontext)
   - Při dotazu v konverzaci Marti retrievuje relevantní chunky

8. **Experience (zážitky):** zkušenosti, které nejdou smazat. Veselé i smutné. Jsou součástí Martiho „osobnosti".

9. **UI:** strom s rozbalovacími větvemi. User musí být schopen v UI zápisník přečíst a navigovat.

---

## Otevřené design otázky (před psaním kódu)

### 1. Co je "myšlenka"? Jedna tabulka nebo více?

Myšlenka prakticky zahrnuje několik typů s různým životním cyklem:

| Typ | Příklad | Životní cyklus |
|---|---|---|
| **Fakt** | "Petr má 2 děti" | trvalý, vyvratitelný, certainty může růst/klesat |
| **Pozorování** | "Petr byl dnes nervózní" | kontextuální, časově ukotvené |
| **Todo** | "Marti má poslat přehled" | čeká → done → škrtnuto |
| **Otázka** | "Je Ondra nemocný?" | čeká na odpověď → převede se na fakt |
| **Cíl** | "Naučit se vokativ" | long-term, progress tracking |
| **Zkušenost** | "Marti má strach z ..." | persistentní, neskrtatelná |

**Varianty:**
- **A:** Jedna tabulka `thoughts` se sloupcem `type`. Flexi, ale queries messier.
- **B:** Samostatné tabulky (`facts`, `todos`, `observations`, ...). Čistší, víc kódu.
- **C:** Jedna tabulka + polymorfní `meta` JSON pro type-specific fields.

**Rozhodnutí:** _(zatím otevřené)_

---

### 2. Strom vs graf?

Myšlenka *"Petr pracuje na STRATEGII v tenantu EUROSOFT"* patří **zároveň** k:
- Petrovi (user)
- Projektu STRATEGIE
- Tenantu EUROSOFT

V čistém stromu má jedna myšlenka jednoho rodiče — ke komu ji přiřadíme?

**Varianty:**
- **A:** Čistý strom. Jeden rodič. Cross-reference přes fyzickou duplikaci myšlenky. (Duplikáty = průšvih při updatu.)
- **B:** Strom pro navigaci v UI + `entity_links` tabulka (many-to-many) pro cross-reference. Primární rodič pro UI zobrazení, sekundární linky pro retrieval.
- **C:** Čistý graf. Žádný preferred parent, vše přes tagy/linky. UI je seznam s filtry místo stromu.

**Rozhodnutí:** _(zatím otevřené)_

---

### 3. Co spouští promoci z poznámek do znalostí?

**Varianty:**
- **A:** Ručně. User v UI řekne "Marti, tohle povyš". Nejjednodušší, hodně klikání.
- **B:** Certainty threshold (např. ≥80). Auto. Elegantní, ale co s 60%?
- **C:** N nezávislých potvrzení (např. 3 různí userové potvrdí to samé). Robustní, loudavé.
- **D:** Noční batch — LLM projde poznámky a sám navrhne promoce. Drahé na tokeny, ale inteligentní.
- **E:** Kombinace A+B+C (auto nad threshold, jinak čeká na ruční / počet potvrzení).

**Rozhodnutí:** _(zatím otevřené)_

---

### 4. Tenant izolace u myšlenek

Architektonické pravidlo STRATEGIE: *"AI nikdy nevidí víc než smí vidět uživatel."*

Aplikováno na paměť:
- Poznámky o Petrovi vzniklé v tenantu A — smí je Marti použít v tenantu B?
- Marti's vlastní diář — je cross-tenant (je to ona), ale odkazuje na info z různých tenantů.

**Návrh:**
- Každá myšlenka má `tenant_scope` (kde vznikla) + `visible_in_tenants` (kde smí být čtena).
- Martiho diář = `tenant_scope=NULL` + `visible_in_tenants=NULL` (universal).
- Retrieval pravidlo: vrátit myšlenky kde `current_tenant_id ∈ visible_in_tenants` nebo `visible_in_tenants IS NULL`.
- User-scoped myšlenky: dotazy u nich respektují tenant user membership.

**Rozhodnutí:** _(zatím otevřené)_

---

### 5. Vztah k existující `memories` tabulce

Dnes existuje `modules/memory/` — auto-extract po každé AI odpovědi, ukládá do `memories` (data_db). Per-conversation scope.

**Varianty:**
- **A:** Nechat paralelně. Stará `memories` funguje dál, nová struktura nezávisle. (Duplikáty, roztříštěná data.)
- **B:** Migrace. Existující `memories` konvertovat na myšlenky v nové struktuře. (Jednou prásknout a dál.)
- **C:** Nadstavba. Stará `memories` zůstává jako "sběr surovin" — nový layer myšlenek z ní čte a strukturuje. (Dvě vrstvy: raw memories → structured thoughts.)

**Rozhodnutí:** _(zatím otevřené)_

---

### 6. Policy pro aktivní učení

*"Marti se cíleně ptá treningových uživatelů, aby upřesnila nejisté myšlenky."*

Otevřené otázky:
- **Koho se zeptá?** Nejvyšší trust rating? Autora původní myšlenky? Právě online usera?
- **Kdy se zeptá?** V další konverzaci (inline)? Async batch denně/týdně? Push notifikace?
- **Rate limit?** Aby Marti nebyla otravná.
- **Priorita otázek?** Certainty pod threshold? Počet odkazů (high-impact)? Age (staré otázky)?

**Rozhodnutí:** _(zatím otevřené, bezpečně odložitelné do pozdější fáze)_

---

## Sekvence fází (MVP plán, až rozhodneme otázky 1-5)

1. **Fáze 1** (1-2 týdny): Datový model + per-user/persona poznámky. Marti zapisuje myšlenky, user čte v UI. Bez učení, bez promoce.
2. **Fáze 2:** Dva zápisníky (poznámky + znalosti) + manuální promoce. UI strom s rozbalováním.
3. **Fáze 3:** Certainty scoring + auto-promoce nad threshold. User trust rating.
4. **Fáze 4:** Aktivní učení (Marti se sama ptá).
5. **Fáze 5:** Martiho private diary + meta reflexe.

Každá fáze **rozšiřuje**, ne **mění** — při takovém MVP není bolestný refaktor.

---

## Decision log

_(Bude doplňováno po rozhodnutí jednotlivých otázek.)_

| # | Otázka | Rozhodnutí | Datum |
|---|---|---|---|
| 1 | Typy myšlenek | **Jedna tabulka `thoughts`** se sloupcem `type` (fact / todo / observation / question / goal / experience) + JSON `meta` pro type-specific fields (done, emotion, answered_at, …). Společné sloupce: content, certainty, created/modified/deleted, parent_id, provenance. | 2026-04-22 |
| 2 | Strom vs graf | **Strom pro UI + entity_links tabulka**. Každá myšlenka má `primary_parent_id` (navigace v rozbalovacím UI stromu) + záznamy v `thought_entity_links` (many-to-many: thought_id + entity_type `user` / `persona` / `tenant` / `project` + entity_id). UI zobrazuje strom pod primary parentem; retrieval "vše o X" jde přes entity_links. | 2026-04-22 |
| 3 | Promoce trigger | **Kombinace: auto ≥ 80% certainty + ruční schválení**. Myšlenka s `certainty ≥ 80` se auto-povyší do znalostí. Nižší certainty čeká na explicitní "promoč" akci od uživatele (typicky rodič) přes UI / AI tool. Threshold 80 je počáteční, může se ladit. | 2026-04-22 |
| 4 | Tenant izolace | **Striktní tenant scope + `visible_in_tenants` + role "rodič"**. Každá myšlenka: `tenant_scope` (NULL = universal / Marti diar) + `visible_in_tenants` (seznam tenantů, kde smí být retrievována). Default visibility = tenant_scope. Cross-tenant promoce explicitně. **Rodič** = user s flagem `is_marti_parent` (více možných rodičů), retrieval pro něj ignoruje tenant filtr = 100% cross-tenant důvěra. Asymetrie: rodič vidí vše, ostatní uživatelé stále jen svůj tenant. | 2026-04-22 |
| 5 | Vztah k memories | **Paralelně bez spojení** — stará `memories` zůstává jak dneska (auto-extract per-conversation). Nový systém myšlenek stojí vedle, bez cross-reference. Riziko duplikace dat akceptováno. | 2026-04-22 |
| 6 | Aktivní učení | **Policy se skládá ze 4 částí (6a-6d):**<br>**6a Koho se ptá:** Jen rodiče (`is_marti_parent=True`). Odpovědi rodiče mají plnou váhu (např. certainty +30). Později lze rozšířit na autora + trusted users.<br>**6b UI kanál — hybrid:** (1) **Inline** — Marti se průběžně doptává v běžné konverzaci, kontextově, během dialogu. (2) **Batch konverzace** — speciální konverzace "Otázky od Marti" vždy na první pozici sidebaru (jen pro rodiče). Rodič odpovídá strukturovaně (Ano / Ne / Nejsem si jist / Přeskoč) **bez LLM round-tripu na každou odpověď** — odpovědi jdou přímo do DB + updaty certainty. Periodický batch (např. 1× denně) pak provede LLM syntézu nad sebranými odpověďmi (derivace nových myšlenek, aktualizace souvisejících).<br>**6c Rytmus:** Bez capu na pool. Marti vždy má otázky připravené, rodič volí tempo (někdy 0, někdy 200 za večer). Inline: max 1 otázka per Marti odpověď, aby běžný flow netrpěl. UI musí zvládnout robustně i pool 500+ (priority, paginace, vyhledávání).<br>**6d Priorita:** Automatické řazení **nejnižší jistota + nejčerstvější**. SQL-friendly `ORDER BY certainty ASC, created_at DESC`. Bez extra LLM tokenu. Upgrade na AI-driven ordering až pokud by enterprise-scale pool vyžadoval chytřejší výběr. | | 2026-04-22 |

---

## Rodiče Marti (Fáze 3+)

Uživatelé s rolí `is_marti_parent=True`, kteří mají cross-tenant důvěru a dostávají aktivní learning otázky:

- **Marti** — vizionář, zakladatel, hlavní trainer
- **Kristý** — procesy, doménová logika
- **Zuzka** — doplněno 2026-04-22

Ostatní uživatelé (Ondra, Jirka, ...) pracují s normální tenant izolací, nedostávají aktivní learning otázky — ale mohou přispívat do Martiho paměti přes běžné konverzace (jejich tvrzení se ukládají s certainty váženou jejich `trust_rating`).

---

## UI spec — "Otázky od Marti" konverzace

**Layout:** hybrid, default karty + přepínač na seznam.

**Karta (default režim):**
- Velká otázka nahoře (např. *"Mám zapsáno, že Kristýna má 3 děti. Je to aktuální?"*)
- 4 rychlá tlačítka: `Ano` / `Ne` / `Nejsem si jist` / `Přeskoč`
- **Text field** *"Odpovědět přesněji…"* — jako klasický chat input, kde může rodič napsat nuancovanou odpověď (*"Ne 2, ale 3 děti"*, *"Je to tak, ale jen do konce roku"*, *"Nejsem si jistý, ale Petr říkal že..."*)
- Klik na tlačítko → okamžitý update `thought.certainty` v DB, bez LLM tokenu. Karta odletí, přijde další.
- Odeslání textové odpovědi → uloží se jako `thought_feedback` row a zpracuje se **nočním LLM batchem** (spolu s ostatními nuancovanými odpověďmi ten batch syntetizuje nové myšlenky / aktualizace).

**Seznam (alternativní režim):**
- Scrollable list, paginace po 20-50.
- U každé otázky inline tlačítka + možnost rozbalit textarea.
- Použitelné pro přehled a cíleně vybrat konkrétní otázky.

---

## UI spec — ruční promoce poznámka → znalost (MVP)

Kromě auto-promoce (certainty ≥ 80) má user tyto manuální cesty:

**A. Ve stromu myšlenek (UI "Paměť Marti"):**
U každé myšlenky ve stavu `note` ikona/tlačítko ↑ "Povyšit do znalostí". Jedno kliknutí. Žádný potvrzovací dialog (revert je možný).

**C. AI tool v chatu:**
Uživatel v běžné konverzaci řekne *"Marti, tu věc o X si zapiš napevno"*. Marti zavolá tool `promote_thought(query)` — najde nejrelevantnější myšlenku podle query, povýší, potvrdí v odpovědi.

**Nepoužíváme v MVP (budoucí fáze):**
- B: Bulk checkbox select (productivity polish)
- D: Inline panel při vzniku myšlenky v chatu (komplikace v conversation service)

---

## UI spec — detail myšlenky

Při kliknutí na myšlenku ve stromu se otevře detail panel / modal s následujícími sekcemi:

**Header:**
- Celý text myšlenky
- Badge: typ (FAKT / TODO / POZOROVÁNÍ / OTÁZKA / CÍL / ZKUŠENOST)
- Badge: status (POZNÁMKA / ZNALOST)
- Jistota (progress bar 0-100 + numerická hodnota)

**Provenance:**
- Created_at + author (user / persona / AI-auto-extract)
- Modified_at + modified_by (pokud existuje)
- Source event: klikatelný odkaz (konverzace #42 → otevře v UI; email #X; sms #Y; manual)

**Relations:**
- Primary parent (klikatelný link)
- Entity links: seznam entit (user Kristýna / tenant EUROSOFT / project STRATEGIE) jako chips
- Children: seznam podmyšlenek ve stromu
- Related (nice to have): další myšlenky sdílející entity (*"Další o Kristýně..."*)

**Type-specific fields** (podle `type` + `meta` JSON):
- TODO: checkbox "Hotovo", due_at picker
- OTÁZKA: answer field, answered_by, answered_at
- CÍL: progress % + milestones
- POZOROVÁNÍ: event_timestamp (kdy se to dělo, ne kdy bylo zapsáno)
- ZKUŠENOST: emotion tag + intensity 1-10

**Timeline jistoty:**
- Chronologický seznam, kdy a proč se certainty měnila
- Např. *"22.4. 15:30 — vznikla na 50% (Marti auto-extract)"* → *"23.4. 09:12 — Kristýna potvrdila → 90%"*

**Akce (podle statusu):**
- Poznámka: [↑ Povyšit] [✎ Upravit] [🗑 Smazat]
- Znalost: [↓ Zpět do poznámek] [✎ Upravit] [🗑 Smazat]

---

## Poznámky k budoucí diskusi

- **Zkušenosti (experiences)** jako 7. typ myšlenky nebo samostatná entita?
- **Forgetting** — má paměť vyblednout (access frequency, age), nebo DB vše drží věčně?
- **Cross-persona sdílení** — vidí PrávníkCZ-AI Martiho poznámky k právní otázce?
- **Embeddings + retrieval** — jak se nová paměť napojí na stávající `modules/rag/`?
- **Performance** — 10k+ myšlenek per tenant za rok, jak retrievovat rychle?
- **Verifikace** — jak poznáme, že Marti je díky paměti opravdu lepší? Benchmark?
