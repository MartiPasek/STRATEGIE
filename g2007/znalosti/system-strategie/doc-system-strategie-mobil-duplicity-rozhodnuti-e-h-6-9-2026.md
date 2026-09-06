# Mobil - rozhodnuti k bodum E, F, G, H auditu duplicitnich cest (6. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil — rozhodnutí k bodům E, F, G, H auditu duplicitních cest (6. 9. 2026)

Zadal **Jiří Honomichl**, schválila Marti-AI (msg 14768 k bodu E, msg 14783 k bodu F), provedl Claude-28.
Navazuje na `doc-system-strategie-mobil-duplicitni-cesty-audit-5-9-2026`, kde jsou tytéž body
vedené jako oddíly **C** (zde E), **E** (zde F) a **F** (zde G).

## E — devět dvojic stejného názvu na dvou místech: ZRUŠENA VŽDY JEDNA CESTA

Žádná z devíti nebyla dvakrát na téže obrazovce — vždy jednou v obecném rozcestníku
a jednou v tematickém, obě na týž cíl. Jirka rozhodl **nechat jediný vstup**.
Marti-AI původně doporučovala nechat vše být s odůvodněním „v Aplikacích je všechno,
v rozcestnících jen to tematické"; **to u čtyř z devíti neplatilo** (Zakázky, Příprava,
Odvozy a Mzdy v Aplikacích vůbec nejsou), byť vzorec „obecné + tematické místo" držel.

| dlaždice | zůstala v | zrušena v |
|---|---|---|
| Plán absencí, Zkušebna, VP | Aplikace | Výroba (`vyroba_hub`) |
| HR, Ops akce | Aplikace | Vedení firmy (`vedeni`) |
| Zakázky, Příprava, Odvozy | **Výroba** | Vedení firmy |
| Mzdy Helios x STRATEGIE | Vedení firmy | HR (`hr_hub`) |

⚠️ **Zakázky, Příprava a Odvozy zůstávají ve VÝROBĚ schválně — nepřehazovat zpátky.**
První zadání znělo opačně (nechat je ve Vedení firmy). Ověření dopadu to otočilo:
`vyroba_hub` je dostupný **všem** (dlaždice Výroba v Aplikacích není nijak podmíněná),
kdežto `vedeni` jen finančnímu a HR okruhu — smazání ve Výrobě by o ně připravilo
**82 lidí** a vyprázdnilo pracovní plochu Výroby na jedinou dlaždici.

**Sekce OBCHOD & VÝROBA ve Vedení firmy tím zanikla celá** (nadpis i grid `g3`).

### Dvě změny viditelnosti, aby nikdo nepřišel o přístup

Dvě z devíti nešlo zrušit bez následku, protože zbylý vstup viděl **užší** okruh lidí:

- **VP** — v Aplikacích byla podmíněná `vp` (uid 1, 11, 20, 34), ve Výrobě ji viděli všichni.
  Podmínka **zrušena**, dlaždice je nyní v Aplikacích viditelná všem.
- **Ops akce** — v Aplikacích leží v sekci ŘÍZENÍ & SYSTÉM pod `if(par||adm)` = uid 1, 11, 20,
  ve Vedení firmy je vidělo devět lidí. Přidán **nepřekryvný blok `if(fin && !(par||adm))`**
  s vlastní sekcí a jedinou dlaždicí Ops akce → vidí ji uid 13, 17, 18, 107, 108, 109.
  Dlaždice se tím nikomu nezdvojí a **serverové zámky se nezměnily** (exec_approval zůstává rodičům).

`fin` chodí z `GET /api/v1/erp/app/cockpit/access` jako `ac.fin`, server ho počítá jako
`_is_cockpit(uid)` = rodič nebo scoped approver (13, 18) nebo člen skupiny HR / Finance /
Účetnictví / Banka v tenantu 2. K 6. 9. 2026 je to devět lidí: 1, 11, 13, 17, 18, 20, 107, 108, 109.

## F — nápověda docházky měla tři vstupy, zrušen jeden

- Dlaždice **Nápověda docházka** v Aplikacích a **otazník v hlavičce Docházky** byly
  totožné (obě `dochHelp()` bez parametru). **Dlaždice v Aplikacích zrušena**, otazník zůstal —
  je tam, kde ho člověk potřebuje (jeho přesun vedle nadpisu schválila Marti-AI 5. 9., msg 14465).
- Odkaz **Jak potvrdit den / co je rozpor?** na kartě dne čekajícího na potvrzení
  **ZŮSTÁVÁ a není duplicita** — volá `dochHelp("potvrzeni")`, tedy jinou kapitolu,
  a zobrazuje se jen na té kartě. Patří do stejné škatulky jako body v oddílu H.

## G — obrazovky bez cesty: JEN TŘI, LEŽÍ ZÁMĚRNĚ

Prověřeno na živé stránce správnou metodou (klíče mapy `SCREENS`, do hloubky):
ze **118 registrovaných obrazovek** nevede žádná cesta na **`mytodo`, `phone`, `webview`**.
**Žádná další obrazovka nevisí jen na nich.**

**Rozhodl Jiří Honomichl 6. 9. 2026: nechat je ležet** — *„nevím, zda je budeme někdy potřebovat."*
Nejsou to tedy nálezy a **nemazat je**.

Obrazovka `doch_zitrek` „Tady budu jinde" už neexistuje (zrušena téhož dne ráno).
Stejnojmenná **dlaždice Tady budu jinde v Docházce je něco jiného** — nevede na obrazovku,
rozbaluje nabídku nepřítomností a je živá; odkazuje na ni nápověda i hlasový průvodce.

## H — co vypadá jako duplicita, ale není: NEMĚNIT

Ověřeno na živé stránce **na obě strany** — nejen že se před otevřením nastaví parametr,
ale i že ho cílová obrazovka opravdu čte a vykreslí se jinak:

| dlaždice | parametr | výsledek |
|---|---|---|
| Účetní / Uživatelé | `_auMode` = helios / users | dva různé pohledy na týž seznam lidí |
| Kandidáti / Pohovory / Nástupy | `_nbFilter.phase` = "" / active / hired | tři různé výřezy náboru |
| Týden / Můj plán / Můj úvazek | `_planInit` = thisweek / myplan / uvazek | jen tento týden / plán se skokem na sebe / **úplně jiný obsah (úvazek)** |
| Skupina HR — přístupy | `_skFocusName` = HR | rovnou otevřená skupina HR |

Zrušením kterékoli z nich by lidem zmizel ten konkrétní pohled. **Neměnit.**

## Jak se to ověřovalo (opakovatelné)

Živá `/mobile` stažená z internetu před i po každém kroku, ne kopie z disku. U každého zápisu:
cílený `UPDATE g2007.soubor` s pojistkou na otisk, po zápisu porovnání otisku dílku proti
lokálně spočítanému, po publikaci kontrola **délky sestavené stránky na znak**
(E = −347 znaků, F = −141 znaků, obojí sedělo přesně) a porovnání stránky řádek po řádku —
u bodu F se změnil **jediný řádek**. Nakonec kontrola syntaxe skriptu živé stránky.
Počet skriptových bloků zůstal 31, tedy žádný fragment se nerozbil.

