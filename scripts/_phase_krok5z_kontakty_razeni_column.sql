-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — Kontakty grid: pocitany sloupec Razeni (priorita) + ORDER BY
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- Marti (30.5.): "potrebujeme ten pocitany sloupec Razeni z EC_Kontakt".
-- Parita s Centralou (Volba B): computed column v st.CRM_Kontakt + grid
-- selektuje K.[Razeni] + ORDER BY K.Razeni ASC.
--
-- Vzorec (priorita = suma potencialu / dny do/po pristim kontaktu, min 1):
--   (((isnull(PoDDspoluprace,1)+isnull(PoProBjednani,1))+isnull(Atraktivita,1))
--    / case when datediff(day,isnull(PristiKontakt,getdate()),getdate())<1
--           then 1
--           else datediff(day,isnull(PristiKontakt,getdate()),getdate()) end)
-- getdate() = nedeterministicke -> computed column NON-PERSISTED (pocita se
-- na read; nelze indexovat — stejny cost jako inline, ale DRY/reusable).
--
-- ── KROK 1: MSSQL (DB_EC, st schema) — HOTOVO Marti 30.5. ────────────────
-- ALTER TABLE st.CRM_Kontakt
-- ADD Razeni AS (
--   (((isnull([PoDDspoluprace],(1))+isnull([PoProBjednani],(1)))+isnull([Atraktivita],(1)))
--    / case when datediff(day,isnull([PristiKontakt],getdate()),getdate())<(1)
--           then (1)
--           else datediff(day,isnull([PristiKontakt],getdate()),getdate()) end)
-- );
--
-- ── KROK 2: PostgreSQL (fw schema) — data_set 40 (Kontakty grid, ds 51) ──
-- Pridat ,K.[Razeni] za PristiKontakt + ORDER BY K.[ID] DESC -> K.Razeni ASC.
-- Izolovane: data_set 40 = jen Kontakty select op 55. Forma core 72 (ds 58,
-- data_set 46) NEdotcena. Ziva data, BEZ restartu API (refresh gridu staci).
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.data_set
SET sql_text = REPLACE(
                 REPLACE(sql_text, ',K.[PristiKontakt]', ',K.[PristiKontakt]
      ,K.[Razeni]'),
                 'ORDER BY K.[ID] DESC', 'ORDER BY K.Razeni ASC')
WHERE id = 40;
-- ocekavej: UPDATE 1

-- Verifikace (SQL ma obsahovat K.[Razeni] + ORDER BY K.Razeni ASC):
-- SELECT id, sql_text FROM fw.data_set WHERE id = 40;
