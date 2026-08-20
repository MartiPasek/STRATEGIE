# MAPA - kde se dochazka za den kresli z HLAVICKY a kde z ROZPADU (prohlidka 20.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## K cemu to je
`tenant.att_entry` (hlavicka) drzi JEDNU zakazku na radek. Do 20.8.2026 se pri prepnuti zakazky za chodu prepisovala in-place, takze hlavicka nesla POSLEDNI volbu bloku a kazde misto, ktere kreslilo den jen z ni, ukazovalo neuplnou pravdu. Skutecnost zije v rozpadu `tenant.vyroba_work`.
Od 20.8.2026 se radek deli ([[doc-dochazka-deleni-zaznamu-pri-prepnuti-zakazky]]), takze nove zaznamy uz nelzou. **Historie ale zustava** - za rok 2026 sedi 382,4 h na 72 zakazkach jinak, nez se doopravdy delalo. Proto tahle mapa plati dal.

## Mista, ktera dnes rozpad UZ UKAZUJI
| Kde | Jak |
|---|---|
| ERP Opravy dochazky (`dochazka-opravy.html`, `att_fix_day`) | rozpad vcetne historie stornovanych radku (5.8.2026) |
| Mobil - Opravy dochazky (Firma - Spoluprace) | "rozpad (N krat)", rozbali tuknuti (5.8.2026) |
| Mobil - potvrzeni dne ("Radeji chci videt detaily") | doplneno 20.8.2026, `att_day_detail` vraci pole `useky` |
| Mobil - detail zaznamu (`_jobOverlay`) a seznam pro "Nesedi mi den" | doplneno 20.8.2026, `att_list` vraci `useky`, znacka pres `_rozpadZnacka` |
| ERP Dochazka po zakazkach (`dochazka-po-zakazkach.html`) | jede primo z rozpadu |
| ERP grid `dochazka.zakazky_vse_list` | jede z rozpadu |
| ERP gridy `system_new.hr_att_entries_list`, `vyroba.dusan_att_entries_list`, `vyroba.dusan_dochazka_vse_list` | doplneno 20.8.2026 - v bunce zakazky pripis "(rozpad N krat)"; rozpis se v mrizce vypsat neda, je to signal jit do Oprav |
| Demo appka (`att_day_detail_demo`, `att_list_demo`) | doplneno 20.8.2026 kvuli parite; demo data rozpad zatim nemaji |

## Mista, ktera hlavicku ukazuji SPRAVNE (nemenit)
- `att_status` a `app_vyroba_lidi` - ukazuji BEZICI volbu ("na cem ted delam"), tam je hlavicka pravda.
- Mobilni seznam Dnesek/Historie - zakazku VUBEC nezobrazuje (rozhodl Marti 19.6.2026, dochazka = jen pritomnost).
- `51_skupiny_sdileny.js` a `71_plan_prace_cinnosti.js` - uz jedou z useku.

## OTEVRENE - jedno misto, kde se z hlavicky pocitaji PENIZE
`vp_finance_zakazky` (dlazdice "Finance zakazek" pro vedeni, Kristy 3.8.2026) scita hodiny a mzdu per zakazka pres `SUM(e.hours) GROUP BY e.project_ref`. **NEMENENO** - je to Kristyna domena a ma to overene proti Centrale (VR10477 zisk +21172). 20.8.2026 ji Jirka poslal nalez i hotovy navrh zmeny zdroje na `vyroba_work` e-mailem; rozhoduje ona.

## Jak si takove misto najit priste
Dotaz nad zivym kodem, ne z hlavy - `g2007.python` a `g2007.soubor` na `project_ref`, a `fw.data_set` na `sql_text LIKE project_ref`. Rozliseni je jednoduche - ukazuje to BEZICI volbu (v poradku), nebo UZAVRENY blok v minulosti (musi umet rozpad)?

