# EC_Vytizeni_KapacitaDilny

**Schema**: dbo · **Cluster**: Production · **Rows**: 753 · **Size**: 0.20 MB · **Sloupců**: 8 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Datum` | date | ANO |  |  |
| 3 | `PocetHodin` | int | ANO |  |  |
| 4 | `Poznamka` | nvarchar(1000) | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_Vytizeni_KapacitaDilny` (CLUSTERED) — `ID`
