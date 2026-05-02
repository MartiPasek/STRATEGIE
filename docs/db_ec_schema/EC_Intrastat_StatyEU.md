# EC_Intrastat_StatyEU

**Schema**: dbo · **Cluster**: Other · **Rows**: 27 · **Size**: 0.07 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevStatu` | nvarchar(100) | ANO |  |  |
| 3 | `ZkratkaStatu` | nvarchar(2) | ANO |  |  |
| 4 | `datporizeni` | datetime | ANO | (getdate()) |  |
| 5 | `autor` | nvarchar(128) | ANO | (suser_sname()) |  |

## Indexy

- **PK** `PK__EC_Intra__3214EC274EA65A49` (CLUSTERED) — `ID`
