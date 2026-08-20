# Priplatky a srazky: schvalovaci kolecko a zkusebni rezim pred prepnutim (30.7.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Priplatky a srazky - schvalovaci kolecko a zkusebni rezim

> oblast: mzdy - Claude-28 (Jirka), 30. 7. 2026. Navazuje na
> [[doc-mzdy-priplatky-srazky-praha-modul-a-migrace]] a [[doc-mzdy-priplatky-srazky-hlidac-cutoveru]].

## 1. Schvalovaci kolecko

Stavy: draft (Rozepsano) -> pending (Navrzeno) -> approved (Schvaleno) -> exported (Predano do mzdy).
Navic rejected (Zamitnuto), storno, archiv. Texty a cisla drzi ciselnik tenant.wage_stav.

**Vlastni endpoint POST /api/v1/erp/app/pripl/workflow** s telem {id, akce},
akce = navrhnout | schvalit | vratit.

Proc vlastni endpoint a ne obycejne ulozeni formulare: **audit "kdo a kdy" musi zapsat SERVER**.
Kdyby to posilal prohlizec, mohl by si kdokoli napsat, ze schvalila Petra. Klient posila jen
"co chci udelat". Server navic overi, jestli akce v danem stavu vubec dava smysl.

K tomu je v `_pripl_write_guard` zakaz menit `status`, `approved_by_id`, `approved_at`,
`exported_at` pres obycejny formular - **stav jde zmenit vyhradne temi tlacitky.**

Prava (Jirka 30. 7.):
- navrhnout / poslat ke schvaleni: vedouci nebo zastupce skupiny, ve ktere je dotycny clovek,
  nebo rovnou schvalovatel,
- schvalit / vratit: jen drzitel postu s priznakem `wage_approver` (MZDOVA UCETNI, PERSONALISTA),
- archivni radky (import_src=EC_PRIPL_HIST nebo status=archiv) se nedaji hnout vubec.

Tlacitka v jadru (`mzdy_pripl_actions.js`) se zobrazuji podle stavu zaznamu - server je ale
autorita, UI jen neukazuje, co nema smysl nabizet.

## 2. Zkusebni rezim pred prepnutim

**Problem:** Petra si ma modul proklikat PRED podpisem, ale cutover je zamceny - a odemknout ho
smi teprve jeji podpis. Klasicka slepice a vejce.

**Reseni (Jirka 30. 7.: "nech to zamcene pro ostatni a povol to jen pro Petru"):**
sloupec `tenant.pripl_cutover.zkusebni_uzivatele integer[]`. Kdo je v nem, smi zapisovat
i kdyz `unlocked_at IS NULL`. Ostatni (vcetne rodicu) dal narazi na 403.

**Bezpecnostni pojistka - tohle je to podstatne:** zapisy ve zkusebnim rezimu dostanou
v `_pripl_write_guard` natvrdo **`import_src='TEST'`** a vyber do mzdy je vylucuje stejne
tvrde jako archiv: `AND coalesce(wm.import_src,'') NOT IN ('EC_PRIPL_HIST','TEST')` na
**vsech ctyrech mistech** (router.py ~34796, 35913, 35974, 36033).
Bez toho by schvalena zkusebni odmena spadla do ostre mzdy.

Uklid po zkousce: `DELETE FROM tenant.wage_movement WHERE tenant_id=2 AND import_src='TEST'`
a vyprazdnit `zkusebni_uzivatele`.

UI: endpoint `/app/pripl/cutover-stav` vraci navic `zkusebni: true`, formular se odemkne,
ale nahore je modry pruh "Zkusebni rezim - co tu zalozis, se do mzdy nedostane".
Overeno 30. 7.: pro uid 20 (Jirka) zustava `odemceno:false` a zapis konci 403.

## 3. Co jeste chybi, nez hlidac odemkne

Ctyri kontroly v `tenant.pripl_cutover` (kontrola_1..4) **nema zatim jak nikdo odskrtnout** -
neni na to ani UI, ani proces. Dokud zustanou `false`, hlidac NEODEMKNE ani po podpisu Petry.
Zatim se odskrtavaji rucne pres schvalovaci banner, s poznamkou kdo overil. Kdyby to melo
byt caste, patri to do UI.

## Navaznosti
- [[doc-mzdy-priplatky-srazky-praha-modul-a-migrace]] · [[doc-mzdy-priplatky-srazky-hlidac-cutoveru]]
- [[doc-mzdy-priplatky-srazky-cutover-praha]]

