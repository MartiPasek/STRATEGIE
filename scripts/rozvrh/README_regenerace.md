# Rozvrh Nerudovka — jak znovu vygenerovat 1. blok (jazyky + TV)

Návod pro budoucí mě / Claude-24. Celý 1. blok jde kdykoli přegenerovat z uložených
skriptů v `scripts/rozvrh/`. Bez živého Bakaláře (zdroj je už vytažený do souborů).

## Soubory (zdroj pravdy v repu)
- `lang_units.txt` — jazykové jednotky `spoj|uk|pred|pnaz|hod|tridy` (AJ/NJ/FJ/ŠJ/RJ).
- `kaj_units.txt` — konverzace AJ `spoj|uk|pred|pnaz|hod|tridy|rocnik` (3./4. ročník).
- `gen_tv_week.json` — TV skupiny (`cells`: d,h1,h2,cy,c,uk,typ,spoj).
- `gen_lang3.py` — generátor (jazyky + KAJ bandy, TV-aware, všechna pravidla).
- `build_kaj.py` — přestaví `kaj_units.txt` z úvazků (mirror).
- `KLARKA_POZADAVKY_2026-06-22.md` — všechna pravidla od Klárky/Marti (závazné).

## Pravidla zabudovaná v gen_lang3.py
- GD/MI jazyky od 1. hodiny; GD max 3 dny jazyků (2 na ateliéry), MI max 4 (1 pro DI).
- Vlková (1.GD, kód 2E) → jazyky/TV na čtvrtek (volný Čt).
- Tesliuk (4.GD, kód 1U) → pátek bez jazyků (učí MD jen pátek 6 h).
- Omezení učitelů: Ždimerová/Vroblová od 2. h, Šedová do 7. h, Kubálková St od 4. h, Layerová Pá do 4. h.
- AJ 4. roč = dvouhodinovka; 1./2./3. CJ ne sousedně; AJ do 7. h, ost. do 8. h.
- TV: 1 tělocvična, cyklus lichý/sudý/každotýdně; pátek ráno bez jen-kluci/dívky.

## Regenerace (POZOR na mount truncation!)
> **Gotcha:** sandbox čte velké soubory přes mount USEKNUTĚ. `gen_lang3.py` proto
> spouštěj přes kopii v `/tmp` (sandbox-lokální), ne přímo z mountu. Datové soubory
> (lang_units/kaj_units/gen_tv_week) jsou malé a čtou se OK.

```bash
cd /sessions/.../mnt/STRATEGIE/scripts/rozvrh
# pokud mount usekává gen_lang3.py: zkopíruj přes Read/Write tool do /tmp/g.py
python3 /tmp/g.py        # vytvoří gen_lang3_out.json (6 variant: res[:6])
```
Výstup: `Var A..F seed N bunky 931 neumisteno 0 pen 0` (931 = 247 jazyk + KAJ rozpad … kontrola dle aktuálních dat).

## Zápis do DB (verze 4–9 = varianty A–F)
```bash
python3 /tmp/bjp.py 0   # dávka A+B -> CLAUDE_SQL.sql  (pak bridge write db=pg, approval banner)
python3 /tmp/bjp.py 1   # C+D
python3 /tmp/bjp.py 2   # E+F
```
`bjp.py` grupuje buňky po (spoj,den,hod), KAJ dostává `cj_uroven=0` (ve viewru „KAJ" bez -čísla).
Dávky jsou <57 KB kvůli mount limitu. TV se NEpřepisuje (zůstává; mění se jen `persist_tv.sql` při změně TV).

## Kontrola výsledku
- V appce: dlaždice „🗓️ Varianty rozvrhu" → **🔍 Kontrola varianty** (živý report: konflikty + pravidla + úvazky).
- Strojově: endpoint `GET /api/v1/erp/app/rozvrh/kontrola?verze=<4..9>`.

## Blokový model (drž)
Každý blok (jazyky / tv / predmet) jde smazat a přegenerovat samostatně:
`DELETE FROM tenant.rozvrh_bunka WHERE verze_id=<id> AND blok='jazyky';` + INSERT.
Ostatní bloky zůstanou. TV/další bloky cílit přes `nazev` varianty, ne přes id (regen jazyků mění id při full delete).
