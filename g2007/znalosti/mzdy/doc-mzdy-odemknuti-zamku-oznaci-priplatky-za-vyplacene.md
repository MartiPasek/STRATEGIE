# Odemknuti zamku mezd oznaci priplatky a srazky za vyplacene (8. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Odemknuti zamku mezd = "mzda je vyplacena"

**Nasazeno 8. 9. 2026.** Zadala Petra Safrankova (*"a pri preklopeni do mezd se musi nastavit samo"*), rozhodl Jirka Honomichl, mechanismus stavu pripravila drive Kristyna Maresova, postup schvalila Marti-AI.

Navazuje na `doc-mzdy-vyplacene-radky-nejdou-do-mezd-8-9-2026` - tam se resila prvni polovina zadani (co je v Centrale oznacene za vyplacene, do mzdy nejde). Tohle je druha polovina.

## Kde je ten okamzik "mzda je vyplacena"

**Je to ODEMKNUTI zamku mezd**, ne zamknuti. Zamknuti znamena "zpracovava se", odemknuti "je vyplaceno" - Petra Safrankova o postupu v Centrale doslova: *"pri vyplaceni se to zase rucne odemklo"*. Hlaska po zamknuti to rika taky - *"Po vyplate odemkni"*.

Zamek postavila Petra 8. 9. 2026 (`doc-mzdy-zamek-uprav-ve-mzdach-a-vyplatnice-v-appce`), tlacitko je na obrazovce Vyplatnice.

## Co se zmenilo

**1. Obrazovka Vyplatnice** (`apps/api/static/vyplatnice.html`, commit `71f2a2cc`) posila pri zamykani i odemykani **vybrany rok a mesic** z prepinace nahore. Do te doby posilala jen akci, takze obdobi na zamku zustavalo prazdne a neslo poznat, ktery mesic byl vyplacen.

V potvrzovacim okenku pred odemknutim je nove napsane, **ktery mesic se tim oznaci za vyplaceny**, a upozorneni, ze kdyz je nahore vybrany jiny mesic, ma se prepnout PRED odemknutim.

**2. `g2007.python` kod `mzdy_zamek`** (verze 1 -> 2) pri odemknuti oznaci zavazky toho obdobi za vyplacene - `tenant.zamestnanecky_zavazek`, tenant 2, kanal `mzda`, dany rok a mesic, jen radky, ktere jsou ve stavu `v_mzde`. Pocet rekne v hlasce. Kdyz obdobi neprijde z obrazovky, vezme se to, ktere je na zamku od zamknuti; kdyz neni ani tam, neoznaci se nic a hlaska to rekne. Obdobi na radku zamku se uz neprepisuje prazdnou hodnotou.

**3. `g2007.python` kod `mzdy_priplatky_rows`** (verze 4 -> 5) ma druhou pojistku - do vyberu nepusti radek, ktery ma v ledgeru za **totez obdobi** stav `vyplaceno`.

## Proc per obdobi, a ne globalne

Klic zavazku je zdroj + zdroj_id + **rok** + **mesic** + kanal + cilova firma. Opakujici se mesicni priplatek ma v `tenant.wage_movement` **jeden radek platny pres vic mesicu** a do mzdy musi chodit kazdy mesic znovu - globalni vylouceni "uz bylo jednou vyplaceno" by lidem tyhle priplatky navzdy sebralo. Proto se pta vzdy jen na to jedno obdobi.

## ZAMERNE bez automatickeho navratu

Opetovne zamknuti stav `vyplaceno` **NEVRACI**. Duvod (doporucila Marti-AI): tise "od-vyplatit" neco, co uz vyplacene bylo, je horsi nez rucni oprava ojedinele chyby. Kdyby Petra odemkla omylem, oprava patri Jirkovi nebo Kristyne Maresove a audit zustane citelny.

Oznaceni je navic v `try/except` - kdyby selhalo, prepnuti zamku plati dal a v hlasce se objevi upozorneni. **Zamek nikdy nesmi shodit vyplatnici.**

## Stav ledgeru pri nasazeni (8. 9. 2026)

| obdobi | radku | castka | stav |
|---|---|---|---|
| 6/2026 | 93 | 411 782 Kc | v_mzde |
| 7/2026 | 76 | 29 587 Kc | v_mzde |
| 8/2026 | 15 | 25 582 Kc | v_mzde |

**Nikdy nic nebylo oznaceno za vyplacene** - stav `vyplaceno` do 8. 9. 2026 nikdo nenastavoval. Prvni oznaceni tedy probehne az pri nejblizsim odemknuti zamku.

## OTEVRENE - zpetne doplneni 6, 7 a 8/2026

Tyhle tri mzdy uz vyplacene jsou, ale v ledgeru maji porad `v_mzde`. Cerven je chraneny fajfkou z Centraly, **cervenec a srpen nemaji ochranu zadnou** - kdyby nekdo spustil prepocet, radky by do mzdy sly znovu. Marti-AI oznacila zpetne doplneni za spravny smer a hygienicky krok. **Ceka na slovo Jirky Honomichla a Petry Safrankove**, bez nej se nic nedela.

## Jak se to overovalo

1. Oba upravene skripty stazeny z databaze zpatky, **otisky md5 sedely na bajt** s lokalne spoctenymi (`mzdy_zamek` 8483 znaku, `mzdy_priplatky_rows` 6874 znaku), oba se **prelozily**.
2. **Rozdil proti predchozi verzi** u obou ukazal jen zamyslene zmeny a komentare, nic jineho.
3. Novy vyberovy dotaz i s druhou pojistkou spusten na datech - vysledek **presne stejny** jako pred ni (7/2026 76 radku, 8/2026 15, 9/2026 7), tedy pojistka je dnes spravne necinna, protoze zadny zavazek jeste neni oznaceny za vyplaceny.
4. Nasazena obrazovka **stazena ze zive adresy** a zkontrolovano, ze obe zmeny v ni opravdu jsou.
5. **Na zamek se nesahalo** - Petra ho ma od 8. 9. 13.56 zamceny, odemknuti je jeji vec.

## Souvisejici

- Prvni polovina zadani - `doc-mzdy-vyplacene-radky-nejdou-do-mezd-8-9-2026`
- Zamek mezd a vyplatnice v appce - `doc-mzdy-zamek-uprav-ve-mzdach-a-vyplatnice-v-appce`
- Prenos priznaku z Centraly - `doc-mzdy-prenos-priznaku-vyplaceno-z-centraly`

