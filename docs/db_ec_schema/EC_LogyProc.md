# EC_LogyProc

**Schema**: dbo · **Cluster**: Logging · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ProcID` | int | ANO |  |  |
| 3 | `ProcName` | nvarchar(100) | ANO |  |  |
| 4 | `DatLastStart` | datetime | NE | (getdate()) |  |
| 5 | `UserIP` | nvarchar(30) | ANO |  |  |
| 6 | `Connect_time` | datetime | ANO |  |  |
| 7 | `Text` | nvarchar(200) | ANO |  |  |
| 8 | `SPID` | int | ANO |  |  |
| 9 | `IDDoklad` | int | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_LogyProc` (CLUSTERED) — `ID`
