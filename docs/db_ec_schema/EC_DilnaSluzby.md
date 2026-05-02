# EC_DilnaSluzby

**Schema**: dbo · **Cluster**: Other · **Rows**: 527 · **Size**: 0.20 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `BITprvni` | bit | ANO |  |  |
| 3 | `Datum` | date | NE |  |  |
| 4 | `Autor` | int | NE |  |  |
| 5 | `CisloZam` | int | NE |  |  |
| 6 | `Sluzba` | nvarchar(2) | NE |  |  |

## Indexy

- **PK** `PK_EC_DilnaSluzby` (CLUSTERED) — `ID`
