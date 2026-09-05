# Docházka: model tabulek (att_entry / vyroba_work / att_day_summary) — jedna položková tabulka

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! POZOR - 5. 9. 2026 se tlacitko v mobilu PREJMENOVALO
> Tlacitko, kterym se v mobilni appce zahajuje prace, se jmenuje **START**.
> Do 5. 9. 2026 se jmenovalo "Makat" - rozhodl Jiri Honomichl. Vecne se nic nezmenilo,
> jen nazev; v textu nize je uz novy. Aktualni stav obrazovky:
> [[doc-dochazka-mobil-dochazka-prejmenovani-a-pravdivost-navodu-5-9-2026]]

> Ověřeno v živé DB přes SQL most. Původ Claude‑24 (Kristý) 28. 7. 2026; SJEDNOCENÍ dokončeno 29. 7. 2026 (C24, Kristý).
> Souvisí: doc-dochazka-vs-vyroba-separace, doc-dochazka-import-vykazu-prace, doc-dochazka-storno-vyroba-kaskada,
> doc-dochazka-opravy-prehled-ui, doc-mzdy-mzdy-podklad-zdroj-pravdy, doc-dochazka-dochazka-mirror-interval.

## ✅ STAV od 29. 7. 2026: JEDNA položková tabulka `vyroba_work` (work_alloc DROPnut)
`tenant.work_alloc` byla **zrušena** (DROP 29. 7. 2026, banner req #1546). Veškerá položková docházka
(úsek na zakázce/režii) žije nově JEN v **`tenant.vyroba_work`**. Záloha před DROP:
`tenant.work_alloc_zaloha_20260729` (1587 řádků) + Excel `work_alloc_zaloha_2026-07-28.xlsx`.

## Tři vrstvy (co je co)
- **tenant.att_entry** — DOCHÁZKA = čas a typ přítomnosti. Víc řádků na den = segmenty
  (příchod/práce/přestávka/absence/cesta), `entry_type_id`→att_entry_type, `started_at/ended_at`,
  `break_minutes`. Sloupec `hours` se u presence NEPOČÍTÁ z ruky (čas z časů). NENÍ hlavička dne.
- **tenant.att_day_summary** — DENNÍ HLAVIČKA se součty = MZDOVÝ PODKLAD
  (`cas_celkem/cas_montaz/cas_rezie/cas_prescas/cas_dovolena/cas_nemoc/cas_pauza/…`, `uzavreno`, `synced_at`).
- **tenant.vyroba_work** — JEDINÁ POLOŽKOVÁ tabulka „po zakázkách": `od/konec`, `zakazka_ref` × `cinnost_id`
  (→vyroba_cinnost) × `hodiny`, `datum`, `source_system`, `source_id`, měkký `att_entry_id`, `cislo_zam`,
  `zakazka_helios_id`. Podklad přehledu „Docházka po zakázkách", Makám/Čekám i výkazů.
  - **Běžící úsek** = `source_system='app' AND konec IS NULL`. (Bogus konec‑NULL z Centrály, např. činnost 27
    „Odměny fin.zakázek", NEjsou 'app' → scoping je nechává být.)
  - **Režie** = `zakazka_ref='Rezie'` (žádný `is_rezie` flag; rozhodnutí Kristý 28. 7.).
  - **Denorm názvy se NEUKLÁDAJÍ** — název zakázky joinem z `tenant.zakazka` (cislo→nazev), činnost/ikona
    z `tenant.vyroba_cinnost` (cinnost_id→name/icon). Klíče pro mobil (project_ref/project_nazev/
    cinnost_name/cinnost_icon/is_rezie/since) se dopočítávají v SELECTu.
  - `source_system`: 'app' (mobil), 'import' (výkaz), 'manual_fix' (Opravy), 'centrala1' (import Centrály).

## Zápisy (kdo píše do vyroba_work) — po sjednocení 29. 7.
- **Mobil „START"** (`_wa_open/_wa_close_running/_wa_running/_wa_latest_today`, router.py) píše/čte nativně
  vyroba_work (`source_system='app'`). Zavření: `konec=now()`, dopočítá `hodiny`. Anti‑parazit (<60 s úsek se
  smaže a nový převezme začátek) drží jako dřív.
- **Import výkazu** (`dochazka_zak_tab.py _dzt_process_parsed`) INSERT do vyroba_work, `source_system='import'`,
  `att_entry_id` = právě založený att_entry.
- **Opravy docházky** (`att_fix_entry/add/merge`, router.py) píší do vyroba_work; `att_fix_day` čte činnost
  z vyroba_work přes `att_entry_id` (fallback časové okno na `od`). ⚠️ Každý časově‑okenní zápis Oprav má
  `source_system<>'centrala1'`, aby oprava NEsáhla na EC agregát.
- **Import z Centrály** (`_sync_vyroba_work_ec`, `source_system='centrala1'`) běží dál (zakázka+činnost z EC).

## Dedup EC agregátu (proti dvojímu započtu) — překlíčováno 29. 7.
App fold `_sync_vyroba_work_app` je **ZRUŠEN** (stub, nevolá se). Dedup, který dřív dělal fold i
`_sync_vyroba_work_ec` přes `work_alloc`, je nově v `_sync_vyroba_work_ec` klíčován na **app řádky ve
vyroba_work** (`source_system='app'`): pro (cislo_zam, den) s app činností se EC agregát (DruhCinnosti=4)
NEimportuje. Bez toho by se app lidem sečetl nativní řádek + EC agregát.

## ⚠️ Past: platnost v att_entry drží `status`, NE `is_active`
Skoro vše je `is_active=false` (živé jen otevřené mobilní píchačky). Platný záznam =
**`status<>'superseded'`** (pending/approved/confirmed/imported). Filtr přes `is_active` → součet ~nula.

## Přehled „Docházka po zakázkách" / Docházka new
Data_set `fw.data_set` **`dochazka.zakazky_vse_list`** (jádro dochazka.centrala, uzel 189) — hlavní zdroj
vyroba_work; sloupec `PraceAktivni` počítán z `konec IS NULL AND DruhCinnosti<>27 AND datum=CURRENT_DATE`.
Fallback subquery na work_alloc **ODSTRANĚN** 29. 7. (běžící úseky jsou nově přímo ve vyroba_work).

## Sumace do att_day_summary — kdy/jak
DNES se NEpočítá z naší docházky. `att_day_summary` = živé 1:1 ZRCADLO `EC_Dochazka_SumaDen` ze staré
Centrály, job `sync_ec_dochazka_sumaden` (`fw.mirror_job`), 10 min, enabled. Opačný směr vypnut od 29. 6.

## Migrace 5→11 (co se stalo 29. 7. 2026) — audit trail
1. Data migrace 749→1522 řádků work_alloc → vyroba_work (source_system='app', source_id).
2. Přesměrování zápisů (mobil/import/opravy) → vyroba_work (commit e6ff07c9).
3. Reconciliace 11 stale běžících app řádků (migrace zkopírovala běžící; zdrojový work_alloc už zavřený)
   dle `source_id → work_alloc.ended_at` (banner #1541).
4. Vypnut app fold + rekey dedup; krok 8 `_refresh_employee_active` bez work_alloc; fold stub (commit ffc46a35).
5. Data_set zakázky_vse_list bez work_alloc fallbacku (banner #1544).
6. Záloha work_alloc_zaloha_20260729 (#1545) → **DROP TABLE tenant.work_alloc (#1546).**
Nemigrováno (zaniklo DROPem, v záloze): 65 vad (32 nulových + podezřelé >16 h + časové) + 3 běžící.

## Vize / otevřené (cílový stav mzdového podkladu — NEspojovat s tímto tahem)
- Součty času mezi vrstvami se DNES nerovnají (att_day_summary = Centrála, att_entry/vyroba_work = naše).
- Pořadí: 1) srovnat att_entry proti Centrále (Plnění FPD pro Dušana), 2) přepnout mzdový podklad ze zrcadla
  na naši att_entry (jen s Marti + Petrou), 3) vypnout zápis v Centrále (`att_source_pref.app_only`+`ec_blocked`).
- Fáze 2 docházkových typů absencí (Překážka 138, Volno 60 %, Mateřská/Otcovská, Nařízené/Náhradní, Ostatní
  s náhradou) — založit typy + `_DRUH_ABSENCE`, viz plán.

