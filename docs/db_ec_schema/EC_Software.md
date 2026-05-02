# EC_Software

**Schema**: dbo · **Cluster**: Other · **Rows**: 6 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Active` | bit | NE | ((1)) |  |
| 3 | `Name` | nvarchar(50) | ANO |  |  |
| 4 | `Description` | nvarchar(MAX) | ANO |  |  |
| 5 | `Type` | nvarchar(20) | ANO |  |  |
| 6 | `FilePath` | nvarchar(500) | ANO |  |  |
| 7 | `ApkFilePath` | nvarchar(500) | ANO |  |  |
| 8 | `FileName` | nvarchar(255) | ANO |  |  |
| 9 | `SourcePath` | nvarchar(500) | ANO |  |  |
| 10 | `Author` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `CreationDate` | datetime | NE | (getdate()) |  |
| 12 | `Changed` | nvarchar(128) | ANO |  |  |
| 13 | `DateChanges` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Software` (CLUSTERED) — `ID`
