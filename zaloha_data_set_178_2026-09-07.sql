
 WITH wd AS (
   SELECT day, row_number() OVER (ORDER BY day) AS rn
   FROM tenant.att_calendar_day WHERE tenant_id=2 AND is_workday=true
 ), a_days AS (
   SELECT e.employee_id, em.full_name, em.cislo_zam::text AS cislo_zam,
          et.code AS typ_code, et.label AS typ_label, e.entry_date AS d, COALESCE(e.ec_druh,0) AS ec_druh,
          e.note, e.vedouci_poznamka, COALESCE(e.ved_schvaleno,false) AS schvaleno,
          e.created_at, e.created_by_id, e.source, e.id AS entry_id,
          zr.id AS zad_id, zr.datum_od AS zad_od, zr.datum_do AS zad_do,
          e.started_at, e.ended_at,
          COALESCE(e.hours,0)::numeric AS hod,
          COALESCE(NULLIF(fd.fond,0), 8.0) AS fond,
          CASE WHEN et.code='homeoffice' THEN 1
               WHEN COALESCE(e.hours,0) > 0
               THEN round(e.hours::numeric / COALESCE(NULLIF(fd.fond,0), 8.0), 4)
               ELSE 1 END AS dny,
          -- Peta 25.8.2026 (zadano), doplneno 27.8.2026 (C26). SEST UDAJU, ktere
          -- se dosud tlacily do jedineho sloupce Autor a prepisovaly se navzajem.
          -- AUTOR = kdo zaznam poridil. Nikdy se nemeni.
          --  * den vznikly SCHVALENIM zadosti z appky -> autor je ZADATEL.
          --    Dosud tu byl schvalovatel, protoze denni zaznamy vznikaji az ve
          --    chvili schvaleni a zaklada je ten, kdo schvaluje (overeno 27.8.2026
          --    na datech - 67 dnu Petra u 18 ruznych lidi, 54 Dusan u 16).
          --  * absence zadana ve Sprave dochazky -> autor je ten, kdo ji zadal.
          --    Pozna se podle status_text, ktery zaklada /app/dochazka-abs/new.
          --  * opraveny zaznam -> autor PUVODNIHO radku. Oprava zaklada NOVY
          --    radek (puvodni zustava schovany kvuli historii), takze by se sem
          --    jinak dostal opravar. Vazbu na puvodni radek nese historie oprav.
          CASE
            WHEN zr.id IS NOT NULL
                 AND left(COALESCE(zr.status_text,''),16) = 'Zadáno ve Správě'
                 THEN zr.decided_by_user_id
            WHEN zr.id IS NOT NULL THEN COALESCE(zr.created_by_user_id, zr.user_id)
            ELSE COALESCE(pe.created_by_id, e.created_by_id)
          END AS autor_id,
          -- KDE BYLO PORIZENO. Den ze schvalene zadosti ma sice source='absence',
          -- ale poridil ho clovek v appce - proto se ridi nejdriv zadosti a teprve
          -- pak zdrojem radku.
          CASE
            WHEN zr.id IS NOT NULL
                 AND left(COALESCE(zr.status_text,''),16) = 'Zadáno ve Správě'
                 THEN 'Správa / ERP'
            WHEN zr.id IS NOT NULL THEN 'appka'
            WHEN e.source IN ('mobile_app','tablet','notif_confirm') THEN 'appka'
            WHEN e.source IN ('absence','manual_fix') THEN 'Správa / ERP'
            WHEN e.source IN ('ec_import','plan_ec','manual','import') THEN 'Centrála'
            WHEN e.source = 'cssz_dpn' THEN 'ČSSZ'
            WHEN e.source = 'automat' THEN 'automat'
            ELSE COALESCE(e.source,'')
          END AS odkud,
          -- KDO A KDY SCHVALIL. U dne, ktery vznikl ze zadosti, to nese sama
          -- zadost (decided_by_user_id / decided_at). U dne, kde nekdo zaskrtl
          -- fajfku primo v prehledu, se dosud neuklada nic - tam zustane prazdno,
          -- dokud nebudou sloupce ved_schvaleno_kym / ved_schvaleno_kdy.
          CASE WHEN zr.id IS NOT NULL AND COALESCE(zr.stav,'')='approved'
               THEN COALESCE(e.ved_schvaleno_kym, zr.decided_by_user_id) ELSE e.ved_schvaleno_kym END AS schvalil_id,
          CASE WHEN zr.id IS NOT NULL AND COALESCE(zr.stav,'')='approved'
               THEN COALESCE(e.ved_schvaleno_kdy, zr.decided_at) ELSE e.ved_schvaleno_kdy END AS schvalil_kdy,
          -- KDO A KDY ZMENIL - posledni zmena z historie oprav (tenant.att_audit).
          au.zmenil_id, au.zmeneno
   FROM tenant.att_entry e
   JOIN tenant.att_employee em ON em.id=e.employee_id AND em.tenant_id=2
   JOIN tenant.att_entry_type et ON et.id=e.entry_type_id
   LEFT JOIN LATERAL (
     SELECT round(g.uvazek_tyden_h / NULLIF(COALESCE(wm.dny_v_tydnu,5),0), 2) AS fond
     FROM tenant.engagement g
     LEFT JOIN tenant.work_mode wm ON wm.id=g.work_mode_id
     WHERE g.employee_id=e.employee_id AND g.tenant_id=2 AND g.uvazek_tyden_h IS NOT NULL
       AND g.valid_from <= e.entry_date AND (g.valid_to IS NULL OR g.valid_to >= e.entry_date)
     ORDER BY g.valid_from DESC, g.is_current DESC, g.id DESC LIMIT 1
   ) fd ON true
   LEFT JOIN tenant.att_absence_request zr ON zr.id = e.source_id AND zr.tenant_id = 2
   LEFT JOIN LATERAL (
     SELECT a2.actor_user_id AS zmenil_id, a2.created_at AS zmeneno,
            substring(a2.detail from 'původní #([0-9]+)') AS puv_id
     FROM tenant.att_audit a2
     WHERE a2.tenant_id=2 AND a2.entry_id=e.id
       AND a2.action IN ('fix','edit','move','restore')
     ORDER BY a2.id DESC LIMIT 1
   ) au ON true
   LEFT JOIN tenant.att_entry pe ON pe.id = CAST(au.puv_id AS bigint) AND pe.tenant_id = 2
   WHERE e.tenant_id=2 AND COALESCE(e.status,'') NOT IN ('superseded','announced')
     -- Peta 19.8.2026: HOME OFFICE je DVOJI VEC a kazda patri jinam.
     --  (a) OHLASENI "budu na HO" (zadava se 8-16) = jen informace, ze clovek nebude
     --      v kancelari. Nikde se nepocita. Patri SEM do Spravy dochazky, sede.
     --  (b) REALNA CINNOST HO = co si clovek skutecne napichal, kdyz doma pracoval.
     --      To je prace - patri do Dochazky new a do Oprav, editovatelne, pocita se.
     --      Do Spravy dochazky NEPATRI, tady se plan a zadosti, ne odpracovany cas.
     -- Rozlisujeme podle puvodu (Peta potvrdila 19.8.2026) - co vzniklo ZE ZADOSTI
     -- (nebo z planu Centraly) je ohlaseni; co je PICHNUTE je prace.
     AND (et.category='absence'
          OR (et.code='homeoffice'
              AND (COALESCE(e.source_system,'')='absence_req' OR e.source='plan_ec')))
 ), a_isl AS (
   -- Peta 12.8.2026: absence se NIKDY neslepuje pres konec mesice. Nemoc 22.7.-31.7.
   -- a 1.8.-10.8. jsou DVE samostatne zadosti, ale prehled je ukazoval jako jeden
   -- radek 22.7.-10.8. V Centrale se to vzdy delilo po mesicich (plati pro vsechny
   -- druhy - nemoc, dovolena, materska...). Proto je v ostrovcich i mesic.
   -- Peta 17.8.2026: v jednom radku smi byt jen dny se STEJNYM poctem hodin za den.
   -- 4 cele dny + pulden = DVA radky, jako v Centrale (prehled 5518: jeden event = jeden radek).
   SELECT a.*, (wd.rn - row_number() OVER (PARTITION BY a.employee_id,a.typ_code,date_trunc('month',a.d),a.hod,a.zad_id,a.ec_druh ORDER BY a.d)) AS grp
   FROM a_days a LEFT JOIN wd ON wd.day=a.d
 ), a_period AS (
   SELECT employee_id, max(full_name) full_name, max(cislo_zam) cislo_zam,
          typ_code,
          -- Peta 4.9.2026: POPISEK ZUSTAVA "Dovolena" i u dnu, ktere uz jsou dopoctene
          -- jako dovolena navic. Ve Sprave se zada dovolena a nic jineho - rozdeleni na
          -- radnou a navic je az dopocet kaskady a patri do Dochazky new. Peta -
          -- "ve sprave to nemuze byt jako dovolena navic".
          -- ec_druh se tu ale NESE DAL, aby se dva pulden radky (4 h radna + 4 h navic)
          -- neslepily do jednoho a neprisly o sebe v odstranovaci duplicit nize.
          max(typ_label) typ_label,
          min(ec_druh) ec_druh, min(d) d_min, max(d) d_max, zad_id,
          -- Peta 12.8.2026: zacatek a konec se berou ze ZADOSTI (orezane na mesic),
          -- ne z pracovnich dnu. Nemoc 1.8.-10.8. zacina v SOBOTU 1.8., ale denni
          -- zaznamy vznikaji az od pondeli 3.8. V prehledu musi byt 1.8. - nemoc
          -- bezi kalendarni dny. Kdyz zadost neni (rucne v Centrale), plati dny.
          CASE WHEN min(COALESCE(zad_od,d)) IS NOT NULL
               THEN GREATEST(min(COALESCE(zad_od,d)), date_trunc('month', min(d))::date)
               ELSE min(d) END odd,
          CASE WHEN max(COALESCE(zad_do,d)) IS NOT NULL
               THEN LEAST(max(COALESCE(zad_do,d)), (date_trunc('month', min(d)) + interval '1 month' - interval '1 day')::date)
               ELSE max(d) END dokon,
          -- ZRUSENO 25.8.2026 (Peta + Claude-26). Prehled uz cas NEDOPOCITAVA. Absence se od
          -- 18.8.2026 vede BEZ CASU (rozhodla Peta) - umely ramec delal falesne prekryvy
          -- s pichnutou dochazkou a v prehledu se ukazoval cas, ktery v datech vubec neni.
          -- Skutecny cas ma jen Lekar (lezi uvnitr pracovniho dne). Kdyz cas neni, zustane prazdno.
          min(started_at) odd_ts,
          max(ended_at) dokon_ts,
          round(sum(dny), 2) pocet_dni,
          round(max(hod), 2) hodin_den,
          max(fond) fond_den,
          count(DISTINCT d)::int dnu_poctem,
          bool_or(schvaleno) schvaleno, min(created_at) created_at,
          max(source) src, max(created_by_id) created_by_id,
          string_agg(DISTINCT entry_id::text, ',') ids, 'dny'::varchar radek_typ,
          string_agg(DISTINCT nullif(note,''),'; ') zampozn,
          string_agg(DISTINCT nullif(vedouci_poznamka,''),'; ') vedpozn,
          -- Sest novych udaju za cely slepeny blok. U "kdo zmenil" se bere ten,
          -- kdo delal POSLEDNI zmenu, ne nejvyssi id.
          max(autor_id) autor_id,
          max(odkud) odkud,
          max(schvalil_id) schvalil_id,
          max(schvalil_kdy) schvalil_kdy,
          (array_agg(zmenil_id ORDER BY zmeneno DESC NULLS LAST))[1] zmenil_id,
          max(zmeneno) zmeneno
   FROM a_isl GROUP BY employee_id, typ_code, date_trunc('month', d), hod, zad_id, grp, ec_druh
 ), b_period AS (
   SELECT r.employee_id, em.full_name, em.cislo_zam::text cislo_zam,
          r.typ typ_code,
          COALESCE((SELECT label FROM tenant.att_entry_type ty WHERE ty.code=r.typ LIMIT 1), r.typ) typ_label,
          r.datum_od odd, r.datum_do dokon,
          NULL::timestamptz odd_ts, NULL::timestamptz dokon_ts,
          round((SELECT count(*) FROM tenant.att_calendar_day c WHERE c.tenant_id=2 AND c.is_workday AND c.day BETWEEN r.datum_od AND r.datum_do)::numeric
               * COALESCE(r.hours_per_day,8)::numeric / COALESCE(NULLIF(fb.fond,0), 8.0), 2) pocet_dni,
          round(COALESCE(r.hours_per_day,8)::numeric, 2) hodin_den,
          COALESCE(NULLIF(fb.fond,0), 8.0) fond_den,
          (SELECT count(*) FROM tenant.att_calendar_day c WHERE c.tenant_id=2 AND c.is_workday AND c.day BETWEEN r.datum_od AND r.datum_do)::int dnu_poctem,
          (r.stav='approved') schvaleno, r.created_at,
          'app'::varchar src, r.user_id created_by_id, r.note zampozn, NULL::text vedpozn,
          r.id::text ids, 'zadost'::varchar radek_typ,
          -- Zadost, ktera je v prehledu videt, je vzdy nematerializovana = z appky
          -- (co se zada ve Sprave dochazky, se materializuje hned a zobrazi se uz
          -- jako den, ne jako zadost - overeno v /app/dochazka-abs/new 27.8.2026).
          COALESCE(r.created_by_user_id, r.user_id) autor_id,
          'appka'::varchar odkud,
          CASE WHEN r.stav='approved' THEN r.decided_by_user_id END schvalil_id,
          CASE WHEN r.stav='approved' THEN r.decided_at END schvalil_kdy,
          ar.zmenil_id, ar.zmeneno
   FROM tenant.att_absence_request r
   JOIN tenant.att_employee em ON em.id=r.employee_id AND em.tenant_id=2
   LEFT JOIN LATERAL (
     SELECT round(g.uvazek_tyden_h / NULLIF(COALESCE(wm.dny_v_tydnu,5),0), 2) AS fond
     FROM tenant.engagement g
     LEFT JOIN tenant.work_mode wm ON wm.id=g.work_mode_id
     WHERE g.employee_id=r.employee_id AND g.tenant_id=2 AND g.uvazek_tyden_h IS NOT NULL
       AND g.valid_from <= r.datum_od AND (g.valid_to IS NULL OR g.valid_to >= r.datum_od)
     ORDER BY g.valid_from DESC, g.is_current DESC, g.id DESC LIMIT 1
   ) fb ON true
   LEFT JOIN LATERAL (
     SELECT a3.actor_user_id AS zmenil_id, a3.created_at AS zmeneno
     FROM tenant.att_audit a3
     WHERE a3.tenant_id=2 AND a3.action='absence_edit'
       AND substring(a3.detail from 'žádosti #([0-9]+)') = CAST(r.id AS text)
     ORDER BY a3.id DESC LIMIT 1
   ) ar ON true
   WHERE r.tenant_id=2 AND COALESCE(r.materialized,false)=false
     -- Peta 26.8.2026: rozhodnuta zadost uz nema viset mezi cekajicimi. Priznak
     -- materialized se z principu NIKDY neprepne u verdiktu info (neni to schvaleni
     -- ani zamitnuti, nic se nezapise) a u schvaleneho home office, ktery se do
     -- dochazky zamerne nematerializuje (att_absence_decide, Peta 12.8.2026 -
     -- HO neni cerpane volno, clovek picha svuj realny cas). Proto se vyrazuji zvlast.
     AND COALESCE(r.stav,'') NOT IN ('cancelled','rejected','info')
     AND NOT (r.stav='approved' AND COALESCE(r.typ,'')='homeoffice')
 ), allp AS (
   -- Peta 4.9.2026: datum ze ZADOSTI se drzi jen tehdy, kdyz z te zadosti vysel
   -- JEDEN radek. Jakmile se rozpadne na vic (pulden, dojity narok), ukazuje kazdy
   -- radek SVOJE dny - jinak meli vsichni stejne od-do, sumace lhala ("3.-5.8. = 1 D")
   -- a odstranovac duplicit nize je pak povazoval za tentyz radek a dva ze tri zahodil.
   SELECT employee_id,full_name,cislo_zam,typ_code,typ_label,
          CASE WHEN count(*) OVER (PARTITION BY employee_id, zad_id, date_trunc('month', d_min)) > 1
               THEN d_min ELSE odd END AS odd,
          CASE WHEN count(*) OVER (PARTITION BY employee_id, zad_id, date_trunc('month', d_min)) > 1
               THEN d_max ELSE dokon END AS dokon,
          odd_ts,dokon_ts,pocet_dni,hodin_den,fond_den,dnu_poctem,schvaleno,created_at,src,created_by_id,zampozn,vedpozn,ids,radek_typ,autor_id,odkud,schvalil_id,schvalil_kdy,zmenil_id,zmeneno,ec_druh FROM a_period
   UNION ALL
   SELECT employee_id,full_name,cislo_zam,typ_code,typ_label,odd,dokon,odd_ts,dokon_ts,pocet_dni,hodin_den,fond_den,dnu_poctem,schvaleno,created_at,src,created_by_id,zampozn,vedpozn,ids,radek_typ,autor_id,odkud,schvalil_id,schvalil_kdy,zmenil_id,zmeneno,0 AS ec_druh FROM b_period
 ), dedup AS (
   SELECT *, row_number() OVER (
     -- Peta 4.9.2026: do klice patri i ec_druh. Bez nej maji dva pulden radky
     -- ze 4. 8. (4 h radna + 4 h navic) stejny typ_code, stejny popisek i stejne
     -- od-do, odstranovac duplicit je povazoval za tentyz radek a jeden zahodil.
     PARTITION BY employee_id, typ_code, ec_druh, odd, dokon
     ORDER BY CASE WHEN src='plan_ec' THEN 2 ELSE 1 END, created_at) AS rnk
   FROM allp
 )
 SELECT CASE WHEN schvaleno THEN '✓' ELSE '' END AS "Schvaleno", typ_code AS "DruhKod",
   cislo_zam AS "CisloZam", full_name AS "JmenoPrijmeni", typ_label AS "Druh",
   COALESCE(to_char(odd_ts,'DD.MM.YYYY HH24:MI'), to_char(odd,'DD.MM.YYYY')) AS "DatumOd",
   COALESCE(to_char(dokon_ts,'DD.MM.YYYY HH24:MI'), to_char(dokon,'DD.MM.YYYY')) AS "DatumDo",
   pocet_dni AS "PocetDni",
   CASE
     WHEN COALESCE(hodin_den,0) <= 0 THEN dnu_poctem::text || ' D'
     WHEN odd = dokon THEN replace(to_char(hodin_den,'FM9990.00'),'.',',') || ' Hod'
     WHEN hodin_den >= COALESCE(fond_den,8) - 0.01 THEN dnu_poctem::text || ' D'
     ELSE dnu_poctem::text || 'x ' || replace(to_char(hodin_den,'FM9990.00'),'.',',') || ' Hod'
   END AS "PocetHodCiDni",
   hodin_den AS "HodinDen",
   CASE WHEN radek_typ='zadost' THEN 'Z:'||ids ELSE 'D:'||ids END AS "RadekId",
   CASE WHEN radek_typ='zadost' THEN 'žádost z appky' WHEN src='plan_ec' THEN 'plán z Centrály' WHEN src='ec_import' THEN 'import z Centrály' WHEN src='cssz_dpn' THEN 'neschopenka ČSSZ' WHEN src='mobile_app' THEN 'appka' WHEN src='manual' THEN 'ručně v Centrále' WHEN src='absence' THEN 'schválená žádost' WHEN src='manual_fix' THEN 'ruční oprava' ELSE COALESCE(src,'?') END AS "Zdroj",
   -- AUTOR = kdo poridil. Uz se neprepisuje schvalovatelem ani opravarem.
   CASE WHEN dedup.autor_id IS NOT NULL
        THEN COALESCE((SELECT u.first_name||' '||u.last_name FROM public.users u WHERE u.id=dedup.autor_id),'')
        WHEN src='plan_ec' THEN 'Centrála'
        WHEN src='app' THEN 'appka'
        ELSE '' END AS "Autor",
   COALESCE(odkud,'') AS "Odkud",
   to_char(created_at,'DD.MM.YYYY') AS "DatPorizeni",
   COALESCE((SELECT u.first_name||' '||u.last_name FROM public.users u WHERE u.id=dedup.schvalil_id),'') AS "KdoSchvalil",
   to_char(schvalil_kdy,'DD.MM.YYYY HH24:MI') AS "KdySchvalil",
   COALESCE((SELECT u.first_name||' '||u.last_name FROM public.users u WHERE u.id=dedup.zmenil_id),'') AS "KdoZmenil",
   to_char(zmeneno,'DD.MM.YYYY HH24:MI') AS "KdyZmenil",
   COALESCE(zampozn,'') AS "ZamPoznamka", COALESCE(vedpozn,'') AS "VedPoznamka",
   (SELECT UPPER(g.engagement_type) FROM tenant.engagement g WHERE g.employee_id=dedup.employee_id AND g.tenant_id=2 AND g.is_current LIMIT 1) AS "Smlouva"
 FROM dedup WHERE rnk=1 ORDER BY odd DESC, full_name
