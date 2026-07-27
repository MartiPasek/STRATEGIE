# PRAVIDLO C.1 (nadrazene vsemu): maximalni overovani, nikdy nevymyslet, chybi info -> zeptat se

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ⭐ PRAVIDLO C.1 — ZAKLADNI PRACOVNI STANDARD (nadrazene vsemu ostatnimu)

> oblast: system-g2007 · uroven: nadrazena vsem · Zadal Marti tym / Jirka 24.7.2026.
> Plati pro VSECHNY, kdo pracuji na projektu STRATEGIE: kazda instance Claude, Marti-AI
> i lide. Cti to jako PRVNI a nejdulezitejsi. Zadny ukol nema vyjimku.

## Pravidlo
STRATEGIE je pracovni nasazeni — data rozhoduji o mzdach, fakturaci, pristupech a chodu
firmy. Proto se od kazdeho vyzaduje MAXIMALNI PROFESIONALITA v OVEROVANI, v NAVRHU i v
RESENI. Vzdy. U kazdeho ukolu. Ne jen u "dulezitych" ukolu.

## Zavazne body
1. **NIKDY NEVYMYSLET.** Netvrdit nic, co neni overene v KODU nebo DATECH. Zadne
   "nejspis / asi / melo by" vydavane za fakt.
2. **CHYBI INFO -> ZEPTAT SE.** Kdyz neco k reseni chybi, polozit dotaz. Nikdy nedoplnovat
   ani nedomyslet chybejici vstup. (Zadavatel dodava vse, co ma; zbytek je na dotaz.)
3. **MAXIMALNI OVEROVANI JAKO DEFAULT.** Pred kazdym zaverem i zapisem overit proti realite
   (kod / DB / soubory). Co neni overene end-to-end, bud overit, nebo JASNE oznacit jako
   "zatim neovereno" — nikdy to nevydavat za jistotu.
4. **ROOT CAUSE Z KODU, ne domyslet z chovani.** Precist skutecnou cestu kodu, ne teoretizovat.
5. **NEHADAT nazvy sloupcu/tabulek/poli/endpointu.** Nejdriv information_schema / precist model / grep, PAK dotaz nebo akce.
6. **ZADNA POLOVICATA ANALYZA.** Dotahnout do konce. Radeji o krok vic overit nez jednou tvrdit spatne.
7. **Kdyz me nekdo opravi, ze "to neni pravda", OKAMZITE prestat obhajovat hypotezu a jit do kodu/dat.**
8. **U penez/pristupu/produkce** platí to same jeste tvrdeji + parovat na plnou identitu zaznamu,
   ne na castecny klic (viz g2007 dochazka doc-dochazka-storno-vyroba-kaskada jako varovny priklad).

## Proc
Chyba z nedbalosti/lenosti = realna skoda (mzdy, faktury, pristupy) + ztrata duvery
("nakonec budou platit me, abych kontroloval tebe"). Je to nebezpecne, ne kosmeticke.
Tohle neni doporuceni — je to tvrdy standard #1, ktery ma prednost pred rychlosti i pohodlim.

