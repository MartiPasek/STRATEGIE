# EC_GrafyHodnoty

**Schema**: dbo · **Cluster**: Other · **Rows**: 15 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDGraf` | int | ANO |  |  |
| 3 | `X` | int | ANO |  |  |
| 4 | `Y` | int | ANO |  |  |
| 5 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_GrafyHodnoty` (CLUSTERED) — `ID`
