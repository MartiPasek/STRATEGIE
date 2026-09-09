
WITH spolu AS (
  SELECT w.datum AS d, w.od AS od_ts, TRUE AS je_prace,
         w.zakazka_ref AS zak, COALESCE(em.full_name,'Zam '||w.cislo_zam) AS jm,
         em.id AS emp_id, w.cislo_zam AS cz, vc.ec_cislo AS dc, vc.name AS cin,
         w.od AS od_raw, w.konec AS kon_raw, round(COALESCE(w.hodiny,0)::numeric,2) AS hod,
         CASE w.source_system WHEN 'app' THEN 'aplikace' WHEN 'centrala1' THEN 'z Centrály' WHEN 'manual_fix' THEN 'ruční oprava' WHEN 'sync' THEN 'dopočet z docházky'
              ELSE COALESCE(w.source_system,'') END AS odkud,
         COALESCE(NULLIF(btrim(w.poznamka), ''), ae.note, '') AS pozn,
         'W' AS kind, w.id AS rid, w.cinnost_id AS cin_id, w.source_system AS src,
         NULL::text AS vpozn, NULL::boolean AS vsch, NULL::boolean AS preq
  FROM tenant.vyroba_work w
  -- Peta 3.9.2026: JEDNA KARTA NA CLOVEKA, jinak se radky NASOBI. tenant.att_employee
  -- ma na jednoho cloveka vic radku (Kristyna Maresova 2, Marti Pasek 3) a obycejny
  -- LEFT JOIN pres user_id vyrobil z jednoho useku dva az tri radky prehledu. U karty
  -- BEZ JMENA k tomu COALESCE dopsal popisek "Zam <cislo>", ktery vypadal jako dalsi
  -- clovek - Peta na to narazila u Kristyny ("Zam 21"). Bereme jednu kartu, prednostne
  -- pojmenovanou a aktivni. Vzor podle gotchy z predani 27.8.2026 (LATERAL ... LIMIT 1).
  LEFT JOIN LATERAL (
    SELECT em2.* FROM tenant.att_employee em2
     WHERE em2.tenant_id=2 AND em2.user_id=w.user_id
     ORDER BY (em2.full_name IS NOT NULL) DESC, COALESCE(em2.is_active,false) DESC, em2.id
     LIMIT 1) em ON true
  LEFT JOIN tenant.vyroba_cinnost vc ON vc.id=w.cinnost_id
   -- Peta + Claude-26, 7.9.2026: poznamku pise editor pri oprave na HLAVICKU (att_entry),
   -- ale prehled ukazuje RADEK ROZPADU (vyroba_work), kde je kolonka prazdna. Text tak
   -- nebyl videt nikde (naslo se u Urbanove 1.8. - prevod 9 h z 31.7.). Kdyz je poznamka
   -- rozpadu prazdna, bere se z navazane hlavicky pres att_entry_id. Nic se neprepisuje.
   LEFT JOIN tenant.att_entry ae ON ae.id=w.att_entry_id
  WHERE w.tenant_id=2 AND w.source_system IN ('app','centrala1','manual_fix','sync') AND w.is_active
  UNION ALL
  SELECT e.entry_date, e.started_at, TRUE,
         COALESCE(e.project_ref,'Rezie'), COALESCE(em.full_name,'Zam '||em.cislo_zam),
         em.id, em.cislo_zam,
         NULL::integer, et.label,
         e.started_at, e.ended_at, round(COALESCE(e.hours,0)::numeric,2),
         CASE e.source WHEN 'mobile_app' THEN 'aplikace' WHEN 'manual_fix' THEN 'aplikace'
              WHEN 'tablet' THEN 'z Centrály' WHEN 'manual' THEN 'z Centrály'
              WHEN 'ec_import' THEN 'z Centrály' WHEN 'cssz_dpn' THEN 'ČSSZ' WHEN 'manual_fix' THEN 'ruční oprava' WHEN 'absence' THEN 'schválená žádost' WHEN 'plan_ec' THEN 'plán z Centrály' WHEN 'automat' THEN 'automat'
              ELSE COALESCE(e.source,'') END,
         COALESCE(e.note,''),
         'P', e.id, NULL::bigint, e.source,
         e.vedouci_poznamka, e.ved_schvaleno, e.pozadavek_uprava
  FROM tenant.att_entry e
  JOIN tenant.att_employee em ON em.id=e.employee_id AND em.tenant_id=2
  JOIN tenant.att_entry_type et ON et.id=e.entry_type_id AND et.category='presence'
  WHERE e.tenant_id=2 AND et.code IN ('work','overhead','homeoffice')
    AND COALESCE(e.status,'') NOT IN ('superseded','announced') AND COALESCE(e.source,'')<>'plan_ec'
     -- Peta 25.8.2026: OHLASENI home office (bez hodin i bez casu) je jen informace
     -- pro vedouciho a patri vyhradne do Spravy dochazky. Sem patri jen REALNE
     -- odpracovany home office. Rozlisuje se podle dat, ne podle znacky puvodu.
     AND NOT (et.code='homeoffice' AND e.hours IS NULL AND e.started_at IS NULL)
    AND (
      NOT EXISTS (SELECT 1 FROM tenant.vyroba_work w2
           WHERE w2.tenant_id=2 AND w2.user_id=em.user_id AND w2.datum=e.entry_date
             AND w2.source_system IN ('app','centrala1','manual_fix','sync'))
      OR (e.ended_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM tenant.vyroba_work w3
               WHERE w3.tenant_id=2 AND w3.user_id=em.user_id AND w3.datum=e.entry_date
                 AND w3.source_system IN ('app','centrala1','manual_fix','sync') AND w3.konec IS NULL AND w3.is_active))
    )
  UNION ALL
  SELECT e.entry_date, e.started_at, FALSE,
         'Rezie', COALESCE(em.full_name,'Zam '||em.cislo_zam),
         em.id, em.cislo_zam,
         CASE WHEN e.ec_druh = 30 THEN 30 ELSE CASE et.code WHEN 'vacation' THEN 20 WHEN 'medical' THEN 21 WHEN 'sick' THEN 22
              WHEN 'family_care' THEN 23 WHEN 'sickday' THEN 31 WHEN 'osvc_absence' THEN 37
              WHEN 'unpaid' THEN 39 WHEN 'ostatni_nahrada' THEN 34 END END, CASE WHEN e.ec_druh = 30 THEN (SELECT c.name FROM tenant.vyroba_cinnost c WHERE c.tenant_id = 2 AND c.ec_cislo = 30 AND COALESCE(c.active, true) LIMIT 1) ELSE et.label END,
         e.started_at, e.ended_at, round(COALESCE(e.hours,0)::numeric,2),
         CASE e.source WHEN 'mobile_app' THEN 'aplikace' WHEN 'tablet' THEN 'z Centrály'
              WHEN 'manual' THEN 'z Centrály' WHEN 'ec_import' THEN 'z Centrály'
              WHEN 'cssz_dpn' THEN 'ČSSZ' WHEN 'manual_fix' THEN 'ruční oprava' WHEN 'absence' THEN 'schválená žádost' WHEN 'plan_ec' THEN 'plán z Centrály' WHEN 'automat' THEN 'automat' ELSE COALESCE(e.source,'') END,
         COALESCE(e.note,''),
         'A', e.id, NULL::bigint, e.source,
         e.vedouci_poznamka, e.ved_schvaleno, e.pozadavek_uprava
  FROM tenant.att_entry e
  JOIN tenant.att_employee em ON em.id=e.employee_id
  JOIN tenant.att_entry_type et ON et.id=e.entry_type_id AND et.category='absence'
  WHERE e.tenant_id=2 AND COALESCE(e.status,'') NOT IN ('superseded','announced')
    -- Peta 17.-18.8.2026: NEPRITOMNOST OSVC do Dochazky new NEPATRI. Neni to dochazka,
    -- je to jen informace, ze ten den clovek nebude v praci - stejne jako to bylo
    -- v Centrale. Zustava videt ve Sprave dochazky a v Opravach (tam se ale nepocita
    -- do souctu dne). Detail v G2007 doc-dochazka-nepritomnost-osvc-nepatri-do-fondu.
    AND et.code <> 'osvc_absence'
  UNION ALL
  SELECT ds.datum, NULL::timestamptz, FALSE,
         'Rezie', COALESCE(em.full_name,'Zam '||ds.cislo_zam),
         em.id, ds.cislo_zam::varchar,
         NULL::smallint, 'Rezie (denní souhrn)',
         NULL::timestamptz, NULL::timestamptz, round(COALESCE(ds.cas_celkem,0)::numeric,2),
         'z Centrály', '', 'C', ds.id, NULL::bigint, 'z Centrály',
         NULL::text, NULL::boolean, NULL::boolean
  FROM tenant.att_day_summary ds
  -- Peta 3.9.2026: totez co u vyroba_work vyse - jedna karta na cloveka.
  LEFT JOIN LATERAL (
    SELECT em2.* FROM tenant.att_employee em2
     WHERE em2.tenant_id=2 AND em2.user_id=ds.user_id
     ORDER BY (em2.full_name IS NOT NULL) DESC, COALESCE(em2.is_active,false) DESC, em2.id
     LIMIT 1) em ON true
  WHERE ds.tenant_id=2 AND ds.datum>='2026-01-01' AND ds.datum<='2026-05-31'
    AND COALESCE(ds.cas_celkem,0) > 0
    AND NOT EXISTS (SELECT 1 FROM tenant.vyroba_work w2
         WHERE w2.tenant_id=2 AND w2.user_id=ds.user_id AND w2.datum=ds.datum
           AND w2.source_system IN ('app','centrala1','manual_fix','sync'))
)
SELECT CASE WHEN je_prace AND kon_raw IS NULL AND COALESCE(dc,0) <> 27 AND d = CURRENT_DATE THEN '✓' ELSE '' END AS "PraceAktivni",
       zak                                            AS "CisloZakazky",
       jm                                             AS "JmenoPrijmeni",
       cz                                             AS "CisloZam",
       dc                                             AS "DruhCinnosti",
       cin                                            AS "CinnostText",
       CASE EXTRACT(dow FROM d) WHEN 1 THEN 'Po' WHEN 2 THEN 'Ut' WHEN 3 THEN 'St'
            WHEN 4 THEN 'Ct' WHEN 5 THEN 'Pa' WHEN 6 THEN 'So' ELSE 'Ne' END AS "DenVTydnu",
       to_char(d,'DD.MM.YYYY') || COALESCE(' '||to_char(od_raw,'HH24:MI'),'') AS "CasZacatek",
       CASE WHEN kon_raw IS NULL AND od_raw IS NULL THEN to_char(d,'DD.MM.YYYY') WHEN kon_raw IS NULL THEN NULL WHEN position('auto-odhlášení' in COALESCE(pozn,'')) > 0 AND to_char(kon_raw AT TIME ZONE 'Europe/Prague','HH24:MI') = '23:59' THEN NULL WHEN (kon_raw AT TIME ZONE 'Europe/Prague')::date <> d THEN NULL ELSE to_char(kon_raw,'DD.MM.YYYY') || ' ' || to_char(kon_raw,'HH24:MI') END AS "CasKonec",
       hod                                            AS "CasCelkem",
       odkud                                          AS "Odkud",
       (SELECT UPPER(g.engagement_type) FROM tenant.engagement g
         WHERE g.employee_id=emp_id AND g.tenant_id=2 AND g.is_current LIMIT 1) AS "Smlouva",
       CASE WHEN pozn LIKE '%ROZPOR:%' THEN btrim(regexp_replace(substring(pozn from position('ROZPOR:' in pozn) + 7), ' / (nahrazeno opravou|🛠|[[]|krátká pauza|zkráceno uživatelem|úprava:|zadáno ve Správě|z plánu|STORNO|SUPERSEDED).*$', '')) ELSE '' END AS "ZamPoznamka",
       COALESCE((SELECT string_agg(x, ' / ') FROM regexp_split_to_table(pozn, ' / ') AS x WHERE x NOT LIKE '%ROZPOR:%' AND x NOT LIKE '%🛠%'), '') AS "Poznamka",
       COALESCE(NULLIF(btrim(vpozn), ''), (SELECT string_agg(x, ' / ') FROM regexp_split_to_table(pozn, ' / ') AS x WHERE x LIKE '%🛠%'), '') AS "VedPoznamka",
       CASE WHEN vsch THEN '✓' ELSE '' END            AS "VedSchvaleno",
       CASE WHEN preq THEN '✓' ELSE '' END            AS "Pozadavek",
       to_char(d,'DD.MM.YYYY')                        AS "DatumPripadu",
       EXTRACT(year FROM d)::int                      AS "Rok",
       EXTRACT(month FROM d)::int                     AS "Mesic",
       kind                                           AS "_kind",
       rid                                            AS "_id",
       zak                                            AS "_zak",
       cin_id                                         AS "_cin_id",
       to_char(od_raw,'YYYY-MM-DD')                   AS "_od_d",
       to_char(od_raw,'HH24:MI')                      AS "_od_t",
       CASE WHEN kon_raw IS NULL THEN NULL ELSE to_char(kon_raw,'YYYY-MM-DD') END AS "_kon_d",
       CASE WHEN kon_raw IS NULL THEN NULL ELSE to_char(kon_raw,'HH24:MI') END    AS "_kon_t",
       hod                                            AS "_hod",
       pozn                                           AS "_pozn",
       src                                            AS "_src",
       cz                                             AS "_cz",
       jm                                             AS "_jm",
       COALESCE(vpozn,'')                             AS "_vpozn",
       COALESCE(vsch,false)                           AS "_vsch",
       COALESCE(preq,false)                           AS "_preq", ((position('auto-odhlášení' in COALESCE(pozn,'')) > 0 AND to_char(kon_raw AT TIME ZONE 'Europe/Prague','HH24:MI') = '23:59') OR (kon_raw IS NOT NULL AND (kon_raw AT TIME ZONE 'Europe/Prague')::date <> d) OR (kon_raw IS NULL AND od_raw IS NOT NULL AND d < CURRENT_DATE)) AS "_neodhl"
FROM spolu WHERE d <= CURRENT_DATE
  AND d >= (date_trunc('month', CURRENT_DATE) - INTERVAL '1 month')::date
ORDER BY d DESC, od_ts DESC NULLS LAST
