# EC_Vytizeni_StatistikaPol

**Schema**: dbo · **Cluster**: Production · **Rows**: 621,548 · **Size**: 21.90 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDHlav` | int | ANO |  |  |
| 3 | `Datum` | date | ANO |  |  |
| 4 | `Statistika` | numeric(18,2) | ANO |  |  |
| 5 | `DatPorizeni` | date | ANO |  |  |
| 6 | `Autor` | date | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_StatistikyPol` (CLUSTERED) — `ID`
