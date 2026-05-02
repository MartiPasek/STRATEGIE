# EC_X_Kmen

**Schema**: dbo · **Cluster**: Other · **Rows**: 25,991 · **Size**: 2.26 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID1` | int | ANO |  |  |
| 3 | `ID2` | int | ANO |  |  |
| 4 | `RegCis1` | nvarchar(30) | ANO |  |  |
| 5 | `RegCis2` | nvarchar(30) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Kmen` (CLUSTERED) — `ID`
