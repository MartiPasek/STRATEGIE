# EC_CenaMedi

**Schema**: dbo · **Cluster**: Finance · **Rows**: 112 · **Size**: 0.07 MB · **Sloupců**: 7 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Datum` | datetime | NE |  |  |
| 3 | `CenaMed_EUR_100Kg` | numeric(18,2) | NE |  |  |
| 4 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 6 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 7 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_CenaMedi` (CLUSTERED) — `ID`
