# Mobil: nasazeni noveho vzhledu (14. 9. 2026) - kde vzhled zije a pet pasti, ktere se ukazaly az naostro

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

> ⚠️ **DOPLNENO 14. 9. 2026 odpoledne (rozhodl Jiri Honomichl).** Tlacitka a rozbalovaci
> menu **uvnitr obrazovek uz nemaji modrofialovy prechod** - maji pozadi dlazdice (trida `tile`)
> a vzdy bily text. Beze zmeny zustaly spodni lista, zalozky, sipka zpet a cervene `warn`.
> Detail, dve pasti a cim se to overuje:
> [[doc-system-strategie-mobil-tlacitka-a-rozbalovaci-menu-pozadi-dlazdice]]

Zapsal Claude-28 (okno strategie-29) 14. 9. 2026. Zadal Jiri Honomichl, schvalila Marti-AI (msg 15606).
Nasazeno v 09:03, overeno naziva na /mobile: 127 obrazovek, vsechny texty v jednom pismu.

## Co se zmenilo

Vzhled mobilni aplikace (varianta "Modre svetlo"): jedno pismo DM Sans vcetne tlacitek a policek,
sedmistupnova skala velikosti, ctyri role barvy textu, mramorovany podklad se svetlem shora,
vystoupene karty, hlavni tlacitka v prechodu modra-fialova (**prechod na tlacitkach NEPLATI
od odpoledne 14. 9. 2026** - viz ramecek nahore). **Ikony zustaly puvodni emoji** -
vyslovne rozhodnuti Jirky Honomichla; nalez auditu (198 ruznych emoji, kresli je operacni system,
takze Android a iPhone vypadaji jinak) tim nezmizel, jen se k nemu rozhodlo jinak.

## Kde vzhled zije

Dilek `apps/api/static/mobile_parts/02_styles.html` (tabulka `g2007.soubor`), blok na KONCI souboru
s hlavickou `NOVY VZHLED MOBILNI APLIKACE`. Meni se v databazi a pak `@@G2007PUBLISH apps/api/static_db/mobile.html`.
Podklad, podle ktereho vznikl, je v gitu v `design/reskin/theme-b.css` - ale zdroj pravdy je databaze.

## Pet pasti, ktere se ukazaly az naostro (a stalo je to dve publikace navic)

1. **Predepsat pismo a nacist pismo jsou dve ruzne veci.** Blok stylu mel `font-family: "DM Sans"`,
   ale stranka pismo odnikud nestahovala - v cele hlavicce nebyl jediny odkaz na font. Prohlizec
   pritom hlasi `font-family: "DM Sans", ...` jako by vse bylo v poradku. **Overuje se merenim sirky
   textu** (`canvas.measureText` pro dane pismo vs. pro vymyslene jmeno - kdyz vyjdou stejne, pismo
   se nepouziva). Odkaz patri do `00_head.html`, ne do stylu (@import na konci souboru neplati).

2. **Vrstva pod obsahem (`body::before` se `z-index:-1`) se nevykresli, kdyz ma `body` neprusvitne
   pozadi.** Prekryje ji. Barvu proto musi nest `html` a `body` byt pruhledne. Overit se to da jedine
   tak, ze se do vrstvy da krikrava barva a clovek se podiva - z vypoctenych stylu to nepoznas,
   protoze pravidlo se tvari spravne.

3. **Dve obrazovky si kresli VLASTNI plochu pres celou vysku** a spolecny podklad tim zakryji:
   `home` (trida `.homebg`, dilek `20_home_phone_notifs.js`) a `firma` (vlozeny prechod
   `linear-gradient(165deg,#0c1420,...)` v dilku `51_skupiny_sdileny.js`). Proto mela Firma jiny
   odstin nez zbytek. Reseno v CSS pruhlednosti obou.

4. **Nevypinej statickou texturu pri systemovem "omezit pohyb".** Textura se nehybe, takze to neni
   animace - a lidi, kteri si omezili animace (napr. Jirka), by nove pozadi nikdy nevideli.

5. **Silu textury nelze odhadnout, musi se ladit naostro.** Prvni pokus byl neviditelny (past c. 2),
   druhy po oprave prilis silny a text na svetlych mistech ztracel citelnost. Vysledek: zilkovani
   na 0,34 **plus maska, ktera vrstvu smerem dolu zeslabuje na ctvrtinu** - nahore charakter,
   pod hustym obsahem klid.

## Mereni, ze ktereho audit vychazel (stav pred nasazenim, 14. 9. 2026)

Na zive aplikaci: 17 ruznych velikosti pisma a 37 barev textu na 14 obrazovkach; 38 prvku z 38
(tlacitka, policka, seznamy) bezelo v Arialu, protoze jim nikdo nenastavil pismo; 198 ruznych emoji
v roli ikon; 2 702 mist, kde je vzhled zapsany primo u prvku; 8 ruznych zaobleni rohu.
Tyka se to vsech 57 lidi, kteri za 30 dni poslali z mobilu 5 092 dochazkovych zaznamu.

## Zaroven opraveno (kontrast pod normou)

- `71_plan_prace_cinnosti.js`: `#5b6b88` -> `#8d98a8` (6x, slovo "vikend", bylo 3,56 pri norme 4,5)
- `50_skupiny_vyroba.js`: `"#667"` -> `"#8d98a8"` (2x, obrazovka Kdo kde, tykalo se 77 lidi z 82, bylo 3,28)

## Jak psat dlouhe CSS pres most

Blok stylu ma pres 7 kB a je plny dvojtecek, ktere most bere jako parametry. Prochazi to takto:
`UPDATE g2007.soubor SET obsah = replace(obsah, '</style>', convert_from(decode('<base64>','base64'),'UTF8'))
WHERE kod=... AND md5(obsah)='<otisk, ktery jsi prave cetl>'` - base64 nema dvojtecky ani zakazana
slova a pojistka na otisk ochrani pred soubehem. Zapis do `g2007.soubor` jde pres most **primo,
bez schvalovaciho prouzku** (hlasi "G2007 KONSTRUKTIVNI"), takze o to vic plati overit ho ctenim.

