# Vyroba Cinnost Model

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Zakázka+činnost+čas ve vyroba_work (EC + app work_alloc); prošlo zkušebnou = zkoušení>0**

Oddělený zakázkový systém: tenant.vyroba_work = zakázka (zakazka_ref) + činnost (cinnost_id) + čas, jako joby. Plněno ze dvou zdrojů (sync _sync_vyroba_work_ec/_app, @@VYRWSYNC): EC_Dochazka (DruhCinnosti, tablet/Centrála) + naše appka (tenant.work_alloc, segmenty s činností). Dedup: app-den přebíjí EC agregát. NEsahá na att_entry (docházka/mzdy).
Činnosti (tenant.vyroba_cinnost): drátování id4, zkoušení id5 (=zkušebna), mechanické, zámečnické, dokončovací. "Prošlo zkušebnou" = má hodiny zkoušení. Pozor: att_entry drží jen zakázku (project_ref), ne jemnou činnost.

_Souvisi:_ vp-flow-zakazky

