# Výběr docházkové karty, když má člověk víc karet (nedeterministický _att_employee)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Výběr docházkové karty, když má člověk víc karet

**Zapsala:** Kristý / Claude-24, 2. 9. 2026. **Souvisí:** doktrína #24 (jeden člověk = víc docházkových/pracovních záznamů), `doc-system-strategie-migrace-app-work-att-employee-pripraveno` (Peťa, 31. 8.).

## Co se stalo

Od 31. 8. 2026 ráno padaly všechny zápisy Kristýny Marešové (user 11) z mobilní apky na **ukončenou OSVČ kartu č. 27** (`tenant.att_employee` id=188, `is_active=false`, bez jména, engagementy OSVČ 2021 až 31. 8. 2025) místo na živou **HPP kartu č. 21** (id=41). Projev v přehledu "Docházka new" = řádky pod číslem 27 a jméno "Zam 27".

Rozsah nálezu (31. 8. až 2. 9.): 10 řádků `att_entry`, 5 `vyroba_work`, 2 `att_day_confirm`, 3 `att_anomaly`, 3 osiřelé `att_day_summary` pod číslem 27.

## Root cause (ověřeno v kódu)

`_att_employee(sess, uid)` v `modules/erp/api/router.py` (r. 23345) hledal kartu dotazem
`SELECT id FROM tenant.att_employee WHERE tenant_id=<bind> AND user_id=<bind>`
— **bez `is_active` a bez `ORDER BY`**. Kdo má víc karet, tomu PostgreSQL vrací libovolnou z nich a pořadí se může kdykoli přehodit (změna plánu / pořadí v haldě). Přesný spouštěč přehození 31. 8. neověřen; vada je ale v samotném dotazu.

Ohrožení nebylo jen Kristý: víc karet má i **Marti** (user 1 → karty id 67 č. 2, id 138 č. 41, id 143 č. 15).

Kontrast: `_plan_employee` (r. 20453) to dělal správně už dřív — `AND is_active=true ORDER BY id LIMIT 1`.

## Oprava

`_att_employee` nově vybírá `ORDER BY is_active DESC NULLS LAST, id LIMIT 1` — tedy **aktivní kartu s nejnižším id**, a když žádná aktivní není, nejnižší id (stejný výsledek jako dřív, jen deterministicky). Záměrně se **nefiltruje** jen na aktivní, aby člověku s pouze neaktivní kartou nevznikla nová karta "U<uid>" (viz incident demo účtu 6.-7. 8. 2026). Deploy commit `273eaa41`, cloud OK.

**Pozor:** `g2007.python` kód `att_employee` (stav `navrzeno`, Peťa 31. 8., 1:1 kopie původní funkce) **má tutéž vadu** a při aktivaci ji vrátí. Nahlášeno Peťovi (notifikace 23058), do jejího skriptu jsem nesahala.

## Úklid dat (request #2666, schválila Kristý)

`att_entry` / `att_day_confirm` / `att_anomaly` employee_id 188 → 41; `vyroba_work` cislo_zam 27 → 21 od 31. 8.; smazány 3 osiřelé `att_day_summary` pod číslem 27. Srpen v té chvíli **nebyl** zamčený (`att_period_lock` max = 2026/7).

## Otevřené (předáno Peťovi a Šárce)

31. 8. je u Kristý kolize: v plánu z Centrály má celodenní dovolenou (2×4 h, `plan_ec`, `ec_druh` 20 a 30), ale reálně pracovala od 08.17 do 13.57. Kristý potvrdila, že **pracovala** a dovolená má pryč. Zrušení patří do **Centrály** (zdroj pravdy pro dovolenou), pak přepočet srpna (`@@DOCHCALC 2026 8`). Ve STRATEGII jsem dovolenou nechala být — sync by ji stejně vrátil.

## Poučení

Kdekoli se hledá docházková karta podle `user_id`, musí být výběr **deterministický a preferovat aktivní kartu**. Doktrína #24 platí i tady: `user_id` není unikátní klíč do `att_employee`.

