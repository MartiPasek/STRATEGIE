# EC_TrackedEmails

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 3

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `MessageID` | nvarchar(255) | NE |  |  |
| 3 | `SenderEmail` | nvarchar(255) | NE |  |  |
| 4 | `RecipientEmail` | nvarchar(255) | NE |  |  |
| 5 | `Subject` | nvarchar(500) | NE |  |  |
| 6 | `SentDate` | datetime | NE |  |  |
| 7 | `ResponseDeadline` | datetime | NE |  |  |
| 8 | `ResponseReceived` | bit | ANO | ((0)) |  |
| 9 | `ResponseDate` | datetime | ANO |  |  |
| 10 | `ReminderSent` | bit | ANO | ((0)) |  |
| 11 | `ReminderDate` | datetime | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_name()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK__EC_Track__3214EC27122D05DF` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_TrackedEmails_MessageID` (NONCLUSTERED) — `MessageID`
- **INDEX** `IX_EC_TrackedEmails_Deadline` (NONCLUSTERED) — `ResponseDeadline`
