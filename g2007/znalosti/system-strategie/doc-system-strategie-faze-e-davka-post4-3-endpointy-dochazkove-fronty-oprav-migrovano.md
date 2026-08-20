# Faze E davka POST4: 3 POST HTTP endpointy dochazkove fronty oprav migrovano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovany 3 dalsi POST HTTP endpointy: att_fix_request (zadost o opravu, jen aktualni mesic), att_fix_resolve (odbaveni polozky fronty bez zasahu - anomalie nebo rozpor dne), att_period_lock_set (zamek/odemek mesice pro mzdy). Vsechny vyuzivaji jiz migrovane male delegat-stuby (att_fix_scope/scope_emps/all/audit/can_lock/editors_for_emp) jako inlinovane zavislosti.

Zbyvajicich 5 fix/* endpointu (fix/entry, fix/add, fix/void, fix/polozka, fix/merge) je vyrazne vetsich (113-180 radku) a odlozeno do dalsi davky. att_fix_resync take odlozen - zavisi na nemigrovane 173-radkove _att_sync_vyroba_work, bude potreba bud ji migrovat prvni (cross-script vzor) nebo duplikovat.

Deploy commit 12fe89d3a, 17 insertions/168 deletions. CELKEM AKTIVNICH FUNKCI: 113. router.py: 63325 radku (z puvodnich 67789 = 6.59% zmenseni).

