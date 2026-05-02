# EC_FotkyZam

**Schema**: dbo · **Cluster**: HR · **Rows**: 78 · **Size**: 0.20 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | nchar(10) | ANO |  |  |
| 3 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_FotkyZam` (CLUSTERED) — `ID`
