# Přejmenování tlačítka nebo obrazovky: šest míst, kde se to musí dohledat (jinak vznikne tichý rozpor)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přejmenoval jsi něco v appce? Projdi těchhle šest míst

**Ověřeno 5. 9. 2026** (Claude-28, zadal Jiří Honomichl, seznam míst doplnila Marti-AI).
Ten den se v mobilu přejmenovalo tlačítko „Makat" → **START** a „Spolupráce" → **Moje docházka**.
Samotná změna trvala minuty; **dohledání všech míst půl hodiny** — a bez něj by systém dál
učil starý název. Je to konkrétní použití **bodu 14 pravidel práce** („změna postupu → oprav ji VŠUDE").

## Šest míst

| # | kde | jak to prohledat |
|---|---|---|
| 1 | **obsah appky a webu** | `g2007.soubor` — pozor, název bývá i v **záložních mapách popisků notifikací** (`20_home_phone_notifs.js`, `25_tasks.js`) a ve **statických stránkách ERP** (`static_db/*.html`) |
| 2 | **nápověda a hlasový průvodce** | tytéž dílky — ⚠️ **mluvený text se čte nahlas**, takže rozpor je slyšet, ne jen vidět |
| 3 | **poznámky v kódu** | komentáře popisující staré chování; nelžou uživateli, ale lžou příští instanci |
| 4 | **znalosti G2007** | `SELECT kod FROM g2007.znalost WHERE stav='aktivni' AND obsah LIKE '%<starý název>%'` |
| 5 | **RAG směrnice** | `SELECT count(*) FROM tenant.kb_smernice t WHERE t::text ILIKE '%<název>%'` |
| 6 | **šablony dokumentů a mailů** | `tenant.hr_template`, `tenant.doc_template`, `fw.template` — stejným způsobem přes `t::text` |

💡 **Trik na hledání, když neznáš názvy sloupců:** `WHERE t::text ILIKE '%…%'` prohledá
celý řádek. Ušetří to hádání jmen sloupců, které je stejně zakázané.

## Jak rozhodnout, co opravit — tři skupiny

Rozdělení schválila Marti-AI 5. 9. 2026:

- **A) Návod nebo specifikace** → oprav **i větu uvnitř**, nejen rámeček. Jinak si instance
  přečte varování a pak se pro jistotu řídí větou pod ním. Sem patří i **proklikávací cesty
  pro testy** — test podle staré cesty spadne.
- **B) Pojmenování** („tlačítko Makat spustí…") → **název jen vyměň**, bez „(dříve Makat)".
  Marti-AI doslova: *„Znalostní báze popisuje aktuální stav, ne historii názvů — na to je git.
  Znalost se starým názvem v závorce by za tři měsíce matla víc než pomáhala."*
- **C) Historický popis** („22. 7. spustil svým prvním Makat…") → **text NEPŘEPISUJ**,
  o minulosti je pravdivý. Stačí rámeček nahoře.

## Na co si dát pozor

- **Znalosti oprav přes `@@G2007ADD`, ne přímým `UPDATE`** — přímý zápis nepřepočítá
  vyhledávání a `@@KB` pak vrací starou pravdu. Postup:
  `doc-system-g2007-editace-znalosti-pres-most-bez-poskozeni`.
- **Stejné slovo nemusí být totéž.** Po přejmenování „Makat" zůstala v appce volba
  **„🏡 Makat z domova"** — to je jiná věc a měnit se nesmí. Čti kontext, nedělej slepou náhradu.
- **Cizí doména** (docházka = Peťa, mzdy = Šárka…): rozhoduje **Jirka Honomichl**, ne ten,
  kdo přejmenovával. 5. 9. rozhodl opravit.

