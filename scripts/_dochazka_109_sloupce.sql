-- ═══════════════════════════════════════════════════════════════════════
-- PŘIPRAVENO, NENASAZENO — čeká na pokyn Peti (21. 7. 2026, Claude-26)
-- Přehled „🏭 Docházka po zakázkách" (uzel 189, jádro dochazka.centrala):
-- sloupce 1:1 s Delphi přehledem 109 v Centrále, v pořadí jak je Peťa vidí
-- v gridu Centrály. VYNECHÁNY na její pokyn: CasBlbost, CasRezie.
-- Data zůstávají naše (tenant.att_*) — sloupce, které u sebe nemáme, jsou
-- prázdné (viz docs/team/dochazka_109_sloupce.md).
-- Spustit přes bridge write (schválí Peťa), pak stačí F5 v ERP — je to jen
-- definice datasetu, žádný deploy kódu.
-- ═══════════════════════════════════════════════════════════════════════

UPDATE fw.data_set
   SET sql_text = $sql$
SELECT e.id                                             AS "ID",
       COALESCE(NULLIF(TRIM(e.project_ref),''), NULLIF(TRIM(w.zakazka_ref),'')) AS "CisloZakazky",
       COALESCE(em.full_name, 'Zam ' || em.cislo_zam)    AS "JmenoPrijmeni",
       em.cislo_zam                                      AS "CisloZam",
       w.cinnost_id                                      AS "DruhCinnosti",
       -- Peťa 21.7.2026: Centrála vede dovolenou/nemoc jako ČINNOST (CinnostText
       -- 'Dovolená', 'Mateřská dovolená'…), ne jako zvláštní sloupec typu. U nás je
       -- výrobní činnost jen u práce, absence nesou typ záznamu → fallback na typ.
       COALESCE(vc.name, et.label)                       AS "CinnostText",
       CASE EXTRACT(dow FROM e.entry_date)
            WHEN 1 THEN 'Po' WHEN 2 THEN 'Ut' WHEN 3 THEN 'St' WHEN 4 THEN 'Ct'
            WHEN 5 THEN 'Pa' WHEN 6 THEN 'So' ELSE 'Ne' END AS "DenVTydnu",
       to_char(e.entry_date,'DD.MM.YYYY') || ' '
         || COALESCE(to_char(e.started_at,'HH24') || ':' || to_char(e.started_at,'MI'),'') AS "CasZacatek",
       CASE WHEN e.ended_at IS NULL THEN NULL
            ELSE to_char(e.ended_at,'DD.MM.YYYY') || ' '
                 || to_char(e.ended_at,'HH24') || ':' || to_char(e.ended_at,'MI') END AS "CasKonec",
       COALESCE(e.break_minutes,0)                       AS "CasPauza",
       NULL::text                                        AS "PozadPomocVed",
       CASE WHEN e.status IN ('approved','locked') THEN 'A' END AS "VedSchvaleno",
       NULL::text                                        AS "SefSchvaleno",
       NULL::text                                        AS "PrevodPrescasu",
       COALESCE(e.note,'')                               AS "ZamPoznamka",
       NULL::text                                        AS "SefMontPoznamka",
       NULL::text                                        AS "VedPoznamka",
       e.hours                                           AS "CasCelkemZakazka",
       NULL::numeric                                     AS "CasCelkemVcRezii",
       CASE WHEN e.is_active THEN 'A' END                AS "PraceAktivni",
       NULL::text                                        AS "Poznamka",
       CASE e.source WHEN 'mobile_app' THEN 'aplikace' WHEN 'tablet' THEN 'tablet'
            WHEN 'manual' THEN 'rucne' WHEN 'ec_import' THEN 'z Centraly'
            WHEN 'cssz_dpn' THEN 'CSSZ' WHEN 'automat' THEN 'automat'
            ELSE COALESCE(e.source,'') END               AS "LoginFrom",
       (SELECT UPPER(g.engagement_type) FROM tenant.engagement g
         WHERE g.employee_id = em.id AND g.tenant_id = 2 AND g.is_current LIMIT 1) AS "SmlouvaAktualni",
       e.source_id                                       AS "IDEventImp",
       NULL::numeric                                     AS "OdmenaZFinanciZak",
       CASE WHEN e.source = 'ec_import' THEN 'A' END     AS "Import",
       to_char(e.entry_date,'DD.MM.YYYY')                AS "DatumPripadu",
       EXTRACT(year FROM e.entry_date)::int              AS "Rok",
       EXTRACT(month FROM e.entry_date)::int             AS "Mesic",
       (SELECT NULLIF(TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')),'')
          FROM public.users u WHERE u.id = e.created_by_id) AS "Autor",
       to_char(e.created_at,'DD.MM.YYYY') || ' '
         || to_char(e.created_at,'HH24') || ':' || to_char(e.created_at,'MI') AS "DatPorizeni",
       to_char(e.updated_at,'DD.MM.YYYY') || ' '
         || to_char(e.updated_at,'HH24') || ':' || to_char(e.updated_at,'MI') AS "DatZmeny",
       NULL::text                                        AS "Zmenil"
FROM tenant.att_entry e
JOIN tenant.att_employee em ON em.id = e.employee_id
LEFT JOIN tenant.att_entry_type et ON et.id = e.entry_type_id
LEFT JOIN LATERAL (
    SELECT w2.zakazka_ref, w2.cinnost_id
    FROM tenant.vyroba_work w2
    WHERE w2.tenant_id = 2 AND w2.user_id = em.user_id AND w2.datum = e.entry_date
      AND (e.started_at IS NULL OR w2.od = e.started_at)
    ORDER BY w2.id LIMIT 1) w ON TRUE
LEFT JOIN tenant.vyroba_cinnost vc ON vc.id = w.cinnost_id
WHERE e.tenant_id = 2
  AND COALESCE(e.status,'') <> 'superseded'
  AND COALESCE(e.source,'') <> 'plan_ec'
  AND e.entry_date <= CURRENT_DATE
ORDER BY e.entry_date DESC, e.started_at DESC NULLS LAST, em.cislo_zam
$sql$,
       updated_at = now()
 WHERE code = 'dochazka.zakazky_vse_list';

-- Sesterský přehled „⏭ Naplánovaná budoucnost" (uzel 190) — stejné sloupce,
-- jen opačné období a řazení.
UPDATE fw.data_set
   SET sql_text = replace(
         replace((SELECT sql_text FROM fw.data_set WHERE code='dochazka.zakazky_vse_list'),
                 'AND e.entry_date <= CURRENT_DATE', 'AND e.entry_date > CURRENT_DATE'),
         'ORDER BY e.entry_date DESC', 'ORDER BY e.entry_date ASC'),
       updated_at = now()
 WHERE code = 'dochazka.zakazky_budoucnost_list';
