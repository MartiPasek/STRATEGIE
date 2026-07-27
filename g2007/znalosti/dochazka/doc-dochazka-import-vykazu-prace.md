# Import výkazu práce (Work Report xlsx) do docházky jako „Makat"

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Import výkazu práce (EUROSOFT Work Report .xlsx) do docházky

Pop-up menu přehledu **Docházka new** → **„⬆ Import z výkazu"**. Nahraje výkaz(y) NEBO je vezme přímo ze sdílené složky Dušana, ukáže **náhled**, po potvrzení založí docházku. Kristý + C24, 24.7.2026, commity `1bdccef2` (základ) → `2fb5aeeb` (složka) → `6c8c11aa` (model „Makat").

## ⚠️ MODEL: import = mobilní „Makat" (NE přímý zápis do vyroba_work!)
Import zakládá docházku **STEJNĚ jako když se člověk píchne na zakázku** (mobil „Makat" / „Přidat záznam" v Opravách), tj. do DVOU vrstev:
1. **`tenant.att_entry`** = přítomnost → **MZDA**. Práce (`entry_type work`) + **pauza** (`entry_type break`) jako samostatné záznamy. `source='import'`, `status='approved'`, `is_active=false`, `created_by_id`.
2. **`tenant.work_alloc`** = úsek na zakázce (`source='import'`) → přeteče do `tenant.vyroba_work` (zakázky). Po zápisu se volá `_sync_vyroba_work_app(frm,to)`, takže se úsek hned objeví v Docházka new.

Po zápisu se pro každý dotčený (employee, den) volá `_att_automat_recalc_day` (fond).

> **Dřívější verze (do 24.7. dopo.) zapisovala rovnou do `vyroba_work` (source_system='app') — ŠPATNĚ:** dalo to zakázku, ale NE mzdu, a nebylo to v Opravách docházky. Přepsáno na model výše. Prvních 12 test-řádků (Valenta 77 + Porner 83) se muselo smazat (byly bez mzdy + hrozilo zdvojení při foldu).

## Pauza (klíčové pro mzdy)
Výkaz dává čistou práci (buňka C) a rozpětí od–do (D/E). Pauza = rozpětí − čistá práce. Den se rozseká jako „Makat": **práce (půl čisté) + pauza uprostřed + práce (druhá půl)**, součet práce = čistý čas. Př. 06:00–14:30, pauza 0,5 → work 06:00–10:00 + break 10:00–10:30 + work 10:30–14:30 = **8 h práce + 0,5 h pauza**, konec 14:30. Helper `_dzt_day_segments`.

## Pojistky proti dvojí mzdě (jako fix/add)
- **Uzamčený měsíc** (`_att_period_locked`) → řádek `error`, přeskočí se.
- **Překryv s existující docházkou** (`_att_fix_overlap` nad celým rozpětím) → `duplicate`, přeskočí se. Tím je import **idempotentní** (druhý běh téhož výkazu = překryv → přeskok) a chrání lidi, co už píchali.
- Zakázka u práce musí být `pichatelna` (jinak `error`). Rezie (`zakazka='Rezie'`) → `is_rezie`, work_alloc se nefolduje do vyroba_work (rozpad jen na reálné zakázky).
- Činnost: `H`=„Činnost č." → `vyroba_cinnost.ec_cislo`, fallback název. Bez činnosti se přítomnost založí, ale na zakázku se nepromítne (fold chce `cinnost_id NOT NULL`) → varování v náhledu.

## Endpointy (`modules/erp/api/dochazka_zak_tab.py`)
- `POST .../import-vykaz` (multipart, `commit` 0/1) — nahrané soubory.
- `GET .../import-slozka` — seznam .xlsx ze složky přes MCP.
- `POST .../import-vykaz-slozka` (`{files:[], commit}`) — vybrané ze složky.
Sdílená logika `_dzt_process_parsed` (náhled i zápis), `_dzt_import_run` (session + po-commit fond/fold). Gate `_dzt_can`.

## Sdílená složka Dušana
`\\192.168.30.11\Data\Vedouci vyroby\ImportDochazky` = lokálně `D:\data\Vedouci vyroby\ImportDochazky` na EC-SERVER2 (whitelistovaný RO root MCP). Čte se přes MCP `eurosoft_file_list`/`file_read` (base_override), jako bank_api/cenik_engine. Prohlížeč neumí předvybrat síťovou složku, proto se čte server-side.

## Parsování listu „Stunden"
`C2` jméno (zobrazení), `G5` číslo zam (párování → `att_employee`), `G2` výchozí zakázka, řádky 8..34: `B` datum, `C` čistá práce, `D` od, `E` do, `F` pauza, `G/H` činnost, `I` pozn, `J` zakázka. openpyxl (server-side dep).

## Koordinace
`dochazka-po-zakazkach.html` sdílí C26 (Peťa) — import je aditivní (menu + modal `#ovimp`), nezasahuje do jeho logiky.

