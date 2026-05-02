# EC_Events

**Schema**: dbo · **Cluster**: Logging · **Rows**: 12 · **Size**: 0.07 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Guide` | uniqueidentifier | ANO |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `StartTime` | datetime | ANO |  |  |
| 5 | `EndTime` | datetime | ANO |  |  |
| 6 | `Subject` | nvarchar(70) | ANO |  |  |
| 7 | `Caption` | nvarchar(70) | ANO |  |  |
| 8 | `Color` | int | ANO |  |  |
| 9 | `Notes` | nvarchar(200) | ANO |  |  |
| 10 | `Image` | int | ANO |  |  |
| 11 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 12 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Events_1` (CLUSTERED) — `ID`
