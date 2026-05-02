# EC_X_KalkSkupiny

**Schema**: dbo · **Cluster**: Other · **Rows**: 115 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID1` | int | ANO |  |  |
| 3 | `ID2` | int | ANO |  |  |
| 4 | `Cislo1` | int | ANO |  |  |
| 5 | `Cislo2` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_X_KalkSkupiny` (CLUSTERED) — `ID`
