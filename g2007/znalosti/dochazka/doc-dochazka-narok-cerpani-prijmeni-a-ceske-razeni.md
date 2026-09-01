# Nárok a čerpání: Příjmení Jméno + české řazení — a past se zpětnými lomítky

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nárok a čerpání dovolené — Příjmení Jméno a české řazení

**27. 8. 2026, Peťa + C26.** Peťa: *„udělej jméno, aby bylo řazeno podle příjmení
a příjmení na prvním místě."*

## Co je hotové
V `g2007.python` **`att_narok_cerpani`**:
- sloupec `jmeno` se jmenuje **„Příjmení Jméno"**,
- hodnota se bere **přednostně z uživatele** — `last_name || ' ' || first_name`,
- **záložní cesta** pro lidi bez uživatele: otočení `att_employee.full_name` (poslední slovo
  dopředu) přes `reverse`/`split_part`,
- řazení: totéž + **`COLLATE "cs-CZ-x-icu"`**.

## Proč se jméno NEBERE z `att_employee.full_name`
**Není jednotné.** Většina lidí je tam „Jméno Příjmení", ale někteří už „Příjmení Jméno" —
doloženo na **Branislavu Mózerovi**, kterého otočení rozhodilo na „Branislav Mózer", zatímco
ostatní vyšli správně. Proto má přednost `public.users`, kde jsou křestní a příjmení
v samostatných sloupcích.

## Proč COLLATE
Bez něj databáze řadí podle bajtů a nezná Č — **Chramosta vycházel před Čivišem**.
S `cs-CZ-x-icu` je Č hned za C (Čepický, Čiviš, Dalecký…) a Chramosta se posunul mezi H.
Platí i pro Š a Ž. Dostupné jsou i `cs-x-icu`, `cs_CZ`, `cs`.

## ⚠️ PAST — ZPĚTNÁ LOMÍTKA V `g2007.python` (stálo to dvě kola a rozbitý přehled)

Dotazy v `g2007.python` jsou **SQL uvnitř řetězce v Pythonu**, a ten se spouští přes `exec()`.
Zpětné lomítko tedy prochází **dvěma vrstvami** a obě si z něj ukousnou:

| Zápis | Co z toho vyjde | Výsledek |
|---|---|---|
| `regexp_replace(x, '…', '\2 \1')` | Python přečte `\2` jako **osmičkový zápis** = `chr(2)` | V přehledu byly místo jmen **řídicí znaky** |
| `regexp_replace(x, r'…', r'\2 \1')` | `r'…'` **není** Python — je uvnitř SQL řetězce, propadne do SQL | **HTTP 500**, přehled nešel vůbec |
| `'\\2 \\1'` | Python udělá `\2`, SQL dostane správně | Fungovalo by |

**Doporučení: v `g2007.python` se zpětným lomítkům radši úplně vyhnout.** Tady to nakonec
řeší `reverse` + `split_part` + `left` — o pár znaků delší, ale nemá co pokazit. Kdo přesto
regulární výraz potřebuje, ať **zdvojí lomítka** a **ověří výsledek čtením dat**, ne
návratovkou — obě chybné verze se zapsaly jako „OK, 1 řádek".

## Souvislost
Stejné pravidlo (příjmení napřed, řadit podle něj) platí i pro výběr lidí v Opravách
docházky — tam se ale řadí v prohlížeči přes `localeCompare(…,'cs')`, ne v databázi.
Viz `doc-dochazka-sprava-dochazky-zadost-vs-den-a-fajfka`.

