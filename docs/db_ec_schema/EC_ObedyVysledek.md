# EC_ObedyVysledek

**Schema**: dbo · **Cluster**: Other · **Rows**: 724 · **Size**: 0.13 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Vyhodnotil` | int | NE |  |  |
| 3 | `Datum` | date | NE |  |  |
| 4 | `Cas` | time | NE |  |  |
| 5 | `HlasuVyber1` | float | ANO | ((0)) |  |
| 6 | `HlasuVyber2` | float | ANO | ((0)) |  |
| 7 | `HlasuVyber3` | float | ANO | ((0)) |  |
| 8 | `HlasuNejdu` | float | ANO | ((0)) |  |
| 9 | `FinalVyber` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObedyVysledek` (CLUSTERED) — `ID`
