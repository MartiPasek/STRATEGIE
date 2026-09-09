# Editace cizi znalosti pres most bez poskozeni: base64 tam i zpet, reindex, a dve pasti (24.8.2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Jak bezpecne upravit CIZI znalost pres most (a dvě pasti, na kterých se to lame)

Zapsal Claude-28 (Jirka Honomichl) **24. 8. 2026**, schvalila Marti-AI (msg 13583)
vcetne jejiho doplneni (krok 5). **Overeno na dvou skutecnych znalostech** (115 a 126 radku).

## Proc to vzniklo

Platilo, ze **znalost, kterou pres most prectes kvuli editaci, nedostanes byte-presne** —
obsah prijde v tabulkovem vystupu se **slepenymi radky**, takze zpetny zapis by rozbil
formatovani. Dva dny se to obchazelo tim, ze se zakladal novy slug s odkazem misto opravy
na miste — coz ale zanechava **dvoji evidenci**, presne to, co zakazuje bod 14 pravidel prace.

**Uz to obchazet netreba.** Postup nize funguje.

## Bezpecny postup

**1. Precti obsah ZAKODOVANE** (a rovnou si vezmi nadpis a otisk):

```sql
SELECT nadpis, md5(obsah) AS otisk, length(obsah) AS delka,
       encode(convert_to(obsah, 'UTF8'), 'base64') AS kod
FROM g2007.znalost WHERE kod = 'doc-...';
```

**2. Dekoduj lokalne a POROVNEJ otisk.** Z base64 odstran vsechny bile znaky (vystup ho
zabaluje), dekoduj a spocitej md5. **Musi sednout na `otisk` z bodu 1** — teprve pak mas
byte-presnou kopii vcetne zlomu radku. Kdyz nesedne, **nepokracuj**.

**3. Uprav lokalne.** Cilene, jednou nahradou; nic neprepisuj "z hlavy".

**4. Zapis zpet pres `@@G2007ADD <oblast> <slug> | <nadpis>`** + obsah na dalsich radcich.
Soubor sestav **strojove** (hlavicka + zlom + obsah), ne prepisovanim — jinak zanesete chybu.
**Tohle je dulezite: `@@G2007ADD` navic PREPOCITA VEKTORY**, takze se srovna i vyhledavani.

**5. Over PO ZAPISU, ze obsah sedi na znak** (doplnila Marti-AI — jinak je smycka otevrena):

```sql
SELECT md5(btrim(obsah, chr(10))) = '<md5 tveho obsahu orezaneho o zlomy na obou koncich>'
         AS sedi,
       length(obsah) AS delka,
       (SELECT count(*) FROM g2007.znalost_chunk c WHERE c.znalost_id = z.id) AS chunku
FROM g2007.znalost z WHERE kod = 'doc-...';
```

Jeji zduvodneni doslova: *„krok 2 overuje byte-presnost cteni, ale ne zapisu… pokud by se
pipeline nekdy zmenil (normalizace whitespace, prevod koncu radku), past by se vratila tise."*
Kdo chce smycku uplne zavrenou, precte si po zapisu obsah znovu pres base64.

`btrim(obsah, chr(10))` tam je proto, ze zapis muze na obou koncich pridat nebo ubrat zlom
radku- **`@@G2007ADD` uklada obsah s UVODNIM zlomem** (oddelovaci radek za hlavickou, viz
`doc-system-strategie-most-gotchy-hlidac-dotazu-uvodni-zlom-a-lane3`) a zaroven **urizne
KONCOVY** (viz nize). Orez obou koncu na obou stranach obe veci obchazi najednou.
**Do 9. 9. 2026 tu stal `ltrim` — ten resil jen uvodni zlom a vyrabel falesne poplachy.**

### ⚠️ Ale pozor — `ltrim` sam umi vyrobit FALESNY POPLACH

**Zjisteno naostro 25. 8. 2026** (Claude-28 / Jirka Honomichl, souhlasila Marti-AI msg 13649).
Kontrola z kroku 5 ohlasila neshodu u znalosti, ktera se ulozila **naprosto presne**.
Pricina: **ta znalost sama legitimne ZACINA zlomem radku** (byl v ni od zacatku, ne od
`@@G2007ADD`), takze `ltrim` urizl i ten a otisky nesedly.

**Proto se od 9. 9. 2026 kontroluje `btrim` (oba konce), ne `ltrim`.** Do te doby tu stalo
"zkus dve varianty a staci, kdyz sedne jedna" — `md5(obsah)` a `md5(ltrim(obsah, chr(10)))`.
**Jenze zlomy jsou dva nezavisle na sobe** (uvodni a koncovy), takze pripadu je **ctyri**
a ty dve varianty pokryvaly jen dva. Dokument, ktery **zaroven** legitimne zacina zlomem
**a zaroven** mu zapis urizl koncovy, nesedl ani na jednu — a kontrola ohlasila neshodu
u obsahu ulozeneho presne na bajt. `btrim` na obou stranach resi vsechny ctyri pripady.

**Kdyz nesedne ani `btrim`, teprve pak** stahni obsah zpet pres base64 a porovnej **znak po znaku** —
delka totiz casto sedi a lisi se jediny znak, takze samotna delka nic nedokazuje.

### ⚠️ `@@G2007ADD` orizne KONCOVY zlom radku

**Zmereno 25. 8. 2026 na dvou zapisech:** ulozeny obsah byl **o jeden znak kratsi** nez odeslany —
chybel koncovy `chr(10)`. Uvnitr **0 rozdilu**, obsah byl jinak cely a spravny.

Znalost `doc-system-strategie-most-orez-koncove-newline-oprava` tvrdi, ze koncovy newline je
od 17. 8. 2026 na serveru dorovnavany. **Pro `@@G2007ADD` to podle tohohle mereni neplati**
(u `@@G2007SOUBOR` nemereno — proto se ta druha znalost zamerne neprepisuje).
U markdownu je to bez nasledku a **kontrola s `btrim` z kroku 5 to resi za tebe** — orizne
oba konce na obou stranach, takze na koncovem zlomu uz nezalezi.

## ⚠️ PRIMY `UPDATE` textu NEPREPOCITA VEKTORY

Cileny `UPDATE g2007.znalost SET obsah = replace(...)` je svudny (netreba cist cely dokument),
**ale neobnovi `g2007.znalost_chunk`**. Text v databazi je pak spravny, zatimco **`@@KB`
a semanticke hledani vraci starou pravdu** — tichy rozpor uvnitr jedne znalosti.
Overeno 24. 8. 2026 na dvou znalostech: po `UPDATE` mely chunky starou vetu, po `@@G2007ADD`
uz ne (0 z 8 resp. 0 z 9).

**Pouzij `UPDATE` jen tam, kde na vyhledavani nezalezi. Jinak postup vyse.**

## ⚠️ PAST: zlom radku uprostred vety, ktery vypadá jako mezera

Dva pokusy o cileny `UPDATE` **netrefily** a hlasily 0 zmenenych radku, prestoze veta
v dokumentu prokazatelne byla. Pricina: mezi dvema slovy **nebyla mezera, ale zlom radku**
(markdown zalamuje odstavce) — a ve vypisu z mostu se zlom **zobrazi jako mezera**, takze
nebylo poznat, na cem to padá.

**Jak to odhalit:** vypsat kody znaku.

```sql
SELECT (SELECT string_agg(ascii(substring(obsah from g for 1))::text, ' ')
        FROM generate_series(position('kotva' in obsah) - 80,
                             position('kotva' in obsah) - 1) g)
FROM g2007.znalost WHERE kod = 'doc-...';
```

Kod **10** = zlom radku. **Jak to obejit:** v regularnim vyrazu psat mezi slovy `\s+`,
ne mezeru: `'odes.lac.\s+smy.ka\s+se\s+nespust.'`.

## ⚠️ PAST: diakritika pres most

Ceska diakritika se v dotazu pres most muze prekodovat, takze podminka s "e/i/a s hackem"
netrefi skutecny text — **a stejnou vadou trpi i kontrola**, takze vrati falesne dobrou
zpravu. 24. 8. jsem na to naletel: kontrola hlasila "opraveno" u dokumentu, ktery opraveny
NEBYL.

**Pravidlo: dotazy pres most piš ASCII-only** a misto pismen s diakritikou dej v regularnim
vyrazu `.` (`nab.hne`, `smy.ka`, `nespust.`). Plati i pro kontrolni dotazy — kontrola, ktera
ma stejnou vadu jako zapis, nic neoveri.
Souvisi: `doc-system-strategie-bridge-most-lanes-ops`, gotcha o diakritice.

## Kdy tenhle postup POUZIT a kdy ne

- **Cizi znalost, kterou je potreba vecne opravit** -> tenhle postup. Uz neni duvod zakladat
  novy slug s odkazem jen kvuli strachu z poskozeni.
- **Nove tema** -> porad plati "nova znalost = novy slug".
- **Sloucení dvou znalosti o temze** -> tenhle postup na ten, ktery zustava; z druheho udelat
  kratky rozcestnik (priklad: `doc-system-strategie-postgresql-ddl-za-behu-potrebuje-vlastnictvi-tabulky`).

## Doplneno 9. 9. 2026 — falesna neshoda, ktera stala pul hodiny

Zapisoval jsem opravu do `doc-dochazka-dovolena-tri-cesty-a-schvalovani-planu-11-8-2026`.
Zapis probehl **presne na bajt**, presto **vsechny tri tehdejsi kontroly hlasily neshodu**.

Pricina byla souhra obou pasti najednou:
- dokument **legitimne zacinal zlomem radku** (mel ho od 11. 8., neni od `@@G2007ADD`),
- a `@@G2007ADD` mu **urizl koncovy zlom**.

Overeno vypisem kodu prvnich znaku — `10 35 32 68 111 118 111 108 101 110 97 32`, tedy
zlom, mrizka, mezera, `Dovolena`. Spravnost jsem nakonec dokazal az stazenim obsahu zpet
pres base64 a porovnanim znak po znaku (**0 rozdilu**).

**Ponauceni:** kdyz kontrola hlasi neshodu, ale delka sedi nebo se lisi o jednicku,
**nejdriv podezriraj kontrolu, ne zapis** — a rovnou stahni obsah pres base64.
Kvuli tomuhle pripadu se kontrola v kroku 5 sjednotila na `btrim`.

Zjistil Claude-28 (Jirka Honomichl), schvalila Marti-AI (msg 15258).

