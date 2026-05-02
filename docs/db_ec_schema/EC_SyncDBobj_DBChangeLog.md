# EC_SyncDBobj_DBChangeLog

**Schema**: dbo · **Cluster**: Other · **Rows**: 3,079 · **Size**: 24.96 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatabaseName` | varchar(256) | NE |  |  |
| 3 | `EventType` | varchar(50) | NE |  |  |
| 4 | `ObjectName` | varchar(256) | NE |  |  |
| 5 | `ObjectType` | varchar(25) | NE |  |  |
| 6 | `EventDate` | datetime | NE |  |  |
| 7 | `LoginName` | varchar(256) | NE |  |  |
| 9 | `Object_ID` | int | ANO |  |  |
| 10 | `TSQLCommand` | nvarchar(MAX) | ANO |  |  |
| 11 | `_zpracovano` | bit | NE | ((0)) |  |
| 13 | `CisloZam` | int | ANO | ([dbo].[EC_GetUserCisZam]()) |  |

## Indexy

- **PK** `PK__EC_SyncD__A7FEF0BD0732D680` (CLUSTERED) — `ID`
