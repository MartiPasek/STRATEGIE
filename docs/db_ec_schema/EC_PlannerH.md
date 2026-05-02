# EC_PlannerH

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | NE |  |  |
| 3 | `CisloZam` | int | ANO |  |  |
| 4 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 5 | `DatZmeny` | datetime | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `Zmenil` | nvarchar(128) | ANO |  |  |

## Indexy

- **PK** `PK_EC_PlannerH` (CLUSTERED) — `ID`
