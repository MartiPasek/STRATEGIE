# EC_AutZprDefPol

**Schema**: dbo · **Cluster**: Workflow · **Rows**: 1,914 · **Size**: 0.53 MB · **Sloupců**: 37 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | NE |  |  |
| 3 | `Poradi` | int | ANO |  |  |
| 4 | `Polozka` | bit | NE | ((0)) |  |
| 5 | `ZaPolozkami` | bit | ANO | ((0)) |  |
| 6 | `Command` | int | NE | ((1)) |  |
| 7 | `ReakceNaRLO` | nvarchar(50) | ANO |  |  |
| 8 | `FieldName` | nvarchar(40) | ANO |  |  |
| 9 | `DefaultText` | nvarchar(200) | ANO |  |  |
| 10 | `CMD_HledejP` | nvarchar(100) | ANO |  |  |
| 11 | `CMD_HledejZ` | nvarchar(100) | ANO |  |  |
| 12 | `CMD_MinLEN` | int | ANO |  |  |
| 13 | `CMD_MaxLEN` | int | ANO |  |  |
| 14 | `CMD_MezeraP` | bit | NE | ((0)) |  |
| 15 | `CMD_MezeraZ` | bit | NE | ((0)) |  |
| 16 | `CMD_JeDatum` | bit | NE | ((0)) |  |
| 17 | `CMD_JeDatumDopZ` | nvarchar(100) | ANO |  |  |
| 18 | `DatumFormat` | nvarchar(50) | NE | ('YYYYMMDD') |  |
| 19 | `CMD_JeCislo` | bit | NE | ((0)) |  |
| 20 | `Pokracuj` | bit | NE | ((1)) |  |
| 21 | `OffsetP` | smallint | NE | ((0)) |  |
| 22 | `OffsetZ` | smallint | NE | ((0)) |  |
| 23 | `ZacatekRadkyP` | bit | NE | ((0)) |  |
| 24 | `KonecRadkyZ` | bit | NE | ((0)) |  |
| 25 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 26 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 27 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 28 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 29 | `DatZmeny` | datetime | ANO |  |  |
| 30 | `DesetinaCisBIT` | bit | ANO |  |  |
| 31 | `CountCHAR` | bit | NE | ((0)) |  |
| 32 | `CMD_CisloJeABO` | bit | NE | ((0)) |  |
| 33 | `CMD_JeXML` | bit | NE | ((0)) |  |
| 34 | `CMD_HledejP_ZacatekRadkyPredTextem` | bit | ANO | ((0)) |  |
| 35 | `CMD_HledejP_KonecRadkyZaTextem` | bit | ANO | ((0)) |  |
| 36 | `CMD_HledejZ_ZacatekRadkyPredTextem` | bit | ANO | ((0)) |  |
| 37 | `CMD_HledejZ_KonecRadkyZaTextem` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_AutZprDokPol` (CLUSTERED) — `ID`
