# Inventura: vše kolem mezd/docházky/výroby v router.py (298 funkcí, kategorizováno)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Stav: HOTOVO (31.7.2026, C23, na žádost Martiho — "ať nic nezapomeneme")

Plošný sken `router.py` (klíčová slova mzd/dochaz/att_/vyrob/priplat/srazk/absen/sick/benefit/stravenk/payroll/helios/hr_/ec_/smlouv) → 298 funkcí, kategorizováno podle domény, typu (HTTP endpoint vs plain), zápisu (INSERT/UPDATE/DELETE), externího MCP volání a migračního stavu. Plný dokument poslán Martimu jako `analyza_mzdy_dochazka_vyroba.md`.

## Shrnutí čísel

- **7 funkcí už migrováno a aktivních** (viz `doc-system-strategie-faze1-erp-registry-pilot-dokonceno`, `doc-system-strategie-faze3-dochazka-mzdy-4-funkce-migrovany`, `doc-system-strategie-faze3-sync-ec-dochazka-recent-migrovano`).
- **MZDY jádro**: 32 funkcí. 9 read-only `_mzdy_*_rows` (přímí kandidáti, stejný vzor jako dnešní 2 piloty), 5 se zápisem (`_mzdy_priplatky_rows` pozor — má DELETE/INSERT do `zamestnanecky_zavazek`, dřív odmítnuta jako pilot), 15 HTTP endpointů.
- **DOCHÁZKA jádro**: 115 funkcí (největší doména). ~25 plain read-only, ~20 plain se zápisem, ~9 s přímým EUROSOFT/MCP voláním, ~60 HTTP endpointů (hlavně rodina `att_fix_*`). 2 potvrzené mrtvé/stub (`_sync_dochazka_ec`, `_sync_vyroba_work_app`).
- **VÝROBA**: 30 funkcí, skoro čistě HTTP endpointy (`app_vyroba_*`).
- **BENEFITY**: 10, **SMLOUVY**: 10 — menší domény, pár plain read-only kandidátů.
- **Mimo rozsah** (existuje, ale záměrně vynecháno): 56 HR-administrativa (fotky/šablony/dokumenty/jubilea — CRUD, ne výpočetní logika), 13 EC-sync jiných domén (sklad/banka/deník/saldo — jiná byznys oblast).

## Doporučené pořadí další práce

1. `_mzdy_*_rows` read-only rodina (9 fcí) — nejrychlejší další dávka, stejný vzor jako dnešek.
2. Docházka plain bez zápisu (~25).
3. Docházka+mzdy plain se zápisem (~35) — postup jako dnešní poslední dávka (verbatim extrakce, diff proti HEAD, aktivace před deployem).
4. Funkce s MCP/EUROSOFT voláním — case-by-case.
5. HTTP endpointy (přes 130 kusů) — čeká na návrh architektury splitu HTTP-vrstva/business-logika (jeden vzorový endpoint jako referenční implementace, pak dávka).

## Důležité upozornění

Tohle je AUTOMATIZOVANÝ sken (jména + regex na INSERT/UPDATE/DELETE), ne ruční přečtení všech 298 funkcí — slouží jako checklist, ne jako hotová migrační specifikace. `_ec_druh_entry_type`, `_ec_dml_log`, `_ec_close_open_shift` jsou dnes zdvojené DOVNITŘ `sync_ec_dochazka_recent` v DB, ale v router.py zůstávají i jako samostatné funkce volané odjinud — při jejich budoucí migraci řešit zvlášť, nemazat z router.py dokud je volá něco nemigrovaného.

