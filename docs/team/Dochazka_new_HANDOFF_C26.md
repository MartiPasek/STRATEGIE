# Docházka new — předávací zápis (C26 / Peťa, Cowork)

> Zápis pro pokračování v NOVÉ konverzaci. Peťa staví „Docházka new" (nahrazuje
> Dušanovu „Docházka po zakázkách" / legacy EC_Dochazka). Konverzace byla dlouhá,
> přesouváme se do čerstvé. Přečti si tohle jako první, pak WORK_LOCK.txt a G2007.

## Co to je
- Přehled **`/dochazka-po-zakazkach`** (node + core přejmenované na **„Docházka new"**).
- Cíl: jeden přehled docházky **všech lidí** (výroba přes zakázky + kancelář jako
  „Rezie" + absence), z Centrály i z aplikace. Změny se musí propisovat tam, kde se
  data používají (mzdy, výkazy, audit).
- Časové rozdělení dat: **led–kvě z Centrály** (att_day_summary, kind C),
  **červen „s výhradou"** (přechod), **červenec+ z aplikace**.

## Klíčové soubory
- **`apps/api/static/dochazka-po-zakazkach.html`** — hlavní stránka. COLS pole,
  chunked render (paintRow/appendChunk, CHUNK=600), editační formulář (openEdit
  režimy W/FIX/RO, openNew, saveEdit), datumový filtr (openDateFilter), kontextové
  menu (openCtx/ctxAction), sumace (sumSelected), našeptávač zakázek (loadZak/ZAK/
  datalist#zaklist).
- **`modules/erp/api/dochazka_zak_tab.py`** — endpointy: `/data`, `/cinnosti`,
  `/zakazky` (píchatelné z tenant.zakazka, ORDER BY REZIE first), `/save`
  (UPDATE vyroba_work), `/save-new` (INSERT vyroba_work), `/save-doch-meta`
  (poznámka/ved_schvaleno na aktivní řádek, supersede-aware), `/widths`.
- **`docs/team/Peta26_pokyny.md`** — pravidla (datumový filtr všude kde je datum;
  výběr řádků jen Ctrl/Shift, prostý klik odznačí; ID filtr = přesná shoda).
- Data_set **`dochazka.zakazky_vse_list`** (v6): 4 UNION větve (vyroba_work W;
  att_entry P; att_entry absence A; att_day_summary C led–kvě), omezeno na
  poslední 2 měsíce; endpoint tuto mez sundá pro obdobi='all'.

## HOTOVO (nasazeno)
- Dvojklik → editační formulář ve stylu Centrály (bez „Nový záznam" checkboxu,
  bez Blbost/Rezie).
- Docházka všech lidí po měsících; kancelář jako „Rezie".
- Editace: výroba (vyroba_work) přímo; app-docházka (kind P) přes engine
  „Opravy docházky" (`/api/v1/erp/app/attendance/fix/entry`) → propisuje do
  mezd/výkazů/auditu; vyžaduje důvod.
- Datumový filtr OD/DO (i v pokladnách + přijatých fakturách).
- Výběr řádků jen Ctrl/Shift; ID filtr přesná shoda.
- Kontextové menu (pravý klik): Nový, Smazat, Excel, Sumace označených, Nastav
  parametry hromadné, Tisk — **funguje zatím jen Nový + Sumace**; ostatní hlásí
  „připravujeme".
- Formulář: ID + Čas zamčené (oranžové, needitovatelné); Zaměstnanec + Vedoucí
  poznámka editovatelné (propíší se do sloupců); Vedoucí schváleno checkbox
  editovatelný (zaškrtne správce při editaci); Požadavek úpravy zatím prázdný.
- DB sloupce pro poznámku/schváleno přidány (att_entry.vedouci_poznamka,
  ved_schvaleno).
- **Zakázka = našeptávač** (datalist#zaklist, endpoint `/zakazky`). Na přání Pety
  nabízí **jen číslo** (název pryč) — poslední edit, deploy commit viz níže.

## ⚠️ HLAVNÍ VĚC K DOŘEŠENÍ PŘÍŠTĚ
**„Soudeček bez asociovaného core přehledu" naskočí ~5× po sobě, než se stránka
načte.** Peťa: „to se nesmí stávat." Je to timing/cache race — node „Docházka new"
nemá v DB asociovaný core a render závisí na JS hooku v `page_render.js`
(kolem ř. 991, klíč 'dochazka.centrala'), který občas doběhne dřív než je vše
ready → fallback → po reloadu OK. **Robustní fix = přiřadit node reálný core**
místo spoléhání na fragilní JS hook, nebo hook zpevnit (retry/ready-guard).
Prozkoumat: `fw.menu_node` + `fw.core` vazba pro tento node; proč není core;
zda hook běží před hydratací.

## ZAKÁZKA — DODĚLAT PICKER JAKO V CENTRÁLE
Teď je Zakázka jen inline **datalist** (píšeš číslo → nabídne). Peťa chce navíc,
aby po kliknutí na čtvereček vyskočilo **okno se seznamem a filtrem nahoře**
(přesně jako Centrála — screenshot 23.7.: titulek „104:0 - Zakázky", sloupec
`CisloZakazky`, řádek filtru nad ním, Rezie první, pak PR4015…PR3994, OK/Storno).
→ Postavit modal picker: seznam z endpointu `/zakazky` + filtrovací input nahoře
(filtruje podle čísla), klik na řádek vybere číslo do `d_zak`, OK/Storno.
Datalist může zůstat jako rychlé psaní; čtvereček otevře tenhle modal.

## DALŠÍ NEDODĚLANÉ AKCE MENU (postupně, Peťa: „delejme to postupně")
- **Smazat** — smaže označené (soft/hard? koordinovat).
- **Excel** — export + Ctrl+A (vybrat vše) + Ctrl+C (kopírovat).
- **Nastav parametry hromadné** — okno, zapsané změny se aplikují na všechny
  označené.
- **Tisk** — odloženo.

## Provozní poznámky
- Deploy: `CLAUDE_DEPLOY.txt` (1. řádek commit msg, další řádky cesty) +
  `CLAUDE_DEPLOY_GO.txt`. Pull přes `CLAUDE_PULL_GO.txt`.
- SQL most: `scripts/claude_sql/CLAUDE_SQL.sql` (VŽDY Write tool) + `CLAUDE_GO.txt`
  (`db=pg`/`db=mssql`) → `CLAUDE_OUT.txt`. Write → schvalovací banner u Pety.
- Cloud NEČTE Centrálu živě (EUROSOFT_SQL_PASSWORD není v env) → pro led–kvě
  používáme PG zrcadlo `att_day_summary`, ne živé EC čtení.
- Ověřování v prohlížeči přes Chrome MCP; tab stav cachuje localStorage
  `erp.tabs.state.v1` (po přejmenování zavřít × a otevřít znovu ze stromu).
- Instance = C26 (Peťa). Lane dle multi-lane bridge (viz CLAUDE.md).
