# Kontrolní tabulky docházky pro lidi

Claude‑26 / Peťa, 3. 8. 2026

Člověk dostane mailem svůj měsíc. Vlevo vidí zamčená data ze systému, vpravo má
žluté kolonky, do kterých dopíše opravy. Soubor vrátí a my podle něj docházku
srovnáme.

## Jak vyrobit tabulku pro jednoho člověka

**1. Vytáhnout data přes SQL most**

Vezmi `dochazka_kontrola_data.sql`, nahraď tři zástupné texty a vlož výsledek
do `scripts/claude_sql/CLAUDE2_SQL.sql`, pak spusť `CLAUDE2_GO.txt` s `db=pg`.

| Nahradit | Znamená | Příklad |
|---|---|---|
| `{CISLO_ZAM}` | osobní číslo zaměstnance | `24` |
| `{OD}` | první den období | `2026-07-01` |
| `{DO}` | poslední den období | `2026-07-31` |

Výsledek si ulož ze souboru `scripts/claude_sql/CLAUDE2_OUT_FULL.txt`.

**2. Postavit soubor**

```
python3 gen_dochazka_kontrola.py data.tsv Dochazka_07_Kolarova.xlsx
```

## Co tabulka ukazuje

| Barva řádku | Znamená |
|---|---|
| bílá | běžný úsek práce |
| zelená kurzívou | přestávka — do součtu se **nepočítá** |
| **červená celý řádek** | pracovní den, o kterém systém neví vůbec nic |
| **červené jen některé kolonky** | docházka zapsaná **je**, ale chybí u ní zakázka a činnost |
| modrá | víkend |
| oranžová | svátek (název je v součtovém řádku) |

Šedý řádek se součtem je za každý den, dole je součet za celé období.

## Na co si dát pozor

* **Absence musí být ve vstupu.** Kdyby v datech chyběla dovolená nebo lékař,
  tabulka by ten den ukázala jako „chybí zápis" a člověk by zbytečně vypisoval
  časy. (Claude‑26 na to narazil 31. 7. 2026 u Kolářové.)
* **ID záznamu je složené** — `W-` úsek rozpadu na zakázky, `P-`/`A-` docházkový
  záznam nebo absence, `B-` přestávka, `C-` denní souhrn. Samotné číslo není
  jednoznačné, vždy se páruje na obě části.
* **Objeví se i velmi krátké úseky** (klidně minutové), pokud u nich chybí
  zakázka. Jsou v docházce doopravdy, jen bývají zbytkem po opravě.
* List je zamčený **bez hesla** — jde jen o to, aby člověk omylem nepřepsal
  data vlevo.

## Historie

* 31. 7. 2026 — první verze (rozeslána Benešovi a Kolářové).
* 3. 8. 2026 — přepsáno a uloženo natrvalo do projektu (původní skript ležel
  v dočasné složce a ztratil se). Nově: sloupce **pauza od / pauza do**, aby šlo
  přestávku doplnit i tam, kde v systému žádná není, a **červené vyznačení
  chybějící zakázky a činnosti** místo hlášky „chybí zápis" u dnů, kde docházka
  ve skutečnosti existuje. Peťa 3. 8.: *„spíš tam ten řádek dej a červeně
  vyznač, co chybí, a do toho napiš, ať nám to řeknou."*
