# HR přehled v ERP stromu — podklad pro Martiho (framework uzel)

> Claude-25 (za Šárku), 2. 7. 2026. Šárka chce HR modul v levém stromu ERP
> jako „Přehled pro obchodníka". Vzor 1:1: uzel 116 → jádro 136 (`crm.plan_obchodnika`)
> + band `crm_obchodnik_pult.js` mountovaný v `page_render.js` (gate na coreId).
>
> **Co potřebuju od Tebe (Marti):** založit 1 jádro + 2 uzly stromu (framework
> `fw.core` / `fw.menu_node` = Tvoje/framework doména, moje scope na to nesahá).
> Vše ostatní (komponenta `hr_pult.js`, include, napojení v page_render) mám hotové /
> dodělám hned po založení.

## Krok 1 (Marti) — SQL: jádro + složka + uzel přehledu
```sql
-- 1) Jádro HR přehledu (zrcadlí core 136: is_active, tenant_visibility='all', version=1)
INSERT INTO fw.core (code, label, is_active, tenant_visibility, version, created_by_text)
VALUES ('hr.prehled', 'HR modul — personalistika', true, 'all', 1, 'claude-25 (Šárka)');

-- 2) Nová složka v kořeni stromu (jako CRM=56, sort_order 1000 → HR dáme 1100)
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, is_immutable, created_by_text)
VALUES ('🧑‍💼 Personalistika', NULL, 1100, 'active', false, 'claude-25 (Šárka)');

-- 3) Uzel přehledu pod složkou (parent_id = id složky z kroku 2; core_id = id jádra z kroku 1)
INSERT INTO fw.menu_node (label, parent_id, sort_order, status, is_immutable, core_id, created_by_text)
VALUES ('📋 HR modul', <ID_SLOZKY>, 10, 'active', false, <ID_JADRA>, 'claude-25 (Šárka)');
```
Pozn.: `<ID_SLOZKY>` = id z insertu 2, `<ID_JADRA>` = id z insertu 1 (nebo použij
`RETURNING id`). Bez data_source → grid pod pultem bude prázdný placeholder; HR pult
ho sám skryje (`hideGridHost`) a vyplní plochu.

## Krok 2 (Claude-25, hned po založení) — napojení
1. Přečtu `SELECT id FROM fw.core WHERE code='hr.prehled'`.
2. Do `apps/api/static/erp/components/page_render.js` přidám gated hook (vzor obchodník 136):
   ```js
   if (String(coreId) === '<ID_JADRA>'
       && window.HrPult && typeof window.HrPult.mount === 'function'
       && !document.getElementById('hr-pult')) {
     var _hrEl = document.createElement('div');
     _hrEl.id = 'hr-pult';
     mainContent.insertBefore(_hrEl, gridHost);
     window.HrPult.mount(_hrEl);
   }
   ```
3. Deploy → HR přehled je v ERP stromu (světlý Pinya vzhled).

## Hotové (Claude-25) — čeká jen na Krok 1
- `apps/api/static/erp/components/hr_pult.js` — HR pult (Pinya styl: KPI + dlaždice
  + aktuality, živě z `/app/hr/dashboard`), fail-safe, skryje prázdný grid.
- `<script>` include v `modules/erp/api/router.py` (vedle obchodníkova pultu).

## Přístup (gate) — beze změny
HR přehled i `/app/hr/dashboard` jsou gated `_hr_can_manage` (rodič nebo skupina HR).
Personalisté vidí data, ostatní dostanou „Nemáš oprávnění" (fail-safe prázdno).
