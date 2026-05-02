# EC_Dochazka_Tisk

**Schema**: dbo · **Cluster**: HR · **Rows**: 19 · **Size**: 0.07 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Mesic` | int | ANO |  |  |
| 4 | `Rok` | int | ANO |  |  |
| 5 | `Tyden` | int | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |

## Indexy

- **PK** `PK_EC_Dochazka_Tisk` (CLUSTERED) — `ID`
