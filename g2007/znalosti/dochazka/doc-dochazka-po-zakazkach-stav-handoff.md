# Docházka po zakázkách — stav a handoff 22.7.2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Handoff pro pokračování v nové konverzaci (Claude-26 + Peťa, 22.7.2026). Vše NASAZENO a funkční. Detaily: doc-dochazka-po-zakazkach-prehled, doc-system-strategie-prehledy-tabulky-standard, doc-system-strategie-prehledy-sirky-sloupcu.

## Hotové
- Strom: slozka Dochazka (uzel 188) -> Opravy dochazky (183) + Dochazka po zakazkach (189, jadro dochazka.centrala) + Naplanovana budoucnost (190). Viditelnost 11 lidi.
- Prehled = VLASTNI stranka /dochazka-po-zakazkach (iframe hook na ZACATKU dispatchPageRender v page_render.js; jadro ma data_source, jinak by se vykreslil framework grid). Endpoint modules/erp/api/dochazka_zak_tab.py bere SQL z data_setu dochazka.zakazky_vse_list / _budoucnost_list (prevadi Decimal/date na JSON).
- Data: tenant.vyroba_work (prace na zakazce + skutecna cinnost, Centrala+app) UNION absence z att_entry (category=absence, bez prestavek), absence maji zakazku Rezie + centralske cislo. Sloupce jako Delphi prehled 109, bez CasBlbost/CasRezie, DruhCinnosti = ec_cislo, CasKonec s datem. CasCelkem overeno v setinne soustave.
- Cinnosti zarovnany na Centralu (1046/1047): vyroba_cinnost ma strategie_cislo (zaloha) + ec_cislo (centralske). Data premapovana (cinnost_id_orig zaloha), import opraven (mapuje pres ec_cislo). Pridana Odmeny fin.zakazek (id 50, ec 27). Rezie sjednocena bez hacku.
- Vzhled = standard (ramecek, sticky hlavicka bez velkych pismen, filtr pod nazvy + krizek, uzky sloupec znacek tecka/sipka, filtr cisel carka i tecka, roztahovani pres colgroup + vodici cara, filtr 1px pod hlavicku). Totez nasazeno i pokladny/faktury (1px fix + zruseni velkych pismen).
- Sirky sloupcu: osobni tazeni se uklada do DB (tenant.att_ui_pref kod dochazka_col_widths_u<uid>), sdilene vychozi = kod dochazka_col_widths. Peta nastavi v CHROMU, rekne nastaveno, Claude povysi osobni na sdilene pres most (bez tlacitka, bez deploye). Petiny vychozi jiz nastavene. POZOR: Petě pripomenout, ze nastaveni sirek dela v Chromu.

## Otevrene
- Absence: mapa centralskych cisel je zatim v data_setu (CASE dle att_entry_type.code), ne v vyroba_cinnost - pro nove typy doplnit.
- Cinnosti bez ec_cislo: ostatni-kancelare (id 45, mrtva), Rezie (14) a Bez rozliseni (43) zamerne (nejsou cinnost).

