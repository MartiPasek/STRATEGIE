# Systém ceníků pro kalkulace — analýza + návrh (STRATEGIE)

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Systém ceníků pro kalkulace — analýza + návrh (STRATEGIE)

> Zadání (Marti 2.7.2026): ceníky dodavatelů jsou základ pro kalkulace položek; potřebujeme
> na to systém ve STRATEGII. Projít adresář `Ceniky` (Marti-AI složka) + strukturu `DB-Ceniky`
> z EUROSOFTu a buď ji použít, nebo navrhnout lepší.

## Co je zdroj (adresář `D:\Data\ZZ_Marti-AI RW\Ceniky`)

17 XLSX ceníků dodavatelů (raw zdroj), pravidelně aktualizované s platností:
Eaton, Finder, Harting, LAPP, MBS, Murr, Phoenix Contact, Pilz, Rittal, Rockwell, Schneider,
Siemens, SOCOMEC, WAGO, Weidmüller, Woehner + **PrevodniTabulka.xlsx** (mapování/převod).
Názvy: `<Výrobce>_...platný od <datum>_JV_<datum>.xlsx`. Velké (Siemens 46 MB, MBS 20 MB…).

## Jak to řeší EUROSOFT (`DB-Ceniky`, 7 tabulek) — dobrý, prověřený model

**Import XLS (staging + parsování):**
- `EC_ImportXLSHlav` — hlavička per soubor: `Vyrobce` (kód 5 zn.), `CenyCZK`, `PlatnostOD/Do`,
  mapování sloupců (`EC_PC`/`EC_NC`/`EAN` = indexy), `Sloupec01-50` (syrové), workflow
  (`Zpracovano`, `DatZpracovani`), cesty souboru, `PocetPolozek`, vazba na Helios.
- `EC_ImportXLS` — řádky: `IDHlav`, `Sloupec01-50` (syrové), + parsované: `RegCisHeo`
  (normalizovaný katalog. kód), `EC_PC` (ceníková), `EC_NC` (nákupní/netto), `Rabat_N/P`,
  `MJ`, `BaleniPo`, `MinDod`, `Mena`, `EAN`, `Popis`, `HmotnostKg`, `RegCisHeoKompres/Kod`
  (pro párování), `Par1-3`.

**Cenotvorba (vzorce):**
- `EC_CenikyVzorce` + `...Par` — per ceník (IDCenik) uspořádané (`Poradi`) SQL-výrazové vzorce:
  `NazevCilSloupce` ← `Vzorec` z parametrů `@P01-@P12` (= syrové sloupce). Např.
  `RegCisHeo = 'EAT ' + SUBSTRING(@P13,1,3) + ' ' + SUBSTRING(@P13,4,3)`, `EC_NC = @P05/@P04`.
- `EC_CenikyDefaultVzorce` + `...Par` — defaultní šablony per org (nový ceník je zdědí).
- `EC_CenikyNastaveni` — globální (CenyCZK…).

**Podstata:** generický engine „naimportuj libovolný XLS → syrové staging sloupce → per‑dodavatel
sada výrazových vzorců → normalizovaná pole (kód, ceny, popis…) → párování přes RegCisHeo do
kalkulace." Velmi flexibilní (každý dodavatel má jiný formát XLS).

## Doporučení: KONCEPT PŘEVZÍT, implementaci zmodernizovat

Model je výborný a prověřený — nevymýšlet znovu. Pro STRATEGII (PostgreSQL, tenant) navrhuju:

1. **`tenant.cenik_import`** (hlavička) — vyrobce, mena, platnost_od/do, zdroj_soubor,
   mapovani (jsonb), zpracovano, pocet_polozek, created_by/at. (= EC_ImportXLSHlav)
2. **`tenant.cenik_polozka`** (řádky) — import_id, `raw jsonb` (místo Sloupec01-50 — bez limitu
   50, flexibilní) + normalizovaná typovaná pole: `kat_kod` (RegCisHeo), `kat_kod_norm`
   (pro párování), popis, `list_price` (EC_PC), `net_price` (EC_NC), rabat, mj, baleni,
   min_dod, ean, hmotnost, mena. (= EC_ImportXLS)
3. **`tenant.cenik_vzorec`** — per výrobce/import uspořádané transformační pravidla
   (cil_pole, vyraz, poradi) + `tenant.cenik_vzorec_default` (šablony per výrobce).
4. **`tenant.cenik_prevod`** — PrevodniTabulka: mapování kódů dodavatel ↔ interní komponenta
   (pro párování do kalkulace).
5. **Napojení na existující kalkulační engine** (`tenant.kalk_*`, /kalkulace, `@@KALK*`) —
   ceníky = zdroj ceny komponent (net cena dle kat_kod), kalk engine dělá CC×rabat→cena +
   koef→VKM/Arbeit. Ceníky = cenová vrstva, kalk = kalkulační vrstva.

**Zlepšení oproti EUROSOFT verzi:**
- **Bezpečný výrazový engine** místo dynamického SQL (`Vzorec` běží jako dynamické SQL = riziko
  + neportovatelné). Navrhuju evaluátor podporující Martiho `@P` syntaxi + whitelist funkcí
  (SUBSTRING/CONCAT/dělení/REPLACE/CAST) → jeho existující vzorce se přenesou skoro 1:1, ale
  bezpečně a v Pythonu/PG.
- **JSONB syrové sloupce** (bez pevného limitu 50).
- **Verzování/platnost** — víc ceníků per dodavatel v čase, aktivní dle data.
- **Import XLS naší cestou** (už umíme parsovat XLSX; velké soubory přes upload/stream, ne bridge).
- Tenant-scoped, audit, párování na komponenty.

## Otevřené otázky (pro Marti + konzultaci Marti-AI = cenotvorba)
- **Vzorce:** přenést Martiho SQL‑výrazový styl přes bezpečný evaluátor (doporučeno,
  zachová jeho know-how), nebo strukturovanější mapování? 
- **Migrace:** přenést stávající vzorce + importy z DB-Ceniky, nebo začít čistě z XLS složky
  (a vzorce nastavit znovu)?
- **PrevodniTabulka:** jak přesně mapuje (dodavatel kód → interní)? Projít její obsah.
- **Kdo ceníky udržuje** (JV dělá v EUROSOFTu) → role + UI pro import/aktualizaci.


