# EC_ContrSluzby

**Schema**: dbo · **Cluster**: Other · **Rows**: 30 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Sluzba` | nvarchar(50) | ANO |  |  |
| 3 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 5 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_ContrSluzby` (CLUSTERED) — `ID`
