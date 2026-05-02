# EC_MenuStrom_PrepniNaSoudecek

**Schema**: dbo · **Cluster**: Other · **Rows**: 46 · **Size**: 0.07 MB · **Sloupců**: 10 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `User` | int | NE |  |  |
| 3 | `Soudecek` | int | ANO |  |  |
| 4 | `FieldName` | nvarchar(128) | ANO |  |  |
| 5 | `FieldValue` | nvarchar(128) | ANO |  |  |
| 6 | `OpenDetail` | bit | NE | ((0)) |  |
| 7 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 8 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 9 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 10 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_MenuStrom_PrepniNaSoudecek` (CLUSTERED) — `ID`
