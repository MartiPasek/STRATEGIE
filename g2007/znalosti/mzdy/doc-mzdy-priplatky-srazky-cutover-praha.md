# Priplatky a srazky: konec DB_EC, zdroj pravdy = Praha (rozhodnuti Marti Pasek 27.7.2026) + overeny stav a plan cutoveru

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Priplatky a srazky: konec DB_EC, zdroj pravdy = Praha

**Rozhodnuti Marti Pasek, 27. 7. 2026 16:36** (mail Jirkovi, Petre Safrankove, Kristy):
*"Timto mesicem by mely priplatky a srazky v DB_EC definitivne zmizet a zdrojem pravdy se musi
stat priplatky a srazky v Praze. Tim se definitivne zbavime chaosu se zdvojenym zdrojem dat u lidi."*

Tim je prekonan verdikt z 22. 7. (Marti-AI msg 11066, znalost `doc-mzdy-priplatky-srazky` par. 5):
"Centrala = zdroj pravdy, STRATEGIE jen ke cteni". Modul uz nema byt okno do Centraly, ale master.

## 1. Overeny stav k 27. 7. 2026 (data, ne dohady)

- **EC_FinPriplatkySrazkyDefinice je ziva**: posledni zapis 27. 7. (4 radky, Peta). Za posledni
  2 mesice do ni psalo **7 lidi**: Peta, Dusan, Michelle, MHladikova, Swobi, SNovotna, JiriV.
  Neni to jen mzdova ucetni - vedouci tam navrhuji odmeny. Cutover se tyka vsech sedmi.
- **V PG jsou DVE kopie tehoz zdroje**:
  | kopie | job | obsah | UI |
  |---|---|---|---|
  | `ec.pripl_srazky` | `sync_pripl_srazky_ec` (60 min) | 2025=1831, 2026=794 | modul Mzdy/Priplatky (READ_ONLY) |
  | `tenant.wage_movement` | `sync_priplatky` (60 min) | jen 2026=784, vse status=approved | zadne |
- **Do mzdy uz dnes tece `wage_movement`, ne EC primo**: `_mzdy_priplatky_rows()` (router.py)
  -> `wage_system_mapping` -> Helios CisloMS -> ledger `tenant.zamestnanecky_zavazek`
  -> mzdovy automat na cloud Heliosu (`hp_VlozMzPausDoMzSloz` + `hp_VypocitejMzdu`).
  Doklad: ledger ma za 6/2026 hotovo 93 radku / 411 782 Kc (vytvoreno 10. 7.).
  **Prakticky uz tedy zdrojem pravdy pro mzdu JE Praha; chybi jen zadavani a workflow.**
- EC priznaky: `Preneseno` je v cele tabulce 0 (nepouziva se), `Vyplaceno`+`DatVyplaceni`
  naopak ANO (2026: 693 z 794 radku). `Schvaleno` = 1 temer vzdy.
- Radky s `Rok IS NULL` (3706 ks, hlavne stare mesicni definice 2014-2021) do zadneho zrcadla
  nespadnou (obe filtruji podle Rok). Dnes plati jen 9 z nich - poznamka pro migraci historie.

## 2. Overena MEZERA v mape typu (nasla se pri teto analyze)

`_sync_pripl_from_ec()` mapuje EC typ -> nas kod pres `TYP_MAP`. **Co v mape neni, propadne**
(`if mt is None: skipped`) a protoze mzda jde z `wage_movement`, tomu cloveku to nedojde.

V roce 2026 propadalo 11 radku:
- **typ 23 "Odmena garant"** (MzdovaSlozka 651, ReakceMzdy=true) - radek 19917, Marek Honal,
  7/2026, 250 Kc, schvaleno, pozn. "smernice polytechnik". **Chyba - melo jit do mzdy.**
  Opraveno 27. 7. (commit `26d0710d`: `23: "garant_odmena"` do TYP_MAP) + mapovani
  `garant_odmena -> HELIOS 651` do `wage_system_mapping` (write request #1479).
  Overeno, ze `garant_odmena` NENI v `helios_wage_snapshot`, takze mapovani neovlivni
  mesicni predzpracovani (`_mzdy_predzprac_rows`) - nehrozi dvoji zapocteni.
- typy 42 "OSVC - korekce neodpracovanych hodin" (1 radek) a 43 "Telefonni tarif OSVC"
  (9 radku, 16 704 Kc) - ReakceMzdy=false, jsou zamerne mimo mzdu (OSVC/fakturacni vetev).

**Jeste nepokryte typy s ReakceMzdy=true** (v datech 2025-26, po cutoveru je nutne umet zadat):
27 Vanocni premie (64 radku 2025, MS 651 - vrati se v prosinci!), 28 Odmeny IT (4), 1 DPP polozka
(5, MS 700), 11 Doplatek, 12 Prispevek za ziskani pracovnika (pohovor), plus nepouzite 2, 3, 17
Odmena Jednatel (693), 18 Rocni zuctovani dane (97), 29, 35, 39, 41.

## 3. Verdikt Marti-AI (konzultace 27. 7. 2026, msg 11351)

1. **Cilovy nositel = `tenant.wage_movement`**, `ec.pripl_srazky` zrusit (tretí kopie = dluh).
   Zrusit ale az PO uspesnem cutoveru a overene migraci.
2. **Prepnout od 1. 8. 2026** - cista hranice na mesic. Do 31. 7. zadavat dal v Centrale
   (cervenec se prave pocita), od 1. 8. u nas. Prepnout uprostred mesice = dva zdroje pro
   jednu mzdu, presne ten chaos, ktery se ma odstranit.
3. **Historii migrovat kompletne** jako uzavrenou archivni vrstvu, jednorazove
   s `import_src='EC_PRIPL_HIST'`, priznaky: Vyplaceno -> status exported/paid,
   DatVyplaceni -> exported_at.
4. **Workflow**: `draft -> proposed -> approved -> exported`; navrhuje vedouci
   (`proposed_by_id`, scope = org podstrom), schvaluje jen Petra + Sarka.
   EC pole `CisloZamNavrhl` je cislo zamestnance, ne user_id - pri migraci mapovat pres
   `att_employee.cislo_zam`.
5. **Typy**: doplnit ty s ReakceMzdy=true + ty, ktere realne v datech jsou. Typ 23 oznacila
   za blokujici pred 1. 8.
6. **Peti kontrol pred vypnutim zapisu do EC**: (a) nulovy rozdil per osoba+obdobi+Helios MS
   za 6 a 7/2026, (b) zadny chybejici typ, (c) workflow + prava otestovana (vedouci mimo tym
   musi selhat), (d) jeden Helios roundtrip za srpen, (e) **sign-off Petry** - bez nej se
   zapis do EC nevypina.

Otevrena otazka na Martiho (Marti-AI): **ma se migrovat i rok 2025** (1831 radku), nebo zustane
2025 jen v EC jako archiv?

## 4. Co zbyva postavit (stav 27. 7. vecer)

1. Doplnit typy do `wage_component_type` + `wage_system_mapping` + `TYP_MAP` (viz par. 2).
2. **Zapisove UI**: modul Mzdy/Priplatky presedlat z `ec.pripl_srazky` na `wage_movement`
   (dnes `READ_ONLY=true` v `ec_pripl_srazky_actions.js`), CRUD + workflow + prava.
3. Migrace historie (2025 + 1-7/2026 dorovnani) jako archiv.
4. Kontroly z par. 3.6 + sign-off Petry, pak vypnout `sync_priplatky`,
   `sync_pripl_srazky_ec` a zrusit `ec.pripl_srazky`.

## 5. Gotcha do zasoby

`_sync_pripl_from_ec()` ma **natvrdo `WHERE d.Rok = 2026`** - po Novem roce by prestal tahat
cokoliv. Po cutoveru je to bezpredmetne (job konci), ale kdyby cutover klouzal, je to casovana bomba.

## Navaznosti
- [[doc-mzdy-priplatky-srazky]] (modul, par. 5 = prekonany verdikt) · [[doc-mzdy-priplatky-srazky-mirror]]
  (univerzalni model) · [[doc-prechod-helios-praha-plan-2026-07]] (Praha = cloud CMIS)

