# EC_ObedyHlasovani

**Schema**: dbo · **Cluster**: Other · **Rows**: 2,233 · **Size**: 0.32 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `Jmeno` | nvarchar(50) | NE |  |  |
| 4 | `Prijmeni` | nvarchar(50) | NE |  |  |
| 5 | `Datum` | date | ANO | (CONVERT([date],getdate(),0)) |  |
| 6 | `Cas` | time | ANO | (CONVERT([time],getdate(),0)) |  |
| 7 | `HlasuVyber1` | float | ANO | ((0)) |  |
| 8 | `HlasuVyber2` | float | ANO | ((0)) |  |
| 9 | `HlasuVyber3` | float | ANO | ((0)) |  |
| 10 | `HlasuNejdu` | float | ANO | ((0)) |  |
| 11 | `Obed` | int | ANO |  |  |
| 12 | `Cesta` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_ObedyHlasovani` (CLUSTERED) — `ID`
