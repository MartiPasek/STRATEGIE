# Správa docházky i Docházka new ukazují PŘÍJMENÍ a pak jméno (Peťa 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Zadala Peťa 7. 9. 2026:** *„můžeš mi přehled Správa docházky udělat taky podle příjmení — první příjmení a pak jméno."*

Ve sloupci `JmenoPrijmeni` přehledu **Správa docházky** (`fw.data_set` id 178,
`dochazka.zakazky_budoucnost_list`) se místo „Josef Artim" ukazuje **„Artim Josef"**.
Přehled se podle toho i řadí (`ORDER BY odd DESC, <příjmení jméno>`).

## Jak se to skládá

`tenant.att_employee.full_name` je jedno pole ve tvaru „Jméno Příjmení", takže se
**nepřehazují slova naslepo** — jméno a příjmení se berou z `public.users`
(`last_name`, `first_name`) a **zbytek `full_name` se zachová a přilepí na konec**:

| `att_employee.full_name` | ukáže se |
|---|---|
| Josef Artim | Artim Josef |
| Kristýna Marešová 2 | **Marešová Kristýna 2** |
| Petra Šafránková ml | **Šafránková Petra ml** |
| Brigádník Saxana (bez vazby na uživatele) | Brigádník Saxana (beze změny) |

Přípony jako „2" a „ml" jsou tam schválně — rozlišují **víc karet téhož člověka**
(doktrína #24). Kdyby se braly rovnou z `users`, obě Marešové by vypadaly stejně
a Peťa by nepoznala, na kterou kartu se dívá.

Když člověk vazbu na uživatele nemá, spadne se zpátky na `full_name` — nikdy nevznikne
prázdné jméno.

## Kde to je

`fw.data_set` id 178, výstupní `SELECT` (sloupec `"JmenoPrijmeni"`) a závěrečný `ORDER BY`.
Poddotaz na `tenant.att_employee` + `public.users` podle `dedup.employee_id`; vnitřní CTE
zůstala nedotčená.

Záloha předchozí podoby: `zaloha_data_set_178_2026-09-07.sql` v kořeni projektu.
Ověřeno spuštěním přehledu naostro před i po zápisu, md5 sedí na bajt.

## Docházka new — dodělána týž den

Peťa 7. 9. 2026 vzápětí: *„ano i tam."* Takže **stejná úprava je i v Docházce new**
(`fw.data_set` id 177, `dochazka.zakazky_vse_list`), sloupec `"JmenoPrijmeni"`.
Záloha: `zaloha_data_set_177_2026-09-07.sql`.

Rozdíly proti 178:
- poddotaz se páruje na `spolu.emp_id` (ne `dedup.employee_id`),
- fallback je `jm` (nese `'Zam '||cislo_zam` pro případ, že karta chybí) — **nechat**,
  jinak by se vrátily prázdné buňky místo „Zam …",
- **interní sloupec `"_jm"` zůstal beze změny** (používá ho stránka, ne uživatel),
- **řazení se nemění** — Docházka new řadí po dnech (`ORDER BY d DESC, od_ts DESC`),
  což je správně; příjmení řadí jen Správa docházky.

## Gotcha při práci s tímhle přehledem přes most

SQL přehledu obsahuje **`to_char(…, 'DD.MM.YYYY HH24:MI')` na čtyřech místech** a `:MI`
bere most jako bind parametr. Při **čtení a testování** dotaz spadne — nahraď
`'DD.MM.YYYY HH24:MI'` za `'DD.MM.YYYY HH24' || chr(58) || 'MI'`. Při **zápisu** to
problém není, pokud se posílá přes base64 (`doc-system-strategie-most-pyrun-a-base64-zapis`).

