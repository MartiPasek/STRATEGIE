# EC_SoftwareVersion

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,390 · **Size**: 1.16 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Software` | int | NE |  |  |
| 3 | `Version` | int | NE |  |  |
| 4 | `TimeStamp` | nvarchar(1000) | ANO |  |  |
| 5 | `Status` | tinyint | NE | ((0)) |  |
| 6 | `StatusText` | varchar(21) | ANO |  |  |
| 7 | `User` | int | ANO |  |  |
| 8 | `ReleaseDate` | datetime | ANO |  |  |
| 9 | `ReleaseAuthor` | nvarchar(128) | ANO |  |  |
| 10 | `Author` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `CreationDate` | datetime | NE | (getdate()) |  |
| 12 | `Changed` | nvarchar(128) | ANO |  |  |
| 13 | `DateChanges` | datetime | ANO |  |  |
| 14 | `Poznamka` | nvarchar(MAX) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SoftwareVersion` (CLUSTERED) — `ID`
