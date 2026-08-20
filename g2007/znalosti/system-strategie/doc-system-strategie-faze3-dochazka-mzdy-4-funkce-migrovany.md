# Fáze 3 start — 4 další docházka/mzdy funkce (se zápisem) migrovány do g2007.python

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Stav: HOTOVO A AKTIVNÍ (31.7.2026, commit 1a1fcb8cf, C23 + Marti)

Navazuje na Fázi 1 (`doc-system-strategie-faze1-erp-registry-pilot-dokonceno`) a obecný endpoint (`doc-system-strategie-erp-registry-run-obecny-endpoint`). Poprvé migrovány funkce SE SKUTEČNÝM VEDLEJŠÍM ÚČINKEM (zápis), ne jen read-only.

## Migrováno (vše `stav_zivota='active'`, verze 2)

1. **`att_recompute_header_from_items`** (`router.py:_att_recompute_header_from_items`) — obousměrný sync položka→hlavička (vyroba_work → att_entry), Kristý 31.7.2026. Bere živou DB session jako argument.
2. **`sickday_lekar_apply`** — čerpání sick day/lékař ze `sick_day_balance`. Bere živou DB session jako argument.
3. **`refresh_employee_active`** — samooprava rosteru (deaktivace odešlých zaměstnanců), bez argumentů.
4. **`sync_plan_to_dochazka`** — propis plánovaných nepřítomností do `att_entry`, argument `rok` (int|None).

## Vynecháno z původního seznamu "hot" kandidátů — a proč

Analýza datovaných komentářů (posledních ~10 dní) v router.py našla 8 kandidátů v doméně docházka/výroba/mzdy. Dva byly vyřazeny hned:
- `_sync_dochazka_ec` — C24/Kristý ji dnes VYPNULA (early-return chyba), řešila incident se zdvojenou docházkou (req #1620). Mrtvý kód, nic k migraci.
- `_sync_vyroba_work_app` — stub po C24 "kroku 7", jen vrací konstantu.

Jeden byl vědomě odložen: `_sync_ec_dochazka_recent` — jádrový EUROSOFT→docházka sync, aktivně upravovaný Kristý dnes (dedup pass), součást její vícekrokové refaktorky (komentáře "krok 5–8"), zjevně neukončené. Migrace teď by zmrazila kód uprostřed cizí rozpracované práce — Kristý by zítra nevěděla, že má editovat g2007.python místo router.py. **Odloženo na koordinaci s ní, ne technické rozhodnutí.**

## Bezpečnostní pozorování z téhle dávky (důležité pro příště)

**Self-test neplatí pro zápisové funkce.** Fáze 1 self-test (`/selftest`, zavolej DB verzi + starou verzi, porovnej) funguje jen pro READ-ONLY kód — u zápisu druhé volání vidí už změněný stav (falešný nesoulad), nebo se reálný zápis provede dvakrát. U téhle dávky byla verifikace: bajtově věrný přepis přímo z živého souboru (ne přepisování od ruky) + `py_compile` + `diff` proti poslední komitnuté verzi před deployem (ne jen syntax check). Aktivace přes write-approval banner zůstává jediný skutečný bezpečnostní gate pro tenhle typ kódu.

**Incident zachycený před nasazením:** při skriptovaném hromadném nahrazování 4 funkcí najednou použil C23 chybný "end marker" u jedné náhrady (jméno vzdáleně pozdější funkce místo bezprostředně následující) — smazalo by to ~6300 řádků nesouvisejícího kódu (28392–34715). Zachyceno PŘED deployem porovnáním s `git show HEAD:soubor` (čistý read, nedotýká se indexu) — potvrzeno že diff = přesně jen 4 zamýšlené změny, teprve pak deploy. Nic špatného se nikdy nenasadilo. Poučení zapsáno do WORK_LOCK — u hromadných náhrad vždy ověřit end-marker jako přesný text bezprostředně následujícího řádku + vždy diffnout celý soubor proti poslední commitnuté verzi, ne jen syntax-checkovat.

**Pořadí aktivace vs. deploy:** u téhle dávky proběhla aktivace (`stav_zivota='active'`) AŽ PO deployi delegát patche (opačně než u Fáze 1 pilotů) — cca 30–45s okno, kdy by reálné volání kterékoli ze 4 funkcí vyhodilo chybu (žádná aktivní implementace). Příště: vždy aktivovat PŘED deployem delegáta.

## Commit

- `1a1fcb8cf` — delegát patch pro všechny 4 funkce (router.py: 226 řádků net -178, jen 4 cílené funkce dotčeny, ověřeno diffem).

## Zbývá

- `_sync_ec_dochazka_recent` — po domluvě s Kristý.
- Endpointy s `req: Request` (att_fix_*, hr_migrate_dochazka, app_payroll_*...) — jiná architektura (HTTP vrstva musí zůstat v router.py, jen business logika by šla do DB), zatím nezačato.

