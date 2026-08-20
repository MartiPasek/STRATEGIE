# GOTCHA: zapis do att_entry (dochazka/mzdy) vyzaduje _att_session (strategie_pg), NE get_data_session (27.7.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Objeveno 27.7.2026 (i28) pri opravovani self-completing doplnovani.

## Problem
Self-completing UPDATE do tenant.att_entry (firma_id, user_id) v _maybe_sync_ec_dochazka pouzival core.database_data.get_data_session (app session). Ten NEMA prava zapisu na tenant.att_entry -> UPDATE TISE SELHAVAL (chyceno v try/except), nove radky zustavaly bez firma_id/user_id (0 z 47 co mely). vyroba_work/zakazka UPDATE pres get_data_session PROSLY (na ty prava ma).

## Pricina
Dochazkove/mzdove zapisy jdou pres privilegovanou roli. _att_session() = modules.strategie_pg.application.service.get_session() (Marti-AI role, db_owner) = MA prava na att_entry i vyroba_work/zakazka. get_data_session (app role) att_entry zapis NEMA.

## Pravidlo
Zapis (UPDATE/INSERT) do tenant.att_entry (a obecne dochazka/mzdy tabulek) VZDY pres _att_session() / strategie_pg (_pg.get_session()), NE get_data_session. Backfilly pres SQL most jedou pres strategie_pg (Marti-AI role), proto fungovaly - ale sync kod musi pouzit stejnou session.

## Druha lekce (robustnost): self-completing fily davat KAZDY do vlastniho commitu + rollback-on-error, ne vsechny do 1 commitu - jinak 1 selhani (napr. prava) shodi VSECHNY a tise. Commit 397d1fd3 (izolace) + d77daae4 (spravna session). Souvisi [[doc-dochazka-doch-firma-id-backfill]].

## POTVRZENO GRANTEM (27.7.2026 odpoledne, i28) - uz to neni domnenka
SELECT z information_schema.role_table_grants:
  tenant.att_entry   -> role 'strategie' ma JEN SELECT ; role "Marti-AI" ma plna prava
  tenant.vyroba_work -> role 'strategie' ma SELECT/INSERT/UPDATE/DELETE
Presne tohle vysvetluje, proc zapisy do vyroba_work prochazeji a do att_entry ne.

## DRUHY VYSKYT TEHOZ BUGU (tyz den, jina funkce)
_sync_plan_to_dochazka() (propis planu nepritomnosti z Centraly do dochazky) mela uplne stejnou chybu. Dusledek: od 28.6.2026 se NEPROPSAL ani jeden novy planovany den (dovolene lidi nebyly v dochazkovem prehledu), a hodinovy job u toho cely mesic hlasil "ok". Fix ec5dfe49 + b64e02ed. Detail [[doc-dochazka-plan-propis-do-att-entry-selhaval]].

## SWEEP - je to jeste nekde? NE (overeno 27.7.2026)
Projity VSECHNY funkce v modules/erp/api/router.py, ktere zapisuji do tenant.att_entry (32 funkci). Vsechny pouzivaji _att_session()/strategie_pg, nebo dostavaji session od volajiciho. Jedine dva vyskyty byly _maybe_sync_ec_dochazka a _sync_plan_to_dochazka, oba opraveny.
Rychly sweep (kdyby pribyl novy kod): rozsekat router.py po funkcich a najit ty, co maji "INSERT INTO tenant.att_entry"/"UPDATE tenant.att_entry" a zaroven get_data_session bez _att_session.

