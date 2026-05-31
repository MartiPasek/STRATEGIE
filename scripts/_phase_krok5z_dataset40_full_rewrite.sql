-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z — data_set 40 (Kontakty grid) FULL REWRITE — dedup ,K.[Razeni]
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- REPLACE/regexp dedup nezabraly (CRLF/whitespace mismatch) -> plny prepis
-- sql_text pres dollar-quote ($RAZ$...$RAZ$ — '' literaly bez escapu).
-- Jeden ,K.[Razeni] + ORDER BY K.Razeni ASC. Spustit jako JEDEN statement.
-- ════════════════════════════════════════════════════════════════════════

UPDATE fw.data_set SET sql_text = $RAZ$SELECT K.[ID]
      ,K.[Autor]
      ,K.[DatPorizeni]
      ,K.[Zmenil]
      ,K.[DatZmeny]
      ,KA.[FirmaText]
      ,nullif(OrgA.Nazev,DruhyNazev) as Firma
      ,KKc.[Kategorie]
      ,KTPZc.[TypZakazky]
      ,KA.[VyhledanoZ]
      ,K.[PoDDspoluprace]
      ,K.[PoProBjednani]
      ,K.[Atraktivita]
      ,K.[PristiKontakt]
      ,K.[Razeni]
      ,PoslAkce.Nazev as PoslAkceNazev
      ,KZC.Zeme
      ,convert(bit,iif(TelKontakt.ID is null,0,1)) as TelKontakt
      ,CONVERT(bit, IIF(NemaZajemRozvadece.ID IS NULL, 1, 0)) AS MaZajemORozvadece
      --,K.FirmaIDOrg
  FROM st.CRM_Kontakt as K
    left outer join st.CRM_Kontakt_Akce as KA on KA.IDhlav=K.ID and KA.IDAkce=16
    LEFT OUTER JOIN dbo.TabCisOrg as OrgA on OrgA.ID=KA.FirmaIDOrg
    LEFT OUTER JOIN st.CRM_Kontakt_KategorieCis as KKc on KKc.ID=KA.Kategorie
    LEFT OUTER JOIN st.CRM_Kontakt_TypZakazekCis as KTPZc on KTPZc.ID=KA.TypZakazky
    left outer join st.CRM_Kontakt_ZemeCis as KZC on KZC.ID=KA.ZemeID
    LEFT OUTER JOIN dbo.TabCisKOs as KOs on KOs.ID=K.KontaktID
    LEFT OUTER JOIN dbo.TabCisZam as Obeslal on Obeslal.ID=K.[ObeslalZamID]
    LEFT OUTER JOIN dbo.TabCisZam as Komunikace on Komunikace.ID=K.[KomunikaceZamID]
    outer apply (   select top 1 KAC.Nazev
                    from st.CRM_Kontakt_Akce KA
                        left outer join st.CRM_Kontakt_AkceCis as KAC on KAC.ID=KA.IDAkce
                    where KA.idhlav=K.ID
                    order by KAC.Poradi desc) as PoslAkce
    outer apply (   select top 1 KA.ID
                    from st.CRM_Kontakt_Akce KA
                    where KA.idhlav=K.ID and KA.IDAkce in (16,17)
                        and (isnull(KA.Telefon,'')<>'' or isnull(KA.Mobil,'')<>'')) as TelKontakt
    OUTER APPLY (   SELECT TOP (1) KA2.ID
                    FROM st.CRM_Kontakt_Akce AS KA2
                    WHERE KA2.IDHlav = K.ID
                      AND KA2.IDAkce = 20
                    ORDER BY KA2.DatPorizeni DESC, KA2.ID DESC
                    ) AS NemaZajemRozvadece
  ORDER BY K.Razeni ASC$RAZ$
WHERE id = 40;

-- Verifikace (jen JEDEN vyskyt):
-- SELECT (length(sql_text) - length(replace(sql_text, ',K.[Razeni]', '')))
--        / length(',K.[Razeni]') AS razeni_count
-- FROM fw.data_set WHERE id = 40;   -- ma byt 1
