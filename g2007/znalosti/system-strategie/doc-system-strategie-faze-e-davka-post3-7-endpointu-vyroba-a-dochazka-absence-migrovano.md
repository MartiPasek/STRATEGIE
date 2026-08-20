# Faze E davka POST3: 7 dalsich POST HTTP endpointu (vyroba cinnosti + dochazka absence) migrovano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovano 7 dalsich POST/zapisovych HTTP endpointu na DB-driven delegaty (Cesta B): app_vyroba_my_cinnosti_toggle, app_vyroba_my_cinnosti_order, app_vyroba_cinnost_master_save, app_vyroba_cinnost_master_order (vsechny 4 pouzivaji _hr_can_manage, ne _vyroba_can_manage jako predchozi davky), att_absence_cancel, att_absence_request (VYSSI RIZIKO - materializuje okamzite do dochazky pres externi modul dochazka_absence_sprava.abs_promitni_zadost), att_absence_decide (VYSSI RIZIKO - vedouci rozhodnuti materializuje/dematerializuje att_entry).

Zavedena vylepsena verifikacni metoda: AST-literal-set diff (porovnani vsech string/ciselnych konstant puvodniho bloku vs. noveho DB skriptu) navic k byte-tail-diffu, plus exec()-compile test a kontrola na zbytkove odkazy na neexistujici promenne (napr. 'body') - reakce na chybu nalezenou v predchozi davce (POST2), kde leftover 'body' reference unikla puvodnimu overovacimu procesu.

Zivy self-test neproveden pro att_absence_request/decide (politika = staticka rigoroznost staci pro dalsi POST stejneho tvaru), ale doporuceno Martimu/Kristy provest brzy spot-check kvuli vyssimu riziku (primy zapis do att_entry).

Deploy commit a7c0bb71a, 38 insertions/291 deletions. CELKEM AKTIVNICH FUNKCI: 110. router.py: 63476 radku (z puvodnich 67789 = 6.36% zmenseni).

