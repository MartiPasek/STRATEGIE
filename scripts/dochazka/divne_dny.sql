-- ============================================================================
-- DIVNÉ DNY V DOCHÁZCE (jeden člověk, jedno období)
-- Claude-26 / Peťa, 3. 8. 2026
--
-- Vypíše JEN dny, kde je něco podezřelého. Prázdný výsledek = všechno v pořádku.
--
-- PŘED SPUŠTĚNÍM NAHRAĎ:
--   {CISLO_ZAM}  osobní číslo zaměstnance, např. 498
--   {OD}         první den období, např. 2026-07-01
--   {DO}         poslední den období, např. 2026-07-31
--
-- CO SE HLEDÁ (meze zadala Peťa 3. 8. 2026):
--   1 Chybí zápis ............ pracovní den, o kterém systém neví vůbec nic
--   2 Neukončený den ......... chybí konec, nebo ho automat dopsal ve 23:59
--   3 Moc dlouhý den ......... odpracováno víc než 10 h
--   4 Moc krátký den ......... odpracováno míň než 6 h (a není to absence)
--   5 Překryv ................ dvě práce na sobě. Odhlášení „Dnes už se mnou
--                              nepočítej" se ZÁMĚRNĚ ignoruje — lidé jinou
--                              možnost v aplikaci nemají, takže přesah do
--                              odpoledne je normální stav, ne chyba.
--   6 Dlouhá pauza ........... přestávka delší než hodina
--   7 Chybí zakázka/činnost .. úsek rozpadu, který je nemá vyplněné
--   8 Docházka a rozpad nesedí  součty dne se liší o víc než 0,05 h
-- ============================================================================
WITH ja AS (
  SELECT em.id AS emp, em.user_id, em.cislo_zam, em.full_name
  FROM tenant.att_employee em
  WHERE em.tenant_id = 2 AND em.cislo_zam::text = '{CISLO_ZAM}'
  ORDER BY em.id LIMIT 1
),
useky AS (
  SELECT e.id, e.entry_date, e.started_at AS s, e.ended_at AS en, et.code, et.category,
         e.hours, COALESCE(e.note,'') AS note
  FROM tenant.att_entry e
  JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
  JOIN ja ON ja.emp = e.employee_id
  WHERE e.tenant_id = 2 AND e.status <> 'superseded'
    AND e.entry_date BETWEEN DATE '{OD}' AND DATE '{DO}'),
zav AS (SELECT * FROM useky WHERE s IS NOT NULL AND en IS NOT NULL AND en > s),
prace AS (SELECT * FROM zav WHERE category = 'presence'),
ordd AS (SELECT entry_date, s, en, max(en) OVER (PARTITION BY entry_date ORDER BY s, en
   ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS pm FROM prace),
grp AS (SELECT entry_date, s, en, sum(CASE WHEN pm IS NULL OR s > pm THEN 1 ELSE 0 END)
   OVER (PARTITION BY entry_date ORDER BY s, en) AS g FROM ordd),
merged AS (SELECT entry_date, min(s) AS s, max(en) AS en FROM grp GROUP BY entry_date, g),
pres AS (SELECT entry_date, sum(EXTRACT(EPOCH FROM (en - s))/3600.0) AS h
         FROM merged GROUP BY entry_date),
brk AS (SELECT m.entry_date,
          sum(GREATEST(EXTRACT(EPOCH FROM (LEAST(b.en,m.en) - GREATEST(b.s,m.s)))/3600.0,0)) AS h
        FROM zav b JOIN merged m ON m.entry_date = b.entry_date
        WHERE b.code = 'break' GROUP BY m.entry_date),
net AS (SELECT pres.entry_date, ROUND((pres.h - COALESCE(brk.h,0))::numeric,2) AS h
        FROM pres LEFT JOIN brk ON brk.entry_date = pres.entry_date),
rozp AS (SELECT w.datum, ROUND(sum(w.hodiny),2) AS h
         FROM tenant.vyroba_work w JOIN ja ON ja.user_id = w.user_id
         WHERE w.tenant_id = 2 AND w.is_active
           AND w.datum BETWEEN DATE '{OD}' AND DATE '{DO}' GROUP BY w.datum),
absn AS (SELECT DISTINCT e.entry_date FROM tenant.att_entry e
         JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
         JOIN ja ON ja.emp = e.employee_id
         WHERE e.tenant_id = 2 AND et.category = 'absence'
           AND e.status IN ('pending','approved')
           AND e.entry_date BETWEEN DATE '{OD}' AND DATE '{DO}')
SELECT (SELECT full_name FROM ja) AS jmeno,
       (SELECT cislo_zam::text FROM ja) AS cislo_zam,
       to_char(den,'DD.MM.YYYY') AS datum,
       CASE EXTRACT(dow FROM den) WHEN 1 THEN 'Po' WHEN 2 THEN 'Ut' WHEN 3 THEN 'St'
            WHEN 4 THEN 'Ct' WHEN 5 THEN 'Pa' WHEN 6 THEN 'So' ELSE 'Ne' END AS den_v_tydnu,
       problem, detail, hodiny
FROM (
  SELECT cd.day AS den, 1 AS por, 'Chybí zápis' AS problem,
         'Pracovní den bez jakéhokoli záznamu' AS detail, '' AS hodiny
  FROM tenant.att_calendar_day cd
  WHERE cd.tenant_id = 2 AND cd.day BETWEEN DATE '{OD}' AND DATE '{DO}'
    AND cd.is_workday AND NOT COALESCE(cd.is_holiday,false) AND cd.day < CURRENT_DATE
    AND NOT EXISTS (SELECT 1 FROM useky u WHERE u.entry_date = cd.day)
  UNION ALL
  SELECT u.entry_date, 2, 'Neukončený den',
         CASE WHEN u.en IS NULL THEN 'Záznam nemá konec (' || to_char(u.s,'HH24:MI') || ' – …)'
              ELSE 'Konec 23:59 dopsal automat (' || to_char(u.s,'HH24:MI') || ' – 23:59)' END, ''
  FROM useky u
  WHERE u.category = 'presence'
    -- POZOR: řádky automatu (doplnění do fondu / nad fond) mají taky kategorii
    -- „presence", ale žádné časy. Bez téhle podmínky se hlásily jako neukončený
    -- den. (Chyba Claude-26, odhalena 3. 8. 2026 na Benešovi.)
    AND u.s IS NOT NULL
    AND (u.en IS NULL OR (u.note ILIKE '%auto-odhlášení%' AND to_char(u.en,'HH24:MI') = '23:59'))
  UNION ALL
  SELECT n.entry_date, 3, 'Moc dlouhý den', 'Odpracováno víc než 10 hodin',
         to_char(n.h,'FM990.00') FROM net n WHERE n.h > 10
  UNION ALL
  SELECT n.entry_date, 4, 'Moc krátký den', 'Odpracováno míň než 6 hodin, a není to absence',
         to_char(n.h,'FM990.00')
  FROM net n JOIN tenant.att_calendar_day cd ON cd.tenant_id = 2 AND cd.day = n.entry_date
       AND cd.is_workday AND NOT COALESCE(cd.is_holiday,false)
  WHERE n.h > 0.1 AND n.h < 6 AND n.entry_date NOT IN (SELECT entry_date FROM absn)
  UNION ALL
  SELECT a.entry_date, 5, 'Překryv',
         to_char(a.s,'HH24:MI') || '–' || to_char(a.en,'HH24:MI') || '  x  '
         || to_char(b.s,'HH24:MI') || '–' || to_char(b.en,'HH24:MI'), ''
  FROM prace a JOIN prace b ON b.entry_date = a.entry_date AND b.id > a.id
  WHERE a.s < b.en AND a.en > b.s
  UNION ALL
  SELECT z.entry_date, 6, 'Dlouhá pauza',
         'Přestávka ' || to_char(z.s,'HH24:MI') || '–' || to_char(z.en,'HH24:MI'),
         to_char(ROUND((EXTRACT(EPOCH FROM (z.en - z.s))/3600.0)::numeric,2),'FM990.00')
  FROM zav z WHERE z.code = 'break' AND EXTRACT(EPOCH FROM (z.en - z.s))/3600.0 > 1.0
  UNION ALL
  SELECT w.datum, 7, 'Chybí zakázka nebo činnost',
         to_char(w.od,'HH24:MI') || '–' || COALESCE(to_char(w.konec,'HH24:MI'),'…') || '  '
         || CASE WHEN COALESCE(w.zakazka_ref,'') = '' THEN 'bez zakázky ' ELSE '' END
         || CASE WHEN w.cinnost_id IS NULL THEN 'bez činnosti' ELSE '' END,
         to_char(COALESCE(w.hodiny,0),'FM990.00')
  FROM tenant.vyroba_work w JOIN ja ON ja.user_id = w.user_id
  WHERE w.tenant_id = 2 AND w.is_active
    AND w.datum BETWEEN DATE '{OD}' AND DATE '{DO}'
    AND (COALESCE(w.zakazka_ref,'') = '' OR w.cinnost_id IS NULL)
  UNION ALL
  -- Peťa 3.8.2026 (nález u Brudnové): den, kdy má člověk zapsanou absenci
  -- a ZÁROVEŇ odpracované hodiny. Typicky zůstane viset dovolená z plánu
  -- nepřítomností, kterou nakonec nečerpal - a strhne se mu z nároku.
  SELECT n.entry_date, 0, 'Dovolená (nebo jiná absence) a zároveň práce',
         (SELECT string_agg(DISTINCT et2.label, ', ') FROM tenant.att_entry a2
          JOIN tenant.att_entry_type et2 ON et2.id = a2.entry_type_id
          JOIN ja ON ja.emp = a2.employee_id
          WHERE a2.tenant_id = 2 AND a2.entry_date = n.entry_date
            AND et2.category = 'absence' AND a2.status <> 'superseded')
         || ' — a přitom odpracováno ' || to_char(n.h,'FM990.00') || ' h',
         to_char(n.h,'FM990.00')
  FROM net n
  WHERE n.h > 0.1 AND n.entry_date IN (SELECT entry_date FROM absn)
  UNION ALL
  SELECT COALESCE(n.entry_date, r.datum), 8, 'Docházka a rozpad nesedí',
         'Docházka ' || to_char(COALESCE(n.h,0),'FM990.00') || ' h, rozpad '
         || to_char(COALESCE(r.h,0),'FM990.00') || ' h',
         to_char(ABS(COALESCE(n.h,0) - COALESCE(r.h,0)),'FM990.00')
  FROM net n FULL JOIN rozp r ON r.datum = n.entry_date
  WHERE ABS(COALESCE(n.h,0) - COALESCE(r.h,0)) > 0.05
) x
ORDER BY den, por;
