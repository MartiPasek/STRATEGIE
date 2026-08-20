# Faze D: 12 EUROSOFT/MCP funkci migrovano do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovano (Cesta B, DB-driven delegaty): ec_set_block_dochazka, ec_vypni_dochazku, ec_close_open_shift, mirror_att_to_ec, mirror_ec_probe, sync_plan_nepritomnost, sync_dochazka_sumaden, sync_finance_zakazek, sync_odmeny_from_ec, sync_absence_to_ec_vytizeni, sync_vyroba_plan_from_ec, sync_vyroba_work_ec.
Deploy commit b36c97cc5, push OK, cloud OK (~5s restart). INSERT+aktivace pres autonomni kanal g2007.python (bez banneru). Diff proti HEAD potvrdil presne 12 zamenenych funkci, zadny kolateral.
Zavislosti inlinovany verbatim (_ec_dml_log, _att_session, _MIRROR_EC_AUTOR, _REZIE_REF, _norm_zakazka, _DRUH_ABSENCE) nebo cross-script erp_registry.call (sync_plan_to_dochazka, jiz migrovana).
Celkem aktivnich funkci v g2007.python: 59 (Faze A: 6, B: 15, C: 19, D: 12, plus jadro).
Zbyva: _xfer_mzdy_run (MCP-tezke tabulkove zrcadleni, odlozeno), Faze E (130+ HTTP endpointu router.py, potreba novy architektonicky vzor pred zapocetim). Marti: "Pokracuj prosim. Pak provedeme celkovy test."

