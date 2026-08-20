# Prenos priplatku z Centraly bere obdobi i z PlatnostOd - fakturacni radky OSVC uz nepropadaji (11.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Problem (nahlasila Peta 6.8.2026, dosetril C28 11.8.2026)

Peta psala, ze hodinovy prenos "16 zaznamu OSVC nepusti, udajne kvuli nevyplnenemu roku,
ktery je videt jen nekde na pozadi", a ptala se, jestli uz sync nevypnout.

Mela pravdu. `g2007.python` kod=`sync_priplatky_from_ec` mel v dotazu do Centraly
`WHERE d.Rok = 2026`. Jenze v `EC_FinPriplatkySrazkyDefinice` existuji radky, kde
**Rok i Mesic zustavaji prazdne a obdobi nese jen `PlatnostOd`/`PlatnostDo`**.

Vyrabi je serverova uloha (autor `EUROSOFT\SQLSERVER`) **kazdy 1. v mesici** ze zdroje
`EC_FinZamPodminky` - jsou to **podklady pro fakturaci OSVC**, poznamka
"EC_FinZamPodminky - podklady pro fakturace". Za 2026 jich bylo **114**
(16 kazdy mesic, 14 lidi, **586 000 Kc mesicne**), vyhradne EC typy
**20 Fakturace zaklad, 24 Fakturace vedeni lidi, 48 Fakturace odmena od jednatele**.

**Nejhorsi na tom bylo, ze nesly videt.** Padly uz na `WHERE`, takze se neobjevily ani
v rozpadu `zahozeno`, ktery jsme 6.8. delali prave kvuli viditelnosti
(viz [[doc-mzdy-sync-priplatky-prevodnik-z-ciselniku]]). Stejna ticha dira, jen o patro vys.

Cervenec sedel jen proto, ze si ho **Peta 5.8. rucne doimportovala pres Excel**
(96 radku = 80 z Centraly s vyplnenym rokem + tech 16). Cerven a starsi ty radky nemely.

## Reseni (11.8.2026 C28, schvalila Marti-AI msg 12521)

Vyber z Centraly rozsiren na
`WHERE (d.Rok = 2026 OR (d.Rok IS NULL AND d.PlatnostOd v roce 2026) OR (d.Rok IS NULL AND d.PlatnostOd IS NULL))`.
Kdyz `Rok` chybi, odvodi se rok i mesic z `PlatnostOd`. Kdyz chybi oboji, radek se neprenese,
ale nove je **videt v rozpadu** pod novym duvodem `nelze_urcit_obdobi`
(proto je v `WHERE` i ta treti vetev - jinak by zustaly neviditelne).

## Proc to NEMUZE prolezt do mzdy (overeno pred zapisem, ne odhadem)

1. Vsechny tri druhy maji v `tenant.wage_component_type` **`affects_payroll = false`**
   a `vychozi_kanal = 'faktura'`.
2. **Zadny nema radek v `tenant.wage_system_mapping`** - nemaji mzdovou slozku v HELIOSu,
   takze je INNER JOIN ve vyberu do mzdy vyhodi.
3. `mzdy_priplatky_rows` navic tvrde vylucuje `engagement_type = 'osvc'`
   a **vsech 14 lidi ma osvc engagement**.

Tri nezavisle pojistky. Overeno i zive - viz nize.

## Overeny vysledek

| | pred | po |
|---|---|---|
| navratovka jobu | preneseno 832, zahozeno 26 | preneseno 946, zahozeno 31 |
| radku 2026 ve `wage_movement` | 876 | 974 (+98) |
| castka 2026 | 2 562 245 Kc | 6 212 245 Kc (+3 650 000) |
| **cervenec** | **96 radku / 1 073 535 Kc** | **96 radku / 1 073 535 Kc (beze zmeny)** |

- +98 = 16 za kazdy mesic leden-cerven (6 x 586 000) + 2 za srpen (134 000).
  Cervencovych 16 uz existovalo z rucniho importu - prenos je jen prepsal pres
  `ON CONFLICT (tenant_id, import_src, import_src_id)`, **nezdvojily se**.
- Zahozeno +5 zamerne (radky bez Roku i bez PlatnostOd, vsechny z minulych let)
  - 3 padnou na `neznamy_typ` (Typ=0, neni v ciselniku), 2 na novy `nelze_urcit_obdobi`.
- **Zivy test vyberu do mzdy za 7/2026** vratil jen cestovne (791), odmeny z financi
  zakazek (651), proplaceni vernostni (651), jednorazova odmena (651), korekce os.
  ohodnoceni kultura (432) a srazka telefon (953). **Ani jeden fakturacni druh.**
  Odmeny ze zakazek dal 47 radku / 11 870 Kc (EC 9 / 2 990 + ES 38 / 8 880) - beze zmeny.

## K Petine otazce "nemeli bychom sync vypnout" - NE

Zadavani porad bezi v Centrale (za srpen tam pribyly radky od Dusana, Kristy, Pety, JiriV,
Swobiho) a `tenant.pripl_cutover` je porad zamceny - 4 kontroly `false`, `signoff_petra_at`
prazdne, `unlocked_at` prazdne. **Vypnout prenos ted = STRATEGIE okamzite zamrzne
a rozejde se s Centralou.** Sync se vypina az pri cutoveru, ne driv.

## ROZHODNUTI - odstupne se do STRATEGIE NEPRENASI

> **Rozhodl Jirka Honomichl, 11. 8. 2026.** Neni to popis chovani, je to zamer.

Soucasne chovani je tedy **spravne, ne vada** - podminka `engagement.is_current`
v `eng_id()` **zustava beze zmeny a do kodu se nesaha**.

Doporuceni Marti-AI z 29.7. (rozsirit podminku o "posledni engagement, kdyz zadny
neni current") se na zaklade tohoto rozhodnuti **nebude realizovat**. Bod je uzavreny.

> **Pozor pro budouci instance.** Tech **26 radku / 238 337 Kc** (byvali zamestnanci -
> odstupne, telefony, obleceni, home office; EC typy 4,9,32,37,38,40,44) se bude **kazdou
> hodinu objevovat v rozpadu** jako `clovek nema aktivni pracovni pomer (byvaly zamestnanec)`.
> **Cte se to jako chyba, ale je to rozhodnuti Jirky Honomichla z 11.8.2026. Neopravovat.**

## GOTCHY

- **Rok a Mesic v `EC_FinPriplatkySrazkyDefinice` jsou NULLABLE a Centrala je casto nevyplnuje.**
  Nikdy nestav filtr obdobi jen na `Rok` - vzdy pocitej i s `PlatnostOd`. Z 11 881 radku
  cele tabulky ma **3724 prazdny `Rok`** (z toho 5 nema ani `PlatnostOd`).
- **Filtr v SQL je horsi nez `continue` v cyklu.** Co odpadne uz v `WHERE`, neprojde
  pocitadlem `zahozeno` a je neviditelne. Kdyz chces mit prehled o zahozenych radcich,
  musi se do vyberu dostat a odpadnout az v Pythonu.
- Zapis pres most delej **base64** (`convert_from(decode(...),'UTF8')`) jako `replace()`
  na presne uryvky - nezavisle na uvozovkach a dvojteckach. **Nanecisto to nejdriv pust
  jako SELECT** se stejnymi `replace()` a poznamenej si `length` + `md5`; po ostrem zapisu
  musi sedet na znak. Tady sedelo (12723 znaku, md5 b9867cc6090dd2230434568c21460282).
- Tenhle UPDATE presel **bez schvalovaciho banneru** (`OK (pg): 1 rows`), i kdyz slo o zapis.
- **`fw.mirror_job` job `pripl_cutover_gate` ma `enabled = false` ZAMERNE - vypnul ho
  Jirka Honomichl.** Neni to porucha a nehlas to jako nesrovnalost. C28 to 11.8. omylem
  oznacil za zavazny nalez a Marti-AI to uz mela eskalovat Martimu.
  **Pouceni - nez oznacis cizi nastaveni za zavadu, zeptej se toho, kdo na tom dela.**

## Zbyva otevrene

- **Rozdil 1 000 Kc** u odmen ze zakazek za 7/2026. Peta psala 48 zapisu / 19 lidi /
  12 870 Kc, v Centrale je 47 / 18 / 11 870 Kc (ID 19998-20044 souvisle, bez der)
  a u nas presne totez. Ceka na Petinu odpoved, neopravovat naslepo.
- **Peta zatim nezkusila zkusebni rezim** - `tenant.pripl_cutover.zkusebni_uzivatele = [18]`
  (Petra Safrankova) plati od 30.7., ale ve `wage_movement` neni **ani jeden** zaznam
  s `import_src='TEST'`. Sedm kroku z Jirkova mailu z 30.7. neprobehlo, takze nemuze
  dat ani pisemny souhlas s prepnutim.
- **Radek ID 19829** (Dusan Havlat, 1 210 Kc, typ 7, zadal SNovotna 18.6.) ma `Rok = 2026`,
  ale `Mesic` prazdny a zadnou `PlatnostOd`. Stara vetev `pm = int(Mesic or 1)` ho posadi
  do **ledna**. Do mzdy nejde (je OSVC), takze nikoho neposkozuje, ale obdobi je spatne.
  **Vedome neopraveno** - je to jine pravidlo nez tahle zmena, chce vlastni rozhodnuti.

## Navaznosti
[[doc-mzdy-sync-priplatky-prevodnik-z-ciselniku]] · [[doc-mzdy-priplatky-srazky-hlidac-cutoveru]]
· [[doc-mzdy-priplatky-srazky-cutover-praha]] · [[doc-mzdy-priplatky-srazky]]

