# EC_ObedySW

**Schema**: dbo · **Cluster**: Other · **Rows**: 2 · **Size**: 0.09 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Verze` | nvarchar(50) | NE |  |  |
| 3 | `Datum` | date | NE |  |  |
| 4 | `Autor` | int | NE |  |  |
| 5 | `Aktivni` | bit | NE | ((1)) |  |
| 6 | `AboutInfo` | text | ANO |  |  |
| 7 | `UpdateInfo` | text | ANO |  |  |
| 8 | `UpdateFilePath` | text | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObedySW` (CLUSTERED) — `ID`
