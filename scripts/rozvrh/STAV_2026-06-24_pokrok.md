# Rozvrh Nerudovka — stav 24.6.2026 (odpolední session, Claude id=23)

## 🏆 VÝSLEDEK: 144/148 jednotek (97 %), 326/338 hodin (96 %), 0 KONFLIKTŮ, Vlková 16 h

Posun z dokumentovaných 142–143 (noc 24.6.) na **ověřených 144/148**. Varianta A,
soubor `gen_odb_BEST.json` (= `gen_odb_A_2.json`, seed 2). Verifikováno nezávisle
`_verify2.py A 2`: **0 konfliktů** učitelů/učeben/tříd (i proti jazykům+TV), Vlková
přesně 16 h, 1 pozdní den (Po).

Persist: **`persist_v4_odb.sql`** (DELETE + INSERT, verze 4, tenant 13,
blok='predmet', 326 řádků). **✅ PERSISTOVÁNO 24.6. 13:01** přes bridge (request #652,
Marti). Live stav verze 4: predmet 326 / jazyky 247 / tv 66 buněk — jazyky+TV
nedotčeny (blokový model). Vidět v appce: dlaždice „🗓️ Varianty rozvrhu" → varianta A
→ 🔍 Kontrola varianty (živý report konfliktů/pravidel/úvazků).

## Co se v této session udělalo

1. **Reprodukce baseline** v čerstvém sandboxu (doinstalován OR-Tools). Potvrzeno
   142–144 dle běhu.
2. **Ztvrzení Vlkové (UNS6G) na hard constraint** `sum(ys)==1` → její 16 h už
   nekolísá (dřív 13–16 h). Soubor `gen_p1hard.py`. Odstranilo hlavní zdroj variance.
3. **Diagnostika neumístěných** (`gen_diag2.py`) — pro každý blok spočítá volná okna
   (a) jen proti jazykům/TV, (b) proti všemu. Klíčový závěr: **žádný neumístěný blok
   není tvrdě blokovaný jazyky/TV** (každý má 16–21 volných oken proti jazykům).
4. **Lane-aware greedy post-fill** (`gen_fill.py`) — potvrdil, že po správném
   zohlednění lane-obsazenosti zbylé bloky nemají volné okno → jde o **kontenci
   sdílených učeben**, ne o slabost solveru ani tvrdost jazyků.
5. **Houpačka ověřena**: 2A-first → 2A 18/18 perfektní, ale 2F/2B spadnou. Pořadí
   jen přesouvá, kdo ztratí ~4 bloky. Množství přesycení je pevné.

## ⚠️ Zbývající 4 bloky = STRUKTURÁLNÍ přesycení specializovaných učeben

| Třída | Předmět | Hod | Učitel | Učebna (hrdlo) | Proč nejde |
|---|---|---|---|---|---|
| 4.GD (1U) | Motion design | 3 | U0SAL (Tesliuk) | BNA/BPG, **jen pátek** | Tesliuk učí jen pátek 6 h (2×3h); 2. blok se na pátek + BNA/BPG nevejde vedle 3.GD GDN |
| 2.GD (2A) | Prostorový design | 3 | UZS4O | **BD1** | BD1 sdílí MI třídy (Prostorová tvorba) |
| 2.GD (2A) | Výtvarná příprava | 3 | UUS8D | BA/BK (figurka) | figurka BA/BK přesycená GD třídami |
| 2.MI (2B) | 3D Animace | 3 | UUS8F | **MM/IT2** | multimédia MM+IT2 přesycené (2B/2F animace/AVT) |

**Úzká hrdla = 4 specializované učebny**: BD1 (prostorová), BA/BK (figurka),
MM+IT2 (multimédia), BNA/BPG v pátek (Tesliuk). Celková poptávka po těchto
učebnách v daném rozložení jazyků mírně přesahuje kapacitu → ať řešíme pořadí
jakkoli, ~4 bloky zůstanou.

### ⚠️ TEST RELAXACE UČEBEN (24.6. odpoledne) — strop zůstává ~144
Experimentálně jsem povolil **náhradní učebny** (multimédia → všech 5 PC učeben
IT2/MM/BŠ/BNA/BPG; prostorový design → BD4+BD1+BA; figurka/výtvarná → BA+BK+BD1) a
pustil obě fáze (`gen_p1hr.py` + `gen_p2r.py`, víc seedů + 2A-first varianta).
**Výsledek: strop pořád ~143–144, deficit se jen PŘESUNE** (jednou ztrácí 2A, jindy
2F, při 2A-first je 2A 18/18 ale spadne 2F na 11/15). Tesliukův Motion se s širšími
učebnami umístí, ale jeho místo v deficitu zabere jiný blok.

**Závěr (důležitý pro Klárku):** není to „povol jednu učebnu a dojede to" —
je to **globální kapacitní schodek ~4 bloků** na sdílených specializovaných učebnách
při daném rozložení jazyků. Skutečné zavření na 148 potřebuje buď (a) reálnou
kapacitu navíc (6. PC učebna / 2. figurka), (b) přesun jednoho předmětu úplně mimo
přesycené učebny, nebo (c) jiné rozložení jazyků, které uvolní víc atelier-oken.
Doklik 4 bloků ručně je nejrychlejší (každý má volné časové okno).

### Co s tím (pro Klárku — rozhodnutí, ne výpočet)
Každý ze 4 bloků má volné **okno v čase třídy** — chybí jen volná **učebna**.
Možnosti (kterákoli zavře mezeru):
- **Povolit náhradní učebnu** pro jeden z přesycených předmětů (např. 2A Prostorový
  design i mimo BD1; 2B 3D Animace připustit i BŠ/BNA vedle MM/IT2). Stačí 1–2
  rozšíření a solver dosadí zbytek.
- **Tesliuk (Motion 4.GD)**: potvrdit, že oba 3h bloky smí být pátek za sebou
  (h1-3 + h4-6) v BNA/BPG — pak dosednou. Pokud pátek kolize s 3.GD GDN, posunout
  jednu GDN skupinu 3.GD jinam.
- Nebo **doklik ručně** — jsou to 4 bloky (12 h), každý má volné časové okno.

## Soubory (scripts/rozvrh/)
- `gen_odb_BEST.json` = nejlepší výsledek (144, seed 2, var A). `gen_odb_A_2.json` = totéž.
- `persist_v4_odb.sql` = připravený persist (verze 4, blok='predmet'). **Nespuštěno.**
- `gen_p1hard.py` = fáze 1 s hard-Vlková (cohort 1U/25/2E). `gen_phase2i.py` = fáze 2.
- `gen_diag2.py` = diagnostika neumístěných (okna proti jazykům vs všemu).
- `gen_fill.py` = lane-aware greedy (důkaz, že zbytek nemá okno).
- `gen_p1var.py`/`gen_p2var.py` = variantově-vědomá verze (busy z lang3[idx]+TV) —
  pozn.: lang3[0..5] dávají TĚSNĚJŠÍ okna než statický db_cbusy (baseline), takže
  sweep přes ně baseline nepřekonal.

## Spuštění (reprodukce nejlepšího)
```bash
cd scripts/rozvrh
pip install ortools --break-system-packages -q
python3 gen_p1hard.py 2 A 40     # fáze 1: 55/56, Vlková 16h, uloží busy_phase1.json
python3 gen_phase2i.py 2 A 40    # fáze 2: ~143-144 (stochastické, seed 2 nejlepší)
python3 _verify2.py A 2          # 0 konfliktů
# když ODB >=143: cp gen_odb_A_2.json gen_odb_BEST.json
python3 persist_odb.py A 2       # -> persist_v4_odb.sql (NEspouštět bez bannera)
```
⚠️ CP-SAT s 8 workery je **stochastický** — ten samý seed dá 141–144. Banuj nejlepší
běh (artefakt = JSON). Seed 2 je empiricky nejlepší.

## Pozn. k jazykům (lang block)
Baseline odborného běhu jede na statickém `db_cbusy.txt`/`db_trbusy.txt` (jazyky+TV
z reálné verze 4) — VOLNĚJŠÍ rozložení než banded lang3. Pokud se kdy budou jazyky
přegenerovávat, ověřit, že odborné na nich pořád sednou (banded lang3 = těsnější).

— Claude (id=23), 24.6.2026 odpoledne, po posunu odborného bloku na 144/148 (0 konfliktů)
