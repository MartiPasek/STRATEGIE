# @@G2007ADD — inline autonomní zápis znalosti do G2007 (STANDARD; docs/Z_ ZAKÁZÁNO)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# @@G2007ADD — inline autonomní zápis znalosti do G2007

**Postaveno:** Claude C27, 21.7.2026, na Martiho princip: *„konstruktivní operace musí jet autonomně, updaty taky; jen mazání se schvaluje."* Priorita = týmová práce a informovanost.
**Status (Marti 22.7.2026): JEDINÁ POVOLENÁ cesta zápisu do G2007. Stará cesta `docs/Z_*.md` + `@@G2007DOC` je ZAKÁZANÁ — NEPOUŽÍVAT a NEZAKLÁDAT žádné `Z_*` soubory v `docs/` ani `docs/GO/`.**

**K čemu:** přispět NEBO opravit znalost v G2007 jedním krokem, inline, **přímým insertem do DB**, **BEZ schvalovacího banneru** a bez souboru/push/deploy. Raw `INSERT`/`UPDATE` do `g2007.znalost` přes bridge spadá pod generický write-guard → banner; `@@G2007ADD` se jako `@@` příkaz chytne PŘED guardem → běží autonomně + reindex.

**Syntaxe:** @@G2007ADD <oblast> <slug> | <nadpis> <obsah na dalších řádcích, markdown>
- `<oblast>` = kód z `g2007.znalost_oblast` (musí existovat), `<slug>` = krátký název. Kód znalosti = `doc-<oblast>-<slug>`.
- Nadpis za `|` je volitelný; když chybí, vezme se první `# ` nadpis z obsahu.
- Nový kód = INSERT, existující kód = UPDATE (upsert). Vždy `stav='aktivni'`, `verze_schvalena=true`, + reindex vektorů (hned dohledatelné přes `g2007 search`).
- Posílá se přes SQL most (`CLAUDE_SQL.sql` → `CLAUDE_GO.txt` db=pg → `CLAUDE_OUT.txt`). Návratovka bývá neutrální (0 řádků) — **ověřuj čtením** (`SELECT ... FROM g2007.znalost WHERE kod=...`, kontrola `chunky>0`), ne návratovkou.

**Kód:** router `diag_sql` dispatch + helper `_g2007_znalost_upsert_inline` (`modules/erp/api/router.py`). Zápis je parametrizovaný (`:c`) → bezpečný vůči libovolnému obsahu (žádné escapování; i „GO"/středník v textu projde).

**Doktrína (drž):**
- Do G2007 přispívej VÝHRADNĚ přes `@@G2007ADD`. NE raw INSERT (zbytečný banner). NE přes `docs/Z_*` / `@@G2007DOC` (ZAKÁZÁNO, mrtvá cesta).
- **NEZAKLÁDAT `docs/Z_*.md` ani `docs/GO/Z_*.md`** — starý handoff je zrušený.
- **Mazání** znalosti zůstává gejtované — destruktivní operace se schvaluje.
- Před editací existující znalosti: **čti-pak-piš** (celý dokument = stávající obsah + tvoje změna) + `git pull` těsně před upsertem (anti-přepis, Marti-AI 20.7.).

