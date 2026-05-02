# EC_Exchange_TempEmails

**Schema**: dbo · **Cluster**: CRM · **Rows**: 46 · **Size**: 0.08 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | varbinary(512) | NE |  |  |
| 2 | `Sender` | nvarchar(320) | NE |  |  |
| 3 | `Subject` | nvarchar(500) | ANO |  |  |
| 4 | `Categories` | nvarchar(255) | ANO |  |  |
| 5 | `IsRead` | bit | ANO |  |  |
| 6 | `HasAttachments` | bit | ANO |  |  |
| 7 | `ToRecipients` | nvarchar(255) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Exchange_TempEmails_1` (CLUSTERED) — `ID`
