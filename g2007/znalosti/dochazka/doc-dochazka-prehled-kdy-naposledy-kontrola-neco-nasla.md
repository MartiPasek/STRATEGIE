# Prehled "Kontroly - posledni nalez": kdy naposledy ktera kontrola dochazky neco nasla (zavedeno 5. 9. 2026, od 7. 9. 2026 ukazuje i kontroly bez nalezu)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


Ticho u kontroly, ktera driv nachazela pravidelne, je SIGNAL k prohlednuti -
ne dukaz chyby. Proto existuje prehled, kde je videt, kdy naposledy ktera
kontrola dochazky neco nasla.

## Proc to vzniklo

Kontrola "zapomenuty_odchod" byla mesic mrtva, protoze ji pulnocni automat
kazdou noc predbehl (vyplnil konec smeny driv, nez pravidlo stihlo hledat
usek bez konce). Nic to nenahlasilo - kod byl v poradku, jen mu jiny automat
sebral praci pod rukama. Naslo se to az nahodou, rucne, po mesici.

Upozornila na to Petra Safrankova (e-mail 3. 9. 2026). Rozhodl Jirka Honomichl
5. 9. 2026, po konzultaci s Marti-AI. Druha polovina stejneho reseni je
kontrolni seznam pri nasazeni automatu:
doc-system-strategie-kontrolni-seznam-pri-nasazeni-automatu

## Kde to najdes

ERP: Dochazka / Kontrolni prehledy / "Kontroly - posledni nalez".
Uzel je omezeny na stejnych 11 lidi jako sousedni kontrolni prehledy.

## KDO SE NA TO DIVA - NEDORESENO (stav k 5. 9. 2026)

Plati pravidlo doc-system-g2007-nerikat-pridal-jsem-pojistku-bez-spousteni,
tak to rikam rovnou: tenhle prehled NIC NESPOUSTI a NIKOMU nic sam neposila.
Je to pasivni obrazovka - ukaze se jen tomu, kdo ji otevre.

Bylo to vedome rozhodnuti (Marti-AI 5. 9. 2026): alarm by u kontrol, kde je
opravdu cisto, pipal porad, clovek by si zvykl a prestal ho cist.

CO ZATIM NENI ROZHODNUTE: kdo prehled otevira a jak casto. Dokud to nekdo
nema v rutine, plati, ze dlouhe ticho u kontroly zase nikdo neuvidi - jen uz
je aspon kam se podivat. Az to nekdo prevezme, dopis sem kdo a jak casto.

## Z ceho je to postavene

- Vypocet: pohled tenant.att_kontroly_prehled nad tenant.att_anomaly.
  Jeden radek na pravidlo: pocet nalezu celkem, prvni a posledni nalez,
  dni od posledniho, nalezu za 30 a za 90 dni, nevyresenych, a slovni stav.
- Prehled v ERP: fw.data_set + fw.data_source + fw.data_source_op +
  fw.core + fw.comp_def (grid, type_id 306) + fw.menu_node pod uzlem
  Kontrolni prehledy.
- Nic nemeni, jen cte. Na att_anomaly_scan se nesahalo.

## Tri vedoma rozhodnuti - nemenit je bez rozmyslu

1. ZADNY PRAH NATVRDO A ZADNY ALARM. Prehled jen ukazuje "posledni nalez pred
   X dny" a clovek si sam rozhodne, co je u ktereho pravidla normalni.
   Duvod (Marti-AI, 5. 9. 2026): natvrdo nastavena hranice by u pravidel, ktera
   jsou ze sve podstaty vzacna, delala falesne poplachy.

2. SEZNAM PRAVIDEL SE BERE Z CISELNIKU tenant.att_kontrola_ciselnik
   (ZMENENO 7. 9. 2026 - do te doby se bral z historie nalezu).
   NEPLATI uz puvodni veta: "pravidlo, ktere jeste NIKDY nic nenaslo, se
   v prehledu neobjevi vubec" a "ciselnik pravidel neexistuje". Zmenu zadal
   Jirka Honomichl 7. 9. 2026 po dotazu Petry Safrankove ("kontrola, ktera
   existuje, patri do prehledu - i s tim, ze zatim nic nenasla; jinak prehled
   zamlcuje presne ten pripad, kvuli kteremu vznikl"), schvalila Marti-AI.
   Zvolena byla varianta, kterou puvodni text sam oznacoval za spravne reseni -
   ciselnik jako jedine misto definice, ne zaplata do pohledu.
   JAK TO TED FUNGUJE: ciselnik ma 18 radku (kod, lidsky nazev, popis, ktery
   automat pravidlo pise, aktivni, poradi). Prehled z nej vychazi a nalezy
   k nemu jen prilepuje, takze pravidlo bez nalezu ma stav "zatim nic nenasla"
   a prazdna cisla. K 7. 9. 2026 jsou takova tri - dva_bezici_naraz,
   sluzebni_cesta a zamitnuto_ale_den_zustal. Pohled ma navic sloupec nazev,
   ktery je v ERP prvni sloupec; technicky kod zustava vedle nej.
   POJISTKA: pravidlo, ktere by v ciselniku chybelo, se z prehledu NEZTRATI
   (druha vetev pohledu ho pripoji z historie) a navic na nej upozorni hlidaci
   pravidlo kontrola-dochazky-chybi-v-ciselniku (tenant.pojistka, oblast
   dochazka). Zname omezeni te pojistky - pravidlo pridane do jineho automatu
   nez att_anomaly_scan, ktere jeste nic nenaslo a nema uklidovy prikaz, se
   chytne az pri prvnim nalezu.

3. TENANT JE V DOTAZU NATVRDO (tenant_id = 2).
   Vsech 1162 nalezu k 5. 9. 2026 patri tenantu 2 a att_anomaly_scan si tenant 2
   take pise natvrdo. Az bude tenantu vic, tohle misto se musi upravit.

## Stav pri zavedeni (overeno ctenim z databaze 5. 9. 2026)

18 pravidel pise do att_anomaly, z toho 15 uz nekdy neco naslo a je v prehledu.
(Od 7. 9. 2026 jsou v prehledu vsechna, viz rozhodnuti 2 vyse.)
Nejdelsi ticho melo budouci_zaznam - 36 nalezu, vsechny 7. 6. 2026, od te doby
nic (90 dni). NEOZNACENO ZA CHYBU: 36 nalezu v jediny den vypada jako
jednorazovy zpetny sber pri zavedeni pravidla a od te doby muze byt opravdu
cisto. Presne ten pripad, kdy je ticho signal, ne dukaz. Kdyby to nekdo resil,
zacatek je overit, jestli pravidlo vubec ma sanci neco najit.
VYRESENO 7. 9. 2026 - presne timhle zpusobem. Ticho je opravnene, od 8. 6. 2026
neexistuje ani jeden zaznam, ktery by vznikl s datem v budoucnu. Pripad, ktery
vypadal jako zmeskany nalez, zpusobil rucni prevod dne na datum uz probehle.
Detail: doc-dochazka-budouci-zaznam-ticho-neni-chyba-prevod-dne.

Ostatnich 14 pravidel naslo neco za poslednich 30 dni. zapomenuty_odchod po
Petrine oprave zase bezi (7 nalezu za 30 dni, posledni 4. 9. 2026).

