# EC_Vytizeni_Log

**Schema**: dbo · **Cluster**: Production · **Rows**: 392,733 · **Size**: 308.15 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DatPorizeni` | datetime | NE |  |  |
| 3 | `Text` | nchar(255) | NE |  |  |
| 4 | `Autor` | nchar(126) | NE |  |  |
| 5 | `DruhUdalosti` | int | NE |  |  |
| 6 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 7 | `Datum` | date | ANO |  |  |
| 8 | `CisloZam` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Log` (CLUSTERED) — `ID`
