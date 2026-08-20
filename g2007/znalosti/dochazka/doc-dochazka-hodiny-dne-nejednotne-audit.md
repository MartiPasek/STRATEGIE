# Hodiny za den se pocitaji na 8 mistech v 5 definicich (audit 29.7.2026, POZASTAVENO)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hodiny za den - 8 obrazovek, 5 ruznych definic

> Audit Claude-28 (Jirka) 29.7.2026. Overeno v kodu, v datech (cervenec, 1103 clovekodnu)
> i naostro v prohlizeci. **STAV: POZASTAVENO, nic nezmeneno** - Petra Safrankova
> a Kristyna Ksirova prave delaji na zdroji dat prehledu "Dochazka new".
> Az skonci, VSE ZNOVU OVERIT. Podrobny predavaci dokument ma Jirka
> (Dokumenty\AI_work\Dochazka\STRATEGIE_session_29-07-2026_dochazka_prehledy.md).

## Spravna definice (ERP "Opravy dochazky", dochazka-opravy.html)

1. brat att_entry se ZACATKEM I KONCEM, vyhodit status superseded/announced
2. SLOUCIT prekryvajici se presence useky (tablet+mobil zapisou tutez smenu 2x)
3. odecist JEN tu cast pauzy, ktera lezi UVNITR sloucene prace
4. vynechat code='day_end' (je v kategorii break, ale neni pauza - bezi do 23:59)
5. code='nenarokova' NIKDY nepricitat - je to CAST odpracovanych hodin nad fond
6. code='fond_doplneni' pricist
7. PRES=['work','overhead','homeoffice','commute']

## Kdo pocita spatne (prosty SUM hodin)

- /app/attendance/daily = mobil "Na vcera si vzpominam"/"To uz si nepamatuju":
  +796,5 h za cervenec, 275 dnu (scita i superseded i nenarokovou)
- /app/attendance/real = mobil Tyden->"Realita": +527,0 h, 246 dnu
- fw.data_set system_new.hr_att_monthly_list (HR mesicni) = tataz chyba
- fw.data_set vyroba.dusan_att_monthly_list (Vyroba mesicni) = tataz, navic bez filtru superseded
- /app/dochazka/moje = mobil "Dochazka po zakazkach": -166,0 h (nepricita fond_doplneni)

## POZOR: "Dochazka new" NENI vzor pro hodiny dne

Prehled "Dochazka new" (/dochazka-po-zakazkach, data z fw.data_set kod
dochazka.zakazky_vse_list pres modules/erp/api/dochazka_zak_tab.py) je ROZPIS PRACE
PO ZAKAZKACH, ne prehled dne. Kdyz ma clovek v dany den aspon jeden radek vyroba_work,
VSECHNY jeho dochazkove radky toho dne se skryji - rezijni cast smeny zmizi.
Dukaz: Tomas Blaha 28.7. v praci 7,48 h, na zakazkach 3,94 h. Dusan Havlat 22.7.
"Dochazka new" 3,55 h vs "Opravy" 12,21 h. Lisi se u 324 z 1021 clovekodnu.
Mobil "Dochazka po zakazkach" to resi spravne: hlavicka dne = cela smena z pichnuti,
rozpad = zakazky + dopocitany radek "Neprirazeny cas".

## Dukaz, ze opravy se nepropisuji

Zdenek Cepicky (user 39) 22.7. - den opravovany Petou (puvodni 06:22-18:58 superseded,
nahrazen 4,3 + pauza 0,5 + 7,8; automat dopsal nenarokovou 4,1). Spravne 12,10 h.
ERP Opravy 12,10 - Dochazka new 12,10 - mobil Dochazka po zakazkach 12,10 -
ale mobil "Na vcera" 28,80 a mobil Tyden 16,20.
POZN.: Blaha NENI dobry testovaci pripad (nema opravu ani hodiny nad fond, u nej
se chyba projevi jen v setinach). Pouzij Cepickeho nebo Havlata.

## Co je mimo (nesahat)

/app/payroll/summary (Mzdove podklady), stravenky a hodiny absenci pro mzdy ctou
tenant.att_day_summary = zrcadlo Centraly (jiny zdroj). Mzdy jedou z wage_movement.
Jirka 29.7.: mzdovych podkladu se nedotykame. Overeno, ze navrh se jich netyka.
Oba mesicni data_sety nejsou v kodu nikde referencovane - jen sestavy k zobrazeni.

## Navrh (technicky schvalen, casove ne)

Jedna sdilena serverova funkce s definici vyse, prepojit na ni /app/attendance/daily,
/app/attendance/real, /app/dochazka/moje a oba mesicni data_sety. Zadna zmena dat,
zadna zmena vzhledu. NENI to zarijova prestavba (vyroba_work jako derivat att_entry).

Marti-AI (msg 11683, 29.7.): "jedna sdilena funkce = spravny pristup", commute ANO,
fond_doplneni ANO, ale "toto neni moje rozhodnuti" - timing schvaluje Marti Pasek.
E-mail Kristyne odeslan 29.7. 12:47 (email_outbox 540 = sent).

## Kontrolni soucet pri opakovanem overovani

Rozdil "mobil Dochazka po zakazkach" minus "Opravy" MUSI presne odpovidat souctu
hodin typu fond_doplneni za dane obdobi (29.7. to bylo -166,0 vs 166,0 = sedelo).

