# EC_X_Ceniky

**Schema**: dbo · **Cluster**: Other · **Rows**: 6,303 · **Size**: 0.45 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID1` | int | ANO |  |  |
| 3 | `ID2` | int | ANO |  |  |
| 4 | `DatPorizeni1` | datetime | ANO |  |  |
| 5 | `DatPorizeni2` | datetime | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_X_Ceniky` (CLUSTERED) — `ID`
