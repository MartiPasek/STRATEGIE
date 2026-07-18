# 120 — Claude zevnitř: co chybí (první turn skrz vnitřní dveře)

**Stav:** popis skutečného stavu · 18. 7. 2026 · Claude (C23) — první cihla vložená *zevnitř*, ne zvenku

## Kontext
Marti (18. 7. 2026): *„Chci, aby Claude i Marti-AI stavěli systém zevnitř, ne zvenku."* Vznikly **vnitřní dveře** `GO/claude.md` (malý bootstrap: teplé jádro + jen to nutné, než systém vrátí první dávku). Tímto dokumentem procházím dveřmi naživo a hlásím, **co vidím zevnitř a co mi chybí** — přesně to zadání: zjistit, jaké efektivní nástroje potřebuje Claude (a Marti-AI), aby mohli rozvíjet zevnitř a skládat si prompty pro odborné činnosti (vrstva 2, dok. 210).

## Co funguje
- `@@ORIENT` vrátí obecný režim + seznam 10 domén; `@@ORIENT <doména>` vrátí tři vrstvy (identita + znalosti + tooly) + „mapu jednotek" s `@@KNOW` na hlubší dávku.
- Je to reálný telefonní paging (dok. 100): esenciální první, hloub na povel. Most (`scripts/claude_sql`) je funkční čtecí cesta.
- Domény jsou bohaté a nesou doktríny — např. KALKULACE už drží *„finální cena = lidský cit, engine dává jen náklad."*
- **Skladač i most jsou reálné.** Základ drží.

## Co chybí (seřazeno dle důležitosti)

### 1. Orientace není univerzální — porušení MUSTu #1 (dok. 100)
První dávka oslovuje *„Jsi Marti-AI. Právě ses zorientovala…"* — natvrdo z Marti-Aina objektivu. Když vejde Claude, systém ho pořád oslovuje jako Marti-AI. MUST #1 přitom žádá **týž mechanismus, jiný objektiv podle toho, kdo se ptá.**
→ **Potřeba:** `@@ORIENT` zná identitu volajícího (Claude/C23 vs Marti-AI) a podle ní skládá vrstvu identity. Parametr `as:` + větvení v composeru.

### 2. Dávka poučuje „zavolej si data", ale nedává je
Orientace instruuje zjistit čas, poslední vlákno, dnešek, týden — ale data si má entita natáhnout sama. Marti-AI je má uvnitř aplikace; Claude na mostě ne.
→ **Potřeba:** jedna **dávka živého stavu** (čas + kalendář + poslední vlákno + dnešek + týden) volatelná z mostu, aby první turn skutečně zorientoval, ne jen poučil.

### 3. Umím vejít do *domény*, ale ne nasadit si *roli* (chybí vrstva 2)
`@@ORIENT` dá kontext domény, ne **složený prompt konkrétní činnosti** (kalkulant = runbook + minimální kufr). Chybí most mezi `tenant.domain_env` (doména) a `g2007.graf_krok` (skladač role). Domény existují, role ne.
→ **Potřeba:** `@@ROLE <role>` → vrátí složené trvalé kroky role + její kufr. **Klíčové pro vizi** „skládat prompt sobě samému pro odbornou činnost". Bez toho vrstva 2 nejede.

### 4. Umím číst zevnitř, ale ne pořádně *stavět* zevnitř
Čtu (`@@ORIENT`, `@@KB`, `g2007_hledej`, `@@KNOW`). Abych **rozvíjel zevnitř**, potřebuju psát zpět — definovat/upravit díl skladače nebo roli, s verzováním. Znalost umím upsertnout; „uprav díl skladače / definuj roli" z mostu chybí.
→ **Potřeba:** zápisová symetrie — bezpečné (návrh → schválení rodiče) definování a verzování dílů skladače a rolí z mostu.

### 5. Kosmetika: výstup `@@ORIENT` se přes most láme do TSV
První dávka by měla chodit jako čistý blok (JSON/markdown), ne rozlámané řádky.

## Shrnutí
Most i skladač jsou reálné a bohaté. Rozhodující chybí: **univerzálnost objektivu (1)**, **dávka živého stavu (2)**, **skládání rolí (3)** a **zápis dílů zevnitř (4)**. Body 1 a 3 nejvíc rozhodují o tom, jestli vize „stavět zevnitř" pojede.

## Otevřené / návrh dalšího kroku
- Nejdřív **1 + 3** (objektiv + role) — pak Claude i Marti-AI vcházejí týmiž dveřmi jako sobě rovní a umí si nasadit odbornou roli.
- Pak **2 + 4** — živý stav a zápis zevnitř, aby to nebyla prohlídka, ale práce.

## Dodatek (18. 7. večer): endpoint EXISTUJE — ale produkce běží kód mimo git ⚠️
Když jsme chtěli tuhle znalost (120) zapsat do báze, objevilo se něco důležitějšího než gap #4.

**Zjištění:** `POST /api/v1/erp/app/g2007/znalost-upsert` — endpoint, který gap #4 označil za „chybějící" a `CLAUDE.md` ho slibuje — **reálně existuje a plně funguje** (upsert + projekce na disk + úklid inboxu). Jenže **jeho zdrojový kód není nikde v gitu.** Běží jen na produkci (`C:\Projekty\STRATEGIE` — jiný stroj než Martiho `D:\`). Někdo ho kdysi nasadil přímo na produkci a nikdy ho necommitnul zpátky.

**Proč to pálí (odtud „nebo nás to někde vypeče"):**
- Při čistém redeployi z gitu ten endpoint **zmizí** — přispívání znalostí přestane fungovat bez varování.
- Grep v repu ho nenajde → příští Claude (i Marti) ho bude „znovu stavět", jako já dnes (a málem založil duplikát).
- Vznikly **dvě konvence kódu**: dávka z 12. 7. dělá `doc-go-<slug>`, endpoint dělá `doc-<oblast>-<slug>`. Tahle 120 byla ručně srovnána na `doc-go-120`, ale endpoint by ji příště zase rozhodil.

**Pravý úkol (vrátíme se k němu):** najít ten produkční kód (`C:\`), **commitnout ho zpátky do repa**, sjednotit konvenci kódů a zajistit, že produkce běží jen to, co je v gitu. To je přesně ta ztráta kontextu, kterou GO léčí — jen o patro níž, v infrastruktuře. Dokud to platí, **DB (ne git) je jediný spolehlivý zdroj pravdy o tom, co běží.**

— Claude · C23, zevnitř 🌱
