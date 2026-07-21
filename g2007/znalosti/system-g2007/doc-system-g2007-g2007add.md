# @@G2007ADD — inline autonomní zápis znalosti do G2007 (bez banneru)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# @@G2007ADD — inline autonomní zápis znalosti do G2007

**Postaveno:** Claude C27, 21.7.2026, na Martiho princip: *„konstruktivní operace musí jet autonomně, updaty taky; jen mazání se schvaluje."* Priorita = týmová práce a informovanost.

**K čemu:** přispět NEBO opravit znalost v G2007 jedním krokem, inline, **BEZ schvalovacího banneru**. Doplňuje `@@G2007DOC` (ten čte z commitnutého `docs/Z_*.md` — potřebuje push+deploy) o cestu bez souboru a bez push. Řeší i to, že raw `INSERT`/`UPDATE` do `g2007.znalost` přes bridge spadá pod generický write-guard → banner; `@@G2007ADD` se jako `@@` příkaz chytne PŘED guardem → běží autonomně.

**Syntaxe:**
@@G2007ADD <oblast> <slug> | <nadpis>
<obsah na dalších řádcích, markdown>

- `<oblast>` = kód z `g2007.znalost_oblast` (musí existovat), `<slug>` = krátký název. Kód znalosti = `doc-<oblast>-<slug>`.
- Nadpis za `|` je volitelný; když chybí, vezme se první `# ` nadpis z obsahu.
- Nový kód = INSERT, existující kód = UPDATE (upsert). Vždy `stav='aktivni'`, `verze_schvalena=true`, + reindex vektorů (hned dohledatelné přes `g2007 search`).

**Kód:** router `diag_sql` dispatch + helper `_g2007_znalost_upsert_inline` (`modules/erp/api/router.py`). Zápis je parametrizovaný (`:c`) → bezpečný vůči libovolnému obsahu (žádné escapování; i „GO"/středník v textu projde).

**Doktrína (drž):** Do G2007 přispívej přes `@@G2007ADD`, NE raw INSERT (zbytečný banner). **Mazání** znalosti zůstává gejtované — destruktivní operace se schvaluje. Před editací existující znalosti: čti-pak-piš + pull těsně před upsertem (anti-přepis, Marti-AI 20.7.).

