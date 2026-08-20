# Faze C (cast 2): 4 odlozene funkce + prvni cross-script erp_registry.call vzor

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Faze C (cast 2): 4 odlozene funkce + prvni cross-script erp_registry.call vzor (31.7.2026)

Dokonceni Faze C docházkove casti: 4 funkce odlozene z casti 1, protoze volaly jine, jiz migrovane funkce.

## Migrovane funkce
- att_apply_work_selection — self-contained (inlinovan _norm_zakazka + _REZIE_REF)
- att_maybe_level_catchup — vola att_automat_level_day (Faze C cast 1)
- att_resync_full — vola sync_ec_dochazka_recent (nejkomplexnejsi migrace dosud, prvni davka)
- att_sync_today — vola sync_ec_dochazka_recent, soucast ziveho 30s scheduler tiku (`loop.run_in_executor(None, _att_sync_today)`)

## Novy vzor: cross-script erp_registry.call() misto duplikace
Dosavadni pravidlo bylo "sobestacny skript = inlinovat VERBATIM kopii kazde zavislosti". U _att_resync_full a _att_sync_today by to znamenalo POTRETI zkopirovat cele telo sync_ec_dochazka_recent (nejkomplexnejsi funkce, 8 vnorenych zavislosti vc. EUROSOFT MCP volani). Misto toho tyto 2 skripty (+ att_maybe_level_catchup pro att_automat_level_day) volaji:

    from modules.erp.api import erp_registry as _ereg
    _ereg.call("sync_ec_dochazka_recent", frm=today, to=today, wipe=True)

primo z jineho DB skriptu (ne z router.py). Zduvodneni: erp_registry.call je normalni importovatelna Python funkce — exec()'d skripty uz prokazatelne zvladaji import+volani (vsech 39 dosavadnich delegatu v router.py to dela), takze inicializace odjinud nez z router.py je stejne bezpecna. Toto VYTVARI zavislost mezi radky v g2007.python (kdyby nekdo deaktivoval sync_ec_dochazka_recent, att_resync_full/att_sync_today by se rozbily) — vedomy kompromis mezi duplikaci (bezpecnejsi izolovane, ale masivne redundantni) a DRY (elegantnejsi, ale zavisle). Pouzito JEN kdyz je duplikovane telo velke (100+ radku) a zavislost uz je aktivni a stabilni.

## Overeno pred aktivaci
SELECT potvrdil, ze sync_ec_dochazka_recent i att_automat_level_day jsou stav_zivota='active' PRED aktivaci teto davky — cross-script volani by jinak selhalo (`RuntimeError: nema aktivni implementaci`).

## Zivy test NEPROVEDEN
att_resync_full/att_maybe_level_catchup/att_sync_today maji realne vedlejsi ucinky (vc. wipe=True kompletni re-import dochazky) — konzistentne s zavedenou praxi u zapisovych funkci overeno jen extrakci+ast.parse+py_compile+diff+code review, ne zivym zavolanim.

## Deploy
Diff proti HEAD potvrdil PRESNE 4 hunky. Commit bcb397909 (14 insertions, 133 deletions).

## Stav Faze C (dochazka)
Vsichni nazvani kandidati z analyza_mzdy_dochazka_vyroba.md sekce 2 (dochazka plain bez zapisu I se zapisem) jsou nyni migrovani. Zbyva: funkce s primym EUROSOFT/MCP volanim (Faze D, case-by-case pozornost), mzdove zapisove funkce s vyssim rizikem (_mzdy_priplatky_rows a pod., doc explicitne rika "opatrneji, ne rutinni davka"), a HTTP endpointy (Faze E, >130 kusu, potrebuje architektonicky vzor pred zapocetim).

