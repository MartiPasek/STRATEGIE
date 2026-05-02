# EC_DopravaZakaznikoviDefaultHodnotyNakladoveKusy

**Schema**: dbo · **Cluster**: Other · **Rows**: 1 · **Size**: 0.08 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Popis` | nvarchar(10) | ANO |  |  |
| 3 | `Prijemce` | int | ANO |  |  |
| 4 | `Blokovano` | bit | ANO | ((0)) |  |
| 5 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 8 | `Vyska` | int | ANO |  |  |
| 9 | `Sirka` | int | ANO |  |  |
| 10 | `Hloubka` | int | ANO |  |  |
| 11 | `Hmotnost` | int | ANO |  |  |
| 12 | `PocetKusu` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_DopravaZakaznikoviDefaultHodnotyNakladoveKusy` (CLUSTERED) — `ID`
