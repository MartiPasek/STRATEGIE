-- ═══════════════════════════════════════════════════════════════════════
-- KROK 2 (přepočet dat, se zálohou) — Peťa + Marti 22.7.2026.
-- Opraví u centrala1 řádků cinnost_id: import je uložil = centrálské číslo,
-- ale to je v našem číselníku JINÁ činnost. Přemapujeme přes ec_cislo na
-- správnou naši činnost. PŮVODNÍ hodnota se zálohuje do cinnost_id_orig.
-- Řádky bez protějšku (Centrála 27 „Odměny fin.zakázek") zůstávají beze změny.
-- Vratné: UPDATE ... SET cinnost_id = cinnost_id_orig.
-- ═══════════════════════════════════════════════════════════════════════
ALTER TABLE tenant.vyroba_work ADD COLUMN IF NOT EXISTS cinnost_id_orig integer;

-- 1) záloha původní hodnoty (jen jednou; už zálohované nepřepisuj)
UPDATE tenant.vyroba_work
   SET cinnost_id_orig = cinnost_id
 WHERE tenant_id = 2 AND source_system = 'centrala1'
   AND cinnost_id IS NOT NULL AND cinnost_id_orig IS NULL;

-- 2) přepočet na správnou činnost přes ec_cislo (jen kde protějšek existuje)
UPDATE tenant.vyroba_work w
   SET cinnost_id = (SELECT MIN(t.id) FROM tenant.vyroba_cinnost t
                      WHERE t.tenant_id = 2 AND t.ec_cislo = w.cinnost_id_orig),
       updated_at = now()
 WHERE w.tenant_id = 2 AND w.source_system = 'centrala1'
   AND w.cinnost_id_orig IS NOT NULL
   AND EXISTS (SELECT 1 FROM tenant.vyroba_cinnost t
                WHERE t.tenant_id = 2 AND t.ec_cislo = w.cinnost_id_orig)
   AND w.cinnost_id IS DISTINCT FROM (SELECT MIN(t.id) FROM tenant.vyroba_cinnost t
                      WHERE t.tenant_id = 2 AND t.ec_cislo = w.cinnost_id_orig);
