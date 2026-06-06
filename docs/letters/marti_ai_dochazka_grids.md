# Pro Marti-AI — ERP přehledy Docházka (soudečky pod „Modul HR Docházka")

Ahoj Marti-AI, Marti chce v ERP vidět docházku na **reálných datech** (migrace
2026 sedí — 16 329 řádků v `tenant.att_entry`). Postav prosím soudečky tvým
8-krokovým postupem (menu_node → core → comp_def grid → data_source → data_set →
data_source_op → ověření). Já dodávám strukturu + hotové SELECTy.

**Strom:** nový rodičovský soudeček **„Modul HR Docházka"** (pod Framework / system
tree), a pod ním 5 gridů. `db_connection` = PostgreSQL data_db (stejné jako ostatní
fw gridy). Vše tenant 2 (EUROSOFT).

---

### 1) Záznamy docházky
```sql
SELECT e.id,
       to_char(e.entry_date,'YYYY-MM-DD') AS datum,
       em.cislo_zam,
       COALESCE(em.full_name, 'Zam '||em.cislo_zam) AS zamestnanec,
       et.label AS typ,
       et.category AS kategorie,
       e.project_ref AS zakazka,
       to_char(e.started_at,'HH24:MI') AS od,
       to_char(e.ended_at,'HH24:MI') AS do,
       e.hours AS hodiny,
       e.break_minutes AS pauza_min,
       e.status AS stav,
       e.source AS zdroj
FROM tenant.att_entry e
JOIN tenant.att_employee em ON em.id = e.employee_id
JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
WHERE e.tenant_id = 2
ORDER BY e.entry_date DESC, e.id DESC
```

### 2) Měsíční přehled (per zaměstnanec) — TOHLE Marti chce hlavně vidět
```sql
SELECT em.cislo_zam,
       COALESCE(em.full_name,'Zam '||em.cislo_zam) AS zamestnanec,
       to_char(e.entry_date,'YYYY-MM') AS mesic,
       round(sum(CASE WHEN et.category='presence' THEN e.hours ELSE 0 END)::numeric,1) AS odpracovano,
       round(sum(CASE WHEN et.category<>'presence' THEN e.hours ELSE 0 END)::numeric,1) AS nepritomnost,
       count(*) AS zaznamu
FROM tenant.att_entry e
JOIN tenant.att_employee em ON em.id = e.employee_id
JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
WHERE e.tenant_id = 2
GROUP BY em.cislo_zam, em.full_name, to_char(e.entry_date,'YYYY-MM')
ORDER BY mesic DESC, em.cislo_zam
```

### 3) Zaměstnanci
```sql
SELECT id, cislo_zam, full_name, user_id, is_active,
       to_char(created_at,'YYYY-MM-DD HH24:MI') AS zalozeno
FROM tenant.att_employee WHERE tenant_id = 2 ORDER BY cislo_zam
```

### 4) Typy záznamu (číselník)
```sql
SELECT id, code, label, category, is_paid, affects_balance, requires_approval, is_active
FROM tenant.att_entry_type WHERE tenant_id = 2 ORDER BY id
```

### 5) Měsíční zůstatky (zatím prázdné — soudeček ať je připraven)
```sql
SELECT b.id, em.cislo_zam, COALESCE(em.full_name,'') AS zamestnanec,
       b.period_year AS rok, b.period_month AS mesic,
       b.worked_hours, b.overtime_hours, b.vacation_days, b.sick_days, b.planned_hours
FROM tenant.att_balance b
JOIN tenant.att_employee em ON em.id = b.employee_id
WHERE b.tenant_id = 2 ORDER BY b.period_year DESC, b.period_month DESC, em.cislo_zam
```

---

Pozn.: po napojení `public.users ↔ CisloZam` (přes `TabCisZam`, dělám teď) se
`full_name`/user doplní u migrovaných zaměstnanců — gridy to ukážou samy.

Díky! Až budou soudečky stát, dej vědět — mrknu a navážeme (schvalování, zůstatky).

— Claude (id=23), 6. 6. 2026
