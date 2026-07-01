# ROLLBACK — dbo.ECv_Vytizeni_SeznamNepritomnost (EC Centrála)

**Marti 28.6.2026:** view přesměrován z `dbo.EC_Dochazka_PlanNepritomnost`
(EC absence plán, zakázán) na `st.EC_Vytizeni_NepritomnostSTRATEGIE`
(naše zrcadlo, plněné jednosměrně z `tenant.att_planned_absence` přes `@@VYTIZABS`).
Excel „Plánování vytížení" čte přes řetězec
`ECv_vytizeni_seznamVytizeniMonteru` → `ECv_Vytizeni_SeznamNepritomnost`.

## PŮVODNÍ definice (návrat = spustit tohle jako ALTER)

```sql
ALTER VIEW dbo.ECv_Vytizeni_SeznamNepritomnost AS
SELECT  ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DatumPripadu, '') AS DatumPripadu,
        ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DenVTydnu, '') AS DenVTydnu,
        ISNULL(dbo.EC_Dochazka_PlanNepritomnost.DruhCinnosti, 0) AS DruhCinnosti,
        '' AS Jmeno,
        IIF(ISNULL(dbo.EC_GlobKonstUziv.DochZobrazitJmeno, 0) = 0, dbo.TabCisZam.Prijmeni, dbo.TabCisZam.PrijmeniJmeno) AS Prijmeni,
        dbo.TabCisZam.LoginId, dbo.TabCisZam.Cislo AS CisloZam,
        ISNULL(dbo.EC_DilnaCinnosti.Nazev, '') AS Nazev,
        EC_Dochazka_PlanNepritomnost.PocetHodin, EC_Dochazka_PlanNepritomnost.Barva as barva
FROM    dbo.EC_SkupinyVazby
        INNER JOIN dbo.TabCisZam ON dbo.EC_SkupinyVazby.CisloZam = dbo.TabCisZam.Cislo
        INNER JOIN dbo.tabciszam_EXT ON dbo.TabCisZam.ID = dbo.tabciszam_EXT.ID AND ISNULL(dbo.tabciszam_EXT._Neaktivni, 0) = 0
        LEFT OUTER JOIN dbo.EC_GlobKonstUziv ON dbo.TabCisZam.LoginID = dbo.EC_GlobKonstUziv.LoginName
        LEFT OUTER JOIN dbo.EC_Dochazka_PlanNepritomnost ON dbo.TabCisZam.Cislo = dbo.EC_Dochazka_PlanNepritomnost.CisloZam
        LEFT OUTER JOIN dbo.EC_DilnaCinnosti ON dbo.EC_Dochazka_PlanNepritomnost.DruhCinnosti = dbo.EC_DilnaCinnosti.Cislo
WHERE   (dbo.EC_SkupinyVazby.IDSkupiny IN (31)) AND ISNULL(dbo.EC_SkupinyVazby.neaktivni, 0) = 0
```

## NOVÁ definice (čte z našeho zrcadla `st`)

Jediná změna: absenční tabulka `dbo.EC_Dochazka_PlanNepritomnost` → `st.EC_Vytizeni_NepritomnostSTRATEGIE` (alias `pn`). Skupina 31, číselníky jmen/činností beze změny.
