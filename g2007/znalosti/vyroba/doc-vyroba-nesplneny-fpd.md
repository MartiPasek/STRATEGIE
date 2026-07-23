# Nesplneny FPD - prehled ve Vyrobe (pro Dusana)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nesplneny FPD - prehled ve Vyrobe (pro Dusana)

> oblast: `vyroba` - postaveno Claude-28 (Jirka) 23.7.2026, zadal Dusan Havlat.

Kopie prehledu "Nesplneny FPD" z Centraly do STRATEGIE, do soudecku 🏭 Vyroba.
Dusan v nem vidi sve podrizene (HPP i OSVC dohromady) a jejich manko hodin za
aktualni mesic do dnesniho dne. Pocita nad daty STRATEGIE (jedno zda prenesena
z Centraly nebo vzniknuta v appce). Synchronizaci Centrala<->STRATEGIE NERESIME.

## Kde to je
ERP -> strom -> 🏭 Vyroba -> "Nesplneny FPD". Cely modul je data-driven pres fw.*,
takze ZADNY DEPLOY - je to zive hned po zapisu do DB.

Objekty (klon vzoru `vyroba.dusan_att_monthly`):
- data_set 198 `vyroba.dusan_nesplneny_fpd_list` (db_connection 1) - SQL nize
- data_source 202 `vyroba.dusan_nesplneny_fpd_list` (op 269 select -> data_set)
- core 209 `vyroba.dusan_nesplneny_fpd`, comp_def 1301 (typ 306 grid, root=1)
- menu_node 197 pod parent 165, sort 109, visibility_scope=private,
  visibility_user_ids={41} (=Dusan; bez toho by uzel nevidel)

## Vzorec (vse overeno na zivych datech vs Centrala)
Sloupce: os_cislo, zamestnanec, skupina, forma, odpracovano, prac_dni, hod_denne, ma_byt, chybi.
- odpracovano = SUM(tenant.att_day_summary.cas_celkem) za aktualni rok/mesic, datum<=dnes
- ma_byt     = SUM(LEAST(tenant.att_plan_effective.expected_hours, 8)) pro plan_date
               od zacatku mesice do dnes, expected>0   (fond, strop 8/den)
- prac_dni   = count tychze plan dnu
- hod_denne  = ma_byt / prac_dni
- chybi      = ma_byt - odpracovano   (absence se NEzapocitava jako odpracovano -> zustava v chybi)
- skupina    = tenant.v_employee_work_params.rezim (Elektromonteri/Kancelare)
- forma      = tenant.att_employee.rez_forma (HPP/OSVC, jen info, NErozlisujeme)
- podrizeni  = user_id IN (SELECT user_id FROM tenant.vyroba_dusan_team)  (view, stejny resolver
               jako ostatni Dusanovy prehledy)

## Puvod v Centrale (co reprodukujeme)
Prehled = proc `EC_Dochazka_Odpracovano` (autor Kristyna Storkova, 18.6.2020, DB_EC):
- odpracovano = SUM(EC_Dochazka.CasCelkemZakazka) - korekce absence u zkracenych uvazku
  (DruhCinnosti IN 20,21,22,23,30,31,33,34,35,36)
- ma_byt = pocet prac. dni (EC_Svatky, bez So/Ne/svatku, od nastupu) * min(uvazek/den, 8)
- chybi (v procu "Prescas" s opacnym znamenkem) = ma_byt - odpracovano
- filtr: aktivni, jen vyrobni skupiny (EC_SkupinyVazby)

## Proc STRATEGIE data, ne 1:1 shoda s Centralou
- Raw zdroj Centraly `ec.dochazka` je v STRATEGII PRAZDNY (jen 3 test radky VR10704) -> nepouzitelny.
- Pouzivame produkcni zrcadlo `att_day_summary` (sync z EC_Dochazka_SumaDen) - u plne
  synchronizovanych lidi sedi s Centralou na haler (Cividis 522, Sedlackova 322, Svenda 488, Blaha 476...).
- ma_byt z `att_plan_effective` overeno: sedi s Centralou MaByt 10/11 (128/112/64...).
- POZOR `att_day_summary.fpd` NENI cisty denni fond (byva 0/7 nekonzistentne) -> pro ma_byt
  se NEPOUZIVA, bere se att_plan_effective.

## Hodinove nesrovnalosti Centrala vs STRATEGIE - dve ruzne priciny (overeno 23.7.)
1) CHYBI VE STRATEGII (zrcadlo pozadu za dopoctem dovolene):
   U dopredu naplanovane dovolene Centrala nejdriv zapise jen CasDovolena=8, a CasCelkem=8
   dopocita az pozdeji (davkove). Sync stahne recentni (neuzavrene) dny drive, nez ma
   Centrala CasCelkem hotovo -> att_day_summary ma na tech dnech cas_celkem=0 pri cas_dovolena=8.
   Signatura: cas_dovolena>0 AND cas_celkem=0. 23.7. zasazeni: Liskova/Trunec/Divis (3 dny=24h),
   Navratil (1 den). Prechodne nadhodnocuje "chybi". Starsi/uzavrene dny sedi. Oprava = ladeni
   syncu = MIMO ZADANI.
2) CHYBI V CENTRALE (app_only lide): kdo pichaji jen v appce STRATEGIE (att_source_pref.app_only=true,
   napr. Urbanova 496, Havlat 105) nejsou v Centrale EC_Dochazka -> Centrala 0 h, STRATEGIE ma
   realne hodiny. Tady je STRATEGIE spravnejsi. Presne proto stavime nad daty STRATEGIE.

## Rozhodnuti (Jirka 23.7.)
- absence = chybi (jako Centrala; pripadne uprava dle Dusana pozdeji)
- HPP + OSVC dohromady (bez rozliseni)
- Skupina = STRATEGIE rezim (EC_Skupiny se do STRATEGIE NEzrcadli, pouzit nejblizsi analog)

## Build gotchas (pro klonovani dalsich Dusanovych prehledu)
- Most (SQL bridge) ODMITNE `WITH ... INSERT` (bere to jako read s forbidden keyword) -> zapis
  MUSI zacinat na INSERT. Reseni: samostatne INSERT ... SELECT, ID se dohledava pres code, ne RETURNING.
- fw.core/comp_def/menu_node.id = identity (nevkladat), data_set/data_source/op maji sekvence.
- comp_def top-level: root NOT NULL (=1), parent NULL. Grid typ 306 renderuje sloupce z data_setu.
- Overuj ctenim (banner @@G2007ADD i write vraci neutralni navratovku).

