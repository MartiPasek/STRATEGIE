# Jeden zdroj pravdy — docházka a zakázky (rozhodnutí)

> oblast: `dochazka` · úroveň: obor · typ: pravidlo · verze: V1.0 · rozsah: globální (všichni tenanti)

# Jeden zdroj pravdy — docházka a zakázky

Rozhodnutí potvrzené 26. 7. 2026 (Marti + Jirka; ověřeno přímo v datech, Claude + Marti-AI). Stará docházka z DB_EC je **odříznutá**; zdrojem pravdy jsou tabulky ve schématu `tenant`.

## Docházka
- **`tenant.att_entry` = jediný zdroj pravdy** pro docházku (kdy člověk pracuje) i pro opravy. Mobil i opravy píší sem.
- **`tenant.vyroba_work` = rozpad docházky na výrobní joby** — odvozený detail, ne druhá realita.
- **Spřáhnout napevno přes `vyroba_work.att_entry_id`.** Sloupec už existuje, ale k 26.7.2026 je naplněný jen u **1 z 13 548** řádků (0 %). Proto systém padá na hádání na minutu → „dvě reality". Oprava: při vzniku rozpadu vyplnit `att_entry_id`; přehledy („Docházka new") číst **přes tuto vazbu**, ne přes shodu na minutu. Oprava i storno se pak propíší po id.
- **Multitenant:** `tenant_id` je v obou tabulkách. Doplnit **`firma_id`** (chybí v obou) a **sjednotit person-key** — `att_entry` má `employee_id`, `vyroba_work` má `user_id`; docházka musí nést `user_id`.

## Zakázky
- **`DB_EC.TabZakazka` = master** (stará Centrála, SQL Server). **`tenant.oz_zakazky` = naše zrcadlo** (doslovná kopie, klíč `CisloZakazky`), zrcadlit co nejčastěji.
- Docházka i rozpad se **opírají o zrcadlo `oz_zakazky`** přes číslo zakázky (`zakazka_ref` / `project_ref` → `CisloZakazky`). Už to tak funguje.
- Naše vlastní doplňky (co Centrála nezná) → tenká **`zakazka_meta`** klíčovaná číslem zakázky. Kopírování se jí nedotkne.
- **`ec_zakazka_prehled`** má ~525 duplicit sám v sobě → nepoužívat jako zdroj; udělat pohled bez duplicit.
- Testovací modul „Vyhodnocení" (měnil by data zakázek ve STRATEGII) nechat **pozastavený**, dokud není `zakazka_meta` hotová — jinak vznikne rozpor s kopií.

## Princip
Jeden zdroj pravdy **na fakt**, ne „vyber jednu tabulku". Naše doplňky vždy do tenké overlay tabulky klíčované stabilním business klíčem (číslo zakázky / `att_entry.id`). Nikdy needitovat tentýž fakt na dvou místech. Dokud je Centrála master, STRATEGIE do kopírovaných tabulek nepíše.

