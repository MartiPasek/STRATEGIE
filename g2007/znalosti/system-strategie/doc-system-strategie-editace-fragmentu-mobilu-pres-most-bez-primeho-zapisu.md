# Editace fragmentu mobilu z mostu - kolo base64 pro vymenu celeho obsahu; primy zapis do g2007.soubor uz ZAKAZANY NENI (opraveno 25.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## !! NEPLATI k 28. 8. 2026 v jednom bodu: fragmenty NEJSOU jedna spolecna closure
> 
> Sekce "Souvisejici, at se na to nezapomene" nize tvrdi, ze fragmenty jsou "hole deklarace
> funkci uvnitr JEDNE obalove funkce" a sdileji `el`, `topbar`, `go`, `api` pres closure.
> **Dnes to tak neni.** Kazdy dilek je **vlastni `<script>` blok s vlastni IIFE**, ktera si
> zavislosti bere z `window.__M2W`, a konci `} catch(e){...}` + registraci pres `__setImpl`.
> Funkce z jednoho dilku proto **neni videt z jineho**, dokud se nezaregistruje do `window.__M2W`.
> Zjisteno naostro 27. 8. 2026 (pad `_mojeHlavicka is not defined` pri presunu fotky a Novinek
> mezi dilky 48 a 60; `node --check` pri publikaci prosel, chyba se ukazala az v prohlizeci).
> Detail a postup: [[doc-system-strategie-mobil-dilky-nejsou-jedna-closure]].
> **Zbytek dokumentu plati beze zmeny** - puvodni veta je nize schvalne ponechana, at je videt,
> co se zmenilo.

> ## !! ROZPOR S PRAVIDLY VYRESEN 26. 8. 2026
>
> Rozpor nahlasil Claude-28: `STRATEGIE_PRAVIDLA_PRACE.md` bod 4 do 26. 8. rikal
> "vyhradne @@G2007SOUBOR", coz je timhle dokumentem prekonane od 25. 8. Potvrdila
> Marti-AI (msg 13832): cileny zapis s md5 pojistkou je bezpecnejsi nez cely soubor,
> protoze hlida soubeh a nedotkne se niceho jineho; cely soubor zustava spravny pri
> vetsi prestavbe nebo kdyz je jasne, ze nikdo jiny soucasne nepise. Rozhodl Jirka:
> souhlasi. **Bod 4 v `STRATEGIE_PRAVIDLA_PRACE.md` uz popisuje obe cesty.**

> ## !! OPRAVA 25. 8. 2026 - PRIMY ZAPIS DO `g2007.soubor` UZ ZAKAZANY NENI
>
> Tenhle dokument od 17. 8. 2026 tvrdil, ze most primy `UPDATE g2007.soubor` odmita
> a ze **jedina** cesta k editaci fragmentu je `@@G2007SOUBOR` s celym novym obsahem.
> **To uz neplati.** 25. 8. 2026 prosel primy `UPDATE g2007.soubor SET obsah = replace(...)`
> pres most a runner ho vyridil jako **`G2007 KONSTRUKTIVNI (primo, bez banneru)`**.
> Stejnou cestou jde i `UPDATE g2007.python`. Overeno naostro tyz den (fragment
> `50_skupiny_vyroba.js` verze 15 -> 16, otisk po zapisu precten z DB), viz
> [[doc-dochazka-absence-obrazovka-bez-karty-zamestnance]].
>
> **Co si z toho vzit:**
> - **Cilena zaplata jednoho mista** = `UPDATE ... SET obsah = replace(obsah, <kotva>, <novy text>)`
>   **s pojistkou `AND md5(obsah) = '<otisk, ktery jsi prave cetl>'`**. Pri soubehu projde
>   0 radku misto ticheho prepsani cizi prace. Diakritiku posilej pres
>   `convert_from(decode('<base64>','base64'),'UTF8')`, at ji nerozbije cesta.
>   **Kotvu si predem over dotazem, ze je v souboru prave jednou.**
> - **Vymena celeho obsahu** = dal `@@G2007SOUBOR` a kolo s base64 popsane nize. Postup nize
>   je stale platny a spravny, uz jen **neni jediny mozny**.
> - **Pri skladani base64 po kouscich dekoduj KAZDY kusek zvlast a spoj az bajty.**
>   Slepit base64 retezce a dekodovat najednou NEJDE - kazdy kus konci vlastnim odsazenim
>   (`=`) a dekoder za nim skonci. Zjisteno 25. 8. 2026: z 4430 bajtu se vratilo jen 4000
>   a otisk nesedel.
>
> Zbytek dokumentu nize zustava beze zmeny. Vety, ktere uz neplati, jsou oznacene **NEPLATI**.

## Co se zmenilo

Most (`/diag-sql`) **odmita primy zapis do `g2007.soubor`**. Pokus o `UPDATE g2007.soubor SET obsah = ...` vraci:

```
query_raw obsahuje forbidden keyword (DELETE/UPDATE/INSERT/DROP/...). Pouzij dedicated tool.
```

Kontrola forbidden keywords bezi **az za obsluhou `@@` prikazu**, takze `@@` prikazy fungujou normalne a slovo UPDATE uvnitr jejich textu nic neshodi. ~~Jedina cesta k editaci fragmentu je proto **`@@G2007SOUBOR`, ktery bere CELY novy obsah**.~~ **NEPLATI od 25. 8. 2026** - primy `UPDATE` prochazi jako G2007 konstruktivni operace, viz ramecek na zacatku. `@@G2007SOUBOR` zustava spravnou cestou pro vymenu CELEHO obsahu.

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

Naprava, kterou dosud doporucovala G2007 (`UPDATE ... SET obsah = obsah || chr(10)`), ~~**JIZ NENI DOSTUPNA** - most primy zapis zakazuje.~~ **NEPLATI od 25. 8. 2026** - primy `UPDATE` uz prochazi, takze i tahle naprava je zase dostupna. Misto ni:

**Over, ze hranice fragmentu je syntakticky bezpecna.** `@@G2007SESTAV`/`@@G2007PUBLISH` slepuji fragmenty pres `"".join(...)` **bez separatoru**, takze posledni radek tveho fragmentu se slepi s prvnim radkem nasledujiciho.
- Bezpecne: tvuj fragment konci `;` nebo `{` nebo `}`. 17.8.2026 `50_skupiny_vyroba.js` konci radkem `  try {` a `51_skupiny_sdileny.js` zacina `  function skupiny(){` - slepene `  try {  function skupiny(){` je platny JS a `node --check` v `@@G2007PUBLISH` prosel.
- **NEBEZPECNE: kdyz tvuj fragment konci `//` komentarem** - slepenim se zakomentuje prvni radek nasledujiciho fragmentu a appka spadne tise. V tom pripade posledni radek prepis tak, aby komentarem nekoncil.

## Souvisejici, at se na to nezapomene

Fragmenty **nejsou samostatne IIFE** - jsou to hole deklarace funkci uvnitr JEDNE obalove funkce otevrene v `10_core.js` a zavrene az v `74_claude27_render_init.js`, sdileji `app`, `el`, `topbar`, `go`, `api` pres closure. Proto (a) bare `go("...")` uvnitr fragmentu funguje, (b) `</script><script>` mezi fragmenty **NEPRIDAVAT** (zkouseno 1.8.2026, shodilo `/mobile`), (c) pro test v prohlizeci se musi prepsat `window.fetch`, prepsani `window.__M2W.api` se do fragmentu neprojevi.

