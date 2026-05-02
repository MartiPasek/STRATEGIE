# EC_SkoleniInterni

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloSkolitel` | int | ANO |  |  |
| 3 | `CisloStudent` | int | ANO |  |  |
| 4 | `DruhSkoleni` | nchar(200) | ANO |  |  |
| 5 | `Datum` | datetime | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatZmeny` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_SkoleniInterni` (CLUSTERED) — `ID`
