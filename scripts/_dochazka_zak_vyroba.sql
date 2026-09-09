-- ═══════════════════════════════════════════════════════════════════════
-- Přehled „Docházka po zakázkách" (Peťa 22.7.2026) — v2: + první sloupec
-- "PraceAktivni" (✓ = člověk je zrovna aktivně píchnutý = úsek nemá konec).
--   • základ = tenant.vyroba_work (práce na zakázce + SKUTEČNÁ činnost), C i app
--   • + absence z att_entry (category='absence'), BEZ přestávek
--   • bez interního ID, bez CasBlbost/CasRezie
-- ═══════════════════════════════════════════════════════════════════════
UPDATE fw.data_set
   SET sql_text = $sql$
WITH spolu AS (
  SELECT w.datum AS d, w.od AS od_ts, TRUE AS je_prace,
         w.zakazka_ref AS zak, COALESCE(em.full_name,'Zam '||w.cislo_zam) AS jm,
         em.id AS emp_id, w.cislo_zam AS cz, vc.ec_cislo AS dc, vc.name AS cin,
         w.od AS od_raw, w.konec AS kon_raw, round(COALESCE(w.hodiny,0)::numeric,2) AS hod,
         CASE w.source_system WHEN 'app' THEN 'aplikace' WHEN 'centrala1' THEN 'z Centrály'
              ELSE COALESCE(w.source_system,'') END AS odkud,
         COALESCE(w.poznamka,'') AS pozn
  FROM tenant.vyroba_work w
  LEFT JOIN tenant.att_employee em ON em.tenant_id=2 AND em.user_id=w.user_id
  LEFT JOIN tenant.vyroba_cinnost vc ON vc.id=w.cinnost_id
  WHERE w.tenant_id=2 AND w.source_system IN ('app','centrala1')
  UNION ALL
  SELECT e.entry_date, e.started_at, FALSE,
         'Rezie', COALESCE(em.full_name,'Zam '||em.cislo_zam),  -- Peťa 22.7.: absence = zakázka Rezie (jako v Centrále)
         em.id, em.cislo_zam,
         -- Peťa 22.7.2026: absence dostávají centrálské číslo (dílna 1047) dle typu,
         -- ať se filtrují jako výrobní činnosti (Dovolená 20, Lékař 21, Nemoc 22…).
         CASE et.code WHEN 'vacation' THEN 20 WHEN 'medical' THEN 21 WHEN 'sick' THEN 22
              WHEN 'family_care' THEN 23 WHEN 'sickday' THEN 31 WHEN 'osvc_absence' THEN 37
              WHEN 'unpaid' THEN 39 END,
         et.label,
         e.started_at, e.ended_at, round(COALESCE(e.hours,0)::numeric,2),
         CASE e.source WHEN 'mobile_app' THEN 'aplikace' WHEN 'tablet' THEN 'z Centrály'
              WHEN 'manual' THEN 'z Centrály' WHEN 'ec_import' THEN 'z Centrály'
              WHEN 'cssz_dpn' THEN 'ČSSZ' ELSE COALESCE(e.source,'') END,
         COALESCE(e.note,'')
  FROM tenant.att_entry e
  JOIN tenant.att_employee em ON em.id=e.employee_id
  JOIN tenant.att_entry_type et ON et.id=e.entry_type_id AND et.category='absence'
  WHERE e.tenant_id=2 AND COALESCE(e.status,'')<>'superseded' AND COALESCE(e.source,'')<>'plan_ec'
)
SELECT CASE WHEN je_prace AND kon_raw IS NULL THEN '✓' ELSE '' END AS "PraceAktivni",
       zak                                            AS "CisloZakazky",
       jm                                             AS "JmenoPrijmeni",
       cz                                             AS "CisloZam",
       dc                                             AS "DruhCinnosti",
       cin                                            AS "CinnostText",
       CASE EXTRACT(dow FROM d) WHEN 1 THEN 'Po' WHEN 2 THEN 'Ut' WHEN 3 THEN 'St'
            WHEN 4 THEN 'Ct' WHEN 5 THEN 'Pa' WHEN 6 THEN 'So' ELSE 'Ne' END AS "DenVTydnu",
       to_char(d,'DD.MM.YYYY') || COALESCE(' '||to_char(od_raw,'HH24:MI'),'') AS "CasZacatek",
       CASE WHEN kon_raw IS NULL THEN NULL
            ELSE to_char(kon_raw,'DD.MM.YYYY') || ' ' || to_char(kon_raw,'HH24:MI') END AS "CasKonec",
       hod                                            AS "CasCelkem",
       odkud                                          AS "Odkud",
       (SELECT UPPER(g.engagement_type) FROM tenant.engagement g
         WHERE g.employee_id=emp_id AND g.tenant_id=2 AND g.is_current LIMIT 1) AS "Smlouva",
       pozn                                           AS "Poznamka",
       to_char(d,'DD.MM.YYYY')                        AS "DatumPripadu",
       EXTRACT(year FROM d)::int                      AS "Rok",
       EXTRACT(month FROM d)::int                     AS "Mesic"
FROM spolu
WHERE d <= CURRENT_DATE
ORDER BY d DESC, od_ts DESC NULLS LAST
$sql$,
       updated_at = now()
 WHERE code = 'dochazka.zakazky_vse_list';

UPDATE fw.data_set
   SET sql_text = replace(
         replace((SELECT sql_text FROM fw.data_set WHERE code='dochazka.zakazky_vse_list'),
                 'WHERE d <= CURRENT_DATE', 'WHERE d > CURRENT_DATE'),
         'ORDER BY d DESC, od_ts DESC NULLS LAST', 'ORDER BY d ASC, od_ts ASC NULLS LAST'),
       updated_at = now()
 WHERE code = 'dochazka.zakazky_budoucnost_list';
