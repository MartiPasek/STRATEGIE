# Předání práce — docházka × rozpad na zakázky

**Pro:** Týnka
**Od:** Peťa (zpracoval Claude‑26)
**Datum:** 17. 8. 2026

---

## O co jde

V ERP je kontrolní přehled **Docházka → Kontrolní přehledy → Docházka × rozpad**.
Porovnává dvě čísla za každý den a člověka:

- **docházka** = kolik měl ten den odpracováno (píchnutí příchodů a odchodů),
- **rozpad** = kolik z toho má rozúčtováno na konkrétní zakázky a činnosti.

Tahle dvě čísla mají sedět. Přehled vypisuje jen dny, kde se liší o víc než 0,1 hodiny.

---

## Záměr, ke kterému to směřuje

**Zakázka a činnost se mají zadávat rovnou přes potvrzení příchodu z notifikace.**
Když člověku přijde do mobilu otázka „jsi v práci?" a on ji potvrdí, má se ho systém
hned doptat, **na jakou zakázku a činnost** jde dělat. Tím by rozpad začínal ve stejnou
chvíli jako docházka a nevznikaly by ranní díry.

**Tohle zatím postavené není.** Ověřeno 17. 8. 2026 přímo v kódu: potvrzení příchodu
z notifikace udělá jedinou věc — založí záznam docházky s aktuálním časem. Žádná další
otázka, žádná navazující notifikace. Není to tedy porucha, která by se občas neprojevila
— nedoptá se to nikoho.

---

## Co je hotové

Všechno níže je zapsané jako **pojistka** (hlídací pravidlo v databázi, tabulka
`tenant.pojistka`). Pojistky se dají kdykoli zkontrolovat dotazem
`SELECT * FROM tenant.pojistky_check();` — vypíše **jen to, co je rozbité**,
takže prázdný výsledek znamená, že je vše v pořádku.

| Co | Kdy | Pojistka |
|---|---|---|
| Každý uzavřený řádek rozpadu musí mít vazbu na své píchnutí (jinak vznikají „sirotci", které není vidět v Opravách) | | `dochazka-rozpad-ma-vazbu-na-pichnuti` |
| Po odhlášení přes notifikaci se spustí kaskáda, která chybějící rozpad dopočítá | 12. 8. 2026 | `dochazka-kaskada-po-odhlaseni-z-notifikace` |
| Kaskáda přeskočí úseky s nulovou délkou (nemají co rozúčtovat) | | `dochazka-kaskada-preskoci-nulove-useky` |
| Kaskáda ignoruje pouhá ohlášení (např. sick day, který nemá konec) | | `dochazka-kaskada-ignoruje-ohlaseni` |
| „Návrat z pauzy" z notifikace zasáhne jen tehdy, když opravdu běží pauza | 12. 8. 2026 | `dochazka-navrat-z-pauzy-jen-pri-pauze` |
| Píchnutí z mobilu se ukládá na celé minuty, bez sekund — i do rozpadu | | `cas-bez-sekund` |
| Půlnoční automat uzavírá nejen docházku, ale i položky rozpadu | | `pulnoc-uzavira-i-rozpad` |
| Ohlášený home office se do porovnání nepočítá (není to práce na zakázce) | 5. 8. 2026 | v SQL přehledu |

„Kaskáda" = automatický dopočet, který dorovná rozpad podle docházky. Je to ta samá
logika, kterou používají ruční opravy docházky, takže výsledek je konzistentní.

---

## Stav k 17. 8. 2026

Přehled hlásí **7 dnů u 5 lidí** (období od 1. 8., dny do včerejška):

| Kdo | Den | Docházka | Rozpad | Rozdíl | Příčina |
|---|---|---|---|---|---|
| Eliška Kolářová | 12. 8. | 8,29 | 6,59 | −1,70 | ranní díra po potvrzení z notifikace |
| Erika Sedláčková | 14. 8. | 8,08 | 7,69 | −0,39 | ranní díra po potvrzení z notifikace |
| Vladimír Navrátil | 11. 8. | 8,36 | 8,20 | −0,16 | ranní díra po potvrzení z notifikace |
| Michal Jirkovský | 11. 8. | 8,09 | 8,34 | +0,25 | prázdné píchnutí na začátku dne |
| Michal Jirkovský | 13. 8. | 8,27 | 8,51 | +0,24 | prázdné píchnutí na začátku dne |
| Michal Jirkovský | 14. 8. | 6,00 | 6,17 | +0,17 | prázdné píchnutí na začátku dne |
| Matěj Svoboda | 12. 8. | 7,92 | 7,81 | −0,11 | zaokrouhlení, nasčítané z 8 píchnutí |

### Příčina 1 — ranní díra po potvrzení příchodu z notifikace

Člověk potvrdí příchod z notifikace, tím se založí docházka. Rozpad ale začne teprve
ve chvíli, kdy si v aplikaci vybere zakázku. Doba mezi tím nemá zakázku žádnou.

- **Kolářová 12. 8.:** docházka od 7:41, rozpad až od 9:22 → chybí 1,68 h
- **Sedláčková 14. 8.:** docházka od 5:10, rozpad od 5:33 → 0,39 h
- **Navrátil 11. 8.:** docházka od 4:50, rozpad od 4:59 → 0,15 h

Oprava z 12. 8. tohle měla řešit — jenže **kaskáda se pouští jen při odhlášení přes
notifikaci.** Kolářová i Sedláčková si den zavřely normálně v aplikaci, takže se kaskáda
vůbec nespustila. Navrátil je z 11. 8., tedy ještě před opravou.

### Příčina 2 — prázdné píchnutí na začátku dne

Jirkovský má ráno píchnutí s nulovými hodinami (7:14 / 7:07 / 7:21) a hned po něm
skutečný začátek práce (7:31 / 7:22 / 7:34). Rozpad se natáhne **od toho prázdného
píchnutí**, docházka počítá až od toho druhého — mezera 13 až 17 minut je proto
v rozpadu navíc.

### Příčina 3 — zaokrouhlení

Hodiny uložené v docházce jsou u **každého** píchnutí o kousek vyšší než přesný rozdíl
časů (o 0,003 až 0,02 h), nikdy nižší. U jednoho dvou píchnutí to není vidět, u Svobody
jich bylo osm a nasčítalo se to na 0,11. **Kde přesně to zaokrouhlení vzniká, ověřené
není** — je to ve výpočtu hodin a do toho jsme zatím nešli.

---

## Co je ještě potřeba

1. **Doptat se na zakázku a činnost při potvrzení příchodu z notifikace.** Hlavní věc,
   viz Záměr nahoře. Odstranilo by to příčinu 1 u zdroje, ne až dopočtem.
2. **Rozšířit spouštěč kaskády.** Dnes běží jen při odhlášení přes notifikaci. Má běžet
   i při běžném uzavření dne v aplikaci a při půlnočním automatu. Malá změna, která by
   pokryla Kolářovou i Sedláčkovou.
3. **Prázdná píchnutí na začátku dne.** Rozhodnout, jestli má rozpad začínat od nulového
   píchnutí, nebo až od skutečného začátku práce. Dnes dělá to první a rozpad kvůli tomu
   vychází vyšší než docházka.
4. **Zaokrouhlení hodin.** Systematické a nikdy nespadne na nulu, takže hranice 0,1 h
   bude u lidí s hodně píchnutími za den vyskakovat pořád, i když je všechno v pořádku.
   Bude potřeba buď srovnat výpočet, nebo hranici odvodit od počtu píchnutí.
5. **Naplánovaná týdenní kontrola má zastaralý dotaz.** Je to starší kopie přehledu —
   chybí jí seznam lidí, kteří se nekontrolují, a filtr na ohlášený home office z 5. 8.
   Kvůli tomu hlásí lidi navíc. Je potřeba ji srovnat s tím, co má aplikace.

---

## Kde co najdeš

| Věc | Kde |
|---|---|
| Přehled pro uživatele | ERP → Docházka → Kontrolní přehledy → Docházka × rozpad |
| SQL toho přehledu | databáze, `g2007.python`, kód `dochazka_kontrola_data` |
| Potvrzení příchodu z notifikace | databáze, `g2007.python`, kód `att_do_att_action` |
| Kontrola pojistek | `SELECT * FROM tenant.pojistky_check();` |
| Docházka (píchnutí) | `tenant.att_entry` |
| Rozpad na zakázky | `tenant.vyroba_work` |

Pozor: kód téhle části **žije v databázi**, ne v souborech na disku. Soubory obsahují
už jen pár řádků, které logiku z databáze zavolají. Úpravy se dělají v databázi —
projeví se hned, bez nasazování a bez restartu aplikace.

---

*Claude‑26 / Peťa*
