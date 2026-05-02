# EC_SkoleniOdborne

**Schema**: dbo · **Cluster**: HR · **Rows**: 56 · **Size**: 0.08 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `DatumOd` | datetime | ANO |  |  |
| 4 | `DatumDo` | datetime | ANO |  |  |
| 5 | `SkolitelExterni` | nvarchar(200) | ANO |  |  |
| 6 | `TemaSkoleni` | nvarchar(200) | ANO |  |  |
| 7 | `Typ` | nvarchar(10) | ANO |  |  |
| 8 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 12 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_ZamSkoleniOdborne` (CLUSTERED) — `ID`
