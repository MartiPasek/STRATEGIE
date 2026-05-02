# EC_Evidence_ElPristroju_SeznamVyrobcu

**Schema**: dbo · **Cluster**: Other · **Rows**: 120 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevVyrobce` | nvarchar(250) | NE | (' ') |  |
| 3 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 4 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 5 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 6 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Evidence_ElPristroju_Vyrobci` (CLUSTERED) — `ID`
