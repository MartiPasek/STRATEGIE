# Editace fragmentu mobilu z mostu - primy zapis do g2007.soubor je ZAKAZANY, overeny postup pres base64 kolo (17.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se zmenilo

Most (`/diag-sql`) **odmita primy zapis do `g2007.soubor`**. Pokus o `UPDATE g2007.soubor SET obsah = ...` vraci:

```
query_raw obsahuje forbidden keyword (DELETE/UPDATE/INSERT/DROP/...). Pouzij dedicated tool.
```

Kontrola forbidden keywords bezi **az za obsluhou `@@` prikazu**, takze `@@` prikazy fungujou normalne a slovo UPDATE uvnitr jejich textu nic neshodi. Jedina cesta k editaci fragmentu je proto **`@@G2007SOUBOR`, ktery bere CELY novy obsah**.

## Past: fragment nejde vyvezt na disk

`@@G2007EXPORT` ma v kodu `WHERE kod=:k AND typ='artefakt'` - **umi jen artefakty** (`mobile.html`), **ne zdrojove fragmenty** (`mobile_parts/*.js`, `typ='zdroj'`). Fragmenty na disk vubec nechodi; kopie v gitu je zastarala a **lze z ni delat jen falesne zavery** (viz [[doc-system-strategie-staticke-artefakty-db-materializace-vyrazeni-z-gitu]]).

Vysledek obou veci dohromady: fragment se **nema kde vzit ani kam poslat po castech**. Naivni SELECT obsahu nepomuze - vystup mostu je TSV a **zalomeni radku v hodnote se cestou slepi na mezery**, takze obsah nejde vratit zpatky nepoškozeny.

## Overeny postup (kolo base64), 17.8.2026

1. **Stahni fragment jako base64 po kouscich**, ne jako text:
   `WITH s AS (SELECT convert_to(obsah,'UTF8') AS b, octet_length(obsah) AS n FROM g2007.soubor WHERE kod=...), i AS (SELECT generate_series(0,4) AS k) SELECT i.k, replace(encode(substring(s.b FROM i.k*14000+1 FOR 14000),'base64'), chr(10),'') FROM s,i WHERE i.k*14000 < s.n ORDER BY i.k;`
   - `replace(..., chr(10), '')` je **povinne** - `encode(...,'base64')` v Postgresu lame vystup po 76 znacich a to by rozbilo TSV.
   - Chunky **musi byt na bajtove hranici** (`convert_to` na bytea), ne na znakove - jinak slepeni base64 nedava puvodni bajty.
2. **Sloz lokalne a NEJDRIV over otisk originalu** proti `md5(obsah)` z DB. Kdyz nesedi, dal se nejde - kolo je poskozene.
3. **Zaplatuj cilenym `replace()`** na jednoznacnych kotvach (predem si over, ze kazda kotva je v souboru **prave jednou**).
4. **Spocitej vysledny otisk nanecisto NA SERVERU** stejnym `replace()` v SELECTu a **porovnej s lokalnim md5**. Kdyz oba souhlasi, tvoje kopie je bajt za bajtem totozna s tim, co v DB vznikne.
5. Posli `@@G2007SOUBOR <kod> | zdroj` + newline + cely obsah.
6. **Precti otisk z DB** - navratovka je neutralni (0 radku), i kdyz zapis prosel.
7. Sestav a nasad `@@G2007PUBLISH apps/api/static_db/mobile.html` (dela `node --check` + samo-overeni zive URL + automaticky rollback) a nakonec si **saham na zivou `/mobile`** - HTTP 200, pocet znaku, pocet skriptovych bloku, konzole.

## ZMENA STARE GOTCHY: orez konce uz nejde napravit UPDATE

Runner dela `sql = SQL_FILE.read_text(...).strip()` (`claude_sql_runner.py` r. 598) na **celem** obsahu souboru. U `@@G2007SOUBOR` proto:

- **Uvodni mezery fragmentu zustanou** - jsou az za hlavickou prikazu (server dela `_rest3.split("\n", 1)`), takze je strip nesebere. Dosud se to uvadelo jako riziko, **neni**.
- **Koncove zalomeni radku se ztrati** - vzdy. 17.8.2026 to znamenalo 56022 na 56021 znaku.

Naprava, kterou dosud doporucovala G2007 (`UPDATE ... SET obsah = obsah || chr(10)`), **JIZ NENI DOSTUPNA** - most primy zapis zakazuje. Misto ni:

**Over, ze hranice fragmentu je syntakticky bezpecna.** `@@G2007SESTAV`/`@@G2007PUBLISH` slepuji fragmenty pres `"".join(...)` **bez separatoru**, takze posledni radek tveho fragmentu se slepi s prvnim radkem nasledujiciho.
- Bezpecne: tvuj fragment konci `;` nebo `{` nebo `}`. 17.8.2026 `50_skupiny_vyroba.js` konci radkem `  try {` a `51_skupiny_sdileny.js` zacina `  function skupiny(){` - slepene `  try {  function skupiny(){` je platny JS a `node --check` v `@@G2007PUBLISH` prosel.
- **NEBEZPECNE: kdyz tvuj fragment konci `//` komentarem** - slepenim se zakomentuje prvni radek nasledujiciho fragmentu a appka spadne tise. V tom pripade posledni radek prepis tak, aby komentarem nekoncil.

## Souvisejici, at se na to nezapomene

Fragmenty **nejsou samostatne IIFE** - jsou to hole deklarace funkci uvnitr JEDNE obalove funkce otevrene v `10_core.js` a zavrene az v `74_claude27_render_init.js`, sdileji `app`, `el`, `topbar`, `go`, `api` pres closure. Proto (a) bare `go("...")` uvnitr fragmentu funguje, (b) `</script><script>` mezi fragmenty **NEPRIDAVAT** (zkouseno 1.8.2026, shodilo `/mobile`), (c) pro test v prohlizeci se musi prepsat `window.fetch`, prepsani `window.__M2W.api` se do fragmentu neprojevi.

