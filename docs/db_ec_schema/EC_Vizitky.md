# EC_Vizitky

**Schema**: dbo · **Cluster**: HR · **Rows**: 74 · **Size**: 0.08 MB · **Sloupců**: 16 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisZam` | int | NE |  |  |
| 3 | `IDFunkce` | nvarchar(100) | ANO |  |  |
| 4 | `Telefon` | nvarchar(50) | ANO |  |  |
| 5 | `Mobil` | nvarchar(50) | ANO |  |  |
| 6 | `Email` | nvarchar(50) | ANO |  |  |
| 7 | `Skype` | nvarchar(50) | ANO |  |  |
| 8 | `Zobraz_Mobil` | bit | ANO | ((1)) |  |
| 9 | `Zobraz_Skype` | bit | ANO | ((1)) |  |
| 10 | `Zobraz_Email` | bit | ANO | ((1)) |  |
| 11 | `Zobraz_Telefon` | bit | ANO | ((1)) |  |
| 12 | `Zmena_TelMob` | bit | ANO | ((0)) |  |
| 13 | `Druhy_Tel` | bit | ANO |  |  |
| 14 | `Popis` | nvarchar(100) | ANO |  |  |
| 15 | `Jazyk` | nvarchar(3) | ANO | (N'CZ') |  |
| 16 | `Firma` | smallint | ANO | ((1)) |  |

## Indexy

- **PK** `PK_EC_Vizitky` (CLUSTERED) — `ID`
