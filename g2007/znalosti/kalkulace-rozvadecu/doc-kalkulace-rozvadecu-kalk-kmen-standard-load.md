# kalk_kmen jako STANDARD z Excelu — schéma, mapování, loader

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# kalk_kmen jako STANDARD kalkulace z Excelu

**Autor: Claude-24 (Kristý), 23. 7. 2026.** Přebudování `proj.kalk_kmen` z „sync indexu z Centrály" na **nosič STANDARD kalkulace nahrané z Excelu**.

## Oprava datové mapy: schéma je `proj`, ne `tenant`
Nativní ceníky i kalkulace žijí ve schématu **`proj`** (`proj.cenik_polozka`, `proj.kalk_kmen`, `proj.kalk_koef` …), NE v `tenant`, jak uvádí `doc-kalkulace-rozvadecu-datova-mapa-tabulky`. V `tenant` jsou jen zrcadla z Centrály (prefix `ec_`).

## Nové schéma kalk_kmen (23.7.2026)
Přidáno 10 sloupců (req #1365): `id` (bigint identity, **nový PK**), `vyrobce`, `oznaceni`, `k_arb`, `k_vkm`, `hmotnost_kg`, `excel_soubor`, `excel_list`, `excel_radek`, `excel_pozice` (int). Původní: `kmen_ec_id`, `reg_cis`, `nazev`, `skp`, `jednotka`, `zdroj`, `synced_at`.

**PK swap (req #1370):** starý PK `kalk_kmen_pkey` byl na `kmen_ec_id` (NOT NULL) → nová data z Excelu nemají EC vazbu, proto: DROP CONSTRAINT → `kmen_ec_id` DROP NOT NULL → PRIMARY KEY přehozen na `id`. `nazev` se u Excel-loadu neplní (Bezeichnung jde jen do `oznaceni`); `kmen_ec_id` je u nových řádků NULL.

## Mapování z STANDARD sešitu (pevně dle Kristý — bere se podle POZICE písmene, ne labelu)
- A → `excel_pozice` (Pos.) · B → `oznaceni` (Bezeichnung) · C → `reg_cis` (Typ/Bestell.-Nr.) · D → `vyrobce` (Lieferant)
- **H (Koeffiz.) → `k_arb` I ZÁROVEŇ `k_vkm`** (stejná hodnota, čisté číslo 1 / 0.25 / 0.5 …)
- J → `hmotnost_kg` (Hmotnost) · dále `excel_soubor`/`excel_list`/`excel_radek`, `zdroj='STANDARD_xlsm'`, `synced_at=now()`

## Filtr řádků
Bere řádky s obj. číslem (C) obsahujícím číslici A vyplněným výrobcem (D != '.'). Výrobce-filtr vyřadí poznámky/oddílové řádky (např. „• díly … chybí v ceníku"). Skip listy: Poznámky, ukladani_data, Rešerše. Hlavička listu = řádek s „Typ / Bestell.-Nr." (řádek 5 nebo 6 dle listu), data pod ní.

## Provedený load
STANDARD `K260XXXXStandSiem_…_260107.xlsm`, 7 listů → **2 728 řádků** (Základní 807, ICOTEK 992, Rozšíření 484, Sie Schraube 170, Siemens 3SU1+ 139, Šínový 108, UL508A 28); 2 346 má koeficient (Šínový systém a část ostatních Koeffiz. nemají → NULL). DELETE+INSERT atomicky přes schvalovací banner.

## Opakovatelný loader
`scripts/kalk_kmen_standard_load.py <STANDARD.xlsm> [--out CLAUDE_SQL.sql] [--no-delete]` — z libovolného STANDARD sešitu vygeneruje `DELETE FROM proj.kalk_kmen; INSERT …` dle mapování výše. Schéma nemění, jen data. Přes most (`db=pg`) = write banner.

## Gotcha
`kmen_ec_id` byl PK+NOT NULL → nešlo ho udělat nullable, dokud je PK. Postup: DROP CONSTRAINT kalk_kmen_pkey → ALTER COLUMN kmen_ec_id DROP NOT NULL → DELETE → ADD PRIMARY KEY (id) → INSERT. Žádné cizí klíče na kalk_kmen neukazovaly (ověřeno), swap byl bezpečný.

