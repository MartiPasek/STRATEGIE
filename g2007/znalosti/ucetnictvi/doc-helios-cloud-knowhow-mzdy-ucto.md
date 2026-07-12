# Know-how: Cloud Helios (188.12) — co a jak vyplňovat / co se kam reportuje

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Know-how: Cloud Helios (188.12) — co a jak vyplňovat / co se kam reportuje

*Vznik 27. 6. 2026 (Claude id=23 + Marti). Žije a doplňuje se. Důvod: migrace Helios na
cloud SQL2025 s očistou — musíme vědět, která data jsou kritická (ČSSZ, daně) a nesmí
se ztratit, a co je naopak balast, který očistou vyhazujeme.*

## 1. Co cloud Helios drží (po očistě)

- **Účetní deník 2025** (`TabDenik`) — na úrovni účtů. Slouží pro obratovou předvahu,
  uzávěrku, kontrolní hlášení. **Není to plný doklad** — vazby na bankovní výpisy,
  pokladnu, úhrady, doklady zboží, zakázky jsou vynulované (saldokonto/párování =
  ve STRATEGII).
- **Mzdy 2025 + 2026** (kompletně, ~190 tabulek) — mzdový list, složky, kontace,
  kalendáře, paušály, srážky, daňové údaje, registrace zaměstnanců.
  **Mzdy = zdroj pravdy pro ČSSZ + daně → data se NESMÍ mazat.**
- **Organizace** (`TabCisOrg`) + **DIČ organizací** (`TabDICOrg`) — kvůli saldokontu
  a kontrolnímu hlášení v Heliosu. CRM detail (kontaktní osoby, bankspojení org,
  cenové úrovně) je vynulovaný → CRM patří do STRATEGIE.
- **Předkontace** (`TabUKod` hlavičky + `TabRadekUKod` řádky) — účtovací předpisy.
- **DPH** (`TabObdobiDPH`, `TabDPH`, `TabDPHDef`, `TabDanoveKlice`) — pro KH/přiznání.

## 2. 🔑 ZÁSADNÍ PRAVIDLO (Marti 27.6.): mzdy → ČSSZ → NEMAZAT

Když data odkazují na chybějící číselník (po očistě), jsou dvě cesty:
- **U MZDOVÝCH tabulek: ZRCADLIT číselník z office** (zachovat data). NIKDY nenulovat
  mzdové údaje — vykazují se na sociálku (ONZ přihláška/odhláška) a finančák.
- **U účetních/dokladových vyloučených věcí** (zakázka, středisko, doklady zboží):
  vynulovat referenci je OK — na report nejdou.

**Příklad, kde se to ukázalo:** `TabZamMzd.DuvodUkonceniPP` / `DuvodVypovedi`
(→ číselník `TabUkonPV`). To je **důvod ukončení pracovního poměru** = povinný údaj
**na odhlášce ČSSZ (ONZ)**. Když chybí číselník, NEnulovat hodnotu — zrcadlit `TabUkonPV`.
(27.6. jsem to nejdřív omylem vynuloval, pak vrátil přepnutím `TabZamMzd`+`TabMzNastupPP`.)

## 3. Mzdové údaje, které jdou na úřady (HLÍDAT — nemazat, raději zrcadlit číselník)

| Údaj | Sloupec / tabulka | Číselník | Kam se reportuje |
|---|---|---|---|
| Důvod ukončení PP | `TabZamMzd.DuvodUkonceniPP`, `DuvodVypovedi` | `TabUkonPV` | **ČSSZ ONZ (odhláška)** |
| Státní příslušnost / občanství | `TabCisZam.StatniPrislus`, `StatNarozeni`, mzdy `*_Stat`/`*Zeme` | `TabZeme` (ISO) | ČSSZ, cizinci |
| Zdravotní pojišťovna | (mzdové složky/registrace) | `TabZdrPoj` | ZP měsíční |
| Daňové údaje | `TabZamDan` + `TabZamDanR` | — | FÚ (roční zúčtování) |
| Banka výplaty | `*.BankSpojeni` | `TabBankSpojeni` | **NEjde na ČSSZ** — výplata jde přes STRATEGII, lze nulovat |

> Pozn.: měna/země u mezd — cloud Helios má `TabZeme` (52 zemí) + `TabKodMen` naseedované.
> CZ/SK/CZK tam jsou → tuzemské mzdy sedí. Nuluje se jen viset­ící cizí hodnota (anti-join),
> ne platná. U cizinců ověřit, že jejich země je v `TabZeme`.

## 4. Co je naopak balast (nulovat referenci OK — nejde na report)

- **Zakázka** (`CisloZakazky` → `TabZakazka`) — nákladové členění, ne report.
- **Středisko/útvar** (`Utvar`/`CisloUtvar` → `TabStrom`) — očista = jediné středisko 001.
- **Doklady zboží / systém A** (`IdDokladyZbozi`, `Obdobi`→`TabDokladyZbozi`) — vyloučeno.
- **Bankovní výpisy / pokladna / úhrady** v deníku — saldokonto je ve STRATEGII.
- **Tiskové formuláře** (`TiskovyForm` → `TabFormDef`) — jen šablona tisku.
- **Vozidla, příjmy/výdaje, nákladový okruh** — provozní, ne účetní jádro.

## 5. Jak se opravuje, když noční Helios skript hlásí FK chybu

Helios pouští **každé ráno** údržbový skript = validace VŠECH cizích klíčů
(`ALTER TABLE WITH CHECK CHECK CONSTRAINT`). Zastaví se na první chybě. **Neblokuje
provoz** — je to údržba. Postup opravy (detail v paměti `helios-cloud-fk-remediace`):

1. **Zjisti typ**: padá child → parent. Je parent prázdný, nebo má hodnoty (value-gap)?
   Je child sloupec NULLABLE? Je child **mzdová** tabulka (→ chraň data)?
2. **Mzdová tabulka** → zrcadli chybějící číselník: `@@XFER DB_EC UCTO_EC <Císelník>` (EC),
   `@@XFER DB_IS UCTO_EC1 <Císelník>` (ES). Data zůstanou.
3. **Účetní vyloučená vazba, nullable** → přímý anti-join NULL:
   `UPDATE c SET col=NULL FROM <db>.dbo.<child> c WHERE col IS NOT NULL AND NOT EXISTS(SELECT 1 FROM <db>.dbo.<parent> p WHERE p.<pcol>=c.col)`.
4. **NOT NULL detail → prázdný header** (master-detail) → zrcadli header z office.
5. Vždy EC (`UCTO_EC`) i ES (`UCTO_EC1`).

## 6. ✅ STAV 27. 6. 2026: OBĚ FIRMY PROŠLY noční validací čistě

EC (`UCTO_EC`) i ES (`UCTO_EC1`) projely Helios noční FK skript bez chyby. Cloud Helios
běží na očištěných datech (deník 2025 + mzdy 2025/26 + organizace + DPH + předkontace).

### Co se konkrétně udělalo (pořadí rodin, jak padaly):
1. **Organizace** `TabCisOrg` (zrcadleno 1992/1938) + očista CRM vazeb (kontakty,
   bankspojení org, cenové úrovně, forma dopravy/úhrady, jazyk — NULL).
2. **DIČ org** `TabDICOrg` (1772/1639) + ISO země NULL.
3. **Deník** — vynulovány vazby na vyloučené doklady (bank. výpisy, pokladna, úhrady,
   doklady zboží, zakázky, středisko, vozidla, currency-tag), ponecháno účetní jádro.
4. **DPH řetězec**: `TabDPHDef` → `TabDPH` (zrcadleno z office).
5. **Účetní číselníky země/měna** (anti-join TabZeme/TabKodMen) — TabSbornik,
   TabObdobiDPH, TabCisUctDef, TabCisZam.
6. **Období-orphan** seedované definice: smazány viset­ící řádky (TabDruhDokZboDef/PoDef/StromDef).
7. **Bankspojení** (73 dětí TabBankSpojeni) — NULL (výplata přes STRATEGII).
8. **Tiskové formuláře** (68 dětí TabFormDef, anti-join — má 899 seedovaných!).
9. **Předkontace řádky** `TabRadekUKod` (zrcadleno) + očista jeho vazeb (zakázka NULL).
10. **Master-detail mzdy** `TabZamDanR`→`TabZamDan` (zrcadlen header), `TabZamMzd`→zakázka NULL.
11. **Mzdový číselník** `TabUkonPV` (důvod ukončení PP) — ZRCADLEN (ČSSZ!), data obnovena.

### ✅ OVĚŘENÍ SPRÁVNOSTI (27.6.2026) — cloud = základ pravdy

Křížová kontrola cloud (UCTO_EC) × office (DB_EC), účetnictví 2025 (IdObdobi=39):
- **Deník 1:1**: 67 710 řádků, Σ MD = Σ DAL = **2 560 088 546,84** — identické na haléř.
- **Konta k 31.12.2025**: Σ MD = Σ DAL = **2 560 112 933,64** — identické na haléř
  (po správném srovnání — viz gotcha „středisková souhrnná řádka" níže).
- **HV EC 2025**: náklady (tř.5) 129 406 631,51 − výnosy (tř.6) 125 574 831,66 =
  **ztráta 3 831 799,85 Kč** → **sedí na číslo, které prezentovali účetní.** ✅
- **Princip ověřen** (Marti): cloud je *bez středisek*, ale na úrovni účtů dává
  **stejná čísla** jako office (středisko obrat účtu nemění).

**🔑 Gotcha „středisková souhrnná řádka" (TabKontaD):** office konta mají u každého
účtu DVĚ úrovně — **souhrnnou řádku (Stredisko prázdné/NULL)** + **střediskový detail**;
souhrn = součet detailů. Naivní `SUM` přes všechny řádky sečte obě → **2× u nákladů/výnosů**.
Při srovnání ber JEN souhrny (`Stredisko IS NULL OR ''`) NEBO jen detail, ne obě. Cloud
je bez středisek → má jen tu jednu (souhrnnou) řádku → je rovnou správně (vyrovnán na 0).

## 7. 🔑 KRITICKÉ GOTCHY (bez nich se to nepostaví znovu)

- **`DECLARE` proměnné UVNITŘ smyčky cursoru = bug.** Když kurzor jel obě DB
  (`SELECT 'UCTO_EC' UNION 'UCTO_EC1'`) a `DECLARE @t,@c` bylo v těle WHILE, druhá
  iterace (ES) spadla na re-deklaraci → **aplikovalo se jen na EC, ES zůstalo pozadu**.
  → Deklaruj proměnné JEDNOU před smyčkou, nebo dělej každou DB samostatným skriptem.
- **Anti-join přímým UPDATE, NE kurzor s `BEGIN TRY/CATCH`.** TRY/CATCH tiše spolkne
  chybu (trigger apod.) a NULL se neaplikuje, aniž to poznáš. Přímý
  `UPDATE c SET col=NULL FROM <db>.dbo.<t> c WHERE col IS NOT NULL AND NOT EXISTS(...)` je spolehlivý.
- **Cloud Helios má jen ČÁST FK** (5868 z 6000 office). Failující FK v cloud grafu
  často NEJSOU (Helios je teprve přidává) → **cloud-side sweeper je MINE**. Úplný
  zdroj vztahů = OFFICE FK graf (`DB_EC.sys.foreign_keys`, přes `db=mssql`).
- **Název sloupce ≠ název FK.** `FK__TabZamMzd__Zakazka` má sloupec **`Zakazka`**, ne
  `CisloZakazky` (to je parent sloupec). `FK__TabCisOrg__CenovaUrovenNakup` →
  sloupec `CenovaUrovenNakup`. VŽDY zjisti skutečný sloupec z `sys.foreign_key_columns`.
- **Empty-parent vs value-gap.** `TabFormDef` má 899 seedovaných řádků = value-gap
  (anti-join, ne blanket!). `TabBankSpojeni` prázdný = empty-parent (blanket NULL OK).
  Vždy ověř `count(*)` parenta.
- **Master-detail orphan**: NOT NULL detail (IDH/IDUKod) → prázdný header → zrcadli
  header z office (`@@XFER`). Scan všech naráz: cloud FK kde parent rows=0 + child
  rows>0 + child col `is_nullable=0`.
- **Mzdy `IdObdobi` → `TabMzdObd`, NE `TabObdobi`!** Nehledej orphany podle názvu
  sloupce (falešné poplachy 31k), vždy z FK definice.
- **`_xfer` LOB skip** (commit 525920d): ntext/image/varbinary se nezrcadlí → NULL.
- **Collation** table var vs sys katalog → `COLLATE DATABASE_DEFAULT`.
- **`_mssql188_query` běží v master kontextu** — `sys.columns`/`OBJECT_ID` bez 3-part
  prefixu míří na master, ne UCTO_EC! Pro cílovou DB použij 3-part nebo `USE`.

## 8. Helios konfigurace (cloud) — kde se co nastavuje

- **Registr databází Heliosu** = `UCTO_EC..TabDBHelios` (firma 1 = `UCTO_EC` Control,
  firma 2 = `UCTO_ES` System). `SysJmeno` = fyzický název DB, `Existuje` = ověření přes
  `DB_ID()`. **27.6. firma 2 přejmenována** `UCTO_EC1` → `UCTO_ES`:
  `ALTER DATABASE UCTO_EC1 SET SINGLE_USER WITH ROLLBACK IMMEDIATE; ALTER DATABASE UCTO_EC1 MODIFY NAME=UCTO_ES; ALTER DATABASE UCTO_ES SET MULTI_USER;`
  + `UPDATE UCTO_EC..TabDBHelios SET SysJmeno='UCTO_ES' WHERE ID=2`.
- **SuperHeslo pro uživatelské editory** (dialog „Potvrzení heslem" u Uživatelských
  editorů — chrání, aby tam nelezl kdokoli): `TabSetup.SuperHeslo`, **jen firma 1**
  (`UCTO_EC`), hodnota `'1'`. **Ostatní firmy ho DĚDÍ** — ES vlastní `TabSetup` nemá
  a nemá mít. Globální (jednořádková tabulka), nešifrované.
- **Globální systémová nastavení** = jednořádkové tabulky `TabSetup`, `TabHGlob`,
  `EC_GlobKonst`. **Per-user** nastavení = `TabUserCfg` (např. `SQLEditorZobrazeni/Spusteni`).
- **„Zobrazit SQL" v přehledu** (jak Marti vytáhl SQL dotazu) = funkce po zadání SuperHesla.

## 9. Otevřené / TODO

- **Doplnit do tabulky v §3, jak přesně se který údaj u nás (STRATEGIE) vyplňuje** — až
  budeme stavět mzdové/ČSSZ/daňové výstupy ve STRATEGII (to je hlavní účel tohoto know-how).
- Doparovací sync: po uzávěrce účetní jen kliknout a dopárovat změny 2025 (TODO #41).
- Pozn.: noční skript = nedestruktivní údržba, neblokuje provoz; teď projde čistě (EC i ES).


