# HR Dashboard — analytický uzel ve stromu HR & LIDÉ

> oblast: `osoba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# HR Dashboard (uzel ve stromu HR & LIDÉ)

Postaveno 24.7.2026 (Šárka + Claude-25), vzor Pinya HR (trial vypršel 25.6.).

## Co to je
Nový uzel **„📊 HR Dashboard"** (fw.core `hr.dashboard` id=214, fw.menu_node id=202, parent 117).
Stránka `/hr-dashboard` (statická HTML, tmavý ERP design). 4 pohledy: Lidé ve firmě · Nástupy ·
Odchody a fluktuace · Kvalita dat + filtr zaměstnanců. **Nahradil a archivoval** starý uzel
„Přehled zaměstnanců a OSVČ" (menu_node 191, core `hr.headcount`) — sloučen dovnitř jako grafy.

## Recept na IFRAME uzel (ověřeno)
1. `fw.core` (code) + `fw.menu_node` (parent, core_id) — id jsou IDENTITY (negeneruj ručně).
2. Hook v `apps/api/static/erp/components/page_render.js`: `if (String(coreCode)==='hr.dashboard'){ iframe src=/hr-dashboard }`.
3. Route v `apps/api/main.py` MUSÍ vracet hlavičky `X-Frame-Options: SAMEORIGIN` + `Content-Security-Policy: frame-ancestors 'self'` — jinak Caddy default DENY = rozbitý čtvereček. (viz docs/erp_iframe_uzel_checklist.md)

## GOTCHA — bridge write přes /diag-sql
Cloud rozhoduje read/write dle 1. klíčového slova: `SELECT|WITH|EXPLAIN|SHOW` = read (query_raw guard
odmítne INSERT i uvnitř `WITH ... (INSERT)`!). Write MUSÍ začínat `INSERT/UPDATE/DELETE` → jde do
`fw.claude_write_request` → schvalovací banner. Multi-statement write projde (exekutor spustí naráz, atomicky).

## Datové definice (tenant 2, k 24.7.2026)
- „lidé/zaměstnanci" = `hr_person` is_current, date_end NULL/future = **64**.
- „pracovní poměry" = `engagement` is_current = **80** (HPP 48 / OSVČ 30 / DPP 2; ES 46 / EC 34). 64≠80: víc poměrů na osobu + poměry lidí bez HR karty (att_employee aktivních 79, z toho 15 bez hr_person).
- pohlaví: `hr_person.gender` smallint **0=muž, 1=žena**.
- rodné číslo: v `user_self_data.birth_number` (NE hr_person; ta má prázdné).
- pracovní úroveň `job_position.level` skoro prázdná (4/80) → místo ní graf podle `engagement.pozice_text` (43/62 vyplněno).
- mateřská/rodičovská NENÍ typ absence (chybí v att_entry_type) → KPI „mimořádný stav" zatím ručně.

## Stav / TODO
Čísla jsou zatím STATICKÁ k datu. Navazující krok: živý read-only agregační endpoint (HR-gated) →
graf se počítá sám. Dále doplnit: typ absence maternity/parental, důvod+způsob odchodu (číselník),
měsíční snímky stavu (vývoj počtu), strukturovaná úroveň + org. vazba nadřízený→podřízený.

