# EC_TabEmails

**Schema**: dbo · **Cluster**: CRM · **Rows**: 51,219 · **Size**: 69.32 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | nvarchar(20) | NE | ('User') |  |
| 3 | `Status` | nvarchar(50) | ANO |  |  |
| 4 | `StatusText` | varchar(12) | NE |  |  |
| 5 | `IDDoklad` | int | ANO |  |  |
| 6 | `Doklad` | nvarchar(20) | ANO |  |  |
| 7 | `From` | nvarchar(255) | NE |  |  |
| 8 | `To` | nvarchar(255) | NE |  |  |
| 9 | `Cc` | nvarchar(255) | ANO |  |  |
| 10 | `Subject` | nvarchar(255) | NE |  |  |
| 11 | `Body` | ntext | ANO |  |  |
| 12 | `Attachments` | ntext | ANO |  |  |
| 13 | `Poznamka` | ntext | ANO |  |  |
| 14 | `CreationTime` | datetime | ANO |  |  |
| 15 | `SentTime` | datetime | ANO |  |  |
| 16 | `ReceivedTime` | datetime | ANO |  |  |
| 17 | `Sent` | int | NE |  |  |
| 18 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 19 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 20 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 21 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_TabEmails` (CLUSTERED) — `ID`
