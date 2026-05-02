# EC_PlannerP

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IdHlav` | int | NE |  |  |
| 3 | `Skup` | tinyint | ANO |  |  |
| 4 | `SkupText` | varchar(14) | NE |  |  |
| 5 | `Nazev` | nvarchar(255) | NE |  |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PlannerP` (CLUSTERED) — `ID`
