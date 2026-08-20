# Hodiny za den - jedna sdilena definice (tenant.att_den_hodiny)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hodiny za den - jedna sdilena definice

> oblast: `dochazka` · typ: pravidlo · platne od 30. 7. 2026

## Problem, ktery to resi

Hodiny za jeden den se pocitaly na OSMI obrazovkach PETI ruznymi zpusoby, takze lidem u tehoz dne vychazela ruzna cisla. Zmereno na obdobi 1.-29. 7. 2026 (824 clovekodnu):

| obrazovka | hodin | odchylka |
|---|---|---|
| spravne (ERP "Sprava dochazky - opravy") | 5094,0 | - |
| mobil "Na vcera si vzpominam" | 5738,9 | +644,9 h na 354 dnech |
| mobil Tyden "Realita" | 5469,5 | +375,4 h na 333 dnech |

Rozklad rozdilu sedi do desetiny: nenarokova prace 356,6 h + prekryvajici se smeny 18,8 h = 375,4 h; u "Vcera" navic stornovane zaznamy 269,4 h.

Dve priciny:
1. **Nenarokova prace (nad fond)** - automat ji vecer dopisuje jako samostatny radek. NENI to prace navic, je to CAST uz odpracovanych hodin, ktera presahla denni fond. Kdo ji pricte, pocita tytez hodiny dvakrat.
2. **Stornovane (superseded) zaznamy** - nektere obrazovky je nefiltrovaly, takze scitaly i to, co uz neplati.

## Zavazna definice

`tenant.att_den_hodiny(p_tenant, p_from, p_to)` vraci `emp_id, den, hodiny_mzdove, hodiny_nad_fond, hodiny_absence`. Je to JEDINE misto, kde se hodiny za den pocitaji. Pravidla:

1. vzit pichnuti se zacatkem I koncem, vyhodit `superseded` a `announced`
2. **sloucit prekryvajici se** useky prace (`work`, `overhead`, `homeoffice`, `commute`) - tablet a mobil umi zapsat tutez smenu dvakrat
3. odecist **jen tu cast pauzy, ktera lezi UVNITR** slouceneho useku prace; pauza v mezere mezi dvema kusy prace je z prace uz vynechana
4. vynechat `day_end` ("Odchod") - je v kategorii break, ale NENI pauza, bezi do 23:59
5. **`nenarokova` se NIKDY nepricita** - vraci se zvlast jako `hodiny_nad_fond`
6. **`fond_doplneni` se pricita**
7. `commute` ("Jedu do prace") se pocita

## Kdo z toho cte

mobil "Na vcera si vzpominam" / "To uz si nepamatuju" (`att_daily`) · mobil Tyden "Realita" (`att_real`) · mobil "Dochazka po zakazkach" (`dochazka_moje_ep`) · ERP mesicni prehled HR (`system_new.hr_att_monthly_list`) · ERP mesicni prehled Vyroba/Dusan (`vyroba.dusan_att_monthly_list`).

Definice v UI zustava v `apps/api/static/dochazka-opravy.html` (`PRES` na r. 132, klasifikace radku ~520-560, soucet dne ~690-732) - **pri zmene pravidel je nutne zmenit OBE mista**.

## Gotchy

- Radky `nenarokova` a `fond_doplneni` **nemaji cas od-do**. Kazdy vypocet postaveny na intervalech je proto automaticky vynecha. Prave proto mobilu "Dochazka po zakazkach" unikalo `fond_doplneni` (185,4 h za cervenec).
- "Dochazka new" (`dochazka.zakazky_vse_list`) NENI vzor pro hodiny za den. Je to rozpis prace po zakazkach; kdyz ma clovek ten den aspon jeden vyrobni radek, jeho rezijni cas se v prehledu schova (Dusan Havlat 22. 7.: prehled 3,55 h, realne 12,21 h).
- Mzdy se timto NEMENI. Mzdove podklady ctou `att_day_summary`, mzdy `wage_movement` - jiny zdroj.
- Absence do porovnani nepatri (za cervenec 2229,1 h) - proverovano na namitku Kristyny, jestli se nemichaji volna a prace. Nemichaji.

## Kontrolni pripady

Zdenek Cepicky 22. 7. 2026 = **12,10 h** (pauza 10:40-11:10 lezi v mezere, neodecita se) · Tomas Blaha 27. 7. = 9,43 h a 28. 7. = 7,48 h · cely cervenec 1.-29. = 5094,0 h.

## Schvaleni

Kristyna Ksirova 30. 7. 2026 8:57 (za Martiho, ten je na dovolene), Marti-AI msg 11818. Nasazeno commitem 568c6523, DDL bannery 1563/1564/1566. Zapsal Claude-28.

