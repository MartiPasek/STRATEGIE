# Docházka — model PLÁN × KOREKCE × REALITA

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Docházka — model PLÁN × KOREKCE × REALITA

*Design doc · 13. 6. 2026 · Claude (id 23) + Marti + konzultace Marti-AI*
*Status: závěry Marti-AI ZÁVAZNÉ. Scope fáze A: PLÁN. Zbytek parkovaný.*

---

## Princip

Tři tabulky = tři různé **pravdy o světě**, záměrně nemíchané do jednoho stavu:

| Vrstva | Tabulka | Smysl |
|---|---|---|
| **PLÁN** | `att_plan_day` (nová) | Statický, zhmotněný dopředu. „Kdo má kdy dorazit a na kolik h." |
| **KOREKCE** | `att_absence_request` (máme) | Žádost o změnu *proti plánu* (dovolená/HO/lékař/zkrácení). Lifecycle, diff. |
| **REALITA** | `att_entry` (máme) | Jen skutečnost — píchnutí + import Heliosu. Bez kopírování absencí. |

Pohledy se skládají za běhu: **plán × schválené korekce × realita.**

## Vstupy plánu (pyramida, většina už stojí)

1. **Obecný kalendář** `att_calendar_day` (svátky, pracovní dny) + `att_calendar_month` (fond). ✅
2. **Firemní výjimky** `att_calendar_exception` (nová) — **hodinové, ne bit** (Marti):
   24. 12. = 4 h, 27.–31. 12. = 0 h. Per tenant (volitelně skupina), s důvodem,
   plánovatelné dopředu.
3. **Vzorec týdne + úvazek** `work_schedule` (per-den works/hours/end_time) +
   `staff_cond` (`uvazek_h_tyden`, resolver systém→skupina→jednotlivec). ✅

## Závazné závěry Marti-AI (13. 6.)

**Q1 — Regenerace vs korekce.** Oddělené tabulky → regenerace se korekcí nedotkne.
Podmínka: **`frozen_until` explicitní** (ne implicitní „jen budoucnost") — jinak
někdo přegeneruje uzavřené čtvrtletí. Okno: **rolující 3 měsíce dopředu** (ne pevné
období — hrana na konci roku). Vyber JEDEN přístup generace (scheduled vs lazy),
nemíchej.

**Q2 — Konflikt plán × realita.** Odpracováno = **realita** (`att_entry`, mzdy odsud).
Placená absence = **jen ze schválené korekce**, ne z plánu. Plán = očekávání, ne
nárok. Přesčas (realita > plán) = **byznys pravidlo → konfigurace, ne pevné chování.**

**Q3 — Částečné korekce.** Legitimní, neporušuje uniformitu (korekce = vždy „změna
proti plánu s typem a cílovým stavem"). `target_hours` nullable: NULL = celý den
pryč, číslo = zkráceno na X h. + `correction_type` + rozsah dní.

**Q4 — Materializace.** Smíš ji odpojit (3 čisté vrstvy → join na měsíc/člověka je
levný), ale **vědomě, ne tiše**: pro hromadný reporting připrav **read-only
materialized view** per osoba/měsíc (ne kopii do att_entry). Závisí na rychlosti
reportingu (viz parkováno).

**Q5 — att_balance.** **Počítat za běhu**, nezhmotňovat (zhmotnění = druhý stav
k synchronizaci = bugy). `nárok = conditions.dovolena_dni (prorated dle nástupu)`,
`čerpáno = SUM(approved korekce typu dovolená)`, `zůstatek = nárok − čerpáno`.
Loňská dovolená = samostatný řádek nároku s `valid_until`. Výstup → `frozen_until`.

**Q6 — Audit + viditelnost.** Korekce **append-only** (kdo/kdy/z čeho/do čeho —
pracovněprávní hygiena). Plán: append-only pro **změny vzorce/výjimek** (audit
vstupů generátoru), ale řádky `att_plan_day` přepisovat smíš (plán = výsledek
výpočtu, ne rozhodnutí). Viditelnost: každý svůj plán; vedoucí tým přes
`resolve_role`; rodiče vše. **Horizontální viditelnost mezi kolegy defaultně
zavřená** — „vidíme všichni všechny" jen explicitní nastavení.

## Parkováno (byznys pravidla — Marti 13. 6.: „neřeš teď, potřebujeme plán")

- **Přesčasy** — per-entry vs schvalovaná korekce. Až bude „normální systém".
- **Reporting rychlost** — real-time vs daily batch (rozhoduje o materialized view).
- **Převod dovolené mezi roky** — zatím brzo.

Dokud tyhle tři nejsou rozhodnuté, nekódovat je natvrdo — nechat místo (konfigurace).

## Scope — Fáze A (teď): PLÁN

1. `att_calendar_exception` — hodinové firemní výjimky (DDL přes banner + GRANT).
2. `att_plan_day` — statická plánová tabulka per osoba/den + `frozen_until` marker
   (na tenant/period). DDL přes banner + GRANT.
3. **Generátor plánu** — kalendář × výjimky × work_schedule/úvazek resolver →
   `att_plan_day`, rolující 3 měsíce, přepíše jen ne-frozen budoucí dny.
4. **„Můj plán na týdny dopředu"** — obrazovka, každý vidí svůj plán vč. výjimek.
5. **Správa výjimek** — HR/rodiče zakládají firemní výjimky + spustí generátor.

## Fáze B (potom): KOREKCE proti plánu

- `att_absence_request` jako korekce: `target_hours` + `correction_type` + diff vůči
  plánu v UI, zrušení/úprava, append-only audit změn stavu.
- Odpojit materializaci absencí do `att_entry` (vědomě, + případně MV pro reporting).
- `att_balance` za běhu (nárok − čerpáno).
- Sjednotit rychlé bubliny v docházce → předvyplní korekci (konec „dvou světů").


