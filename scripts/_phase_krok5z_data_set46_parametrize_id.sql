-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — data_set 46 (crm_kontakt_detail_test) parametrizace WHERE K.ID
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): po re-pointu Kontakty (62) -> detail form (72) se "nektere
-- fieldy nevyplnuji". Diagnoza: forma core 72 nacita main row pres
-- fw_form_load_by_id -> entity_config (db_type=mssql) -> MCP edit-form path
-- (Krok 5-B Fix C, router.py ~2892). Data_set 46 ma natvrdo WHERE K.ID = 11341
-- (zbytek z TEST detail #40011). Backend wrap: SELECT * FROM (<data_set>) WHERE
-- [ID] = row_id -> vnitrek vraci jen 11341 -> vnejsi filtr na jiny row_id
-- nesedi -> 0 radku -> prazdne fieldy.
--
-- Fix: nahradit literal 11341 za :ID placeholder (Marti's "detail SQL idiom",
-- router.py ~2986). Backend detekuje :ID -> dosadi int(row_id), BEZ outer wrap
-- -> WHERE K.ID = <row_id> primo v bazi (predicate pushdown, rychle).
--
-- data_source 58 ma jediny op (select, op 73 -> data_set 46), sdileny formou
-- (core 72) i gridem (core 71 "TEST detail"). S :ID grid select dostane
-- :ID=None (Fix H auto-default) -> WHERE K.ID = NULL -> 0 radku. core 71 byl
-- test scaffold (jako core 63) -> prazdny grid akceptovatelny; pripadne
-- hard-delete core 71 nebo mu dat vlastni data_set bez filtru (follow-up).
--
-- Ziva data, BEZ restartu API (data_set sql_text se cte fresh per call).
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.data_set
SET sql_text = REPLACE(sql_text, 'WHERE K.ID = 11341', 'WHERE K.ID = :ID')
WHERE id = 46;
-- ocekavej: UPDATE 1

-- Verifikace (konec SQL ma obsahovat ':ID'):
-- SELECT id, right(sql_text, 40) AS sql_tail FROM fw.data_set WHERE id = 46;
