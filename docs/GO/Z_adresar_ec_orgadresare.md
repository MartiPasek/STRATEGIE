# Adresář dokladů: EC_OrgAdresare (Centrála přehled 115) + resolver EC_ZjistiAdresar

> Autor: Claude ID24, 19. 7. 2026, na pokyn Marti („Někde jsme to vytratili… už jsi to řešil zhruba před měsícem a půl. Prozkoumej to a udělej z toho znalostní dokument." + „je k tomu i nějaká EC_ procedura, která ten adresář podle přehledu a jádra dotáhne").
> Stav: autoritativní katalog definic adresářů Centrály + resolver, který z **typu dokladu / jádra + ID záznamu** složí fyzickou cestu ke složce. Řeší dřívější otevřenou otázku „proč `/app/dir/list` posílá record id (751137), ale složka se jmenuje po dokladu (EP26309)".
> Navazuje na [[Centrála — stavba jader]] (`doc-go-centrala_stavba_jader`) a [[přijaté poptávky]] (`doc-go-prijate_poptavky`).

## 1. Co je EC_OrgAdresare (přehled 115 „Definice adresářů a zkratek")
Jedna tabulka v DB_EC = **číselník definic adresářů**. Každý řádek = jedna třída dokumentů (doklad, zakázka, směrnice, karta zaměstnance…) a říká, **kam se její soubory ukládají a jak se jmenuje podsložka konkrétního záznamu**. Je to zároveň **most doklad ↔ jádro** (viz §5) — proto „adresář podle přehledu a jádra".

### Sloupce
| sloupec | význam | příklad (Poptávka) |
|---|---|---|
| `Zkratka` | **prefix složky** záznamu | `EP` |
| `Nazev` / `SysNazev` | lidský název / **systémový klíč** (resolver matchuje na `SysNazev`) | Poptávky / `PoptavkaP` |
| `Adresar` | **kořenová UNC cesta** (root) | `\\192.168.30.11\data\poptavky\` |
| `Podadresar` | **pravidlo podsložky** (viz §3) — NE hodnota, ale typ | `PoradoveCislo` |
| `Rada` | rozlišení variant téže zkratky (Směrnice 0..4, Neshody 0..3) | prázdné |
| `RadaDokladu` | číslo řady dokladu (900/910/920…) — spojka na `TabDokladyZbozi.RadaDokladu` | `900` |
| `Jadro` | **ID editačního jádra** (`EC_FORMDEF`) pro tento doklad | `3` |
| `Archiv` | archivní varianta | — |

**Klíčový řádek (Poptávka):** `Zkratka=EP · SysNazev=PoptavkaP · Adresar=\\192.168.30.11\data\poptavky\ · Podadresar=PoradoveCislo · RadaDokladu=900 · Jadro=3`.

## 2. Vzorec cesty
```
plná cesta = Adresar (root)  +  Podadresar (složka záznamu, složená dle pravidla §3)
```
Poptávka s PoradoveCislo=26309 →
`\\192.168.30.11\data\poptavky\` + `EP` + `26309` = **`\\192.168.30.11\data\poptavky\EP26309`** ✓

## 3. Pravidla podsložky (`Podadresar`) = slovník
Sloupec `Podadresar` nese **typ pravidla**, ne hotovou hodnotu. Resolver ho přeloží (CASE) na skutečnou složku:
| `Podadresar` | složka záznamu = | pozn. |
|---|---|---|
| `ID` | `Zkratka` + `@pID` (ID záznamu) | většina evidencí (úkoly, reklamace, faktury přijaté…) |
| `PoradoveCislo` | `Zkratka` + `PoradoveCislo` (z `TabDokladyZbozi`) | **doklady zboží** (poptávka EP+, nabídka EN+, obj. přijatá EB+…) |
| `CisloZakazky` | `CisloZakazky` | zakázky, podklady výroba, foto, ZL… |
| `CisloOrg` | `CisloOrg` | šablony ZL (`sab_ZL`) |
| prázdné + prázdné ID/Rada | `''` (přímý náhled do jednoho rootu) | `@DirectDir=1` — např. složka šablon |

⚠️ **Tady je rozřešení dřívějšího zmatku:** u dokladů zboží NENÍ složka pojmenovaná record-ID, ale **`Zkratka` + `PoradoveCislo`**. Record ID (`TabDokladyZbozi.ID`, např. 751137) je jen vstup, ze kterého resolver dotáhne `PoradoveCislo` (26309) a slepí `EP26309`.

## 4. Resolver — EC_ procedura, co „adresář dotáhne"
Procedury z DB_EC (nalezeno přes `sys.sql_modules` referencující `EC_OrgAdresare`):

### 4.1 `EC_ZjistiAdresar_NEW` — PRIMÁRNÍ (aktuální)
Vstup: `@pTyp` (přijímá **Zkratku i SysNazev**), `@pRada`, `@pID` (ID záznamu). Výstup OUT: `@pAdresar` (root), `@pPodadresar` (složka záznamu), `@pPomocneAdresare` (podsložky k založení).
Postup:
1. **Normalizace typu:** `SELECT @pTyp = ISNULL(SysNazev,@pTyp) FROM EC_OrgAdresare WHERE Zkratka LIKE @pTyp` → z `EP` udělá `PoptavkaP`.
2. **`Doklad`/`TabDokladyZbozi` vstup:** když voláš obecně přes doklad, dotáhne SysNazev přes `TabDokladyZbozi.RadaDokladu = EC_OrgAdresare.RadaDokladu`. (To je ta vazba „podle přehledu/dokladu".)
3. **Identifikátor dle typu:** pro `PoptavkaP`/`NabidkaV`/`ObjednavkaP`/`ObjednavkaV`/`DodaciList`/`FakturaP`/`PoptavkaV` → `SELECT @PoradoveCislo, @CisloZakazky FROM TabDokladyZbozi WHERE ID=@pID`. Pro zakázky → z `TabZakazka`.
4. **Dotažení definice:** `SELECT TOP 1 @Adresar=Adresar, @ZkratkaRady=Zkratka, @TypPodadresare=Podadresar FROM EC_OrgAdresare WHERE SysNazev LIKE @pTyp AND Rada=ISNULL(@pRada,'')`.
5. **Složení podsložky** (CASE dle §3), pak `@pAdresar=@Adresar`, `@pPodadresar=<složka>`.
6. **`@pPomocneAdresare`** = seznam podsložek, které se u záznamu automaticky zakládají (dle typu + `EC_GlobKonst.Firma='EC'` + data pořízení; u zakázek `DL, ZL, VP, CE, BEI…`).

### 4.2 `EC_ZjistiAdresar` — STARÁ varianta
Stejná myšlenka, ale `@pTyp` = **Zkratka** a matchuje `WHERE Zkratka=@Zkratka`. Stejný CASE (ID/CisloZakazky/PoradoveCislo). U zakázek odvozuje Zkratku z `LEFT(CisloZakazky,2)`.

### 4.3 `EC_Directory_GetRootDir` — jen root
`@Name`(SysNazev)+`@Series`(Rada) → vrátí pouze `Adresar` (kořen bez podsložky).

### 4.4 `EC_GetIDJadra` — doklad → jádro (EC_FORMDEF)
`@IDDoklad` → `EC_GetDokladType` (typ) → `SELECT @IDJadra = Jadro FROM EC_OrgAdresare WHERE SysNazev=@Typ`. **Tím je `EC_OrgAdresare.Jadro` oficiální spojka doklad→editační jádro.**

## 5. EC_OrgAdresare jako most doklad ↔ jádro (klíčové!)
Jeden řádek drží současně **řadu dokladu, adresář i jádro** → je to Rosetta mezi třemi světy:
```
TabDokladyZbozi.RadaDokladu ──┐
                              ├─ EC_OrgAdresare (řádek) ─→ Jadro ─→ EC_FORMDEF (editační formulář)
SysNazev (PoptavkaP) ─────────┘                        └─→ Adresar+Podadresar ─→ složka souborů
```
Ověřené páry doklad → Jadro:
| doklad | RadaDokladu | Zkratka | Podadresar | **Jadro** |
|---|---|---|---|---|
| Poptávky (přijaté) | 900 | EP | PoradoveCislo | **3** |
| Nabídky | 910 | EN | PoradoveCislo | 88 |
| Kalkulace | — | EK | PoradoveCislo (root nabídek!) | — |
| Přijaté objednávky | 920 | EB | PoradoveCislo | 10 |
| Objednávky vydané | 800 | EO | PoradoveCislo | 49 |
| Poptávky vydané | 940 | EVP | PoradoveCislo | 50 |
| Faktury přijaté | 500 | FP | ID | 111 |
| Dodací listy | 950 | DL | CisloZakazky\DL\DL<n> | 90 |
→ Poptávka `Jadro=3` **potvrzuje** vzor „Poptávky edit" (form 3) z [[Centrála — stavba jader]].

## 6. Speciální případy v resolveru (na co pozor)
- **Kalkulace sdílí adresář nabídky:** resolver u `Kalkulace` dotáhne `PoradoveCislo` z `EC_KalkulaceHlav→TabDokladyZbozi` a pak **`SET @pTyp='NabidkaV'`** → kalkulace i nabídka padnou do `\\…\data\nabidky\EN<poř>`. (Sedí s tím, že EK má `Adresar=\\…\data\nabidky\`.)
- **ZL:** podsložka = `CisloZakazky\ZL`. **DodaciList:** `CisloZakazky\DL\DL<pořadí>`.
- **ProhlaseniOS:** `CisloZakazky\zkoušky\Prohlášení o shodě`. **BankVypis:** podsložka = přímo `@pID`.
- **Zaměstnanci se skupinou SW** (Kristýna 12/2025): přesměrování `KZ→KZSW` (`\\…\Zamestnanci\Software\`).
- **Firma=EC** rozšiřuje `@pPomocneAdresare` (PLÁNY, ZL, zkoušky\… ) dle data pořízení zakázky.

## 7. Mapping na STRATEGIE = recept na duplikaci adresáře
`EC_OrgAdresare` (řádek) → **`tenant.dir_config` + `tenant.dir_config_storage`**:
| Centrála (EC_OrgAdresare) | → STRATEGIE |
|---|---|
| `SysNazev` (PoptavkaP) | `dir_config.sys_name` |
| `Zkratka` (EP) | `dir_config.short_code` |
| `Podadresar` (PoradoveCislo) | `dir_config.subfolder_rule` = `poradove_cislo` (ekvivalenty: ID→`id`, CisloZakazky→`cislo_zakazky`, CisloOrg→`cislo_org`, prázdné→`none`) |
| `Adresar` (`\\192.168.30.11\data\poptavky\`) | `dir_config_storage.root_path`, `backend=eurosoft_unc` |
| `RadaDokladu` (900) | `dir_config.series` (identita dokladu) |
| `Jadro` (3) | vazba na `fw.core` (které jádro edituje tento doklad) |

**Zásadní oprava STRATEGIE resolveru:** dnešní `directories.py resolve()` staví složku jako `short_code + entity_id` (record ID). Pro doklady zboží to musí být `short_code + PoradoveCislo` (= chování `Podadresar='PoradoveCislo'`), jinak míří na `EP751137` místo `EP26309`. Tj. resolver STRATEGIE musí u `subfolder_rule='poradove_cislo'` dotáhnout `PoradoveCislo` z `oz_prij_popt`/`TabDokladyZbozi` podle `id`, ne lepit id přímo. Endpoint `/app/dir/list?sys_name=poptavky&id=<recordID>` zůstává (posílá record id jako VSTUP), překlad na doklad dělá resolver — přesně jako `EC_ZjistiAdresar_NEW`.

## 8. Konkrétní setup pro Poptávku (core 195)
```
tenant.dir_config:         sys_name=poptavky, short_code=EP, subfolder_rule=poradove_cislo, series=900
tenant.dir_config_storage: root_path=\\192.168.30.11\data\poptavky\  (backend eurosoft_unc)
core 195 komponenta:       comp_type 311 (adresar), region adresar-RIGHT, dir_sys_name=poptavky
resolve(id) →              root_path + 'EP' + (SELECT PoradoveCislo … WHERE id=@id)  =  \\…\poptavky\EP26309
```

---
*Znalostní modul „Adresář dokladů — EC_OrgAdresare + EC_ZjistiAdresar" — Claude C24, 19. 7. 2026. Autoritativní číselník definic adresářů + resolver + most doklad↔jádro. Vzorec: root(Adresar) + Zkratka+Podadresar. Řeší record-id vs doklad-folder (EP26309).*
