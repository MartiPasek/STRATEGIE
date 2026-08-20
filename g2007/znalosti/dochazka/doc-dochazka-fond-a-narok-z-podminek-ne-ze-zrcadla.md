# Fond (FPD) a nárok dovolené brát z podmínek zaměstnance, ne ze zrcadla Centrály (ZADÁNÍ, 28.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Fond (FPD) a nárok dovolené — brát z podmínek, ne ze zrcadla Centrály

> **ZADÁNÍ (Peťa 28. 7. 2026), zatím NEIMPLEMENTOVÁNO.** Vše ověřeno v datech
> (Claude‑26 přes SQL most, PG + DB_EC). Týká se stránky **Mzdové podklady**
> (`/payroll`, endpointy `/app/payroll/summary` a `/app/payroll/kontrola`).

## 1) Fond (FPD) se má počítat z ÚVAZKU

Dnes se fond bere jako `sum(att_day_summary.fpd)` — tedy 1:1 zrcadlo sloupce
`FPD` z `EC_Dochazka_SumaDen` v Centrále. **To je špatný zdroj.**

**Ověřeno:** `EC_Dochazka_SumaDen.FPD` má natvrdo **7,00** u 40 lidí a **8,00**
u 8 lidí, a **vůbec nekouká na úvazek**. Sedí jen náhodou u těch, kdo mají 35 h/týden.

| č. | člověk | úvazek | má být / den | FPD v SumaDen |
|---|---|---|---|---|
| 425 | Nosek | 40 h | 8 | **7** ✗ |
| 476 | Bláha | 40 h | 8 | **7** ✗ |
| 464 | Namjak | 40 h | 8 | **7** ✗ |
| 472 | Navrátil | 40 h | 8 | **7** ✗ |
| 49 | Dvořáková | 30 h | 6 | **7** ✗ |
| 42 | Veverková | 20 h | 4 | **7** ✗ |
| 322 | Sedláčková | 40 h | 8 | 8 ✓ |
| 50 | Duspivová | 35 h | 7 | 7 ✓ |

**Dopad:** plný úvazek → o 1 h/den menší fond → **falešný přesčas** (Nosek ~15 h
za červenec). Zkrácený úvazek → fond vyšší, než má → vypadá to, že **hodiny chybí**.

**V Centrále to nevadí** — tamní obrazovka „Nesplněný FPD" (procedura
`EC_Dochazka_Odpracovano`) čte **`EC_FinZamPodminky.SmlouvaUvazekT`**, tedy
skutečný úvazek, a počítá správně (HodDenne = 8). Sloupec `SumaDen.FPD` v Centrále
do mezd nevstupuje. **Chyba je jen na naší straně — čteme špatný sloupec.**

**Jak to má být:** `fond = počet pracovních dnů (tenant.att_calendar_day.is_workday)
× (tenant.engagement.uvazek_tyden_h / 5)`. Data máme a jsou správná — `engagement`
sedí na `EC_FinZamPodminky` přesně (ověřeno na 10 lidech).

## 2) Do mzdového přehledu se musí dotahovat i docházka z APPKY

Dnes `/app/payroll/summary` čte **jen** `att_day_summary` (zrcadlo Centrály).
Kdo přešel na appku, tomu v přehledu **chybí dny úplně**.

**Příklad (Bláha, červenec 2026):** data z Centrály mu končí **22. 7.**, dál píchá
jen v appce. K 28. 7. je 19 pracovních dnů, v přehledu má jen **15**.
Fond ukazuje 105 h, správně má být 152 h (19 × 8). Chybí skoro třetina.

**Jak to má být:** přehled skládat z obou zdrojů. Pravidlo pro překryv
(člověk × den má obojí): **přednost má appka**, Centrála se použije jen tam,
kde appka pro ten den nic nemá — jinak se hodiny počítají dvakrát.

## 3) Nárok na dovolenou — taky z úvazku

`tenant.holiday_balance.narok_h` je **natvrdo 200,0 h u všech** (= 25 dnů × 8 h),
bez ohledu na úvazek. `cerpano_h` je **0 u všech**, i když lidé dovolenou čerpají.

| člověk | úvazek | nárok má být | má | = dnů |
|---|---|---|---|---|
| Senft Ondřej | 5 h | 25 h | 200 h | **200 dnů** |
| Vlková Klára | 15 h | 75 h | 200 h | 66,7 |
| Veverková | 20 h | 100 h | 200 h | 50 |
| Dvořáková, Šik | 30 h | 150 h | 200 h | 33,3 |
| Bernardová | 32 h | 160 h | 200 h | 31,3 |
| Novotná, Duspivová, Brudnová | 35 h | 175 h | 200 h | 28,6 |

**Jak to má být:** `narok_h = počet dnů nároku × (uvazek_tyden_h / 5)`; k tomu
doplnit **čerpání** z reálných absencí (`att_entry`, typ `vacation`).

## Pozor při realizaci

- Jde o **mzdový podklad** → paralelní běh a porovnání proti Centrále,
  ne přepnutí naslepo.
- Uzavřené měsíce nepřepisovat.
- Oprava `holiday_balance` je **zápis do dat o nárocích** — přes schvalovací banner,
  ne autonomně.

## Souvislosti

`doc-dochazka-nepritomnost-evidence` · `doc-dochazka-vs-vyroba-separace` ·
`doc-dochazka-cinnosti-mzdy-prehled` · e‑mail Marti Paška 26. 7. 2026 (jeden zdroj pravdy)

