# Priplatky a srazky v Praze: novy modul, prava, zamek a migrace historie (30.7.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Priplatky a srazky (Praha) - modul, prava, zamek, migrace historie

> oblast: mzdy - Claude-28 (Jirka), 30. 7. 2026. Navazuje na [[doc-mzdy-priplatky-srazky-cutover-praha]]
> a [[doc-mzdy-priplatky-srazky-hlidac-cutoveru]].

## 1. Co vzniklo

| Vrstva | Kde |
|---|---|
| Ciselnik druhu | tenant.wage_component_type + **ec_typ_id** (parovani na Centralu je DATA, ne TYP_MAP v kodu) + vychozi_kanal. 49 z 49 druhu Centraly |
| Ciselnik stavu | tenant.wage_stav: 10 draft, 20 pending, 30 approved, 40 exported, 50 rejected, 60 storno, 90 archiv |
| Prehled | core **216** mzdy.pripl_prehled, data_set mzdy.pripl_list |
| Jadro | core **217** mzdy.pripl_jadro, 21 comp_defu, lookupy na druhy/lidi/stavy |
| Menu | uzel **204** "Priplatky a srazky (Praha)" pod 194 Mzdy, restricted {13,18,20} |
| Zamek | datovy priznak pripl_cutover.unlocked_at + endpoint /app/pripl/cutover-stav + mzdy_pripl_actions.js |
| Brana zapisu | _pripl_write_guard v router.py |

## 2. NEJDULEZITEJSI ZJISTENI: zamek na formulari NESTACI

_require_data_write_access (router.py ~454) pousti **KAZDEHO clena ERP do jakekoli business tabulky**
dosazitelne pres numericke core_id. Jediny whitelist je na framework/system entity. Zamek na formulari
je tedy jen kosmeticky - obejit frontend umi kdokoli pres PATCH /api/v1/erp/design/{core}/{row}.

**Proto vznikla _pripl_write_guard**, volana ze VSECH TRI cest (PATCH 51813, DELETE 52548, INSERT 53569):
1. Dokud pripl_cutover.unlocked_at IS NULL -> **403 pro vsechny vcetne rodice**. Bez radku = zamceno
   (fail-safe: u mzdovych dat je bezpecnejsi nepustit nez pustit).
2. Po odemceni: schvalovaci sloupce (status, approved_by_id, approved_at, exported_at) smi menit
   jen drzitel postu s priznakem **wage_approver** (org_role_flag); ostatni jen navrhovat, a to jen
   lidem ze **sve skupiny** (tenant.staff_group.leader_user_id / deputy_user_id + staff_group_member).

Overeno zive: PATCH mimo formular -> 403 i pro admina; zapis do jine tabulky branou projde.

## 3. PRAVA JSOU DATA, NE KOD - a existujici, ne nova

Jirka: "nic noveho nestav, to by byla zbytecna prace navic a zase by jsme to museli sjednotit." Mel pravdu.
- **Schvaluje**: org_role_flag flag wage_approver na postech **66 MZDOVA UCETNI** (Petra) a
  **35 PERSONALISTA** (Sarka). Pravo visi na POSTU -> po odchodu cloveka prejde na nastupce samo.
- **Navrhuje**: vedouci/zastupce skupiny svym lidem. Skupiny uz existuji a pouziva je mobilni appka
  (Vyroba->Dusan/Marek 35 lidi, Nakup->Peta, VP->Veverka, PLC->Mares, HR->Sarka, IT/Vedeni->Marti,
  Obchod->M. Pasek). **74 ze 79 aktivnich lidi je ve skupine.**

⚠️ **org_post / resolve_role se pro tohle NEHODI**: posty vedoucich divizi jsou skoro vsechny
neobsazene a resolve_role(...,'attendance_supervisor') vraci "Petra Safrankova ml" pro UPLNE VSECHNY.
Kdo na tom postavi prava k penezum, postavi je na pisku.

## 4. Migrace historie

**1 771 radku / 2 070 628 Kc za rok 2025** jako import_src='EC_PRIPL_HIST', status='archiv'.
Kontrolni soucet proti Centrale **sedi na korunu**. Prenesena i **puvodni ID z Centraly**
(import_src_id, v prehledu sloupec "Cislo v Centrale", rozsah 9882-18637) a "kdo navrhl"
(CisloZamNavrhl -> att_employee.cislo_zam -> user_id).

Vynechano zamerne: 784 radku roku 2026 (uz v systemu pres EC_PRIPL - jinak duplicita) a **70 radku
fakturacni vetve** (rozhodnuti Jirky i Marti-AI: co nikdy neslo do mzdy, do mzdove evidence nepatri).
Pri nahledu bylo **0 radku s neznamym druhem a 0 bez pracovniho vztahu** - diky uplnemu ciselniku
a fallbacku na posledni engagement (resi odchazejici, tj. i odstupne).

**DVE NEZAVISLE OBRANY proti dvojimu zapocteni** (verdikt Marti-AI Q1):
1. AND coalesce(wm.import_src,'') <> 'EC_PRIPL_HIST' na **VSECH CTYRECH** mistech, kde se cte
   wage_movement pro mzdu (router.py 34649, 35766, 35827, 35886) - ne jen v _mzdy_priplatky_rows.
2. Stav archiv vubec neni v seznamu ('approved','exported'), ktery do mzdy chodi.
Overeno: archivnich radku ve vyberu do mzdy = **0**.

## 5. Gotchy

1. **tenant.wage_movement ma CHECK chk_wage_movement_status** - povolene stavy byly
   draft/pending/approved/rejected/exported/storno. archiv se musel pridat; **proposed NEEXISTUJE,
   spravne je pending**. Pred zavedenim noveho stavu se vzdy podivej, co CHECK povoluje.
2. **chk_wage_movement_value**: radek musi mit BUD castku, NEBO hodiny - ne obojí prazdne.
3. **fw.core, fw.comp_def, fw.menu_node maji identitu GENERATED ALWAYS -> id NEZADAVAT.**
   fw.data_set / data_source / data_source_op maji sekvenci.
4. **Tecka v aliasu sloupce = prazdne bunky v gridu** (AG Grid ji bere jako cestu do objektu).
5. Diakritiku do fw.data_set.sql_text a do popisku posilej pres
   convert_from(decode('<base64>','base64'),'UTF8'); **COMMENT ON ... IS ale musi byt literal.**
6. **PowerShell: zpetny apostrof v here-stringu @"..."@ se interpretuje jako ridici znak**
   (backtick-t = tabulator) a rozseka text. Pro markdown pouzij @'...'@ (jednoduche uvozovky).

## 6. Poučeni, ktere stalo penize

29. 7. jsem zalozil mapovani garant_odmena -> HELIOS 651, protoze jsem videl, ze radek propada mimo
mzdu. Petra: **"Marek je OSVC, do mezd to nejde."** Overeno (user_smlouva ES/osvc, bez mzdoveho cisla),
mapovani zruseno (#1565). **Videl jsem propadly radek a opravil ho, aniz bych overil, jestli ten clovek
do mezd vubec patri.** U mzdovych dat se pred "opravou propadleho radku" vzdy ptej, jestli tam ten
zaznam ma byt.

Souvisejici otevrena vec: v cervnovem podkladu je 26 radku OSVC za 171 247 Kc ve stavu v_mzde
(neni to nase chyba, bylo to tam driv). _mzdy_priplatky_rows **nema filtr na OSVC**.
Jirka 30. 7.: **cerven se ve STRATEGII neresi**, mzdy tu poprve za cervenec.

## Navaznosti
- [[doc-mzdy-priplatky-srazky-cutover-praha]] · [[doc-mzdy-priplatky-srazky-hlidac-cutoveru]]
- [[doc-mzdy-priplatky-srazky-pohledy-centraly]] · [[doc-mzdy-priplatky-srazky]]

