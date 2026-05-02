# EC_DochazkaApp

**Schema**: dbo · **Cluster**: HR · **Rows**: 2 · **Size**: 0.09 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktivni` | bit | ANO | ((1)) |  |
| 3 | `Verze` | nvarchar(10) | NE |  |  |
| 4 | `Platforma` | nvarchar(10) | NE |  |  |
| 5 | `UpdatePath` | nvarchar(150) | NE |  |  |
| 6 | `UpdateInfo` | text | ANO |  |  |
| 7 | `Poznamka` | text | ANO |  |  |
| 8 | `Autor` | int | NE |  |  |
| 9 | `Datum` | date | NE |  |  |

## Indexy

- **PK** `PK_EC_DochazkaApp` (CLUSTERED) — `ID`
