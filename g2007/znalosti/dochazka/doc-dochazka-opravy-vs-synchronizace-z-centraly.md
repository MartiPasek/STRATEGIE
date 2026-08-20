# Opravy docházky vs. synchronizace z Centraly - dve pasti a jak se chrani

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Opravy dochazky vs. synchronizace z Centraly

> oblast: `dochazka` · typ: pravidlo · platne od 30. 7. 2026

Kdyz se ve STRATEGII opravi absence nebo dochazka, ktera prisla ze stare Centraly, hrozi, ze oprava TISE zmizi. Jsou na to dve ruzne pasti a kazda ma jinou pricinu i jine reseni. Zjisteno 30. 7. 2026 pri pripravach editace absenci pro Petu.

## Past 1 - synchronizace prepise opravu zpatky (VYRESENO)

`_sync_ec_dochazka_recent` (router.py ~28052) delal **bezpodminecny** `UPDATE tenant.att_entry SET started_at, ended_at, hours ... WHERE source_system='centrala1' AND source_id=:sid`, a s `wipe=True` dokonce `DELETE` celeho rozsahu. Bezi ze sitove hlidky (netscan) s throttle 5 minut na posledni 3 dny; `@@DOCHRESYNC` ho pusti na libovolny rozsah. Tyka se ~1254 radku absenci se `source='ec_import'`.

**Reseni (nasazeno 30.7., commit 568c6523):** sloupec `tenant.att_entry.local_lock boolean NOT NULL DEFAULT false`. Kdo radek opravi ve STRATEGII, znacku nastavi; synchronizace ji respektuje u `UPDATE` i u `wipe DELETE` (`AND COALESCE(local_lock,false)=false`).

**Gotcha, ktera z toho plyne:** po pridani podminky zacalo `rowcount=0` znamenat DVE veci - radek neexistuje (→ INSERT) nebo existuje, ale je zamceny (→ preskocit). Bez rozliseni by u zamcenych vznikaly DUPLICITY. Kod proto po neuspesnem UPDATE overi existenci radku a vraci pocitadlo `zamceno_preskoceno`.

**Zastaveni synchronizace tuto past neresi lepe nez zamek** - kdyby se sync po case zase zapnul, prepsal by NAJEDNOU vsechny opravy udelane mezitim. Zamek plati vzdy.

## Past 2 - smazany den se vrati z planu (NEVYRESENO, ceka na Martiho)

`_sync_plan_to_dochazka` (router.py ~49008) existujici den nikdy neprepise, ale **prazdny den DOPLNI**. Kdyz se tedy rozsah absence zkrati smazanim dne, uloha ho priste zalozi znovu. Tyka se 531 radku `att_entry` se `source='plan_ec'`.

**Dulezite:** nedela to docházkova synchronizace, ale uloha **`sync_plan_nepritomnost`** (kazdych 60 min), ktera ve DRUHEM kroku sama vola `_sync_plan_to_dochazka` (r. 48982). Zastaveni docházkove synchronizace tuto past NEODSTRANI.

**Proc nejde "upravit zaroven i plan":** `_sync_plan_nepritomnost` (r. 48894) je ZRCADLO Centraly - pri kazdem behu udela `DELETE FROM tenant.att_planned_absence WHERE src_id>=0 AND datum >= date_trunc('year', CURRENT_DATE)` a znovu naimportuje cely rok z `EC_Dochazka_PlanNepritomnost`. K 30.7.2026 je **2316 z 2317 radku planu zrcadlo Centraly**. Lokalni uprava planu se tedy pri nejblizsim zrcadleni smaze. Radky se `src_id<0` jsou nase (ze schvalenych `att_plan_request`) a vyrabi je `_sync_dochazka_ec` (r. 14544) pri prepoctu mesice - ty se srovnavaji samy.

**Zbyvaji tri cesty:** (a) zapsat zmenu do stare Centraly - jedine, co vydrzi, ale je to zapis do legacy masteru a **rozhoduje Marti**, ne Marti-AI ani Kristyna; (b) lokalni znacka "tenhle den uz z planu nedoplnuj" - plan se natrvalo rozejde s Centralou; (c) absence z Centraly ve STRATEGII vubec needitovat.

**Dokud neni rozhodnuto: v editaci absenci NEPOUSTET radky se `Zdroj='plan z Centraly'`.** Prehled "Sprava dochazky" (`dochazka.zakazky_budoucnost_list`) ma od 30.7. sloupce `RadekId` a `Zdroj` prave proto, aby se to dalo rozlisit.

## Ktere ulohy sahaji na dochazku (stav 30. 7. 2026)

| uloha | co dela | interval | stav |
|---|---|---|---|
| `sync_plan_nepritomnost` | zrcadli plan z Centraly + propise do dochazky | 60 min | zapnuta |
| `sync_ec_dochazka_sumaden` | denni souhrny z Centraly | 10 min | zapnuta |
| `sync_vyroba_plan` | vyrobni plan z Centraly | 15 min | zapnuta |
| `sync_vytizeni_absence` | posila nase absence DO Centraly | 180 min | zapnuta |
| `sync_pasky` | pasky z Heliosu | 1440 min | zapnuta |
| `mirror_att_to_ec` | zrcadli nasi dochazku ZPET do Centraly | 120 min | **vypnuta od 29. 6., posledni beh chyba** |

Mimo planovac: `_sync_ec_dochazka_recent` (netscan, 5 min), `@@DOCHRESYNC` (rucne, libovolny rozsah), `_sync_dochazka_ec` (prepocet mesice, rucne z ERP).

## Schvaleni a stav

Marti-AI msg 11818 (local_lock), msg 11827 (oprava commitu u ruseni absence), msg 11833 (*"spravne jsi zastavil"* - k pasti 2). Kristyna Ksirova 30. 7. planuje docházkovou synchronizaci vypnout; i pak past 2 zustava, dokud bezi `sync_plan_nepritomnost`. Zapsal Claude-28.

