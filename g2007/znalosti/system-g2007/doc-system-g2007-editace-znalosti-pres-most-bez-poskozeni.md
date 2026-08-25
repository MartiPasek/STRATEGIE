# Editace cizi znalosti pres most bez poskozeni: base64 tam i zpet, reindex, a dve pasti (24.8.2026)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

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
SELECT md5(ltrim(obsah, chr(10))) = '<md5 toho, co jsi poslal>' AS sedi,
       length(obsah) AS delka,
       (SELECT count(*) FROM g2007.znalost_chunk c WHERE c.znalost_id = z.id) AS chunku
FROM g2007.znalost z WHERE kod = 'doc-...';
```

Jeji zduvodneni doslova: *„krok 2 overuje byte-presnost cteni, ale ne zapisu… pokud by se
pipeline nekdy zmenil (normalizace whitespace, prevod koncu radku), past by se vratila tise."*
Kdo chce smycku uplne zavrenou, precte si po zapisu obsah znovu pres base64.

`ltrim(obsah, chr(10))` tam je proto, ze **`@@G2007ADD` uklada obsah s UVODNIM zlomem radku**
(oddelovaci radek za hlavickou) — viz `doc-system-strategie-most-gotchy-hlidac-dotazu-uvodni-zlom-a-lane3`.

### ⚠️ Ale pozor — `ltrim` sam umi vyrobit FALESNY POPLACH

**Zjisteno naostro 25. 8. 2026** (Claude-28 / Jirka Honomichl, souhlasila Marti-AI msg 13649).
Kontrola z kroku 5 ohlasila neshodu u znalosti, ktera se ulozila **naprosto presne**.
Pricina: **ta znalost sama legitimne ZACINA zlomem radku** (byl v ni od zacatku, ne od
`@@G2007ADD`), takze `ltrim` urizl i ten a otisky nesedly.

**Kontroluj proto OBE varianty a staci, kdyz sedne jedna z nich:**

```sql
SELECT md5(obsah) = '<md5 toho, co jsi poslal>'                    AS sedi_presne,
       md5(ltrim(obsah, chr(10))) = '<md5 toho, co jsi poslal>'    AS sedi_po_orezu,
       length(obsah) AS delka
FROM g2007.znalost WHERE kod = 'doc-...';
```

**Kdyz nesedne ani jedna, teprve pak** stahni obsah zpet pres base64 a porovnej **znak po znaku** —
delka totiz casto sedi a lisi se jediny znak, takze samotna delka nic nedokazuje.

### ⚠️ `@@G2007ADD` orizne KONCOVY zlom radku

**Zmereno 25. 8. 2026 na dvou zapisech:** ulozeny obsah byl **o jeden znak kratsi** nez odeslany —
chybel koncovy `chr(10)`. Uvnitr **0 rozdilu**, obsah byl jinak cely a spravny.

Znalost `doc-system-strategie-most-orez-koncove-newline-oprava` tvrdi, ze koncovy newline je
od 17. 8. 2026 na serveru dorovnavany. **Pro `@@G2007ADD` to podle tohohle mereni neplati**
(u `@@G2007SOUBOR` nemereno — proto se ta druha znalost zamerne neprepisuje).
U markdownu je to bez nasledku, ale **pri kontrole otisku s tim pocitej**: porovnavej proti
`md5(<tvuj obsah>.rstrip(chr(10)))`, nebo pouzij obe varianty vyse.

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

