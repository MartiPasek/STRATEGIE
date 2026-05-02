# EC_ROBOT_Dil

**Schema**: dbo · **Cluster**: Production · **Rows**: 293 · **Size**: 0.13 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloDilu` | int | ANO |  |  |
| 3 | `PopisDilu` | nvarchar(50) | ANO |  |  |
| 4 | `Vyrobce` | nvarchar(20) | ANO |  |  |
| 5 | `X_VyskaDilu` | numeric(5,1) | NE |  |  |
| 6 | `Y_SirkaDilu` | numeric(5,1) | NE |  |  |
| 7 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 8 | `PoznamkaROBOT` | nvarchar(50) | ANO |  |  |
| 9 | `ReadOnly` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_ROBOT_Komponenta` (CLUSTERED) — `ID`
