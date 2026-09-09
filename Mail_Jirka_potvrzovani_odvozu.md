# Mail pro Jirku — potvrzování odvozů z tabletu

**Předmět:** Jak funguje potvrzování odvozů z tabletu (přehled Doprava zákazníkovi, def. 27)

---

Ahoj Jirko,

posílám na vědomí, jak přesně funguje potvrzování odvozů z dotykových terminálů — dohledávala jsem to kvůli přehledu „Doprava zákazníkovi" a přijde mi, že to stojí za sdílení.

**Kde to sedí**

Přehled „Doprava zákazníkovi" (a „Doprava zákazníkovi – přehled všech") má v menu Centrály číslo definice 27, za ním je tabulka `EC_DopravaZakaznikovi`. Sloupec se statusem odvezeno vychází z `DatumOdvezeni`; kdo odvoz potvrdil, drží `OdvozPotvrdil` (osobní číslo).

**Co se stane po stisku tlačítka na tabletu**

Volá se procedura `EC_DopravaZakaznikovi_PotvrzeniOdvozu` (Michal Špinka 2019, notifikace doplnil Ondra 2022, archivaci ty v září 2024). Udělá tři věci:

1. **Zapíše potvrzení** — do řádku dopravy nastaví `DatumOdvezeni` na aktuální čas a `OdvozPotvrdil` na osobní číslo člověka přihlášeného na tabletu.
2. **Založí záznam do archivu** `EC_DopravaZakaznikovi_Archiv` — celou kopii řádku s poznámkou „Potvrzení odvozu zaměstnancem.". Ověřeno na datech, ke každému potvrzení archivní záznam sedí.
3. **Pošle dvě notifikace v Centrále** — Dušanovi (os. č. 105) a ZDivis (os. č. 147). Text: „Zakázka <číslo> – <příjemce> byla právě označena jako odvezená dopravcem: <dopravce>. Odvoz potvrdil: <login>".

**Tři věci, které mě u toho zaujaly**

- **Je to přepínač, ne jednosměrné potvrzení.** Když je `DatumOdvezeni` prázdné, doplní se čas; když už vyplněné je, druhý stisk ho **vynuluje** a smaže i to, kdo potvrdil. Původní hodnota zůstane jen v archivu.
- **Notifikace odejde i při tom zrušení** — a pořád s textem „byla právě označena jako odvezená". Příjemce to může svést na scestí.
- **Příjemci notifikace jsou natvrdo v kódu** (přihlašovací jména `Dusan` a `ZDivis`). Při personální změně se musí sáhnout přímo do procedury.

**Kde je tlačítko vidět**

Řídí se přepínačem `TlOdvozy` v nastavení terminálů (`EC_Dochazka_NastavZar`). Zapnuté má Tablet_Vedlejsi_Vchod, Tablet_Prizemi_Perforex, Ondra_Pc a jeden nepojmenovaný záznam. Vypnuté má Tablet_3NP a Tablet_Perforex.

**Co mě zarazilo v číslech**

Měsíční počty potvrzených odvozů jedou od roku 2024 stabilně mezi 15 a 40. Červenec 2026: 21. Srpen 2026 zatím **nula**, a přitom je 19. Nevím, jestli je za tím provozní změna nebo něco přestalo chodit — nechávám na zvážení, jestli to stojí za kontrolu.

**Co jsem neověřila**

Vlastní obarvení řádku a převod na hodnotu 1 v přehledu není v databázi (žádný databázový objekt slovo „Odvezeno" neobsahuje) — sedí to v klientovi Centrály. Že se to odvozuje z vyplněného `DatumOdvezeni`, je závěr z dat, ne z kódu. A ještě existuje procedura `EC_DopravaZakaznikovi_KontrolaVyplneni`, která s týmiž sloupci pracuje — tu jsem nečetla.

Kdyby k tomu bylo něco potřeba dohledat, dej vědět.

Peťa
