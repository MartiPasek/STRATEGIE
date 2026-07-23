# Schéma `proj` + úklid kalkulačního know-how (22.7.2026)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schéma `proj` + úklid kalkulačního know-how (22.7.2026)

## ✅ PROVEDENO (22.7.2026 večer)
- **Schéma `proj` založeno.** Role **`Marti-AI` je natrvalo superuser**.
- **Přesunuto do `proj` (data intaktní, SET SCHEMA = metadata):** **10× `proj.kalk_*`** (kalk_kmen, kalk_koef, kalk_cena, kalk_rabat, kalk_regcis_def, kalk_sestava(_pol), kalk_skupina(_pol), kalk_std_stage) + **5× `proj.cenik_*`** (cenik_polozka 539 459 řádků, cenik_import, cenik_vyrobce, cenik_vzorec, cenik_cena_medi).
- **Ceník produkčně, bez view:** 41 odkazů `tenant.cenik_` → `proj.cenik_` ve 3 souborech (`cenik_engine.py`, `router.py`, `kalkulace_engine.py`), nasazeno (commit `df8e66c9f`). 0 DB funkcí/views na starém `tenant.cenik_`.
- **NEpřesunuto (správně):** `ec_*` zrcadla — nejsou čistě kalkulační, sahá na ně celý ERP; `proj.kalk_*` si je čte přes schéma.

## Rozhodnutí o schématu (Marti, 22.7.2026)
Jedno schéma **`proj`** = domov pro **řízení a vedení projektů** (výhledově celá firma). Prefixy: **`proj.kalk_*`** (kalkulace) + **`proj.cenik_*`** (ceník) + do budoucna **`proj.plan_*`/`proj.zakazka_*`/`proj.ukol_*`** (provoz, dle „všechno je plán" — `doc-vp-ai-rizeni-vize`).

## Úklid — VERDIKTY (finalizováno 22.7. večer, ověřeno kódem)
- **NECHAT:** celé `proj.kalk_*` + `proj.cenik_*`. Také **`es_doklad_zbozi`** — NENÍ mrtvá (empty jen dočasně): zrcadlo **ES faktur/dokladů z Heliosu**, `bank_api.py` do ní syncuje i z ní čte. (Oprava dřívějšího chybného „smazat".)
- **`ec_kalkulace*` — kanonický je ŽIVÝ „router" pár** `ec_kalkulace_hlav` + `ec_kalkulace_polozka` (sync 22.7., používá `router.py`). **Zastaralý „bank_api" pár** `ec_kalkulace` + `ec_kalkulace_pol` (sync 5.7. / nikdy, používá `bank_api.py`) = kandidát na retirement, ale **až po refaktoru `bank_api.py`** (páry mají jiné sloupce: cena/koef vs sklad/nákup). ⚠️ `bank_api.py` teď čte zastaralá kalkulační data.
- **SMAZÁNO 22.7.:** `cenik_prevod` (prázdná dodavatelská překladovka — netřeba).
- **PROVĚŘIT:** `ec_cenik_vzorec*` (duplicita vůči `proj.cenik_vzorec`?).

## Otevřené otázky pro Kristý (zítra)
1. Oživit `proj.kalk_*` na živý zdroj pravdy (pravidelný sync z DB_EC + napojení na app)?
2. Refaktor `bank_api.py` na živý `ec_kalkulace_hlav`/`_polozka` pár + retire zastaralý `ec_kalkulace`/`ec_kalkulace_pol` (a proč bank_api četl zastaralá data)?
3. `ec_cenik_vzorec*` — použití/duplicita vůči `proj.cenik_vzorec`?

## Vazby
Datová mapa: `doc-kalkulace-rozvadecu-datova-mapa-tabulky`. Vize AI-řízení VP: `doc-vp-ai-rizeni-vize`.

