# Bod obnovy pred vetsim zasahem do obsahu appky - ctyri vrstvy a POVINNY nacvik navratu (overeno 3. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Kdy to pouzit

Pred **vetsim zasahem do obsahu webu nebo mobilni appky** (`g2007.soubor`), zvlast kdyz je
predem jasne, ze se to muze nelibit a bude se vracet. Samotna automaticka historie
(`doc-system-strategie-soubor-historie-automaticky-archiv`) je dobra zachranna sit,
ale navrat z ni znamena hledat spravny radek podle casu. Pojmenovany bod obnovy je **jeden krok**.

## Ctyri vrstvy

**1. Pojmenovana zaloha v databazi**

```sql
CREATE TABLE g2007.soubor__zaloha_<tema>_<RRRRMMDD> AS
SELECT * FROM g2007.soubor
WHERE kod LIKE 'apps/api/static/mobile_parts/%'
   OR kod = 'apps/api/static_db/mobile.html';
```

⛔ **NIKDY nepis `SELECT ... INTO`** - most to vyhodnoti jako cteni, pusti bez schvalovaciho
prouzku a zahodi; tabulka nevznikne a hlaska vypada jako drobnost.
Viz `doc-system-strategie-most-select-into-nevytvori-tabulku`.

**2. Seznam otisku mimo databazi** - `SELECT kod, length(obsah), md5(obsah) ...` a uloz mimo DB.

**3. Skutecny obsah mimo databazi** - obsah zil dosud jen v databazi (ziva tabulka + zaloha
+ historie = jedno misto). Stahni ho:

```sql
SELECT encode(convert_to(obsah,'UTF8'),'base64') AS b64
FROM g2007.soubor WHERE kod = '<kod>';
```

Vystup z `CLAUDE_OUT_FULL.txt` (bez prvniho radku s nazvem sloupce), odstranit mezery a zlomy,
dekodovat z base64 a **hned overit md5 proti seznamu z vrstvy 2**.
Overeno 3. 9. 2026: **most unese i slozenou stranku pres 1 MB**, projde vsech 32 zaznamu.

**4. Navratovy stav kodu** - poznamenat commit. Overit, ze mezi nim a dneskem **nejsou zadne
databazove migrace**, jinak navrat kodu nestaci.

## ⭐ NACVIK NAVRATU - bez nej to neni bod obnovy

Zadani i zdravy rozum zada **overit, ze navrat funguje**, ne jen ze zaloha sedi.
Bezpecny nacvik naostro, ktereho si nikdo nevsimne:

1. Vyber **prazdny a nepouzivany dilek** (napr. `45_hr_hub.js`, 0 znaku).
2. Zapis do nej jeden znak (cileny UPDATE s pojistkou na md5).
3. **Over ctenim, ze je opravdu zmeneny** - jinak si nacvik jen namlouvas.
4. Spust **presne ten navratovy prikaz**, ktery mas v bodu obnovy zapsany:
   ```sql
   UPDATE g2007.soubor z SET obsah = b.obsah
   FROM g2007.soubor__zaloha_<tema>_<RRRRMMDD> b
   WHERE z.kod = b.kod AND z.obsah IS DISTINCT FROM b.obsah;
   ```
5. **Over ctenim**, ze otisk je zpet a ze proti zaloze sedi vsechny zaznamy.
6. **NEPUBLIKUJ.** Cely nacvik probehne jen v databazi, ziva `/mobile` se nehne
   a lide v telefonu nic nepoznaji.

Jedina stopa, ktera po nacviku zustane, je **cislo `verze` u toho dilku o 2 vyssi**.
Obsah je bajt po bajtu puvodni a cislo verze na chovani appky nema vliv.

## Pri skutecnem navratu nezapomen na publikaci

Vrat obsah (prikaz vyse), over ctenim, a **teprve pak** `@@G2007PUBLISH apps/api/static_db/mobile.html`.
Bez publikace zustane oprava jen v databazi a lide v telefonu vidi dal starou verzi -
server posila soubor **z disku**.
Nakonec over na zive `/mobile`, ze otisk stranky odpovida tomu v databazi.

## Zaloha zastarava

Bod obnovy je **otisk okamziku**. Kdyz se mezi jeho porizenim a zasahem cokoli zmeni
(pracuje vic lidi), **udelej ho znovu** - jinak by navrat vratil zastaraly stav.
Pred zacatkem prace vzdy porovnej aktualni otisky proti zaloze.

