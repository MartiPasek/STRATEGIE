# EC_RegCisDodavateleVazby

**Schema**: dbo · **Cluster**: Other · **Rows**: 13 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `RegCisZkratka` | nvarchar(8) | NE |  |  |
| 3 | `CisloOrg` | int | ANO |  |  |
| 4 | `Poradi` | tinyint | NE | ((0)) |  |
| 5 | `Vychozi` | bit | NE | ((0)) |  |
| 6 | `Blokovano` | bit | NE | ((0)) |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 13 | `DatZamceni` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_RegCisDodavateleVazby` (CLUSTERED) — `ID`
