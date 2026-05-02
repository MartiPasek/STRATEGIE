# EC_Vytizeni_PlanSuma

**Schema**: dbo · **Cluster**: Production · **Rows**: 14,690 · **Size**: 5.58 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 3 | `Datum` | date | ANO |  |  |
| 4 | `PocetHodin` | int | ANO |  |  |
| 5 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 7 | `Zmenil` | nvarchar(126) | ANO |  |  |
| 8 | `DatZmeny` | datetime | ANO |  |  |
| 9 | `Poznamka` | nvarchar(4000) | ANO |  |  |
| 10 | `Typ` | int | ANO |  |  |
| 11 | `Blokovano` | bit | ANO |  |  |
| 12 | `Barva` | nvarchar(10) | ANO |  |  |
| 13 | `BarvaRamecek` | nvarchar(10) | ANO |  |  |
| 14 | `ZobrazujNuly` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Vytizeni_PlanSuma` (CLUSTERED) — `ID`
