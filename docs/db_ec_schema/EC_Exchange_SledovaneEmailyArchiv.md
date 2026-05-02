# EC_Exchange_SledovaneEmailyArchiv

**Schema**: dbo · **Cluster**: CRM · **Rows**: 31 · **Size**: 0.07 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `OriginalID` | int | ANO |  |  |
| 3 | `MessageID` | nvarchar(255) | ANO |  |  |
| 4 | `SentDate` | datetime | ANO |  |  |
| 5 | `Recipient` | nvarchar(255) | ANO |  |  |
| 6 | `Subject` | nvarchar(500) | ANO |  |  |
| 7 | `Categories` | nvarchar(MAX) | ANO |  |  |
| 8 | `ResponseReceived` | bit | ANO |  |  |
| 9 | `ResponseDate` | datetime | ANO |  |  |
| 10 | `DaysToResponse` | int | ANO |  |  |
| 11 | `LastChecked` | datetime | ANO |  |  |
| 12 | `ArchivedDate` | datetime | ANO |  |  |
| 13 | `ArchiveReason` | nvarchar(MAX) | ANO |  |  |
| 14 | `OwnerEmail` | nvarchar(255) | ANO |  |  |
| 15 | `LastNotificationSent` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Excha__3214EC27FE13BC02` (CLUSTERED) — `ID`
