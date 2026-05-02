# EC_LogyProcVazby

**Schema**: dbo · **Cluster**: Logging · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_LogyProc` | int | NE |  |  |
| 3 | `Logovat` | bit | ANO | ((1)) |  |
| 4 | `LogUser` | nvarchar(128) | ANO |  |  |
| 5 | `FirstRun` | datetime | ANO |  |  |
| 6 | `LastRun` | datetime | ANO |  |  |
| 7 | `CountRun` | int | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_LogyProcVazby` (CLUSTERED) — `ID`
