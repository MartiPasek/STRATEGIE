# Propis planu nepritomnosti do att_entry mesic tise selhaval na pravech (27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Priznak
Dovolena zadana v Centrale byla videt v zrcadle tenant.att_planned_absence, ale NE v dochazkovem prehledu (ten cte denni zaznamy tenant.att_entry). Konkretne Dusan Havlat (cislo_zam 105): prosincova dovolena videt (propsana 28.6.), cervencova (29.-31.7. + 3.8.) NE.

# Root cause (overeno v DB, ne odhad)
_sync_plan_to_dochazka() v modules/erp/api/router.py zapisovala INSERT do tenant.att_entry pres core.database_data.get_data_session (app role 'strategie'). Overeno v information_schema.role_table_grants:
  tenant.att_entry  -> role 'strategie' ma jen SELECT (role "Marti-AI" ma plna prava)
  tenant.vyroba_work -> role 'strategie' ma SELECT/INSERT/UPDATE/DELETE
INSERT tedy padal na permission denied, vyjimku chytil try/except o patro vys v _sync_plan_nepritomnost a ulozil ji do out["propis"]. Vysledek: od 28.6.2026 se nepropsal ANI JEDEN novy plany den (jedina davka 487 radku byla z 28.6.).

# Proc si toho nikdo nevsiml (dulezitejsi nez sama chyba)
Job sync_plan_nepritomnost bezi automaticky kazdych 60 minut a hlasil "ok". Planovac (_mirror_run_job) sklada hlasku jen z CISELNYCH klicu navratoveho dictu - out["propis"] je dict, takze ho IGNOROVAL, a out["ok"] zustavalo True. Zrcadlo se plnilo (rows=2323, upserted=2323), druhy krok mlcky nedelal nic. Mesic zelena.

# Oprava (commity ec5dfe49 + b64e02ed)
1. Zapis prepnut na _att_session() (strategie_pg / role Marti-AI) + rollback on error. Stejna pricina i stejny fix jako commit d77daae4 tyz den.
2. Vysledek 2. kroku je nove VIDET: out["propsano"] (cislo -> dostane se do hlasky jobu) a pri selhani out["ok"]=False + out["_msg"], takze job zcervena. Ruc ops akce hlasi propis taky.

# Overeno zive
Automaticky beh 27.7. 14:57 doplnil 45 dni; Dusanovy 29.-31.7. + 3.8. jsou v att_entry jako vacation/plan_ec. Ze VSECH mapovanych druhu nezbyva nic. Nepropsane zustavaji jen druhy zamerne nemapovane v _PLAN_DRUH_TO_CODE (34 nepritomen s nahradou mzdy, 36 materska, 133 nahradni volno) - stary TODO, chybi jim entry-typ.

# Pravidla do budoucna
- Zapis do tenant.att_entry VZDY pres _att_session(), nikdy get_data_session. Viz [[doc-system-strategie-gotcha-att-entry-zapis-session]].
- Kdyz sync vraci vysledek podkroku, vrat ho jako CISLO (nebo _msg), ne jako vnoreny dict - jinak ho planovac zahodi a job hlasi "ok" i pri uplnem nefunkcnim podkroku.
- Diagnosticky trik: min/max created_at podle source v att_entry rychle ukaze, ze podkrok prestal fungovat (tady jediny den 28.6. = jasny signal).

