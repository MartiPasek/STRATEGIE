# EC_CenikySkupiny

**Schema**: dbo · **Cluster**: Finance · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(100) | NE |  |  |
| 3 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenikySkupiny` (CLUSTERED) — `ID`
