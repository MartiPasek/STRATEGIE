# Mzdove hodiny dne - jedna definice pro mobil i ERP (day_end NENI pauza)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mzdove hodiny dne - jedna definice pro mobil i ERP

Plati od 27.7.2026 (Jirka/C28, commit 2096d429). Zdroj pravdy pro hodiny = `tenant.att_entry`
(rozhodnuti Marti Paska 26.7.2026).

## Vypocet (musi byt stejny na vsech obrazovkach)

1. Vezmi zaznamy `att_entry` se ZACATKEM I KONCEM, `status NOT IN ('superseded','announced')`.
2. Prítomnost = `att_entry_type.category='presence'`. **SLUC PREKRYVY** (dva zdroje, tablet+mobil,
   umi zapsat tutez smenu 2x; prosty SUM by dal 16 h misto 8).
3. Pauzy = `category='break'` **KROME `code='day_end'`**. Odecti jen tu cast pauzy, ktera lezi
   UVNITR slouceneho pracovniho intervalu (pauza v mezere mezi dvema kusy prace uz je z prace
   vynechana, druhe odecteni by ubralo hodiny 2x).

## GOTCHA: `day_end` je v kategorii `break`, ale NENI pauza

`code='day_end'` ("Dnes uz se mnou nepocitej", v mobilu "Mam volno", v prehledech "@ Odchod")
je STAV, ne prestavka - **bezi az do 23:59**. Kdyz se s nim zachazi jako s pauzou, u kazdeho,
kdo se po "odchodu" znovu pichl, se hodiny tise ubiraji.

- Chyba byla v `/app/dochazka/moje` (mobil "Dochazka po zakazkach") od 27.7. dopoledne
  (commit b407938b) do 27.7. odpoledne (fix 2096d429): filtr bral `category IN ('presence','break')`
  a day_end tim propadl do pauz.
- Doklad z cervence: os. 475 8.7. -2,42 h; os. 105 22.7. -3,55 h (spravne 12,22 h = fond 8
  + nenarokove 4,22); os. 49 14.7. -0,08 h.
- ERP "Opravy" to dela spravne uz od 21.7. (`dochazka-opravy.html`: `if(isDE) return;`).

## Dalsi typy, na ktere pozor

- `fond_doplneni` a `nenarokova` maji `category='presence'`, ale **NEMAJI casy od-do**
  (overeno: 107 + 164 radku v cervenci, vsechny bez casu), takze do vypoctu podle casu
  nespadnou. `nenarokova` je navic CAST odpracovanych hodin (hodiny nad fond), nikdy se
  nepricitava.
- `commute` ("Jedu do prace") ma `category='travel'` - ERP "Opravy" ho do souctu pocita
  (je v jejich seznamu PRES), vypocet v mobilu ne. V datech jsou zatim jen 2 takove radky,
  ale je to latentni rozdil v definici - pri dalsi uprave sjednotit.

## Kde se hodiny pocitaji jinde

`tenant.att_day_summary` = 1:1 zrcadlo Centraly (`EC_Dochazka_SumaDen`), NENI derivat `att_entry`.
Cte z nej mesicni "Mzdove podklady" (`/app/payroll/summary`) a ERP prehled `dochazka.zakazky_vse_list`.
Pro mzdy je masterem Centrala, takze to neni chyba - ale "att_entry = jediny zdroj pravdy pro hodiny"
plati zatim jen pro mobil a Opravy, ne pro mzdovy souhrn.

