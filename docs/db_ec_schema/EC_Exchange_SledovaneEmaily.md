# EC_Exchange_SledovaneEmaily

**Schema**: dbo · **Cluster**: CRM · **Rows**: 2 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `MessageID` | nvarchar(255) | ANO |  |  |
| 3 | `SentDate` | datetime | ANO |  |  |
| 4 | `Recipient` | nvarchar(255) | ANO |  |  |
| 5 | `Subject` | nvarchar(500) | ANO |  |  |
| 6 | `Categories` | nvarchar(MAX) | ANO |  |  |
| 7 | `ResponseReceived` | bit | ANO | ((0)) |  |
| 8 | `ResponseDate` | datetime | ANO |  |  |
| 9 | `DaysToResponse` | int | ANO |  |  |
| 10 | `LastChecked` | datetime | ANO |  |  |
| 11 | `OwnerEmail` | nvarchar(255) | ANO |  |  |
| 12 | `LastNotificationSent` | datetime | ANO |  |  |

## Indexy

- **PK** `PK__EC_Excha__3214EC27EB5B15D5` (CLUSTERED) — `ID`
