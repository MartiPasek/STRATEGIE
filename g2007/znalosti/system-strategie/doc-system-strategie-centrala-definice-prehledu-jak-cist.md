# Stara Centrala: jak precist definici prehledu, akci a volanych procedur (pasti, 25. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Jak z Centraly vycist, jak je prehled postaveny

Postup overeny 25. 8. 2026 pri rozboru prehledu "Cely den - VV". Vse pres SQL most, `db=mssql` (databaze DB_EC).

## 1. Definice prehledu

Tabulka **`EC_DELPHI_TabObecnyPrehled`**.

⚠️ **PAST c. 1: cislo prehledu je ve sloupci `Cislo`, NE v `ID`.** Cislo, ktere Centrala ukazuje ve stavovem radku (napr. 2060), je `Cislo`. Hledani podle `ID` vrati **uplne jiny prehled** a vypada to jako spravny vysledek. Stalo se to hned na zacatku rozboru.

Klicove sloupce: `DefView` (zdrojovy dotaz), `InsertSQL` / `UpdateSQL` / `DeleteSQL` (co dela Novy / Oprava / Smazat), `ID_Edit` (odkaz na editacni formular), `MasterFieldName`, `Nazev`, `Skupina`.

⚠️ **PAST c. 2: prazdny `DeleteSQL` neznamena, ze mazani neni.** A naopak — u prehledu 2060 `DeleteSQL` existuje, ale jen vraci hlasku "nelze smazat"; skutecne mazani je zakomentovane. **Cti obsah, ne delku.**

⚠️ **PAST c. 3: sloupce, ktere vypadaji prazdne, mohou nest funkcni hodnotu.** U 2060 je `IDKontroly` natvrdo `-2` a to je **priznak "otevri posledni kontrolu"**, na ktery reaguje jadro chyb. Neni to prazdno.

## 2. Podminena barevnost radku

**`EC_DELPHI_TabObecnyPrehledPodminky`** (vazba pres `CisloPrehledu`). Kdyz je prazdna, zvyrazneni na snimku obrazovky je jen **oznaceni radku uzivatelem**, ne podminene formatovani.

## 3. Akce praveho tlacitka

**`EC_FormDefPopupMenu`** (vazba `CisloPrehledu`) = polozky menu. Sama o sobe **neobsahuje zadny kod**.

Co se pod polozkou spusti: **`EC_FormDefEditAkce`** pres `ID_PopupMenu`. Jedna polozka menu ma casto vic kroku (`Poradi`).

Vyznam `CisloAkce` je v ciselniku **`EC_FormDefActionList`** (sloupec `NazevAkce`, popis v `Popis`):
- **6** = spust SQL proceduru (nazev v `Parametr2`)
- **9** = zobraz pozadovany prehled (`Parametr1` = cislo prehledu)
- **30** = grid, SQL procedura s parametrem (`Parametr1` = cislo formulare/jadra, `Parametr2` = procedura)
- **35** = otevri formular jadra (`Parametr1` = ID formulare)
- **1010** = obnov vybrany dataset (`Parametr2` = nazev datasource)

⚠️ **PAST c. 4: polozka menu bez radku v `EC_FormDefEditAkce` je MRTVA.** U 2060 tak vypada "Smazat cely den" — v menu je, ale nedela nic. Overeno i pres ostatni vazby (`ID_Prehledu`, `ID_Komponenty`).

## 4. ⚠️⚠️ PAST c. 5 (nejzavaznejsi): pocitadlo spusteni meri JEN rucni klikani

`EC_FormDefEditAkce` ma sloupce `CitacSpusteni`, `NaposledySpusteno`, `PoprveSpusteno`. Je lakave z nich odvodit, co se pouziva a co je mrtve.

**Nula v pocitadle NEZNAMENA, ze se procedura nepouziva.** Meri se jen spusteni z te polozky menu. Procedura muze byt volana **automaticky z jine procedury** a bezet denne.

Konkretne u "Cely den - VV": `EC_Dochazka_ProdluzObed` mela pocitadlo **0** a `EC_Dochazka_SrovnejCasy` **1** — pritom se **obe volaji automaticky z nocni kontroly** `EC_KontrolaDochazky` u kazdeho cloveka a kazdeho dne. Puvodni zaver "temer se nepouzivaji" byl proto **zavadejici a musel se opravit**.

**Pravidlo:** nez z pocitadla vyvodis, ze je neco mrtve, **prohledej telo ostatnich procedur na nazev te procedury**.

## 5. Editacni formulare (jadra)

**`EC_FormDef`** = formulare (`Nazev`, `EditModeCondition`, `SQL_Select`).
**`EC_FormDefEdit`** = jednotliva pole (`cCaption`, `cFieldName`, `cTop`, `cLeft`, `Smazana`).

⚠️ **PAST c. 6:** `EC_FormDef.SQL_Select` u jadra casto neobsahuje dotaz, ale **cislo prehledu**, ze ktereho se jadro plni. Teprve v tom prehledu jsou `UpdateSQL` a `InsertSQL`.

⚠️ **PAST c. 7:** hodne radku v `EC_FormDefEdit` ma popisek "NOVA" a prazdne pole — skutecne vlastnosti jsou v `EC_FormDefEditProperty`. Priznak `Smazana=True` navic **neznamena, ze pole na obrazovce neni**.

## 6. Cim overit, co prehled dela DNES

Definice rikaji, co JDE. Co se realne deje, rekne az pohled do dat:
- kolik zaznamu za poslednich 40 dni (zda zdroj vubec zije),
- pocitadla akci **plus** hledani volani v ostatnich procedurach (viz past 5),
- kdo je podepsany ve sloupcich typu `ChybuPotvrdil` — to rekne **jmenovite**, kdo nastroj pouziva.

