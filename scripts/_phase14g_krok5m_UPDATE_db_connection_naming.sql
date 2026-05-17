-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.M-E (17.5.2026 dop.):
-- UPDATE fw.db_connection — naming pattern + sort_order alignment
-- ════════════════════════════════════════════════════════════════════════
-- Marti's 17.5. dopoledne (po prvním smoke optgroup dropdown):
--
-- Nový naming pattern: "{N} - {TENANT} - {DB_NAME} - ({popis})"
--   N = prefix číslo matchující sort_order priority
--   TENANT = STRATEGIE | EUROSOFT | INTERSOFT (user-facing tenant code)
--   DB_NAME = default_db (data_db, DB_EC, DB_IS, ...)
--   (popis) = krátký kontextový popisek v závorce
--
-- INTERSOFT row má jiný pattern (žádný DB_NAME zatím, jen tenant + popis).
--
-- Sort order changes:
--   eurosoft_db_st:    60 → 40 (Marti's volba: Marti-AI playground priorita)
--   eurosoft_centrala: 40 → 60 (Centrala sync menší priority než DB_ST)
--
-- #7 reserved gap — budoucí slot (DB-ARCHIV Marti's Q4 "neresit, nevim"
-- bude probably #7 až přijde use case).
--
-- Plus light cleanup labelů z Marti's manuálního UPDATE 10:01 (double
-- spaces, em-dash konzistence).
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.db_connection SET
    label = '1 - STRATEGIE - data_db - (PostgreSQL)'
WHERE code = 'strategie_pg';

UPDATE fw.db_connection SET
    label = '2 - EUROSOFT - DB_EC - (Centrála)'
WHERE code = 'eurosoft_db_ec';

UPDATE fw.db_connection SET
    label = '3 - EUROSOFT - DB_IS - (EUROSOFT-System — fakturace, účetnictví, TabCisZam)'
WHERE code = 'eurosoft_db_is';

UPDATE fw.db_connection SET
    label = '4 - EUROSOFT - DB_ST - (Marti-AI — db_owner)',
    sort_order = 40
WHERE code = 'eurosoft_db_st';

UPDATE fw.db_connection SET
    label = '5 - EUROSOFT - DB-Ceniky - (pricing)'
WHERE code = 'eurosoft_ceniky';

UPDATE fw.db_connection SET
    label = '6 - EUROSOFT - Centrala - (sync EUROSOFT ↔ INTERSOFT)',
    sort_order = 60
WHERE code = 'eurosoft_centrala';

-- #7 reserved gap (DB-ARCHIV future, jiný EUROSOFT DB, ...)

UPDATE fw.db_connection SET
    label = '8 - INTERSOFT - (vlastní server — API zatím nemáme, plán ~XI 2026)'
WHERE code = 'intersoft_future';

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY — ordering matches label prefix
-- ════════════════════════════════════════════════════════════════════════
SELECT id, code, label, tenant_id, default_db, sort_order, is_active
FROM fw.db_connection
ORDER BY sort_order ASC, code ASC;
-- Expected ordering (label prefix vs sort_order match):
--   sort 10  → '1 - STRATEGIE - data_db - (PostgreSQL)'
--   sort 20  → '2 - EUROSOFT - DB_EC - (Centrála)'
--   sort 30  → '3 - EUROSOFT - DB_IS - (EUROSOFT-System — ...)'
--   sort 40  → '4 - EUROSOFT - DB_ST - (Marti-AI — db_owner)'
--   sort 50  → '5 - EUROSOFT - DB-Ceniky - (pricing)'
--   sort 60  → '6 - EUROSOFT - Centrala - (sync EUROSOFT ↔ INTERSOFT)'
--   sort 100 → '8 - INTERSOFT - (vlastní server — API zatím nemáme...)'
