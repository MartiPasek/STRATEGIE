# Finanční podmínky — ERP zamčený uzel (SQL pro Martiho)

> Claude-25 (za Šárku), 8. 7. 2026. Šárka + Marti odsouhlasili přístup pro **8 lidí**
> (skupina HR + Marti). Náhled i editace už běží na `/finance-podminky` (gate
> `_finance_can_uid` = pevný seznam 8 ID). ERP jádro `hr.finance` už má hook v
> `page_render.js` (iframe té stránky). **Zbývá jen založit strom-uzel** — a to je
> framework (fw.core + fw.menu_node), takže prosím spusť přímo Ty (bridge write CTE nedá).

## SQL k spuštění (atomické, jádro + zamčený uzel)
```sql
WITH c AS (
  INSERT INTO fw.core (code, label, is_active, tenant_visibility, version, created_by_text)
  VALUES ('hr.finance', 'Finanční podmínky', true, 'all', 1, 'claude-25 (Šárka)')
  RETURNING id
)
INSERT INTO fw.menu_node
  (label, parent_id, sort_order, status, is_immutable, core_id,
   visibility_scope, visibility_user_ids, created_by_text)
SELECT '💰 Finanční podmínky', 117, 15, 'active', false, c.id,
       'restricted', ARRAY[1,11,13,18,107,20,109,108]::integer[], 'claude-25 (Šárka)'
FROM c;
```

- `parent_id=117` = složka „🧑‍💼 HR & LIDÉ".
- `visibility_scope='restricted'` + `visibility_user_ids={8}` → uzel vidí **jen těch 8**
  (Marti 1, Kristý 11, Šárka 13, Petra Š. 18, Fajmonová 107, Honomichl 20, Hrbek 109,
  Šafaříková 108). Pro ostatní je neviditelný (díky opravenému filtru stromu z 7.7.).
- Jádro je „drafted" (bez data_source) → `page_render` pozná `hr.finance` a namountuje
  **iframe** `/finance-podminky` (data i tak gated `_finance_can_uid`, dvojitý zámek).

Po spuštění: uzel „💰 Finanční podmínky" naskočí pod HR & LIDÉ jen těm 8; klik → stránka.
