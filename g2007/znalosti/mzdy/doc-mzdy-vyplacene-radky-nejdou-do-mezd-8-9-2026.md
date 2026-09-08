# Vyplacene priplatky a srazky uz do mzdy nejdou (rozhodnuti Petry Safrankove 8. 9. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Vyplacene radky uz do mzdy nejdou

**Zadala Petra Safrankova 8. 9. 2026** (pisemna odpoved v mailu "Priplatky a srazky"), **rozhodl Jirka Honomichl**, schvalila Marti-AI. Provedl Claude-28 tyz den.

Doslovne zadani Petry - *"Prosim nastavit plosne, co je vyplaceno, nemuze jit do mezd, ikdyz vyplaceno nastaveno rucne, a pri preklopeni do mezd se musi nastavit samo."*

## Co se zmenilo

`g2007.python` kod **`mzdy_priplatky_rows`** (verze 3 -> 4) ma ve vyberovem dotazu novou podminku **`AND coalesce(wm.ec_vyplaceno,false) = false`**. Radek, ktery je v Centrale oznaceny za vyplaceny, uz se do mzdoveho podkladu nedostane. Jina zmena v kodu zadna neni (rozdil proti verzi 3 overen radek po radku, krome te podminky jen novy komentar v hlavicce).

Tim **prestava platit** starsi veta z `doc-mzdy-prenos-priznaku-vyplaceno-z-centraly` a z hlavicky `sync_priplatky_from_ec`, ze "chovani mezd se nemeni a mzdy_priplatky_rows priznak zamerne necte". Obe mista jsou 8. 9. 2026 opravena.

## Proc

Petra nasla 3. 9. 2026 radek, ktery uz byl proplaceny fakturou a presto mel jit jeste do mzdy - **Michelle Safrankova, os. c. 381, jednorazova odmena 50 537 Kc, faktura 26007, obdobi 9/2026**. Bez teto zmeny by dostala tytez penize dvakrat. Zarijova mzda v te chvili jeste vygenerovana nebyla.

## Zmereny dopad (stav k 8. 9. 2026)

| obdobi | pred zmenou | po zmene | rozdil |
|---|---|---|---|
| 6/2026 | 67 radku / 42 lidi / 237 343 Kc | 0 radku | cely mesic |
| 7/2026 | 76 radku / 24 935 Kc | beze zmeny | zadny |
| 8/2026 | 15 radku / 25 582 Kc | beze zmeny | zadny |
| 9/2026 | 8 radku / 73 043 Kc | 7 radku / 22 506 Kc | Michelle Safrankova 50 537 Kc |

## POZOR - vedome prijate riziko u cervna

V cervnu 2026 maji po vyplate fajfku "vyplaceno" **vsechny** radky, takze pripadny **prepocet 6/2026 vyda o 237 343 Kc u 42 lidi min** nez puvodni cervnova mzda. Jirka na to Petru vyslovne upozornil vcetne tech cisel a ona presto zadala plosne nastaveni; Jirka pak rozhodl udelat to podle ni bez omezeni na obdobi. Cervnova mzda je vyplacena a prepocet se nechysta. **Neni to chyba, je to zamer** - kdyby nekdo cerven prepocital a divil se, tohle je duvod.

Priznak `ec_vyplaceno` porad **nerika kanal** vyplaty (mzda vs. faktura) - sloupec `Preneseno` je u vsech letosnich radku nulovy i v samotne Centrale. Rozliseni z dat tedy nejde a tahle zmena ho neresi.

## Take smazano

Tri osirele radky v `tenant.wage_movement` se zdrojem `EC_PRIPL`, ktere v Centrale uz neexistuji (nesel u nich ziskat priznak vyplaceni) - Petra k nim napsala "Ty prosim smazat". Sly ven po overeni, ze nejsou v `tenant.wage_export_batch`, nejsou cilem storna a maji prazdne `exported_at`.

- id 1057 - Jakub Hrdinka, os. c. 429, 4/2026, -267 Kc (jediny z tri, ktery byl ve vyberu do mezd, a to za DUBEN, tedy uzavreny mesic)
- id 611329 - Radek Hellmayer, os. c. 11, 6/2026, -3 600 Kc
- id 884295 - Vasyl Namjak, os. c. 464, 6/2026, 1 Kc

Po smazani ma `EC_PRIPL` 1003 radku a **zadny bez priznaku vyplaceni**.

## Druha veta Petry - DODELANA TYZ DEN

> **Zmena 8. 9. 2026 vecer.** Do te doby tu stalo, ze druha veta Petry
> *"a pri preklopeni do mezd se musi nastavit samo"* **udelana NENI**, protoze Petra neurcila,
> kde a kdy se ma priznak nastavovat. **Uz to neplati - dodelano tyz den**, kdyz Jirka Honomichl
> rekl "doreste to cele". Postup doporucila Marti-AI, mechanismus stavu pripravila drive
> Kristyna Maresova. **Detail - `doc-mzdy-odemknuti-zamku-oznaci-priplatky-za-vyplacene`.**

Reseni ve zkratce - priznak se **nevede v Centrale ani v `ec_vyplaceno`** (ten by hodinovy prenos
do hodiny prepsal), ale v **nasem ledgeru `tenant.zamestnanecky_zavazek`**, kde uz byl stav
`otevreno -> v_mzde -> vyplaceno` pripraveny. Nastavuje se **pri odemknuti zamku mezd**, tedy
ve chvili, kdy je mzda opravdu vyplacena. `mzdy_priplatky_rows` (verze 5) ma proti tomu stavu
druhou pojistku.

Puvodni dve prekazky tim padly takto:

- **Kde** - hodinovy prenos `sync_priplatky_from_ec` (verze 9) priznak `ec_vyplaceno` pri kazdem behu prepisuje hodnotou z Centraly, takze vlastni nastaveni na nasi strane by do hodiny zmizelo. Proto se nas priznak vede jinde - v ledgeru zavazku, kterym prenos nehybe.
- **Kdy** - az po vyplate (odemknuti zamku), ne pri vyberu do podkladu. Kdyby uz pri vyberu, prepocet tehoz mesice by si sam vsechno vyhodil.

## Jak se to overovalo

1. Zdroj po zapisu stazen z databaze, otisk md5 sedel na bajt s lokalne spoctenym, kod se prelozil (`compile`), podminka je v nem prave jednou.
2. Rozdil proti predchozi verzi 3 (z `g2007.python_historie`) ukazal **jen** ten jeden radek dotazu a novy komentar - nic jineho.
3. Vyber do mezd premeren znovu po zmene - viz tabulka vyse.
4. Smazani overeno ctenim - z tri id nezustalo zadne, `EC_PRIPL` ma 1003 radku, 0 bez priznaku.

## Souvisejici

- Prenos samotneho priznaku z Centraly - `doc-mzdy-prenos-priznaku-vyplaceno-z-centraly`
- Modul a smer dat - `doc-mzdy-priplatky-srazky`, `doc-mzdy-priplatky-srazky-cutover-praha`
- Proc musi byt zrcadlo plny re-import - `doc-mzdy-zrcadlo-pripl-srazky-plny-reimport`

