-- ============================================================================
-- PODKLAD PRO KONTROLNÍ TABULKU DOCHÁZKY (jeden člověk, jedno období)
-- Claude-26 / Peťa, 3. 8. 2026
--
-- Načte se přes SQL most (vloží se do scripts/claude_sql/CLAUDE2_SQL.sql a spustí
-- CLAUDE2_GO.txt s db=pg), výsledek z CLAUDE2_OUT_FULL.txt pak zpracuje skript
-- scripts/dochazka/gen_dochazka_kontrola.py a vyrobí .xlsx pro daného člověka.
--
-- PŘED SPUŠTĚNÍM NAHRAĎ tři zástupné texty:
--   {CISLO_ZAM}  osobní číslo zaměstnance, např. 24
--   {OD}         první den období, např. 2026-07-01
--   {DO}         poslední den období, např. 2026-07-31
--
-- Vrací JEDNU plochou tabulku, kde sloupec `druh` říká, co je to za řádek:
--   OSOBA  = hlavička (jméno, osobní číslo)
--   W      = úsek rozpadu na zakázky (tenant.vyroba_work)
--   B      = přestávka (tenant.att_entry, typ break)
--   A      = absence – dovolená, lékař, nemoc… (tenant.att_entry, kategorie absence)
--   P      = docházkový záznam BEZ rozpadu na zakázky → v tabulce se červeně
--            vyznačí chybějící zakázka a činnost a člověk je doplní
--   DEN    = kalendář (pracovní den / víkend / svátek + název svátku)
--   ZAMEK  = uzavřená období (mzdy zpracovány) – jen pro informaci v hlavičce
-- ============================================================================
WITH ja AS (
  SELECT em.id AS employee_id, em.user_id, em.cislo_zam, em.full_name
  FROM tenant.att_employee em
  WHERE em.tenant_id = 2 AND em.cislo_zam::text = '{CISLO_ZAM}'
  ORDER BY em.id LIMIT 1
),
-- docházkové úseky (práce/režie/home office), které mají smysl rozpadat na zakázky
useky AS (
  SELECT e.id, e.entry_date, e.started_at, e.ended_at, e.hours, e.project_ref, e.note
  FROM tenant.att_entry e
  JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
  JOIN ja ON ja.employee_id = e.employee_id
  WHERE e.tenant_id = 2
    AND e.entry_date BETWEEN DATE '{OD}' AND DATE '{DO}'
    AND e.status <> 'superseded'
    AND et.code IN ('work','overhead','homeoffice')
    AND e.started_at IS NOT NULL
)
SELECT 'OSOBA' AS druh, ''::text AS id, NULL::date AS datum,
       NULL::timestamptz AS od, NULL::timestamptz AS konec, NULL::numeric AS hodiny,
       ''::text AS zakazka, NULL::int AS ec_cislo, ja.full_name AS cinnost,
       ja.cislo_zam::text AS poznamka
FROM ja
UNION ALL
-- ---------------------------------------------------------------- rozpad (W)
SELECT 'W', 'W-' || w.id::text, w.datum, w.od, w.konec, w.hodiny,
       COALESCE(w.zakazka_ref,''), c.ec_cislo, COALESCE(c.name,''), COALESCE(w.poznamka,'')
FROM tenant.vyroba_work w
JOIN ja ON ja.user_id = w.user_id
LEFT JOIN tenant.vyroba_cinnost c ON c.id = w.cinnost_id
WHERE w.tenant_id = 2 AND w.is_active
  AND w.datum BETWEEN DATE '{OD}' AND DATE '{DO}'
UNION ALL
-- ------------------------------------------------------------- přestávky (B)
SELECT 'B', 'B-' || e.id::text, e.entry_date, e.started_at, e.ended_at, e.hours,
       '', NULL, 'Přestávka', COALESCE(e.note,'')
FROM tenant.att_entry e
JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
JOIN ja ON ja.employee_id = e.employee_id
WHERE e.tenant_id = 2 AND et.code = 'break' AND e.status <> 'superseded'
  AND e.entry_date BETWEEN DATE '{OD}' AND DATE '{DO}'
UNION ALL
-- --------------------------------------------------------------- absence (A)
-- Absence MUSÍ být ve vstupu, jinak se dovolená ukáže jako "chybí zápis"
-- (na tom se Claude-26 spálil 31. 7. 2026 u Kolářové).
SELECT 'A', 'A-' || e.id::text, e.entry_date, e.started_at, e.ended_at, e.hours,
       'Rezie',
       CASE et.code WHEN 'vacation' THEN 20 WHEN 'medical' THEN 21 WHEN 'sick' THEN 22
                    WHEN 'family_care' THEN 23 WHEN 'sickday' THEN 31 WHEN 'unpaid' THEN 26
                    WHEN 'homeoffice' THEN 8 WHEN 'plac_volno_70' THEN 47
                    WHEN 'plac_volno_80' THEN 50 WHEN 'plac_volno_90' THEN 51 END,
       et.label, COALESCE(e.note,'')
FROM tenant.att_entry e
JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
JOIN ja ON ja.employee_id = e.employee_id
WHERE e.tenant_id = 2 AND et.category = 'absence' AND e.status <> 'superseded'
  AND e.entry_date BETWEEN DATE '{OD}' AND DATE '{DO}'
UNION ALL
-- ------------------------------------- docházka BEZ rozpadu na zakázky (P)
-- Úsek, ke kterému neexistuje žádný aktivní řádek rozpadu. Časy jsou známé,
-- chybí jen zakázka a činnost → v tabulce se vyznačí červeně s výzvou doplnit.
SELECT 'P', 'P-' || u.id::text, u.entry_date, u.started_at, u.ended_at, u.hours,
       COALESCE(u.project_ref,''), NULL, '', COALESCE(u.note,'')
FROM useky u
JOIN ja ON true
WHERE NOT EXISTS (
  SELECT 1 FROM tenant.vyroba_work w
  WHERE w.tenant_id = 2 AND w.user_id = ja.user_id AND w.is_active
    AND w.datum = u.entry_date
    AND (w.att_entry_id = u.id
         OR (u.ended_at IS NOT NULL AND w.konec IS NOT NULL
             AND w.od < u.ended_at AND w.konec > u.started_at)))
UNION ALL
-- -------------------------------------------------------------- kalendář (DEN)
SELECT 'DEN', '', cd.day, NULL, NULL, NULL,
       CASE WHEN cd.is_workday THEN 'pracovni' ELSE 'volno' END,
       CASE WHEN COALESCE(cd.is_holiday,false) THEN 1 ELSE 0 END,
       COALESCE(cd.holiday_name,''), ''
FROM tenant.att_calendar_day cd
WHERE cd.tenant_id = 2 AND cd.day BETWEEN DATE '{OD}' AND DATE '{DO}'
UNION ALL
-- ----------------------------------------------------------- zámek období
SELECT 'ZAMEK', '', make_date(pl.rok, pl.mesic, 1), NULL, NULL, NULL,
       'uzavreno', NULL, COALESCE(pl.note,''), ''
FROM tenant.att_period_lock pl
WHERE pl.tenant_id = 2
  AND make_date(pl.rok, pl.mesic, 1) BETWEEN date_trunc('month', DATE '{OD}')::date AND DATE '{DO}'
ORDER BY 3, 4, 1, 2;
