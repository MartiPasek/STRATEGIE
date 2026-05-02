# EC_Hala_PLCLog_LogList

**Schema**: dbo · **Cluster**: Production · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `id_Check_List` | int | NE |  |  |
| 3 | `value` | nvarchar(50) | NE | ('') |  |
| 4 | `date` | date | ANO | (CONVERT([date],getdate())) |  |
| 5 | `time` | time | ANO | (CONVERT([time],getdate())) |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Hala_PLCLog_LogList` (CLUSTERED) — `ID`
