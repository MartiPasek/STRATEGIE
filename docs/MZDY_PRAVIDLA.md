# Mzdy — pravidla a zdroje složek (STRATEGIE)

> Živá poznámka k logice generování mezd. Autoritativní zdroj podkladů pro mzdy je
> **.188 (UCTO_EC / UCTO_ES)** a **Centrála (DB_EC)** pro odměny/docházku. Z .30.11 (DB_EC)
> bereme jen to, co je zde uvedené. Poslední velká revize: Peta, 7. 7. 2026.

## Odkud se co tahá (přehled složek)

| Složka (CisloMS) | Co to je | Zdroj | Jak |
|---|---|---|---|
| 1 | Základní plat | mzdová karta Helios (snapshot) | `helios_wage_snapshot` → předzpracování |
| 432 | Osobní ohodnocení / Landmark korekce | snapshot + benefit engine | `_mzdy_benefity_apply` |
| 651 | Prémie / příplatky / odměny (bucket) | viz níže (základ + loajalita + zakázky) | více zdrojů, `_mzdy_consolidate` je sečte |
| 693 | Odměny společníků / jednatelská odměna | **Centrála** (typ 17) | `att_odmena_centrala` → `_mzdy_odmeny_rows` |
| 700 | DPP odměna | **Centrála** (typ 1 pevná, typ 3 hodinová) | `att_odmena_centrala` → `_mzdy_odmeny_rows` |
| 793 | Stravenkový paušál | docházka | `_mzdy_stravenky_rows` |
| 794 | Náhrada OBL (oblečení) | benefit systém | `_mzdy_benefity_apply` |
| 795 | Náhrada Home Office | benefit systém (napevno 6 dnů, viz níže) | `_mzdy_benefity_apply` |
| 953 | Srážka telefon | příplatky/srážky | `_mzdy_priplatky_rows` |
| 200/201/211 | Docházka (nemoc/OČR/dovolená) | naše docházka | `_mzdy_absence_rows` |

## Odměny z Centrály (typ → složka)

Zdroj: `EC_FinPriplatkySrazkyDefinice` (DB_EC / Centrála), zrcadleno při **`@@DOCHSUM <rok> <mesic>`**
do `tenant.att_odmena_centrala`, generátor `_mzdy_odmeny_rows` je skládá do mzdy.

Bere se, co je **schválené a AKTIVNÍ pro dané období** (PlatnostOd ≤ konec měsíce, PlatnostDo je
NULL nebo ≥ začátek) — pokrývá i opakující se (Měsíčně) záznamy vedené pod starším rokem.

- **typ 1** = DPP „Položka do dohody" (pevná částka) → **složka 700**
- **typ 3** = DPP hodinová (částka = Hodiny × Sazba) → **složka 700**
- **typ 17** = Odměna jednatele / společníka → **složka 693**

**Routing firmy:** přes `user_smlouva` (helios_cislo → firma). EC dostane jen své lidi, ES své.
DPP se daní srážkově 15 % (bez pojistného), jednatelská odměna 693 = plné pojistné + zálohová daň.

## Jednatelé / společníci (kdo má odměnu 693)

Osoby s odměnou 693 (jednatelé/společníci) dostávají v mzdě **odměnu (693) + PLNÉ stravné (793)**.
**NEdostávají** dovolenou/absenci (211/200/201), OBL (794) ani HO (795).

- **Plné stravné** = celý pracovní fond měsíce (Po–Pá) × sazba (`_STRAVENKA_KC`), NE jen napíchané dny.
  Dopočítává se napevno — protože jednatelé „nemají dovolenou", berou se jako plně přítomní.
  Platí v každé firmě, kde je jednatel generován (např. Pašek dostane stravné v EC i ES; Mózer taky).
- **Důvod vyloučení dovolené:** náhradu za dovolenou Helios neumí spočítat bez mzdového základu
  (průměrného výdělku) → bořilo to výpočet celé pásky.

Filtr je v generaci hned před `_mzdy_consolidate` (celková i jednotlivcová cesta).

## Prémie ze zakázek (651)

`SUM(OdmenazFinanciZak)` z `EC_Dochazka` (Centrála) za období (DatumPripadu) → zrcadlo
`tenant.att_finance_zakazek` (plněno při `@@DOCHSUM`) → generátor `_mzdy_finance_zakazek_rows`
→ přičítá do složky **651**. Routing firmy přes `user_smlouva`. Na výplatnici v rozpisu 651
řádek „Prémie ze zakázek". Může být i záporné (korekce).

## Loajalita (651)

Přesčas výroby nad fond → `_mzdy_loajalita_rows` → složka **651** (řádek „Loajalita (přesčas výroby)").
Kancelář (kategorie s dopichavat_fond) loajalitu nemá.

## Home Office napevno (795)

Kdo má **nárok na HO** (kancelář = skupina 24 + výjimky dílny, viz `_HO_DILNA_VYJIMKA`) má
**napevno 6 HO dnů** — nezávisle na self-service volbě. Engine to poměrově zkrátí podle
odpracovaného fondu (absence sníží). Kdo nárok nemá, HO nedostane.

## Lidé na běžné mzdové kartě

Kdo NENÍ v Centrále v příplatcích/odměnách (např. **Vlková 361**) → bere se z **mzdové karty
v Heliosu** (snapshot / smluvní podmínky). Nevadí, že nemá docházku.

## Ruční složky (fallback)

`tenant.mzdy_rucni_slozka` (durable, přežije přegenerování) → `_mzdy_rucni_rows`.
Příkaz **`@@RUCNI <firma> <cislo> <cislo_ms> <castka> [dny]`** založí/upraví (castka=0 = deaktivuje).
Používat jen pro to, co NENÍ v Centrále. **Pozor na dvojí započtení** — když jede člověk
z Centrály, ruční složku deaktivovat.

## Klíčové příkazy

- `@@DOCHSUM <rok> <mesic>` — zrcadlí docházku + prémie ze zakázek + odměny z Centrály do našich tabulek.
  (Kosmeticky spadne watcher AŽ po dokončení operace — data se zapíšou celá, hláška „WATCHER CRASH" je neškodná.)
- `@@MZDY <firma> <rok> <mesic> [CLEAN]` — generuje mzdy. **Dávkové** — opakovat (bez CLEAN),
  dokud počet hotových nepřestane růst. CLEAN vyčistí a postaví od nuly (nutné po změně složek).
- `@@RUCNI <firma> <cislo> <cislo_ms> <castka> [dny]` — ruční mzdová složka.

## Klíčové tabulky (tenant, PostgreSQL)

- `att_odmena_centrala` — odměny z Centrály (jednatel 693, DPP 700)
- `att_finance_zakazek` — prémie ze zakázek (651)
- `att_day_summary` — docházkové zrcadlo (fond, přesčas, absence…)
- `mzdy_rucni_slozka` — ruční složky (fallback)
- `helios_wage_snapshot` — zrcadlo mzdových karet Heliosu
- `user_smlouva` — mapování helios_cislo → firma (EC/ES), routing
