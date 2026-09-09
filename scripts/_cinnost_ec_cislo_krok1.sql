-- ═══════════════════════════════════════════════════════════════════════
-- KROK 1 (bezpečný, čistě additivní) — zarovnání činností na Centrálu.
-- Peťa + Marti 22.7.2026. Marti: „udělejte si záložní sloupec, jak jsme to
-- ve STRATEGII měli." Naše interní id + code + name se NEMĚNÍ → mobilní appka
-- a 5 návazných tabulek jedou beze změny. Jen PŘIDÁVÁME:
--   • strategie_cislo = záloha našeho původního čísla (= id)
--   • ec_cislo        = číslo z Centrály (1046 režie / 1047 dílna), napárováno dle názvu
-- Nejednoznačné případy zůstávají NULL (ec_cislo) → rozhodne Peťa v kroku 2.
-- Vratné: obě sloupce lze DROP.
-- ═══════════════════════════════════════════════════════════════════════
ALTER TABLE tenant.vyroba_cinnost ADD COLUMN IF NOT EXISTS strategie_cislo integer;
ALTER TABLE tenant.vyroba_cinnost ADD COLUMN IF NOT EXISTS ec_cislo integer;

-- záloha původního STRATEGIE čísla
UPDATE tenant.vyroba_cinnost SET strategie_cislo = id WHERE tenant_id = 2;

-- centrálské číslo dle jednoznačného napárování názvu (id -> ec_cislo)
UPDATE tenant.vyroba_cinnost v SET ec_cislo = m.ec
FROM (VALUES
  -- dílenské (sedící 1-5 + přehozené)
  (1,1),(2,2),(3,3),(4,4),(5,5),
  (6,11),(7,13),(8,38),(9,40),(10,41),(11,42),(12,7),(15,6),(16,9),(17,43),(18,44),
  -- absence
  (47,39),(48,21),(49,20),
  -- home office (u nás rezie, v C dílna 8)
  (44,8),
  -- režijní 19..42 -> 101..118 / 121..137
  (19,101),(20,104),(21,107),(22,102),(23,105),(24,108),(25,103),(26,106),(27,109),
  (28,121),(29,122),(30,124),(31,134),(32,135),(33,137),(34,110),(35,111),(36,112),
  (37,113),(38,114),(39,115),(40,116),(41,117),(42,118)
) AS m(id, ec)
WHERE v.tenant_id = 2 AND v.id = m.id;
