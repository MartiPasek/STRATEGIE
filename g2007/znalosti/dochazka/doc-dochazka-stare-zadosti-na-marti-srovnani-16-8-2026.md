# Stare nerozhodnute zadosti o absenci na Martim - srovnani 16.8.2026 + kde se bere schvalovatel

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se stalo

Pri praci na mobilni obrazovce Absence (viz [[doc-dochazka-mobil-absence-obrazovka-vedouciho]]) se ukazalo, ze na Martim (user 1) visi **8 nerozhodnutych zadosti** o dovolenou z 23. 6. - 18. 7. 2026. Jirka se ptal, proc, kdyz uz se schvalovani delegovalo.

**Odpoved: delegovani funguje, jen nepusobi zpetne.** Schvalovaci skupiny (`tenant.att_approver_group` + `att_approver`) vznikly **21. 7. 2026**. Zadosti podane PRED tim si nesou `manager_user_id` z doby vzniku a zpetne se neprepocitavaji. Srpnove zadosti uz chodi spravne na delegovane schvalovatele.

## Kde se bere schvalovatel (aby to pristi clovek nehledal)

`tenant.resolve_approvers(tenant, employee, datum)`:
1. Podle **pozice zadatele v organizacni strukture** (`tenant.org_post_assign` → `att_approver_group_member`, podporuje i podstrom) najde schvalovaci skupinu.
2. Kdyz nic nesedi → **zalozni skupina** (`je_fallback`).
3. Ze skupiny vezme lidi z `tenant.att_approver`: hlavni vzdy, **zastupce jen kdyz je hlavni sam na dovolene/u lekare/OCR** (kontroluje se proti schvalenym zadostem na to datum).
4. **Zadatel je ze seznamu vzdy vylouceny** (`a.employee_id <> p_emp`).

**PAST: `att_approver.group_id` NEODKAZUJE na `tenant.staff_group`** (pracovni skupiny), ale na `tenant.att_approver_group` (schvalovaci skupiny). Kdo si to splete pri joinu, dostane spravna jmena lidi, ale **uplne spatne nazvy skupin**. Stalo se to 16. 8. 2026.

Stav k 16. 8. 2026: **vyroba** = Dusan Havlat (zastupce Marek Honal) · **nakupci** = Petra Safrankova · **projekty** = Jiri Veverka · **ostatni (zalozni)** = Sarka Novotna.

## Dusledek, ktery je treba doresit (predano lidem)

Sarka Novotna je **jediny** schvalovatel zalozni skupiny a sama sobe schvalovat nesmi → resolver pro ni vraci **prazdno** a jeji zadosti padaji na Martiho (posledni zachrana v `att_absence_request`). Podle dohody HR z 5.-6. 8. 2026 ([[doc-dochazka-odpovednost-schvalovani-volna]]) si maji **Sarka Novotna a Michaela Hladikova schvalovat volno navzajem** - v systemu to ale nastavene neni, v tom zapisu je to vedene jako nedodelek.

**Jirka 16. 8. 2026 toto rozhodnuti vedome delegoval** na rodice + HR (e-mail Marti / Kristy / Sarka / Michaela, odeslano 19:40). Pro nas je tim uzavrene - nenastavovat svevolne.

## Co se 16. 8. 2026 udelalo se starymi zadostmi (rozhodl Jirka)

Pravidlo: **zapsane v dochazce → oznacit za rozhodnute a dochazky se NEDOTYKAT; bez zaznamu → smazat.**

| Zadost | Clovek | Termin | Dnu v dochazce | Vysledek |
|---|---|---|---|---|
| 16 | Michal Sik | 13.-17. 7. | 5 | approved (dodatecne srovnano) |
| 20 | Andrea Bernardova | 20.-24. 7. | 5 | approved (dodatecne srovnano) |
| 21 | Andrea Bernardova | 20.-24. 7. | 0 (zneplatnene) | **cancelled - duplicita c. 20** |
| 19 | Michaela Hladikova | 29. 7. - 3. 8. | 4 | approved (dodatecne srovnano) |
| 22 | Iva Hruzova | 27. 7. - 7. 8. | 10 | approved (dodatecne srovnano) |
| 5 | Sarka Novotna | 27.-31. 7. | 0 | smazano |
| 18 | Pavel Zeman | 16. 7. - 7. 8. | 0 | smazano |
| 6 | Sarka Novotna | 16.-23. 10. | 0 | **ponechano pending** - ceka na rozhodnuti lidi |

`decided_by_user_id` = 20 (Jirka), `status_text` u kazde rika, ze jde o dodatecne srovnani.

**U smazanych dvou to NEZNAMENA, ze dovolenou nemeli** - jen ze zadost nikdo nerozhodl a do dochazky se nic nepropsalo. V e-mailu je vyslovne zadost, aby si schvalovatele overili, jestli na dovolene byli, a pripadne dochazku doplnili.

## Gotcha, ktera zachranila skodu

Zadani znelo "prosle zadosti smaz". Kontrola PRED mazanim ukazala, ze **5 z 7 ma navazane zaznamy v dochazce** (celkem 24 platnych dnu dovolene, cast uz v cervencovych mzdach) - dovolena se totiz propisuje do dochazky **rovnou pri podani, bez ohledu na schvaleni** (zmena Peti z 30. 7. 2026). Smazani zadosti by ty dny neodstranilo, jen jim utrhlo vazbu → sirotci. Proto se mazalo jen to, co skutecne nikde nevisi, a zbytek se oznacil za rozhodnuty.

**Pravidlo: pred mazanim zadosti o absenci VZDY zkontroluj `tenant.att_entry` se `source_system='absence_req'` a `source_id` = id zadosti.**

Andreina dvojita zadost na tentyz termin je pravdepodobne i zdroj nalezu pojistky `absence-bez-duplicit`.

