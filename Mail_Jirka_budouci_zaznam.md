# Návrh mailu Jirkovi — budouci_zaznam

**Předmět:** budouci_zaznam vypadá na druhého němého hlídače

---

Ahoj Jirko,

díky za ten přehled, hned se hodil. Kouknu-li na `budouci_zaznam`, vypadá to na tři věci.

**1. To ticho nejspíš není v pořádku.**
Michal Jirkovský má **6 záznamů práce na 22. 8., pořízené 20. 8.** (dva dny dopředu), stav `pending`, z mobilu. Prošla jsem je proti podmínkám pravidla — splňují všechny, nic je nevylučuje. **Nález žádný.** Pravidlo mělo 20. a 21. 8. v noci hlásit šestkrát a nehlásilo ani jednou.

Netvrdím, že je mrtvé celých 90 dní — od 7. 6. mělo reálnou příležitost jen dvakrát. Ale tuhle jednu prokazatelně minulo. Stejný vzorec jako u zapomenutého odchodu, stálo by za to mrknout do kódu.

**2. Těch 36 nálezů z června se už nedá prošetřit.**
Odkazují na záznamy s čísly 2–15 708, jenže nejnižší číslo v `att_entry` je dnes 16 349 — tabulka se mezitím přeimportovala. Nálezy zůstaly, záznamy pod nimi zmizely. To je samo o sobě vada: nález, který ukazuje do prázdna, nikdo neprošetří.

**3. K číselníku: ano.**
Kontrola, která existuje, patří do přehledu — i s tím, že zatím nic nenašla. Jinak přehled zamlčuje přesně ten případ, kvůli kterému vznikl: kontrolu, která nefunguje od začátku.

Nehoří to.

Peťa
