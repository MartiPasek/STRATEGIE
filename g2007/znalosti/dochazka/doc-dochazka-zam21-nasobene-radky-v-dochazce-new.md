# „Zam 21" a násobené řádky v Docházce new — join přes user_id na víc karet (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# „Zam 21" a násobené řádky v Docházce new

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Příznak
V přehledu **Docházka new** se objevoval člověk **„Zam 21"**, který v datech neexistuje,
a některé úseky byly v přehledu dvakrát až třikrát (Marti Pašek 3×, Kristýna Marešová 2× —
jednou jménem, jednou jako „Zam 21"). Ty dva řádky se lišily i ve sloupci Smlouva
(jeden HPP, druhý prázdný), takže to vypadalo jako dva různí lidé.

## Příčina (ověřeno v kódu i v datech)
Datová sada **`fw.data_set` id 177 (`dochazka.zakazky_vse_list`)** měla ve dvou větvích
UNIONu obyčejný join na jméno:

    LEFT JOIN tenant.att_employee em ON em.tenant_id=2 AND em.user_id=w.user_id

`tenant.att_employee` má ale **na jednoho člověka víc řádků** (doktrína „jeden člověk =
víc docházkových záznamů", CLAUDE.md #24). Kristýna má 2 karty, Marti 3 — join tedy
z jednoho úseku udělal dva až tři řádky přehledu. A protože jedna Kristýnina karta má
**`full_name` NULL**, dopsal jí `COALESCE(em.full_name, 'Zam '||w.cislo_zam)` popisek
**„Zam 21"** (číslo se bere z řádku rozpadu, ne z té karty — ta má číslo 27).

V datech to vidět nebylo — `tenant.vyroba_work` má na ten úsek **jeden** řádek. Násobilo
to až zobrazení. Přesně proto Peťa 3. 9. do pokynů zadala, že kontrola má koukat
i na obrazovky, ne jen do tabulek.

## Oprava (3. 9. 2026)
Oba joiny nahrazeny `LEFT JOIN LATERAL … LIMIT 1` — jedna karta na člověka, přednostně
**pojmenovaná a aktivní**:

    LEFT JOIN LATERAL (
      SELECT em2.* FROM tenant.att_employee em2
       WHERE em2.tenant_id=2 AND em2.user_id=w.user_id
       ORDER BY (em2.full_name IS NOT NULL) DESC, COALESCE(em2.is_active,false) DESC, em2.id
       LIMIT 1) em ON true

Druhá větev (`tenant.att_day_summary`, leden–květen 2026) opravena stejně. Větve nad
`att_entry` problém neměly — ty joinují na `em.id = e.employee_id`, tedy 1:1.

## Ověření
Celá sada spuštěna nad živými daty: **3 566 řádků proti dřívějším 3 595** (29 duplicit
pryč) a **žádný řádek „Zam …"**. Záloha původního SQL: `zaloha_data_set_177_2026-09-03.sql`
ve složce Strategie.

## Pro příště
Gotcha z předání 27. 8. 2026 platí doslova: *„`tenant.att_employee` má víc řádků na
člověka — join kvůli jménu zdvojuje. Používej LATERAL … LIMIT 1."* Kdo bude psát další
datovou sadu nad docházkou, ať na jméno nejoinuje přes `user_id` napřímo.

