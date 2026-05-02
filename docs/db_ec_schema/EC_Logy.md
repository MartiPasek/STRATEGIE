# EC_Logy

**Schema**: dbo · **Cluster**: Logging · **Rows**: 27,821 · **Size**: 5.14 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Typ` | tinyint | NE | ((0)) |  |
| 4 | `TypText` | varchar(9) | NE |  |  |
| 5 | `Location` | nvarchar(255) | ANO |  |  |
| 6 | `Text` | nvarchar(4000) | ANO |  |  |
| 7 | `Text3` | nvarchar(255) | ANO |  |  |
| 8 | `Text4` | nvarchar(255) | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Log` (CLUSTERED) — `ID`
