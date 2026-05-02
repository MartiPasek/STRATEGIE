# EC_KmenZbozi_KonverzeRegCis

**Schema**: dbo · **Cluster**: Production · **Rows**: 406 · **Size**: 0.25 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `RadekExcel` | int | ANO |  |  |
| 4 | `RegCisZdroj` | nvarchar(100) | NE |  |  |
| 5 | `RegCisCil` | nvarchar(100) | ANO |  |  |
| 6 | `DodavatelZdroj` | nvarchar(100) | ANO |  |  |
| 7 | `Rabat` | nvarchar(20) | ANO |  |  |
| 8 | `NahradaPopis` | nvarchar(200) | ANO |  |  |
| 9 | `Nahrada` | bit | NE | ((0)) |  |
| 10 | `Upozornit` | bit | NE | ((0)) |  |
| 11 | `Neaktivni` | bit | NE | ((0)) |  |
| 12 | `Poznamka` | ntext | ANO |  |  |
| 13 | `IdKalkPolZdroj` | int | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 15 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 16 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 19 | `DatZamceni` | datetime | ANO |  |  |
| 20 | `DocasnaNahrada` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_KmenZbozi_KonverzeRegCis` (CLUSTERED) — `ID`
