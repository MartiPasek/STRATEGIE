# EC_ObedyZam

**Schema**: dbo · **Cluster**: Other · **Rows**: 11 · **Size**: 0.07 MB · **Sloupců**: 9 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | NE |  |  |
| 3 | `Jmeno` | nvarchar(50) | NE |  |  |
| 4 | `Prijmeni` | nvarchar(50) | NE |  |  |
| 5 | `Heslo` | nvarchar(50) | NE |  |  |
| 6 | `PocObedu` | int | ANO |  |  |
| 7 | `PocCest` | int | ANO |  |  |
| 8 | `Vaha` | decimal(18,5) | ANO |  |  |
| 9 | `EditAuthorization` | bit | NE | ((0)) |  |

## Indexy

- **PK** `PK_EC_ObedyZam` (CLUSTERED) — `ID`
