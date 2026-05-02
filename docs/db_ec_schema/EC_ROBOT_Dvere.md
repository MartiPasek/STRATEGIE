# EC_ROBOT_Dvere

**Schema**: dbo · **Cluster**: Production · **Rows**: 61 · **Size**: 0.07 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `NazevDveri` | varchar(20) | NE |  |  |
| 3 | `X_VyskaDveri` | smallint | NE |  |  |
| 4 | `Y_SirkaDveri` | smallint | NE |  |  |
| 5 | `X_CistaVyskaDveri` | smallint | NE |  |  |
| 6 | `Y_CistaSirkaDveri` | smallint | NE |  |  |
| 7 | `LevePrave` | char(1) | NE | (' ') |  |
| 8 | `JednoDvouKridle` | char(1) | NE | (' ') |  |
| 9 | `Poznamka` | varchar(50) | ANO |  |  |
| 10 | `Popis` | varchar(45) | ANO |  |  |
| 11 | `ReadOnly` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_ROBOT_Dvere` (CLUSTERED) — `ID`
