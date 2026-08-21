# Dovolena radna (20) vs dovolena navic (30) - rozpad, deleni zlomoveho dne, stravenky a chyby Centraly

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Dovolena radna vs dovolena navic - jak to ma byt a proc

Zadala Peta (mzdova ucetni), postaveno 19.-20. 8. 2026. Podklad z Centraly dodala
Tynka Storkova (autorka puvodni logiky), zmenu schematu odsouhlasila Marti-AI.

## PRAVIDLO

Clovek na HPP ma **20 dnu radne dovolene** (cinnost 20) a k tomu par dnu **dovolene
navic** (cinnost 30). **OSVC ma cely narok v "navic"**, radnou nema vubec.
Narok je v Podminkach - tenant.staff_cond, kody dovolena_zakladni_dni a
dovolena_navic_dni; dovolena_dni je jen POCITADLO (soucet drzi trigger).

**Rozdil je v penezich - za radnou dovolenou stravenka NENALEZI, za dovolenou navic ANO.**
Proto neni kosmeticky, jestli je u dne 20 nebo 30.

## KDE TO ZIJE

Jediny zdroj pravdy je **tenant.att_entry.ec_druh** (20 nebo 30). Nikde jinde.

**Ve Sprave dochazky se to nerozlisuje** - tam je vzdy "dovolena", protoze u budouciho
dne se jeste nevi, jak dopadne poradi cerpani. Rozhodne se to az pri preklopeni do
Dochazky new (tu deli jen podminka "den uz nastal").

POZOR - cislo, ktere je videt v Dochazce new, se u absenci **DOPOCITAVA z typu zaznamu**,
neni to ulozena hodnota. Prazdne ec_druh se proto tvari jako 20. Vypocet stravenek ale
cte ULOZENOU hodnotu. Dokud tam neni 30, clovek o stravenku prijde a na obrazovce to
nepozna.

## DELENI ZLOMOVEHO DNE

Kdyz narok dojde uprostred dne, den se **rozdeli na dva zaznamy** (napr. 4 h cinnost 20
+ 4 h cinnost 30) pod TOUTEZ zadosti. Presne tak to dela Centrala - vklada "D 1/2" a
"DN 1/2" se stejnym IDEventImp. Za takovy den stravenka NENALEZI, protoze je tam radna
dovolena (rozhodla Peta 19. 8. 2026).

Do 20. 8. 2026 to blokoval unikatni index **ux_att_entry_source_den**. Byl zuzen o
podminku source_system <> 'absence_req', takze ochrana proti dvojimu importu z Centraly
zustala a deleni dne se povolilo. Overeno, ze nikde v kodu neni predpoklad "jedna zadost
= jeden radek na den".

## CO TO POCITA

**g2007.python kod=att_dovolena_kaskada** (Peta 20. 8. 2026). Projde rok chronologicky
od ledna, scita vycerpane dny a prirazuje 20 dokud staci narok, pak 30. Parametry
(rok, dry) - dry=True nic nezapisuje, jen vrati navrh.

Bezi na trech mistech:
- **v noci 2-5 h** (router.py, _dovolena_kaskada_nocni). Peta - "prijde mi to spatne
  delat to v dobe, kdy do toho muze rucne zasahovat nekdo z nas".
- **po rozhodnuti o zadosti** (g2007.python att_absence_decide).
- **po zapisu ve Sprave dochazky** (dochazka_absence_sprava.py, _prepocti_dovolenou -
  ctyri mista, vedle _prepocti_fond).

Nesaha na uzamcena obdobi (tenant.att_period_lock) ani na dny, ktere jeste nenastaly.
Je idempotentni.

## CTYRI CHYBY CENTRALY, KTERE TU NESMI VZNIKNOUT

Rozbor procedury **dbo.EC_Events_PropsatDoDoch** (19. 8. 2026). Vysvetluji, proc lidem
v Centrale vychazela dovolena navic, i kdyz jeste meli radnou (Hladikova, Maresova, Zeman):

1. **Zustatek se odecita DVAKRAT za tyz den** - dva bloky pro cinnost 20 bezi za sebou
   a oba odectou. Clovek tak vycerpa narok v polovine.
2. **Kurzor jede ORDER BY DatumOd DESC**, tedy od nejnovejsiho dne. Poradi cerpani
   neodpovida kalendari - novejsi zadost snedla zustatek drive nez starsi.
3. **Pomocna promenna pro deleni dne se nenuluje** a drzi hodnotu i pro dalsiho cloveka.
   Kristyna si toho byla vedoma uz v dubnu 2022 - v kodu je jeji poznamka.
4. **Nikdy se to neprepocitava.** Procedura preskakuje dny, ktere uz propsala. Kdyz se
   pozdeji zrusi drivejsi dovolena, poradi se posune a stare znacky zustanou spatne.

Nas skript ma proti tomu - jeden dotaz misto kurzoru s pomocnymi promennymi,
chronologicke poradi, a PREPOCET celeho roku misto jednorazoveho razitka.

## STRAVENKY A KOREKCE

Vypocet **mzdy_stravenky_rows** rozhoduje podle ec_druh - 30 NENI v seznamu vyloucenych
cinnosti, takze za dovolenou navic stravenka nalezi. Od 19. 8. 2026 navic cte **korekce
z ec.pripl_srazky** (druh 8 "Stravenky navic / popr. srazka"), stejne jako to dela
Centrala v EC_Mzdy_PrepocetMesicZam - castka je POCET kusu, zaporna = srazka, ridi se
platnosti a schvalenim, priznak vyplaceni se nectete. Vysledek nikdy nejde pod nulu.

Zrcadlo ec.pripl_srazky se JEN CTE - zpetny zapis do Centraly se nedela (verdikt
Marti-AI 22. 7. 2026) a hodinovy sync by ho stejne prepsal. Znacit se ma v Centrale.

## POJISTKY

dovolena-navic-videt-v-prehledech, dovolena-osvc-vzdy-navic,
stravenky-ctou-korekce-priplatku, dovolena-prepocet-napojeny, index-dovoluje-deleni-dne.

## OTEVRENE

- **Prehled Narok a cerpani si rozpad D/DN pocita VLASTNIM pravidlem**, ne z ec_druh.
  Dve mista pocitaji totez. Az bude ec_druh plnene spolehlive, ma cist odtud.
- **Ciselnik cinnosti se vede na peti mistech** (vyroba_cinnost, att_entry_type,
  absence_type, att_planned_absence_type, c_slozka) plus ctyri seznamy natvrdo v kodu.
  Peta chce sjednotit do vyroba_cinnost.
- **Denni ukony a kontroly maji byt oddelene**, kazdy se svym casem a hlidanim
  (Peta 20. 8. 2026) - dnes visi v jedne smycce _hr_daily_pass v router.py.

