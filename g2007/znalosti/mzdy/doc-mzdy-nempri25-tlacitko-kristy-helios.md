# NEMPRI25 (ošetřovné) — tlačítko pro Kristý: generování z Heliosu + ověření + stažení

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# NEMPRI25 (ošetřovné) — tlačítko pro Kristý: generování z Heliosu + ověření + stažení

**Oblast:** mzdy · **Zapsal:** Claude-26 (Marti), 20. 7. 2026
**Navazuje na:** `doc-mzdy-nempri25-ose-gotchy-podani` (proč ČSSZ zamítá + ruční záchyt).
**Stav:** ✅ živé a ověřené — Marešová bez ručního zadání účtu → ✓ ČSSZ 0 chyb.

## Co Kristý dělá (cesta k tlačítku)
**Výplatnice → „🧾 Dávky NP · ošetřovné → ČSSZ"** (tlačítko vedle „JMHZ → ČSSZ")
→ stránka **`/davky`** → sekce **„📁 Generovat z mzdového systému (Helios)"**:
vybrat firmu (EC/ES) → **Načíst přílohy** → u osoby **Generovat + ověřit** →
zelený banner „✓ ČSSZ 0 chyb" → **⬇ Stáhnout XML** → poslat do DS `5ffu6xk`
(nebo OSSZ Plzeň‑město). Účet Kristý psát nemusí — dotáhne se z Heliosu.

## Zdroj dat = Helios (kompletní), ne ruční záchyt
`generate_nempri_xml(firma, priloha_id, ucet=None)` → `load_nempri_priloha` čte
`TabMzPrilohaDnp` + **`TabMzPrilohaDNPRO`** (rozhodné období = 12 měsíců příjmů/
vyloučených dnů). Rozhodné období NIKDE jinde není → ruční záchyt (`tenant.davka_podani`)
ho nemá a pro OSE „vznik" tak sám o sobě neprojde. Endpointy:
`GET /app/davka/helios-list` (filtruje OSE = Helios `DruhDavky=1`),
`POST /app/davka/helios-generuj` (generuje + validuje + vrací XML/banner/filename).

## Tři věci, které rozhodovaly o přijetí (gotchy)

1. **Vztah ošetřované osoby (`kodRodVztah`).** Helios ukládá vlastní číselný kód
   (`Zadost_OS_Vztah` = „1"), ČSSZ chce kód z číselníku **CIS_RODVZTAH** (pattern
   `[0-9A-Z]{1,3}`). „1" i volný text „dítě" ČSSZ **zamítne** (kód 6 / XSD pattern).
   Řešení v `mzdy_nempri.py`:
   - `_download_rodvztah()` + `load_rodvztah_ciselnik()` stáhnou oficiální
     **CIS_RODVZTAH.xlsx** ze ČSSZ (parsuje se stdlib zipfile, cache, fallback = PL).
   - `_rodvztah_kod()`: platný kód číselníku → projde; Helios `HELIOS_VZTAH {"1":"PL"}`;
     volný text (dítě/syn/dcera…) → PL; jinak vynechá (XSD nepovinné).
   - **`PL` = potomek v přímé linii (dítě) — ověřeno u produkčního validátoru ČSSZ.**
   - Endpoint pro našeptávač: `GET /app/davka/ciselnik/rodvztah`.
2. **RČ ošetřované osoby.** `_rc_valid()` — 10místné musí být dělitelné 11 (po r. 1954),
   9místné = staré (bez kontroly). Když je RČ neplatné/placeholder, generátor
   **vynechá `rodneCislo` a spolehne se na `datumNarozeni`** (jinak ČSSZ kód 311).
3. **Platební spojení (pro OSE „vznik" POVINNÉ).** Helios ho v příloze **NEdrží**
   (`Platba_BankSpoj` prázdný, `Platba_Zpusob=1` = na účet). Účet zaměstnance je v
   **`TabMzdaNaUcetView`** (`CisloUctu` + `KodUstavu` = kód banky, dle `ZamestnanecId`).
   `_zam_ucet(cdb, zid)` ho dotáhne automaticky; ruční přebití přes pole v UI
   (`_parse_ucet`, formát `[předčíslí-]účet/kód`). Marešová = `247287648/0300`.

## Ověření přímo v tlačítku
`helios-generuj` i `generuj-xml` volají `epodani_validace.validate_xml_string(xml, test=True)`
→ UI banner: zelený „0 chyb" / červený s konkrétní chybou ČSSZ / oranžový „validátor
nedostupný". Stažení přes Blob (soubor `NEMPRI25_OSE_<firma>_<id>.xml`).

## Diagnostika přes most
- `@@NEMPRIGEN <firma> <priloha_id> [ucet]` — z Heliosu → build_nempri → ověří u ČSSZ.
- `@@NEMPRIDEMO` — demo Marešová. `@@EPVALSTR | <xml>` — validace stringu.
- Pozn.: `@@NEMPRIGEN`/`@@NEMPRIDEMO` už nejsou stíněné handlerem `@@NEMPRI` (fix 20.7.).

## Ověřeno
ES příloha 1053 (Marešová, OSE 06/2026), **bez zadaného účtu** → účet dotažen z
Heliosu → **✓ ČSSZ: 0 chyb**. Rozhodné období (12 měsíců), vztah PL, RČ dítěte OK.

## Pozn. k souběžné práci
Živá cesta pro Kristý je **Heliosový picker** (funkce `_zam_ucet`, `_rodvztah_kod`,
`helios-generuj`). Znalost `doc-mzdy-nempri25-ose-gotchy-podani` popisuje i variantu
ručního záchytu s `load_rozhodne_obdobi`/`zkontroluj_podani` — vznikla souběžně jinou
instancí; při další práci ověřit, že se obě větve v kódu nekříží.


