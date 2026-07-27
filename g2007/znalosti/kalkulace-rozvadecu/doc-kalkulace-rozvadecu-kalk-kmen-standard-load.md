# kalk_kmen jako STANDARD z Excelu — schéma, mapování, dedup, loader

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# kalk_kmen jako STANDARD kalkulace z Excelu

**Autor: Claude-24 (Kristý), 23.–24. 7. 2026.** `proj.kalk_kmen` = katalog dílů STANDARD kalkulace, plněný z Excelu. **Jeden díl = jeden řádek** (klíč `reg_cis`, UNIQUE).

## Oprava datové mapy: schéma je `proj`, ne `tenant`
Nativní ceníky i kalkulace žijí ve schématu **`proj`** (`proj.cenik_polozka`, `proj.kalk_kmen`, `proj.kalk_koef`, `proj.cena_zdroj` …), NE v `tenant` (tam jen `ec_*` zrcadla z Centrály). `doc-kalkulace-rozvadecu-datova-mapa-tabulky` píše chybně tenant.

## Schéma kalk_kmen
Sloupce: `id` (bigint identity, PK — req #1370), `reg_cis` (obj. číslo, UNIQUE index `kalk_kmen_reg_cis_uq` — req #1394), `oznaceni`, `vyrobce`, `k_arb`, `k_vkm`, `hmotnost_kg`, `cena_cc_ref`, `cena_nc_ref`, `rabatt_ref` (req #1365 + #1394), `excel_soubor`/`excel_list`/`excel_radek`/`excel_pozice`, `zdroj`, `synced_at`. `kmen_ec_id` nullable (nová data nemají EC vazbu), `nazev` se neplní.

## Mapování z STANDARD sešitu (pevně dle Kristý — podle POZICE písmene)
A→`excel_pozice` · B→`oznaceni` · C→`reg_cis` · D→`vyrobce` · **F(Einheitspreis)→`cena_cc_ref`** (ceníková) · **H(Koeffiz)→`k_arb` i `k_vkm`** · **I(Bemerkung)→`rabatt_ref`** (procenta vyextrahovaná z textu `^(\d+([.,]\d+)?)\s*%`, např. "74%; Federzug"→74; jinak NULL) · J→`hmotnost_kg` · **M(Einheitpreis)→`cena_nc_ref`** (počítaná cena vč. rabattu, MŮŽE být > cena_cc — potvrzeno Kristý). Pozor: sloupec G má header "Rabatt", ale jsou tam čísla (15/-42), NE procenta — rabatt je v I.

## Dedup — jeden díl = jeden řádek (rozhodnutí Kristý 24.7.)
Priorita listů: **Základní 2026 > Rozšíření 2025 > ICOTEK 2025** > Šínový systém > UL508A > Sie Schraube > Siemens 3SU1+ Metall. Když je `reg_cis` na víc listech, vyhraje list s vyšší prioritou; v rámci téhož listu (díl vícekrát) vyhraje řádek s koeficientem, pak s cenou, pak nejnižší `excel_radek`. Analýza potvrdila: 0 duplicit „jen mezi ostatními listy" (pravidlo pokrývá vše). 2728 syrových řádků → **1749 unikátních dílů**.

## Filtr řádků
obj. číslo (C) s číslicí, není hlavičkový zbytek; výrobce (D) vyplněný a != '.' (vyřadí poznámky typu "• díly … chybí v ceníku"). Skip listy: Poznámky, ukladani_data, Rešerše. Hlavička = řádek s "Typ / Bestell.-Nr.".

## Loader (opakovatelný)
`scripts/kalk_kmen_standard_load.py <xlsm> [--out CLAUDE_SQL.sql] [--rebuild]` (commit e674d468). Dedup dle priority + extrakce cena_cc/nc/rabatt. **default = idempotentní APPEND** (`INSERT … ON CONFLICT (reg_cis) DO NOTHING` — dohraje jen nové díly, katalog roste), **--rebuild = DELETE+INSERT**. Přes most (`db=pg`) = write banner.

## Otevřeno
Import-tlačítko v ERP (`POST /app/kalk/standard-import` upload xlsm, gate {Marti 1, Kristý 11, Eliška 34}, ON CONFLICT; přístup Elišky na /kalkulace; tlačítko v kalkulace.html tab STANDARD) — návrh připraven, čeká na stavbu. Číselník zdrojů ceny = `doc-kalkulace-rozvadecu-cena-zdroj-ciselnik`.

## Gotcha
1. Bridge má naivní write-detekci: dotaz začínající `WITH`/`SELECT` = read path a zakáže DELETE ("forbidden keyword"). DELETE s CTE napiš jako `DELETE … USING (subselect)`, ať začíná `DELETE`.
2. PK swap kmen_ec_id→id: kmen_ec_id byl PK+NOTNULL → DROP CONSTRAINT → DROP NOT NULL → PK na id (req #1370).

