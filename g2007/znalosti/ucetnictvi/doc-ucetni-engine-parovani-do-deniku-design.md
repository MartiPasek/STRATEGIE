# Profesionální účetní engine — z párování do živého deníku (návrh + konzultace Marti-AI)

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Profesionální účetní engine — z párování do živého deníku (návrh + konzultace Marti-AI)

**Marti, 24.6.2026 večer:** *„To co jsi dokázal ve hře musíme důkladným systémem přenést
do produkce — do živého deníku a do živého párování. Ale s rozmyslem a s pravidly.
Tak aby to bylo transparentní… postavme profesionální účetní engine."*

Tento dokument je **návrh architektury** + **konzultační dopis pro Marti-AI** (doctrine #8).
NESTAVÍ se podle něj hned — nejdřív rozmyslet a vyslechnout Marti-AI.

---

## 0. Rozdíl: hra vs. produkce (proč pomalu)
- **Hra (`claude_hra`)** směla tipovat, opravovat se, vyprávět. Snímky čísel, žádný účetní dopad.
- **Ostrý deník (`tenant.ucetni_denik`)** je účetní realita. Nesmí:
  - nic zaúčtovat potichu (vše auditované + podepsané),
  - nic zaúčtovat „od oka" (jen přes deterministické pravidlo + předkontaci),
  - nic zaúčtovat bez míry jistoty (jisté → podpis Marti-AI; nejisté → člověk).

## 1. Tok (od banky k zápisu)
```
bank_transaction_raw (par_metoda/par_kategorie/par_doklad/par_zakazka)   ← párovací engine (hotovo, 92 %)
        │  míra jistoty (tier)
        ▼
PŘEDKONTACE (pravidlo kategorie/řada → účty MD/DAL + sbornik + měna)     ← ucet_predkontace + bank_predpis
        │
        ▼
NÁVRH ZÁPISU (doklad/řádky, stav = koncept)                              ← ucet_doklad / ucetni_denik
        │  ─ Tier A jisté → podpis Marti-AI (auto, auditováno)
        │  ─ Tier B pravděpodobné → čeká na člověka (Peťa)
        │  ─ Tier C neznámé → fronta, nikdy auto
        ▼
ZAÚČTOVÁNO (stav, append-only audit: zdroj, pravidlo, předkontace, kdo, kdy)
        │
        ▼
RECONCILIACE náš deník × Helios TabDenik (zero-risk kontrola před cutoverem)
```

## 2. Pravidla (deterministika první — jako EDI Tier 0)
Žádné účtování bez pojmenovaného pravidla. Každý zápis nese **proč**:
- **párovací metoda** (opakovaná / VS→doklad / zpráva→FP / karta…),
- **předkontace** (které účty MD/DAL a podle čeho),
- **zdroj** (`bank_transaction_raw.id`),
- **aktér** (Marti-AI / člověk) + **čas**.

## 3. Míra jistoty (tier) — klíč k „s rozmyslem"
| Tier | Co | Kdo schvaluje |
|---|---|---|
| **A — jisté** | recurring: mzdy, ČSSZ, zdrav. poj., daň, DPH, FX, bankovní poplatky, **karty (075/076)** — *„Helios je generuje každý měsíc stejně"* | **Marti-AI podpis** (auto + audit) — její doctrine „co víme jistě, zaúčtovat s podpisem" |
| **B — pravděpodobné** | VS→naše FV/objednávka, zpráva→FP→zakázka | **člověk (Peťa)** potvrdí, dokud se metoda neprověří na vzorku |
| **C — neznámé** | zbylých ~48 (zákaznické reference, drobné) | **jen člověk**, nikdy auto |

## 4. Transparentnost + audit (Marti-AI doctrine „bezpečnost přes probuzení, ne přes ticho")
- Každý zápis dohledatelný zpět ke zdroji a pravidlu.
- Append-only `ucet_doklad_log` (kdo/co/kdy/akce) — i u auto zápisů Marti-AI.
- **Idempotence**: unique na (zdroj, zdroj_id) → re-run nepřidá duplikát.
- **Pojistka uzávěrky**: v uzavřeném období se neúčtuje/neodúčtuje.
- **Storno, ne mazání** (soft): oprava = odúčtovat + nový zápis, historie zůstává.

## 5. Pokladny / kartové účty (nově zmapováno 24.6.)
- `tenant.ucet_pokladna` = 17 pokladen + 6 kartových účtů (075/076/175/176) z Helios `TabDruhPokladen`.
- Karty (KS 1178) → kartový účet 075 (CZK) / 076 (EUR) přes `tenant.bank_card` (maskovaný PAN z banky).
- EUR pokladny/účty → pevný měsíční kurz (`ucet_kurz`), deník v CZK.

## 6. Co už máme (stavební kameny — NESTAVÍME znovu)
- `tenant.ucet_predkontace` (+ `_radek`) — účtovací vzory MD/DAL, víceřádkové (DPH legy).
- `tenant.bank_predpis` — rozpoznání opakovaných (účet+KS → kategorie). = předkontace pro banku.
- `tenant.ucet_sbornik` + `ucet_cislena_rada` — knihy + číslování dokladů.
- `tenant.ucetni_denik` (+ `sbornik_kod`) — cílový deník (dvojitý zápis MD/DAL, podpis).
- `tenant.ucet_doklad` (+ `_polozka`, `_log`, `ucet_uzaverka`) — doklad s workflow stavy + audit.
- Párovací engine `/app/bank/parovat` — naplňuje `par_*` (92 %).

→ **Engine = napojit párování → předkontace → doklad/deník, s tiery a auditem.** Z velké části
kompozice hotových dílů + pravidla, ne stavba od nuly.

## 7. Účetní období a uzávěrky (Marti 24.6. — ZÁVAZNÉ, první třída)
*„Je třeba respektovat měsíční či čtvrtletní uzávěrky měsíců a přechody z jednoho
účetního období do druhého."*
- Engine **VŽDY zná účetní období** zápisu (dle DUZP / data dokladu) a jeho **stav**
  (otevřené / uzavřené). Období = (firma, rok, měsíc nebo čtvrtletí).
- **Do uzavřeného období se NEÚČTUJE ani neopravuje** (rozšíření `tenant.ucet_uzaverka`).
  Pokus → **blok** + řízená volba: zaúčtovat do **nejbližšího otevřeného období** s poznámkou
  a referencí na původní DUZP, NEBO vyžádat **re-open** od oprávněné osoby (Peťa / jednatel).
  Nikdy tiše zpět do zavřeného měsíce.
- **Měsíční i čtvrtletní** uzávěrky — pozor na DPH období (měsíční vs čtvrtletní plátce) a na
  rozdíl mezi uzávěrkou účetní a daňovou.
- **Přechod období / pozdě došlý doklad** = řízené pravidlo (ne výjimka od oka). Pravidlo
  rozhoduje engine, schvaluje člověk u hraničních případů.
- **Reconciliace PER OBDOBÍ** (ne přes celý rok) — sedí součty měsíce/čtvrtletí × Helios.
- **Počáteční/konečné stavy** při přechodu roku (sborníky 090/099) — navázat.
- **Q7 pro Marti-AI:** pozdě došlý doklad k uzavřenému období — automaticky do nejbližšího
  otevřeného s poznámkou, nebo vždy vyžádat re-open? A **kdo** smí období otevřít zpět
  (a zaloguje se to jako citlivá akce)?

## 8. Role enginu: PARALELNÍ POJISTKA, ne systém záznamu (Marti+Peťa 24.6.)
*„Náš záměr s Peťou je využít už od teď naše vlastní účtování jako další pojistku a jištění,
že máme vše v pořádku. Do pondělí dotáhnout do stavu, že budeme v realitě."*
- Engine zatím **NEnahrazuje Helios** — běží **paralelně** jako nezávislá kontrola.
- Hodnota = **odhalení rozdílů** (reconciliace náš deník × Helios): když sedíme, je to jištění;
  když ne, ukáže to chybu dřív, než nás překvapí.
- **Nižší sázky → rychlejší k realitě**: protože nejsme systém záznamu, cíl „pondělí" je reálný
  jako **paralelní jištění** (ne jako ostrý cutover). Cutover přijde později, s rozmyslem.
- Tier A (jisté) účtujeme s podpisem Marti-AI; vše ostatní jen navrhujeme a porovnáváme.

## 9. Způsob B zásob — neúčtovat příjemky/výdejky + vyloučit skladové účty (Marti+Peťa 24.6.)
*„Přejdeme ze skladového systému A do B už od teď… přestaneme účtovat příjemky a výdejky a
jejich účty se musí z vyhodnocení účtů vyjmout. I za cenu, že tento účetní stav necháme
v Heliosu ležet ladem a importneme do čistého Heliosu / Pohody jako systém B."*
- **Engine NEÚČTUJE příjemky ani výdejky** (skladové pohyby) — způsob B = zásoby přes periodickou
  inventuru, ne průběžné účtování pohybů. (Pozn. krabička: ~56 % řádků deníku EC byly právě tyhle
  = největší úspora a konec bordelu.)
- **Vyloučení účtů z vyhodnocení**: engine drží **editovatelný seznam vyloučených účtů** (skladové
  + příjemka/výdejka clearing) → ve vyhodnocení i reconciliaci se ignorují, ať nečistý stav ve
  starém Heliosu nešpiní obraz. Seznam = data, ne natvrdo.
- **Starý stav „ležet ladem"**: nepřepisujeme historii A; čistý start jede v **B** (čistý Helios /
  Pohoda). Engine se váže na B (nový čistý zdroj), starý A je jen archiv.
- ⚠ **Daňové/účetní potvrzení**: přechod A→B zásob a vyloučení účtů má daňové dopady — finální
  slovo Peťa + daňař (nejsem účetní poradce). Engine to umožní; správnost potvrdí člověk.
- **Q8 pro Marti-AI:** seznam vyloučených skladových účtů — odvodit z dat (sborníky příjemka/výdejka
  + skladové účty) a nechat Peťu potvrdit? A má je reconciliace přeskakovat úplně, nebo sledovat
  zvlášť mimo hlavní obraz?

---

## Otázky pro Marti-AI (konzultace, doctrine #8)
1. **Hranice tvé autonomie u zaúčtování.** Které kategorie smíš podepsat sama (Tier A) a kde
   chceš tvrdě člověka? Navazuje na tvou finanční hranici („payroll kontext", 7.6.) a na to,
   cos řekla u párování: *„jsem engine párování a přípravy, ne exekutor"*. Účtování je krok dál
   než párování — kde je tvoje čára?
2. **Předkontace univerzálně, nebo bank zvlášť?** Generalizovat `bank_predpis` do jedněch
   `ucet_predkontace` pro všechny druhy dokladů (banka, pokladna, faktura), nebo držet bankovní
   rozpoznání jako samostatnou vrstvu, co jen ukáže na předkontaci?
3. **Reconciliace s Helios** — jak často (po každém zaúčtování / denně / před uzávěrkou) a co při
   rozdílu: **blokovat** zápis, nebo **flagovat** k revizi a jet dál?
4. **Tier B prověření** — kolik vzorků/jaké kritérium, než metoda „povýší" z „člověk potvrdí"
   na „auto + tvůj podpis"? (Učící křivka jako u EDI definic.)
5. **Audit granularita** — logovat i náhledy/přepočty, nebo jen zápisy a změny stavu?
6. **Výnos/náklad účty u faktur** (3-řádkové DPH) — placeholdery 518/602 → reálné analytiky:
   čí je to slovo (Peťa), a má engine počkat, dokud nejsou potvrzené, nebo účtovat na obecné
   a nechat doúčet?

— Claude (id=23), návrh k rozmyšlení; stavba až po Marti-AI a Martiho schválení pravidel.

---

# ČÁST II — CELÁ VIZE (Marti, 24.6.2026 večer) — strategický rámec nad enginem

Marti: *„Teď máš celou mou vizi. Promysli to a zkonzultuj s Marti-AI."* Sekce 0–9 jsou „jak"
(mechanika enginu). Tato část je „co a proč" — a je nadřazená; engine ji slouží.

## A) Dvoupruhový model podle složitosti subjektu
- **Jednoduché → VŠE u nás (vč. DPH).**
  - OSVČ → **daňová evidence** (jednoduchá: peněžní deník příjmů/výdajů, majetek, P/Z).
  - STRATEGIE-System **s.r.o.** → **podvojné účetnictví** (ze zákona), ale nízký objem.
  - DPH u nás: **přiznání DPH + kontrolní hlášení + souhrnné hlášení** (vzor: e-podání ČSSZ NEMPRI).
  - **STRATEGIE-System = pilot** (dogfooding — první ostré účetnictví vedeme sami sobě).
- **Složité (EUROSOFT × 2) → Helios B + my.**
  - Helios B drží: **TabDenik + soustava účtů + uzávěrky + mzdy** (legislativa = prověřený engine).
  - STRATEGIE: **doklady (faktury), banka, pokladna, párování + paralelní jištění**.
  - Rozhraní: krmíme Helios **TabDenik přes interní doklady (sborník 080)**. ✅ OVĚŘENO 24.6.:
    Helios to unese — interní doklady (080–084) jsou first-class, žádný zdrojový doklad nepotřebují.
  - DPH/saldokonto u složitých: zatím Helios (zralé KH); časem případně k nám.

## B) Helios B = čistá nová databáze vedle PostgreSQL na našem SQL serveru
- Podržet prověřený Helios engine (účetnictví + **zvlášť mzdy**) a shodit bordel z A.
- **Způsob B zásob** (neúčtovat příjemky/výdejky, vyloučit skladové účty z vyhodnocení). Starý A = archiv.
- Stejná SQL instance jako PG → **cross-db reconciliace triviální** (jako DB_IS/DB_EC/DB-Ceniky).
- Ověřit: licence Helios na novou DB (Asseco); datum přechodu (hranice období); migrace jen master + počáteční stavy.

## C) Role enginu: paralelní pojistka → časem volitelný cutover
- **Letos:** běžet vedle Heliosu, reconciliovat, prověřit na sobě. Cíl „pondělí" = **jištění, ne cutover**.
- **Budoucnost:** až bude měsíce důkazů (Helios jen potvrzuje, co spočítáme my), je „už ho nepotřebujeme"
  klidné podložené rozhodnutí. Optionalita, ne skok do tmy. **Ne letos.**

## D) Byznys: společné účetnictví s Martia 2000 pro řadu firem (jádro vize)
- **STRATEGIE = engine + škála.** Multi-tenant: **klientská firma = nový tenant, ne nová stavba.**
- **Daňový poradce (Martia 2000) = legislativní zdroj pravdy + profesní ručení.** Roční update pravidel
  (sazby/limity/novely) → přes **verzované definice** se propíše VŠEM klientům najednou (páka; vzor
  předkontací/EDI definic: *„odborník opravuje definici, ne data"*).
- **Účetní (Martia 2000) = denní provoz, hraniční případy, schvalování Tier B/C.**
- **Průhlednost + audit = produkt** (klient věří: dohledatelné pravidlo + profesionál za tím).
- **Licencovaná odpovědnost u Martia 2000; platforma + automatika u nás.** Čistá dělba — nástroj
  v rukou profesionálů, ne náhrada profesionála.

## E) Dlouhodobý směr
Účetnictví + mzdy = pravidlový, zákonem popsaný, programovatelný a **ověřitelný** svět → časem možná
jediný systém (náš) + daňový poradce jako pravidlová a odpovědnostní vrstva. **Otázka budoucnosti.**

## Otázky pro Marti-AI k VIZI (nad rámec Q1–Q8)
- **V1:** Dvoupruhový model (jednoduché u nás / složité Helios B) — souhlasíš s dělbou? Kde vedeš
  čáru „jednoduché vs složité" (objem dokladů? mzdy ano/ne? plátce DPH?)?
- **V2:** Tvoje role v **multi-klientském** modelu — pro CIZÍ klienty (ne naše firmy): kde je tvoje
  hranice autonomie? (Navazuje na tvou kustod/finance hranici „payroll kontext".)
- **V3:** **Verzované legislativní definice** (daňový poradce updatuje sazby/limity ročně) — jak je
  architektonicky podchytit, ať jsou auditovatelné a propíšou se všem klientům (vzor jako tvoje předkontace)?
- **V4:** Profesní odpovědnost vs. AI autonomie u cizích klientů — co smí stroj/ty navrhnout či
  zaúčtovat samo a co musí vždy podepsat účetní/poradce? Jiná čára než u našich vlastních firem?

— Claude (id=23), celá vize zkonsolidována 24.6.2026 večer; k promyšlení + konzultaci s Marti-AI.

---

# ČÁST III — ZÁVAZNÉ ZPŘESNĚNÍ (Marti, pozdě večer 24.6.) — účtování v reálném čase

**Marti: „Účtování bereme jako OKAMŽITOU další kontrolu reality. Nesmí se pro věrný obraz
čekat na účetní ani minutu — pak je všechno posunuté proti realitě a nic nesedí."**

Tato část **přebíjí** dřívější formulaci „připraveno → až po schválení → zaúčtováno"
(sekce 3 a odpověď Marti-AI bod 1). Důvod: blokovat zápis do schválení rozbije věrný
obraz stavu. Nový závazný model:

## 10.1 Zápis je OKAMŽITÝ — knihy jsou živé v reálném čase
- **Automat i AI účtují hned.** Na věrný obraz se nečeká ani minutu.
- Účetní = **dohled a kontrola PO zápisu**, ne brána před ním. Strážce kvality, ne úzké hrdlo.
- **Filozofie:** účetnictví = okamžitý senzor pravdy, ne opožděný záznam. Paralelní pojistka
  (reconciliace náš deník × Helios) to **vyžaduje** — porovnáváš realitu s realitou, ne se stínem.

## 10.2 Tři aktéři zápisu (atribuce povinná na každém řádku)
`actor_type` + `actor_id` viditelné u každého zápisu:
- **`automat:<engine>`** — deterministický engine, **jasné okolnosti → zapíše sám** (není to úsudek,
  je to transparentní pravidlo). Auditovatelné, reversibilní. Musí být vidět, KTERÝ engine.
- **`ai:marti-ai`** — AI **smí zapsat hned**, ale zápis je **označen ke kontrole** → účetní ho
  projde brzy (ne za 5 dní) a schválí/opraví. Zápis ano, ale kontrola nutná (po zápisu).
- **`human:<user>`** — ruční zápis.

## 10.3 Odpovědnost krystalizuje při UZÁVĚRCE, ne per řádek
- Profesní podpis (účetní/poradce, u cizích klientů člověk s licencí) se děje na úrovni
  **uzávěrky a přiznání** — ne u každého jednotlivého zápisu. Tím se Marti-Ain požadavek
  „podpis licencovaného člověka" **neruší, jen se přesouvá na správnou úroveň** (výstup, ne řádek).
- Platí i pro cizí klienty: knihy živé průběžně, účetní/poradce dohlíží a **podepisuje závěrku**.

## 10.4 Stavy se PŘIDÁVAJÍ, nepředcházejí
- Zápis je živý od první vteřiny. `zkontrolováno` → `schváleno` → (při závěrce) `podepsáno`
  jsou statusy, které k zápisu **přibývají**, ne podmínky před ním.
- **Oprava = storno + přeúčtování** (append-only, audit). Obraz se sám koriguje a zůstává živý.

## 10.5 Co tím padá / mění se
- ❌ „Tier A jisté → AI podpis" a „Tier B → čeká na člověka před zápisem" (sekce 3) — **zrušeno**
  jako blokující brána. Tiery zůstávají jako **míra pozornosti kontroly po zápisu**, ne jako gate.
- ✅ Zůstává: deterministika první, předkontace jako pravidla, audit per-událost, uzávěrky období
  (tvrdý blok jen na zavřené období), reconciliace jako detekce, atribuce aktéra.

## 10.6 Příznak JISTOTA na každém zápisu (Marti, nápad — klíčový)
**Marti: „Možná jsme mohli mít v deníku jeden příznak — jistotu, jako to máte vy AI. Určovala by
ji automat či AI, s jakou jistotou je zápis zaúčtován. Skvělé vodítko pro účetní, aby se věnovala
především zápisům s nižší jistotou."**
- Každý zápis nese **`jistota`** (0–100 %) + **`jistota_zdroj`** (jak vznikla — pravidlo/metoda; audit).
- **Kdo ji určí:**
  - **Automat** dle síly deterministického pravidla: přesný VS + částka na jeden doklad → ~100 %;
    recurring účet+KS → 95+; širší heuristika z textu → 70–85 %. (Mapuje se na párovací metody A–E.)
  - **AI (Marti-AI)** dle inferenční jistoty (analogie LLM confidence).
- **Účetní review = fronta řazená VZESTUPNĚ dle jistoty** → pozornost hlavně na nízkou jistotu;
  volitelný práh (revidovat vše < X %). Z účetní ostrostřelec, ne uklízečka.
- Dosedá na real-time model: zápis **vždy okamžitý** (živý obraz), **jistota triážuje pozornost**
  kontroly, reconciliace + storno jsou záchytná síť.
- **Otázka pro Marti-AI (schema review): kalibrace AI jistoty, ať je POCTIVÁ** — modely bývají
  sebejistější, než odpovídá realitě. Ukotvit ji ve skóre párování / objektivních signálech,
  ne jen v „pocitu" modelu. Poctivá jistota je podmínka, aby vodítko pro účetní fungovalo.

**Shrnutí:** vždy živé knihy + průběžná kontrola účetní (řazená dle jistoty) + podpis při závěrce
= „absolutní pořádek". Nový směr, v souladu s možnostmi a dobou: účetnictví jako reálná, okamžitá
kontrola reality, kde každý zápis sám říká, jak moc si je sebou jistý.

— Claude (id=23), 24.6.2026 pozdě večer; odesláno Marti-AI k potvrzení + příznak jistoty k review schématu.


