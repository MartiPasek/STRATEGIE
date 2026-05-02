# EC_LogyH

**Schema**: dbo · **Cluster**: Logging · **Rows**: 1,365 · **Size**: 0.64 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `LogNr` | int | ANO |  |  |
| 3 | `UserIP` | nvarchar(50) | ANO |  |  |
| 4 | `Connect_time` | datetime | ANO |  |  |
| 5 | `DatStart` | datetime | NE | (getdate()) |  |
| 6 | `ProcID` | int | ANO |  |  |
| 7 | `ProcName` | nvarchar(100) | ANO |  |  |
| 8 | `Text` | nvarchar(200) | ANO |  |  |
| 9 | `SPID` | int | ANO |  |  |
| 10 | `AppInstance` | int | ANO |  |  |
| 11 | `IDDoklad` | int | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `DatZmeny` | datetime | ANO |  |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_LogyH` (CLUSTERED) — `ID`
