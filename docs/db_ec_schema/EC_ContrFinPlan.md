# EC_ContrFinPlan

**Schema**: dbo · **Cluster**: Other · **Rows**: 27 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDPredpis` | int | ANO |  |  |
| 3 | `IDObdobi` | int | ANO |  |  |
| 4 | `Obdobi` | nvarchar(10) | ANO |  |  |
| 5 | `Popis` | nvarchar(200) | ANO |  |  |
| 6 | `Castka` | numeric(18,0) | ANO |  |  |
| 7 | `CisloOrg` | int | ANO |  |  |
| 8 | `Organizace` | nvarchar(100) | ANO |  |  |
| 9 | `Stredisko` | int | ANO |  |  |
| 10 | `Splatnost` | datetime | ANO |  |  |
| 11 | `CisloZaznamu` | int | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_FinPlan` (CLUSTERED) — `ID`
