# EC_Exchange_Users

**Schema**: dbo · **Cluster**: CRM · **Rows**: 1 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Name` | nvarchar(128) | NE |  |  |
| 3 | `SMTPAddress` | nvarchar(255) | NE |  |  |
| 4 | `SpamFilter` | bit | NE | ((0)) |  |
| 5 | `SaveMailToDB` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_Exchange_Users` (CLUSTERED) — `ID`
