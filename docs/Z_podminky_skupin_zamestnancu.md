# Podmínky skupin zaměstnanců + individuální výjimky (Šárka, 12. 6. 2026)

**Zdroj:** Šárka Novotná (personalistka), text 12.6.2026 · **Model:** 3vrstvý resolver
**systém → skupina → jednotlivec** (stejný vzor jako docházkové volby + rez_* režimy).
Specifičtější vrstva **přepíše** stejný klíč (doctrine „INSERT row, ne schema migrace").

## Vrstvy
- **systém** — default pro všechny HPP (dovolená, sick days, stravenka, přesčas. limit…).
- **skupina** — `elektromontri` (Výroba) / `kancelare` (Kanceláře). Další: vedeni / vp (zatím bez podmínek).
- **jednotlivec** — override na user_id.

## Katalog podmínek (staff_cond_def)
| code | label | kind | unit |
|---|---|---|---|
| uvazek_h_tyden | Týdenní úvazek | num | h/týд |
| nastup_max | Povinný nástup nejpozději | time | |
| absence_nahlasit_do | Nepřítomnost nahlásit do | time | |
| neplaceny_prescas_h_den | Neplacený přesčas | num | h/den |
| danova_obleceni | Daňová úspora – oblečení | bool | |
| danova_ho | Daňová úspora – home office | bool | |
| home_office_h | Home office | num | h/měs |
| sick_days_rok | Sick days | num | dní/rok |
| dovolena_dni | Dovolená (zákl.+dodatková) | num | dní/rok |
| stravenka_kc | Stravenkový paušál | num | Kč/směna |
| prescas_limit_rok | Limit přesčasů | num | h/rok |
| vikend_jen_schvaleni | Víkend jen po schválení | bool | |
| prac_dny | Obvyklá pracovní doba | text | |

## Systém (default pro všechny HPP)
- dovolena_dni = **25** (20 zákl. + 5 dodatková); +1 po **10 / 15 / 20** letech (seniorita — pravidlo, řeší výpočet z nástupu).
- sick_days_rok = **2** · nevyčerpané na konci roku **proplaceny 70 %**.
- stravenka_kc = **82** Kč/odpracovaná směna (nenáleží: sick day, OČR, PN, neodpracovaná směna).
- prescas_limit_rok = **150** (zákoník práce). Nařízený = proplácen dle ZP; dobrovolný = **prémie za loajalitu** (→ napojení na konto/loajalita engine).
- vikend_jen_schvaleni = ANO · prac_dny = Po–Pá.

## Skupina ELEKTROMONTÉŘI (`elektromontri`)
uvazek_h_tyden=40 · nastup_max=**07:00** · absence_nahlasit_do=07:00 ·
neplaceny_prescas_h_den=**0.0** · danova_obleceni=ANO · danova_ho=NE · home_office_h=0.

## Skupina KANCELÁŘE (`kancelare`)
uvazek_h_tyden=40 · nastup_max=**09:00** · absence_nahlasit_do=09:00 ·
neplaceny_prescas_h_den=**0.5** · danova_obleceni=ANO · danova_ho=ANO · home_office_h=**48**.

## Individuální výjimky (user override)
| osoba | user_id | skupina | override |
|---|---|---|---|
| Ivana Brudnová | 48 | elektromontri | uvazek_h_tyden=35; sick_days_rok=5 (2+3) |
| Tomáš Bláha | 64 | elektromontri | danova_ho=ANO + home_office_h (HO navíc) |
| Andrea Bernardová | 63 | kancelare | uvazek_h_tyden=32 (4×8) |
| Petra Dvořáková | 40 | kancelare | uvazek_h_tyden=30 |
| Tereza Veverková | 36 | kancelare | uvazek_h_tyden=20 |
| Šárka Novotná | 13 | kancelare | uvazek_h_tyden=35; sick_days_rok=15 (místo navýšení mzdy) |
| Kristýna Marešová | 11 | kancelare | uvazek_h_tyden=40, možnost individuálně méně (note) |
| Vlková | 15 | kancelare | uvazek_h_tyden=15 (v EC 0 prac. dnů/týд) |
| Mózer Branislav | 98 | kancelare | paušální mzda, 1 prac. den/týд (úterky) → prac_dny=Úterý |
| Pavel Zeman | 30 | kancelare | home_office_h=64 |
| Luboš Trunec | 60 | — | individuální odměna od jednatele (řeší finance, ne tady) |

## Mimo-skupinové (finance/odměny — návazné, ne podmínka docházky)
- **Individuální odměna od jednatele** — mimo mzdový výměr (stabilizační/dorovnání/retenční). Aktuálně Trunec; dříve Purkar, Pěchouček. Jen ve finančních podmínkách.
- **Doporučení nového zaměstnance:** 500 Kč za pohovor; nástup: elektromontér 30 000 · VP/IT 50 000 · PLC programátor 100 000.
- **Prémie za vedení lidí** — individuální u vedoucích oddělení (Havlát, Šafránková, Veverka…).

## Tabulky
- `tenant.staff_cond_def` — katalog (code/label/kind/unit/sort/active).
- `tenant.staff_cond` — hodnoty po vrstvách (scope_kind system/group/user, group_code, user_id, cond_code, value, note).
- Členství: `att_employee.cond_group` (elektromontri/kancelare) — zatím seed individuálních + skupiny; plné rozřazení 67 lidí přes UI.

## TODO
- Napojit Vlková + Mózer na user_id (chybí/placeholder).
- UI „Podmínky skupin" v brand templatu (lišta = skupiny/systém, vlevo podmínky, individuální výjimky).
- Resolver endpoint (resolved podmínky pro usera) + napojení na docházku (nástup/nahlášení), konto (loajalita/přesčas), stravenku, dovolenou (seniorita).
- Konzultace Marti-AI (doctrine #8) k hlubšímu modelu + napojení na výpočty.
