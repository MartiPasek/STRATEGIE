# Mzdové podmínky: platnost od–do + zaškrtávátko „krátí se docházkou" (26. 8. 2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mzdové podmínky: platnost od–do a krácení docházkou

**Zadala Peťa, nasadil Claude‑26, 26. 8. 2026.** Commit `35c86476`, DDL požadavek mostu #2516, data #2520.

## Proč to vzniklo

Herejtové (EC 525, úklid) se odměna nepočítá napevno — **1 000 Kč za návštěvu, strop 4 000 Kč/měsíc**. Dopočet z docházky měl čísla schovaná v konstantě ve skriptu, takže **Šárka na kartě neviděla vůbec nic** a nepoznala, že ten člověk něco dostává, natož kolik a proč. Peťa to zachytila slovy *„ale to je přece špatně, že tam neuvidíme nic"*.

Řešení podle jejího návrhu: **řádek v Podmínkách zůstane, ale dostane zaškrtávátko.**

## Jak to teď vypadá v Mzdových podmínkách

| Složka | Plán | Skutečnost | Platí od | Platí do | Krátí docházkou |
|---|---|---|---|---|---|
| DPP – Položka do dohody | 4 000 | 4 000 | 1. 1. 2026 | | ☑ 4 |

- **Zaškrtnuté** = částka není pevná. Vyplatí se **částka ÷ počet dnů × kolikrát člověk přišel**, nejvýš celá částka. Herejtová: 4× → 4 000, 2× → 2 000, 5× → pořád 4 000.
- Řádek nese štítek **„dle docházky"** a **do součtu Celkem hrubá se nezapočítává** — kolik se opravdu vyplatí, se pozná až z docházky za konkrétní měsíc.
- **Bez vyplněného počtu dnů to obrazovka neuloží** — dopočet by neměl čím dělit a člověk by dostal 0 Kč.

## Platnost od–do

Nové sloupce `platnost_od` / `platnost_do` v `tenant.wage_component`. **Prázdné = platí vždy**, což je stav všech řádků do 26. 8. 2026, takže se přepnutím nic nerozbilo.

Smysl: **změna částky má založit nový řádek a starému doplnit platnost do**, ne přepsat hodnotu. Pak přegenerování starého měsíce vezme částku, která tehdy platila. Dopočet `mzdy_dpp_navstevy_rows` už platnost respektuje; `mzdy_predzprac_rows` zatím ne — ten dostává jen firmu, ne období.

## Co se změnilo v kódu

| Kde | Co |
|---|---|
| `tenant.wage_component` | +4 sloupce: `platnost_od`, `platnost_do`, `krati_dochazkou`, `plny_pocet_dnu` (s komentáři v DB) |
| `router.py` — čtení finančních podmínek | vrací nová pole do karty |
| `router.py` — `/app/hr/finance/slozka-save` | ukládá je (prázdné datum = `NULL`, ne dnešek) |
| `apps/api/static/finance_podminky.html` | tři nové sloupce, zaškrtávátko, políčko „dnů", kontrola při uložení |
| `g2007.python` — `mzdy_dpp_navstevy_rows` | čte částku i počet dnů **z Podmínek**, ne z konstanty; respektuje platnost |
| `tenant.pojistka` — `dpp-za-navstevu-ma-dochazku` | hlídané lidi bere podle zaškrtávátka, ne ze seznamu v kódu |

## Past, kterou to neřeší

**Docházka z tabletu chodí v dávkách se zpožděním.** Když se měsíc nenahraje, dopočet vrátí nulu. Hlídá to pojistka `dpp-za-navstevu-ma-dochazku` — kontroluje, že každý člověk se zaškrtnutým krácením má za minulý měsíc aspoň jeden záznam.

⚠️ **Obrazovka nebyla vyzkoušená naživo** — ověřená je syntaxe a průchod dotazů, ne kliknutí v prohlížeči. Při prvním použití zkontrolovat, že se uložení propíše.

Souvisí: [[doc-mzdy-dpp-placene-za-navstevu-uklid]] · [[doc-mzdy-zdroj-pravdy-podminky-misto-centraly]]

