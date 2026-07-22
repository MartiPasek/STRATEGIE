# Schéma `proj` + úklid kalkulačního know-how (22.7.2026)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schéma `proj` + úklid kalkulačního know-how (22.7.2026)

## ✅ PROVEDENO (22.7.2026 večer)
- **Schéma `proj` založeno.** Role **`Marti-AI` je natrvalo superuser** (aby most nespadl na vlastnictví tabulek).
- **Přesunuto do `proj` (data intaktní, SET SCHEMA = metadata):**
  - **10× `proj.kalk_*`**: `kalk_kmen`, `kalk_koef`, `kalk_cena`, `kalk_rabat`, `kalk_regcis_def`, `kalk_sestava(_pol)`, `kalk_skupina(_pol)`, `kalk_std_stage`.
  - **5× `proj.cenik_*`**: `cenik_polozka` (539 459 řádků), `cenik_import`, `cenik_vyrobce`, `cenik_vzorec`, `cenik_cena_medi`.
- **Ceník produkčně, bez view:** přepsáno 41 odkazů `tenant.cenik_` → `proj.cenik_` ve 3 souborech (`modules/erp/api/cenik_engine.py`, `router.py`, `kalkulace_engine.py`), nasazeno (commit `df8e66c9f`, py_compile OK). Ověřeno: 0 DB funkcí i views odkazujících na starý `tenant.cenik_`.
- **Zatím NEpřesunuto:** `ec_*` zrcadla (živě synchronizovaná z DB_EC) + duplicitní `ec_kalkulace*` mirrory — čekají na verdikty s Kristý.

## Rozhodnutí o schématu (Marti, 22.7.2026)
Jedno schéma **`proj`** = domov pro **řízení a vedení projektů** (výhledově celá firma, ne jen VP). Uvnitř čisté prefixy, nemíchat referenci a provoz naslepo:
- **Kalkulační know-how → `proj.kalk_*`** (+ ceník reference `proj.cenik_*`).
- **Projektový provoz → `proj.plan_*` / `proj.zakazka_*` / `proj.ukol_*`**: plány, zakázky, úkoly, tok poptávka→dodání (dle „všechno je plán", viz `doc-vp-ai-rizeni-vize`).

## Klíčové zjištění: zdroj pravdy z velké části UŽ EXISTUJE
Nativní `kalk_*` (**seed z 1.7.2026 — NE živý**, nyní v `proj`): identita `kalk_kmen`, **koeficienty `kalk_koef`** (`k_arb`/`k_vkm` = crown-jewel IP), `kalk_cena`, `kalk_rabat`, **`kalk_regcis_def`** (pravidla normalizace čísel per výrobce — řeší párování), sestavy/skupiny.
Ceník **živý**: `cenik_polozka` (539k, 11 výrobců SIE/MUR/WEI/PHO/EAT/SCH/WAG/LAP/RIT/FIN/HAR, import 2.7.2026).
→ **Hlavní úkol není stavět, ale OŽIVIT** `kalk_*` (sync z DB_EC + napojení na app) a doklidit okolí.

## Úklid — VERDIKTY (zatím NÁVRH, finalizovat s Kristý)
- **NECHAT:** celé `proj.kalk_*` + `proj.cenik_*`.
- **SLOUČIT (duplicita):** `ec_kalkulace` × `ec_kalkulace_hlav` (hlavičky); `ec_kalkulace_pol` (cena/koef pohled) × `ec_kalkulace_polozka` (sklad/nákup pohled) — dva neúplné mirrory jedné `EC_KalkulacePolozky`.
- **SMAZAT:** `es_doklad_zbozi` (prázdné). `cenik_prevod` již smazáno 22.7.
- **PROVĚŘIT:** `ec_cenik_vzorec*` (duplicita vůči `proj.cenik_vzorec`?).

## Otevřené otázky pro Kristý (zítra)
1. Oživit `kalk_*` na živý zdroj pravdy (pravidelný sync + app)? 2. Který z dvojic `ec_kalkulace*` mirrorů je kanonický? 3. `ec_cenik_vzorec*` — použití?

## Vazby
Datová mapa tabulek: `doc-kalkulace-rozvadecu-datova-mapa-tabulky`. Vize AI-řízení VP: `doc-vp-ai-rizeni-vize`.

