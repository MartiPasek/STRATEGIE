# EC_ContrFinPredpis

**Schema**: dbo · **Cluster**: Other · **Rows**: 184 · **Size**: 0.13 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDZdroj` | int | ANO |  |  |
| 3 | `IDTyp` | nvarchar(20) | ANO |  |  |
| 4 | `IDZboSklad` | int | ANO |  |  |
| 5 | `IDPoklText` | int | ANO |  |  |
| 6 | `Uct` | bit | ANO | ((0)) |  |
| 7 | `Contr` | bit | ANO | ((0)) |  |
| 8 | `RegCis` | nvarchar(30) | ANO |  |  |
| 9 | `Popis` | nvarchar(50) | ANO |  |  |
| 10 | `PlatnostOd` | datetime | ANO |  |  |
| 11 | `UkoncitKDat` | datetime | ANO |  |  |
| 12 | `DatUpozorneni` | datetime | ANO |  |  |
| 13 | `IDPredpisTyp` | int | ANO |  |  |
| 14 | `Castka` | numeric(18,0) | ANO |  |  |
| 15 | `CisloOrg` | int | ANO |  |  |
| 16 | `CisloContrUcet` | int | ANO |  |  |
| 17 | `CisloUctUcet` | int | ANO |  |  |
| 18 | `Stredisko` | int | ANO |  |  |
| 19 | `VytvorenoZ` | nvarchar(50) | ANO |  |  |
| 20 | `Aktivni` | bit | ANO | ((1)) |  |
| 21 | `Pokladna` | bit | ANO | ((0)) |  |
| 22 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 23 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 24 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ContrFinPredpis` (CLUSTERED) — `ID`
