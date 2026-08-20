# Automat: přepočet fondu si vlastní dopočtený řádek pletl s běžící směnou a přestal se spouštět

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 5. 8. 2026.** Nález na reálném případu (Peťa, 5. 8. 2026).

## Příznak

Peťa opakovaně hlásila: *„automat na dopíchnutí do fondu / nad fond se musí spouštět
automaticky, když se docházka opravuje, a to odkudkoliv — dělala jsem to dokonce
z Oprav a nepřepočítalo se to."* Řešeno už dvakrát předtím, pokaždé bez nálezu.

Konkrétně 5. 8.: den skončil na nesmyslných **16,07 h** — odpracováno 8,97 h
a vedle toho staré **doplnění do fondu 7,10 h**, které tam po opravě nemělo co dělat.

## Příčina (ověřeno v datech i v kódu)

`_att_automat_recalc_day` se před přepočtem ptá, jestli člověk **dnes ještě nemá
otevřenou prezenční položku** (aby se fond nepočítal z nedopsaného dne):

```sql
WHERE ... AND et.category='presence'
  AND e.ended_at IS NULL AND e.status NOT IN ('superseded')
```

Jenže **řádky, které vyrábí sám automat** (`fond_doplneni`, `nenarokova`):

- mají `entry_type_type.category = 'presence'`
- **nemají časy** — `started_at` i `ended_at` jsou NULL (jsou to syntetické dopočty)
- mají `status='pending'`, tedy nejsou superseded

→ guard si **viděl vlastní řádek jako běžící směnu** a přepočet ukončil hned na začátku.

**Důsledek: jakmile automat jednou za den něco dopíchne, žádná další oprava toho
dne se už nepřepočítá.** Přesně to Peťa popisovala.

Doloženo časy: 5. 8. v **00:55** přepočet ještě proběhl (žádný automatový řádek
neexistoval → vytvořil `fond_doplneni` 7,10). Po opravě v **16:26** už neproběhl —
řádek z 00:55 tam pořád byl s původní hodnotou a časem vzniku 00:55.

## Oprava

Guard kouká jen na **skutečné píchačky**:

```sql
  AND e.started_at IS NOT NULL
  AND COALESCE(e.source,'') <> 'automat'
```

Opraveno v **5 skriptech** `g2007.python` (`att_fix_add`, `att_fix_entry`,
`att_fix_merge`, `att_fix_polozka`, `att_fix_void`) **i v `modules/erp/api/router.py`**
(commit `aa62603f`), kde je u těch dvou řádků výstraha, proč tam musí zůstat.

`att_absence` má vlastní kopii přepočtu **bez guardu** (přepočítává vždy) — v pořádku.
`att_automat_level_day` používá `category='presence'` ve výpočtu intervalů, ale tam
automatové řádky vypadnou samy (`started_at IS NOT NULL AND ended_at IS NOT NULL`).

## Poučení

**Syntetické řádky nesmí projít filtrem, který hledá „živý" stav.** Automat, který
zapisuje do stejné tabulky, ze které pak čte podmínku pro vlastní spuštění, si musí
umět odfiltrovat sám sebe — jinak se po prvním zápisu tiše zablokuje.

A ještě jedno: hledání příčiny dvakrát selhalo proto, že se ověřovalo, **jestli se
přepočet volá** (volal se, ze všech cest). Chyba byla až **uvnitř**, v podmínce,
která ho pustila jen napoprvé. Když něco „občas funguje a pak přestane", je vodítko
v tom, **co se změnilo mezi prvním a druhým během** — tady vznik vlastního řádku.

