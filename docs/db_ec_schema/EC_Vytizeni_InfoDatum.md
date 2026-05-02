# EC_Vytizeni_InfoDatum

**Schema**: dbo · **Cluster**: Production · **Rows**: 121 · **Size**: 0.20 MB · **Sloupců**: 5 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Datum` | date | ANO |  |  |
| 3 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 4 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 5 | `DatPorizeni` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_Vytizeni_InfoDatum` (CLUSTERED) — `ID`
