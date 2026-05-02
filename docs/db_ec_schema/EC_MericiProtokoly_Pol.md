# EC_MericiProtokoly_Pol

**Schema**: dbo · **Cluster**: Production · **Rows**: 30,404 · **Size**: 6.30 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_Hlav` | int | NE |  |  |
| 3 | `TimeBCR` | nvarchar(100) | ANO |  |  |
| 4 | `Dev` | nvarchar(100) | ANO |  |  |
| 5 | `Mem` | nvarchar(100) | ANO |  |  |
| 6 | `Description` | nvarchar(100) | ANO |  |  |
| 7 | `Limit` | nvarchar(100) | ANO |  |  |
| 8 | `Result1` | nvarchar(100) | ANO |  |  |
| 9 | `Result2` | nvarchar(100) | ANO |  |  |
| 10 | `Result3` | nvarchar(100) | ANO |  |  |
| 11 | `Result4` | nvarchar(100) | ANO |  |  |
| 12 | `Result5` | nvarchar(100) | ANO |  |  |
| 13 | `Result6` | nvarchar(100) | ANO |  |  |
| 14 | `Result7` | nvarchar(100) | ANO |  |  |
| 15 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `DatZmeny` | datetime | ANO |  |  |
| 18 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MericiProtokoly_Pol` (CLUSTERED) — `ID`
