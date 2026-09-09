# Strom skupin — návrh ke schválení

> **Pro:** Marti Pašek · **Od:** Peťa Šafránková (připravil Claude‑26) · **21. 7. 2026**
> **Stav: NÁVRH, NENASAZENO.** Dotýká se tří oblastí (docházka, org struktura, mzdy),
> proto jde ke schválení, ne rovnou do práce.

## 1. Co se stalo

Peťa má v Opravách docházky působnost „kancelář". V „Najít člověka" jí chybí
**Zuzana Duspivová** — přitom je to finance a administrativa (kontrolor vydaných
faktur, správce upomínek, pojištění, výkazů firmy, firemního e‑mailu).

Důvod: drží šestý, okrajový post **REFERENT NESHOD**, který visí pod **VEDOUCÍM
KVALITY**, a ten drží Dušan. Pravidlo zní „jeden post pod Dušanem = celý člověk je
výroba", takže jeden post z šesti přebije všech pět ostatních.

Není to ojedinělé. Stejně vypadává Jiří Veverka a stejná logika by hodila do výroby
i Dušana samotného, kdyby na něj někdo pravidlo pustil obráceně.

## 2. Proč to nejde spravit jednou opravou

Systém dnes odpovídá na otázku „patří tenhle člověk do výroby, nebo do kanceláře?"
**čtyřmi různými způsoby** — a každý dá jiný výsledek:

| kde | jak se to počítá |
|---|---|
| Opravy docházky (`att_fix_scope`) | org podstrom pod Dušanem, natvrdo `user_id=41` v kódu |
| Automat a fond do FPD | docházková kategorie (`att_kategorie.dopichavat_fond`) |
| Plán nepřítomností (`_ABSENCE_SEGMENTY`) | **napevno psaný seznam názvů skupin v kódu** |
| Schvalování volna (`att_approver_group`, Jirka 21. 7.) | členství přes org posty |

Duspivovou tři z nich shodně hodí do výroby, pokaždé z jiného důvodu. Spravit
jedno pravidlo znamená, že další tři zůstanou rozejité.

## 3. Návrh: jeden strom skupin

Personální skupiny (`tenant.staff_group`) už mají skoro všechno, co je potřeba —
vedoucího, zástupce, pracovní režim, ikonu, řazení, archivaci, a přes
`staff_group_member.score` i pojem **primární skupiny**. Založil je Marti
9.–11. 6. 2026.

**Chybí jim jediné: nadřazenost.**

```sql
ALTER TABLE tenant.staff_group ADD COLUMN parent_id bigint
    REFERENCES tenant.staff_group(id);
```

Nullable sloupec, čistě aditivní — staré dotazy ho ignorují, nic se nerozbije.

```
VÝROBA .......................... Dušan Havlát + Michaela Hladíková
   ├── Výroba (35) · Zkušebna (2) · PLC (11) · VP (7) · E-plan (2)
KANCELÁŘE ....................... Peťa Šafránková
   ├── Vedení (7) · Nákup (7) · Finance (6) · Obchod (5) · HR (7)
   └── IT (5) ................... Kristýna Marešová   ← přebíjí rodiče
```

### Odpovědnost per agenda (přesně jako Centrála)

V Centrále má každá skupina (přehled **7626**, `EC_Skupiny`) tři samostatné sloupce:
`OdpovedneOsobyDoch` (kontrola docházky), `OdpovedneOsSchvalVolno` (schvalování
volna), `OdpovedneOsobyPrescasy` (přesčasy). Vazba člověk ↔ skupina je M:N
(přehled **7630**, `EC_SkupinyVazby`) — lidé jsou běžně ve víc skupinách.

Navrhujeme totéž: k uzlu stromu se přiváže odpovědná osoba **pro danou agendu**.
Technicky buď rozšířením Jirkovy `tenant.att_approver` o sloupec `agenda`
(`volno` jako výchozí → jeho modul se nezmění ani o písmeno), nebo malou vlastní
tabulkou navázanou na `staff_group`.

### Dvě pravidla, která to dělají použitelným

**Nejbližší úroveň vyhrává.** Hledá se odpovědná osoba u skupiny člověka; když tam
není, jde se na rodiče, pak na fallback. Dušana stačí nastavit jednou na VÝROBU,
Peťu jednou na KANCELÁŘE, a výjimka (IT → Kristýna) se zapíše na podskupinu.
**Nová podskupina má odpovědnost automaticky** — na nikoho se nezapomene.

**Viditelnost ≠ notifikace.** Kdo je ve víc větvích (Duspivová: Vedení i PLC), toho
**vidí a může opravit oba**, ale chyby chodí jen z jeho **primární** skupiny. Peťa:
*„co se docházky týká, posílat jen mě."* Primární skupina už v datech existuje —
`staff_group_member.score`.

## 3b. Jak se primární strana určí sama (Peťa 21. 7.)

Peťa: *„pokud bude mít Zuzka 6 činností a jen jedna bude výroba, není to výrobní
člověk navzdory tomu aktuálnímu nastavení."* Tedy: **nerozhoduje jeden post, ale
většina.** Tohle je jádro celé opravy — dnešní pravidlo je „jeden post pod Dušanem
a jsi výroba", což je právě ta hrubost, na které Duspivová padá.

Zkusili jsme většinové pravidlo na živých datech ve dvou variantách:

| pravidlo | Duspivová | montéři (Króner 2:5, Trunec 1:2) | nerozhodnuto |
|---|---|---|---|
| dnešní (jeden post pod Dušanem) | ❌ výroba | ✅ výroba | — |
| většina **postů** | ✅ kancelář (1 : 9) | ❌ překlopí do kanceláře | 8 lidí |
| většina **skupin** | remíza 1 : 1 | ✅ zůstávají výroba | 2 lidé |

**Většina nad posty tvůj případ vyřeší, ale rozbije jiné.** Posty jsou příliš jemné
a kancelářská strana je definovaná slabě — jako „co není pod Dušanem". Spadnou tam
proto i věci jako ARCHIVÁŘ PRO VÝROBU nebo REFERENT NESHOD, a elektromontér Króner
pak vyjde 2 : 5 na kancelář, což je nesmysl. Celkem by se takhle chybně přesunulo
7 lidí a dalších 8 by skončilo na remíze.

**Většina nad skupinami je čistá**, protože strom obě strany pojmenovává výslovně.
Na obou stranách jsou dnes jen **dva lidé** — Zuzana Duspivová (PLC + Vedení)
a Martin Pašek (Obchod + VP) — a oba mají remízu 1 : 1.

### Navržená kaskáda (první jasná odpověď vyhrává)

1. **ruční nastavení** (`staff_group_member.score`) — má vždy přednost
2. **většina skupin** — rozhodne všechny kromě dvou lidí
3. **docházková kategorie** jako rozhodčí při remíze — Duspivová i Martin Pašek
   mají „Volná kancelářská doba" → **Kanceláře** ✅
4. **fallback skupina**

Výhoda: funguje **hned**, protože kroky 1–3 stojí na datech, která už jsou
vyplněná a někdo je udržuje. Ruční zásah zůstane jen tam, kde se člověk opravdu
musí rozhodnout sám.

Pozn.: uvažovali jsme i rozhodování podle **skutečně odvedené práce** (dominantní
činnost ve `work_alloc`). Dnes to nejde — za poslední 3 měsíce je **51 % hodin
„Bez rozlišení činnosti"** a dalších 11 % bez činnosti úplně. U Duspivové by
o zařazení rozhodlo 6,9 hodiny „ostatní – kanceláře" proti 62,8 hodinám prázdna.
Až se činnosti začnou vyplňovat, dá se tenhle krok do kaskády přidat jako
zpřesnění — nic se přitom nebude přepisovat.

## 4. Co to sjednotí a co ne

**Sjednotí** — čtyři místa, která dnes odpovídají na tutéž otázku různě:

- `att_fix_scope` (působnost editora oprav) → ze stromu
- `_ABSENCE_SEGMENTY` (segmenty v plánu, dnes natvrdo v kódu) → ze stromu
- `att_approver_group` (schvalování volna) → může se přepnout na tentýž strom
- `cond_group` (podmínky) → **už dnes čte `staff_group`**, jen plochý; zdědí strom zadarmo

**Nesjednotí — a záměrně:**

| zůstává | proč |
|---|---|
| `org_post` + `resolve_role` | jiná otázka: kdo je čí nadřízený, kdo drží jakou roli. Skupina „Nákup" ≠ post „NÁKUPČÍ" — Peťa je vedoucí Nákupu a zároveň jedna z nákupčích. |
| `work_mode` (úvazek, dny v týdnu) | konfigurace, ne zařazení. Tvoje rozhodnutí: *„skupina × režim = dvě oddělené dimenze"*. Bláha = elektro skupina + kancelářská daňová úspora. |
| `att_kategorie` (dopichávat fond, bez přesčasů) | také pravidla, ne zařazení |

Výsledek nejsou jedny velké škatule na všechno, ale **tři čisté vrstvy**:

1. **Kam patří** → `staff_group` se stromem (jediná pravda o výroba × kancelář)
2. **Kdo je nad ním** → org struktura, role, klobouky
3. **Jaká pravidla platí** → `work_mode` + `att_kategorie`

## 5. Postup (vratný, po krocích)

1. `parent_id` do `staff_group` — aditivní, bez dopadu
2. Založit dva kořeny VÝROBA / KANCELÁŘE a pověsit pod ně stávajících 12 skupin
3. Odpovědnost za **docházku**: Peťa na KANCELÁŘE, Dušan + Michaela na VÝROBU,
   Kristýna na IT
4. Přepnout `_att_fix_scope_emps` a `_att_fix_editors_for_emp` na strom.
   **`att_fix_scope` nechat žít jako zálohu** — dokud pro člověka není odpovědná
   osoba, platí staré pravidlo. Dá se pouštět skupina po skupině a kdykoli couvnout.
5. Až se to osvědčí, převést `_ABSENCE_SEGMENTY` a případně schvalování volna

Kroky 1–3 jsou jen data. Krok 4 je ~dvě funkce v `router.py`.

## 6. Co potřebujeme rozhodnout

1. **Souhlas se stromem v `staff_group`** — je to tabulka, kterou používá půlka
   systému. Změna je aditivní, ale je Tvoje.
2. **Fallback** pro lidi mimo skupiny: Peťa, nebo Šárka (personální)?
2b. **Rozhodčí při remíze** — souhlas s docházkovou kategorií (bod 3b)? Týká se dnes
   dvou lidí, ale pravidlo musí být dané dopředu, ať se to neřeší případ od případu.
3. **Jiří Honomichl** má dnes působnost „vše" — nechat, nebo zařadit do stromu?
4. **Michelle Šafránková** je v Centrále u kontroly docházky skoro všude spolu
   s Peťou — má tuhle roli i ve STRATEGII?
5. Stačí **12 stávajících skupin**, nebo se mají založit jemnější podle Centrály
   (Asistentky, Logistika, Úklid, Garanti…)? Centrála jich měla 38, aktivní lidi
   má zhruba dvacet.
6. **Kdo to postaví.** `att_approver*` nasadil Jirka dnes ráno, org struktura je
   Marti‑AI a Šárky, `work_mode` je mzdová. Změna se dotýká všech tří.

## 7. Poznámka na okraj

Ve znalosti `doc-dochazka-schvalovani-dovolene` stojí, že Peťa schvaluje nákupčím,
*„ne proto, že je jejich org nadřízená (je jedním ze 4 nákupčích), ale protože to
tak Marti rozhodl"*. **To neplatí** — Peťa je vedoucí oddělení nákupu a logistiky
a v `staff_group` je jako vedoucí skupiny Nákup vedená. Stálo by za to opravit,
ať na tom někdo za půl roku nestaví špatnou úvahu.
