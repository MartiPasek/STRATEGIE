# Benefity (samoobsluha v mobilu) jdou primo do mezd - bez historie, bez logu a bez ohledu na zamek mezd (10.9.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Volba benefitu, kterou si zamestnanec udela sam v mobilu, se pocita do jeho vyplaty -
a nikde po ni nezustane stopa.** Zaroven se u ni nekontroluje zamek mezd. Tri mezery najednou,
proto jsou pojmenovane v jedne znalosti a ne rozptylene.

## O co jde

V mobilni aplikaci je na obrazovce **Ukoly** dlazdice **Benefity** vedouci na stranku `/benefity`.
Clovek si tam sam nastavi, kolik dni v mesici chce **home office** a jestli chce **nahradu za
obleceni** - v mezich castky, kterou mu predem urci HR. Zalozil Marti 28.6.2026.

Smysl to ma. Jsou to danove zvyhodnene slozky mzdy- snizi dan, **ale zaroven snizi vymerovaci
zaklad na socialni pojisteni**, tedy budouci duchod a nemocenskou. To je osobni kompromis, ktery
za cloveka nikdo rozhodnout nemuze, proto samoobsluha.

## Tri mezery

### 1. Volba jde PRIMO do mzdoveho podkladu
Funkce `_mzdy_benefity_apply` v `router.py` cte `tenant.benefit_volba` podle roku a mesice
a promita HO dny i zapnute obleceni do podkladu. **Neni to informace, pocita se z toho vyplata.**

### 2. Zmena po sobe nenechava stopu
- Zapis je **prepis** (`ON CONFLICT DO UPDATE`), **historie se nikam neuklada**.
- Protokol mzdovych zmen `tenant.mzdy_zmena_log` sleduje **jedinou tabulku, `wage_movement`**;
  benefitu se netyka vubec (overeno dotazem, **0 radku**).
- HR ani rodicum **nechodi zadne upozorneni**.
- Dohledatelna je jen **posledni** hodnota, kdo ji ulozil (`user_id`) a kdy (`updated_at`).

➡️ **Clovek muze ovlivnit svou vyplatu, aniz o tom kdokoli vi.**

### 3. Zamek mezd se u benefitu nekontroluje
Funkce `_mzdy_zamek_blokuje` existuje a u **priplatku a srazek se vola**. U ulozeni benefitu
se **nevola vubec** (overeno ctenim kodu). K 10.9.2026 je pritom **zamceno** - zamek zalozila
Peta 8.9.2026. Volbu tedy jde menit i behem zpracovani mezd.

Navic **rok a mesic posila sama stranka** a server je nijak neomezuje, takze v principu jde sahnout
i na mesic zpatky. *(Overeno v kodu. NENI dolozeno, ze by to nekdo udelal.)*

## Co naopak funguje - tyhle tri pojistky drzi

Aby to nevypadalo deravé cele. Overeno v kodu-
- **cizi osobni cislo** server odmitne ("not your number", 403),
- **strop od HR** nejde prekrocit, server hodnotu orizne,
- **seznam vsech lidi** (`/app/benefity/lidi`) je jen pro HR, ostatni dostanou 403.

## Cisla k 10.9.2026

| co | kolik |
|---|---|
| vidi dlazdici v Ukolech | **83** (vsichni aktivni - dlazdice neni nijak omezena) |
| ma strop od HR | **41** |
| volbu opravdu udelalo | **41** lidi, 45 zaznamu, cerven az zari 2026 |
| bez stropu | **42** - od 9.9.2026 vidi jen vetu, ze pro ne nic nastavene neni |

"HR" je pro benefity- rodice (Marti, Kristyna) + Sarka Novotna a Petra Safrankova.

## Kde to zije

| co | kde |
|---|---|
| dlazdice v mobilu | dilek `20_home_phone_notifs.js` v `g2007.soubor`, vede na `/benefity` |
| stranka pro zamestnance | `apps/api/static/benefity.html` (git) |
| stranka pro HR | `/benefity-hr` |
| volby lidi | `tenant.benefit_volba` (prepis, bez historie) |
| stropy od HR | `tenant.benefit_limit` |
| napojeni na mzdy | `_mzdy_benefity_apply` |
| zamek mezd | `tenant.mzdy_zamek` + `_mzdy_zamek_blokuje` (u benefitu se NEVOLA) |
| uzel v ERP menu | `fw.menu_node` id 110 pod id 94 (Dochazka) |

## OTEVRENE - ceka na rozhodnuti

Nic z toho neni opravene. Jirka Honomichl 10.9.2026 rozeslal Martimu, Kristyne, Sarce a Petre
dotaz, **kam ma dlazdice patrit** (dnes je na Ukolech, coz mu neprijde vhodne) a jestli o zmenach
benefitu potrebuji vedet. Ve hre jsou tri cesty-
- **A** nechat a zavrit mezery (kontrola zamku + zapis do protokolu + upozorneni HR),
- **B** totez a navic dlazdici presunout pryc z Ukolu (doporuceno),
- **C** dat benefity z mobilu pryc a nechat je nastavovat HR na pozadani.

**Nez na to nekdo sahne, over aktualni stav** - tahle znalost popisuje stav k 10.9.2026.

## Jak to bylo overeno

Kod (`router.py`, funkce vyse), data (dotazy nad `benefit_volba`, `benefit_limit`,
`mzdy_zmena_log`, `mzdy_zamek`) a stranka v prohlizeci pod uctem Jiriho Honomichla.
Zjistil Claude-28 (Jirka Honomichl), schvalila Marti-AI (msg 15298).

