# Mzdy — pravidla a zdroje složek (STRATEGIE)

> Živá poznámka k logice generování mezd. Autoritativní zdroj podkladů pro mzdy je
> **.188 (UCTO_EC / UCTO_ES)** a **Centrála (DB_EC)** pro odměny/docházku. Z .30.11 (DB_EC)
> bereme jen to, co je zde uvedené. Poslední velká revize: Peta, 7. 7. 2026.

## Odkud se co tahá (přehled složek)

| Složka (CisloMS) | Co to je | Zdroj | Jak |
|---|---|---|---|
| 1 | Základní plat | mzdová karta Helios (snapshot) | `helios_wage_snapshot` → předzpracování |
| 432 | Osobní ohodnocení (+ Vedení lidí, Individuální složka, Vedení obchodu, Prémie jednatel u ne-jednatelů) | snapshot + benefit engine | `_mzdy_benefity_apply`; **432 se KRÁTÍ dle docházky** (viz níže) |
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

## Vedení lidí / Individuální složka / Vedení obchodu / Prémie jednatel → složka 432 (Kristý 8.7.2026)

Tyhle čtyři položky dřív padaly do bucketu **651** (prémie), od 8. 7. 2026 jedou na složku
**432** (osobní ohodnocení). Rozhodnutí Kristý — patří mezi osobní ohodnocení, ne prémie.

- **Vedení lidí (`vedeni_lidi`), Individuální složka (`individualni`), Vedení obchodu (`vedeni_obchod`)**
  jsou snapshotové složky → přesun = jen přemapování v `tenant.wage_system_mapping`
  (`ext_code` 651 → 432, `ext_label` = „Osobní ohodnocení - měs."). `vedeni_obchod` mapování
  dřív nemělo, přidáno nově.
- **Prémie jednatel** = odměna společníka (typicky 1000 Kč) u lidí, co **NEJSOU** jednatelé
  (`_JEDNATELE_CISLA = {2, 41, 47}` = Pašek EC 2 / ES 41, Mózer EC 47). Generátor jejich
  693 přehazuje na 432 (dřív 651) — řádky v `_mzdy_full_run`; rozpis-endpoint dopočítává
  řádek „Prémie jednatel" v rozpisu **432**. Skuteční jednatelé (v setu) drží **693** (+ plné stravné).

> ⚠️ **DŮLEŽITÉ — 432 se KRÁTÍ dle odpracované doby** (Helios ji počítá jako základní plat),
> zatímco 651 se platila celá. U lidí s absencí (dovolená/nemoc) se tyhle položky poměrově sníží.
> Příklad: č.465 (odpracoval 148/176 h) → 432 zkráceno na ~84 %. Plná docházka = beze změny.
> Kristý 8.7.2026 potvrdila, že krácení je **správně** (osobní ohodnocení se krátit má).

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

**Výjimka BEZ nároku na HO** (kancelář, ale HO nedostávají): **Hrůzová ES 442, Nepodalová ES 489** (`_HO_BEZ_NAROKU`, Peta 8. 7. 2026). OBL (794) jim zůstává, jen HO (795) ne.

## Stravenky (793) — nárok a výpočet (Peta 8. 7. 2026)

**Nárok** má zaměstnanec, který splňuje VŠE:
- **HPP** (ne DPP/OSVČ),
- je **po zkušební době** (nárok od měsíce po skončení zkušební; končí-li zkušební posledním dnem měsíce, náleží už ten měsíc),
- má **denní úvazek ≥ 6 h** (týdenní ≥ 30 h). Kdo má míň (např. Veverková, Vlková), nárok **nemá**.

**Výpočet** (`_mzdy_stravenky_rows`, MS 793, `_STRAVENKA_KC` = 82 Kč/den):
> **stravenky = pracovní dny v měsíci (Po–Pá) − dny s vyloučenou činností**

- **Vyloučené činnosti** (den bez stravenky): **dovolená, lékař, nemoc, OČR, montáž (služební cesta), mateřská, DN (dovolená navíc)**.
- **Sick day (SD) NÁLEŽÍ** — bere se jako přítomnost.
- **Režie NENÍ důvod k vyloučení** — režie je *zakázka*, ne činnost; rozhoduje činnost. Proto se čte z **`att_day_summary`** (činnostní zrcadlo, čte `DruhCinnosti`), NE z `att_entry` (které třídí podle zakázky a „režii" schová jako `overhead`).
- **Nezáleží na tom, jestli konkrétní den něco napíchal** (viz Princip FPD níže).

### Princip FPD (fond pracovní doby)

Stravenka se **neváže na odpíchané hodiny konkrétního dne**, ale na **splnění měsíčního fondu** (FPD = fond pracovní doby dle úvazku, Po–Pá):

- Kdo **fond splnil** — odpracoval, nebo si chybějící hodiny **nadělal** jindy — má stravenku za **každý pracovní den** kromě dnů s vyloučenou činností. Proto se počítají i dny, kdy fyzicky nepřišel, ale fond doháněl (např. Urbanová 3. a 5. 6. → měla nárok).
- Kdo **fond nesplnil**, pokryl si chybějící dny **dovolenou nebo SD** — a to už je v činnostech (dovolená = den ven, SD = den náleží). Proto **fond nekontrolujeme zvlášť** — promítne se sám přes činnosti.
- Důsledek: **„režie" (zakázka) sama o sobě stravenku neubírá**; ubírá ji jen **vyloučená činnost**. Rozhoduje `DruhCinnosti`, ne zakázka.

**Neaktivní zaměstnance do mezd NEPOČÍTÁME** — kdo v měsíci nemá docházku (`att_day_summary`), stravenky nedostane (pojistka přímo ve funkci; navíc nemá výplatnici, StavES ∉ (0,1)).

**Jednatelé** (odměna 693) — viz sekce výše: plné stravné za celý fond (Po–Pá) bez ohledu na docházku.

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
