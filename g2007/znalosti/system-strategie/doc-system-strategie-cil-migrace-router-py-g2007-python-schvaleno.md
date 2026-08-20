# Cil: migrace router.py do g2007.python, schvaleno jako celek

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Cil: migrace router.py -> g2007.python, schvaleno jako celek (31.7.2026)

Marti explicitne pozadal, aby se INSERT/UPDATE zapisy do g2007.python behem probihajici migrace (viz analyza_mzdy_dochazka_vyroba.md, faze A-E) nemusely schvalovat jednotlive v banneru: "Pojd zalozit cil na migraci router.py do g2007.python a ja ho schvalim jako celek... jinak jsem tu jen jako opici klikac na kazdy update, ktery jsem uz davno odsouhlasil."

## Co se zmenilo (jadro, commit 84b42adc2)
Router.py SQL most (`/api/v1/erp/... claude_sql` endpoint) uz mel presedens: DENIK SANDBOX (Marti 25.6.2026) — zapisy do `tenant.ucetni_denik` / `_log` / `bank_predkontace` bezi primo bez banneru ("hra o nic"). A `@@G2007ADD` (Marti 21.7.2026) — inline zapis do g2007.znalost bez banneru, doktrina: "konstruktivni operace musi jet autonomne, updaty taky; jen mazani se schvaluje".

Ta stejna doktrina je ted rozsirena i na `g2007.python`:
- **INSERT** (novy kod) a **UPDATE** (napr. aktivace stav_zivota navrzeno->active, oprava popisu) na g2007.python bezi PRIMO, bez cekani na banner.
- **DELETE / TRUNCATE / ALTER** na g2007.python ZUSTAVAJI gated — jdou dal na banner presne jako dřív. To je ta "mazani" cast doktriny.
- Podminka je striktni: VSECHNY zapisove cile v danem SQL prikazu musi byt presne `g2007.python` (zadne smichane vicetabulkove zapisy) — jinak jde na banner jako drив.

## Overeno naostro
- UPDATE (no-op) na g2007.python -> "OK · 1 řádků · g2007.python KONSTRUKTIVNI (přímo, bez banneru)" bez banneru.
- DELETE (na neexistujici kod, testovaci) -> SPRAVNE skoncil na "ČEKÁ NA SCHVÁLENÍ" (banner), jak ma.

## Dusledek pro pokracujici migraci
Faze C/D/E (viz analyza_mzdy_dochazka_vyroba.md) uz nebudou pri kazdem INSERT/aktivaci cekat na Martiho klik v banneru. Aktivace + deploy poradi (aktivovat PRED deployem delegate patche) zustava beze zmeny — jde jen o odstraneni bannerove prodlevy u samotneho zapisu do g2007.python.

