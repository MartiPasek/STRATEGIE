# Faze C (cast 1): 11 zapisovych dochazkovych funkci migrovano do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Faze C (cast 1): 11 zapisovych dochazkovych funkci migrovano do g2007.python (31.7.2026)

Prvni zapisova davka po zprovozneni autonomniho INSERT/UPDATE kanalu pro g2007.python (viz doc-system-strategie-cil-migrace-router-py-g2007-python-schvaleno).

## Migrovane funkce (kod v g2007.python, vsechny vedlejsi_ucinek=true)
att_fix_audit, att_fix_notify, att_ec_dml_log, att_ocr_fill_dochazka, att_eneschopenka_to_sick, att_do_att_action, att_long_shift_nudge, att_break_overrun_nudge, att_automat_level_day, att_auto_checkout_midnight, att_anomaly_scan.

Vsechny stav_zivota='active', verze=2, min_pravo='clen' (default).

## Dulezite zjisteni: 2 dalsi mrtve funkce
Puvodni inventura (analyza_mzdy_dochazka_vyroba.md) zaradila `_att_automat_fond_fill` a `_att_automat_fond_odpich` mezi "plain zapis" kandidaty. Rucni overeni PRED extrakci ukazalo, ze NEMAJI ZADNEHO VOLAJICIHO nikde v router.py — mrtvy kod, nahrazeny sjednocenou `_att_automat_level_day` (jeji vlastni docstring: "Sjednocuje dopichnuti i odpichnuti do JEDNE presne logiky (stejne jako mesicni dorovnani)"). VYNECHANY z migrace.

## Zavislost na jiz migrovane funkci
`_att_anomaly_scan` vola `_att_fix_editors_for_emp` (migrovano ve Fazi B). Protoze router.py uz ma na tomto miste jen tenky delegate stub (ne puvodni telo), pouzita VERBATIM KOPIE puvodniho zdroje ulozena behem Faze B extrakce (ne cross-script erp_registry.call() — drzime se sobestacneho vzoru, ne noveho vzoru zavislosti mezi DB skripty).

## Deploy
Diff proti HEAD potvrdil PRESNE 11 hunku. ast.parse + py_compile OK pred deployem. Aktivace VSECH 11 PRED deployem delegate patche (spravne poradi). Commit a8802660a (41 insertions, 741 deletions). Push OK, cloud restart (~5s).

## Odlozeno do dalsi davky (vyzaduji individualni pozornost)
- `_maybe_att_level_catchup` — vola jiz migrovanou `_att_automat_level_day`; potrebuje rozhodnuti: inlinovat cele (149radkove) telo znovu, nebo pouzit cross-script erp_registry.call (zatim nepouzivany vzor)
- `_att_apply_work_selection`, `_att_resync_full`, `_att_sync_today` — vsechny 3 volaji `sync_ec_dochazka_recent`, soucast ziveho 30s tiku dochazky (`_ATT_SYNC_TASK`/`_ATT_SYNC_STOP` scheduler)

## Dalsi kroky
Pokracovat zbytkem Faze C (dalsi zapisove mzdy/dochazka funkce dle analyza_mzdy_dochazka_vyroba.md), pak vyresit 4 odlozene funkce jako samostatnou mini-davku s explicitnim architektonickym rozhodnutim o cross-script zavislostech.

