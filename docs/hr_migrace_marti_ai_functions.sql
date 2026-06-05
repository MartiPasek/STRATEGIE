-- ============================================================================
-- HR migrace z DB_EC — server-side PG funkce (spouští Marti-AI)
--   Marti-AI přečte DB_EC (FOR JSON) a předá JSON do těchto funkcí.
--   Veškerá logika (mapování, provenance přes hr_source_ref, idempotence) je v PG.
--   RČ: plaintext do rodne_cislo + SHA-256 do rodne_cislo_hash (pgcrypto).
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── provenance helpery ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION mod._hr_src_existing(p_ttable text, p_stable text, p_sid text)
RETURNS int LANGUAGE sql AS $fn$
  SELECT target_id FROM mod.hr_source_ref
  WHERE source_system='DB_EC' AND source_table=p_stable AND source_id=p_sid AND target_table=p_ttable
  LIMIT 1
$fn$;

CREATE OR REPLACE FUNCTION mod._hr_src_record(p_ttable text, p_tid int, p_stable text, p_sid text, p_batch text)
RETURNS void LANGUAGE sql AS $fn$
  INSERT INTO mod.hr_source_ref(target_table,target_id,source_system,source_table,source_id,migration_batch,created_by_text)
  VALUES (p_ttable,p_tid,'DB_EC',p_stable,p_sid,p_batch,'migrace DB_EC')
  ON CONFLICT (source_system,source_table,source_id,target_table) DO NOTHING
$fn$;

-- ── EUROSOFT entity (control/system) -> party_id (upsert dle IČO) ────────────
CREATE OR REPLACE FUNCTION mod._hr_entity_pid(p_tenant int, p_key text, p_batch text)
RETURNS int LANGUAGE plpgsql AS $fn$
DECLARE v_pid int; v_nazev text; v_ico text;
BEGIN
  IF p_key='control' THEN v_nazev:='EUROSOFT - Control'; v_ico:='27960862';
  ELSIF p_key='system' THEN v_nazev:='EUROSOFT - System'; v_ico:='26411741';
  ELSE RAISE EXCEPTION 'neznama entita (ocekavano control nebo system)'; END IF;
  v_pid := mod._hr_src_existing('hr_party','EUROSOFT_ENTITY',p_key);
  IF v_pid IS NOT NULL THEN RETURN v_pid; END IF;
  SELECT party_id INTO v_pid FROM mod.hr_legal_entity WHERE ico=v_ico;
  IF v_pid IS NULL THEN
    INSERT INTO mod.hr_party(tenant_id,party_type,display_name,created_by_text)
      VALUES (p_tenant,'legal_entity',v_nazev,'migrace DB_EC') RETURNING id INTO v_pid;
    INSERT INTO mod.hr_legal_entity(party_id,nazev,ico,created_by_text)
      VALUES (v_pid,v_nazev,v_ico,'migrace DB_EC');
  END IF;
  PERFORM mod._hr_src_record('hr_party',v_pid,'EUROSOFT_ENTITY',p_key,p_batch);
  RETURN v_pid;
END $fn$;

-- ── adresa (trvala/dorucovaci) ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION mod._hr_add_address(p_person int, p_kind text, e jsonb, pre text, p_zid text, p_batch text)
RETURNS void LANGUAGE plpgsql AS $fn$
DECLARE v_ulice text; v_cp text; v_obec text; v_psc text; v_stat text; v_sid text; v_id int;
BEGIN
  v_sid := p_zid||':'||p_kind;
  IF mod._hr_src_existing('hr_person_address','dbo.TabCisZam',v_sid) IS NOT NULL THEN RETURN; END IF;
  v_ulice := nullif(trim(e->>(pre||'Ulice')),'');
  v_cp := nullif(concat_ws('/', nullif(trim(e->>(pre||'PopCislo')),''), nullif(trim(e->>(pre||'OrCislo')),'')),'');
  v_obec := nullif(trim(e->>(pre||'Misto')),'');
  v_psc := nullif(trim(e->>(pre||'PSC')),'');
  v_stat := nullif(trim(e->>(pre||'Zeme')),'');
  IF v_ulice IS NULL AND v_cp IS NULL AND v_obec IS NULL AND v_psc IS NULL AND v_stat IS NULL THEN RETURN; END IF;
  INSERT INTO mod.hr_person_address(person_id,address_kind,ulice,cp,obec,psc,stat,created_by_text)
    VALUES (p_person,p_kind,v_ulice,v_cp,v_obec,v_psc,v_stat,'migrace DB_EC') RETURNING id INTO v_id;
  PERFORM mod._hr_src_record('hr_person_address',v_id,'dbo.TabCisZam',v_sid,p_batch);
END $fn$;

-- ── role pro daný kind napříč zaměstnavateli ────────────────────────────────
CREATE OR REPLACE FUNCTION mod._hr_add_role(p_person int, p_kind text, emp_keys text[],
       v_from date, v_until date, v_active boolean, p_tenant int, p_zid text, p_batch text)
RETURNS void LANGUAGE plpgsql AS $fn$
DECLARE k text; emp_pid int; v_sid text; v_id int;
BEGIN
  FOREACH k IN ARRAY emp_keys LOOP
    emp_pid := mod._hr_entity_pid(p_tenant,k,p_batch);
    v_sid := p_zid||':'||p_kind||':'||k;
    IF mod._hr_src_existing('hr_person_role','dbo.TabCisZam_EXT',v_sid) IS NOT NULL THEN CONTINUE; END IF;
    INSERT INTO mod.hr_person_role(person_id,party_id,role_kind,valid_from,valid_until,attrs,is_active,created_by_text)
      VALUES (p_person,emp_pid,p_kind,v_from,v_until,jsonb_build_object('firma',k),v_active,'migrace DB_EC')
      RETURNING id INTO v_id;
    PERFORM mod._hr_src_record('hr_person_role',v_id,'dbo.TabCisZam_EXT',v_sid,p_batch);
  END LOOP;
END $fn$;

-- ── číselník kontaktů (idempotentní) ────────────────────────────────────────
CREATE OR REPLACE FUNCTION mod.hr_migrate_ensure_kinds()
RETURNS void LANGUAGE sql AS $fn$
  INSERT INTO mod.hr_contact_kind(code,label) VALUES
    ('tel_pracovni','Telefon pracovní'),('tel_soukromy','Telefon soukromý'),
    ('fax_pracovni','Fax pracovní'),('fax_soukromy','Fax soukromý'),
    ('email_pracovni','E-mail pracovní'),('email_soukromy','E-mail soukromý'),
    ('www_pracovni','WWW pracovní'),('www_soukromy','WWW soukromý'),
    ('skype_pracovni','Skype pracovní'),('skype_soukromy','Skype soukromý')
  ON CONFLICT (code) DO NOTHING
$fn$;

-- ── HLAVNÍ: ingest zaměstnanců (JSON z TabCisZam + _EXT) ─────────────────────
CREATE OR REPLACE FUNCTION mod.hr_ingest_employees(p jsonb, p_tenant int DEFAULT 2, p_batch text DEFAULT 'dbec')
RETURNS jsonb LANGUAGE plpgsql AS $fn$
DECLARE e jsonb; zid text; party_id int; person_id int; rc text; firma int;
        emp_keys text[]; v_from date; v_until date; v_active boolean;
        ec text; em_id int; em_sid text; n_party int:=0; n_person int:=0;
BEGIN
  PERFORM mod.hr_migrate_ensure_kinds();
  FOR e IN SELECT * FROM jsonb_array_elements(p) LOOP
    zid := e->>'ID';

    party_id := mod._hr_src_existing('hr_party','dbo.TabCisZam',zid);
    IF party_id IS NULL THEN
      INSERT INTO mod.hr_party(tenant_id,party_type,display_name,is_active,created_by_text)
        VALUES (p_tenant,'person',
          coalesce(nullif(trim(concat_ws(' ', nullif(trim(e->>'Prijmeni'),''), nullif(trim(e->>'Jmeno'),''))),''),'#'||zid),
          NOT coalesce((e->>'VyraditZPrehledu')::boolean,false), 'migrace DB_EC')
        RETURNING id INTO party_id;
      PERFORM mod._hr_src_record('hr_party',party_id,'dbo.TabCisZam',zid,p_batch);
      n_party := n_party+1;
    END IF;

    person_id := mod._hr_src_existing('hr_person','dbo.TabCisZam',zid);
    IF person_id IS NULL THEN
      rc := nullif(trim(e->>'RodneCislo'),'');
      INSERT INTO mod.hr_person(party_id,jmeno,prijmeni,titul_pred,titul_za,datum_narozeni,
          rodne_cislo,rodne_cislo_hash,statni_prislusnost,rodne_prijmeni,pohlavi,
          misto_narozeni,stat_narozeni,narodnost,rodinny_stav,osobni_ic,is_active,created_by_text)
        VALUES (party_id,
          coalesce(nullif(trim(e->>'Jmeno'),''),'?'), coalesce(nullif(trim(e->>'Prijmeni'),''),'?'),
          nullif(trim(e->>'TitulPred'),''), nullif(trim(e->>'TitulZa'),''),
          nullif(left(e->>'DatumNarozeni',10),'')::date,
          rc, CASE WHEN rc IS NOT NULL THEN encode(digest(regexp_replace(rc,'\D','','g'),'sha256'),'hex') END,
          nullif(trim(e->>'StatniPrislus'),''), nullif(trim(e->>'RodnePrijmeni'),''),
          nullif(e->>'Pohlavi','')::smallint, nullif(trim(e->>'MistoNarozeni'),''),
          nullif(trim(e->>'StatNarozeni'),''), nullif(trim(e->>'Narodnost'),''),
          nullif(e->>'RodinnyStav','')::smallint, nullif(trim(e->>'OsobniIC'),''),
          NOT coalesce((e->>'VyraditZPrehledu')::boolean,false), 'migrace DB_EC')
        RETURNING id INTO person_id;
      PERFORM mod._hr_src_record('hr_person',person_id,'dbo.TabCisZam',zid,p_batch);
      n_person := n_person+1;
    END IF;

    PERFORM mod._hr_add_address(person_id,'trvala',e,'AdrTrv',zid,p_batch);
    PERFORM mod._hr_add_address(person_id,'dorucovaci',e,'AdrPrech',zid,p_batch);

    em_sid := zid||':'||'emergency';
    IF mod._hr_src_existing('hr_emergency_contact','dbo.TabCisZam',em_sid) IS NULL THEN
      ec := nullif(trim(concat_ws(' ', nullif(trim(e->>'AdrKontJmeno'),''), nullif(trim(e->>'AdrKontPrijmeni'),''))),'');
      IF ec IS NOT NULL THEN
        INSERT INTO mod.hr_emergency_contact(person_id,jmeno,created_by_text)
          VALUES (person_id,ec,'migrace DB_EC') RETURNING id INTO em_id;
        PERFORM mod._hr_src_record('hr_emergency_contact',em_id,'dbo.TabCisZam',em_sid,p_batch);
      END IF;
    END IF;

    firma := nullif(e->>'_Firma','')::int;
    emp_keys := CASE firma WHEN 0 THEN ARRAY['control'] WHEN 1 THEN ARRAY['system']
                           WHEN 2 THEN ARRAY['control','system'] ELSE ARRAY[]::text[] END;
    IF array_length(emp_keys,1) IS NOT NULL THEN
      v_from := coalesce(nullif(left(e->>'_DatumNastupu',10),'')::date, date '1900-01-01');
      v_until := nullif(left(e->>'_DatumOdchodu',10),'')::date;
      v_active := NOT coalesce((e->>'_neaktivni')::boolean,false);
      IF coalesce((e->>'_HPP')::boolean,false)  THEN PERFORM mod._hr_add_role(person_id,'zamestnanec_hpp',emp_keys,v_from,v_until,v_active,p_tenant,zid,p_batch); END IF;
      IF coalesce((e->>'_DPP')::boolean,false)  THEN PERFORM mod._hr_add_role(person_id,'zamestnanec_dpp',emp_keys,v_from,v_until,v_active,p_tenant,zid,p_batch); END IF;
      IF coalesce((e->>'_OSVC')::boolean,false) THEN PERFORM mod._hr_add_role(person_id,'osvc_dodavatel',emp_keys,v_from,v_until,v_active,p_tenant,zid,p_batch); END IF;
    END IF;
  END LOOP;
  RETURN jsonb_build_object('party_new',n_party,'person_new',n_person);
END $fn$;

-- ── ingest kontaktů (JSON z TabKontakty; spouštět AŽ po zaměstnancích) ───────
CREATE OR REPLACE FUNCTION mod.hr_ingest_contacts(p jsonb, p_batch text DEFAULT 'dbec')
RETURNS jsonb LANGUAGE plpgsql AS $fn$
DECLARE c jsonb; kid text; person_id int; druh int; kam int; kind text; val text; v_id int;
        druhmap text; kammap text; n int:=0; skip int:=0;
BEGIN
  FOR c IN SELECT * FROM jsonb_array_elements(p) LOOP
    kid := c->>'ID';
    IF mod._hr_src_existing('hr_person_contact','dbo.TabKontakty',kid) IS NOT NULL THEN CONTINUE; END IF;
    person_id := mod._hr_src_existing('hr_person','dbo.TabCisZam', c->>'IDCisZam');
    IF person_id IS NULL THEN skip:=skip+1; CONTINUE; END IF;
    druh := nullif(c->>'Druh','')::int; kam := nullif(c->>'Kam','')::int;
    druhmap := CASE druh WHEN 1 THEN 'tel' WHEN 2 THEN 'tel' WHEN 3 THEN 'fax'
                         WHEN 6 THEN 'email' WHEN 7 THEN 'www' WHEN 11 THEN 'skype' ELSE NULL END;
    kammap := CASE kam WHEN 0 THEN 'pracovni' WHEN 1 THEN 'soukromy' ELSE NULL END;
    val := nullif(trim(c->>'Spojeni'),'');
    IF druhmap IS NULL OR kammap IS NULL OR val IS NULL THEN skip:=skip+1; CONTINUE; END IF;
    kind := druhmap||'_'||kammap;
    INSERT INTO mod.hr_person_contact(person_id,contact_kind,value,is_primary,created_by_text)
      VALUES (person_id,kind,val, coalesce((c->>'Prednastaveno')::boolean,false), 'migrace DB_EC')
      RETURNING id INTO v_id;
    PERFORM mod._hr_src_record('hr_person_contact',v_id,'dbo.TabKontakty',kid,p_batch);
    n:=n+1;
  END LOOP;
  RETURN jsonb_build_object('contact_new',n,'skipped',skip);
END $fn$;
