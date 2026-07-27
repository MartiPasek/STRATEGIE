# Tenanti a firemní číselník (EC=1, ES=2) — model a pravidlo pro nové tabulky

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Tenanti a firemní číselník (EC=1, ES=2) — model a pravidlo pro nové tabulky

> oblast: `system-strategie` · typ: dokument · rozsah: globální (všichni tenanti) · ověřeno proti živé PG 24.7.2026 (C24)

## Dvě nezávislé osy — nepleť si je

Data ve STRATEGII se rozlišují **dvěma samostatnými poli**:

1. **`tenant_id`** = *který svět / kontext* (firma jako právní tenant, škola, osobní prostor). Hlavní izolační pole. Ověřeno: nese ho **240 tabulek ve schématu `tenant`** + **28 tabulek v `public`**.
2. **kód firmy** = *která právní firma UVNITŘ tenantu*. Relevantní tam, kde jsou data firmně specifická (účetnictví, mzdy, banka), protože EUROSOFT jede jako **dvě právní entity** ve stejném pracovním tenantu.

Princip #2 architektury (`user → tenant → project → system`) mluví o `tenant_id`. Firemní osa je jemnější dělení pod tenantem. Viz [[doc-system-strategie-architektonicke-principy]] a [[doc-system-strategie-db-architektura]].

## Registr tenantů — `public.tenants` (ověřeno 24.7.2026)

Sloupce: `id, tenant_type, tenant_name, tenant_code, owner_user_id, status`. Klíčové:

| id | typ | název | kód |
|---|---|---|---|
| **2** | company | **EUROSOFT** | EUR |
| 14 | company | INTERSOFT | INTERSOFT |
| 13 | school | NERUDOVKA | NERUDOVKA |
| 12 | system | STRATEGIE | STRATEGIE |
| 1 | personal | Osobní (Marti) | MARTI |

+ `personal` tenanty jednotlivců a demo (UKAZKA, MARTIA2000). **Pracovní tenant EUROSOFTu = `tenant_id=2`** — to je to `tenant_id=2`, co je vidět napříč dotazy (VP, kalkulace, docházka…). PG má 4 schémata `AUTHORIZATION "Marti-AI"`: `master` (framework), `tenant_group` (sdílené per skupina), `tenant` (per firma), `"user"` (per uživatel).

## Firemní číselník — `tenant.company` = ZDROJ PRAVDY (ověřeno 24.7.2026)

Sloupce: `id, tenant_id, code, nazev, aktivni, ext_payroll_system, ext_export_mode, ext_company_id`. Obsah pod tenantem 2:

| id (= kód firmy) | code | název |
|---|---|---|
| **1** | **EC** | EUROSOFT - Control |
| **2** | **ES** | EUROSOFT - System |

Takže **EC = 1, ES = 2** (potvrzeno). Sedí i s Heliosem: registr `UCTO_EC..TabDBHelios` má firma 1 = `UCTO_EC` (Control), firma 2 = `UCTO_ES` (System) — viz [[doc-helios-cloud-knowhow-mzdy-ucto]]. VS: EC `4445158191`, ES `4442058998`. Ověřeno v datech: `tenant.bank_platak.firma` má hodnoty `1` (8×) a `2` (5×).

## PRAVIDLO pro každou novou tabulku (Kristý, 24.7.2026)

Při zakládání nové tabulky zaveď **dvě rozlišovací pole**:

- **`tenant_id`** (bigint) — vždy, kvůli izolaci tenantů.
- **kód firmy** (smallint) rozlišující **EC=1 / ES=2**, jako **FK → `tenant.company.id`** — tam, kde jsou data firmně specifická (účto, mzdy, banka, doklady). **Cílový jednotný název sloupce = `firma_id`** (smallint).

## Ověřený stav 24.7.2026 + past na názvosloví

- `tenant_id` je konzistentní (240 `tenant` + 28 `public` tabulek).
- Kód firmy zatím **nemá jednotný název**: `firma` (28×), `company_id` (12×), `firma_id` (11×), `company` (3×). **Do budoucna sjednocovat na `firma_id`** (smallint FK→`tenant.company.id`) — rozhodnutí Kristý 24.7.2026.
- ⚠️ **`firma` je přetížený název**: v `tenant.ec_organizace` (CRM) je `firma` **text = název organizace/zákazníka**, NE kód firmy. Kód firmy je typu **smallint** (viz `ucetni_denik`, `bank_platak`). Před použitím sloupce `firma` ověř datový typ a význam v dané tabulce.
- Princip „**osoba = user, engagement per firma**": jeden člověk může mít víc pracovních vazeb per firma (Marti = ES č.2 + EC č.41 v `att_employee`). Viz doctrina #24 v CLAUDE.md.

## Zdroje ověření (C24, 24.7.2026, přes SQL most, db=pg)
- `information_schema.columns` — výskyt `tenant_id` / `firma` / `company_id` napříč schématy.
- `public.tenants`, `tenant.company` — obsah registrů.
- `tenant.bank_platak` — reálné hodnoty `firma` = 1/2.

