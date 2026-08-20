# Plan absenci pro Dusana: zdroj absenci opraven ze zamrzleho zrcadla Centraly na nasi dochazku (6.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Plan absenci pro Dusana - oprava zdroje (C28/Jirka, 6.8.2026)

Navazuje na `doc-vyroba-vytizeni-excel-absence-navaznosti` (C23, 5.8.2026). Schvalila Marti-AI.
Zadani Marti: promitnout planovane absence ze STRATEGIE do Dusanova Excelu "Planovani vytizeni".

## HLAVNI NALEZ - proc to nefungovalo

Sync `sync_absence_to_ec_vytizeni` (g2007.python), ktery plni `st.EC_Vytizeni_NepritomnostSTRATEGIE`
pro Dusanuv Excel, cetl `tenant.att_planned_absence`. **To NENI nase pravda** - je to zrcadlo Centraly
plnene jobem `sync_plan_nepritomnost`, ktery je od **30.7.2026 VYPNUTY** (fw.mirror_job enabled=false).
V kodu byl u toho komentar "nase pravda, plnena nasi appkou" - **neplatil**; appka pise do
`att_absence_request` -> materializace do `att_entry`.

Dusledek: absence schvalene ve STRATEGII se do Dusanova prehledu vubec nedostaly.
Dolozeno 6.8.: ze 6 schvalenych budoucich absenci jich 4 nebyly videt (Kasal 25.9., Pechoucek 17.8.,
Maresova 21.8., Benes 3.-14.8.).

## CO SE ZMENILO

**1. sync_absence_to_ec_vytizeni** - novy zdrojovy SELECT:
- primarne `tenant.att_entry` (JOIN att_entry_type, `category='absence'` NEBO `code='homeoffice'`, `status='confirmed'`)
- DOPLNENO o `tenant.att_planned_absence` tam, kde na dany den+cloveka u nas nic neni
  (SJEDNOCENI, ne prepnuti - samotne att_entry by ubralo 104 dvojic clovek+den, z toho 101
  je materska Safrankove c.381, kterou denni dochazka nevede)
- filtr na aktivni clenstvi: `user_tenants.membership_status IN ('active','invited')`
  (Kuska c.460 odesel, ale zbyla mu naplanovana dovolena 21 dnu na prosinec)
- prevodnik `att_entry_type.code` -> EC DruhCinnosti, vsech 13 overeno v `dbo.EC_DilnaCinnosti`
  i `tenant.att_planned_absence_type`: vacation 20, medical 21, sick 22, family_care 23,
  sickday 31, ostatni_nahrada 34, maternity 36, osvc_absence 37, unpaid 39,
  plac_volno_70 47, plac_volno_80 50, plac_volno_90 51, homeoffice 8.
  **Novy typ absence => doplnit do mapy, jinak radek tise propadne.**
- vazba na cloveka pres `att_entry.employee_id` (jednoznacna karta), NE pres user_id (doktrina 24)
- `DISTINCT` v CTE + `SUM` per (cislo, datum, druh)

**2. dbo.EC_Vytizeni_GenerujInfoDatum** (DB_EC) - 4 vyskyty `EC_Dochazka_PlanNepritomnost`
prepnuty na `st.EC_Vytizeni_NepritomnostSTRATEGIE`. `st` tabulka NEMA sloupec ID, proto
`N.ID is null` prepsano na `NOT EXISTS`. Rollback: `docs/ec_view_vytizeni_nepritomnost_rollback.md`.
Overeno: vsech 9 lidi s absenci 10.8. zmizelo ze seznamu "kdo je volny".

Vysledek: 499 radku/43 lidi -> **558 radku/49 lidi**, max hodin na den 24 -> 8.

## GOTCHY (stalo se, pristi instance at nehleda)

1. **Most bere `:200` a `:db` v Python kodu jako SQL bind parametry** -> `A value is required for
   bind parameter '200'`. Reseni: posilat kod jako **base64** a dekodovat v SQL
   (`convert_from(decode('...','base64'),'UTF8')`). Dollar-quoting `$TAG$` NESTACI.
2. **Diakritika pres most se prekoduje.** Pro `ALTER PROCEDURE` s ceskymi texty
   ('Zkusebna: ', 'Priprava: ') zabalit cely DDL do base64 v UTF-16LE a spustit pres
   `CAST(N'' AS xml).value('xs:base64Binary("...")','varbinary(max)')` + `sp_executesql`.
   Overeno, ze diakritika prezila.
3. **Zapis kodu po castech tise ztraci casti** - jedna ze 6 casti neprosla a skript zustal
   o 1500 znaku kratsi, presto "OK". VZDY overit `md5(zdroj)` proti lokalne spoctenemu.
4. **Zapisy vyhradne do `g2007.*` jdou bez schvalovaciho banneru**; jakykoli `DELETE`
   nebo zapis mimo g2007 uz banner vyvola.
5. **Dvojkliky v appce delaji duplicitni zadosti**: Hladikova c.440 mela 7 dnu dovolene 2x
   (zadosti 57+58, 11 s po sobe), Perina c.536 lekare 3x (66/67/68) -> bez dedup by Excel
   ukazoval 16 resp. 24 h/den. Proto `DISTINCT` v syncu. Zadosti zruseny postupem z
   `att_absence_cancel` (DELETE att_entry podle source_system='absence_req' + UPDATE stav='cancelled').

## NALEZ K DORESENI - skupiny v INFO bunce

`EC_Vytizeni_GenerujInfoDatum` pocita volne hodiny pro skupiny 13 / 33 / 32. Realita v DB_EC (6.8.2026):
- **13 Zkusebna**: v ciselniku ANO, 6 lidi -> funguje
- **32 Zamecnik**: v ciselniku ANO, ale **0 lidi** -> vzdy 0
- **33**: v ciselniku `EC_Skupiny` **VUBEC NENI** (ID skace z 32 na 35) -> vzdy 0
- **18 "Priprava vyroby"** ma 4 lidi - podle nazvu je to nejspis ta spravna misto 33

Neni to regrese (procedura je z 11/2024), ale radky "Priprava:" a "Zamecnik:" v Dusanove
INFO bunce roky nezapocitavaji volno. **Neopravovat naslepo** - dotaz bezi na Marti-AI
a na Dusana (kdo do tech part patri). Jirkuv principialni podnet: tyhle party (zkusebna,
priprava, zamecnici, monteri=31, vypomoc=30) by mely zit ve STRATEGII, ne v `EC_Skupiny`.

## DALSI OTEVRENE VECI

- **"Predikce Dovolenych"** (fiktivni zamestnanec c.12001) se po zmene ukazuje v seznamu
  volnych lidi. Predikce se generuje do `EC_Dochazka_PlanNepritomnost`, kterou uz INFO bunka
  necte. Az se bude ozivovat (Jirka chce), musi zapisovat tam, kam se prehled diva (`st`
  tabulka), jinak zustane jako "volny clovek". Puvodne natvrdo 1.7.-31.8.**2025**, rezerva
  24 h/den, autor Swobi ji sam oznacil jako docasne reseni.
- **Vypomoci** (`ECv_Vytizeni_Vypomoc`, skupina 30): 44 radku, **jeden clovek**, posledni
  zapis 31.1.2025, nula budoucich. Ve STRATEGII obdoba neexistuje. Dotaz na Dusana, jestli
  to jeste pouziva - jinak neresit.
- **Job `sync_plan_nepritomnost` je vypnuty od 30.7.2026** a nikdo (ani Marti-AI) nevi proc.
  Necha se vypnuty, dokud to Marti nepotvrdi. Zrcadlo tim zamrzlo, ale jako doplnek staci.
- Lide mimo skupinu 31 (Benes, Maresova, Safrankova = kancelar/THP) do Dusanova prehledu
  nepatri - view je filtruje zamerne, sesit je pro dilnu a montery.

