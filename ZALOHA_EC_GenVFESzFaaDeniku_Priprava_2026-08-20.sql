-- Autor: Kristýna Kšírová
-- Datum: 19.7.2023
-- Popis: Načte záznamy pro čtvrtletní fakturaci ES a sgroupuje je do požadované podoby pro vytvoření vydané faktury

CREATE PROCEDURE [dbo].[EC_GenVFESzFaaDeniku_Priprava]
@Mesic int = null, @Kvartal int = null, @Rok int, @NajemneOsMes numeric(18,2) = 0, @ProcentMarze numeric(18,2) = 0 --Kristýna 18.7.2024 - možno přidat marži
AS


--DECLARE @Mesic1 int
DECLARE @Mesic2 int
DECLARE @Mesic3 int

IF isnull(@Kvartal,0) <> 0
BEGIN
   IF isnull(@Kvartal,0) = 1
   BEGIN
      SET @Mesic = 1
      SET @Mesic2 = 2
      SET @Mesic3 = 3
   END
   ELSE
   IF isnull(@Kvartal,0) = 2
   BEGIN
      SET @Mesic = 4
      SET @Mesic2 = 5
      SET @Mesic3 = 6
   END
   ELSE
   IF isnull(@Kvartal,0) = 3
      BEGIN
      SET @Mesic = 7
      SET @Mesic2 = 8
      SET @Mesic3 = 9
   END
   ELSE
   IF isnull(@Kvartal,0) = 4
   BEGIN
      SET @Mesic = 10
      SET @Mesic2 = 11
      SET @Mesic3 = 12
   END
END


   --drop table ##TempFakturaceES


-- načtení záznamů z faktur a z účetního deníku
IF OBJECT_ID('tempdb..##TempFakturaceES' , 'U') IS NOT NULL
BEGIN
  --SET IDENTITY_INSERT tempdb..##TempFakturace ON 
  DELETE ##TempFakturaceES
END  
IF OBJECT_ID('tempdb..##TempFakturaceES' , 'U') IS NOT NULL
BEGIN 
   INSERT INTO ##TempFakturaceES (Castka, ProcentMarze, Skupina, Stredisko, Mesic, Kvartal, Rok, Autor, DatPorizeni)	
	SELECT 
       	    sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END) + isnull(@NajemneOsMes,0) + ((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/100)*isnull(@ProcentMarze,0)) as Castka
			,isnull(@ProcentMarze,0) as ProcentMarze
            ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID where V.cislozam=D.CisloZam and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
            ,D.Utvar
			,@Mesic as Mesic
			,@Kvartal as Kvartal
			,@Rok as Rok
			,suser_sname()
			,getdate()
           FROM [DB_IS].[dbo].[TabDenik] as D
           WHERE (CisloUcet like '5%' OR D.CisloUcet IN (336200, 336202)) and year(D.DatumPripad) = @Rok 
           and (month(D.DatumPripad) = @Mesic or month(D.DatumPripad) = isnull(@Mesic2,0) or month(D.DatumPripad) = isnull(@Mesic3,0))
		   and D.CisloZam not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5) -- nepočítat IT, fakturuje se polovinou částky viz union all
           GROUP BY d.CisloZam, d.utvar
           
           UNION ALL
           
           SELECT
            TabDokladyZbozi.SumaKcBezDPH + isnull(@NajemneOsMes,0) + ((TabDokladyZbozi.SumaKcBezDPH/100)*isnull(@ProcentMarze,0))
			,isnull(@ProcentMarze,0) as ProcentMarze
           ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID  where V.cislozam=Z.Cislo and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) 
		   AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) <> 0 THEN 1 ELSE 0 END) = 1) 
           and Z.Cislo not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)  -- nepočítat IT, fakturuje se polovinou částky  viz union all 

           UNION ALL

------------------ Kristýna 18.3.2026 - IT udělat zvlášť - přefakturujeme jen polovinu nákladů, druhou polovinu platí IAP ---------------------------------------------------------------------------------------------------------------
            SELECT 
       	    ((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2) + isnull(@NajemneOsMes,0) + (((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2)/100)*isnull(@ProcentMarze,0))) as Castka
			,isnull(@ProcentMarze,0) as ProcentMarze
            ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID where V.cislozam=D.CisloZam and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
            ,D.Utvar
			,@Mesic as Mesic
			,@Kvartal as Kvartal
			,@Rok as Rok
			,suser_sname()
			,getdate()
           FROM [DB_IS].[dbo].[TabDenik] as D
           WHERE (CisloUcet like '5%' OR D.CisloUcet IN (336200, 336202)) and year(D.DatumPripad) = @Rok 
           and (month(D.DatumPripad) = @Mesic or month(D.DatumPripad) = isnull(@Mesic2,0) or month(D.DatumPripad) = isnull(@Mesic3,0))
		   and D.CisloZam in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5) -- nepočítat IT, fakturuje se polovinou částky viz union all
           GROUP BY d.CisloZam, d.utvar
           
           UNION ALL
           
           SELECT
            (TabDokladyZbozi.SumaKcBezDPH/2) + isnull(@NajemneOsMes,0) + (((TabDokladyZbozi.SumaKcBezDPH/2)/100)*isnull(@ProcentMarze,0))
			,isnull(@ProcentMarze,0) as ProcentMarze
           ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID  where V.cislozam=Z.Cislo and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) 
		   AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) <> 0 THEN 1 ELSE 0 END) = 1) 
           and Z.Cislo in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)  -- nepočítat IT, fakturuje se polovinou částky  viz union all
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
           
		   UNION ALL

		   -- nově fakturovat i režjní náklady
		   SELECT
            TabDokladyZbozi.SumaKcBezDPH + ((TabDokladyZbozi.SumaKcBezDPH/100)*isnull(@ProcentMarze,0))
			,isnull(@ProcentMarze,0) as ProcentMarze
           ,'Režijní náklady ' + convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok)
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) 
		   AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) = 0 THEN 1 ELSE 0 END) = 1) 
           --and Z.Cislo not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)  -- nepočítat IT, fakturuje se zvlášť fakturou na Centrálu    
           AND TabDokladyZbozi.CisloOrg not in(878,0)

		   UNION ALL
           
           SELECT
           TabDokladyZbozi.SumaKcBezDPH
		   ,0 as ProcentMarze
		   ,'Nájemné ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Mesic) + ' - ' + convert(nvarchar,@Mesic3) + '/' + convert(nvarchar,@Rok) END)
           --,TabDokladyZBozi.Popis--,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID  where V.cislozam=Z.Cislo and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28) FOR XML PATH(''))
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))
		   --AND(TabDokladyZbozi.DruhPohybuZbo>=18)AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)
		   AND(TabDokladyZbozi.RadaDokladu like '6%') and exists(SELECT ID FROM TabPohybyZbozi as P WHERE p.IDDoklad = tabdokladyzbozi.id and (poznamka like '%nájem%' or poznamka like 'najem')))
		   and tabdokladyzbozi.Cisloorg = 1
		  -- and (PopisDodavky like 'Nájemné' or PopisDodavky like 'Najemne' or PopisDodavky like 'Najem' or PopisDodavky like 'Nájem'))
END
ELSE
            SELECT 
			 sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END) + isnull(@NajemneOsMes,0)+ ((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/100)*isnull(@ProcentMarze,0)) as Castka
			,isnull(@ProcentMarze,0) as ProcentMarze
            ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID where V.cislozam=D.CisloZam and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH('')) as Skupina
            ,D.Utvar as Stredisko
			,@Mesic as Mesic
			,@Kvartal as Kvartal
			,@Rok as Rok
			,suser_sname() as Autor
		    ,getdate() as DatPorizeni
			INTO ##TempFakturaceES
            FROM [DB_IS].[dbo].[TabDenik] as D
            WHERE (CisloUcet like '5%' OR D.CisloUcet IN (336200, 336202)) and year(D.DatumPripad) = @Rok 
            and (month(D.DatumPripad) = @Mesic or month(D.DatumPripad) = @Mesic2 or month(D.DatumPripad) = @Mesic3)
			and D.CisloZam not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5) -- nepočítat IT, fakturuje se zvlášť fakturou na Centrálu
            GROUP BY d.CisloZam, d.utvar
           
            UNION ALL
           
            SELECT
            TabDokladyZbozi.SumaKcBezDPH + isnull(@NajemneOsMes,0) + ((TabDokladyZbozi.SumaKcBezDPH/100)*isnull(@ProcentMarze,0)) as Castka
		   ,isnull(@ProcentMarze,0) as ProcentMarze
           ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID where Z.Cislo=V.CisloZam FOR XML PATH('')) as Skupina
           ,TabDokladyZbozi.StredNaklad as Stredisko
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname() as Autor
		   ,getdate() as DatPorizeni
            FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN EC_DokladyPomocnePolozky DokP ON TabDokladyZbozi.ID=DokP.IDDoklad
             LEFT OUTER JOIN TabScontoFaktury S ON S.IDFak = TabDokladyZbozi.ID
             LEFT OUTER JOIN (select DISTINCT(IDFak) from TabUhrady where Puvod=3) AS Uhrady ON Uhrady.IDFak = TabDokladyZbozi.ID
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
            WHERE
            ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) <> 0 THEN 1 ELSE 0 END) = 1)         
		   and Z.Cislo not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5) -- nepočítat IT, fakturuje se zvlášť fakturou na Centrálu

           UNION ALL
		   
---------------- Kristýna 18.3.2026 - IT udělat zvlášť - přefakturujeme jen polovinu nákladů, druhou polovinu platí IAP ------------------------------------------------------------------------------------------------------------
            SELECT 
       	    (sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2) + isnull(@NajemneOsMes,0) + (((sum(CASE WHEN D.CisloUcet = 336202 THEN -D.Castka ELSE D.Castka END)/2)/100)*isnull(@ProcentMarze,0)) as Castka
			,isnull(@ProcentMarze,0) as ProcentMarze
            ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID where V.cislozam=D.CisloZam and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
            ,D.Utvar
			,@Mesic as Mesic
			,@Kvartal as Kvartal
			,@Rok as Rok
			,suser_sname()
			,getdate()
           FROM [DB_IS].[dbo].[TabDenik] as D
           WHERE (CisloUcet like '5%' OR D.CisloUcet IN (336200, 336202)) and year(D.DatumPripad) = @Rok 
           and (month(D.DatumPripad) = @Mesic or month(D.DatumPripad) = isnull(@Mesic2,0) or month(D.DatumPripad) = isnull(@Mesic3,0))
		   and D.CisloZam in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5) -- nepočítat IT, fakturuje se polovinou částky viz union all
           GROUP BY d.CisloZam, d.utvar
           
           UNION ALL
           
           SELECT
            (TabDokladyZbozi.SumaKcBezDPH/2) + isnull(@NajemneOsMes,0) + (((TabDokladyZbozi.SumaKcBezDPH/2)/100)*isnull(@ProcentMarze,0))
			,isnull(@ProcentMarze,0) as ProcentMarze
           ,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID  where V.cislozam=Z.Cislo and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28,39,40,41,42) FOR XML PATH(''))
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) 
		   AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) <> 0 THEN 1 ELSE 0 END) = 1) 
           and Z.Cislo in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)  -- nepočítat IT, fakturuje se polovinou částky  viz union all
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


		   UNION ALL

		   -- nově fakturovat i režjní náklady
		   SELECT
            TabDokladyZbozi.SumaKcBezDPH + ((TabDokladyZbozi.SumaKcBezDPH/100)*isnull(@ProcentMarze,0))
			,isnull(@ProcentMarze,0) as ProcentMarze
           ,'Režijní náklady ' + convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok)
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))AND(TabDokladyZbozi.DruhPohybuZbo>=18)
           AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)AND(TabDokladyZbozi.RadaDokladu in(501, 511, 521, 531, 541)) 
		   AND (CASE WHEN isnull(ZE._CisloOrgVazbaMzdy,0) = 0 THEN 1 ELSE 0 END) = 1) --and Z.Cislo not in(SELECT CisloZam FROM EC_SkupinyVazby WHERE IDSkupiny = 5)  -- nepočítat IT, fakturuje se zvlášť fakturou na Centrálu    
           AND TabDokladyZbozi.CisloOrg not in(878,0)

		   UNION ALL

		   SELECT
           TabDokladyZbozi.SumaKcBezDPH
		   ,0 as ProcentMarze
		   ,'Nájemné ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Mesic) + ' - ' + convert(nvarchar,@Mesic3) + '/' + convert(nvarchar,@Rok) END)
           --,TabDokladyZBozi.Popis--,(SELECT S.Nazev + ', ' FROM EC_SkupinyVazby AS V LEFT OUTER JOIN EC_Skupiny AS S ON V.IDSkupiny = S.ID  where V.cislozam=Z.Cislo and IDSkupiny not in(16,17,19,20,21,22,23,26,27,28) FOR XML PATH(''))
           ,TabDokladyZbozi.StredNaklad
		   ,@Mesic as Mesic
		   ,@Kvartal as Kvartal
		   ,@Rok as Rok
		   ,suser_sname()
		   ,getdate()
           FROM TabDokladyZbozi
             LEFT OUTER JOIN TabCisOrg VDokZboCisOrg ON TabDokladyZbozi.CisloOrg=VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam_EXT as ZE on ZE._CisloOrgVazbaMzdy = VDokZboCisOrg.CisloOrg
             LEFT OUTER JOIN TabCisZam as Z on Z.ID = ZE.ID
           WHERE
           ((year(DUZP) = @Rok and (month(DUZP) = @Mesic or month(DUZP) = @Mesic2 or month(DUZP) = @Mesic3))
		   --AND(TabDokladyZbozi.DruhPohybuZbo>=18)AND(TabDokladyZbozi.DruhPohybuZbo<=19)AND(TabDokladyZbozi.PoradoveCislo>=0)
		   AND(TabDokladyZbozi.RadaDokladu like '6%') and exists(SELECT ID FROM TabPohybyZbozi as P WHERE p.IDDoklad = tabdokladyzbozi.id and (poznamka like '%nájem%' or poznamka like 'najem')))
		  and tabdokladyzbozi.CisloOrg = 1
		  -- and (PopisDodavky like 'Nájemné' or PopisDodavky like 'Najemne' or PopisDodavky like 'Najem' or PopisDodavky like 'Nájem'))
		   


-- sgroupování záznamů z předchozí tabulky dle jednotlivých popisů položek na faktuře
IF OBJECT_ID('tempdb..##TempFinal' , 'U') IS NOT NULL
BEGIN 
 --SET IDENTITY_INSERT tempdb..##TempFinal ON  
  DELETE ##TempFinal
END  
IF OBJECT_ID('tempdb..##TempFinal' , 'U') IS NOT NULL
BEGIN 
   INSERT INTO ##TempFinal (Castka, ProcentMarze, Popis, Stredisko, Kvartal, Mesic, Rok, Autor, DatPorizeni)
       SELECT sum(Castka) as Castka, ProcentMarze
	      ,(CASE
           WHEN Skupina like '%Příprava výroby%' THEN 'Příprava materiálu pro výrobu za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)
           WHEN Skupina like '%Logistika%' THEN 'Zpracování dokladů souvisejících s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END) --+convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Kanceláře, Asistentky, Asistentky, ' THEN 'Administrativa spojená s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END) --+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Asistentky, Asistentky, Kanceláře, ' THEN 'Administrativa spojená s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedoucí projektů výroba%' THEN 'Vedení zakázek divize rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Nákup%' THEN 'Zpracování dokladů souvisejících s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Dílna, ' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Dílna, Garanti, ' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedení společnosti%' THEN 'Správní výdaje - vedení za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Personální%' THEN 'Personální služby za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Zkušebna%' THEN 'Zkoušení rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%IT,%' THEN 'Správa a údržba informačního systému a IT podpora uživatelů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedoucí projektů SW,%' THEN 'Dodavatelské služby pro software za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vytížení - montéři%' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   WHEN Skupina like '%Vytížení - výpomoc%' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   WHEN Skupina like '%Zámečník%' THEN 'Zámečnické práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   ELSE isnull(Skupina,'CHYBÍ SKUPINA') END
           ) as Popis
           ,Stredisko
		   ,Kvartal
           ,Mesic
		   ,Rok
		   ,suser_sname() as Autor
		   ,getdate() as DatPorizeni
           FROM ##TempFakturaceES
           GROUP BY Skupina, Stredisko, Mesic, Kvartal, Rok, ProcentMarze
END
ELSE
   SELECT sum(Castka) as Castka, ProcentMarze
	      	      ,(CASE
           WHEN Skupina like '%Příprava výroby%' THEN 'Příprava materiálu pro výrobu za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)
           WHEN Skupina like '%Logistika%' THEN 'Zpracování dokladů souvisejících s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END) --+convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Kanceláře, Asistentky, Asistentky, ' THEN 'Administrativa spojená s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END) --+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Asistentky, Asistentky, Kanceláře, ' THEN 'Administrativa spojená s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedoucí projektů výroba%' THEN 'Vedení zakázek divize rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Nákup%' THEN 'Zpracování dokladů souvisejících s výrobou rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Dílna, ' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like 'Dílna, Garanti, ' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedení společnosti%' THEN 'Správní výdaje - vedení za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Personální%' THEN 'Personální služby za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Zkušebna%' THEN 'Zkoušení rozvaděčů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%IT,%' THEN 'Správa a údržba informačního systému a IT podpora uživatelů za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vedoucí projektů SW,%' THEN 'Dodavatelské služby pro software za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
           WHEN Skupina like '%Vytížení - montéři%' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   WHEN Skupina like '%Vytížení - výpomoc%' THEN 'Elektromontážní práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   WHEN Skupina like '%Zámečník%' THEN 'Zámečnické práce za ' + (CASE isnull(@Kvartal,0) WHEN 0 THEN convert(nvarchar,@Mesic) + '/' + convert(nvarchar,@Rok) ELSE convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok) END)--+ convert(nvarchar,@Kvartal) + 'Q/' + convert(nvarchar,@Rok)
		   ELSE isnull(Skupina,'CHYBÍ SKUPINA') END
           ) as Popis
           ,Stredisko
           ,Kvartal
		   ,Mesic
		   ,Rok
		   ,suser_sname() as Autor
		   ,getdate() as DatPorizeni
		   INTO ##TempFinal
           FROM ##TempFakturaceES
           GROUP BY Skupina, Stredisko, Mesic, Kvartal, Rok, ProcentMarze
