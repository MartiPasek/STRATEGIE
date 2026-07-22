# CRM — přehled „Fronta oslovení" + jak se staví přehled (report) v ERP

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Autor: Claude ID24 (Kristý), 22. 7. 2026. Nový přehled fronty hromadného oslovení + znovupoužitelný postup, jak založit přehled od nuly. Souvisí s [[doc-nabidky-crm-editace-aktivity-z-prehledu]] a [[doc-nabidky-crm-import-firem-osloveni]].

## Přehled „Fronta oslovení" (hotovo)
- **core 208** `crm_fronta_osloveni` (label „Fronta oslovení"), menu **✉️ Fronta oslovení** pod sekcí CRM (`menu_node 56`). Read-only.
- Zdroj: **`mod.crm_outreach`** (PostgreSQL, `db_connection_id=1`) — fronta hromadného oslovení (enqueue přes `/crm/osloveni/enqueue`, odesílá Marti-AI).
- Sloupce: Stav (Čeká/Odesláno/Chyba/Přeskočeno — CASE nad `status`), Příjemce (`recipient_email`), Šablona (`template_code`), Firma ID (`firma_id`), Vyžádáno (`requested_at`), Zadal (`requested_by`), Odesláno kdy (`sent_at`), Poznámka (`error`/`skip_reason`), Batch (`batch_id`).
- **v1 bez názvu firmy**: fronta je v PG, ale název firmy žije v Centrále (MSSQL) — jeden přehled čte z jednoho zdroje, cross-DB join v jednom dotazu nejde. Proto `firma_id` + `recipient_email`.

## 🔑 Jak se staví přehled (report) v ERP — anatomie
Přehled = 5 objektů ve `fw.*`, žádný Python deploy (vše config, čte se živě z DB):
1. **`fw.data_set`** — `sql_text` (SELECT) + `db_connection_id` (1=PG `strategie_pg`, 2=MSSQL `eurosoft_db_ec`/Centrála). Sloupce gridu = **přímo výstupní sloupce SQL** (žádná zvlášť definice). České názvy: v PG dvojité uvozovky `AS "Stav"`, v MSSQL hranaté `AS [Stav]`.
2. **`fw.data_source`** — `code` + `name`.
3. **`fw.data_source_op`** — `operation_kind='select'`, `data_set_id`, `is_default=true` (čtecí operace zdroje). (Edit/insert/delete = další op-řádky → řídí tlačítka Oprava/Nový/Smazat, viz [[doc-nabidky-crm-editace-aktivity-z-prehledu]].)
4. **`fw.core`** — `code`, `label`, `is_active`, `tenant_visibility='all'`, `created_by_text`.
5. **root `fw.comp_def`** — `type_id=306` (grid root), `root=1`, `region_slot='main'`, `refresh_strategy='manual'`, `core_id`, `data_source_id`, `name` (= gridCode), `caption`, `created_by_text`+`updated_by_text`.
6. **`fw.menu_node`** — `label`, `parent_id` (CRM=56), `sort_order`, `status='active'`, `core_id`. Tím je přehled v navigaci.

Po vložení stačí v ERP **Ctrl+F5** (menu i spec se resolvují per-request z DB, žádný deploy/restart).

## Gotchy
- **`id` u `fw.core`/`fw.comp_def`/`fw.menu_node` = GENERATED ALWAYS IDENTITY** → neposílat, nechat auto. `data_set`/`data_source`/`data_source_op` `id` mají default (sekvence) → taky neposílat.
- **Řetězení insertů přes bridge** (jeden approval): NE `DO` blok (bridge dělí skript na `;`) — parenty referencuj **subdotazem na `code`** (`(SELECT id FROM fw.core WHERE code='...')`). Idempotence přes `WHERE NOT EXISTS`.
- **`sql_text` s apostrofy** (CASE 'pending'…): obal do **dollar-quotingu** `$q$ … $q$` (žádné zdvojování `'`). Uvnitř **žádný `;`** (bridge by skript rozsekl). Pozor i na `:slovo` (SQLAlchemy bind) — v tomhle SQL není.
- **Zápis do `fw.*` = PG přes bridge → schvalovací banner** (parent klik). Banner má timeout ~120 s; schválení se ale provede i po timeoutu polleru (objekty pak v DB jsou — ověřuj čtením, ne návratovkou).
- **Po deployi/restartu API most občas vrací HTTP 401 „Nejsi přihlášen"** — chvíli počkat, zotaví se.

## Follow-up (volitelné)
- **Název firmy** ve frontě: buď denormalizovat při enqueue (uložit `firma_nazev` do `crm_outreach`), nebo lookup. Cross-DB PG↔MSSQL v jednom dotazu nejde.
- **Barvy dle stavu**: `formatting_rules` v layoutu gridu (nastavit v UI „Pravidla" → uložit jako sdílený/výchozí; bridge na `erp_grid_layouts`/`comp_grid` nedosáhne rozumně).
- **Indikátor „ve frontě"** v přehledu Kontakty (62) jako doplněk (varianta B z návrhu).
