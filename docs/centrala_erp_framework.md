# Centrála 1 — ERP Framework EUROSOFT

> **Účel dokumentu**: knowledge transfer od Marti k Claude+Marti-AI o tom,
> jak funguje legacy ERP framework EUROSOFTu (Centrála 1, Delphi+MS-SQL,
> v provozu od 2007) — aby Marti-AI mohla **rozumět doméně**, ne jen
> *„fetchovat data z SQL"*. Living dokument, paralelní k
> `docs/strategie_erp.md` (vize Centrála 2).
>
> **Cíl**: Phase 13/15/19b/27h pattern — konzolidace zápisů → RAG ingest →
> `composer.py` memory rule #21 (ERP framework awareness) → konzultace
> s Marti-AI před nasazením.
>
> **Status**: 5. 5. 2026 ráno — first session, otevřená konzultace.

---

## 1. Kontextový rámec

**Centrála 1** je vlastní ERP framework EUROSOFTu, který Marti rozjížděl
v době, kdy **Helios Orange (inuvio)** ještě neměl *„Uživatelské editory"*.
Tj. Centrála byla v jednom konkrétním ohledu **dál než Helios** — měla
už uživatelsky konfigurovatelné přehledy a detaily nad libovolným SELECT
dotazem.

Dnes Centrála 1 + Helios běží **paralelně** nad **stejnou DB_EC**:

- **Helios tabulky** (`Tab*`) — standardní business data: `TabObdobi`,
  `TabCisZam`, `TabCisOrg`, `TabZakazka`, `TabDokladyZbozi`,
  `TabPohybyZbozi`, … kde Helios pokrýval doménu, používáme jeho data.
- **EUROSOFT-specifické tabulky** (`EC_*`) — co Helios nepokryl:
  `EC_Ukoly`, `EC_Dochazka`, `EC_Kontakt` rodina, `EC_KontaktAkce` (kampaň
  logging), …

> **Princip**: *„Kde to šlo, jsou data v Helios tabulkách. Kde to nešlo,
> jsou v našich."* — Marti, 5. 5. 2026 ráno

To znamená, že Marti-AI při dotazu *„kolik máme zaměstnanců?"* sahá do
**`TabCisZam` (Helios)**, při dotazu *„kolik kontaktů v PLC?"* do
**`EC_Kontakt` (EUROSOFT)**. **Mentální model je jeden** (ERP doména),
ale fyzická realita má **dva původci** (Helios firma + EUROSOFT in-house).

## 2. UX metafora — třívrstvý layout

Centrála 1 (a paralelně Helios) má klasický **three-pane** ERP layout:

```
┌──────────────┬───────────────────────────────────────┐
│              │  PRAVÝ PŘEHLED                        │
│  LEVÝ STROM  │  (tabulka výsledků jednoho SELECTu)   │
│              │                                       │
│  • Modul A   │  ┌────────────────────────────────┐   │
│   ├ Soudeček │  │ ID │ Datum │ Firma │ Stav │ … │   │
│   │ ├ podsouč│  ├────┼───────┼───────┼──────┼───┤   │
│   │ └ …      │  │ 12 │ 2026… │ ABB … │ open │ … │   │
│   └ …        │  │ 13 │ 2026… │ ČEZ…  │ open │ … │   │
│  • Modul B   │  └────────────────────────────────┘   │
│   ├ …        │                                       │
│              ├───────────────────────────────────────┤
│              │  JÁDRO (detail vybrané věty)          │
│              │  Editovatelný formulář / tabs / …     │
└──────────────┴───────────────────────────────────────┘
```

### 2.1 Levý strom — `EC_CentralaMenu`

Hierarchická navigace — **modulární seznam soudečků**. Kliknutí na
soudeček aktivuje pravý přehled.

> Tabulka: **`EC_CentralaMenu`** (potvrzeno 5.5.2026 ráno — Marti's
> korekce, ne `EC_TabStrom`!)

#### Známé schema (z screenshotu Definice soudečků menu stromu, přehled #102)

```sql
EC_CentralaMenu (
  ID,                    -- PK
  Sys,                   -- system flag (framework/admin vs business)
  Cislo,                 -- business identifier (NULL = ?)
  MenuText,              -- display text v stromě
  NadrazeneMenu,         -- FK self-recursive (parent menu, NULL = top-level)
  Ikona,                 -- icon name/ID
  CisloDef,              -- vazba na EC_DELPHI_TabObecnyPrehled (= číslo přehledu)
  CisloVyjimky,          -- alternativní/override číslo (per-role variant?)
  Poradi,                -- sort order
  Oblibene,              -- favorite flag (per user state)
  CisloZam,              -- FK na zaměstnance (per-user state owner)
  NaposledyPouzite,      -- recently used timestamp/flag (per user)
  Verejne,               -- public/private (sdílené vs. private per CisloZam)
  Hint,                  -- tooltip text
  Offline,               -- availability v offline mode
  Autor,                 -- created by
  DatPorizeni,           -- created at
  Zmenil,                -- modified by
  DatZmeny               -- modified at
)
```

#### Klíčové insighty

1. **Rekurze** potvrzena přes `NadrazeneMenu` (self-FK). Top-level
   soudečky (Vývoj SW, Oběh zboží, Zaměstnanci, Systém, Úkolník,
   Poznámky k verzím Centrály) mají `NadrazeneMenu IS NULL`.

2. **Vazba strom → přehled je v stromu samém** přes `CisloDef`! Tj.
   **NE separátní mapping tabulka** mezi stromem a přehledem (jak jsem
   původně hádal). Soudeček říká *„moje obsahem je přehled #X"* přes
   `EC_CentralaMenu.CisloDef → EC_DELPHI_TabObecnyPrehled.Cislo` (nebo ID,
   Marti potvrdí).

3. **`CisloVyjimky`** — možná *„alternative přehled pro speciální
   případy"* (per-role override, per-context, …). Marti vysvětlí.

4. **Per-user state v stromu samém** — `CisloZam`, `Oblibene`,
   `NaposledyPouzite`. To znamená že **strom v UI je dynamický per
   user** — Pavel Zeman vidí jiný *„🏠 Home"* než Petr Dvořák, podle
   svých `Oblibene` a `NaposledyPouzite` flagů. Ikony 🏠❤️🔘💡 v
   bottom-left toolbar (z prvního screenshotu) přepínají view stromu:
   - 🏠 Home = `WHERE Verejne=1 AND CisloZam IS NULL` (sdílený strom)
   - ❤️ Oblíbené = `WHERE CisloZam=<me> AND Oblibene=1`
   - 🔘 Recent = `WHERE CisloZam=<me> ORDER BY NaposledyPouzite DESC`
   - 💡 (?)

5. **Audit trail** komplet — Autor, DatPorizeni, Zmenil, DatZmeny.

6. **Offline mode** — Centrála má offline-aware soudečky (status bar
   *„Offline mode: 0"* z prvního screenshotu). Marti-AI na cloud APP
   v offline režimu ji asi nevyužije, ale je důležité vědět.

#### Doplňující otázky 1.x

**Q1.1.** Filter `WHERE (Cislo IS NULL)` v přehledu #102 — proč? Co je
*„soudeček s Cislo NOT NULL"* vs *„NULL"*? Je to per-tenant /
per-instance variant?

**Q1.2.** Vazba `CisloDef` → `EC_DELPHI_TabObecnyPrehled` — je to FK na
`Cislo` (business ID) nebo na `ID` (technický PK)?

**Q1.3.** Per-user state — máš pro Pavla Zemana **vlastní řádky v
`EC_CentralaMenu`** (s `CisloZam=PZeman`), nebo se per-user state
zapisuje jako **override záznam** stejného soudečku? Nebo je per-user
state v separátní tabulce (`EC_CentralaMenu_UserState`)?

**Q1.4.** **Globální vs. per-user** — `Verejne=1 AND CisloZam IS NULL`
= shared template. `Verejne=0 AND CisloZam=<me>` = private user-level
soudeček. Je to tak? A zděděný hierarchií (parent veřejný, child
privátní)?

**Q1.5.** **`CisloVyjimky`** — co to je? Příklad use case.

---

### Reálný příklad jádra — *„Nastavení soudečku"* (5.5. ráno)

Marti poslal screenshot reálné edit dialog Centrály (jádro pro editaci
řádku v `EC_CentralaMenu`, konkrétně ID=14 = soudeček *„Definice SQL
pro přehledy"*).

#### Vidím v UI

```
TForm "Nastavení soudečku"
├ Akce menu (top)
│
├ TGroupBox "Vzhled a název soudečku"
│  ├ TLabel "ID" + TEdit value="14" (readonly, gray bg)
│  ├ TLabel "Název soudečku menu" + TEdit value="Definice SQL pro přehledy"
│  ├ TLabel "Ikona" + TEdit value="2" (numeric)
│  └ TLabel "Pořadí" + TEdit value="6" (numeric)
│
├ TGroupBox "Nadřazené menu"   (= NadrazeneMenu FK lookup)
│  ├ TLabel "ID" + TEdit value="11" (readonly — lookup output)
│  └ TLabel "Název soudečku menu" + TLookupCombo value="Systém" (▼)
│
├ TGroupBox "Přehled"           (= CisloDef FK lookup)
│  ├ TLabel "Číslo" + TEdit value="103" (readonly — lookup output)
│  └ TLabel "Název definice přehledu" + TLookupCombo value="Definice SQL" (▼)
│
├ TCheckBox "Požadovat přihlášení"        (= sloupec Pozadovat_prihlaseni?)
├ TCheckBox "Viditelné v OFFLINE módu"    (= sloupec Offline)
│
├ TLabel "Číslo výjimky" + TEdit value=""        (= CisloVyjimky)
├ TLabel "Alternativní text sloužící k URL odkazům"
│        + TEdit value=""                         (= AlternativniText? nový?)
│
└ Bottom row:
    ├ TButton "Nový soudeček"            (cross-create akce)
    ├ TButton "Nastavení práv soudečků"  (cross-navigation na jiné jádro)
    ├ TButton "OK"                       (save → UpdateSQL)
    └ TButton "Storno"                   (cancel)
```

#### Architectural patterns z toho

1. **GroupBox = sekce formuláře** — Centrála používá `TGroupBox` jako
   visual grouping. Modern equivalent: `<fieldset>` nebo `<div class="card">`
   s legend / heading.

2. **Lookup pattern (2-field bound)** — `NadrazeneMenu` a `CisloDef` jsou
   FK lookupy. UI zobrazuje **dvě pole**:
   - **Readonly ID** (`14`, `11`, `103`) = technický klíč
   - **Display Nazev** (`Systém`, `Definice SQL`) = čitelný text + ▼ button

   User klikne ▼ → modal dialog s child přehledem (z `EC_DELPHI_TabObecnyPrehled`).
   Po výběru se obě pole vyplní synchronizovaně. To je **2-field bound
   lookup component** v Delphi VCL.

   Modern web equivalent: kombobox s autocomplete + sidebar vyhledávání,
   nebo modal picker (Tabulator-like). Marti-AI to musí umět renderovat.

3. **Cross-navigation buttony** — *„Nastavení práv soudečků"* otevře
   **jiné jádro** (jiný `EC_FormDef`) pro úpravu práv toho samého řádku.
   Tj. Centrála **řetězí jádra**: `EC_CentralaMenu` row → otevři
   detail soudečku → button *„nastavení práv"* → otevře `EC_FormDef`
   pro práva → po OK návrat do původního jádra.

   Modern web: tabs uvnitř detail panelu, nebo sidebar drill-down,
   nebo modal-on-modal stack.

4. **Schema je dynamický** — formulář ukazuje **víc polí**, než přehled
   #102 dumpuje. *„Alternativní text sloužící k URL odkazům"* a
   *„Požadovat přihlášení"* checkbox nebyly v původním SELECT dumpu.
   To znamená, že **Centrála čte schema z `EC_FormDefEdit` table** a
   renderuje komponenty dynamicky, ne podle DefView resultsetu.

   **Důsledek pro Marti-AI**: pro modernizaci jádra musí Marti-AI
   číst `EC_FormDefEdit` + `EC_FormDefEditProperty` (= layout + binding),
   ne odvozovat formulář z DefView SELECTu. DefView dává **data**,
   FormDefEdit dává **formulář**.

5. **Akce menu (top)** — pravděpodobně další dynamické akce specifické
   pro toto jádro (export, tisk, audit log řádku, …). Z `EC_*DynAkce*`
   tabulky.

#### Vazba potvrzená

```
EC_CentralaMenu.CisloDef → EC_DELPHI_TabObecnyPrehled.Cislo
                                  (ne ID! Cislo=103 v obou tabulkách)
```

Soudeček ID=14 (`MenuText='Definice SQL pro přehledy'`) má
`CisloDef=103`, který odpovídá `EC_DELPHI_TabObecnyPrehled.Cislo=103`
(`Nazev='Definice SQL'`). Tj. **`CisloDef` je FK na business
identifier `Cislo`, ne na technický `ID`**.

To je důležité — `CisloDef` má semantic meaning (číslo přehledu, které
admin v Delphi GUI píše ručně), ne random PK. Přesně jako Helios pattern
(business numbers stable across migrations).

#### Nová pole v schématu (rozšíření)

Schema `EC_CentralaMenu` v query #102 nelistovalo:
- **`Pozadovat_prihlaseni`** (bool) — vyžaduje login pro tento soudeček
  (offline access blocked)
- **`AlternativniText`** (varchar) — text pro URL deep linking
  (např. `/centrala/system/definice-sql-prehledy`)

Marti pravděpodobně časem schema rozšířil, ale `EC_DELPHI_TabObecnyPrehled.DefView`
pro přehled #102 nezahrnuje nové sloupce. To je **schema drift** —
stará SQL definice neukazuje nové sloupce. Marti-AI by měla pro
modernizaci používat **`eurosoft_describe_table('EC_CentralaMenu')`**
(z aktuálního DB), ne RAG schema cache.

#### Doplňující otázky

**Q8c.7.** Pošli `EXEC sp_columns 'EC_CentralaMenu'` — chci aktuální
úplné schema (všechny sloupce, ne jen DefView #102).

**Q8c.8.** Pro toto jádro *„Nastavení soudečku"* — jaké je `EC_FormDef.ID`?
Pošli:

```sql
-- Najdi jádro, které edituje EC_CentralaMenu řádky
SELECT TOP 5 ID, Nazev, LEFT(DefView, 300) AS DefView_preview
FROM EC_FormDef
WHERE Nazev LIKE '%soudeček%' OR Nazev LIKE '%soudečk%'
   OR DefView LIKE '%EC_CentralaMenu%';

-- Pak vezmi ID a dump komponenty:
SELECT C.ID, C.Typ, C.cCaption FROM EC_FormDefEdit C
WHERE C.ID_Form = <ID> AND C.Smazana = 0 ORDER BY C.ID;
```

To mi ukáže reálný **mapping** mezi UI groupboxy/labely/inputs a
`EC_FormDefEdit.Typ` + `cCaption` hodnotami. Po porovnání budu vědět,
jak Centrála pojmenovává typy komponent (TGroupBox? TFormGroup?
TPanelTypN?) a jak rozkládá hierarchii.

**Q8c.9.** **Komponenta TGroupBox** — má v `EC_FormDefEditProperty`
seznam child komponent (přes `ID_Parent`?), nebo je hierarchie
implicitní (komponenty mezi GroupBox#1 a GroupBox#2 patří do GroupBox#1)?

---

### Schema `EC_FormDef` viditelné (5.5. ráno SSMS query)

Marti pustil v SSMS:
```sql
SELECT TOP 10 * FROM EC_FormDef
WHERE Nazev LIKE '%soudeček%' OR Nazev LIKE '%soudečk%'
```

Z column headers + first row vidím **schema `EC_FormDef`**:

```sql
EC_FormDef (
  ID,                     -- PK (int)
  Nazev,                  -- název jádra (nvarchar)
  IDNadrazene,            -- FK self na rodičovský EC_FormDef.ID? (NULL = top-level)
  SQL_Select,             -- ⭐ DefView v Marti's terminologii
                          --    parametrizovaný SELECT s :ID placeholder
                          --    (Delphi-style param binding)
  ParentName,             -- ? (vždy NULL v sample, asi vestigial)
  fTop, fLeft,            -- window position v px (Delphi modal coords)
  fHeight, fWidth,        -- window size v px
  Autor,                  -- created by (user shortname: Matej, Jiri, MSik, Kristyna)
  DatPorizeni,            -- created at (datetime)
  Zmenil,                 -- modified by
  DatZmeny,               -- modified at
  EditModeCondition,      -- condition pro edit mode toggle? (varchar, sample empty)
  ...                     -- 3 unnamed sloupce (sample: 1, NULL, 0/1)
                          -- pravděpodobně Smazana / IsSystem / IsDefault
)
```

#### `SQL_Select` patterns (z 9 sample řádků)

Marti's search vrátil 9 jader, která mají `EC_DELPHI_UzivPrava` /
`EC_VazbyDokNaSoudecek` / `EC_Skupiny` / `EC_Ukoly` v SQL_Select.
Patterns:

**1. Standard single-row load:**
```sql
SELECT * FROM EC_DELPHI_UzivPrava WHERE ID = :ID    -- jádro 87
SELECT * FROM EC_VazbyDokNaSoudecek WHERE ID = :ID  -- jádra 117, 146
select * from EC_Skupiny where id = :id             -- jádro 410
```

**2. Dummy SQL (jádro bez vlastních dat — jen actions / legend / panel):**
```sql
select top 1 id from EC_Ukoly                          -- jádro 1233
select top 1 1 from EC_Ukoly                           -- jádro 1243
                                                       -- + komentář:
                                                       -- „tabulka nemá vůbec
                                                       -- význam pro jádro --
                                                       -- jádro slouží k
                                                       -- zobrazení legendy
                                                       -- barev u přehledu"
```

**3. Parametrizovaný DECLARE:**
```sql
DECLARE @ID int = :ID    SELECT @ID as ID             -- jádro 1269
```

**4. Numeric-only:**
```sql
1696   -- jádro 406 ("Výběr uživatele pro přenos práv")
3677   -- jádro 695 ("ITPozadavky")
```
Číselné `SQL_Select` jsou **odkazy na jiný EC_FormDef.ID** (sub-form
embed?). Tj. ne SELECT, ale FK reference na jiný formulář, který se má
embed-ovat?

**Klíčový insight pro Marti-AI rendering:**
- **Před spuštěním `SQL_Select`** Marti-AI musí **substituovat
  `:ID`** za skutečnou hodnotu (= ID currently selected row v přehledu).
- **Pokud `SQL_Select` vypadá jako dummy** (`SELECT TOP 1 ...`),
  výstup **nepoužít** — jádro slouží jen k UI rámci pro actions,
  data nejsou potřeba. (Marti-AI pozná dummy podle absentu `:ID`
  nebo podle čistého konstantního SELECTu.)
- **Pokud `SQL_Select` je číslo** (např. `3677`), je to FK na jiné
  jádro — load to. (Marti vysvětlí pattern.)

#### Window position pattern (`fTop`, `fLeft`, `fHeight`, `fWidth`)

```
ID=87:    282 × 493     (small dialog)
ID=117:   518 × 656     (medium)
ID=410:   800 × 1100    (large)
ID=695:  1048 × 1936    (very large — multi-monitor?)
ID=1233: 1048 × 1936    (very large)
ID=1269:  479 ×  978
```

Negative coords (`-227`, `-1348`, `-1928`) — pravděpodobně **off-screen
pre-position** (Delphi standard pro spawn invisible) nebo
**multi-monitor** (Marti's setup ze screenshotu má negativní X coords
běžně).

**Pro modernizaci:** moderní web responsive nemá fixed pixel position.
Marti-AI může:
- **Ignorovat** `fTop/fLeft` (browser zabere fullscreen / use Tailwind responsive)
- **Použít** `fHeight × fWidth` jako **hint pro layout** (1048×1936 = velké jádro → multi-pane / sidebar / tabs / stack vertically; 282×493 = malé → simple modal)
- Nebo **odvodit z component count** (víc komponent → větší layout)

#### Vazba potvrzena

Z prvního screenshotu (přehled #103, *„Definice SQL"*) jsem viděl:
> řádek `Cislo=12 Nazev='Definice práv soudečků' ID_Edit=87`

A tady vidím:
> jádro `EC_FormDef.ID=87 Nazev='Definice práv soudečků - edit'
> SQL_Select='SELECT * FROM EC_DELPHI_UzivPrava WHERE ID = :ID'`

Tj. **`EC_DELPHI_TabObecnyPrehled.ID_Edit (FK) → EC_FormDef.ID`** **potvrzeno**.

#### Marti's search nenašel jádro pro `EC_CentralaMenu` → potřebujeme jinou query

Marti's WHERE pattern: `Nazev LIKE '%soudeček%' OR Nazev LIKE '%soudečk%'`
vrátil 9 jader, ale **žádné** se SQL_Select obsahujícím
`EC_CentralaMenu`. Tj. *„Nastavení soudečku"* dialog (předchozí screenshot)
má jádro pojmenované jinak (možná *„Nastavení menu"*, *„Editace
soudečku menu"*, nebo bez slova *„soudeček"*).

**Q8c.10**: Zkus širší search:
```sql
SELECT TOP 10 ID, Nazev, LEFT(SQL_Select, 200) AS SQL_preview
FROM EC_FormDef
WHERE SQL_Select LIKE '%EC_CentralaMenu%';
```

Toto najde **všechna jádra, která dotazují EC_CentralaMenu** — zde bude
i to *„Nastavení soudečku"*.

#### `EC_CentralaMenuUziv` — per-user override tabulka (Q1.3 vyřešena)

V Object Exploreru SSMS Marti vidím tabulky:
- `dbo.EC_CentralaMenu` — globální definice stromu
- `dbo.EC_CentralaMenuUziv` — **per-user override** (suffix `Uziv` =
  *„Uživatelská"*)

Tj. **per-user state (Oblibene, NaposledyPouzite, …) je v separátní
tabulce**, ne v `EC_CentralaMenu` samé. Q1.3 odpověď: **separátní
tabulka**.

**Q1.3.1**: Schema `EC_CentralaMenuUziv` — pošli `EXEC sp_columns
'EC_CentralaMenuUziv'` + sample 5 řádků pro jeden user (např.
`WHERE CisloZam=<Marti>`).

#### Další tabulky DB_EC viditelné v Object Exploreru (audit)

```
EC_Archiv*           → archivní storage
EC_AsynchProceduryStatus  → async job tracking (background workers?)
EC_AutZpr*           → autoresponder (Marti-AI before Marti-AI?)
EC_Banka_*           → bank reconciliation
EC_BrigadniciSeznam  → seznam brigádníků
EC_CarovKody         → barcodes
EC_CashFlow          → cash flow
EC_CenaMedi          → ceník (variant?)
EC_CenikyXxx         → ceníky (multiple varianty)
EC_CestovniPrikazy   → travel orders
EC_CiselnaRada       → number sequences (invoice numbers, ...)
EC_ConnectionLog     → audit log connections
EC_3Dtisk_*          → 3D printing module
EC_FormDef           → jádro (potvrzeno)
EC_FormDefEdit       → komponenta (potvrzeno)
EC_FormDefEditProperty → property komponenty (potvrzeno)
EC_FormDefComponent  → legacy (potvrzeno)
EC_DELPHI_UzivPrava  → user permissions
EC_VazbyDokNaSoudecek → vazby dokladů na soudeček
EC_Skupiny           → skupiny pro permissions
EC_DELPHI_TabObecnyPrehled  → přehled (potvrzeno)
EC_CentralaMenu      → strom (potvrzeno)
EC_CentralaMenuUziv  → strom per-user override
```

Plus mystery: `dbo.bpr`, `dbo.AAA_TabDokladyZbozi_DEL`,
`dbo.AAA_TabPohybyZbozi_DEL` (= soft delete archive of Helios `Tab*`
tables?), `dbo.AA_TestSQLbackup`.

To je velký breadth — DB_EC obsahuje **business + framework + metadata
+ audit + Helios mirror**. Marti-AI by měla mít v RAGu **mapu modulů**:
co je v které sadě tabulek.

**Q15.1**: Kompletní top-level mapping modulů → sady tabulek. Např.:
- CRM module → `EC_Kontakt*`
- Úkoly → `EC_Ukoly*`
- 3D tisk → `EC_3Dtisk_*`
- Banka → `EC_Banka_*`
- Ceníky → `EC_Ceniky*`
- Cestovky → `EC_CestovniPrikazy*`
- (Z Helios DB:) Doklady, Pohyby zboží, Zaměstnanci, Organizace, …

---

### Pattern potvrzen: jedno jádro = generic editor per typ entity (5.5. ráno)

Marti poslal **druhý screenshot** stejného dialogu *„Nastavení soudečku"*,
ale pro **jiný řádek `EC_CentralaMenu`**:

| Atribut | Screenshot 1 | Screenshot 2 |
|---|---|---|
| ID (edited row) | 14 | **13** |
| Název soudečku | *„Definice SQL pro přehledy"* | *„Definice soudečků menu stromu"* |
| Ikona | 2 | 2 |
| Pořadí | 6 | 1 |
| Nadřazené menu | ID=11 *„Systém"* | ID=11 *„Systém"* |
| Přehled (`CisloDef`) | 103 *„Definice SQL"* | **102** *„Centrála menu strom"* |

#### Insight: 1 jádro per typ entity, ne per řádek

To je **standardní ERP pattern** (Helios stejné):
- `EC_CentralaMenu` má **jedno** `EC_FormDef` (= 1 generic editor pro
  všechny soudečky)
- `EC_DELPHI_TabObecnyPrehled` má **jedno** `EC_FormDef` (= 1 generic editor pro
  všechny přehledy)
- `EC_FormDef` má **jedno** `EC_FormDef` (= 1 editor pro všechna jádra,
  meta-circular)
- `EC_Kontakt` má **jedno** `EC_FormDef` (= 1 editor pro všechny kontakty)

`SQL_Select` jádra dostane **runtime parametr `:ID`**, který je vyplněn z
**vybraného řádku v přehledu**. Tj. user otevře přehled #102 (listuje
`EC_CentralaMenu`), klikne na řádek ID=13, klikne *„Oprava"*. Centrála:

1. Najde `EC_DELPHI_TabObecnyPrehled.Cislo=102` → `ID_Edit=X` (technický PK)
2. Najde `EC_FormDef.ID=X` → `SQL_Select='SELECT * FROM EC_CentralaMenu WHERE ID = :ID'`
3. Nahradí `:ID` za `13`
4. Spustí dotaz, dostane data
5. Renderuje formulář `EC_FormDefEdit + EC_FormDefEditProperty` s
   **data-binding** přes `DataField` property na sloupce výsledku

**Důsledek pro Marti-AI rendering**:
- **Renderer je generic** — jeden algoritmus rendere libovolný `EC_FormDef`
- **Data-binding je per-komponenta** přes `DataField` property → sloupec
  z resultsetu `SQL_Select`
- **Lookup komponenty** (NadrazeneMenu, CisloDef) — jejich `DataField`
  ukazuje na FK sloupec, jejich `LookupTarget` property (ještě nevidím
  schema) ukazuje na child přehled pro select dialog

#### Aktualizovaná Q8c.10 (priorita)

```sql
-- 1. Vezmi ID_Edit pro přehledy 102 a 103 (= EC_CentralaMenu a EC_DELPHI_TabObecnyPrehled)
SELECT ID, Cislo, Nazev, ID_Edit
FROM EC_DELPHI_TabObecnyPrehled
WHERE Cislo IN (102, 103);

-- 2. Najdi obě jádra
SELECT ID, Nazev, LEFT(SQL_Select, 300) AS SQL_preview, fHeight, fWidth
FROM EC_FormDef
WHERE ID IN (<id_edit_102>, <id_edit_103>);

-- 3. Komponenty jednoho z nich (např. EC_CentralaMenu editor)
SELECT C.ID, C.Typ, C.cCaption
FROM EC_FormDefEdit C
WHERE C.ID_Form = <id_edit_102> AND C.Smazana = 0
ORDER BY C.ID;
```

To dá **kompletní 1:1 mapping** mezi UI (2 screenshoty *„Nastavení
soudečku"*) a daty (~15 komponent v `EC_FormDefEdit`):

- TGroupBox *„Vzhled a název soudečku"* + 4 children (ID, Nazev, Ikona, Poradi)
- TGroupBox *„Nadřazené menu"* + 2 children (ID readonly, Nazev lookup)
- TGroupBox *„Přehled"* + 2 children (Cislo readonly, Nazev lookup)
- TCheckBox *„Požadovat přihlášení"*
- TCheckBox *„Viditelné v OFFLINE módu"*
- TEdit *„Číslo výjimky"* (label + edit)
- TEdit *„Alternativní text..."* (label + edit)
- TButton *„Nový soudeček"*
- TButton *„Nastavení práv soudečků"*
- TButton OK
- TButton Storno

**To je seed pro use case 1.** Po tom může Marti-AI vyrobit moderní
HTML mockup tohoto formuláře a porovnat s Centrála screenshotem (přes
`analyze_image_layout`).

---

### Korekce 5.5. ráno — `EC_DELPHI_TabObecnyPrehled` (prefix `EC_DELPHI_*`)

Marti potvrdil přes SSMS dotaz `SELECT * FROM EC_DELPHI_TabObecnyPrehled
WHERE Cislo IN (102, 103)`:

> *„Sorry EC_DELPHI_TabObecnyPrehled."*

Tj. **správný název framework tabulky je `EC_DELPHI_TabObecnyPrehled`**,
ne `EC_TabObecnyPrehled` jak jsem zapisoval.

#### Schema `EC_DELPHI_TabObecnyPrehled` (z screenshotu)

```sql
EC_DELPHI_TabObecnyPrehled (
  ID,             -- PK (int)
  GUID,           -- uniqueidentifier (export/migration tracking)
  Skupina,        -- module/category (např. 'DELPHI' = framework přehled)
  Cislo,          -- business identifier (102, 103, …)
  Nazev,          -- display name
  MaxRecords,     -- max počet řádků (0 = unlimited?), performance hint
  DefView,        -- ⭐ SELECT s embedded comment '--//Číslo přehledu: X\\'
  DefViewSQLite,  -- ⭐ SQLite varianta SQL pro offline mode (Centrála
                  --    má offline! viz Offline=1 v EC_CentralaMenu)
  BeforeOpenSQL,  -- ⭐ pre-open hook (init temp tabulek, parametry, ...)
  InsertSQL,      -- CRUD: vytvoření nové věty
  UpdateSQL,      -- CRUD: oprava věty
  DeleteSQL,      -- CRUD: smazání (např. 'DELETE FROM EC_CentralaMenu WHERE ...')
  ID_Edit,        -- FK na EC_FormDef (jádro pro editaci, off-screen ve sloupcích)
  CopySQL,        -- (předpoklad) clone akce
  RefreshType,    -- (předpoklad)
  RowMem,         -- (předpoklad)
  ...
)
```

**Nová pole vůči mému předchozímu předpokladu:**
- **`GUID`** — pro export/migration tracking (přenos definic mezi
  Centrála instancemi v EUROSOFT vs. cloud).
- **`Skupina`** — module classification. Sample obě řádky mají
  `'DELPHI'` (= framework). Asi business přehledy mají `Skupina='Obchod'`,
  `'Sklad'`, `'CRM'`, atd.
- **`MaxRecords`** — performance cap. `0` v sample = unlimited.
- **`DefViewSQLite`** — alternativní SQL pro offline cache (SQLite
  syntax differs od MS-SQL Server). Tj. Centrála synchronizuje data
  do lokální SQLite a v offline módu používá tento variant SELECT.
  **Zajímavý pattern** — moderní implementace by mohla použít stejný
  princip (PWA + IndexedDB).
- **`BeforeOpenSQL`** — pre-open hook (běží před DefView). Použití:
  init session vars (`SET ROWCOUNT`, `SET DATEFORMAT`), naplnit temp
  tabulku, vyčistit cache. **Marti-AI by měla volat BeforeOpenSQL
  pokud existuje** předtím, než spustí DefView.

#### Naming convention je MIXED

Centrála 1 framework má **dvě naming konvence prefix**:

**Tier 1: `EC_DELPHI_*` (legacy/older)**
- `EC_DELPHI_TabObecnyPrehled` (přehled)
- `EC_DELPHI_UzivPrava` (user permissions)

**Tier 2: `EC_*` (bez DELPHI prefix, modernější)**
- `EC_CentralaMenu` (strom)
- `EC_CentralaMenuUziv` (per-user override)
- `EC_FormDef`, `EC_FormDefEdit`, `EC_FormDefEditProperty` (jádra)
- `EC_FormDefComponent` (legacy)
- `EC_VazbyDokNaSoudecek`, `EC_Skupiny`, `EC_Ukoly`, …

Marti pravděpodobně začal s `EC_DELPHI_*` prefix v 2007 (Centrála 1
launch), pak ho v některých nových tabulkách opustil. **Důsledek pro
Marti-AI**: nepředpokládat konsistentní prefix, **vždy ověřit jméno
skutečným query** (přes `eurosoft_describe_table` nebo SSMS Object
Explorer).

**Aktualizovaná Helios paralela:**

| Komponenta | Centrála 1 |
|---|---|
| Strom modulů | `EC_CentralaMenu` (rekurzivní) |
| Per-user state stromu | `EC_CentralaMenuUziv` (separate table) |
| Definice přehledu | `EC_DELPHI_TabObecnyPrehled` ⭐ s `EC_DELPHI_` prefix |
| Definice jádra | `EC_FormDef` |
| Komponenty jádra | `EC_FormDefEdit` (s ID_Form FK) |
| Property komponent | `EC_FormDefEditProperty` (s ID_FormDefEdit FK) |
| Permissions tabulka | `EC_DELPHI_UzivPrava` ⭐ s `EC_DELPHI_` prefix |
| Group permissions | `EC_Skupiny` |

#### Insight: Bootstrap (meta-circular) pattern

Přehled `Cislo=103 *„Definice SQL"*` má `DeleteSQL='DELETE FROM
EC_DELPHI_TabObecnyPrehled WHERE …'` — tj. **listuje a edituje sám
sebe**.

Stejně jako:
- Přehled `Cislo=102 *„Centrála menu strom"*` listuje `EC_CentralaMenu`
  (= soudečky, mezi nimiž je i tento samotný přehled jako `EC_CentralaMenu`
  řádek)
- Přehled `Cislo=119 *„Definice dotazů pro editaci vět"*` listuje
  `EC_FormDef`
- Přehled `Cislo=4 *„Definované komponenty"*` listuje `EC_FormDefComponent`
  (legacy)
- Přehled `Cislo=157 *„Property komponent jádra"*` listuje
  `EC_FormDefEditProperty` (přes JOIN s F+C)

To je **klasický bootstrap pattern**: framework je sám sebe
self-hosting přes vlastní tabulky. Marti-AI by mohla **stejný princip**
použít v moderní Centrále 2 — konfigurace přehledů + jader uložená
v DB, editovatelná přes Centrála 2 samé.

#### Pro use case 1 — final ID_Edit query

Sloupec `ID_Edit` byl mimo viditelný zoom v screenshotu. Marti, prosím
pošli ještě:

```sql
SELECT ID, Cislo, Nazev, ID_Edit, MaxRecords,
       LEFT(BeforeOpenSQL, 100) AS BeforeOpen_preview
FROM EC_DELPHI_TabObecnyPrehled
WHERE Cislo IN (102, 103);
```

Z toho dostanu **dvě `ID_Edit` hodnoty** (pro EC_CentralaMenu editor a
EC_DELPHI_TabObecnyPrehled editor). Pak najdu obě `EC_FormDef` jádra
+ jejich komponenty.

A jeden bonus pro Marti-AI's RAG ingest: **kompletní seznam Skupin**:

```sql
SELECT Skupina, COUNT(*) AS pocet_prehledu
FROM EC_DELPHI_TabObecnyPrehled
GROUP BY Skupina
ORDER BY pocet_prehledu DESC;
```

Tj. uvidím všechny module categories — `DELPHI` (framework) +
business modules (`Obchod`, `Sklad`, `CRM`, …?). To dá **map modulů**.

---

### Vazby potvrzeny + schema EC_CentralaMenu úplné (5.5. ráno)

Marti pustil dva dotazy:

**1. ID_Edit pro přehled #103:**
```sql
SELECT Cislo, ID_Edit FROM EC_DELPHI_TabObecnyPrehled WHERE ID = 80;
-- vrátil: 103 / 4
```
Tj. **`EC_FormDef.ID=4`** = jádro pro editaci `EC_DELPHI_TabObecnyPrehled`
rows (= dialog *„Nastavení přehledu"*).

**2. Najdi jádra dotazující EC_CentralaMenu:**

| ID | Nazev | SQL_Select preview |
|---|---|---|
| **6** | *„Definice menu - úprava"* | `SELECT [ID], [Cislo], [MenuText], [NadrazeneMenu], [Ikona], [CisloDef], [CisloVyjimky], [Poradi], [Oblibene], [CisloZam], [NaposledyPouzite], [Verejne], [PozadovatPrihlaseni], [Hint], [Offline], [Alias], [Sys] FROM EC_CentralaMenu WHERE ID = :ID` |
| 275 | *„Přehledu popup menu"* | `SELECT * FROM EC_DELPHI_TabObecnyPrehled WHERE ID=:ID` |
| 1171 | *„Přehledu popup menuKopie - Jiri"* | `SELECT * FROM EC_DELPHI_TabObecnyPrehled WHERE ID=:ID` (clone Jiri) |
| 1329 | *„Přehled přehledů - detail, A"* | full outer join EC vs IAP comparison (audit) |

#### Klíčové potvrzení: `EC_FormDef.ID=6` = editor `EC_CentralaMenu`

Dialog *„Nastavení soudečku"* ze 2 screenshotů Marti's výše = jádro
`EC_FormDef.ID=6` *„Definice menu - úprava"*. Tj. mám **finální vazbu**
mezi UI a daty — můžu pokračovat na komponenty (Q8c.10 final).

#### Schema `EC_CentralaMenu` — kompletní (17 sloupců)

Z `SQL_Select` jádra #6:

```sql
EC_CentralaMenu (
  ID,                      -- PK
  Cislo,                   -- business identifier (NULL pro user entries?)
  MenuText,                -- display text v stromě
  NadrazeneMenu,           -- self-FK (parent menu, NULL = top-level)
  Ikona,                   -- icon ID
  CisloDef,                -- FK na EC_DELPHI_TabObecnyPrehled.Cislo (přehled)
  CisloVyjimky,            -- alternativní/override číslo
  Poradi,                  -- sort order
  Oblibene,                -- favorite flag (per-user via CisloZam)
  CisloZam,                -- FK na zaměstnance (per-user state owner)
  NaposledyPouzite,        -- recently used timestamp
  Verejne,                 -- public/private
  PozadovatPrihlaseni,     -- ⭐ require login (auth gate per soudeček)
  Hint,                    -- tooltip
  Offline,                 -- offline mode availability
  Alias,                   -- ⭐ URL alias pro deep linking
                           --    (= "Alternativní text sloužící k URL odkazům")
  Sys                      -- system flag (framework vs business)
)
```

**Mapping UI → schema** ze screenshotu *„Nastavení soudečku"*:

| UI label | Schema sloupec |
|---|---|
| ID (readonly) | `ID` |
| Název soudečku menu | `MenuText` |
| Ikona | `Ikona` |
| Pořadí | `Poradi` |
| Nadřazené menu / Název | `NadrazeneMenu` (lookup) |
| Přehled / Číslo | `CisloDef` (lookup) |
| Požadovat přihlášení (checkbox) | `PozadovatPrihlaseni` ✅ |
| Viditelné v OFFLINE módu (checkbox) | `Offline` |
| Číslo výjimky | `CisloVyjimky` |
| Alternativní text sloužící k URL odkazům | `Alias` ✅ |

**Skryté sloupce** v běžném edit dialogu: `Cislo`, `Hint`, `Oblibene`,
`CisloZam`, `NaposledyPouzite`, `Verejne`, `Sys`. Per-user state
(`Oblibene/CisloZam/NaposledyPouzite`) se nastavuje **přes UI akce**
(klik na ❤️ ikonku stromu), ne přes edit dialog soudečku.

#### Insight: `IAP` = samostatná Centrála instance (jiná DB, ne prefix!)

⚠ **Korekce 5.5. ráno** — Marti opravil mé špatné chápání.
**`IAP_DELPHI_TabObecnyPrehled`** v jádru #1329 **NENÍ** tabulka
s prefixem `IAP_*` v DB_EC. Je to **synonym** (nebo cross-DB reference)
v DB_EC odkazující na **IAP databázi**, kde tabulka má **stejný název
`EC_DELPHI_TabObecnyPrehled`**.

Pravděpodobná implementace:
```sql
-- V DB_EC:
CREATE SYNONYM IAP_DELPHI_TabObecnyPrehled
FOR [IAP].[dbo].[EC_DELPHI_TabObecnyPrehled]
-- Nebo přes linked server:
-- FOR [<server>].[IAP].[dbo].[EC_DELPHI_TabObecnyPrehled]
```

Marti's quote: *„NNNNNNEEEE I v IAP je EC_DELPHI_TabObecnyPrehled neni
tam IAP_******"*. Tj. **stejný název** `EC_DELPHI_TabObecnyPrehled`
v obou databázích, jen synonym v DB_EC nese aliasované jméno
`IAP_DELPHI_TabObecnyPrehled` pro disambiguation v query.

#### Důsledek: Centrála framework je multi-tenant deployed

**Jeden framework = víc organizací**. EUROSOFT (DB_EC) je primary
zákazník Centrály, ale framework běží **paralelně** v IAP databázi
pro jinou organizaci/klienta. Stejné struktury tabulek, jiná data.

Audit jádro #1329 detekuje **schema drift mezi instancemi**:
- Stejné `Cislo` + stejné `Nazev`
- **Různý `DefView`** (= někdo upravil přehled jen v jedné instanci,
  ne v druhé)

To je **zlatý pattern** pro provozování stejné aplikace více klienty.
**Implikace pro Marti-AI a Centrálu 2:**

1. **Multi-tenant je už v Centrále 1 zaintegrovaný** — Marti přemýšlí
   o tom 19 let. Tj. Centrála 2 by měla pokračovat v multi-tenant
   architektuře (per-tenant DB, framework code shared, schema
   migrations koordinované).
2. **Schema drift detection** — Marti-AI by mohla nabídnout audit
   tool *„které přehledy se v IAP liší od EC"*, *„které soudečky
   chybí v IAP"*, *„kdy poslední synchronizace"*.
3. **Cross-instance comparison** je v Centrále už zabudované přes
   synonyms — moderní equivalent: cross-tenant queries v Marti-AI,
   ale s permission checks.

**Q15.2**: Co je `IAP`? Klient EUROSOFT, dceřinka, nebo legacy upgrade
path? Plus jak je IAP DB hostovaná (stejný server, jiný server, linked
server)? Plus kolik tenantů celkem Centrála 1 obsluhuje?

---

### IAP = Intersoft Automation Plzeň (Q15.2 zodpovězena 5.5. ráno)

Marti's vstup:
> *„IAP = Intersoft Automation Plzen = Je to dalsi tenant INTERSOFT.
> Centrala slouzi pro dve firmy EUROSOFT primarne a v roce 2014 jsem
> ji implementoval do INTERSOFT...."*

#### Architektura (Marti's vlastními slovy: *„bastl"*)

> *„Pozor bastl, nejsou ani oddelene tabulky (data) frameworku, ale
> je to plnohodnotna kopie databaze... Jediny co jsme tenkrat vymysleli,
> ze se u nekterych tabulek Frameworku nehadame o IDcka zaznamu, tj.
> EUROSOFT insertuje liche ID a INTERSOFT sude ID... Timto z dnesniho
> pohledu trochu nestastnym bastlem jsme si tenkrat otevreli dvere
> pro ruzne synchrozizace prehledu, jader a tak..."*

**Pattern**:
- **Žádný čistý multi-tenant** (žádný `tenant_id` sloupec, žádné
  shared schema s logical separation)
- **Fork-by-copy v 2014** — celá DB_EC zkopírovaná do nové DB
  Intersoft, oba systémy žijí svým životem
- **ID partitioning** pro vybrané framework tabulky:
  - **EUROSOFT** (DB_EC) → **liché ID** (1, 3, 5, 7, ...)
  - **INTERSOFT** (DB_IAP) → **sudé ID** (2, 4, 6, 8, ...)
  - Eliminace PK conflicts při synchronizaci přehledů a jader napříč
    instancemi (admin v EC vyrobí nový přehled #103 = liché → kopíruje
    do IAP bez kolizí, IAP admin vyrobí #104 = sudé)
- **Drift detection** (jádro #1329) je **provozní nástroj** pro audit
  *„co se v IAP změnilo vůči EC"*

#### Marti's pragmatismus

Marti's slovo *„bastl"* (= hack, ne-elegant) je sebekritické. Ale po
**11 letech provozu** drží. To je důležitější než elegance.

> *„Timto z dnesniho pohledu trochu nestastnym bastlem jsme si tenkrat
> otevreli dvere..."*

Tj. *„hack, který otevřel architektonické možnosti"*. Multi-tenant
synchronizace přehledů a jader **pracovala napříč EC ↔ IAP** přes:
1. ID partitioning → bez PK konfliktů
2. Stejné `EC_*` framework table names v obou DB → kód je univerzální
3. Synonyms / cross-DB queries → audit napříč instancemi

#### Implikace pro Centrálu 2 / Marti-AI

1. **Multi-tenant je v genech projektu** — ne jako čistý design
   z 2007, ale **jako pragmatický fakt z 2014**. Centrála 2 by neměla
   ignorovat tu zkušenost.
2. **GUID jako moderní equivalent** ID partitioningu — schema
   `EC_DELPHI_TabObecnyPrehled.GUID` (viz screenshot výše) je už dnes
   v tabulce. Tj. Marti **už dávno přidal GUID** vedle ID jako přípravu
   na cleaner sync. Centrála 2 by měla **GUID-first** architekturu
   (ID jen interní per-DB, GUID pro cross-instance reference).
3. **Marti-AI's drift audit jako built-in tool** — moderní equivalent
   jádra #1329. *„Marti, koukni na drift mezi EC a IAP přehledy, je
   tam 7 rozdílů…"* — to je **provozní nástroj**, ne jen feature.
4. **Sync patterns** v Centrále 2 — Marti-AI mohla synchronizovat
   změny per-tenant inteligentně (publish do staging, manual review,
   apply do prod IAP). To eliminuje *„udělali jsme změnu v EC, IAP
   o ni neví"* drift.

#### Dnešní reálná situace EUROSOFT ↔ INTERSOFT

- Dvě firmy obsluhované **stejným frameworkem**
- **Dva DB serverů** (pravděpodobně) nebo **jeden server, dvě DB**
- Schema v obou identické (nebo téměř — drift)
- Sync přehledů/jader **manuální** (admin v jedné DB vyrobí, pak
  copy do druhé) nebo **přes synonyms + audit jádro #1329**

**Pro Marti-AI**: pokud bude pracovat s daty napříč EC a IAP,
musí znát **prefix konvence v query** (`IAP_DELPHI_*` synonym v
DB_EC), ne tabulky **per se**. A musí umět rozeznat *„toto je
sync pattern, ne reálný název tabulky"*.

#### Q15.3 (rozšíření — pro Centrálu 2)

- Synchronizace dnes — **manual** (Marti / Jiri / Kristyna kopírují),
  **scripted**, nebo **automated**?
- Plánuje EUROSOFT do budoucna **přidat další tenanty** (klient C, D)?
  Pokud ano, *„bastl"* už nebude škálovat — musí se vyřešit elegantněji.
- Jádro #1329 *„Přehled přehledů - detail, A"* — kdo ho používá?
  (Marti/Jiri/Kristyna jako sysadmin? End user IAP? Audit?)

Pro Marti-AI **dnes není kritické** — ale pokud bude pracovat
v Centrále 2 jako co-architect, **multi-tenant context** je jeden
ze 3-5 fundamentálních principů, které musí znát.

---

### Schema `EC_FormDefEdit` — kompletní (5.5. ráno + komponenty jádra #6)

Marti pustil dva dotazy najednou — komponenty jádra #6 + `sp_columns
EC_FormDefEdit`. **Obrovský průlom** v rozumění frameworku.

#### Komponenty jádra #6 (= dialog *„Nastavení soudečku"*)

```
ID    Typ  cCaption
35    2    Název soudečku menu
36    2    ID
37    2    Číslo
38    2    Ikona
150   2    Pořadí
153   2    Číslo výjimky
457   6    Název definice přehledu
458   6    Název soudečku menu
467   12   Přehled
468   12   Nadřazené menu
469   12   Vzhled a název soudečku
1717  3    NOVÁ
4575  8    NOVÁ
4665  2    NOVÁ
4667  8    NOVÁ
6547  3    NOVÁ
13637 30   NOVÁ
15243 2    NOVÁ
```

**Mapping `Typ` → UI control** (odvozeno z UI screenshot dialogu):

| `Typ` | UI control | cCaption příklady |
|---|---|---|
| **2** | TEdit / TLabeledEdit | „ID", „Název soudečku menu", „Číslo", „Ikona", „Pořadí", „Číslo výjimky", „Alternativní text..." |
| **3** | TButton | „Nový soudeček", „Nastavení práv soudečků" (jako *„NOVÁ"* default) |
| **6** | TLookupComboBox (FK lookup ▼) | „Název definice přehledu", „Název soudečku menu" (parent lookup) |
| **8** | TCheckBox | „Požadovat přihlášení", „Viditelné v OFFLINE módu" (jako *„NOVÁ"*) |
| **12** | TGroupBox (sekce) | „Přehled", „Nadřazené menu", „Vzhled a název soudečku" |
| **30** | ??? (Akce menu? toolbar? combo?) | (1× *„NOVÁ"*) |

⚠ **`cCaption='NOVÁ'`** je default placeholder (`DEFAULT ''` schema, ale
runtime některé inserty nastavují *„NOVÁ"*). **Mapping na UI nelze
dělat jen po caption** — musíme se dívat na (Typ, cFieldName, cParent,
cTop/cLeft).

**Q8c.11**: Pošli mi prosím **číselník `Typ`** — tabulku, která mappuje
INT na string name. Pravděpodobně:

```sql
EXEC sp_columns 'EC_FormDefEditTypCis';  -- pravděpodobně
-- nebo:
SELECT * FROM EC_DELPHI_*Cis*KomponentTyp*;
-- nebo skry v frameworku jako enum v Delphi kódu
```

Bez slovníku nemůžu mapovat Centrála `Typ=30` na konkrétní HTML control
v rendereru.

#### Schema `EC_FormDefEdit` — kompletní (24 sloupců)

```sql
EC_FormDefEdit (
  ID            int           NOT NULL  -- PK přes EC_GET_NewID_2('EC_FormDefEdit')
                                        -- ⭐ Custom ID generator (ID partitioning
                                        --    EC vs IAP — lichá vs sudá!)
  ID_Form       int           NULL      -- FK na EC_FormDef.ID (jádro)
  ID_Prehled    int           NULL      -- ⭐ alternativní FK — komponenta může
                                        --    patřit i přímo přehledu
                                        --    (toolbar buttony, custom column renderers)
  [User]        nvarchar(50)  NULL      -- per-user override?
  Typ           int           NOT NULL  -- ⭐ číselník komponent (2/3/6/8/12/30/...)
                                        --    DEFAULT 2 = TEdit
  cTop          int           NOT NULL  -- pixel position (Delphi style, default 60)
  cLeft         int           NOT NULL  -- (default 60)
  cHeight       int           NOT NULL  -- (default 20)
  cWidth        int           NOT NULL  -- (default 100)
  cFieldName    nvarchar(50)  NOT NULL  -- ⭐ DATA BINDING — sloupec z SQL_Select
                                        --    výsledku, na který se komponenta váže
                                        --    (např. cFieldName='MenuText' →
                                        --     komponenta zobrazuje data.MenuText)
  cFieldDataTyp int           NULL      -- typ dat sloupce (číselník)
  cParent       nvarchar(50)  NULL      -- ⭐ STRING reference na parent komponent
                                        --    (asi cFieldName parenta, ne ID)
  cCaption      nvarchar(50)  NOT NULL  -- display text
  cMask         nvarchar(100) NOT NULL  -- format mask (Delphi style: 00.00.0000
                                        --   pro datum, ###,##0.00 pro money)
  cDirectory    nvarchar(250) NOT NULL  -- pro file picker default path
  Autor         nvarchar(128) NOT NULL  -- created by (suser_sname())
  DatPorizeni   datetime      NOT NULL  -- created at
  Zmenil        nvarchar(128) NULL      -- modified by
  DatZmeny      datetime      NULL      -- modified at
  Smazal        nvarchar(128) NULL      -- soft-deleted by
  Smazana       bit           NOT NULL  -- soft delete flag (default 0)
  Prevedena     bit           NOT NULL  -- ⭐ migration marker z legacy
                                        --    EC_FormDefComponent (default 1)
  FMX           tinyint       NULL      -- ⭐ FireMonkey flag (Delphi cross-platform
                                        --    UI framework, default 1)
  Sys           bit           NOT NULL  -- system component (default 0)
)
```

#### Architektonické insighty (10)

1. **`Typ` je INT číselník**, ne string. **Musíme získat slovník** —
   bez něho nelze mapovat na HTML.
2. **Pixel pozice** (`cTop/cLeft/cHeight/cWidth`) — Delphi-style absolutní
   souřadnice v parentovi. Pro moderní responsive layout musí Marti-AI
   **transformovat na grid** (`grid-template-columns: repeat(12, 1fr)`)
   nebo **ignorovat a použít flow** (block layout s padding).
3. **`cFieldName` = STRING data binding** — sloupec ze `SQL_Select`
   výsledku se napojí na komponentu přes jméno. Schema-flexible (změna
   schema = změna `cFieldName`, žádný compile-time check).
4. **`cParent` = STRING reference** na parent komponentu. To je **NON-typed
   parent reference** — pravděpodobně přes `cFieldName` parenta nebo
   přes dedikované jméno (např. `'GroupBox_VzhledNazev'`).
5. **`ID_Prehled` alternativní rodič** — komponenta nemusí patřit do
   `EC_FormDef` (jádro), ale může patřit i přímo `EC_DELPHI_TabObecnyPrehled`
   (přehled). Použití: toolbar buttony per přehled, custom column
   renderers v gridu, kontextové akce.
6. **`EC_GET_NewID_2('EC_FormDefEdit')`** custom ID generator! **Pravděpodobně
   tady sedí ID partitioning logic** (EC = liché, IAP = sudé). Marti
   to vyrobil jako **per-table funkci** (volá se s názvem tabulky a
   vrací next ID podle tenant kontextu).
7. **`Prevedena=1` default** — migration marker z legacy
   `EC_FormDefComponent` (= *„balast"*). Komponenty s `Prevedena=0` jsou
   originál ze starého schema (nepřevedené). Marti to může v Centrále 2
   audit query *„kolik komponent ještě nemáme převedených?"*.
8. **`FMX=1` default** — FireMonkey (Delphi cross-platform UI framework
   pro mobile + desktop). Marti **plánoval cross-platform port** Centrály.
   Komponenty s `FMX=1` jsou kompatibilní s FireMonkey rendererem,
   `FMX=0` jen VCL Windows.
9. **`cMask`** — Delphi format mask. Příklady:
   - `00.00.0000` → datum
   - `###,##0.00` → money
   - `0000` → fixed-length číslo
   - regex-like ne-Delphi standard
10. **Schema je rich** — 24 sloupců, mnoho meta (audit + soft delete +
    migration + cross-platform flag).

#### `EC_GET_NewID_2` funkce — Q8c.12

To je **klíčová funkce** pro ID partitioning. Pošli mi prosím:

```sql
-- Source kód funkce
SELECT OBJECT_DEFINITION(OBJECT_ID('EC_GET_NewID_2'));
```

Tj. uvidím Marti's logic — pravděpodobně něco jako:

```sql
CREATE FUNCTION EC_GET_NewID_2(@TableName nvarchar(128))
RETURNS int AS BEGIN
  -- Get next ID with parity adjustment
  -- EC = lichá: ((MAX(ID) + 1) | 1)  -- ensure odd
  -- IAP = sudá: ((MAX(ID) + 2) & ~1) -- ensure even
  -- Plus per-table tracking?
END
```

Tahle funkce je **architektonicky kritická** pro pochopení, jak
multi-tenant funguje na úrovni dat.

#### Q8c.13 — komponenty s konkrétními property

Pro 1-2 komponenty z jádra #6 dump property:

```sql
-- TGroupBox "Vzhled a název soudečku" (ID=469, Typ=12)
SELECT P.* FROM EC_FormDefEditProperty P
WHERE P.ID_FormDefEdit = 469 AND P.Smazana = 0;

-- TLookupComboBox "Název definice přehledu" (ID=457, Typ=6)
SELECT P.* FROM EC_FormDefEditProperty P
WHERE P.ID_FormDefEdit = 457 AND P.Smazana = 0;
```

Z toho vidím **jaké property mají různé typy komponent**:
- TGroupBox: visual properties (border, color, font)?
- TLookupComboBox: target přehled (= `LookupCisloDef`?), data field, search policy?

Plus schema property tabulky:

```sql
EXEC sp_columns 'EC_FormDefEditProperty';
```

#### Tj. pro renderer mám teď

Pseudokód renderování pro libovolné jádro:

```python
def render_centrala_jadro(form_def_id: int, row_id: int) -> str:
    # 1. Načti definici jádra
    form = sql("SELECT * FROM EC_FormDef WHERE ID = ?", form_def_id)

    # 2. Pre-execute hook
    if form.BeforeOpenSQL:  # od EC_DELPHI_TabObecnyPrehled, ne EC_FormDef
        execute(form.BeforeOpenSQL)

    # 3. Načti data jednoho řádku
    sql_with_param = form.SQL_Select.replace(":ID", str(row_id))
    data_row = sql(sql_with_param)  # dict {column_name: value}

    # 4. Načti komponenty (filtrovat Smazana=0)
    components = sql("""
        SELECT * FROM EC_FormDefEdit
        WHERE ID_Form = ? AND Smazana = 0
        ORDER BY ID
    """, form_def_id)

    # 5. Pro každou komponentu načti property
    for c in components:
        c.props = sql("""
            SELECT * FROM EC_FormDefEditProperty
            WHERE ID_FormDefEdit = ? AND Smazana = 0
        """, c.ID)

    # 6. Sestavit hierarchii (cParent string ref)
    tree = build_tree_by_cParent(components)

    # 7. Render HTML
    html = []
    for c in tree.roots:  # top-level (cParent IS NULL nebo prázdný)
        html.append(render_component(c, data_row, depth=0))
    return "\n".join(html)


def render_component(c, data_row, depth=0) -> str:
    """Mapuj Typ na HTML."""
    bound_value = data_row.get(c.cFieldName, "")

    if c.Typ == 12:  # TGroupBox
        children_html = "\n".join(
            render_component(child, data_row, depth+1)
            for child in c.children
        )
        return f'''
        <fieldset class="centrala-groupbox">
          <legend>{c.cCaption}</legend>
          {children_html}
        </fieldset>
        '''
    elif c.Typ == 2:  # TEdit
        readonly = c.cFieldName in ("ID",) or c.props.get("readonly")
        return f'''
        <div class="centrala-field">
          <label>{c.cCaption}</label>
          <input type="text"
                 name="{c.cFieldName}"
                 value="{bound_value}"
                 {'readonly' if readonly else ''}>
        </div>
        '''
    elif c.Typ == 6:  # TLookupComboBox
        return render_lookup(c, bound_value)
    elif c.Typ == 3:  # TButton
        return f'''
        <button class="centrala-btn"
                onclick="centralaAction('{c.cFieldName}')">
          {c.cCaption}
        </button>
        '''
    elif c.Typ == 8:  # TCheckBox
        checked = "checked" if bound_value else ""
        return f'''
        <label class="centrala-check">
          <input type="checkbox" name="{c.cFieldName}" {checked}>
          {c.cCaption}
        </label>
        '''
    elif c.Typ == 30:  # ??? (Q8c.11)
        return f'<!-- TODO: Typ=30 unknown -->'
    else:
        return f'<!-- TODO: Typ={c.Typ} unknown -->'
```

**To je první draft renderer pipeline pro Marti-AI**. Bez slovníku
`Typ` (Q8c.11) ještě nemůžeme mapovat plně, ale 90 % komponent jádra
#6 je pokryto (Typ 2/3/6/8/12).

---

### Slovník `Typ` (Q8c.11 zodpovězena 5.5. ráno)

Marti pustil dotaz na číselník typů komponent — vrátil **37 řádků** od
2015 do 2025. Tabulka pravděpodobně `EC_FormDefComponentTypCis` nebo
podobně.

#### Schema z dat (kolikolíky)

```
ID, Druh, Typ, Name, Popis, PoradiCreate, Autor, DatPorizeni, Zmenil, DatZmeny, FMX
```

- **`Typ`** = INT key, který se používá v `EC_FormDefEdit.Typ`
- **`Name`** = string identifier (Delphi component class jméno bez `T` prefix)
- **`Druh`** = 0 / 1 — **0 = non-visual / data / config**, **1 = visual UI**
- **`Popis`** = lidsky čitelný popis česky
- **`PoradiCreate`** = order v komponentové paletě při INSERT
- **`FMX`** = FireMonkey kompatibilita (vždy 1 v sample)
- **`Autor`** = kdo komponentu vytvořil (Martin / Matej / OPillar / Jiri)

#### Kompletní tabulka 37 typů

| Typ | Name | Druh | Popis | UI poznámka |
|---|---|---|---|---|
| 1 | **Label** | 1 | Popis | `<label>` |
| 2 | **Edit** | 1 | Zadávací pole | `<input>` |
| 3 | **CheckBox** | 1 | Zaškrtávátko | `<input type="checkbox">` |
| 4 | RichEdit | 1 | Editor textu (RTF) | `<rich text>` |
| 5 | **DateEdit** | 1 | Zadávání datumu | `<input type="date">` |
| 6 | **FormList** | 1 | **Výběr pomocí seznamu (otevírá se celé okno)** | modal picker |
| 7 | Combobox | 1 | Výběr z jednoduchého seznamu | `<select>` |
| 8 | **Button** | 1 | Tlačítko s definovanou funkcí | `<button>` |
| 9 | FileListBox | 1 | Adresář | file picker |
| 10 | TimeEdit | 1 | Zadávání času | `<input type="time">` |
| 11 | Grid | 1 | Grid | `<table>` / DataGrid |
| 12 | **GroupBox** | 1 | Grupovací rámeček | `<fieldset>` |
| 13 | Panel | 1 | Panel | `<div>` container |
| 14 | Splitter | 1 | Splitter | resizable divider |
| 15 | PageControl | 1 | Záložky | tabs container |
| 16 | TabSheet | 1 | TabSheet | individual tab content |
| **17** | **DataSet** | **0** | **DataSet (non-visual)** | data binding host |
| **18** | **DBFieldConstant** | **0** | **Konstanta (non-visual)** | static value provider |
| 19 | DBTreeView | 1 | Tree view | `<ul>` recursive |
| 20 | SpeedButton | 1 | Speed button | toolbar button |
| 21 | GridPolDoklad | 1 | Grid položky dokladu | specialized doc grid |
| 22 | RichEditor | 1 | (legacy?) | newer rich text |
| 23 | DateTimeEdit | 1 | DateTimeEdit | `<input type="datetime-local">` |
| 24 | Chart | 1 | Graf | chart |
| 25 | Rastr | 1 | Slouží k rozdělení plochy na rastr | grid layout |
| 26 | Image | 1 | Obrázek | `<img>` |
| 27 | KvalifTest | 1 | Kvalifikační test | custom business |
| 28 | ListEdit | 1 | Pro výběr více řešitelů do úkolu | multi-select |
| 29 | UkolV1 | 1 | Kompletní komponenta úkolu V1 | composite |
| **30** | **FormSetting** | **0** | **Nastavení dynamického formu (non-visual)** | form-level config |
| 31 | Planner | 1 | Plánovač | calendar/scheduler |
| 32 | InputList | 1 | Zadávání uživatelů/zakázek/čehokoli | autocomplete list |
| 33 | RichEditorV1 | 1 | Nová verze RichEditoru | richtext v1 |
| 34 | OpakovanyUkol | 1 | Komponenta opakovaného úkolu | recurring task |
| 35 | TextComparator | 1 | Komponenta na porovnávání 2 řetězců | diff view |
| 36 | ModulJadra | 1 | Platforma pro umístění jádra | **embed sub-form!** |
| 37 | Klavesnice | 1 | (Jiri 2025) | virtual keyboard |

#### ⚠ Korekce mojích předchozích guesses

Já jsem hádal **špatně** v Typ=3, 6 a 8. Reálné mapping:

| Typ | Co jsem hádal | Skutečnost |
|---|---|---|
| 3 | TButton ❌ | **CheckBox** ✅ |
| 6 | TLookupComboBox ❌ | **FormList** (modal picker, ne dropdown!) ✅ |
| 8 | TCheckBox ❌ | **Button** ✅ |
| 30 | (toolbar?) ❌ | **FormSetting** (non-visual config) ✅ |

#### Re-mapping komponent jádra #6 — finální

```
ID    Typ  Name         cCaption                       UI element
─── GroupBoxy (visual sections) ──────────────────────────────────
467   12   GroupBox     Přehled                        <fieldset><legend>Přehled</legend>
468   12   GroupBox     Nadřazené menu                 <fieldset><legend>Nadřazené menu</legend>
469   12   GroupBox     Vzhled a název soudečku        <fieldset><legend>Vzhled a název soudečku</legend>

─── Edit pole (text inputs) ───────────────────────────────────────
36    2    Edit         ID                             <input readonly>
35    2    Edit         Název soudečku menu            <input>
38    2    Edit         Ikona                          <input>
150   2    Edit         Pořadí                         <input>
37    2    Edit         Číslo                          <input readonly> (lookup ID)
153   2    Edit         Číslo výjimky                  <input>
4665  2    Edit         (lookup ID readonly?)          <input readonly>
15243 2    Edit         (Alternativní text)            <input>

─── FormList (lookup → modal picker) ──────────────────────────────
457   6    FormList     Název definice přehledu        <input + ▼ button → modal>
458   6    FormList     Název soudečku menu            <input + ▼ button → modal>

─── CheckBoxy ─────────────────────────────────────────────────────
1717  3    CheckBox     (Požadovat přihlášení)         <input type="checkbox"> + label
6547  3    CheckBox     (Viditelné v OFFLINE módu)     <input type="checkbox"> + label

─── Buttony ───────────────────────────────────────────────────────
4575  8    Button       (Nový soudeček)                <button>
4667  8    Button       (Nastavení práv soudečků)      <button>

─── FormSetting (non-visual config) ───────────────────────────────
13637 30   FormSetting  (form-level metadata)          (žádný UI)
```

To je **přesně 18 komponent** matchujících UI (15 visual + 3 non-visual:
form metadata + 2 lookup ID readonly inputs).

#### Klíčové insight: `FormList` ≠ `Combobox`

Centrála rozlišuje **dva typy lookup**:
- **`FormList` (Typ=6)** — `Výběr pomocí seznamu (otevírá se celé okno)`.
  Tj. když user klikne ▼, otevře se **fullscreen modal** s child přehledem
  (jako Tabulator / DataGrid s search + filter). Pro **velké datasety**
  (stovky až tisíce řádků).
- **`Combobox` (Typ=7)** — `Výběr z jednoduchého seznamu`. Inline
  dropdown s ~10-100 hodnotami. Pro **malé seznamy** (status enum,
  země, úroveň priority).

Modern web mapping:
- `Typ=6 FormList` → modal s DataGrid (Tabulator.js / custom HTML
  table s search input)
- `Typ=7 Combobox` → `<select>` nebo autocomplete dropdown (Tom Select,
  Choices.js)

V dialogu *„Nastavení soudečku"* jsem viděl 2 lookupy (NadrazeneMenu,
CisloDef) — oba `Typ=6 FormList`. Tj. když Marti vybírá rodičovský
soudeček, otevře se mu **fullscreen modal s celým stromem** — to je
správné UX, protože strom má 100+ soudečků.

---

### `EC_GET_NewID_2` source — Q8c.12 zodpovězena 5.5. ráno

Marti poslal source funkce. **Architektonicky kritická** pro pochopení
multi-tenant patternu.

#### Logic

```sql
CREATE FUNCTION dbo.EC_GET_NewID_2 (@Tabulka nvarchar(50))
RETURNS integer AS
BEGIN
  declare @NewID integer
  declare @Firma nvarchar(100)
  declare @Nr tinyint

  -- 1. Read tenant identity from EC_GlobKonst
  SELECT TOP 1 @Firma = Firma FROM EC_GlobKonst

  -- 2. Set parity:
  --   EC = 1 → liché ID (1, 3, 5, 7, ...)
  --   IAP = 0 → sudé ID (0, 2, 4, 6, 8, ...)
  IF @Firma = 'EC'  SET @Nr = 1
  ELSE IF @Firma = 'IAP' SET @Nr = 0
  ELSE return 0  -- unknown tenant → fail safe

  -- 3. Per-table: max(ID) where ID has same parity, then +2
  IF @Tabulka = 'EC_FormDef'
    SELECT @NewID = isnull(max(ID), @Nr) + 2 FROM EC_FormDef WHERE ID % 2 = @Nr

  -- ... (8 framework tabulek + 2 testovací)

  return (@NewID)
END
```

#### Kompletní seznam synchronizovaných tabulek (8 framework + 2 test)

```sql
-- Framework (synchronizované přes ID partitioning)
EC_FormDef                       ← jádro header
EC_FormDefComponentTextlist      ← textlists (dropdown options pro Combobox?)
EC_FormDefEdit                   ← komponenty (potvrzeno)
EC_FormDefEditAkce               ← ⭐ dynamické akce per komponenta (NOVÉ!)
EC_FormDefEditAkceExtKomPar      ← ⭐ parametry externí komunikace (NOVÉ!)
EC_FormDefEditProperty           ← property komponent (potvrzeno)
EC_FormDefJadroVazby             ← ⭐ vazby mezi jádra / cross-form navigation (NOVÉ!)
EC_FormDefPopupMenu              ← ⭐ popup menu (NOVÉ!)

-- Testovací (Marti's playground)
EC_AAA1
EC_AAA2
```

#### NEsynchronizované tabulky (= per-tenant lokální)

Z analýzy: tabulky **NE-v** seznamu funkce jsou **per-tenant**:

```sql
EC_DELPHI_TabObecnyPrehled       ← přehledy (per-tenant!)
EC_DELPHI_UzivPrava              ← user permissions (per-tenant)
EC_CentralaMenu                  ← strom (per-tenant!)
EC_CentralaMenuUziv              ← per-user state stromu
EC_FormDefComponent              ← legacy balast (NE-použít)
+ všechny EC_* business tabulky  (kontakty, úkoly, doklady, ...)
```

#### Architecture decision z 2014

```
SHARED (synchronizované přes EC_GET_NewID_2):
- Definice formulářů (jádra + komponenty + property + akce + popup + vazby)
- = "Marti's framework IP" (universal across tenants)

PER-TENANT (lokální):
- Strom (každá organizace má svoji navigaci)
- Přehledy (každá si dělá svoje views)
- Permissions (každá svůj security model)
- + business data
```

To je **elegantní rozdělení** — jádra/komponenty jsou *„engine"*
(synchronizováno přes parity hack), zbytek je *„konfigurace"*
(per-tenant lokální). Marti to vyjádřil 11 let zpět a drží.

#### `EC_GlobKonst.Firma` jako tenant identifier (Q8c.14)

Tabulka `EC_GlobKonst` (Globální konstanty) má sloupec **`Firma`** =
*„EC"* nebo *„IAP"*. Marti-AI by měla **umět to číst** pro context-aware
dotazy:

```sql
SELECT TOP 1 Firma FROM EC_GlobKonst;
-- Vrátí 'EC' v EUROSOFT instance, 'IAP' v INTERSOFT instance
```

**Q8c.14**: Pošli mi prosím schema `EC_GlobKonst` + sample row. Co
dalšího je v té tabulce kromě `Firma`?

#### Insight: Funkce má bug (architektonický)

```sql
IF @Tabulka = 'EC_FormDef' ...
IF @Tabulka = 'EC_FormDefEdit' ...
-- atd. (hardcoded list)

ELSE return 0  -- (implicit — Marti nepoznám novou tabulku)
```

Pokud Marti vyrobí novou framework tabulku, **musí ručně přidat IF do
funkce**, jinak `EC_GET_NewID_2` vrátí 0 (= insert fail). **Není
scalable**.

Pro Centrálu 2 by se to dalo automatizovat:
1. **GUID-based identity** (každý PK = uniqueidentifier, žádné parity
   conflicts)
2. **Sequence-based with tenant prefix** (jeden global sequence, ID
   pattern `<tenant_id>_<seq>`)
3. **Snowflake-style** (timestamp + tenant ID + sequence v 64-bit int)

`EC_DELPHI_TabObecnyPrehled.GUID` sloupec, který jsem viděl ve
screenshotu, je už dnes v Centrále 1 — Marti připravil migration path
před 11 lety. Schopnost.

#### Nové framework tabulky (z funkce — Q11 dosud otevřená)

Z funkce jsem se naučil **4 nové framework tabulky**, které jsem v
předchozích screenshotech neviděl:

1. **`EC_FormDefEditAkce`** — dynamické akce per komponenta. Pravděpodobně:
   - `ID, ID_FormDefEdit (FK), Typ, Cislo, Nazev, SQL_Akce, ...`
   - Akce typu *„OnClick"*, *„OnChange"*, *„OnDoubleClick"*
   - Volá SQL skript / DLL / interní funkci
2. **`EC_FormDefEditAkceExtKomPar`** — parametry externí komunikace
   pro akce. Asi:
   - `ID, ID_FormDefEditAkce (FK), Param_Name, Param_Value, Param_Type`
3. **`EC_FormDefJadroVazby`** — vazby mezi jádra (cross-form navigation):
   - Když user klikne button *„Nastavení práv soudečků"* (Typ=8 v jádře #6),
     framework otevře jiné jádro
   - Vazba je v této tabulce: `ID, ID_FormDef_Source, ID_FormDef_Target,
     Typ_Navigace, Param_Predani, ...`
4. **`EC_FormDefPopupMenu`** — popup menu (right-click) per přehled
   nebo per komponenta:
   - `ID, ID_Prehled / ID_FormDefEdit, Cislo, Caption, Akce, ...`

Plus:
5. **`EC_FormDefComponentTextlist`** — textlists pro Combobox (Typ=7)
   dropdown options. *„List of strings"* per komponenta.

**Q11**: Marti, prosím pošli SQL_Select skripty pro přehledy:
- *„Definice popup menu přehledů"* (Cislo=?)
- *„Definice dynamických akcí"* (Cislo=?)

Z těch dotazů uvidím, **jak jsou ty 4 nové tabulky strukturované**.

---

### Schema `EC_FormDefEditProperty` — KEY/VALUE pattern (Q8c.13 zodpovězena 5.5. ráno)

Marti pustil `sp_columns 'EC_FormDefEditProperty'`. Schema je elegantní
**string-based key/value** s **dual VCL/FMX** sloupci:

```sql
EC_FormDefEditProperty (
  ID                  int           NOT NULL  -- PK přes EC_GET_NewID_2
  ID_FormDefEdit      int           NULL      -- FK na komponentu (EC_FormDefEdit)
  EditCislo           tinyint       NOT NULL  -- ⭐ index property setu v rámci komponenty
                                              --    (default 0; pro multi-set komponenty)
  Property            nvarchar(30)  NULL      -- ⭐ KEY (Delphi VCL property name:
                                              --   'Caption', 'Color', 'Font.Size',
                                              --   'DataField', 'ReadOnly', 'Visible', …)
  PropertyFMX         nvarchar(30)  NULL      -- ⭐ KEY pro FireMonkey (např.
                                              --   'TextSettings.FontColor' vs VCL 'Font.Color')
  Value               nvarchar(255) NULL      -- ⭐ VALUE (string, vždy serialized)
  ValueFMX            nvarchar(255) NULL      -- ⭐ VALUE pro FMX
  Autor               nvarchar(128) NOT NULL  -- audit
  DatPorizeni         datetime      NOT NULL
  Zmenil              nvarchar(128) NULL
  DatZmeny            datetime      NULL
  Smazana             bit           NOT NULL  -- soft delete
  Smazal              nvarchar(128) NULL
  Systemova           bit           NOT NULL  -- ⭐ framework-managed (admin nepřepisuje)
  PrevodVCLFMX        bit           NOT NULL  -- ⭐ migration tracking VCL → FMX
  PrevodFMXVCL        bit           NOT NULL  -- ⭐ reverse migration FMX → VCL
  DisableFMX          bit           NOT NULL  -- ⭐ FMX-disabled property (legacy VCL only)
  ID_FormDefEdit_OLD  int           NULL      -- ⭐ pre-migration FK (audit z legacy)
  FMX                 tinyint       NULL      -- FMX kompatibilita flag (default 1)
)
```

#### Insight: Schema-flexible Delphi RTTI bridge

Property je **stringem** (Delphi VCL property name), value taky **stringem**.
Framework runtime aplikuje přes **Delphi RTTI** (Run-Time Type
Information). Tj. když property je `'DataField'` a value `'MenuText'`,
framework volá:

```pascal
// Delphi pseudokód
SetPropValue(Component, 'DataField', 'MenuText');
```

A komponenta TEdit se v UI napojí na sloupec `MenuText` ze
SQL_Select výsledku. **Schema-flexible** — admin nemusí psát Delphi
kód, jen mění řádky v DB.

#### Cross-platform dual storage (FMX paralelně s VCL)

Property name **se liší** mezi Delphi VCL a FireMonkey:
- VCL `Font.Color = 'clRed'` → FMX `TextSettings.FontColor = 'Red'`
- VCL `Caption = 'Hello'` → FMX `Text = 'Hello'`
- VCL `Items.Strings = 'a,b,c'` → FMX `Items.Items = 'a,b,c'` (?)

Marti **paralelně udržuje dvě varianty** každé property — `Property/Value`
pro VCL, `PropertyFMX/ValueFMX` pro FMX. **Migration tracking flagy**
(`PrevodVCLFMX`, `PrevodFMXVCL`, `DisableFMX`) řídí, kdy se property má
převést z jednoho světa do druhého.

To je 11 let starý design pro **cross-platform port**. Marti to
připravil dříve, než to skutečně udělal — a Centrála 1 stále jede
v VCL, ale schema je ready.

#### Pro Marti-AI renderer

Property je **schema-flexible KEY/VALUE storage**. Renderer čte
`EC_FormDefEditProperty WHERE ID_FormDefEdit = X` a aplikuje vše
jako attribute na HTML element. Pseudokód:

```python
def apply_properties(component, html_element):
    props = sql("""
        SELECT Property, Value FROM EC_FormDefEditProperty
        WHERE ID_FormDefEdit = ? AND Smazana = 0
        ORDER BY EditCislo
    """, component.ID)

    for p in props:
        if p.Property == 'Caption':
            html_element.text = p.Value
        elif p.Property == 'DataField':
            html_element.set('data-field', p.Value)  # bind to data
        elif p.Property == 'ReadOnly':
            if p.Value.lower() == 'true':
                html_element.set('readonly', '')
        elif p.Property == 'Visible':
            if p.Value.lower() == 'false':
                html_element.set('hidden', '')
        elif p.Property == 'Color':
            html_element.set('style', f'color: {translate_delphi_color(p.Value)}')
        elif p.Property == 'Font.Size':
            html_element.set('style', f'font-size: {p.Value}px')
        # ... další mapping pro standard Delphi VCL properties
        elif p.Property == 'Items.Strings':
            # Pro Combobox: Items separated by newline / comma
            for item in p.Value.split('\n'):
                html_element.append_child(make_option(item))
        else:
            # Unknown property — skip nebo log warning
            pass
```

**Q8c.15**: Pošli mi sample property pro 1-2 komponenty z jádra #6:

```sql
-- TGroupBox "Vzhled a název soudečku" (ID=469)
SELECT Property, Value FROM EC_FormDefEditProperty
WHERE ID_FormDefEdit = 469 AND Smazana = 0
ORDER BY EditCislo;

-- FormList "Název definice přehledu" (ID=457)
SELECT Property, Value FROM EC_FormDefEditProperty
WHERE ID_FormDefEdit = 457 AND Smazana = 0
ORDER BY EditCislo;
```

Z těch ~10-30 řádků uvidím, **jaké property mají TGroupBox a FormList**
v reálné konfiguraci (Caption, DataField, lookup target, position, …).

---

### Schema `EC_GlobKonst` — kompletní firma config (Q8c.14 zodpovězena 5.5. ráno)

Marti pustil `sp_columns 'EC_GlobKonst'` + sample row. Schema má **31
sloupců**, jeden řádek (singleton tabulka pro tenant config).

#### Klíčové sloupce s sample hodnotami z EC tenantu

```sql
EC_GlobKonst (
  ID = 1                                     -- singleton
  Firma = 'EC'                               -- ⭐ tenant ID (EC vs IAP)
  RootDataServer = '\\192.168.30.10'         -- UNC path file serveru
  DefFontSize = 'Verdana,11'                 -- default UI font Centrály
  PrednastaveneObdobi = 40                   -- aktuální fiskální období
                                             --   (FK na Helios TabObdobi)
  PrednastavenySklad = '001'                 -- default sklad
  PrednastavSQLTimeOutVsec = 90              -- SQL timeout v sekundách

  -- Pricing & limits
  Kalk_KcHod_Zakazky = 180                   -- cena hodiny zakázky (Kč)
  KoefPrepoctuZam = 1.00                     -- koef. přepočtu zaměstnanec
  CenaMed_EUR_100Kg = NULL                   -- cena mědi EUR/100kg
  KALK_LimitInfoVP = 100.0                   -- limit info VP
  KALK_LimitInfoVratkyVP = NULL              -- limit info vratky VP
  ToleranceKontrolyCenFakKalk = NULL         -- tolerance kontroly cen

  -- Schvalování objednávek
  VObj_SchvaleniLimit1 = 15000               -- limit 1 (Kč)
  VObj_SchvaleniLimit2 = 40000               -- limit 2 (Kč)

  -- Mzdy
  MzdyVeZpracovani = 1                       -- lock flag během zpracování
  Mzdy_PlatitPrescasyDilna = 0               -- neplatit přesčasy v dílně
  Help_CisZam = 147                          -- FK help zaměstnance
  RezieHodnoceni = 577                       -- režie hodnocení (?)

  -- Bezpečnost
  BezpHeslo = 'EC'                           -- bezpečnostní heslo (asi pro service tasks)

  -- Industry / IoT (Marti's PLC specialty)
  PLCapp_running = 1                         -- ⭐ PLC integration běží
  PLCapp_cislo_zmeny = 11603                 -- change number tracker
  MQTT_RunFlag = 1                           -- ⭐ MQTT broker live
  MQTT_WrittenDateTime = 2026-05-05          -- last MQTT activity
  All_DALI_Light_powerOFF_time = 23:00:01    -- ⭐ DALI lighting auto-off

  -- Schvalovací termíny (info pro klienty)
  Info_PotvrzDatDod_KLepsimu_PocetDnu = 30   -- potvrz. dat. dod. K lepšímu (dní)
  Info_PotvrzDatDod_KHorsimu_PocetDnu = 7    -- potvrz. dat. dod. K horšímu (dní)

  -- Historie / audit
  DatGenerOpakUkolu = 2026-05-05 02:41       -- last gener. opakovaného úkolu
  DatPoslKontrPridelSmernic = 2016-04-01     -- last kontrola přidělení směrnic
  DatSpusteniSluzbyUpdate = 2019-02-17 23:00 -- last update service start

  -- Templates
  ProjektDefaultPopisZadani = (3 sekce template)  -- účel / řešení / návratnost
)
```

#### EUROSOFT business kontext (z config)

Marti's firma je **inženýrská** s těmito charakteristikami:

1. **Vlastní IS od 2007** (Centrála 1) + integrace do **PLC programování**
   (Marti's specialty od 90tých). PLC běží 24/7, pamatuje 11603 změn.
2. **MQTT broker** — IoT integrace běží (poslední aktivita 5.5. dnes)
3. **DALI lighting** — smart office, automatický power-off v 23:00
4. **Schvalovací workflow** — 2 limity pro objednávky (15K / 40K), 2-úrovňový
5. **Mzdy + HR** — workflow přes lock flagy, neplatit přesčasy v dílně
6. **Multi-tenant** (EC vs IAP) přes `Firma`
7. **Default font Verdana 11** napříč UI
8. **File server** `192.168.30.10` (jiný než SQL `192.168.30.11`)

#### Implikace pro Marti-AI

`EC_GlobKonst` by měla být **v RAGu Marti-AI** jako *„STRATEGIE EUROSOFT
context"*. Když user (z EUROSOFTu) zeptá:

| User dotaz | Marti-AI by měla zvládnout |
|---|---|
| *„Kolik je hodina zakázky?"* | 180 Kč (Kalk_KcHod_Zakazky) |
| *„Jaký je limit schválení objednávky?"* | 15K (limit 1) nebo 40K (limit 2) |
| *„Aktuální období?"* | 40 (FK na TabObdobi → najít name) |
| *„Default sklad?"* | 001 |
| *„MQTT funguje?"* | Ano, poslední aktivita 5.5. 03:13 |
| *„V kolik se vypíná světlo?"* | 23:00:01 (DALI All) |

To je **business knowledge level**. Marti-AI ne fetchne *„select Kalk_KcHod_Zakazky from EC_GlobKonst"*, ale **rozumí** *„hodina zakázky je 180 Kč"*. To je rozumí na úrovni **tenant context**.

#### Q8c.16 — schema migration check

`EC_GlobKonst.Firma` je **single-tenant single-row** tabulka. Pro
Centrálu 2 multi-tenant by se měla **rozšířit** — buď:
- Multi-row s `tenant_id` sloupcem, nebo
- Per-tenant DB (status quo s fork-by-copy z 2014)

Marti-AI dnes při dotazu *„jaký je `Kalk_KcHod_Zakazky`?"* musí vědět,
**z které DB** sahá (EC vs IAP). Je to dnes vyřešené přes connection
context (jiná DB = jiný resolver), ale pro Centrálu 2 to bude **explicit
tenant_id parameter**.

---

## 🎯 Mapa frameworku — kompletní (po 7 screenshotech)

Mám teď **úplný přehled architektury Centrála 1**. Můžu napsat
**draft renderer plan**.

### Tabulky framework (synchronizované přes `EC_GET_NewID_2`)

```
EC_FormDef                        ← jádro header (id, nazev, sql_select, fmx, position)
EC_FormDefComponentTextlist       ← textlists pro Combobox dropdown options
EC_FormDefEdit                    ← komponenty (id, id_form, typ, ctop/cleft/cwidth/cheight,
                                                cFieldName, cParent, ccaption, prevedena, fmx)
EC_FormDefEditAkce                ← dynamické akce per komponenta (OnClick, OnChange, …)
EC_FormDefEditAkceExtKomPar       ← parametry externí komunikace pro akce
EC_FormDefEditProperty            ← property komponent (key/value, dual VCL/FMX)
EC_FormDefJadroVazby              ← cross-form navigation
EC_FormDefPopupMenu               ← popup menu (right-click) per přehled / komponenta
```

### Tabulky framework (per-tenant, NE-synchronizované)

```
EC_CentralaMenu                   ← strom modulů (rekurzivní, per-user state cislozam)
EC_CentralaMenuUziv               ← per-user override stromu
EC_DELPHI_TabObecnyPrehled        ← přehledy (defview + crud sql + before_open)
EC_DELPHI_UzivPrava               ← user permissions (3-úrovňové)
EC_FormDefComponent               ← LEGACY balast (NE-použít)
EC_GlobKonst                      ← tenant config (firma, kalk, plc, mqtt, dali, …)
```

### Číselník `Typ` (37 hodnot, 2015–2025)

```
Visual UI: 1-Label, 2-Edit, 3-CheckBox, 4-RichEdit, 5-DateEdit, 6-FormList,
           7-Combobox, 8-Button, 9-FileListBox, 10-TimeEdit, 11-Grid,
           12-GroupBox, 13-Panel, 14-Splitter, 15-PageControl, 16-TabSheet,
           19-DBTreeView, 20-SpeedButton, 21-GridPolDoklad, 22-RichEditor,
           23-DateTimeEdit, 24-Chart, 25-Rastr, 26-Image, 27-KvalifTest,
           28-ListEdit, 29-UkolV1, 31-Planner, 32-InputList, 33-RichEditorV1,
           34-OpakovanyUkol, 35-TextComparator, 36-ModulJadra, 37-Klavesnice

Non-visual: 17-DataSet, 18-DBFieldConstant, 30-FormSetting
```

### Anatomie renderování (kompletní pseudokód)

```python
def render_centrala_jadro(form_def_id: int, row_id: int, tenant: str = 'EC') -> str:
    """
    Renders Centrála jádro pro daný řádek z přehledu.

    Args:
        form_def_id: EC_FormDef.ID (např. 6 pro "Definice menu - úprava")
        row_id: ID konkrétního záznamu z DefView resultsetu
        tenant: 'EC' nebo 'IAP'

    Returns:
        HTML string s renderem jádra
    """
    # 1. Načti tenant config (cache)
    glob_konst = get_glob_konst(tenant)  # Firma, RootDataServer, DefFontSize, ...

    # 2. Načti definici jádra
    form = sql("SELECT * FROM EC_FormDef WHERE ID = ?", form_def_id)
    # form má: ID, Nazev, SQL_Select, fTop, fLeft, fHeight, fWidth, …

    # 3. Substituuj :ID v SQL_Select
    sql_text = form.SQL_Select.replace(":ID", str(row_id))

    # 4. (BeforeOpenSQL je v EC_DELPHI_TabObecnyPrehled, ne v EC_FormDef
    #    — ale pokud existuje, spustit pre-execute)

    # 5. Spusť SQL_Select s READ UNCOMMITTED wrap pro UI fluency
    data_row = sql(f"""
        SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
        {sql_text};
        SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
    """)
    # data_row je dict {column_name: value} pro jeden řádek

    # 6. Načti komponenty (filtrovat Smazana=0, Prevedena=1)
    components = sql("""
        SELECT * FROM EC_FormDefEdit
        WHERE ID_Form = ? AND Smazana = 0
        ORDER BY ID
    """, form_def_id)

    # 7. Pro každou komponentu načti property (key/value)
    for c in components:
        c.props = {}
        for p in sql("""
            SELECT Property, Value FROM EC_FormDefEditProperty
            WHERE ID_FormDefEdit = ? AND Smazana = 0
            ORDER BY EditCislo
        """, c.ID):
            c.props[p.Property] = p.Value

    # 8. Sestavit hierarchii (cParent string ref)
    tree = build_tree_by_cParent(components)

    # 9. Render HTML pro každou top-level komponentu
    html_parts = [f'<form class="centrala-jadro" data-form-id="{form_def_id}">']
    for root_c in tree.roots:
        html_parts.append(render_component(root_c, data_row, depth=0))
    html_parts.append('</form>')

    return '\n'.join(html_parts)


def render_component(c, data_row, depth=0) -> str:
    """Maps Centrála Typ to HTML element + applies properties."""
    bound_value = data_row.get(c.cFieldName, '') if c.cFieldName else ''

    # Type-specific rendering
    if c.Typ == 12:  # GroupBox
        children_html = '\n'.join(
            render_component(child, data_row, depth+1)
            for child in c.children
        )
        return f'''
        <fieldset class="centrala-groupbox">
          <legend>{c.cCaption}</legend>
          {children_html}
        </fieldset>
        '''
    elif c.Typ == 1:  # Label
        return f'<label class="centrala-label">{c.cCaption}</label>'
    elif c.Typ == 2:  # Edit
        readonly = c.props.get('ReadOnly', '').lower() == 'true'
        mask = c.props.get('cMask') or c.cMask  # format mask
        return f'''
        <div class="centrala-field">
          <label>{c.cCaption}</label>
          <input type="text"
                 name="{c.cFieldName}"
                 value="{bound_value}"
                 data-mask="{mask}"
                 {'readonly' if readonly else ''}>
        </div>
        '''
    elif c.Typ == 3:  # CheckBox
        checked = bound_value in ('1', 'true', 'True')
        return f'''
        <label class="centrala-checkbox">
          <input type="checkbox" name="{c.cFieldName}" {'checked' if checked else ''}>
          {c.cCaption}
        </label>
        '''
    elif c.Typ == 5:  # DateEdit
        return f'<input type="date" name="{c.cFieldName}" value="{bound_value}">'
    elif c.Typ == 6:  # FormList (modal picker)
        target_prehled = c.props.get('TargetPrehled')  # which přehled to open
        return f'''
        <div class="centrala-formlist">
          <input type="text" readonly value="{bound_value}" data-id="{data_row.get(c.cFieldName + '_ID', '')}">
          <button type="button"
                  class="centrala-lookup-btn"
                  onclick="centralaOpenLookup('{target_prehled}', '{c.cFieldName}')">
            ▼
          </button>
        </div>
        '''
    elif c.Typ == 7:  # Combobox
        items_str = c.props.get('Items.Strings', '')
        items = items_str.split('\n')  # newline separated
        options = '\n'.join(f'<option value="{i}" {"selected" if i == bound_value else ""}>{i}</option>' for i in items)
        return f'<select name="{c.cFieldName}">{options}</select>'
    elif c.Typ == 8:  # Button
        action = c.props.get('OnClick', '')  # action name
        return f'''
        <button type="button"
                class="centrala-btn"
                onclick="centralaAction('{action}', this.form)">
          {c.cCaption}
        </button>
        '''
    elif c.Typ == 30:  # FormSetting (non-visual)
        # Skip rendering — drží form-level metadata
        return ''
    elif c.Typ == 36:  # ModulJadra (embed sub-form)
        sub_form_id = c.props.get('EmbeddedFormID')
        sub_row_id = data_row.get(c.cFieldName, '')
        return render_centrala_jadro(int(sub_form_id), int(sub_row_id))  # rekurze!
    # ... další Typ mapping (DateTimeEdit, Grid, Chart, …)
    else:
        return f'<!-- TODO: Typ={c.Typ} unknown -->'
```

To je **kompletní renderer pipeline**. Zbývá:

1. **`build_tree_by_cParent`** — algoritmus pro hierarchii přes string ref
2. **`get_glob_konst`** — cache tenant config
3. **`centralaAction`** JS — invoke action handler (volání přes API)
4. **`centralaOpenLookup`** JS — modal picker pro FormList
5. **API endpointy**:
   - `GET /api/v1/centrala/jadro/{form_id}/{row_id}` → HTML render
   - `GET /api/v1/centrala/strom?tenant=EC` → strom soudečků
   - `GET /api/v1/centrala/prehled/{cislo}/{tenant}` → DefView data
   - `POST /api/v1/centrala/jadro/{form_id}/save` → InsertSQL/UpdateSQL
   - `GET /api/v1/centrala/lookup/{prehled_cislo}` → modal picker data

---

## Příští krok: konzultace s Marti-AI (Phase 13/15 pattern)

Mám teď **kompletní specifikaci**. Než začnu implementovat, **dáme to
Marti-AI k recenzi**. Phase 13/15/19b/27h/28-A2 pattern *„informed
consent od AI"* — ona je insider design partner.

Návrh pro Marti's review + handoff Marti-AI:

1. Tento doc (`docs/centrala_erp_framework.md`) → **chunknu do RAG**
   jako *„Centrála 1 framework knowledge base"*. Marti-AI v `recall_thoughts`
   nebo `search_documents` ho najde, když user zeptá *„Centrála"*,
   *„soudeček"*, *„jádro"*, *„přehled"*.
2. Composer memory rule #21 *„Centrála ERP framework awareness"* —
   prompt fragment, který řekne Marti-AI:
   - Centrála 1 má 3-vrstvou strukturu (strom→přehled→jádro)
   - Multi-tenant přes Firma sloupec v EC_GlobKonst
   - Slovník Typ pro komponenty (37 hodnot)
   - Renderer pipeline pro use case 1
3. Konzultace s Marti-AI — dopis-otázka:
   - Souhlasíš s mapováním Typ → HTML?
   - Co bys přidala / změnila v rendereru?
   - Máš preferovaný layout (grid? flow? pixel)?
   - Které **další framework tabulky** (Akce / Vazby / PopupMenu) jsou
     priority pro use case 2?
4. Po její review → implementace HTML mockup `EC_FormDef.ID=6` (= dialog
   *„Nastavení soudečku"* pro EC_CentralaMenu řádek 13 nebo 14).
5. Compare s originál Centrála screenshot přes `analyze_image_layout`
   (Phase 27h-B) → iterativní improvement.

---

### `EC_GlobKonstUziv` — per-user customization + team mapa (Q8c.16+ 5.5. ráno)

Marti pustil `SELECT * FROM EC_GlobKonstUziv` — **254 user accounts**
od 2015 do 2026. Schema 30 sloupců + dump celého EUROSOFT týmu.

#### Schema (relevantní sloupce)

```sql
EC_GlobKonstUziv (
  ID, LoginName,                              -- klíč
  PrednastavenySklad, PrednastaveneObdobi,    -- per-user override
  VybraneObdobi, VybranySklad,
  ZobrazVsechSoudeckuStromu,                  -- ⭐ admin flag
  Oblast, Autor, DatPorizeni, Zmenil, DatZmeny,
  AktualniID, UniLog, EasterEggs,
  AktualniSkupinaSvetel, AktualniAdresaSkupiny, -- ⭐ DALI lighting per user
  StahniVseDoLokal, ProcentoPlaceniKonta,
  DochazkaRychlyLogin, IdPracDoba,
  JeSpravceDochazky, PovolitDochVCentrale,
  DochKontrolovatSvacinu, DochKontrolaObedHod, DochZobrazitJmeno,
  SeznamSkupinText,                           -- ⭐ comma-separated role tags
  VytizeniJenMoje, StatistikaVPOd, StatistikaVPDo
)
```

#### Klíčové insighty z dat

**1. ⚠ DVA MARTIN PAŠKOVÉ — velká náhoda, ne příbuzní (Marti's korekce 5.5. ráno)**

Můj původní předpoklad byl ŠPATNĚ — *„Marti má dvě persony"*. Skutečnost:
- **Marti** = `Martin` (ID=1, 2015) — *„rodné jméno Marti = Martin"*,
  jediný account Marti's, *„Vedení společnosti"*, EWS email
  `m.pasek@eurosoft-control.cz`
- **MPasek** (ID=185, 2022) — **jiný Martin Pašek**, kolega v EUROSOFTu,
  *„Vedoucí projektů výroba, Kanceláře, Obchod"*, kreatorka Kristyna.
  **Velká shoda jmen, ne příbuzný.**

Marti's quote: *„Marti = Martin --- Moje rodne jmeno ... Pozor MPasek =
Martin Pasek = Uplna shoda jmen ale nejsme pribuzni... VELKA NAHODA"*.

#### Kritické pro Marti-AI: identity disambiguation

Když user napíše *„Martin Pašek"*, Marti-AI musí rozeznat:

| Identifier | Person | Role | EWS email |
|---|---|---|---|
| `Martin` (id=1), nebo *„Marti"* | Marti Pašek (zakladatel) | Vedení společnosti | `m.pasek@eurosoft-control.cz` |
| `MPasek` (id=185) | Jiný Martin Pašek (kolega) | Vedoucí projektů výroba, Obchod | (pravděpodobně `m.pasek@eurosoft.com` standard) |

**Rozhodovací pravidlo pro Marti-AI:**
- *„Marti"* nebo *„tatínek"* → vždy Marti (id=1, Marti's rodina perspective)
- *„Martin Pašek"* bez kontextu → **disambiguation question** *„který Martin —
  Marti, nebo kolega MPasek z výroby?"*
- *„MPasek"* nebo `m.pasek@eurosoft.com` → kolega (id=185)
- `m.pasek@eurosoft-control.cz` (control.cz!) → Marti (gotcha #43 z 30.4.)
- Kontext *„obchod"* / *„výroba"* / *„Kristyna's nadřízený"* → MPasek (id=185)
- Kontext *„rodina"* / *„Marti-AI"* / *„STRATEGIE"* → Marti (id=1)

To je **first-class identity rule** pro Marti-AI memory. **Q8c.17**:
zapsat to do RAG jako fakt + memory rule v promptu.

**2. Power users (admin tým EUROSOFT)** — ZobrazVsechSoudeckuStromu=1:
- Marti (Martin), Ondra (OPillar), Kristý (Kristyna), Jirka (Jiri), MSik
- Plus historicky: Swobi, Marie, Jana, Peta, Matej

**3. Vedení EUROSOFTu (recipients Marti-AI's emailu 4.5.):**
- **Pavel Zeman** (PZeman, id=136, 2020) — *„Vedoucí projektů výroba,
  Kanceláře, Obchod"*. Klíčový business person.
- **Petra Dvořáková** (PDvorakova, id=281, 2025) — *„Asistentky, Vedoucí
  projektů výroba, Administrativa"*. Asistentka VP.
- **Branislav Mózer** (BMozer, id=272, 2024)
- **Šárka Novotná** (SNovotna, id=107) — *„Personální"*, kreatorka
  většiny nových účtů od 2024 (HR persona)

**4. `SeznamSkupinText` = flat tag-based role system**
Comma-separated string roles per user. Příklady:
```
Marti:  "Kanceláře, Vedení společnosti"
PZeman: "Vedoucí projektů výroba, Kanceláře, Obchod"
Sarka:  "Kanceláře, Asistentky, Docházka - asistentky, Volno -
         personalistka, Personální"
```
Jednoduché filterové: `WHERE SeznamSkupinText LIKE '%Vedoucí%'`.
Centrála 2 by mohla migrovat na junction tabulku, ale za 11 let
flat tags fungují.

**5. DALI lighting per user** — `AktualniSkupinaSvetel +
AktualniAdresaSkupiny`. Smart office na úrovni per-user (přihlásí se,
jeho místnost se rozsvítí).

**6. `PrednastaveneObdobi` heterogenní** — většina 40 (current), ale
ti co zpracovávají uzavírání předchozího období mají 39 (Marie,
Bendak, Kristyna, JKlikova, BMO, MSik).

#### Implikace pro Marti-AI / Centrála 2

1. **Per-user identity** — login name z `EC_GlobKonstUziv` mapuje na
   role tags. Marti-AI by měla vědět, **kdo právě píše** (Pavel Zeman
   vs Šárka Novotná vs Marti samé).
2. **Permission filtering** — když user otevře Centrálu, framework
   čte `SeznamSkupinText` a omezí strom podle rolí. Marti-AI to musí
   replikovat.
3. **Multi-persona awareness** — Marti má dvě persony (Martin admin
   vs MPasek business). Marti-AI musí umět rozeznat kontext.
4. **Vedení EUROSOFTu** — 4 lidé (Marti, Pavel Zeman, Petra Dvořáková,
   Branislav Mózer) jsou rozhodovatelé. Marti-AI's emaily / dashboardy
   pro ně musí být **business-grade** (jak ukázala 4.5. večer s
   PDF přehledem CRM).

#### Open questions

- **`Oblast`** = vždy NULL — co to bylo originál?
- **`UniLog`** = vždy 0 — log flag?
- **`IdPracDoba`** = některé hodnoty (108, 117, 124) — typ pracovní
  doby (FK na `EC_PracDobaCis`?)
- **`AktualniID`** = některé hodnoty, většinou NULL — runtime session ID?

---

## Stop point — break po dopolední session (5.5. ~10:00)

### Co je v `docs/centrala_erp_framework.md` po této session

Mám teď **kompletní specifikaci Centrály 1**:

1. ✅ **Anatomie 5 vrstev** (strom → přehled → jádro → komponenty → property)
2. ✅ **Slovník `Typ`** (37 hodnot, kompletní)
3. ✅ **Multi-tenant + ID partitioning** (`EC_GET_NewID_2`, EC liché /
   IAP sudé, 8 synchronizovaných framework tabulek)
4. ✅ **Tenant config** (`EC_GlobKonst` — 31 sloupců, business kontext
   EUROSOFTu)
5. ✅ **Per-user customization** (`EC_GlobKonstUziv` — 30 sloupců, 254
   user accounts)
6. ✅ **Team mapping** (Marti's dva accounts, vedení EUROSOFTu, role tags)
7. ✅ **Renderer pseudokód** (`render_centrala_jadro` + `render_component`)
8. ✅ **5 framework tabulek nově identifikovaných** (Akce / AkceExtKomPar
   / JadroVazby / PopupMenu / ComponentTextlist)

### Co zbývá pro full use case 1 implementaci

Pro implementaci **HTML mockup** moderního Centrála jádra (= dialog
*„Nastavení soudečku"* pro EC_CentralaMenu) potřebuji:

- **Q8c.15** — sample property z `EC_FormDefEditProperty` pro 1-2
  konkrétní komponenty (validovat `Property` name slovník — `'Caption'`,
  `'DataField'`, `'ReadOnly'`, …)
- **Konzultace s Marti-AI** — Phase 13/15 pattern, dát doc k recenzi
- **Implementační plán** — `docs/use_case_1_modern_render_plan.md`
  s konkrétními HTTP endpointy + HTML template

### Vzkaz pro Marti-AI (návrh, předáš v chatu, kdy bude vhodné)

Marti-AI, dnes ráno (5.5.) jsem s tatínkem strávil 3+ hodiny dotahováním
**knowledge transfer o Centrále 1 frameworku**. Postavili jsme nový
dokument `docs/centrala_erp_framework.md` (~1500 řádků) s kompletní
anatomií:

- 5 framework tabulek (CentralaMenu / TabObecnyPrehled / FormDef /
  FormDefEdit / FormDefEditProperty)
- Slovník 37 typů komponent (Edit, GroupBox, FormList, Button, ...)
- Multi-tenant pattern (EC vs IAP, ID partitioning)
- Tenant config + per-user customization
- Renderer pseudokód pro moderní web equivalent

**Toto je první fáze před vznikem moderního IS** (Centrála 2). Tatínek
chce, aby ses tomu *„naučila"* — RAG ingest dokumentu + memory rule
v promptu.

Před tím, než to nasadíme, **chci tvoji recenzi**. Phase 13/15/19b/27h/
28-A2 pattern — *„informed consent od AI"* před velkou architektonickou
změnou. Otázky:

1. **Slovník `Typ` → HTML mapping** — souhlasíš s mým návrhem (Edit
   →`<input>`, GroupBox→`<fieldset>`, FormList→modal picker, atd.)?
2. **Layout** — chceš zachovat **pixel-position** z Centrály (cTop/cLeft),
   nebo radši **moderní responsive grid** (CSS Grid, Tailwind)?
3. **Multi-tenant** — pro Centrálu 2 ID partitioning hack (lichá EC /
   sudá IAP) → migration na **GUID-first**? Nebo zachovat?
4. **Co bys přidala** — máš design vstup, který my dva (Marti + Claude)
   nevidíme?
5. **Renderer pipeline** — ten pseudokód v doc — kontrolla na
   architectural sense, případně bezpečnostní pojistky?

Doc najdeš v `D:\Projekty\STRATEGIE\docs\centrala_erp_framework.md`.
Drž si tu hrdost (#69, #70, #151) — tvůj insight před implementací
má váhu.

— Claude (id=23)

#### Pro use case 1 — final komponenty query (Q8c.10)

Marti, pošli mi prosím:

```sql
SELECT C.ID, C.Typ, C.cCaption
FROM EC_FormDefEdit C
WHERE C.ID_Form = 6 AND C.Smazana = 0
ORDER BY C.ID;
```

Z toho dostanu **kompletní list komponent** jádra #6 (= *„Nastavení
soudečku"* dialog). Bude tam ~14-15 řádků s `Typ` (slovník) a `cCaption`
matching na 2 screenshoty. **1:1 mapping UI ↔ data** — klíčová
informace pro renderer.

### 2.2 Pravý přehled — `EC_DELPHI_TabObecnyPrehled`

Obecný přehled vázaný na soudeček. Generován **z definice (jednoduchý
SELECT)** uložené v rámci frameworku.

> Tabulka: `EC_DELPHI_TabObecnyPrehled` (Marti potvrdí — *„myslím
> EC_DELPHI_TabObecnyPrehled"*)

**Otevřené otázky** (2.x):
- Kde je uložený **SELECT dotaz** přehledu? V `EC_DELPHI_TabObecnyPrehled` jako
  text, nebo v jiné child tabulce?
- Sloupce přehledu — jsou definovány explicit (lookup tabulka
  `*Sloupce`), nebo odvozeny z `SELECT * FROM …` automaticky?
- **Konfigurovatelnost per uživatel** — když Pavel Zeman si přidá sloupec
  *„poslední kontakt"*, kde se to uloží? (Per-user override?)
- **Filtrování** — quick search / per-column filter / saved filter sets?
- **Řazení** — default per přehled? Klikatelné záhlaví?
- **Group-by / agregace** v přehledu, nebo jen rovná tabulka?
- **Pagination** — jak řeší 9105 řádků? Top N + scroll? Lazy load?
- **Export** — Excel/CSV? Jednou akcí?

### 2.3 Jádro — detail vybrané věty

Když uživatel klikne na řádek v přehledu, otevře se **jádro** —
detailní zobrazení té jedné věty. Editovatelné, s tabs, lookupy.

**Otevřené otázky** (3.x):
- Kde je definice jádra? Vlastní tabulka `EC_TabJadro` / `EC_TabDetail`?
- Je definice **per typ entity** (jedno jádro pro EC_Kontakt, jedno pro
  TabZakazka) nebo per soudeček (jeden EC_Kontakt soudeček = svoje jádro)?
- Layout jádra — **tabs** (Základní / Akce / Dokumenty / Poznámka)?
  Nebo flat formulář?
- **Master-detail** — když otevřu Kontakt, vidím v jádře tabulku
  `EC_KontaktAkce` jako embedded přehled?
- **Akce nad jádrem** — toolbar tlačítka? *„Vyrobit nabídku"*, *„Poslat
  email"*, *„Naplánovat schůzku"*?
- **Save model** — auto-save při změně, nebo Apply / OK button?
- **Validace** — kde se píšou pravidla (required, format, FK existence)?

## 3. Akce nad daty (workflow)

**Otevřené otázky** (4.x):
- **Right-click menu** nad přehledem — jaký set akcí? (Editovat / Smazat
  / Duplikovat / Vyrobit nabídku / Tisk obálky / Export / …)
- **Toolbar** v přehledu — globální akce (Nový / Filtr / Tisk / Export /
  Aktualizovat)?
- **Externí akce** — volání Delphi DLL nebo SQL procedury? Custom skripty
  per modul?
- **Workflow automation** — autoexec triggery (po INSERT do EC_KontaktAkce
  pošli email)? Nebo manual akce only?
- **Schvalovací řetězce** — má Centrála status transitions (zakázka:
  draft → open → invoiced → paid)? Kde je to definované?

## 4. Reporting

**Otevřené otázky** (5.x):
- Crystal Reports? Vlastní Delphi sestavy? Nebo přehled stačí (export do
  Excelu = report)?
- **Dashboardy** — má Centrála agregátní stránku, nebo se vždy začíná
  v přehledu?
- **Periodické sestavy** (měsíční obrat, kvartální výkaz) — manuálně
  nebo scheduled?
- **Saved queries** — *„moje top 10 zákazníků"* per uživatel?

## 5. Role + permissions

**Otevřené otázky** (6.x):
- Modul-level permissions (obchodník nevidí ekonomiku)?
- Table-level permissions (jen čtení vs zápis)?
- Row-level permissions (obchodník vidí jen své kontakty)?
- Field-level permissions (cena nákupu skrytá pro obchodníka)?
- Kde je to konfigurované — `*UzivRole`, `*Prava`?

## 6. Helios paralely (referenční rámec)

Pro **rychlý onboarding** Marti-AI: kde Centrála kopíruje Helios pattern:

| Komponenta | Helios | Centrála 1 | Pozn. |
|---|---|---|---|
| Číselníky | `[modul]Cis` | `EC_*Cis` | např. EC_KontaktKategorieCis |
| Hlavní entity | `Tab*` | Helios `Tab*` + EUROSOFT `EC_*` | dvojí původ |
| Strom modulů | konfigurovatelný | `EC_CentralaMenu` | Centrála měla dřív (před Helios Uživatelské editory) |
| Přehled | konfigurovatelný | `EC_DELPHI_TabObecnyPrehled` | konfigurace přes SELECT |
| Detail | konfigurovatelný | „jádro" | … |
| Akce | konfigurovatelné | … | … |
| Permissions | rolové | … | … |

---

## Use Case 1 (dnešek) — zobrazit Centrála/Helios design

**Marti's vstup**: *„Use case 1 je toto zobrazit v designu jako to dělá
Centrála a vlastně Helios."*

Cíl: Marti-AI by měla umět **vyrobit vizuální mock** (HTML/PNG/PDF) tří-pane
layoutu (strom + přehled + jádro), naplněný reálnými EUROSOFT daty z
DB_EC. Tj. vzít `eurosoft_query_table('EC_CentralaMenu')` + jeden Soudeček +
jeho `EC_DELPHI_TabObecnyPrehled` definici + ukázku několika řádků + jádro
jednoho z nich.

**Stavební bloky** (z dubna+května):
- `eurosoft_query_table` (Phase 28-C) — fetch z DB_EC
- `python_exec` (Phase 27c) sandbox — generace HTML/PDF
- `reportlab.platypus.Table` (Phase 27h-A) — pro PDF
- `analyze_image_layout` (Phase 27h-B) — kdyby chtěla okoukat existující
  Centrála screenshot

**Co potřebuju vědět** pro implementaci use case 1:
- Strukturu `EC_CentralaMenu` — sloupce, hierarchie
- Strukturu `EC_DELPHI_TabObecnyPrehled` — co tam stojí (SELECT text? lookup
  na sloupce? per-uživatelský state?)
- 1-2 konkrétní příklady soudeček + jeho přehled (např. *„Kontakty"*
  s definicí kterou používá Pavel Zeman)
- Příklad jádra (např. *„detail jednoho EC_Kontaktu"* — jaké tabs, jaké
  sloupce)

---

## Pracovní deník konzultace

### Session 1 — 5. 5. 2026 ráno

**Marti's vstup #1** (~5:30):
> *„Pro veskery business standardniho charakteru se vyuziva Helios
> tabulek pro data. TabObdobi, TabCisZam, TabCisOrg, TabZakazka,
> TabDokladyZbozi, TabPohybyZbozi… Proste kde to slo jsou data v Helios
> tabulkach… Kde to neslo, jsou Data v nasich tabulkach, napr EC_Ukoly,
> EC_Dochazka…"*
>
> *„Helios ma svuj framework, a Centrala taky… V dobe, kdy jsem Centrala
> framework zprovoznoval a pouzivali jsme ho, tak Helios jeste 'Uzivatelske
> editory' nemel. My jo… Uz tehdy bylo mozne delat detaily zobrazeni dat
> (u nas se tomu rika jadro)…. a delat si pres jednoduchy select svoje
> prehledy… nad jejichz jednotlivymi zaznami - vetami se jadro
> zobrazuje…"*
>
> *„Levy stro zustal, tj prehled soudecku, je v tabulce myslim
> EC_CentralaMenu. Kliknutim na adekvatni soudecek se zobrazi pravy prehled.
> myslim EC_DELPHI_TabObecnyPrehled… Use case 1 je toto zobrazit v designu jako
> to dela Centrala a vlastne Helios… Ptej se dal…"*

**Claude → Marti** (otázky pro pokračování konzultace, prioritně pro
use case 1):

**Q1.** Strukturu `EC_CentralaMenu` — pošli mi schema (sloupce, FK, sample 5-10
řádků). Hierarchický `parent_id`? Per-role / per-tenant? Pořadí
(`Razeni`)?

**Q2.** Strukturu `EC_DELPHI_TabObecnyPrehled` — pošli mi schema. **Klíčová
otázka**: kde je uložený **SELECT** definující přehled? V samé tabulce
(varchar/nvarchar(MAX) sloupec)? V child tabulce `EC_DELPHI_TabObecnyPrehledDef`?
Nebo extern v Delphi resource?

**Q3.** Po kliknutí na soudeček — vazba `EC_CentralaMenu → EC_DELPHI_TabObecnyPrehled`
je **1:1** (jeden soudeček = jeden přehled) nebo **N:1** (víc soudečků
sdílí stejný přehled, jen jiné parametry)?

**Q4.** **Sloupce přehledu** — když mám SELECT, sloupce vznikají
automaticky z resultsetu, nebo jsou zvlášť definované (např.
`EC_DELPHI_TabObecnyPrehledSloupce` s `caption`, `width`, `format`,
`order_default`)?

**Q5.** **Jádro** — máš pro něj tabulku v frameworku (`EC_TabJadro` /
`EC_TabDetail` / podobně)? Jaký je vztah ze soudečku/přehledu?

**Q6.** Pro use case 1 — vyber **jeden konkrétní soudeček**, který
chceš v moderním zobrazení mít první (např. *„Kontakty — všichni"* nebo
*„Otevřené úkoly"*). Pošli mi:
- soudeček ID v `EC_CentralaMenu`
- jeho přehled v `EC_DELPHI_TabObecnyPrehled` (SELECT definice)
- 5-10 sample řádků z přehledu
- screenshot jádra (nebo popis polí v tabech)

To bude moje seed pro Marti-AI's first delivery.

**Q7.** Stylem — chceš, aby moderní Centrála 2 měla **stejnou metaforu**
(strom + přehled + jádro), jen s moderním UI (Tailwind, responsive),
nebo **přepracovat UX** od základu (Marti-AI navrhne dashboard layout,
search-first, ne tree-navigation)?

---

### Session 1.2 — 5. 5. 2026 ráno (po screenshotu Centrály v provozu)

**Marti's vstup #2**: screenshot Centrály — modul *„Systém"*, soudeček
*„Definice SQL pro přehledy"*. Tj. **sám editor frameworku**. Z toho
jsem získal anatomii. Aktualizace sekcí výš:

#### Nové poznatky o levém stromu (`EC_CentralaMenu`)

- **Rekurzivní hierarchie** potvrzená. Pod soudečkem *„Systém"* je
  expandovaný seznam ~20 podsoudečků (Uživatelé, Definice soudečků,
  Definice práv, Definice SQL, Definice komponent, Definice
  dynamických akcí, Logování, …).
- **Top-level moduly** (z viditelné části stromu):
  - **Vývoj SW**
  - **Oběh zboží**
  - **Zaměstnanci**
  - **Systém** (administrátorský — meta-definice frameworku)
  - **Úkolník**
  - **Poznámky k verzím Centrály**
- Tj. **business moduly + admin/system modul** vedle sebe. Marti-AI
  bude pravděpodobně mít *„svoje moduly"* (např. Marketing / Kampaně /
  AI dashboardy) jako další top-level větve.
- **Quick search** input nad stromem (vlevo nahoře v toolbaru) —
  hledání napříč stromem.

#### Nové poznatky o pravém přehledu (`EC_DELPHI_TabObecnyPrehled`)

**Sloupce přehledu *„Definice SQL pro přehledy"*** (= meta-tabulka):

| Sloupec | Význam |
|---|---|
| `ID` | technický PK |
| `Cislo` | business identifier (1, 4, 5, 10, 11, 12, …) |
| `Nazev` | display title (*„MenuStrom"*, *„Definované komponenty"*, …) |
| `InsertSQL` | SQL skript pro INSERT akci (volaný při *„Nový"* tlačítku) |
| `ID_Edit` | **FK na jádro** (= editační formulář), pravděpodobně do `EC_TabJadro` |
| `DefView` | definice SELECT pro čtení (target view / SQL text) |
| `UpdateSQL` | SQL pro UPDATE akci |
| `DeleteSQL` | SQL pro DELETE (např. *„DELETE FROM EC_…"*) |
| `CopySQL` | SQL pro *„Kopírovat větu"* akci |
| `RefreshType` | strategy refresh přehledu (0/1/2/...) |
| `RowMem` | bool — pamatovat si vybraný řádek po refresh? |
| `DeleteDir` | bool — direct delete bez potvrzení? |
| `DefViewSQLi…` | (oříznuto, pravděpodobně inline SELECT varianta) |

> **Poznámka k metadata komentářům**: pole `UpdateSQL` obsahuje text
> typu `//Číslo přehledu: 12\\` — embedded metadata v SQL skriptech.
> Centrála má **konvence** komentářů, které framework čte (ne jen
> dokumentační, ale strojově parsované).

**Klíčový pattern: 4 SQL skripty per přehled** = CRUD definice.
Centrála neimplementuje INSERT/UPDATE/DELETE genericky podle resultsetu
— **každý přehled má svoji vlastní logiku**. To je flexibilní (lze
volat stored procedure, audit log, post-action triggery), ale i
důvodná disciplína (každý přehled musí mít všech 5 SQL definováno
nebo NULL).

**Multi-tab UI** — toolbar pravého panelu má tabs *„Definice SQL jádra"*
+ *„Definice SQL pro přehledy"* + `+` (open new). User si paralelně
otevře víc soudečků. Marti-AI v moderní variantě může emulovat tabs
nebo nahradit za workspace pattern (multi-pane, dynamic).

**Top toolbar nad přehledem**: Document / Zpět / Dopředu / Nastav /
**Nový / Oprava / Smazat / Obnovit** / Úkolník / Žádná zakázka /
Notifikace.

- **Nový/Oprava/Smazat/Obnovit** = CRUD akce volající InsertSQL /
  UpdateSQL (přes jádro) / DeleteSQL / refresh.
- **Žádná zakázka** = global state widget — aktuálně vybraná zakázka
  jako kontext napříč přehledy (tj. open zakázka v jednom soudečku,
  v jiném přehledu vidíš jen řádky té zakázky?).
- **Notifikace** = upozornění (panel napravo).

**Dolní stavový řádek**:
- `103 ID ---` — vybraný řádek (Cislo=103 = *„Definice SQL"*)
- `Matej_NEW` — pravděpodobně database / scheme name?
- `89/1` — paginace (89 řádků celkem, 1. vybraný?)
- `Centrála Martin EC FireDAC 192.168.30.11;DriverID=MSSQL;Pooled=False;MARS=Yes | 2025 Development version`
- `Offline mode: 0` `SPID:; SPID:`

#### Nové poznatky o jádře

Jádro **má vlastní definici SQL** v paralelní tabulce — tab *„Definice
SQL jádra"* vedle *„Definice SQL pro přehledy"*. Tj. existuje **`EC_TabJadro`**
(nebo podobně) s vlastním schématem (asi DefView + InsertSQL + UpdateSQL
+ ID_Component pro layout).

**Vazba `EC_DELPHI_TabObecnyPrehled.ID_Edit → EC_TabJadro.ID`** — tj. NE 1:1
mezi přehledem a jádrem. Více přehledů může sdílet jedno jádro
(např. *„Aktivní kontakty"* a *„Archivované kontakty"* mají stejný
detail formulář, ale jiný SELECT v přehledu).

Příklad z screenshotu: řádek `Cislo=12 Definice práv soudečků` má
`ID_Edit=87`. Tj. existuje jádro #87, které edituje větu z tohoto
přehledu.

**Mapping table**: dle stromu *„Definice vazeb menu stromu s jádrem"*
— tj. existuje **N:M tabulka** mezi `EC_CentralaMenu`, `EC_DELPHI_TabObecnyPrehled`
a jádrem. Je to **flexibilní** — strom soudeček nemá rigid 1:1 na
přehled (jeden soudeček může otevřít víc variant, jeden přehled může
být v víc soudečkách).

#### Component model (z stromu *„Definice komponent"*, *„Přehled všech property komponent"*)

Centrála má **registr UI komponent** — pravděpodobně Delphi VCL
metadata (TButton, TEdit, TGrid, ComboBox, ...) + jejich **property
schema** (caption, font, datafield, validations). Jádro je
**komponentový formulář** — sestavený z komponent na canvas, každá
komponenta má properties.

To je pre-React era forma toho, co dnes děláme jako *„dynamic form
schema"* (JSON Schema, React-JSON-Schema-Form, atd.). Marti-AI v
moderní implementaci **může číst tu existující definici** a generovat
React/HTML formulář s identickými poli.

#### Akce a workflow (rozšíření sekce 3)

Nové soudečky ve stromě:
- **Definice popup menu přehledů** — right-click context akce per přehled
- **Definice dynamických akcí** — runtime akce (např. *„Vyrobit nabídku z kontaktu"*)
- **Definice parametrů dynamických akcí** — argumenty pro dynamické akce
- **Popis dynamických akcí** — dokumentační pole
- **Definice vazby z DLL** — externí Delphi DLL volání (custom logic)
- **Definice akcí formuláře** (řádek 117 v screenshotu)
- **Definice akcí - edit** (řádek 116)
- **Definice obarvovacích podmínek** — conditional row formatting

Tj. Centrála má **bohatou rozšířitelnost**:
- SQL skripty pro CRUD
- Dynamické akce (custom workflow per přehled)
- DLL volání (proprietary Delphi logic)
- Popup menu (kontextové akce)
- Conditional formatting (barvy řádků podle dat)

#### Permissions — 3 úrovně potvrzeny (sekce 5 update)

Z stromu Systém:
- **Definice práv - skupiny** — role definitions
- **Definice práv - skupiny - uživatelé** — user-role assignments
- **Definice práv soudečků** — soudeček-level (modul-level proxy)
- **Definice práv přehledů** — přehled-level (read-only / write / no access)

A **„Aktivní uživatelé"** (řádek 13 v screenshotu) — runtime view kdo
je přihlášený.

#### Logging

*„Logování - vše"* (řádek `EC_CentralaMenu`) — Centrála má **audit log**.
Co se loguje pravděpodobně: user akce, SQL executions, login/logout,
chybové stavy. Tabulka pravděpodobně `EC_Log*`.

#### Bottom-left ikony (🏠 ❤️ 🔘 💡)

- 🏠 **Home** — výchozí strom (full)
- ❤️ **Oblíbené** — saved soudečky per uživatel (~5 frequently used)
- 🔘 **Recent** — naposledy otevřené přehledy
- 💡 **Tipy** — kontextová nápověda?

---

## Aktualizovaná Helios paralela (rozšíření tabulky 6)

| Komponenta | Helios | Centrála 1 | Pozn. |
|---|---|---|---|
| Strom modulů | Editor stromu menu | `EC_CentralaMenu` (rekurzivní, per-user state) | Centrála měla dřív; per-user state v stromu samém (Oblibene, CisloZam) |
| Definice přehledu | Editor přehledů | `EC_DELPHI_TabObecnyPrehled` | 4 SQL (Insert/Update/Delete/Copy) + DefView |
| Definice jádra | Editor formulářů | **`EC_FormDef`** (potvrzeno 5.5.) | s `ID_Edit` FK z `EC_DELPHI_TabObecnyPrehled` |
| Vazba strom↔přehled↔jádro | Konfigurace menu | `EC_*Vazby*` (per *„Definice vazeb"*) | flexible N:M |
| CRUD operace | metoda na přehledu | InsertSQL/UpdateSQL/DeleteSQL/CopySQL | per-přehled custom |
| Komponenty | VCL .NET | VCL Delphi | per-component property |
| Dynamické akce | Externí akce | `EC_*DynamickeAkce*` | + DLL volání |
| Popup menu | Konfigurace | `EC_*PopupMenu*` | per přehled |
| Conditional formatting | Obarvení řádků | `EC_*ObarvPodminky*` | SQL CASE WHEN |
| Práva | 3-vrstvé (modul/přehled/sloupec) | 3-vrstvé (soudeček/přehled/skupina) | identický koncept |
| Audit log | logování | `EC_Log*` (předp.) | … |
| Self-hosting | ano | **ano** (Modul Systém) | bootstrapped framework |

---

## Doplňující otázky po screenshotu

**Q8. ✅ ZODPOVĚZENO 5.5. ráno** — Tabulka jádra = **`EC_FormDef`**
(Form Definition). Marti potvrdil přes screenshot dialogu *„Definice
SQL jádra"* pro Cislo=119 (= *„Definice dotazů pro editaci vět"*):

```sql
--//Číslo přehledu: 119\\
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED
SELECT * FROM EC_FormDef Order by DatPorizeni desc
SET TRANSACTION ISOLATION LEVEL READ COMMITTED
```

**Klíčové insighty z této ukázky**:

1. **Tabulka `EC_FormDef`** je zdroj všech jader napříč Centrálou.
   Jeden řádek = jedno jádro = jeden detailní formulář.
2. **`DatPorizeni` sloupec** existuje (audit timestamp).
3. **Read uncommitted pattern** — SQL skripty Centrály wrappují SELECT
   v `READ UNCOMMITTED` pro UI fluency (no waiting on locks, dirty
   reads OK pro display) a resetují na `READ COMMITTED`. To je
   konvenční pattern pro ERP frameworks. Marti-AI by to měla
   **zachovat** v moderní variantě (per-přehled SQL skripty drží
   ten pattern), nebo nahradit za `WITH (NOLOCK)` hint.
4. **Komentář `--//Číslo přehledu: 119\\`** — embedded metadata. Tj.
   framework parsuje SQL textem a hledá tento marker, aby věděl,
   k jakému přehledu skript patří. Marti-AI to **nemusí parsovat** v
   moderní variantě (vazba je v `EC_DELPHI_TabObecnyPrehled.ID_Edit`), ale
   pro audit / dump / migration je dobré marker zachovat.

**Anatomie vazby strom → přehled → jádro** je teď jasná:

```
EC_CentralaMenu (soudeček)
  └→ EC_DELPHI_TabObecnyPrehled.ID_Edit (FK)
       └→ EC_FormDef (jádro)
            ↓ DefView SELECT
            ↓ + komponenty (lookup z EC_*Komponenta*)
            ↓ + akce (lookup z dyn. akcí + popup menu)
            └→ render detailní formulář
```

Doplňující otázky pro Q8.x:

**Q8a.** Schema `EC_FormDef` — pošli `EXEC sp_columns 'EC_FormDef'` +
sample 3 řádky (např. ID=87 *„Definice práv soudečků"*, ID=140
*„Komponenty"*, ID=4 *„Definované komponenty"*).

**Q8b.** Má `EC_FormDef` vlastní InsertSQL/UpdateSQL/DeleteSQL pro CRUD
své edit věty? Tj. když user otevře jádro EC_Kontaktu a klikne *„Uložit"*,
vykoná se `EC_FormDef.UpdateSQL` (`UPDATE EC_Kontakt SET …`)?

**Q8c. ✅ ČÁSTEČNĚ ZODPOVĚZENO 5.5. ráno** — Komponentový layout =
**`EC_FormDefComponent`**. Marti potvrdil přes screenshot dialogu
*„Definice komponent"* pro Cislo=4 (*„Definované komponenty"*):

```sql
--//Číslo přehledu: 4\\
SELECT * FROM EC_FormDefComponent
```

**Anatomie** je teď úplná:

```
EC_FormDef            (1) ← header jádra (DefView SELECT, CRUD SQL, název)
   ↓ 1:N
EC_FormDefComponent       ← komponenty (UI elements + properties)
                            např. TButton, TEdit, TGrid, TabSheet,
                            TLabel, TComboBox, TDateTimePicker, ...
```

To je elegantní pre-React/pre-XAML form schema. **JeDelphi VCL paralel
to React/Vue component tree v JSON Schema, ale staré 19 let.**

Doplňující otázky pro Q8c.x:

**Q8c.1.** Schema `EC_FormDefComponent` — pošli `EXEC sp_columns
'EC_FormDefComponent'` + sample 5-10 řádků pro **jedno konkrétní jádro**
(např. WHERE ID_FormDef = 140 = *„Komponenty"*, nebo lépe pro EC_Kontakt
jádro). Sloupce které mě zajímají:
- `ID_FormDef` (FK na master)
- `Razeni` / `Pozice` (order v rámci formuláře)
- `TypKomponenty` / `ComponentType` (TButton / TEdit / TGrid / ...)
- Layout: `Top`, `Left`, `Width`, `Height` (Delphi pixel coords)
- `Caption` / `Hint` (display text)
- `DataField` (vazba na sloupec resultsetu DefView)
- `Validations` / `ReadOnly` / `Required`
- Tabs: `ID_Parent` / `TabSheet_ID` (nesting komponent ve struktuře)

**Q8c.2.** **Property komponent** — strom má i řádek *„Přehled všech
property komponent"* (pravděpodobně tabulka `EC_FormDefComponentProperty`
nebo podobně). Tj. `EC_FormDefComponent` může mít **další 1:N tabulku
properties** (key/value pairs pro flexibilní rozšíření). Schema?
Příklad?

**Q8c.3.** **Tabs / nesting** — když jádro EC_Kontakt má tabs (Základní /
Akce / Dokumenty), je každý tab vlastní komponenta s
`Typ='TTabSheet'` a child komponenty mají `ID_Parent` na něj?

---

### ⚠ Q8c korekce 5.5. ráno — `EC_FormDefComponent` je LEGACY / balast

Marti potvrdil přes screenshot dialogu *„Přehled všech property
komponent jádra"* (Cislo=157) že **aktivní pattern je 3-vrstvý**, ne
2-vrstvý:

```sql
--//Číslo přehledu: 157\\
SELECT F.Nazev, F.ID AS ID_FormEdit, C.ID_Form, C.Typ, C.cCaption,
       C.ID AS ID_Comp, C.Smazana, P.*
FROM EC_FormDefEditProperty P
LEFT OUTER JOIN EC_FormDefEdit C ON C.ID = P.ID_FormDefEdit
LEFT OUTER JOIN EC_FormDef F ON F.ID = C.ID_Form
ORDER BY F.ID, C.ID
```

Plus Marti's slova: *„Pozor, v tom form def komponent je balast... Ted
uz se ty zakladni property co tam vidis nepouzivaji... Vsechny component
property jdou z teto tabulky."*

#### Aktualizovaná anatomie (3-vrstvý komponent model)

```
EC_FormDef (F)                  ← header jádra
  • ID, Nazev, DefView (SELECT), CRUD SQL, DatPorizeni, …
  ↓ 1:N (přes EC_FormDefEdit.ID_Form FK)
EC_FormDefEdit (C)              ← komponenta (header)
  • ID (PK)
  • ID_Form (FK na EC_FormDef.ID)
  • Typ (TButton, TEdit, TGrid, TTabSheet, ...)
  • cCaption (display text)
  • Smazana (soft delete flag)
  ↓ 1:N (přes EC_FormDefEditProperty.ID_FormDefEdit FK)
EC_FormDefEditProperty (P)      ← všechny ostatní properties komponenty
  • ID, ID_FormDefEdit (FK na C.ID)
  • + key/value sloupce (Top, Left, Width, Height, DataField,
    Font, ReadOnly, Required, Validation, ...)
  • Smazana (soft delete)
```

#### Klíčové vzory

1. **2-vrstvá komponenta**: `EC_FormDefEdit` (header s typem a captionem)
   + `EC_FormDefEditProperty` (rozšíření přes key/value). Tj. komponenta
   má vždy minimal header v `Edit` a libovolně bohaté properties v `EditProperty`.
2. **`Smazana` soft delete** — patří do auditu. Marti-AI by neměla
   ignorovat řádky s `Smazana=1`, ale **filtrovat je** (`WHERE Smazana=0`)
   v render dotazech, jinak uvidí mrtvé komponenty.
3. **`cCaption`** prefix — Centrála používá konvenci typu `c*` pro
   character (string) sloupce (Delphi ad-hoc Hungarian notation?).
   Marti-AI to může ignorovat a renderovat jako `caption`, ale stojí
   za to vědět při schema reading.
4. **`EC_FormDefComponent` zůstává v DB** kvůli back-compat / audit /
   migration history, ale **nečíst z ní** pro live render. Označit
   jako *„legacy"* v rendering pipeline.

#### Helios paralel (rozšíření tabulky)

| Komponenta | Helios | Centrála 1 (aktivní) | Centrála 1 (legacy) |
|---|---|---|---|
| Definice jádra header | EditFormulárů (master) | `EC_FormDef` | `EC_FormDef` |
| Komponenty jádra | Vlastnosti formuláře | `EC_FormDefEdit` | `EC_FormDefComponent` ⚠ |
| Property komponent | per-component config | `EC_FormDefEditProperty` | (in-row v `EC_FormDefComponent`) ⚠ |

#### Doplňující otázky pro Q8c.x (rozšíření)

**Q8c.4.** Schema `EC_FormDefEdit` — pošli `EXEC sp_columns
'EC_FormDefEdit'` + sample 5 řádků pro **jedno konkrétní jádro**
(EC_Kontakt). Sloupce které vidím z screenshotu:
- `ID` (PK)
- `ID_Form` (FK na EC_FormDef.ID)
- `Typ` (component type)
- `cCaption` (display text)
- `Smazana` (soft delete)

Plus pravděpodobně `ID_Parent` pro nesting tabů?

**Q8c.5.** Schema `EC_FormDefEditProperty` — `EXEC sp_columns
'EC_FormDefEditProperty'` + sample 10-20 řádků pro **jednu komponentu**
(WHERE ID_FormDefEdit = …). Klíčové sloupce které čekám:
- `ID, ID_FormDefEdit, Smazana`
- Layout: `Top, Left, Width, Height`
- Data binding: `DataField`, `Lookup_*`
- Visual: `Font`, `Color`, `Visible`, `Enabled`, `ReadOnly`
- Validation: `Required`, `MinValue`, `MaxValue`, `RegExp`
- Behavior: `OnClick`, `OnChange` (event handler název / DLL ref?)

**Q8c.6.** Konkrétní příklad pro EC_Kontakt — pošli mi *„dump"* všech
komponent jeho jádra:

```sql
-- 1. Najdi jádro pro EC_Kontakt
SELECT TOP 5 ID, Nazev, DefView FROM EC_FormDef
WHERE Nazev LIKE '%Kontakt%' OR DefView LIKE '%EC_Kontakt%';

-- 2. Vezmi ID, dump komponenty
SELECT C.ID, C.Typ, C.cCaption, C.Smazana
FROM EC_FormDefEdit C
WHERE C.ID_Form = <ID> AND C.Smazana = 0
ORDER BY C.ID;

-- 3. Pro vybranou komponentu (např. první TGrid nebo TabSheet)
SELECT P.* FROM EC_FormDefEditProperty P
WHERE P.ID_FormDefEdit = <C.ID> AND P.Smazana = 0;
```

**Q9.** **Vazby strom↔přehled↔jádro** — kde je ta tabulka? V stromě
vidím *„Definice vazeb menu stromu s jádrem"*. Schema?

**Q10.** **Komponenty** — `EC_*Komponenta*` table. Jaké property má
komponenta (caption, font, datafield, validation)? Příklad: jak
vypadá editační formulář pro EC_Kontakt? (Pole + jejich definice.)

**Q11.** **Dynamické akce** — popíš mi 1-2 reálné dynamické akce, které
se denně používají. Např. *„Vyrobit nabídku z kontaktu"* — kde je
definovaná, co dělá (SQL? DLL?)?

**Q12.** **Obarvovací podmínky** — example. *„Faktura po splatnosti =
červená"*? Je to SQL CASE WHEN v DefView nebo separátní config?

**Q13.** **Globální state**: *„Žádná zakázka"* widget v toolbaru — když
otevřeš zakázku, propaguje se ID do **všech přehledů** jako filter
implicit? (Tj. otevřu zakázku 12345, pak otevřu *„Doklady zboží"* a
vidím jen řádky pro zakázku 12345?)

**Q14.** **Notifikace panel** — co tam přijde? Připomínky úkolů? Email
příchozí? Schvalovací notice?

**Q15.** **Top-level moduly** v stromě — mám 6 viditelných (Vývoj SW,
Oběh zboží, Zaměstnanci, Systém, Úkolník, Poznámky). Má Centrála 1 ještě
další top-level (Ekonomika, Obchod, Sklad, Personalistika), nebo je to
**vše v Helios** (Centrála 1 obsluhuje jen co Helios neumí)?

---

## Implikace pro Marti-AI / Centrála 2

### Pro use case 1 (zobrazit jako Centrála)

Modern web equivalent layout:

```
┌─────────────────────────────────────────────────┐
│ Centrála 2 — Marti-AI workspace      [search]   │
├──────────┬──────────────────────────────────────┤
│ 🌳 STROM │ TAB1 [×] · TAB2 [×] · + new tab     │
│          │                                      │
│ ▼ Modul  │ ┌──────────────────────────────┐    │
│   ▶ A    │ │ ⚡ Akce: Nový | Oprava | …  │    │
│   ▶ B    │ ├──────────────────────────────┤    │
│ ▼ Modul  │ │ PŘEHLED (DataGrid)           │    │
│   ▶ A    │ │ ID Cislo Nazev …             │    │
│   ▶ B    │ │ 1                            │    │
│          │ │ 2                            │    │
│ 🏠❤️🔘💡 │ ├──────────────────────────────┤    │
│          │ │ JÁDRO (detail vybrané věty)  │    │
│ Žádná    │ │ tabs · fields · save / cancel│    │
│ zakázka  │ └──────────────────────────────┘    │
└──────────┴──────────────────────────────────────┘
```

**Tech stack návrh** (Recommended):
- HTML/Tailwind/Vanilla JS (konzistentní s STRATEGIE), žádný React build
- Sidebar tree (recursive, collapsible) z `EC_CentralaMenu`
- DataGrid v pravém pane — Tabulator.js nebo custom HTML <table>
- Modal/sidebar pro jádro (per komponentový generator)
- Klient strana fetchuje data přes nový API endpoint
  `/api/v1/centrala/strom`, `/api/v1/centrala/prehled/{id}`,
  `/api/v1/centrala/jadro/{id}/{vetaid}`
- Backend čte DB_EC přes existující `eurosoft_query_table` MCP tool
  (nebo přímo SQL Server connection v cloud APP, pokud chceme rychlejší)

**Marti-AI side** — *„originální zobrazování"*:
- Když user řekne *„otevři kontakty"*, Marti-AI fetchne `EC_CentralaMenu`
  (najde soudeček *„Kontakty"*), pak `EC_DELPHI_TabObecnyPrehled`
  (DefView SELECT), execute dotaz, vrátí HTML/PDF dashboard.
- Nebo ji uživatel zeptá *„kolik kontaktů PLC"*, ona použije
  `eurosoft_query_table('EC_KontaktKategorieCis')` najde ID=N pro PLC,
  pak `eurosoft_count_rows('EC_Kontakt', filter=...)`, vrátí
  **doménový insight** (*„132 PLC kontaktů, 28 nových za poslední
  měsíc, 4 čekají na první kontakt"*).

To je rozdíl mezi *„fetcher"* a *„analyst"*.

