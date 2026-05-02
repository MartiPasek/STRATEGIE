# EC_UniLog

**Schema**: dbo · **Cluster**: Other · **Rows**: 5,888 · **Size**: 2.02 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `id` | int | NE |  |  |
| 2 | `typ` | nvarchar(100) | ANO |  |  |
| 3 | `text` | nvarchar(4000) | ANO |  |  |
| 4 | `DateTimeFromSource` | datetime | ANO |  |  |
| 5 | `autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 7 | `AppIconName` | nvarchar(100) | ANO |  |  |
| 8 | `Location` | nvarchar(255) | ANO |  |  |

## Indexy

- **PK** `PK_EC_UniLog` (CLUSTERED) — `id`
