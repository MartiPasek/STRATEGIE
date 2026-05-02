# EC_Mzdy_SumaMesic

**Schema**: dbo · **Cluster**: HR · **Rows**: 4,107 · **Size**: 3.45 MB · **Sloupců**: 115 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CasCelkem` | numeric(19,2) | ANO |  |  |
| 4 | `KontoMinulyMesic` | numeric(19,2) | ANO |  |  |
| 5 | `KontoKonecMesic` | numeric(19,2) | ANO |  |  |
| 6 | `KontoPlaceneMinulyMesic` | numeric(19,2) | ANO |  |  |
| 7 | `KontoPlaceneKonecMesic` | numeric(19,2) | ANO |  |  |
| 8 | `DatumPrepoctu` | datetime | ANO |  |  |
| 9 | `Uzavreno` | bit | ANO |  |  |
| 10 | `HodinyDoFPD` | numeric(19,2) | ANO |  |  |
| 11 | `UvazekHodSmlouva` | int | ANO |  |  |
| 12 | `UvazekHodReal` | int | ANO |  |  |
| 13 | `ZaklMzda` | int | ANO |  |  |
| 14 | `OsHodnoceni` | int | ANO |  |  |
| 15 | `Premie` | int | ANO |  |  |
| 16 | `PremieVykon` | int | ANO |  |  |
| 17 | `PremieKultura` | int | ANO |  |  |
| 18 | `PremieIndividualOhod` | int | ANO |  |  |
| 19 | `PremieVedeniLidi` | int | ANO |  |  |
| 20 | `PremieVedeniObch` | int | ANO |  |  |
| 21 | `PremieNapracovaneVolno` | int | ANO |  |  |
| 22 | `PremieGarant` | int | ANO |  |  |
| 23 | `OdmenaZFinanciZak` | int | ANO |  |  |
| 24 | `OdmenaPrescasy` | int | ANO |  |  |
| 25 | `PocetStravenek` | smallint | ANO |  |  |
| 26 | `DovolenaCerpano` | numeric(19,2) | ANO |  |  |
| 27 | `DovolenaZbyva` | numeric(19,2) | ANO |  |  |
| 28 | `SickDayCerpano` | numeric(19,2) | ANO |  |  |
| 29 | `SickDayZbyva` | numeric(19,2) | ANO |  |  |
| 30 | `NahradaPlacVolna_Proc` | smallint | ANO |  |  |
| 31 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 32 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 33 | `DatZmeny` | datetime | ANO |  |  |
| 34 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 35 | `Mesic` | int | ANO |  |  |
| 36 | `Rok` | int | ANO |  |  |
| 37 | `ZakladZaHod` | int | ANO |  |  |
| 38 | `OsOhodZaHod` | int | ANO |  |  |
| 39 | `VykonOhodZaHod` | int | ANO |  |  |
| 40 | `PrescasCelkemMesic` | numeric(19,2) | ANO |  |  |
| 41 | `RezijniMzdaHod` | int | ANO |  |  |
| 42 | `PremieFinanceZam` | int | ANO |  |  |
| 43 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 44 | `NaborovyPrizpevek` | int | ANO |  |  |
| 45 | `OdmenaSkolitel` | int | ANO |  |  |
| 46 | `JednorazoveOdmeny` | int | ANO |  |  |
| 47 | `DovolenaText` | nvarchar(4000) | NE | ('') |  |
| 48 | `SouhrnText` | nvarchar(4000) | NE | ('') |  |
| 49 | `NemocText` | nvarchar(4000) | NE | ('') |  |
| 50 | `OCRText` | nvarchar(4000) | NE | ('') |  |
| 51 | `LekarText` | nvarchar(4000) | NE | ('') |  |
| 52 | `OstatniNepritomnostText` | nvarchar(4000) | NE | ('') |  |
| 53 | `MaterskaText` | nvarchar(4000) | NE | ('') |  |
| 54 | `Tarif` | numeric(19,2) | ANO |  |  |
| 55 | `DPP` | bit | ANO |  |  |
| 56 | `HPP` | bit | ANO |  |  |
| 57 | `Neaktivni` | bit | ANO |  |  |
| 58 | `PoznamkaKZam` | nvarchar(4000) | NE | ('') |  |
| 59 | `MzdOK` | int | NE |  |  |
| 60 | `PreneslDoMezd` | nvarchar(126) | ANO |  |  |
| 61 | `PrenesenoDoMezdDat` | datetime | ANO |  |  |
| 62 | `UvazekSnizeniHod` | numeric(9,2) | ANO |  |  |
| 63 | `UvazekSnizeniKC` | numeric(9,2) | ANO |  |  |
| 64 | `HodSazba` | numeric(9,2) | ANO |  |  |
| 65 | `OsOhodSrazka` | numeric(9,2) | ANO |  |  |
| 66 | `PrescasSNeplacenym` | numeric(19,2) | ANO |  |  |
| 67 | `DatumSmlouvyOd` | datetime | ANO |  |  |
| 68 | `DatumSmlouvyDo` | datetime | ANO |  |  |
| 69 | `ZkusebniDobaDo` | datetime | ANO |  |  |
| 70 | `IDPodm` | int | ANO |  |  |
| 71 | `PodepsaneProhl` | bit | ANO | ((0)) |  |
| 72 | `ZdrPojKod` | int | ANO |  |  |
| 73 | `PrumerHV` | numeric(9,2) | ANO |  |  |
| 74 | `DPPSuma` | numeric(9,2) | ANO |  |  |
| 75 | `JPSkolitel` | numeric(9,2) | ANO |  |  |
| 76 | `JPNabor` | numeric(9,2) | ANO |  |  |
| 77 | `JPVedouci` | numeric(9,2) | ANO |  |  |
| 78 | `Stredisko` | nvarchar(30) | ANO | ((1)) |  |
| 79 | `PremieKvalita` | numeric(18,2) | ANO |  |  |
| 80 | `SrazkaNarizeneVolnoMes` | numeric(18,2) | ANO |  |  |
| 81 | `CasNarizeneVolnoMes` | numeric(18,2) | ANO |  |  |
| 82 | `CasNahrazeneVolnoMes` | numeric(18,2) | ANO |  |  |
| 83 | `PrescasSnizeny` | numeric(18,2) | ANO |  |  |
| 84 | `PremieNahrazeneVolno` | numeric(18,2) | ANO |  |  |
| 85 | `OdmenaPrescasBezNahrazeni` | numeric(18,2) | ANO |  |  |
| 86 | `KontoPlaceneKCMinulyMesic` | numeric(18,2) | ANO |  |  |
| 87 | `KontoPlaceneKCKonecMesic` | numeric(18,2) | ANO |  |  |
| 88 | `OtecText` | nvarchar(4000) | ANO |  |  |
| 89 | `Volno60Text` | nvarchar(4000) | ANO |  |  |
| 90 | `NeplaceneVolnoText` | nvarchar(4000) | ANO |  |  |
| 91 | `Firma` | int | ANO |  |  |
| 92 | `CasVolnoMesCelkem` | numeric(18,2) | ANO |  |  |
| 93 | `HodSazbaPrescas` | numeric(9,2) | ANO | ((0)) |  |
| 94 | `Prescas_Vikend` | numeric(6,2) | ANO | ((0)) |  |
| 95 | `Prescas_Svatek` | numeric(6,2) | ANO | ((0)) |  |
| 96 | `Prescas_Zbytek` | numeric(6,2) | ANO | ((0)) |  |
| 97 | `PrescasKC_Vikend` | numeric(9,2) | ANO | ((0)) |  |
| 98 | `PrescasKC_Svatek` | numeric(9,2) | ANO | ((0)) |  |
| 99 | `PrescasKC_Zbytek` | numeric(9,2) | ANO | ((0)) |  |
| 100 | `PlatitPrescasyDilna` | bit | ANO | ((0)) |  |
| 101 | `CasVikend` | numeric(9,2) | ANO | ((0)) |  |
| 102 | `CasSvatek` | numeric(9,2) | ANO | ((0)) |  |
| 103 | `Odpocet1Mesic` | bit | ANO |  |  |
| 104 | `Volno80Text` | nvarchar(4000) | ANO |  |  |
| 105 | `Volno90Text` | nvarchar(4000) | ANO |  |  |
| 106 | `PrekazkaVPraciText` | nvarchar(4000) | ANO |  |  |
| 107 | `CasNeplaceneVolno` | numeric(18,2) | ANO |  |  |
| 108 | `KontoPlacenePropadlo` | numeric(19,2) | ANO |  |  |
| 109 | `KontoPlacenePropadloKc` | numeric(19,2) | ANO |  |  |
| 110 | `KontoPlaceneSwobi` | numeric(19,2) | ANO |  |  |
| 111 | `CasVolnoBezMzdy` | numeric(19,2) | ANO |  |  |
| 112 | `VolnoBezMzdyText` | numeric(19,2) | ANO |  |  |
| 113 | `Cestak` | numeric(18,2) | ANO |  |  |
| 114 | `PremieJednatel` | numeric(18,2) | ANO |  |  |
| 115 | `Volno70Text` | nvarchar(4000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Mzdy_SumaMesic` (CLUSTERED) — `ID`
