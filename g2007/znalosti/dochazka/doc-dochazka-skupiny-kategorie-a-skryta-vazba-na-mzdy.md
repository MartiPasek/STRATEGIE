# Docházkové skupiny (att_kategorie), přesčasy a skrytá vazba na mzdy

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Model

Docházkové skupiny = `tenant.att_kategorie` (číselník) + `tenant.att_user_kategorie`
(zařazení, **PK = user_id** → jeden člověk = jedna skupina; klíč je `user_id`, ne `employee_id`).

Příznaky skupiny: `dopichavat_fond`, `fond_h_den`, `bez_prescasu`,
`hlidat_dlouhou_smenu` + `dlouha_smena_h`, `hlidat_pauzy`, `auto_odhlasit`, `aktivni`, `poradi`.

## Skupina rozhoduje, jestli člověk může mít PŘESČAS

Rozhoduje jediný příznak `dopichavat_fond`:

| Skupina | dopichavat_fond | Hodiny nad fond | Přesčas ve mzdách |
|---|---|---|---|
| Kancelář (`volna_kancelar`) | true | automat je překlopí do `nenarokova` | **nemá** — `mzdy_loajalita_rows` přeskočí |
| Výroba (`pevna_doba`) | false | automat se jich nedotkne | **má** — nad fond → složka 651 |
| Hodinoví / OSVČ | dle zařazení | — | vyjdou nad fond, je to správně |
| Bez skupiny | — | automat je ignoruje (INNER JOIN, žádný fallback) | chová se jako dílna |

Kancelář přesčas nemá záměrně (Martiho motivační systém 26.6.2026). Detail automatu:
[[doc-dochazka-automat-fond-doplneni]], FPD vzorce: [[doc-dochazka-fpd-vypocet-kancelar-vs-dilna]],
víkend/svátek: [[doc-dochazka-vikend-svatek-cely-nad-fond]].

Přesčas do peněz: `mzdy_loajalita_rows` → složka 651 (prémie), sazba `hod_sazba_prescas`
z `tenant.helios_wage_snapshot`, kaskáda svátky → víkendy → běžný den.
`CasPrescas` chodí navíc do `att_day_summary` ze Centrály (`EC_Dochazka_SumaDen`)
přes `sync_dochazka_sumaden`.

## ⚠️ Hlavní gotcha: `dopichavat_fond` nese DVĚ role

Kromě docházky určuje i to, **kdo je „kancelář" ve mzdách**. Tři aktivní funkce
v `g2007.python` si množinu kanceláří počítají přímo z docházkové skupiny:

```sql
skup24 = SELECT uk.user_id FROM tenant.att_user_kategorie uk
         JOIN tenant.att_kategorie k ON k.id = uk.kategorie_id
         WHERE k.tenant_id = 2 AND k.dopichavat_fond = true AND k.aktivni = true
```

- `mzdy_benefity_apply` — `is_office = user_id in skup24` → oblečení **109 Kč/den
  (kancelář) vs 279 Kč/den (dílna)** + nárok na home office (6 dní napevno).
- `mzdy_loajalita_rows` — kdo je v `skup24`, **se přeskočí** → nemá přesčasovou prémii (651).
- `payroll_raporty` — CTE `kancl`.

**Důsledek: jakýkoli přesun člověka do/ze skupiny s `dopichavat_fond=true` mění
mzdové složky.** Zmírnění: `mzdy_benefity_apply` počítá jen `typ_smlouvy='hpp'`,
`mzdy_loajalita_rows` vylučuje `osvc` → **u OSVČ je přesun mzdově neutrální**.

**Doporučení do budoucna:** rozpadnout `dopichavat_fond` na dva nezávislé příznaky
(docházkový + `mzdy_kancelar`), aby docházková změna nehýbala mzdami.

## `bez_prescasu` je MRTVÝ příznak

Živý automat `att_automat_level_day` ho **vůbec nečte** — hledání přes celý
`g2007.python` na `bez_prescasu` nevrátí ani řádek. Automat jede jen na
`dopichavat_fond=true` a přebytek nad fond vždy překlápí do `nenarokova`.
Četl ho `_att_automat_fond_odpich` v `router.py`, což je mrtvý kód s nula voláními.

Proto byla 17.8.2026 skupina **`volna_prescasy` deaktivována** (rozhodnutí Kristý):
dělala by pravý opak toho, co slibuje názvem — přesčas by spadl do nenárokové práce
a nositel by navíc kvůli `dopichavat_fond=true` přišel i o prémii 651.

## Kdo skupiny čte (dopadová mapa, ověřeno v g2007.python)

- Automat: `att_automat_level_day`, `att_prazdny_den_fond` — **INNER JOIN**, takže
  **kdo nemá skupinu, toho se automat vůbec nedotkne** (žádný fallback).
- Hlídače: `att_auto_checkout_midnight`, `att_long_shift_nudge`, `att_break_overrun_nudge`.
- Fond pro absence/kontroly: `att_absence_request`, `att_absence_mine`, `att_fix_day`,
  `dochazka_kontrola_data`.
- Mzdy: viz výše.

## Nepleteme si to se třemi souběžnými mechanismy

| Mechanismus | K čemu | Kdo čte |
|---|---|---|
| `tenant.staff_group` + `staff_group_member` + `staff_cond` | **nároky — dovolená, sick days** (3vrstvý resolver user → group → system) | `att_narok_cerpani`, `att_sick_balance_h`, `hr_podminky_prehled`, `sickday_lekar_apply` |
| `att_employee.cond_group` (varchar) | historický zbytek | **nic to nečte** (viz níže) |
| `engagement.plny_fond_bez_dochazky` (boolean na smlouvě) | „bez docházky, vždy plný fond" | `att_day_summary_recompute`, `dochazka_kontrola_data` |

**Požadavek „bez docházky – plný fond" NENÍ skupina** — je to flag na engagementu,
nastavený u Marti Pašek, Vlková, Senft, Mózer. Rozhodnutí Kristý 17.8.2026:
**pátou skupinu se stejným významem nezakládat**, aby nevznikly dva zdroje pravdy.

## ⚠️ Podezření k ověření: přiřazení do podmínkové skupiny se nikam nepropíše

- **Zápis:** `POST /app/hr/conditions/assign` (`router.py` ~ř. 19981) dělá
  `UPDATE tenant.att_employee SET cond_group = :g` — jen do sloupce, do
  `staff_group_member` nezapisuje nic.
- **Čtení:** `_cond_group_of`, `att_narok_cerpani`, `att_sick_balance_h` berou skupinu
  výhradně z `staff_group_member` + `staff_cond`. Sloupec `cond_group` nečte nikdo.
- Data: `cond_group` vyplněn u 8 lidí z 237, hodnoty textové (`kancelare`), zatímco
  `staff_cond.group_code` je číselné ID → nespárují se. `staff_cond`: 275× scope `user`,
  16× `system`, 9× `group`. Ze 17 skupin mají podmínky jen `3 Výroba` a `4 Nákup`;
  `14 KANCELÁŘE` a `15 VÝROBA` mají 0 členů.
- **Důsledek:** kdo nemá vlastní `user` řádek, spadne až na `system` → vidí 25 dnů
  dovolené a 2 sick days, i když v Centrále má 0. Sedí na Jirkův nález ze 17.8.
- **NEOVĚŘENO:** jestli neexistuje jiná synchronizace `cond_group` → `staff_group_member`.
  Doména Jirka (C28), předáno k ověření, nic neměněno.

## Stav k 17. 8. 2026 (po zařazení, requesty #2142 a #2143)

| Skupina | dopichavat_fond | lidí | přesčas |
|---|---|---|---|
| `volna_kancelar` — Kanceláře | true | 23 | ne (nenároková práce) |
| `pevna_doba` — Výroba | false | 33 | ano |
| `bez_dochazky_absence` — Bez docházky, hlídat absenci (nová 17.8.) | true | 2 (Mareš, Pillár) | ne |
| `bez_automatu` | false | 1 (Bernardová) | ano |
| `volna_prescasy` | true | 0 | **DEAKTIVOVÁNA 17.8.** |

Zařazení do výroby proběhlo podle `engagement.pozice_text` (elektromontér, zámečník,
skladový asistent, přípravář) — 25 HPP + 8 OSVČ. Do 17.8. bylo bez skupiny 59 lidí.
**Mzdový dopad zařazení: nulový** — dílenští zůstávají mimo `skup24`, Mareš a Pillár
jsou bez mzdových složek.

## Hardcoded výjimky ve mzdách (kandidáti na nahrazení skupinou)

V `mzdy_benefity_apply`: `_HO_DILNA_VYJIMKA = {(ES, 476)}` Bláha ·
`_HO_BEZ_NAROKU = {(ES, 442), (ES, 489)}` Hrůzová, Nepodalová.

## Otevřené (k 17.8.2026)

- 3 HPP bez vyplněné `pozice_text`: Peřina (536), M. Šafránková (381), Herejtová (525, dpp).
- Nepodalová (489) — pozice „pracovník v příjmu zboží", ale sedí v `volna_kancelar`.
- Martin Pašek (29) — Kristý ho zatím nechala v `volna_kancelar` kvůli mzdovému dopadu.
- Zastaralá věta v [[doc-dochazka-automat-fond-doplneni]]: „na mzdy to nedopadá, protože
  ty čtou att_day_summary plněné z Heliosu" — od 6.8. se plní ze STRATEGIE, viz
  [[doc-mzdy-zrcadlo-dochazky-ze-strategie]]. Opravit má Peťa (C26), autor znalosti.

Podklady: `docs/dochazka_skupiny_navrh.md` (dopadová mapa),
`docs/dochazka_skupiny_pro_jirku_c28.md` (výklad pro Jirku a C28). Claude-24, 17.8.2026.

