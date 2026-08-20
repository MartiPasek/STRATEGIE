# Faze E davka 2: 15 GET HTTP endpointu vyroby a mezd migrovano na DB-driven delegaty

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Druha davka Faze E (31.7.2026 17:19-17:54 UTC, commit 0b1fbe284): 15 GET/read-only HTTP endpointu ze dvou novych domen (vyroba, mzdy) - prvni davka mimo dochazku od pilotu.

Endpointy: app_vyroba_my_cinnosti, app_vyroba_cinnost_master, app_vyroba_can_manage, app_vyroba_lidi, app_vyroba_zakazky_lide, app_vyroba_moje, app_vyroba_zpravy, app_vyroba_odvozy, app_vyroba_odvoz_pozn_list, app_vyroba_todo_list, mzdy_vyplatnice, mzdy_vyplatnice_detail, mzdy_vyplatnice_slozka_detail, mzdy_financni_podminky, mzdy_c_smlouvy.

Pouzity stejny wrapper vzor jako davka 1 (_status_code klic + surove query-param predavani) - zadna dalsi generalizace nebyla potreba, coz potvrzuje ze vzor je stabilni pro cele GET spektrum.

Nove zavislosti objevene:
- Vyroba: _vyroba_can_manage (+_VYROBA_MANAGERS + import is_marti_parent), _hr_can_manage (jina funkce, uzsi HR-only kontrola).
- Mzdy: cely "cockpit" auth okruh (_is_cockpit -> _is_parent + _is_fin_hr_group + scoped-approver konstanty Petra/Sarka, ~39 radku inlinovano vcelku), _zrc_dbs + _mssql188_query (primy pristup Helios cloud MSSQL), _WAGE_LABEL, jiz-migrovane staby _mzdy_loajalita_rows/_mzdy_finance_zakazek_rows (Faze A), _c_vypocet + _C_* konstanty.

DULEZITY NALEZ - predexistujici bug v produkci (NEOPRAVOVANO, jen zdokumentovano, verbatim zachovano pri migraci): mzdy_vyplatnice_detail a mzdy_vyplatnice_slozka_detail odkazuji na nedefinovane jmeno _JEDNATELE_CISLA (korekce slozky 432 "premie jednatel"). U vyplatnice_detail je NameError tise polknuty (try/except Exception: pass) - korekce v produkci ted nikdy nefunguje. U vyplatnice_slozka_detail NENI odchycen - realne pouziti (cislo_ms=432 s platnym cislem zamestnance) vyhodi 500. Toto NENI migracni regrese (chovani zachovano presne jako v originalu), je to nalezeny existujici stav hodny Martiho pozornosti mimo tuto migraci.

Provozni pouceni (bridge cesty): CLAUDE_SQL.sql/CLAUDE_GO.txt/CLAUDE_OUT.txt i CLAUDE_DEPLOY.txt/CLAUDE_DEPLOY_GO.txt/CLAUDE_DEPLOY_OUT.txt zijou VSECHNY pod scripts/claude_sql/, NIKDY v korenu repa (i kdyz tam matouci stare kopie lezi) - overeno v claude_sql_runner.py zdrojaku po dvou neuspesnych pokusech (SQL dotaz i DEPLOY trigger tise nezpracovany kvuli spatne ceste).

Post-deploy overeno pres SQL most: vsech 15 kodu stav_zivota='active'. Celkem aktivnich funkci v g2007.python: 92.

