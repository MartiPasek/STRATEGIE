# Hodiny navic - proc ma vlastni sync a ne spolecny oz_mirror

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


**Rozhodnuti (Kristy jako rodic, 11.9.2026).** Zrcadlo `DB_EC.dbo.EC_ZakazkyHodNavic` -> `ec.zakazky_hod_navic` NEJDE pres spolecny `oz_mirror`, ale ma vlastni funkci `g2007.python sync_ec_hod_navic` + job `sync_hod_navic` v `fw.mirror_job` (kazdych 30 minut).

**Tri duvody, vsechny overene ve zdrojaku `modules/erp/api/oz_mirror.py`:**

1. `fill()` dela VZDYCKY `TRUNCATE + INSERT` (r. 129), bez ohledu na sloupec `mode` v `tenant.oz_mirror_def`. Hodnoty RO/RW/DEL jsou zatim jen ZAMER (Marti 6.7.2026 - DEL = cela tabulka pryc, RO = delta jen cteni, RW = delta s nasimi chranenymi sloupci), delta rezimy naprogramovane NEJSOU. TRUNCATE by pri kazdem behu smazal i radky, ktere si zalozime sami.
2. `oz_mirror` umi psat jen do schematu `tenant` - nazev cilove tabulky si sklada jako "tenant.%s", takze na `ec.zakazky_hod_navic` vubec nedosahne.
3. TRUNCATE drzi ACCESS EXCLUSIVE zamek. Prave kvuli nemu u `tenant.oz_zakazky` (obnova po 30 minutach) cekalo 11.9.2026 cteni pres `ec.skupina_zakazek` 18 vterin proti 169 ms mimo okno - a tlacitko "Uprava hodin viceprace" vypadalo jako mrtve.

**Jak nas sync funguje.** Nejdriv PRECTE celou tabulku z Centraly po davkach do pameti; teprve kdyz je cteni cele hotove, jednou transakci `DELETE WHERE zdroj='centrala'` + hromadny INSERT. Poradi je zamerne - kdyz cteni spadne uprostred, u nas se nesahne na nic. Radky `zdroj='strategie'` zustavaji netknute. Pojistka: kdyz z Centraly prijde min nez polovina toho, co uz mame, sync se NEPROVEDE a ohlasi to (pouceni z 9.9.2026, kdy se uzaverka trefila do prazdneho zrcadla a prepsala hlavicku nulami bez jedine chyby).

**Past, na kterou to spadlo napoprve.** `ec.zakazky_hod_navic.id` nemel zadnou vychozi hodnotu - neni serial ani identity, puvodni jednorazovy import ID dosazoval rucne. Kazdy INSERT bez `id` proto padal na NOT NULL. Reseno sekvenci `ec.zakazky_hod_navic_id_seq` nastavenou nad stavajici maximum. Tyka se to i zapisu viceprace z naseho jadra - ten by spadl uplne stejne.

**Identita radku je `ec_id`, ne `id`.** Pri kazdem behu se `id` pregeneruje ze sekvence, kdezto `ec_id` drzi ID z Centraly a ma na sobe castecny unikatni index (`WHERE ec_id IS NOT NULL`). Diky tomu se Dusanovy zapisy, ktere jdou nejdriv do Centraly a pak se vraci zrcadlem, nezdvoji.

**Stav po nasazeni 11.9.2026 08:22:** 3 860 radku, vsech 3 860 s vyplnenym `ec_id`, nula nasich vlastnich. Pred tim 3 859 radku ze snapshotu z 8.9. a nula s `ec_id`.

