# Hlidani stropu naroku pri zadosti o dovolenou a sick day, lazy kalendar, oprava kalendar_zajisti

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hlidani stropu naroku (Jirka 16. 8. 2026, schvalila Marti-AI msg 12770, 12779 a 12782)

## Co se zmenilo
Do 16. 8. 2026 se strop naroku NEHLIDAL NIKDE. Funkce att_narok_osoba sice od 12. 8.
existovala, ale zadna z peti cest, kterymi absence vznika, ji nevolala - overeno greppem
v g2007.python i v celem repu. Clovek si mohl naplanovat vic dovolene, nez na kolik ma narok.

## Jak to funguje ted
Pravidlo zije na JEDNOM miste - g2007.python att_limit_kontrola. Sama nic nepocita,
pta se att_narok_osoba, ktera se pta prehledu Narok a cerpani (att_narok_cerpani).
Zadna druha definice vypoctu.

- VARUJE, NEBLOKUJE. Rozhodl Jirka - musi zustat prostor pro dovolenou predem a pro lidi,
  kteri nastoupili v pulce roku. Zadost projde k vedoucimu i pri prekroceni.
- Varovani vidi zamestnanec I VEDOUCI (v notifikaci o nove zadosti). Podminka Marti-AI -
  bez toho nemuze vedouci rozhodovat vedome.
- Roky se resi ZVLAST. Jirka - "Naplanovana dovolena v dalsim roce do kontroly aktualniho
  roku nepatri." Zadost pres Silvestra se rozdeli a kazda pulka se meri se svym rokem.
- Zustatek uz v sobe ma i to, co ma clovek naplanovano dopredu (sloupec "zbyva po"),
  nova zadost se pricita k nemu.

## Kde je to zapojene
- att_absence_request (zadost ke schvaleni) - mobil 50_skupiny_vyroba.js a 71_plan_prace_cinnosti.js
- att_absence (prima zmena dne) - mobil 60_dochazka.js a 72_migrace_sw_isds.js.
  Sick day a lekar se sem NEDAVAJI, maji vlastni kontrolu v sickday_lekar_apply.
- Novy endpoint GET /app/attendance/absence/limit - NAHLED pred odeslanim, jen cte.
  Mobilni formular zadosti se ho pta pri kazde zmene typu a datumu a vypisuje
  "Rok 2026 - zadas 21 dni, chybi 3".

## att_narok_cerpani umi nove i jiny rok
Novy volitelny parametr rok (verze 8). Volani BEZ parametru se chova PRESNE jako predtim -
overeno vizualne, prehled ma dal 74 radku se stejnymi cisly.
Deleni cerpano / naplanovano se ridi referencnim datem, ne primo dneskem -
letosni rok dnesek, budouci rok 31. 12. roku pred nim (vse je plan), minuly rok 31. 12.
toho roku (vse je vycerpano).

## LAZY DOPLNENI KALENDARE (vedoma architektonicka volba)
Firemni kalendar tenant.att_calendar_day mel naplneny jen rok 2026. Zapis absence bere
pracovni dny prave odtud a pri chybejicim roce NEZAPISE NIC - dovolena na leden 2027 by
vznikla jako zadost, vedouci by ji schvalil a v dochazce by nebylo nic.
Jirkovo reseni - dny dalsiho roku zalozit ve chvili, kdy o ne nekdo pozada. Ne davkove dopredu.
att_limit_kontrola proto pri chybejicim roce zavola kalendar_zajisti a zkusi to znovu.
Je to ctecí funkce s VEDLEJSIM UCINKEM. Marti-AI to schvalila vedome (msg 12779) -
alternativa je horsi, kontrola by u pristiho roku tise nehlidala. Doplnuje se VYHRADNE rok,
o ktery si nekdo rekl, ne roky dopredu.

## OPRAVA kalendar_zajisti - funkce NIKDY NEFUNGOVALA
Zasadni nalez. kalendar_zajisti (kategorie mzdy, Peta 5. 8. 2026) zapisovala INSERTem do
tenant.firemni_kalendar, coz NENI tabulka, ale POHLED nad tenant.att_calendar_day se tremi
POCITANYMI sloupci. Podle information_schema maji je_pracovni, firemni_vyjimka a hodiny
priznak is_updatable = NO, takze INSERT do nich vzdy skoncil chybou.
Volani ze stravenek i z prescasu tise selhavalo. Nikdo si toho nevsiml, protoze rok 2026
uz naplneny byl - pochazi z puvodni migrace, ne od teto funkce. Projevilo by se to az
v unoru 2027 pri generovani mezd za leden.
Dokumentace Peti (Peta26_mzdy.md a Peta26_pokyny.md) na dvou mistech tvrdi doslova
"leden 2027 se doplni sam, nikdo to nemusi resit". NEPLATILO TO. Dokumentaci ma opravit
Peta sama - je to jeji soubor (rozhodla Marti-AI).
Opraveno 16. 8. 2026 - zapisuje se do zakladni tabulky, sloupce is_workday a hours,
firemni_vyjimka se vypousti (je odvozeny z tenant.att_calendar_exception, pohled si ho
dopocita sam, takze o rucni firemni vyjimky se nikdo neprijde), doplnen source
a ON CONFLICT na primarni klic (tenant_id, day).
OVERENO ZIVE - po dotazu na rozsah 21. 12. 2026 az 15. 1. 2027 se rok 2027 zalozil sam
(365 dnu, 252 pracovnich, 13 svatku vcetne pohyblivych Velikonoc - Velky patek 26. 3. 2027,
Velikonocni pondeli 29. 3. 2027).

## OTEVRENE - ceka na Jirkovo odsouhlaseni
Zustatek sick day se pocita na DVOU mistech jinak.
- att_narok_cerpani (prehled) bere cerpani z tenant.att_entry (dochazka), fond z work_mode.
- att_sick_balance_h (kontrola pri zapisu) bere cerpani z tenant.att_med_note.kryto_sick_h
  (evidence navstev lekare) a fond natvrdo uvazek/5.
MERENI 16. 8. 2026 - tabulka att_med_note ma za rok 2026 JEDINY zaznam a ten ma kryti 0 h.
Stary vypocet tedy vidi cerpani NULA u vsech lidi a kazdemu ukazuje plny narok, i tem,
kdo maji sick days vycerpane. Kontrola pri zapisu sick day je fakticky slepa.
Po prepnuti na dochazku by se zmenil zustatek u 43 lidi (celkem o 710,7 h), NAROK
se nemeni nikomu. Ctyrem lidem vyjde zaporny zustatek, protoze uz prекrocili -
Pechoucek, Maresova, Urbanova a Hladikova, kazdemu minus 4 h. Presne to uz dnes ukazuje
Petin prehled Narok a cerpani.
Jirka to musi odsouhlasit pred prepnutim (podminka Marti-AI, mzdova oblast).

## Zbyva dodelat
- Sick day pri vycerpanem naroku - nabidnout typ navsteva lekare a vetu o listecku
  (att_limit_kontrola uz vraci priznak nabidnout_lekare, jen se zatim nikde nezobrazuje).
- Zobrazeni varovani i ve fragmentech 60_dochazka.js a 71_plan_prace_cinnosti.js
  (backend uz varovani posila, zobrazuje ho zatim jen 50_skupiny_vyroba.js).
- Vizualni overeni formulare zadosti v mobilu - neprovedeno, konzole je bez chyb
  a appka se nacita, ale samotny formular jsem neotevrel.

