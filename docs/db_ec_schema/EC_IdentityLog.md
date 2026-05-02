# EC_IdentityLog

**Schema**: dbo · **Cluster**: Other · **Rows**: 312 · **Size**: 2.54 MB · **Sloupců**: 17 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `LogID` | int | NE |  |  |
| 2 | `Cas` | datetime2 | NE | (sysdatetime()) |  |
| 3 | `TabName` | nvarchar(100) | NE |  |  |
| 4 | `NovaHodnotaID` | int | NE |  |  |
| 5 | `PredchoziMaxID` | int | NE |  |  |
| 6 | `Skok` | int | ANO |  |  |
| 7 | `UserName` | nvarchar(200) | NE | (suser_sname()) |  |
| 8 | `AppName` | nvarchar(500) | NE | (app_name()) |  |
| 9 | `HostName` | nvarchar(200) | NE | (host_name()) |  |
| 10 | `SessionID` | int | NE | (@@spid) |  |
| 11 | `IPAdresa` | nvarchar(50) | ANO |  |  |
| 12 | `OriginalLogin` | nvarchar(200) | ANO |  |  |
| 13 | `TransactionID` | bigint | ANO |  |  |
| 14 | `NestLevel` | int | ANO |  |  |
| 15 | `VolajiciSQL` | nvarchar(MAX) | ANO |  |  |
| 16 | `VolajiciProc` | nvarchar(500) | ANO |  |  |
| 17 | `VolajiciDB` | nvarchar(200) | ANO |  |  |

## Indexy

- **PK** `PK__EC_Ident__5E5499A82E8C5162` (CLUSTERED) — `LogID`
