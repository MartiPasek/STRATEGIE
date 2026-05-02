# EC_SkoleniSamostudium

**Schema**: dbo · **Cluster**: HR · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Datum` | datetime | ANO |  |  |
| 4 | `Skolitel` | nvarchar(200) | ANO |  |  |
| 5 | `DruhSkoleni` | nvarchar(200) | ANO |  |  |
| 6 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 7 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 10 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZamSkoleniOstatni` (CLUSTERED) — `ID`
