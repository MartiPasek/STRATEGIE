# Schéma `proj` + úklid kalkulačního know-how (rozhodnutí 22.7.2026)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schéma `proj` + úklid kalkulačního know-how (rozhodnutí 22.7.2026)

## Rozhodnutí o schématu (Marti, 22.7.2026)
Jedno schéma **`proj`** = domov pro **řízení a vedení projektů** (výhledově celá firma, ne jen VP). Uvnitř čisté prefixy, nemíchat referenci a provoz naslepo:
- **Kalkulační know-how → `proj.kalk_*`**: `kalk_dil`, `kalk_koef`, `kalk_cena`, `kalk_rabat`, `kalk_regcis_def`, `kalk_sestava(_pol)`, `kalk_skupina(_pol)`, nově `kalk_preklad_zakaznik`. Ceník reference (`cenik_*`) také pod `proj`.
- **Projektový provoz → `proj.plan_*` / `proj.zakazka_*` / `proj.ukol_*`**: plány, zakázky, úkoly, tok poptávka→dodání (dle „všechno je plán", viz `doc-vp-ai-rizeni-vize`).

## Klíčové zjištění: zdroj pravdy z velké části UŽ EXISTUJE
Nativní systém **`kalk_*`** (v `tenant`, **seed z 1.7.2026 — NE živý**): `kalk_kmen` (identita 5112), **`kalk_koef`** (koeficienty `k_arb`/`k_vkm` = crown-jewel IP, 4122), `kalk_cena` (2508), `kalk_rabat` (2967), **`kalk_regcis_def`** (pravidla normalizace čísel per výrobce — řeší párování, 60), `kalk_sestava`/`kalk_skupina`.
Ceník **živý**: `cenik_polozka` (539k, 11 výrobců SIE/MUR/WEI/PHO/EAT/SCH/WAG/LAP/RIT/FIN/HAR, import 2.7.2026).
→ **Hlavní úkol není stavět, ale OŽIVIT** `kalk_*` (sync z DB_EC + napojení na aplikaci) a uklidit okolí.

## Úklid — VERDIKTY (zatím NÁVRH, finalizovat s Kristý)
- **NECHAT:** celé `kalk_*` jádro + `cenik_*`.
- **SLOUČIT (duplicita):** `ec_kalkulace` × `ec_kalkulace_hlav` (hlavičky); `ec_kalkulace_pol` (cena/koef pohled) × `ec_kalkulace_polozka` (sklad/nákup pohled) — dva neúplné mirrory jedné `EC_KalkulacePolozky`.
- **SMAZAT:** `es_doklad_zbozi` (prázdné). `cenik_prevod` již smazáno 22.7.
- **PROVĚŘIT:** `cenik_cena_medi`, `ec_cenik_vzorec*` (duplicita vůči nativnímu `cenik_vzorec`?).

## Otevřené otázky pro Kristý (zítra)
1. Oživit `kalk_*` na živý zdroj pravdy (pravidelný sync + app)? 2. Který z dvojic mirrorů je kanonický? 3. `cenik_cena_medi` / `ec_cenik_vzorec*` — použití?

## Vazby
Datová mapa tabulek Centrála↔STRATEGIE: `doc-kalkulace-rozvadecu-datova-mapa-tabulky`. Vize AI-řízení VP: `doc-vp-ai-rizeni-vize`.

