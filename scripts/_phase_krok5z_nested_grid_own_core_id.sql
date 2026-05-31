-- ============================================================================
-- Krok 5.Z (31.5.2026) — Nested grid dostane VLASTNÍ core_id (72 → 79/80)
-- ============================================================================
-- Marti: "comp_def musi byt provazana na master core_id daneho hlavniho
-- prehledu. Update core_id 72 -> 79 (Akce) a 80 (Osoby)."
--
-- Blokuje trigger comp_def_inherit_core_id (dite dedi core_id parenta).
-- ÚPRAVA: výjimka pro grid_modern — nested grid (embedded master-detail) smí
-- mít vlastní core_id (svůj master přehled), ostatní typy dál dědí. Backward
-- compat: grid_modern s NULL core_id se pořád auto-zdědí.
--
-- DVĚ ČÁSTI — spustit ODDĚLENĚ (DBeaver $ delimiter gotcha):
--   ČÁST 1: CREATE OR REPLACE FUNCTION → highlight celé + Alt+X (jako 1 stmt)
--   ČÁST 2: UPDATE + verify → spustit zvlášť
-- Marti-AI session (db_owner fw).
-- ============================================================================

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ ČÁST 1 — uprav trigger funkci (highlight CELÉ + Alt+X)                    ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION fw.comp_def_inherit_core_id()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  parent_core_id BIGINT;
  new_type_code  TEXT;
BEGIN
  IF NEW.parent_comp_def_id IS NULL THEN
    IF NEW.core_id IS NULL THEN
      RAISE EXCEPTION 'Root komponenta (parent_comp_def_id IS NULL) musí mít core_id explicitně set';
    END IF;
    RETURN NEW;
  END IF;

  SELECT core_id INTO parent_core_id
  FROM fw.comp_def WHERE id = NEW.parent_comp_def_id;

  IF parent_core_id IS NULL THEN
    RAISE EXCEPTION 'Parent comp_def % nemá core_id set — cannot auto-inherit',
      NEW.parent_comp_def_id;
  END IF;

  -- Krok 5.Z (31.5.2026): VÝJIMKA pro nested grid (grid_modern s parentem).
  -- Embedded master-detail grid je sub-přehled s VLASTNÍM core (master přehled).
  -- Smí mít core_id != parent. Když není set, auto-zdědí (backward compat).
  SELECT ct.code INTO new_type_code
  FROM fw.comp_type ct WHERE ct.id = NEW.type_id;

  IF new_type_code = 'grid_modern' THEN
    IF NEW.core_id IS NULL THEN
      NEW.core_id := parent_core_id;   -- backward compat
    END IF;
    RETURN NEW;                        -- explicit core_id (i != parent) povolen
  END IF;

  -- Ostatní typy: dědí / enforce (beze změny)
  IF NEW.core_id IS NULL THEN
    NEW.core_id := parent_core_id;
  ELSIF NEW.core_id != parent_core_id THEN
    RAISE EXCEPTION 'core_id mismatch: NEW.core_id=% != parent.core_id=% (parent_comp_def_id=%)',
      NEW.core_id, parent_core_id, NEW.parent_comp_def_id;
  END IF;

  RETURN NEW;
END;
$function$;


-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ ČÁST 2 — UPDATE nested grid core_id + verify (spustit zvlášť)             ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
BEGIN;

-- 373 (nested Akce, ds 52)  → core 79 crm_kontakt_akce
-- 372 (nested Osoby, ds 53) → core 80 crm_kontakt_osoby
UPDATE fw.comp_def SET core_id = 79 WHERE id = 373;
UPDATE fw.comp_def SET core_id = 80 WHERE id = 372;

-- verify
SELECT cd.id AS nested_grid, cd.name, cd.core_id, cd.parent_comp_def_id,
       ct.code AS type_code, cd.data_source_id,
       c.code AS core_code, c.label AS core_label
FROM fw.comp_def cd
JOIN fw.comp_type ct ON ct.id = cd.type_id
LEFT JOIN fw.core c ON c.id = cd.core_id
WHERE cd.id IN (372, 373)
ORDER BY cd.id;

COMMIT;

-- ============================================================================
-- Očekávaný výstup: 372 → core_id 80 (crm_kontakt_osoby), 373 → core_id 79
-- (crm_kontakt_akce). parent_comp_def_id zůstává 319/324 (grid stále ve formu).
--
-- ROLLBACK: UPDATE fw.comp_def SET core_id = 72 WHERE id IN (372, 373);
-- (po revertu triggeru zpět by to ale neprošlo — drž výjimku)
-- ============================================================================
