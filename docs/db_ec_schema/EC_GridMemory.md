# EC_GridMemory

**Schema**: dbo · **Cluster**: Other · **Rows**: 40,620 · **Size**: 5.32 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `AppName` | nvarchar(128) | NE |  |  |
| 3 | `FormName` | nvarchar(128) | NE |  |  |
| 4 | `GridName` | nvarchar(128) | NE |  |  |
| 5 | `ViewNumber` | int | NE |  |  |
| 6 | `User` | int | NE |  |  |
| 7 | `FieldName` | nvarchar(128) | NE | ('ID') |  |
| 8 | `FieldValue` | nvarchar(100) | NE |  |  |
| 9 | `ColumnName` | nvarchar(128) | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_GridMemory` (CLUSTERED) — `ID`
